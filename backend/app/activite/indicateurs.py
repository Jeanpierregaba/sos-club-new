"""Les indicateurs de la page « Activité » (spec 051), calculés à la demande, en SQL agrégé.

Deux sources : les événements anonymes (bruts sur 90 jours, totaux par jour au-delà) et les tables du site (comptes,
parties, certification, clubs). Les visiteurs d'une période sont la somme des visiteurs de chaque jour (ADR-0014).
"""

import contextlib
from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, extract, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement

from app.activite.models import (
    DIMENSIONS_VISITEURS,
    ORDRE_DIMENSIONS,
    SEPARATEUR,
    EvenementActivite,
    PresenceSemaine,
    TotalActiviteJour,
    TypeEvenement,
    VisiteursGroupeJour,
    VisiteursJour,
)
from app.activite.purge import PRESENCE_SEMAINES
from app.activite.schemas_admin import Bloc, Chiffre, Colonne, Grille, NomBloc, PointSerie, Serie, Tableau
from app.bibliotheque.models import Ressource
from app.certification.models import BadgeObtenu, Certificat, PlaceReussie
from app.clubs.activation import en_service
from app.clubs.models import Adhesion, Club, EtatAdhesion
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.jeux.models import DefiReponse
from app.moderation.models import Contenu, VersionContenu
from app.quiz.models import EtatTentative, QuestionQuiz, Quiz, ReponseQuiz, TentativeQuiz
from app.referentiel.models import Dre, Etablissement, Iesg

E = EvenementActivite
T = TotalActiviteJour
V = VisiteursGroupeJour
INSCRITS = (Role.eleve, Role.encadreur, Role.visiteur)
NOTE_MINIMUM = (
    "Les visiteurs se comptent par jour, sans cookie : une classe sur un même ordinateur compte pour un, et un "
    "bloqueur de publicités peut cacher des pages vues. Les chiffres tirés des comptes et des parties restent exacts."
)


@dataclass(frozen=True)
class Periode:
    du: date
    au: date

    @property
    def jours(self) -> int:
        return (self.au - self.du).days + 1

    @property
    def precedente(self) -> Periode:
        return Periode(self.du - timedelta(days=self.jours), self.du - timedelta(days=1))

    @property
    def debut(self) -> datetime:
        return datetime.combine(self.du, time(), UTC)

    @property
    def fin(self) -> datetime:
        return datetime.combine(self.au + timedelta(days=1), time(), UTC)

    def contient(self, colonne: Any) -> ColumnElement[bool]:
        return and_(colonne >= self.debut, colonne < self.fin)


def _taux(partie: float | None, tout: float | None) -> float | None:
    return round(100 * partie / tout, 1) if partie is not None and tout else None


def _bloc(nom: NomBloc, p: Periode, **contenu: Any) -> Bloc:
    a = p.precedente
    return Bloc(bloc=nom, du=p.du, au=p.au, precedent_du=a.du, precedent_au=a.au, **contenu)


def _serie_jours(p: Periode, valeurs: dict[date, float], cle: str, libelle: str) -> Serie:
    jours = (p.du + timedelta(days=i) for i in range(p.jours))
    return Serie(cle=cle, libelle=libelle, points=[PointSerie(jour=j, valeur=valeurs.get(j, 0)) for j in jours])


async def _deux_periodes(p: Periode, calcul: Callable[[Periode], Awaitable[float | None]]) -> tuple[Any, Any]:
    return await calcul(p), await calcul(p.precedente)


# Événements : bruts et totaux réunis -----------------------------------------------------------------------------


async def evenements(
    db: AsyncSession, p: Periode, type_: TypeEvenement, *groupe: str, **egal: str | bool
) -> dict[tuple[Any, ...], tuple[int, int]]:
    """{valeurs du groupe: (événements, visiteurs)} sur la période ; les visiteurs sont sommés jour par jour."""
    filtres_e = [E.type == type_, E.jour >= p.du, E.jour <= p.au, *(getattr(E, c) == v for c, v in egal.items())]
    colonnes_e = [func.coalesce(getattr(E, c), "") if c not in ("jour", "connecte") else getattr(E, c) for c in groupe]
    par_jour = (
        select(*(c.label(n) for c, n in zip(colonnes_e, groupe, strict=True)), func.count().label("n"),
               func.count(E.visiteur.distinct()).label("v"))
        .where(*filtres_e)
        .group_by(E.jour, *colonnes_e)
        .subquery()
    )  # fmt: skip
    bruts = await db.execute(
        select(*(par_jour.c[n] for n in groupe), func.sum(par_jour.c.n), func.sum(par_jour.c.v)).group_by(
            *(par_jour.c[n] for n in groupe)
        )
    )
    filtres_t = [T.type == type_, T.jour >= p.du, T.jour <= p.au, *(getattr(T, c) == v for c, v in egal.items())]
    totaux = await db.execute(
        select(*(getattr(T, c) for c in groupe), func.sum(T.evenements))
        .where(*filtres_t)
        .group_by(*(getattr(T, c) for c in groupe))
    )
    resultat: dict[tuple[Any, ...], list[int]] = defaultdict(lambda: [0, 0])
    for *cle, n, v in bruts.all():
        resultat[tuple(cle)][0] += int(n or 0)
        resultat[tuple(cle)][1] += int(v or 0)
    for *cle, n in totaux.all():
        resultat[tuple(cle)][0] += int(n or 0)
    for cle, v in (await _visiteurs_anciens(db, p, type_, groupe, egal)).items():
        resultat[cle][1] += v
    return {cle: (n, v) for cle, (n, v) in resultat.items()}


