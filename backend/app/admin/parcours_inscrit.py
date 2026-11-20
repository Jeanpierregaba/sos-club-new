"""Fiche complète d'un inscrit (spec 045), en lecture seule : points, quiz, certification et contenus.

Chaque liste est paginée en SQL. Les temps (spec 046) sont des agrégats SQL : le temps de jeu d'une tentative va de
son début à sa dernière activité, car une partie abandonnée n'est close qu'au retour du joueur.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Numeric, Select, and_, case, func, or_, select
from sqlalchemy.dialects.postgresql import ARRAY, aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.schemas import (
    BadgeAdmin,
    CertificatAdmin,
    CertificationInscrit,
    ContenuAdmin,
    DetailTentative,
    PageContenusInscrit,
    PageTentatives,
    PlaceAdmin,
    PointsInscrit,
    QuestionTentative,
    QuizInscrit,
    QuizValide,
    ResumeQuiz,
    SemestreInscrit,
    TentativeAdmin,
    TotauxInscrit,
)
from app.certification.models import BadgeObtenu, Certificat, PlaceReussie
from app.comptes.models import Role, Utilisateur
from app.moderation.models import Contenu, EtatContenu, VersionContenu
from app.moderation.types import TYPES
from app.points import registre
from app.points import service as points
from app.points.models import MouvementPoints, Semestre
from app.points.schemas import LigneRegistre, PageRegistre
from app.quiz.models import (
    PARCOURS_CERTIFICATION,
    PLACES,
    EtatTentative,
    ParametresQuiz,
    QuestionQuiz,
    Quiz,
    ReponseQuiz,
    TentativeQuiz,
)
from app.quiz.partie import INACTIVITE
from app.referentiel.models import Axe

PAR_PAGE_POINTS = 50
PAR_PAGE = 25
LONGUEUR_EXTRAIT = 80
# Repères de la spec 046 : la moyenne des autres joueurs ne s'affiche qu'à partir de cet effectif, et une première
# réussite en moins de cette fraction de la moyenne est marquée « Très rapide ».
EFFECTIF_MOYENNE = 5
FRACTION_TRES_RAPIDE = 0.5

TEMPS_DE_JEU = func.greatest(func.extract("epoch", TentativeQuiz.derniere_activite - TentativeQuiz.commencee_le), 0)


class Introuvable(Exception):
    pass


async def verifier(db: AsyncSession, utilisateur_id: UUID) -> Utilisateur:
    """Un élève ou un encadreur : ni un collaborateur, ni un visiteur, ni un joueur sans compte (spec 045)."""
    utilisateur = await db.get(Utilisateur, utilisateur_id)
    if utilisateur is None or utilisateur.role not in (Role.eleve, Role.encadreur):
        raise Introuvable
    return utilisateur


# Points -------------------------------------------------------------------------------------------------------


async def points_de(db: AsyncSession, utilisateur_id: UUID, semestre_id: UUID | None, page: int) -> PointsInscrit:
    await verifier(db, utilisateur_id)
    calcul = await points.totaux(db, utilisateur_id)
    filtres = registre.FiltresRegistre(utilisateur_id=utilisateur_id, semestre_id=semestre_id)
    resultat = await registre.lister(db, filtres, page, PAR_PAGE_POINTS)
    semestres = await db.execute(
        select(Semestre.id, Semestre.libelle)
        .where(
            Semestre.id.in_(select(MouvementPoints.semestre_id).where(MouvementPoints.utilisateur_id == utilisateur_id))
        )
        .order_by(Semestre.debut.desc())
    )
    return PointsInscrit(
        totaux=TotauxInscrit(
            semestre=calcul.semestre.libelle if calcul.semestre else None,
            points_semestre=calcul.points_semestre,
            total=calcul.total,
        ),
        semestres=[SemestreInscrit(id=r.id, libelle=r.libelle) for r in semestres.all()],
        registre=PageRegistre(
            total=resultat.total,
            page=page,
            par_page=PAR_PAGE_POINTS,
            lignes=[LigneRegistre(**ligne) for ligne in resultat.lignes],
        ),
    )


# Quiz ---------------------------------------------------------------------------------------------------------


def _tentatives_de(utilisateur_id: UUID) -> Select[Any]:
    return (
        select(
            TentativeQuiz,
            Quiz.titre,
            Quiz.parcours,
            Quiz.place,
            Quiz.niveau,
            Axe.libelle.label("axe"),
            ParametresQuiz.nb_questions,
            MouvementPoints.montant.label("points"),
        )
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .join(Axe, Axe.code == Quiz.axe_code)
        .join(ParametresQuiz, ParametresQuiz.id == TentativeQuiz.parametres_id)
        .outerjoin(MouvementPoints, MouvementPoints.id == TentativeQuiz.mouvement_id)
        .where(TentativeQuiz.joueur_id == utilisateur_id)
    )


async def quiz_de(
    db: AsyncSession, utilisateur_id: UUID, parcours: str | None, resultat: str | None, page: int
) -> QuizInscrit:
    await verifier(db, utilisateur_id)
    compte = and_(
        TentativeQuiz.joueur_id == utilisateur_id,
        TentativeQuiz.etat == EtatTentative.terminee,
        TentativeQuiz.essai.is_(False),
    )
    resume = (
        await db.execute(
            select(
                func.count(func.distinct(TentativeQuiz.quiz_id)).filter(TentativeQuiz.reussie.is_(True)),
                func.count(),
                func.count().filter(TentativeQuiz.reussie.is_(False)),
                func.coalesce(func.sum(MouvementPoints.montant), 0),
                func.coalesce(func.sum(TEMPS_DE_JEU), 0),
                func.coalesce(func.avg(TEMPS_DE_JEU), 0),
            )
            .select_from(TentativeQuiz)
            .outerjoin(MouvementPoints, MouvementPoints.id == TentativeQuiz.mouvement_id)
            .where(compte)
        )
    ).one()

    reussies = and_(compte, TentativeQuiz.reussie.is_(True))
    valides = await db.execute(
        select(
            Quiz.id,
            Quiz.titre,
            Axe.libelle,
            Quiz.parcours,
            Quiz.place,
            Quiz.niveau,
            func.min(TentativeQuiz.terminee_le),
            func.max(TentativeQuiz.score),
            func.max(ParametresQuiz.nb_questions),
            func.count(),
            func.coalesce(func.sum(MouvementPoints.montant), 0),
            func.array_agg(aggregate_order_by(TEMPS_DE_JEU, TentativeQuiz.terminee_le), type_=ARRAY(Numeric))[1],
        )
        .select_from(TentativeQuiz)
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .join(Axe, Axe.code == Quiz.axe_code)
        .join(ParametresQuiz, ParametresQuiz.id == TentativeQuiz.parametres_id)
        .outerjoin(MouvementPoints, MouvementPoints.id == TentativeQuiz.mouvement_id)
        .where(reussies)
        .group_by(Quiz.id, Axe.libelle)
        .order_by(func.min(TentativeQuiz.terminee_le).desc())
    )
    valides_rangees = valides.all()
    moyennes = await _moyennes_nationales(db, utilisateur_id, [r[0] for r in valides_rangees])

    requete = _tentatives_de(utilisateur_id)
    if parcours:
        requete = requete.where(Quiz.parcours == parcours)
    if resultat == "reussies":
        requete = requete.where(TentativeQuiz.reussie.is_(True))
    elif resultat == "echouees":
        requete = requete.where(TentativeQuiz.reussie.is_(False))
    total = int(await db.scalar(select(func.count()).select_from(requete.subquery())) or 0)
    rangees = await db.execute(
        requete.order_by(TentativeQuiz.commencee_le.desc(), TentativeQuiz.id.desc())
        .limit(PAR_PAGE)
        .offset((page - 1) * PAR_PAGE)
    )

    return QuizInscrit(
        resume=ResumeQuiz(
            quiz_valides=resume[0],
            tentatives=resume[1],
            echecs=resume[2],
            points=resume[3],
            temps_total_s=round(resume[4]),
            temps_moyen_s=round(resume[5]),
        ),
        valides=[_valide(r, moyennes.get(r[0])) for r in valides_rangees],
        tentatives=PageTentatives(
            total=total, page=page, par_page=PAR_PAGE, tentatives=[_tentative(r) for r in rangees.all()]
        ),
    )


async def _moyennes_nationales(db: AsyncSession, utilisateur_id: UUID, quiz_ids: list[UUID]) -> dict[UUID, Any]:
    """Temps de jeu moyen des réussites des autres joueurs, hors essais, sur chaque quiz demandé."""
    if not quiz_ids:
        return {}
    rangees = await db.execute(
        select(TentativeQuiz.quiz_id, func.avg(TEMPS_DE_JEU), func.count())
        .where(
            TentativeQuiz.quiz_id.in_(quiz_ids),
            TentativeQuiz.joueur_id != utilisateur_id,
            TentativeQuiz.essai.is_(False),
            TentativeQuiz.etat == EtatTentative.terminee,
            TentativeQuiz.reussie.is_(True),
        )
        .group_by(TentativeQuiz.quiz_id)
    )
    return {r[0]: r for r in rangees.all()}


def _valide(r: Any, national: Any) -> QuizValide:
    temps = round(r[11] or 0)
    effectif = national[2] if national is not None else 0
    moyenne = round(national[1]) if national is not None and effectif >= EFFECTIF_MOYENNE else None
    return QuizValide(
        quiz_id=r[0],
        titre=r[1],
        axe=r[2],
        parcours=r[3],
        place=r[4],
        niveau=_valeur(r[5]),
        premiere_reussite=r[6],
        meilleur_score=r[7] or 0,
        nb_questions=r[8],
        reussites=r[9],
        points=r[10],
        temps_premiere_reussite_s=temps,
        moyenne_nationale_s=moyenne,
        reussites_nationales=effectif,
        tres_rapide=moyenne is not None and temps < moyenne * FRACTION_TRES_RAPIDE,
    )


def _valeur(valeur: Any) -> Any:
    return getattr(valeur, "value", valeur)


def _tentative(rangee: Any) -> TentativeAdmin:
    tentative: TentativeQuiz = rangee.TentativeQuiz
    duree = max(0, round((tentative.derniere_activite - tentative.commencee_le).total_seconds()))
    # Close au retour du joueur, longtemps après sa dernière action : la partie avait été quittée.
    abandonnee = tentative.terminee_le is not None and tentative.terminee_le - tentative.derniere_activite > INACTIVITE
    return TentativeAdmin(
        id=tentative.id,
        quiz_titre=rangee.titre,
        axe=rangee.axe,
        parcours=rangee.parcours,
        place=rangee.place,
        niveau=_valeur(rangee.niveau),
        commencee_le=tentative.commencee_le,
        terminee_le=tentative.terminee_le,
        etat=tentative.etat.value,
        essai=tentative.essai,
        score=tentative.score,
        nb_questions=rangee.nb_questions,
        reussie=tentative.reussie,
        duree_s=duree,
        abandonnee=abandonnee,
        points=rangee.points,
    )


async def tentative_de(db: AsyncSession, utilisateur_id: UUID, tentative_id: UUID) -> DetailTentative:
    """Les questions d'une tentative de l'inscrit, dans l'ordre, avec le temps mis sur chacune."""
    await verifier(db, utilisateur_id)
    rangee = (await db.execute(_tentatives_de(utilisateur_id).where(TentativeQuiz.id == tentative_id))).first()
    if rangee is None:
        raise Introuvable
    tentative: TentativeQuiz = rangee.TentativeQuiz
    temps_ms = await db.scalar(select(ParametresQuiz.temps_ms).where(ParametresQuiz.id == tentative.parametres_id))
    imparti = (temps_ms or 0) / 1000
    lignes = await db.execute(
        select(ReponseQuiz, QuestionQuiz.enonce, QuestionQuiz.choix)
        .join(QuestionQuiz, QuestionQuiz.id == ReponseQuiz.question_id)
        .where(ReponseQuiz.tentative_id == tentative.id)
        .order_by(ReponseQuiz.rang)
    )
    return DetailTentative(
        tentative=_tentative(rangee),
        temps_imparti_s=imparti,
        questions=[_question(r.ReponseQuiz, r.enonce, r.choix, tentative, imparti) for r in lignes.all()],
    )


