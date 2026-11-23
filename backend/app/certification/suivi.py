"""Suivi des certifications par l'équipe (spec 043) : les candidats, l'entonnoir des 20 places, les chiffres par DRE
et par semaine, et l'export nominatif.

Un candidat est un élève ou un encadreur qui a joué au moins une partie de certification (hors parties d'essai des
collaborateurs). Tout est calculé à partir des tables du parcours (`tentative_quiz`, `place_reussie`,
`badge_obtenu`, `certificat`) : aucune table de compteurs à tenir à jour.

Un collaborateur de DRE ne voit que les candidats de sa DRE (celle de l'établissement de l'élève ou de l'encadreur),
et les élèves par leur pseudonyme seulement (RULES) ; l'export nominatif est national (SECURITY).
"""

import csv
import io
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import Select, and_, case, func, literal_column, or_, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.exports import neutraliser
from app.admin.journal import journaliser
from app.certification import regles
from app.certification.models import BadgeObtenu, Certificat, EtatCertificat, PlaceReussie
from app.certification.schemas import (
    BadgeCompte,
    CandidatCertification,
    ClubCandidat,
    FiltresCandidats,
    LigneDre,
    LigneEntonnoir,
    LigneSemaine,
    PageCandidats,
    StatistiquesCertification,
    TotauxCertification,
)
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.config import settings
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.quiz.models import PARCOURS_CERTIFICATION, PLACES, EtatQuiz, Quiz, TentativeQuiz
from app.referentiel.models import Dre, Etablissement, Iesg

INACTIF = timedelta(days=30)
SEMAINES = 12
ENTETES = [
    "Nom", "Pseudonyme", "Rôle", "Club", "Établissement", "DRE", "Places validées", "Badges", "Place en cours",
    "Tentatives sur la place", "Tentatives", "Début", "Dernière activité", "Certificat",
]  # fmt: skip


def voit_les_noms(acces: Acces) -> bool:
    """Le nom réel d'un élève (souvent mineur) : seulement pour un collaborateur national dont la double
    authentification est active, comme les autres lectures nominatives sensibles (RULES, catalogue des droits).
    Les autres voient son pseudonyme ; un encadreur reste nommé."""
    return acces.national and acces.double_auth_active


def nom_affiche(acces: Acces, role: Role | str, prenom: str, nom: str, pseudonyme: str | None) -> str:
    if Role(role) is not Role.eleve or voit_les_noms(acces):
        return f"{prenom} {nom}"
    return pseudonyme or "Élève"


def comptes_de_la_dre(code: str) -> Any:
    """Les élèves et les encadreurs dont l'établissement est dans la DRE."""

    def du_lieu(colonne_id: Any, colonne_lieu: Any) -> Select:
        return (
            select(colonne_id)
            .join(Etablissement, Etablissement.id == colonne_lieu)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .where(Iesg.dre_code == code)
        )

    return du_lieu(Eleve.utilisateur_id, Eleve.etablissement_id).union(
        du_lieu(Encadreur.utilisateur_id, Encadreur.etablissement_id)
    )


def _tentatives() -> Select:
    """Les parties de certification qui comptent : ni partie d'essai, ni autre parcours."""
    return (
        select(TentativeQuiz)
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(Quiz.parcours == PARCOURS_CERTIFICATION, TentativeQuiz.essai.is_(False))
    )