def _texte(valeur: str | bool) -> str:
    return ("true" if valeur else "false") if isinstance(valeur, bool) else valeur


async def _visiteurs_anciens(
    db: AsyncSession, p: Periode, type_: TypeEvenement, groupe: tuple[str, ...], egal: dict[str, str | bool]
) -> dict[tuple[Any, ...], int]:
    """Les visiteurs des jours sortis des 90 jours, lus dans le regroupement gardé par la purge."""
    colonnes = {c for c in groupe if c != "jour"} | set(egal)
    dimensions = tuple(d for d in ORDRE_DIMENSIONS if d in colonnes)
    if dimensions not in DIMENSIONS_VISITEURS:
        raise ValueError(f"Regroupement sans visiteurs gardés : {dimensions}")
    lignes = await db.execute(
        select(V.jour, V.valeurs, V.visiteurs).where(
            V.type == type_, V.jour >= p.du, V.jour <= p.au, V.dimensions == ",".join(dimensions)
        )
    )
    resultat: dict[tuple[Any, ...], int] = defaultdict(int)
    for jour, valeurs, visiteurs in lignes:
        ligne = dict(zip(dimensions, valeurs.split(SEPARATEUR), strict=True)) if dimensions else {}
        if any(ligne[c] != _texte(v) for c, v in egal.items()):
            continue
        cle = tuple(jour if c == "jour" else (ligne[c] == "true" if c == "connecte" else ligne[c]) for c in groupe)
        resultat[cle] += int(visiteurs)
    return resultat


async def visiteurs_par_jour(db: AsyncSession, p: Periode) -> dict[date, int]:
    bruts = await db.execute(
        select(E.jour, func.count(E.visiteur.distinct())).where(E.jour >= p.du, E.jour <= p.au).group_by(E.jour)
    )
    anciens = await db.execute(
        select(VisiteursJour.jour, VisiteursJour.visiteurs).where(
            VisiteursJour.jour >= p.du, VisiteursJour.jour <= p.au
        )
    )
    return {jour: int(n) for jour, n in [*anciens.all(), *bruts.all()]}


def _top(lignes: Iterable[dict[str, Any]], cle: str, nombre: int = 20) -> list[dict[str, Any]]:
    return sorted(lignes, key=lambda ligne: ligne[cle] or 0, reverse=True)[:nombre]


# 1. Audience -----------------------------------------------------------------------------------------------------


async def audience(db: AsyncSession, p: Periode) -> Bloc:
    async def totaux(q: Periode) -> tuple[int, int, int]:
        vues = await evenements(db, q, TypeEvenement.page_vue, "connecte")
        toutes = sum(n for n, _ in vues.values())
        connectees = sum(n for (connecte,), (n, _) in vues.items() if connecte)
        return sum((await visiteurs_par_jour(db, q)).values()), toutes, connectees

    (visiteurs, vues, connectees), (visiteurs_av, vues_av, connectees_av) = await totaux(p), await totaux(p.precedente)
    par_jour_vues = await evenements(db, p, TypeEvenement.page_vue, "jour")
    pages = await evenements(db, p, TypeEvenement.page_vue, "chemin")
    entrees = await evenements(db, p, TypeEvenement.page_vue, "provenance")
    appareils = await evenements(db, p, TypeEvenement.page_vue, "appareil")
    navigateurs = await evenements(db, p, TypeEvenement.page_vue, "navigateur")
    colonnes = [Colonne(cle="libelle", libelle="", unite="texte"), Colonne(cle="visiteurs", libelle="Visiteurs")]

    def repartition(donnees: dict[tuple[Any, ...], tuple[int, int]], cle: str, titre: str) -> Tableau:
        lignes = [{"libelle": c[0], "visiteurs": v} for c, (_, v) in donnees.items() if c[0]]
        return Tableau(cle=cle, titre=titre, colonnes=colonnes, lignes=_top(lignes, "visiteurs"))

    return _bloc(
        "audience",
        p,
        chiffres=[
            Chiffre(cle="visiteurs", libelle="Visiteurs", valeur=visiteurs, precedent=visiteurs_av),
            Chiffre(cle="pages_vues", libelle="Pages vues", valeur=vues, precedent=vues_av),
            Chiffre(
                cle="pages_par_visiteur",
                libelle="Pages par visiteur",
                valeur=round(vues / visiteurs, 1) if visiteurs else None,
                precedent=round(vues_av / visiteurs_av, 1) if visiteurs_av else None,
            ),
            Chiffre(
                cle="part_connectes",
                libelle="Pages vues connecté",
                unite="pourcent",
                valeur=_taux(connectees, vues),
                precedent=_taux(connectees_av, vues_av),
            ),
        ],
        series=[
            _serie_jours(p, await visiteurs_par_jour(db, p), "visiteurs", "Visiteurs"),
            _serie_jours(p, {c[0]: n for c, (n, _) in par_jour_vues.items()}, "pages_vues", "Pages vues"),
        ],
        tableaux=[
            Tableau(
                cle="pages",
                titre="Pages les plus vues",
                colonnes=[
                    Colonne(cle="chemin", libelle="Page", unite="texte"),
                    Colonne(cle="vues", libelle="Vues"),
                    Colonne(cle="visiteurs", libelle="Visiteurs"),
                ],
                lignes=_top(({"chemin": c[0], "vues": n, "visiteurs": v} for c, (n, v) in pages.items()), "vues"),
            ),
            repartition(entrees, "provenance", "D'où viennent les visiteurs"),
            repartition(appareils, "appareils", "Appareils"),
            repartition(navigateurs, "navigateurs", "Navigateurs"),
        ],
        notes=[NOTE_MINIMUM],
    )