def _question(
    ligne: ReponseQuiz, enonce: str, choix: list[str], tentative: TentativeQuiz, imparti: float
) -> QuestionTentative:
    if ligne.envoyee_le is None:
        return QuestionTentative(rang=ligne.rang, enonce=enonce, etat="non_posee", reponse=None, secondes=None)
    if ligne.choix is not None:
        # Aux jeux, la question suivante est envoyée après la pause de correction : son heure d'envoi peut dépasser
        # légèrement celle de la réponse, d'où la borne à 0.
        fin = ligne.repondue_le or ligne.envoyee_le
        secondes = round(max(0.0, (fin - ligne.envoyee_le).total_seconds()), 1)
        return QuestionTentative(
            rang=ligne.rang, enonce=enonce, etat="juste" if ligne.correcte else "fausse",
            reponse=choix[ligne.choix] if ligne.choix < len(choix) else None, secondes=secondes,
        )  # fmt: skip
    if ligne.correcte is None and tentative.etat is EtatTentative.en_cours:
        return QuestionTentative(rang=ligne.rang, enonce=enonce, etat="en_cours", reponse=None, secondes=None)
    # Pas de réponse dans le temps imparti (ou réponse arrivée trop tard) : la question vaut le temps imparti.
    return QuestionTentative(rang=ligne.rang, enonce=enonce, etat="temps_ecoule", reponse=None, secondes=imparti)