def _candidats(acces: Acces) -> Select:
    """Une ligne par candidat du périmètre du collaborateur, avec tout ce que la liste et les chiffres lisent."""
    t = (
        _tentatives()
        .with_only_columns(
            TentativeQuiz.joueur_id.label("uid"),
            func.min(TentativeQuiz.commencee_le).label("debut"),
            func.max(TentativeQuiz.derniere_activite).label("derniere"),
            func.count().label("tentatives"),
        )
        .group_by(TentativeQuiz.joueur_id)
        .subquery("t")
    )
    places = (
        select(PlaceReussie.utilisateur_id.label("uid"), func.count().label("n"))
        .group_by(PlaceReussie.utilisateur_id)
        .subquery("places")
    )
    badges = (
        select(
            BadgeObtenu.utilisateur_id.label("uid"),
            func.array_agg(aggregate_order_by(BadgeObtenu.rang, BadgeObtenu.rang)).label("rangs"),
            func.count().label("n"),
        )
        .group_by(BadgeObtenu.utilisateur_id)
        .subquery("badges")
    )
    certificat = (
        select(Certificat.utilisateur_id.label("uid"), Certificat.numero)
        .where(Certificat.etat == EtatCertificat.valide)
        .subquery("certificat")
    )
    adhesion = (
        select(Adhesion.eleve_id.label("uid"), Adhesion.club_id)
        .where(Adhesion.etat == EtatAdhesion.active)
        .subquery("adhesion")
    )
    rattachement = (
        select(Rattachement.encadreur_id.label("uid"), Rattachement.club_id)
        .where(Rattachement.etat == EtatRattachement.actif)
        .subquery("rattachement")
    )
    nb_places = func.coalesce(places.c.n, 0)
    place_en_cours = case((nb_places < PLACES, nb_places + 1), else_=None)
    tentatives_place = (
        _tentatives()
        .with_only_columns(func.count())
        .where(TentativeQuiz.joueur_id == t.c.uid, Quiz.place == place_en_cours)
        .scalar_subquery()
    )
    requete = (
        select(
            t.c.uid,
            t.c.debut,
            t.c.derniere,
            t.c.tentatives,
            Utilisateur.role,
            Utilisateur.prenom,
            Utilisateur.nom,
            Utilisateur.ancien_eleve_le,
            Eleve.pseudonyme,
            Club.id.label("club_id"),
            Club.nom.label("club_nom"),
            Etablissement.nom.label("etablissement"),
            Dre.code.label("dre_code"),
            Dre.nom.label("dre_nom"),
            nb_places.label("places"),
            badges.c.rangs.label("badges"),
            func.coalesce(badges.c.n, 0).label("nb_badges"),
            certificat.c.numero.label("certificat"),
            place_en_cours.label("place_en_cours"),
            tentatives_place.label("tentatives_place"),
        )
        .select_from(t)
        .join(Utilisateur, Utilisateur.id == t.c.uid)
        .outerjoin(Eleve, Eleve.utilisateur_id == t.c.uid)
        .outerjoin(Encadreur, Encadreur.utilisateur_id == t.c.uid)
        .outerjoin(Etablissement, Etablissement.id == func.coalesce(Eleve.etablissement_id, Encadreur.etablissement_id))
        .outerjoin(Iesg, Iesg.id == Etablissement.iesg_id)
        .outerjoin(Dre, Dre.code == Iesg.dre_code)
        .outerjoin(adhesion, adhesion.c.uid == t.c.uid)
        .outerjoin(rattachement, rattachement.c.uid == t.c.uid)
        .outerjoin(Club, Club.id == func.coalesce(adhesion.c.club_id, rattachement.c.club_id))
        .outerjoin(places, places.c.uid == t.c.uid)
        .outerjoin(badges, badges.c.uid == t.c.uid)
        .outerjoin(certificat, certificat.c.uid == t.c.uid)
        .where(Utilisateur.role.in_([Role.eleve, Role.encadreur]))
    )
    if not acces.national:
        requete = requete.where(Dre.code == acces.collaborateur.perimetre_dre)
    return requete


def _filtrer(requete: Select, acces: Acces, filtres: FiltresCandidats, instant: datetime) -> Select:
    c = requete.selected_columns
    if filtres.dre:
        requete = requete.where(c.dre_code == filtres.dre)
    if filtres.club_id:
        requete = requete.where(c.club_id == filtres.club_id)
    if filtres.role:
        requete = requete.where(c.role == Role(filtres.role))
    if filtres.etat == "certifie":
        requete = requete.where(c.certificat.is_not(None))
    elif filtres.etat == "inactif":
        requete = requete.where(c.certificat.is_(None), c.derniere < instant - INACTIF)
    elif filtres.etat == "en_cours":
        requete = requete.where(c.certificat.is_(None), c.derniere >= instant - INACTIF)
    if filtres.recherche:
        # Les jokers de LIKE sont échappés : « 100% » cherche « 100% », pas tout.
        echappe = filtres.recherche.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        motif = f"%{echappe}%"
        nom_complet = func.concat(c.prenom, " ", c.nom)
        # Le nom réel d'un élève n'est cherchable que par ceux qui peuvent le voir ; sinon, son pseudonyme seulement.
        nom_cherchable = nom_complet.ilike(motif, escape="\\")
        if not voit_les_noms(acces):
            nom_cherchable = and_(c.role == Role.encadreur, nom_cherchable)
        requete = requete.where(or_(c.pseudonyme.ilike(motif, escape="\\"), nom_cherchable))
    return requete


def _candidat(ligne: Any, acces: Acces) -> CandidatCertification:
    eleve = ligne.role is Role.eleve
    nom = nom_affiche(acces, ligne.role, ligne.prenom, ligne.nom, ligne.pseudonyme)
    return CandidatCertification(
        id=ligne.uid,
        nom=nom,
        pseudonyme=ligne.pseudonyme,
        role="eleve" if eleve else "encadreur",
        ancien_eleve=ligne.ancien_eleve_le is not None,
        club=ClubCandidat(id=ligne.club_id, nom=ligne.club_nom) if ligne.club_id else None,
        etablissement=ligne.etablissement,
        dre=ligne.dre_nom,
        places_validees=ligne.places,
        badges=list(ligne.badges or []),
        place_en_cours=None if ligne.certificat else ligne.place_en_cours,
        tentatives_place=ligne.tentatives_place if ligne.place_en_cours and not ligne.certificat else 0,
        tentatives=ligne.tentatives,
        debut=ligne.debut,
        derniere_activite=ligne.derniere,
        certificat=ligne.certificat,
    )