# 2. Inscription --------------------------------------------------------------------------------------------------

ETAPES = {
    "eleve": ("ouvert", "commence", "envoye", "cree"),
    "encadreur": ("ouvert", "commence", "envoye", "cree"),
    "visiteur": ("ouvert", "commence", "envoye", "cree", "confirme"),
}
NOMS_ETAPES = {
    "ouvert": "Formulaire ouvert",
    "commence": "Formulaire commencé",
    "envoye": "Formulaire envoyé",
    "cree": "Compte créé",
    "confirme": "E-mail confirmé",
}
NOMS_PROFILS = {"eleve": "Élèves", "encadreur": "Encadreurs", "visiteur": "Visiteurs"}


async def _comptes_crees(db: AsyncSession, q: Periode) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(Utilisateur)
            .where(Utilisateur.role.in_(INSCRITS), q.contient(Utilisateur.cree_le))
        )
        or 0
    )


async def inscription(db: AsyncSession, p: Periode) -> Bloc:
    clics = await evenements(db, p, TypeEvenement.clic_inscription, "detail")
    clics_av = await evenements(db, p.precedente, TypeEvenement.clic_inscription, "detail")
    refus = await evenements(db, p, TypeEvenement.etape_inscription, "detail")
    etapes = {c[0]: v for c, (_, v) in refus.items()}
    tableaux = [
        Tableau(
            cle="clics",
            titre="Clics « S'inscrire », par endroit du site",
            colonnes=[
                Colonne(cle="endroit", libelle="Endroit", unite="texte"),
                Colonne(cle="clics", libelle="Clics"),
                Colonne(cle="visiteurs", libelle="Visiteurs"),
            ],
            lignes=_top(({"endroit": c[0], "clics": n, "visiteurs": v} for c, (n, v) in clics.items()), "clics"),
        )
    ]
    taux_conversion: list[float | None] = []
    for profil, noms in ETAPES.items():
        lignes: list[dict[str, str | float | None]] = []
        precedent: int | None = None
        for nom in noms:
            nombre = etapes.get(f"{profil}:{nom}", 0)
            passage = _taux(nombre, precedent) if precedent is not None else None
            lignes.append(
                {"etape": NOMS_ETAPES[nom], "visiteurs": nombre, "passage": passage,
                 "abandon": round(100 - passage, 1) if passage is not None else None}
            )  # fmt: skip
            precedent = nombre
        taux_conversion.append(_taux(etapes.get(f"{profil}:cree", 0), etapes.get(f"{profil}:ouvert", 0)))
        tableaux.append(
            Tableau(
                cle=f"entonnoir_{profil}", titre=f"Entonnoir d'inscription : {NOMS_PROFILS[profil]}",
                colonnes=[Colonne(cle="etape", libelle="Étape", unite="texte"),
                          Colonne(cle="visiteurs", libelle="Visiteurs"),
                          Colonne(cle="passage", libelle="Passent à cette étape", unite="pourcent"),
                          Colonne(cle="abandon", libelle="Abandonnent avant", unite="pourcent")],
                lignes=lignes,
            )
        )  # fmt: skip
    motifs = [
        {"profil": NOMS_PROFILS.get(c[0].split(":")[0], c[0]), "motif": c[0].split(":", 1)[1], "nombre": n}
        for c, (n, _) in refus.items()
        if ":" in c[0] and "refuse-" in c[0]
    ]
    tableaux.append(
        Tableau(
            cle="refus", titre="Inscriptions refusées, par motif",
            colonnes=[Colonne(cle="profil", libelle="Profil", unite="texte"),
                      Colonne(cle="motif", libelle="Motif", unite="texte"), Colonne(cle="nombre", libelle="Refus")],
            lignes=_top(motifs, "nombre"),
        )
    )  # fmt: skip
    crees, crees_av = await _deux_periodes(p, lambda q: _comptes_crees(db, q))
    return _bloc(
        "inscription",
        p,
        chiffres=[
            Chiffre(cle="comptes_crees", libelle="Comptes créés", valeur=crees, precedent=crees_av),
            Chiffre(
                cle="clics",
                libelle="Clics « S'inscrire »",
                valeur=sum(n for n, _ in clics.values()),
                precedent=sum(n for n, _ in clics_av.values()),
            ),
            Chiffre(
                cle="conversion_eleves",
                libelle="Élèves : formulaire ouvert → compte créé",
                unite="pourcent",
                valeur=taux_conversion[0],
            ),
        ],
        tableaux=tableaux,
        notes=["« Comptes créés » vient des comptes en base ; l'entonnoir, des événements anonymes."],
    )


