"""Fiche complète d'un inscrit (spec 045), en lecture seule : points, quiz, certification et contenus.

Chaque liste est paginée en SQL. Les questions et les réponses d'une tentative ne sortent jamais d'ici.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    BadgeAdmin,
    CertificatAdmin,
    CertificationInscrit,
    ContenuAdmin,
    PageContenusInscrit,
    PageTentatives,
    PlaceAdmin,
    PointsInscrit,
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
from app.quiz.models import PLACES, EtatTentative, ParametresQuiz, Quiz, TentativeQuiz
from app.referentiel.models import Axe

PAR_PAGE_POINTS = 50
PAR_PAGE = 25
LONGUEUR_EXTRAIT = 80


class Introuvable(Exception):
    pass


async def verifier(db: AsyncSession, utilisateur_id: UUID) -> Utilisateur:
    """Un élève ou un encadreur : un collaborateur ou un joueur sans compte n'a pas de fiche d'inscrit."""
    utilisateur = await db.get(Utilisateur, utilisateur_id)
    if utilisateur is None or utilisateur.role in (Role.admin, Role.invite):
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
            Semestre.id.in_(
                select(MouvementPoints.semestre_id).where(MouvementPoints.utilisateur_id == utilisateur_id)
            )
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
        resume=ResumeQuiz(quiz_valides=resume[0], tentatives=resume[1], echecs=resume[2], points=resume[3]),
        valides=[
            QuizValide(
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
            )
            for r in valides.all()
        ],
        tentatives=PageTentatives(
            total=total, page=page, par_page=PAR_PAGE, tentatives=[_tentative(r) for r in rangees.all()]
        ),
    )


def _valeur(valeur: Any) -> Any:
    return getattr(valeur, "value", valeur)


def _tentative(rangee: Any) -> TentativeAdmin:
    tentative: TentativeQuiz = rangee.TentativeQuiz
    duree = None
    if tentative.terminee_le is not None:
        duree = int((tentative.terminee_le - tentative.commencee_le).total_seconds())
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
        points=rangee.points,
    )


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
    places = [
        PlaceAdmin(
            place=place,
            reussie_le=reussies[place].reussie_le if place in reussies else None,
            quiz_titre=reussies[place].titre if place in reussies else None,
        )
        for place in range(1, PLACES + 1)
    ]
    badges = await db.scalars(
        select(BadgeObtenu).where(BadgeObtenu.utilisateur_id == utilisateur_id).order_by(BadgeObtenu.rang)
    )
    certificats = await db.scalars(
        select(Certificat).where(Certificat.utilisateur_id == utilisateur_id).order_by(Certificat.delivre_le.desc())
    )
    return CertificationInscrit(
        places=places,
        badges=[BadgeAdmin(rang=b.rang, nom=b.nom, palier=b.palier, obtenu_le=b.obtenu_le) for b in badges.all()],
        certificats=[
            CertificatAdmin(
                numero=c.numero,
                etat=c.etat.value,
                delivre_le=c.delivre_le,
                titulaire=f"{c.titulaire_prenom} {c.titulaire_nom}",
                motif=c.motif,
                decide_le=c.decide_le,
            )
            for c in certificats.all()
        ],
    )


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