# Certification ------------------------------------------------------------------------------------------------


async def certification_de(db: AsyncSession, utilisateur_id: UUID) -> CertificationInscrit:
    await verifier(db, utilisateur_id)
    reussies = {
        r.place: r
        for r in (
            await db.execute(
                select(PlaceReussie.place, PlaceReussie.reussie_le, Quiz.titre)
                .join(Quiz, Quiz.id == PlaceReussie.quiz_id)
                .where(PlaceReussie.utilisateur_id == utilisateur_id)
            )
        ).all()
    }
    temps_places = await _temps_des_places(db, utilisateur_id)
    places = [
        PlaceAdmin(
            place=place,
            reussie_le=reussies[place].reussie_le if place in reussies else None,
            quiz_titre=reussies[place].titre if place in reussies else None,
            temps_s=temps_places.get(place, (0, 0))[0],
            tentatives=temps_places.get(place, (0, 0))[1],
        )
        for place in range(1, PLACES + 1)
    ]
    premiere = await db.scalar(
        select(func.min(TentativeQuiz.commencee_le))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_certification(utilisateur_id))
    )

    badges: list[BadgeAdmin] = []
    precedent: datetime | None = None
    for b in (
        await db.scalars(
            select(BadgeObtenu)
            .where(BadgeObtenu.utilisateur_id == utilisateur_id)
            .order_by(BadgeObtenu.obtenu_le, BadgeObtenu.rang)
        )
    ).all():
        badges.append(
            BadgeAdmin(
                rang=b.rang, nom=b.nom, palier=b.palier, obtenu_le=b.obtenu_le,
                temps_s=await _temps_certification(db, utilisateur_id, precedent, b.obtenu_le),
                temps_cumule_s=await _temps_certification(db, utilisateur_id, None, b.obtenu_le),
                duree_calendaire_s=_ecart(precedent or premiere, b.obtenu_le),
            )
        )  # fmt: skip
        precedent = b.obtenu_le
    badges.sort(key=lambda badge: badge.rang)

    certificats = await db.scalars(
        select(Certificat).where(Certificat.utilisateur_id == utilisateur_id).order_by(Certificat.delivre_le.desc())
    )
    return CertificationInscrit(
        places=places,
        badges=badges,
        certificats=[
            CertificatAdmin(
                numero=c.numero,
                etat=c.etat.value,
                delivre_le=c.delivre_le,
                titulaire=f"{c.titulaire_prenom} {c.titulaire_nom}",
                motif=c.motif,
                decide_le=c.decide_le,
                temps_cumule_s=await _temps_certification(db, utilisateur_id, None, c.delivre_le),
                duree_calendaire_s=_ecart(premiere, c.delivre_le),
            )
            for c in certificats.all()
        ],
    )