# 3. Jeux ---------------------------------------------------------------------------------------------------------


def _abandonnee() -> ColumnElement[bool]:
    """Une partie jamais finie : toujours en cours une heure après sa dernière réponse."""
    return and_(
        TentativeQuiz.etat == EtatTentative.en_cours,
        TentativeQuiz.derniere_activite < datetime.now(UTC) - timedelta(hours=1),
    )


def _parties(p: Periode, parcours: str) -> list[ColumnElement[bool]]:
    return [Quiz.parcours == parcours, TentativeQuiz.essai.is_(False), p.contient(TentativeQuiz.commencee_le)]


async def _comptes_parties(db: AsyncSession, q: Periode, parcours: str) -> dict[str, int]:
    ligne = (
        await db.execute(
            select(
                func.count(),
                func.count().filter(TentativeQuiz.etat == EtatTentative.terminee),
                func.count().filter(TentativeQuiz.reussie.is_(True)),
                func.count().filter(_abandonnee()),
                func.count(TentativeQuiz.joueur_id.distinct()),
            )
            .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
            .where(*_parties(q, parcours))
        )
    ).one()
    return dict(zip(("lancees", "terminees", "reussies", "en_cours", "joueurs"), map(int, ligne), strict=True))


async def jeux(db: AsyncSession, p: Periode) -> Bloc:
    actuel, avant = await _comptes_parties(db, p, "jeux"), await _comptes_parties(db, p.precedente, "jeux")
    par_jour = await db.execute(
        select(TentativeQuiz.jour, func.count(), func.count(TentativeQuiz.joueur_id.distinct()))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_parties(p, "jeux"))
        .group_by(TentativeQuiz.jour)
    )
    jours = par_jour.all()
    invites = await db.scalar(
        select(func.count(TentativeQuiz.joueur_id.distinct()))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .join(Utilisateur, Utilisateur.id == TentativeQuiz.joueur_id)
        .where(*_parties(p, "jeux"), Utilisateur.role == Role.invite)
    )
    niveaux = await db.execute(
        select(Quiz.niveau, func.count(), func.count().filter(TentativeQuiz.reussie.is_(True)))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_parties(p, "jeux"))
        .group_by(Quiz.niveau)
    )
    quiz = await db.execute(
        select(
            Quiz.numero, Quiz.titre, func.count(), func.count().filter(TentativeQuiz.reussie.is_(True)),
            func.count().filter(_abandonnee()),
        )
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_parties(p, "jeux"))
        .group_by(Quiz.id, Quiz.numero, Quiz.titre)
        .order_by(func.count().desc())
        .limit(15)
    )  # fmt: skip
    questions = await db.execute(
        select(QuestionQuiz.enonce, Quiz.numero, func.count(), func.count().filter(ReponseQuiz.correcte.is_(False)))
        .join(TentativeQuiz, TentativeQuiz.id == ReponseQuiz.tentative_id)
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .join(QuestionQuiz, QuestionQuiz.id == ReponseQuiz.question_id)
        .where(*_parties(p, "jeux"), ReponseQuiz.correcte.is_not(None))
        .group_by(QuestionQuiz.id, QuestionQuiz.enonce, Quiz.numero)
        .having(func.count() >= 5)
        .order_by((func.count().filter(ReponseQuiz.correcte.is_(False)) * 1.0 / func.count()).desc())
        .limit(10)
    )
    # Vies épuisées (spec 048) : un joueur, un jour, au moins 3 parties terminées sans réussite.
    echecs = (
        select(TentativeQuiz.joueur_id, TentativeQuiz.jour)
        .where(
            TentativeQuiz.essai.is_(False), p.contient(TentativeQuiz.commencee_le),
            TentativeQuiz.etat == EtatTentative.terminee, TentativeQuiz.reussie.is_not(True),
            # Comme `quiz/vies.py` : les invités sans compte n'ont pas de vies.
            TentativeQuiz.joueur_id.not_in(select(Utilisateur.id).where(Utilisateur.role == Role.invite)),
        )
        .group_by(TentativeQuiz.joueur_id, TentativeQuiz.jour)
        .having(func.count() >= 3)
        .subquery()
    )  # fmt: skip
    vies = await db.scalar(select(func.count()).select_from(echecs))
    defis = (
        await db.execute(
            select(func.count(), func.count(DefiReponse.eleve_id.distinct())).where(
                DefiReponse.jour >= p.du, DefiReponse.jour <= p.au
            )
        )
    ).one()
    return _bloc(
        "jeux",
        p,
        chiffres=[
            Chiffre(cle="lancees", libelle="Parties lancées", valeur=actuel["lancees"], precedent=avant["lancees"]),
            Chiffre(cle="reussies", libelle="Parties réussies", valeur=actuel["reussies"], precedent=avant["reussies"]),
            Chiffre(
                cle="taux_reussite",
                libelle="Taux de réussite",
                unite="pourcent",
                valeur=_taux(actuel["reussies"], actuel["terminees"]),
                precedent=_taux(avant["reussies"], avant["terminees"]),
            ),
            Chiffre(
                cle="abandons",
                libelle="Parties jamais finies",
                unite="pourcent",
                valeur=_taux(actuel["en_cours"], actuel["lancees"]),
                precedent=_taux(avant["en_cours"], avant["lancees"]),
            ),
            Chiffre(cle="joueurs", libelle="Joueurs", valeur=actuel["joueurs"], precedent=avant["joueurs"]),
            Chiffre(
                cle="invites",
                libelle="Joueurs sans compte",
                unite="pourcent",
                valeur=_taux(int(invites or 0), actuel["joueurs"]),
            ),
            Chiffre(cle="vies_epuisees", libelle="Fois où les 3 vies ont été perdues", valeur=int(vies or 0)),
            Chiffre(cle="defis", libelle="Défis du jour joués", valeur=int(defis[0])),
        ],
        series=[
            _serie_jours(p, {j: n for j, n, _ in jours}, "parties", "Parties lancées"),
            _serie_jours(p, {j: v for j, _, v in jours}, "joueurs", "Joueurs actifs"),
        ],
        tableaux=[
            Tableau(
                cle="niveaux",
                titre="Par niveau",
                colonnes=[
                    Colonne(cle="niveau", libelle="Niveau", unite="texte"),
                    Colonne(cle="lancees", libelle="Parties"),
                    Colonne(cle="reussite", libelle="Réussite", unite="pourcent"),
                ],
                lignes=[{"niveau": str(n or "—"), "lancees": t, "reussite": _taux(r, t)} for n, t, r in niveaux],
            ),
            Tableau(
                cle="quiz",
                titre="Les quiz les plus joués",
                colonnes=[
                    Colonne(cle="quiz", libelle="Quiz", unite="texte"),
                    Colonne(cle="lancees", libelle="Parties"),
                    Colonne(cle="reussite", libelle="Réussite", unite="pourcent"),
                    Colonne(cle="abandon", libelle="Jamais finies", unite="pourcent"),
                ],
                lignes=[
                    {"quiz": f"{numero or '—'}. {titre}", "lancees": t, "reussite": _taux(r, t), "abandon": _taux(a, t)}
                    for numero, titre, t, r, a in quiz
                ],
            ),
            Tableau(
                cle="questions",
                titre="Les questions les plus ratées (au moins 5 réponses)",
                colonnes=[
                    Colonne(cle="question", libelle="Question", unite="texte"),
                    Colonne(cle="quiz", libelle="Quiz", unite="texte"),
                    Colonne(cle="reponses", libelle="Réponses"),
                    Colonne(cle="ratees", libelle="Ratées", unite="pourcent"),
                ],
                lignes=[
                    {"question": e, "quiz": str(n or "—"), "reponses": t, "ratees": _taux(r, t)}
                    for e, n, t, r in questions
                ],
            ),
        ],
    )