def _trier(requete: Select) -> Select:
    c = requete.selected_columns
    return requete.order_by(c.derniere.desc(), c.uid)


async def lister(
    db: AsyncSession, acces: Acces, filtres: FiltresCandidats, *, page: int = 1, par_page: int = 50
) -> PageCandidats:
    requete = _filtrer(_candidats(acces), acces, filtres, datetime.now(UTC))
    total = await db.scalar(select(func.count()).select_from(requete.subquery()))
    lignes = (await db.execute(_trier(requete).offset((page - 1) * par_page).limit(par_page))).all()
    return PageCandidats(total=total or 0, candidats=[_candidat(ligne, acces) for ligne in lignes])


# Les chiffres -----------------------------------------------------------------------------------------------------


def _lundi(jour: date) -> date:
    return jour - timedelta(days=jour.weekday())


async def statistiques(db: AsyncSession, acces: Acces) -> StatistiquesCertification:
    instant = datetime.now(UTC)
    c = _candidats(acces).subquery("c")
    ids = select(c.c.uid)

    candidats, actifs, certifies = (
        await db.execute(
            select(
                func.count(),
                func.count().filter(c.c.derniere >= instant - INACTIF),
                func.count(c.c.certificat),
            ).select_from(c)
        )
    ).one()

    noms = (await regles.en_cours(db)).noms
    par_rang = dict(
        (
            await db.execute(
                select(BadgeObtenu.rang, func.count())
                .where(BadgeObtenu.utilisateur_id.in_(ids))
                .group_by(BadgeObtenu.rang)
            )
        ).all()
    )
    totaux = TotauxCertification(
        candidats=candidats,
        actifs_30_jours=actifs,
        certifies=certifies,
        badges=[BadgeCompte(rang=r, nom=nom, nombre=par_rang.get(r, 0)) for r, nom in enumerate(noms, start=1)],
    )

    return StatistiquesCertification(
        totaux=totaux,
        entonnoir=await _entonnoir(db, ids),
        par_dre=[
            LigneDre(code=code, dre=nom, candidats=n, badges=b, certifies=cert)
            for code, nom, n, b, cert in (
                await db.execute(
                    select(c.c.dre_code, c.c.dre_nom, func.count(), func.sum(c.c.nb_badges), func.count(c.c.certificat))
                    .where(c.c.dre_code.is_not(None))
                    .group_by(c.c.dre_code, c.c.dre_nom)
                    .order_by(c.c.dre_nom)
                )
            ).all()
        ],
        par_semaine=await _par_semaine(db, c, instant),
    )


async def _entonnoir(db: AsyncSession, ids: Select) -> list[LigneEntonnoir]:
    publiees = set(
        (
            await db.scalars(
                select(Quiz.place).where(Quiz.parcours == PARCOURS_CERTIFICATION, Quiz.etat == EtatQuiz.publie)
            )
        ).all()
    )
    tentatives = {
        place: (tentes, terminees, reussies)
        for place, tentes, terminees, reussies in (
            await db.execute(
                _tentatives()
                .with_only_columns(
                    Quiz.place,
                    func.count(TentativeQuiz.joueur_id.distinct()),
                    func.count(TentativeQuiz.terminee_le),
                    func.count().filter(TentativeQuiz.reussie.is_(True)),
                )
                .where(TentativeQuiz.joueur_id.in_(ids))
                .group_by(Quiz.place)
            )
        ).all()
    }
    # Pour chaque place réussie : le nombre de tentatives jouées sur cette place jusqu'à la réussite.
    jusqu_a_reussite = (
        select(PlaceReussie.place, func.count(TentativeQuiz.id).label("n"))
        .join(
            TentativeQuiz,
            and_(
                TentativeQuiz.joueur_id == PlaceReussie.utilisateur_id,
                TentativeQuiz.commencee_le <= PlaceReussie.reussie_le,
                TentativeQuiz.essai.is_(False),
            ),
        )
        .join(Quiz, and_(Quiz.id == TentativeQuiz.quiz_id, Quiz.place == PlaceReussie.place))
        .where(PlaceReussie.utilisateur_id.in_(ids), Quiz.parcours == PARCOURS_CERTIFICATION)
        .group_by(PlaceReussie.place, PlaceReussie.utilisateur_id)
        .subquery()
    )
    reussites = {
        place: (reussis, moyenne)
        for place, reussis, moyenne in (
            await db.execute(
                select(jusqu_a_reussite.c.place, func.count(), func.avg(jusqu_a_reussite.c.n)).group_by(
                    jusqu_a_reussite.c.place
                )
            )
        ).all()
    }
    lignes = []
    for place in range(1, PLACES + 1):
        tentes, terminees, reussies = tentatives.get(place, (0, 0, 0))
        reussis, moyenne = reussites.get(place, (0, None))
        lignes.append(
            LigneEntonnoir(
                place=place,
                quiz_publie=place in publiees,
                tentes=tentes,
                reussis=reussis,
                taux_reussite=reussies / terminees if terminees else None,
                tentatives_avant_reussite=float(moyenne) if moyenne is not None else None,
            )
        )
    return lignes