def _certification(utilisateur_id: UUID) -> tuple[ColumnElement[bool], ...]:
    """Les tentatives de certification de l'inscrit, hors essais (à joindre à Quiz)."""
    return (
        TentativeQuiz.joueur_id == utilisateur_id,
        TentativeQuiz.essai.is_(False),
        Quiz.parcours == PARCOURS_CERTIFICATION,
    )


async def _temps_des_places(db: AsyncSession, utilisateur_id: UUID) -> dict[int, tuple[int, int]]:
    """Temps de jeu et nombre de tentatives par place, sur tous les quiz qui l'ont occupée, jusqu'à la tentative
    réussie incluse : ce qui est rejoué après ne compte pas pour la place."""
    reussite = aliased(TentativeQuiz)
    rangees = await db.execute(
        select(Quiz.place, func.coalesce(func.sum(TEMPS_DE_JEU), 0), func.count())
        .select_from(TentativeQuiz)
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .outerjoin(
            PlaceReussie, and_(PlaceReussie.utilisateur_id == TentativeQuiz.joueur_id, PlaceReussie.place == Quiz.place)
        )
        .outerjoin(reussite, reussite.id == PlaceReussie.tentative_id)
        .where(
            *_certification(utilisateur_id),
            Quiz.place.is_not(None),
            or_(reussite.id.is_(None), TentativeQuiz.commencee_le <= reussite.commencee_le),
        )
        .group_by(Quiz.place)
    )
    return {r[0]: (round(r[1]), r[2]) for r in rangees.all()}