# 4. Certification ------------------------------------------------------------------------------------------------


async def certification(db: AsyncSession, p: Periode) -> Bloc:
    actuel, avant = (
        await _comptes_parties(db, p, "certification"),
        await _comptes_parties(db, p.precedente, "certification"),
    )
    duree = extract("epoch", TentativeQuiz.terminee_le - TentativeQuiz.commencee_le)
    places = await db.execute(
        select(Quiz.place, func.count(), func.count().filter(TentativeQuiz.reussie.is_(True)),
               func.avg(duree).filter(TentativeQuiz.etat == EtatTentative.terminee))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_parties(p, "certification"), Quiz.place.is_not(None))
        .group_by(Quiz.place)
    )  # fmt: skip
    par_place = {place: (t, r, m) for place, t, r, m in places}
    atteintes = dict((await db.execute(select(PlaceReussie.place, func.count()).group_by(PlaceReussie.place))).all())
    lignes = []
    for place in range(1, 21):
        t, r, m = par_place.get(place, (0, 0, None))
        lignes.append(
            {"place": place, "candidats": int(atteintes.get(place, 0)), "tentatives": t, "echec": _taux(t - r, t),
             "temps": round(float(m)) if m is not None else None}
        )  # fmt: skip
    badges = await db.scalar(select(func.count()).select_from(BadgeObtenu).where(p.contient(BadgeObtenu.obtenu_le)))
    badges_av = await db.scalar(
        select(func.count()).select_from(BadgeObtenu).where(p.precedente.contient(BadgeObtenu.obtenu_le))
    )
    certificats = await db.scalar(select(func.count()).select_from(Certificat).where(p.contient(Certificat.delivre_le)))
    certificats_av = await db.scalar(
        select(func.count()).select_from(Certificat).where(p.precedente.contient(Certificat.delivre_le))
    )
    return _bloc(
        "certification",
        p,
        chiffres=[
            Chiffre(cle="candidats", libelle="Candidats actifs", valeur=actuel["joueurs"], precedent=avant["joueurs"]),
            Chiffre(cle="tentatives", libelle="Tentatives", valeur=actuel["lancees"], precedent=avant["lancees"]),
            Chiffre(
                cle="echec",
                libelle="Taux d'échec",
                unite="pourcent",
                valeur=_taux(actuel["terminees"] - actuel["reussies"], actuel["terminees"]),
                precedent=_taux(avant["terminees"] - avant["reussies"], avant["terminees"]),
            ),
            Chiffre(cle="badges", libelle="Badges délivrés", valeur=int(badges or 0), precedent=int(badges_av or 0)),
            Chiffre(
                cle="certificats",
                libelle="Certificats délivrés",
                valeur=int(certificats or 0),
                precedent=int(certificats_av or 0),
            ),
        ],
        tableaux=[
            Tableau(
                cle="places",
                titre="Les 20 quiz du parcours",
                colonnes=[
                    Colonne(cle="place", libelle="Quiz"),
                    Colonne(cle="candidats", libelle="Réussi par (depuis le début)"),
                    Colonne(cle="tentatives", libelle="Tentatives sur la période"),
                    Colonne(cle="echec", libelle="Échec", unite="pourcent"),
                    Colonne(cle="temps", libelle="Temps moyen", unite="secondes"),
                ],
                lignes=lignes,
            )
        ],
        notes=["« Réussi par » compte tous les candidats depuis le début : c'est l'entonnoir du parcours."],
    )