async def _par_semaine(db: AsyncSession, c: Any, instant: datetime) -> list[LigneSemaine]:
    """Les 12 dernières semaines (lundi à dimanche, heure de Lomé, qui est l'heure UTC)."""
    premiere = _lundi(instant.date()) - timedelta(weeks=SEMAINES - 1)
    debut_periode = datetime.combine(premiere, datetime.min.time(), UTC)

    def semaine(colonne: Any) -> Any:
        # Des constantes SQL, pas des paramètres : le GROUP BY doit reprendre exactement l'expression du SELECT.
        return func.date_trunc(literal_column("'week'"), func.timezone(literal_column("'UTC'"), colonne))

    nouveaux = dict(
        (
            await db.execute(
                select(semaine(c.c.debut), func.count()).where(c.c.debut >= debut_periode).group_by(semaine(c.c.debut))
            )
        ).all()
    )
    # Un certifié compte la semaine de son premier certificat (une réémission ne le recompte pas).
    premier = (
        select(Certificat.utilisateur_id, func.min(Certificat.delivre_le).label("le"))
        .where(
            Certificat.utilisateur_id.in_(select(c.c.uid).where(c.c.certificat.is_not(None))),
            # Spec 049 : les certificats de la phase de test ne comptent plus.
            Certificat.archive_le.is_(None),
        )
        .group_by(Certificat.utilisateur_id)
        .subquery()
    )
    certifies = dict(
        (
            await db.execute(
                select(semaine(premier.c.le), func.count())
                .where(premier.c.le >= debut_periode)
                .group_by(semaine(premier.c.le))
            )
        ).all()
    )
    nouveaux = {cle.date(): n for cle, n in nouveaux.items()}
    certifies = {cle.date(): n for cle, n in certifies.items()}
    return [
        LigneSemaine(debut=jour, candidats=nouveaux.get(jour, 0), certifies=certifies.get(jour, 0))
        for jour in (premiere + timedelta(weeks=i) for i in range(SEMAINES))
    ]


# L'export ---------------------------------------------------------------------------------------------------------


def _date(valeur: datetime) -> str:
    return valeur.astimezone(UTC).strftime("%Y-%m-%d %H:%M")


async def exporter(
    db: AsyncSession, acces: Acces, filtres: FiltresCandidats, finalite: str, ip: str
) -> tuple[bytes, int]:
    """Le CSV des candidats filtrés, journalisé avec sa finalité. Refusé au-delà de la limite des exports."""
    requete = _trier(_filtrer(_candidats(acces), acces, filtres, datetime.now(UTC)))
    # La même limite que les autres exports du back office.
    limite = settings.export_lignes_max
    lignes = (await db.execute(requete.limit(limite + 1))).all()
    if len(lignes) > limite:
        raise Refus(f"Trop de candidats (plus de {limite}) : précise les filtres.")
    tampon = io.StringIO()
    ecrivain = csv.writer(tampon, delimiter=";")
    ecrivain.writerow(ENTETES)
    for ligne in lignes:
        c = _candidat(ligne, acces)
        ecrivain.writerow(
            [
                neutraliser(c.nom),
                neutraliser(c.pseudonyme or ""),
                "Élève" if c.role == "eleve" else "Encadreur",
                neutraliser(c.club.nom if c.club else ""),
                neutraliser(c.etablissement or ""),
                c.dre or "",
                c.places_validees,
                " ".join(str(r) for r in c.badges),
                c.place_en_cours or "",
                c.tentatives_place,
                c.tentatives,
                _date(c.debut),
                _date(c.derniere_activite),
                c.certificat or "",
            ]
        )
    journaliser(
        db, "export_suivi_certification", acces.utilisateur, cible_type="certification", perimetre="national",
        details={"finalite": finalite, "filtres": filtres.model_dump(mode="json", exclude_none=True),
                 "lignes": len(lignes)},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return ("﻿" + tampon.getvalue()).encode("utf-8"), len(lignes)