async def _temps_certification(db: AsyncSession, utilisateur_id: UUID, apres: datetime | None, jusqua: datetime) -> int:
    """Temps de jeu des tentatives de certification commencées dans ]apres ; jusqua]."""
    requete = (
        select(func.coalesce(func.sum(TEMPS_DE_JEU), 0))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_certification(utilisateur_id), TentativeQuiz.commencee_le <= jusqua)
    )
    if apres is not None:
        requete = requete.where(TentativeQuiz.commencee_le > apres)
    return round(await db.scalar(requete) or 0)


def _ecart(debut: datetime | None, fin: datetime) -> int | None:
    if debut is None or debut > fin:
        return None
    return round((fin - debut).total_seconds())


# Contenus -----------------------------------------------------------------------------------------------------


def _type_libelle(code: str) -> str:
    """« l'article » devient « Article » ; un type inconnu garde son code."""
    type_contenu = TYPES.get(code)
    if type_contenu is None:
        return code
    libelle = type_contenu.libelle
    for article in ("l'", "l’", "le ", "la ", "les ", "un ", "une "):
        if libelle.lower().startswith(article):
            libelle = libelle[len(article) :]
            break
    return libelle[:1].upper() + libelle[1:]


def _titre(code: str, donnees: dict[str, Any] | None) -> str:
    if not donnees:
        return "Sans titre"
    type_contenu = TYPES.get(code)
    try:
        titre = type_contenu.titre(donnees) if type_contenu else ""
    except KeyError, TypeError, ValueError:
        titre = ""
    if not titre:
        texte = donnees.get("titre") or donnees.get("texte") or ""
        titre = str(texte)
    titre = " ".join(titre.split())
    return titre if len(titre) <= LONGUEUR_EXTRAIT else titre[: LONGUEUR_EXTRAIT - 1] + "…"


async def contenus_de(
    db: AsyncSession, utilisateur_id: UUID, type_: str | None, etat: EtatContenu | None, page: int
) -> PageContenusInscrit:
    await verifier(db, utilisateur_id)
    # La version la plus récente : celle en travail, sinon la publiée.
    requete = (
        select(Contenu, VersionContenu.donnees)
        .outerjoin(
            VersionContenu,
            VersionContenu.id
            == case(
                (Contenu.version_travail_id.is_not(None), Contenu.version_travail_id),
                else_=Contenu.version_publiee_id,
            ),
        )
        .where(Contenu.auteur_id == utilisateur_id)
    )
    if type_:
        requete = requete.where(Contenu.type == type_)
    if etat is not None:
        requete = requete.where(Contenu.etat == etat)
    total = int(await db.scalar(select(func.count()).select_from(requete.subquery())) or 0)
    rangees = await db.execute(
        requete.order_by(Contenu.cree_le.desc(), Contenu.id.desc()).limit(PAR_PAGE).offset((page - 1) * PAR_PAGE)
    )
    return PageContenusInscrit(
        total=total,
        page=page,
        par_page=PAR_PAGE,
        contenus=[
            ContenuAdmin(
                id=c.id,
                type=c.type,
                type_libelle=_type_libelle(c.type),
                titre=_titre(c.type, donnees),
                etat=c.etat.value,
                cree_le=c.cree_le,
                publie_le=c.publie_le,
            )
            for c, donnees in rangees.all()
        ],
    )