# 5. Contenus -----------------------------------------------------------------------------------------------------


async def contenus(db: AsyncSession, p: Periode) -> Bloc:
    fichiers = await evenements(db, p, TypeEvenement.telechargement, "detail")
    par_document: dict[str, dict[str, int]] = defaultdict(lambda: {"lire": 0, "telecharger": 0})
    for (detail,), (n, _) in fichiers.items():
        action, _, identifiant = detail.partition(":")
        if action in ("lire", "telecharger"):
            par_document[identifiant][action] += n
    identifiants = []
    for identifiant in par_document:
        with contextlib.suppress(ValueError):
            identifiants.append(UUID(identifiant))
    titres = {
        str(i): t
        for i, t in await db.execute(select(Ressource.id, Ressource.titre).where(Ressource.id.in_(identifiants)))
    }
    documents = [
        {"document": titres.get(i, "Document retiré"), "lectures": c["lire"], "telechargements": c["telecharger"]}
        for i, c in par_document.items()
    ]
    articles = await evenements(db, p, TypeEvenement.page_vue, "detail", chemin="/articles/$adresse")
    debuts = [c[0] for c in articles if c[0]]
    noms: dict[str, str] = {}
    if debuts:
        titre = VersionContenu.donnees["titre"].astext
        lignes = await db.execute(
            select(Contenu.adresse, titre)
            .join(VersionContenu, VersionContenu.id == Contenu.version_publiee_id)
            .where(func.left(Contenu.adresse, 60).in_(debuts))
        )
        noms = {adresse[:60]: t for adresse, t in lignes if adresse}
    partages = await db.scalar(
        select(func.count()).select_from(Contenu).where(Contenu.type == "partage", p.contient(Contenu.cree_le))
    )
    lectures = sum(c["lire"] + c["telecharger"] for c in par_document.values())
    lectures_av = sum(n for n, _ in (await evenements(db, p.precedente, TypeEvenement.telechargement)).values())
    return _bloc(
        "contenus",
        p,
        chiffres=[
            Chiffre(
                cle="documents",
                libelle="Lectures et téléchargements de la bibliothèque",
                valeur=lectures,
                precedent=lectures_av,
            ),
            Chiffre(cle="articles", libelle="Pages d'articles vues", valeur=sum(n for n, _ in articles.values())),
            Chiffre(cle="partages", libelle="Partages déclarés", valeur=int(partages or 0)),
        ],
        tableaux=[
            Tableau(
                cle="bibliotheque",
                titre="Bibliothèque",
                colonnes=[
                    Colonne(cle="document", libelle="Document", unite="texte"),
                    Colonne(cle="lectures", libelle="Lectures"),
                    Colonne(cle="telechargements", libelle="Téléchargements"),
                ],
                lignes=_top(documents, "lectures"),
            ),
            Tableau(
                cle="articles",
                titre="Articles les plus lus",
                colonnes=[
                    Colonne(cle="article", libelle="Article", unite="texte"),
                    Colonne(cle="vues", libelle="Vues"),
                    Colonne(cle="visiteurs", libelle="Visiteurs"),
                ],
                lignes=_top(
                    (
                        {"article": noms.get(c[0], c[0]), "vues": n, "visiteurs": v}
                        for c, (n, v) in articles.items()
                        if c[0]
                    ),
                    "vues",
                ),
            ),
        ],
    )


# 6. Régions et clubs ---------------------------------------------------------------------------------------------


def _dre_de_l_eleve() -> Any:
    return (
        select(Eleve.utilisateur_id, Iesg.dre_code)
        .join(Etablissement, Etablissement.id == Eleve.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .subquery()
    )


async def regions(db: AsyncSession, p: Periode) -> Bloc:
    eleves = _dre_de_l_eleve()
    inscrits = dict(
        (
            await db.execute(
                select(eleves.c.dre_code, func.count())
                .join(Utilisateur, Utilisateur.id == eleves.c.utilisateur_id)
                .where(p.contient(Utilisateur.cree_le))
                .group_by(eleves.c.dre_code)
            )
        ).all()
    )
    joueurs = dict(
        (
            await db.execute(
                select(eleves.c.dre_code, func.count(TentativeQuiz.joueur_id.distinct()))
                .join(TentativeQuiz, TentativeQuiz.joueur_id == eleves.c.utilisateur_id)
                .where(TentativeQuiz.essai.is_(False), p.contient(TentativeQuiz.commencee_le))
                .group_by(eleves.c.dre_code)
            )
        ).all()
    )
    certifies = dict(
        (
            await db.execute(
                select(eleves.c.dre_code, func.count())
                .join(Certificat, Certificat.utilisateur_id == eleves.c.utilisateur_id)
                .where(p.contient(Certificat.delivre_le))
                .group_by(eleves.c.dre_code)
            )
        ).all()
    )
    # Un club en service est dormant si aucun de ses membres actifs n'a joué dans les 30 jours avant la fin.
    recents = Periode(p.au - timedelta(days=29), p.au)
    actifs = (
        select(Adhesion.club_id)
        .join(TentativeQuiz, TentativeQuiz.joueur_id == Adhesion.eleve_id)
        .where(Adhesion.etat == EtatAdhesion.active, recents.contient(TentativeQuiz.commencee_le))
        .distinct()
    )
    clubs = await db.execute(
        select(Iesg.dre_code, func.count(), func.count().filter(Club.id.not_in(actifs)))
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .where(en_service(p.fin))
        .group_by(Iesg.dre_code)
    )
    par_club = {code: (n, d) for code, n, d in clubs}
    lignes = []
    for code, nom in await db.execute(select(Dre.code, Dre.nom).where(Dre.actif.is_(True)).order_by(Dre.ordre)):
        en_service_n, dormants = par_club.get(code, (0, 0))
        lignes.append(
            {"dre": nom, "inscrits": int(inscrits.get(code, 0)), "joueurs": int(joueurs.get(code, 0)),
             "certifies": int(certifies.get(code, 0)), "clubs": en_service_n, "dormants": dormants}
        )  # fmt: skip
    return _bloc(
        "regions",
        p,
        chiffres=[
            Chiffre(cle="clubs", libelle="Clubs en service", valeur=sum(int(r["clubs"]) for r in lignes)),
            Chiffre(
                cle="dormants", libelle="Clubs dormants (30 jours)", valeur=sum(int(r["dormants"]) for r in lignes)
            ),
        ],
        tableaux=[
            Tableau(
                cle="dre",
                titre="Par DRE",
                colonnes=[
                    Colonne(cle="dre", libelle="DRE", unite="texte"),
                    Colonne(cle="inscrits", libelle="Élèves inscrits"),
                    Colonne(cle="joueurs", libelle="Élèves qui jouent"),
                    Colonne(cle="certifies", libelle="Certifiés"),
                    Colonne(cle="clubs", libelle="Clubs en service"),
                    Colonne(cle="dormants", libelle="Clubs dormants"),
                ],
                lignes=lignes,
            )
        ],
        notes=["Un club est dormant quand aucun de ses membres n'a joué dans les 30 jours avant la fin de la période."],
    )


# 7. Rétention et moments d'usage ---------------------------------------------------------------------------------


def _lundi(jour: date) -> date:
    return jour - timedelta(days=jour.weekday())


def _grille(lignes: Iterable[tuple[Any, Any, Any]]) -> list[list[int]]:
    grille = [[0] * 24 for _ in range(7)]
    for jour_semaine, heure, nombre in lignes:
        # PostgreSQL : 0 = dimanche ; la grille commence le lundi.
        grille[(int(jour_semaine) + 6) % 7][int(heure)] = int(nombre)
    return grille


async def retention(db: AsyncSession, p: Periode, aujourdhui: date) -> Bloc:
    # Une seule requête : chaque cohorte (semaine d'inscription) jointe à ses présences 1 et 4 semaines après.
    semaine = func.date_trunc("week", Utilisateur.cree_le).cast(PresenceSemaine.semaine.type)
    comptes = (
        select(Utilisateur.id.label("id"), semaine.label("semaine"))
        .where(Utilisateur.role.in_(INSCRITS), p.contient(Utilisateur.cree_le))
        .subquery()
    )
    s1, s4 = aliased(PresenceSemaine), aliased(PresenceSemaine)
    cohortes = await db.execute(
        select(
            comptes.c.semaine, func.count(comptes.c.id.distinct()),
            func.count(s1.utilisateur_id.distinct()), func.count(s4.utilisateur_id.distinct()),
        )
        .select_from(comptes)
        .outerjoin(s1, and_(s1.utilisateur_id == comptes.c.id, s1.semaine == comptes.c.semaine + literal_column("7")))
        .outerjoin(s4, and_(s4.utilisateur_id == comptes.c.id, s4.semaine == comptes.c.semaine + literal_column("28")))
        .group_by(comptes.c.semaine)
        .order_by(comptes.c.semaine)
    )  # fmt: skip
    # Une semaine pas encore finie, ou déjà purgée (26 semaines), n'a pas de part : « — », pas 0 %.
    lundi_courant = _lundi(aujourdhui)
    horizon = lundi_courant - timedelta(weeks=PRESENCE_SEMAINES)

    def part(lundi: date, decalage: int, presents: int, taille: int) -> float | None:
        cible = lundi + timedelta(weeks=decalage)
        return None if cible >= lundi_courant or cible < horizon else _taux(presents, taille)

    lignes = [
        {"semaine": lundi.isoformat(), "inscrits": taille, "s1": part(lundi, 1, un, taille),
         "s4": part(lundi, 4, quatre, taille)}
        for lundi, taille, un, quatre in cohortes
    ]  # fmt: skip
    dow, heure = extract("dow", E.cree_le), extract("hour", E.cree_le)
    pages = await db.execute(
        select(dow, heure, func.count()).where(E.type == TypeEvenement.page_vue, E.jour >= p.du, E.jour <= p.au)
        .group_by(dow, heure)
    )  # fmt: skip
    dow_t, heure_t = extract("dow", TentativeQuiz.commencee_le), extract("hour", TentativeQuiz.commencee_le)
    parties = await db.execute(
        select(dow_t, heure_t, func.count())
        .where(TentativeQuiz.essai.is_(False), p.contient(TentativeQuiz.commencee_le))
        .group_by(dow_t, heure_t)
    )
    return _bloc(
        "retention",
        p,
        tableaux=[
            Tableau(
                cle="cohortes",
                titre="Reviennent après leur inscription",
                colonnes=[
                    Colonne(cle="semaine", libelle="Inscrits la semaine du", unite="texte"),
                    Colonne(cle="inscrits", libelle="Inscrits"),
                    Colonne(cle="s1", libelle="Actifs la semaine suivante", unite="pourcent"),
                    Colonne(cle="s4", libelle="Actifs 4 semaines après", unite="pourcent"),
                ],
                lignes=lignes,
            )
        ],
        grilles=[
            Grille(cle="pages", titre="Pages vues par jour et par heure", valeurs=_grille(pages)),
            Grille(cle="parties", titre="Parties lancées par jour et par heure", valeurs=_grille(parties)),
        ],
        notes=[
            "Un compte est actif une semaine s'il a ouvert le site connecté. Seules des parts s'affichent, jamais de nom.",
            "Les heures sont celles de Lomé ; les pages vues ne remontent pas au-delà de 90 jours.",
        ],
    )


# 8. Erreurs et recherches ----------------------------------------------------------------------------------------

SEUIL_RECHERCHE = 3


async def erreurs(db: AsyncSession, p: Periode) -> Bloc:
    introuvables = await evenements(db, p, TypeEvenement.erreur, "chemin", detail="404")
    serveur = await evenements(db, p, TypeEvenement.erreur, "jour", detail="500")
    routes = await evenements(db, p, TypeEvenement.erreur, "chemin", detail="500")
    recherches = await evenements(db, p, TypeEvenement.recherche, "chemin", "detail")
    rares = [
        {"recherche": d, "page": c, "visiteurs": v} for (c, d), (_, v) in recherches.items() if v >= SEUIL_RECHERCHE
    ]
    return _bloc(
        "erreurs",
        p,
        chiffres=[
            Chiffre(
                cle="introuvables", libelle="Pages introuvables vues", valeur=sum(n for n, _ in introuvables.values())
            ),
            Chiffre(cle="serveur", libelle="Erreurs du serveur", valeur=sum(n for n, _ in serveur.values())),
        ],
        series=[_serie_jours(p, {c[0]: n for c, (n, _) in serveur.items()}, "serveur", "Erreurs du serveur")],
        tableaux=[
            Tableau(
                cle="introuvables",
                titre="Pages introuvables les plus demandées",
                colonnes=[
                    Colonne(cle="chemin", libelle="Adresse", unite="texte"),
                    Colonne(cle="vues", libelle="Vues"),
                    Colonne(cle="visiteurs", libelle="Visiteurs"),
                ],
                lignes=_top(
                    ({"chemin": c[0], "vues": n, "visiteurs": v} for c, (n, v) in introuvables.items()), "vues"
                ),
            ),
            Tableau(
                cle="routes",
                titre="Erreurs du serveur, par route de l'API",
                colonnes=[
                    Colonne(cle="route", libelle="Route", unite="texte"),
                    Colonne(cle="nombre", libelle="Erreurs"),
                ],
                lignes=_top(({"route": c[0], "nombre": n} for c, (n, _) in routes.items()), "nombre"),
            ),
            Tableau(
                cle="recherches",
                titre="Recherches sans résultat",
                colonnes=[
                    Colonne(cle="recherche", libelle="Recherche", unite="texte"),
                    Colonne(cle="page", libelle="Page", unite="texte"),
                    Colonne(cle="visiteurs", libelle="Visiteurs"),
                ],
                lignes=_top(rares, "visiteurs", 30),
            ),
        ],
        notes=[f"Une recherche ne s'affiche qu'à partir de {SEUIL_RECHERCHE} visiteurs différents."],
    )


# Aiguillage ------------------------------------------------------------------------------------------------------


async def calculer(db: AsyncSession, bloc: NomBloc, p: Periode, aujourdhui: date) -> Bloc:
    if bloc == "retention":
        return await retention(db, p, aujourdhui)
    fonctions: dict[str, Callable[[AsyncSession, Periode], Awaitable[Bloc]]] = {
        "audience": audience, "inscription": inscription, "jeux": jeux, "certification": certification,
        "contenus": contenus, "regions": regions, "erreurs": erreurs,
    }  # fmt: skip
    return await fonctions[bloc](db, p)
