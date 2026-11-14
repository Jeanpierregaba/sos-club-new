"""Classements courants (spec 036, ADR-0013) : calculés à la demande depuis le registre.

Un score reste une somme de lignes (ADR-0004). Les classements publics ne montrent jamais d'identifiant
utilisateur, de nom complet ni de contact ; le routeur choisit le schéma qui expose ou non les identifiants.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.clubs import activation
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification
from app.points.models import MouvementPoints, Semestre
from app.points.service import semestre_en_cours
from app.referentiel.models import Dre, Etablissement, Iesg


class Categorie(StrEnum):
    eleves = "eleves"
    encadreurs = "encadreurs"
    clubs = "clubs"


class Niveau(StrEnum):
    national = "national"
    dre = "dre"


class Periode(StrEnum):
    semestre = "semestre"
    historique = "historique"


class DreRequise(Exception):
    """Le niveau DRE exige un code de DRE."""


class DreIntrouvable(Exception):
    """La DRE demandée n'existe pas ou n'est pas active."""


@dataclass(frozen=True)
class LigneClassement:
    rang: int
    nom: str
    club: str | None
    dre: str
    points: int | float
    # Renseignés pour l'admin seulement ; jamais servis par une route publique.
    utilisateur_id: UUID | None = None
    club_id: UUID | None = None
    etablissement: str | None = None


@dataclass(frozen=True)
class Classement:
    categorie: Categorie
    niveau: Niveau
    dre: Dre | None
    periode: Periode
    semestre: Semestre | None
    total: int
    lignes: list[LigneClassement]


def _nom_encadreur(prenom: str, nom: str) -> str:
    """Le prénom et l'initiale du nom, comme les signatures d'articles."""
    initiale = f" {nom.strip()[:1].upper()}." if nom.strip() else ""
    return f"{prenom.strip()}{initiale}"


async def _resoudre_dre(db: AsyncSession, niveau: Niveau, dre_code: str | None) -> Dre | None:
    if niveau is Niveau.national:
        return None
    if not dre_code:
        raise DreRequise
    dre = await db.scalar(select(Dre).where(Dre.code == dre_code, Dre.actif.is_(True)))
    if dre is None:
        raise DreIntrouvable
    return dre


def _points_par_utilisateur(periode: Periode, semestre: Semestre | None) -> Select:
    requete = select(
        MouvementPoints.utilisateur_id.label("utilisateur_id"),
        func.sum(MouvementPoints.montant).label("points"),
    ).group_by(MouvementPoints.utilisateur_id)
    if periode is Periode.semestre and semestre is not None:
        requete = requete.where(MouvementPoints.semestre_id == semestre.id)
    return requete.subquery()


def _base_eleves(points: Select, periode: Periode, dre_code: str | None) -> Select:
    club = aliased(Club)
    requete = (
        select(
            Eleve.utilisateur_id,
            Eleve.pseudonyme.label("nom"),
            club.nom.label("club"),
            Dre.nom.label("dre"),
            points.c.points,
        )
        .join(points, points.c.utilisateur_id == Eleve.utilisateur_id)
        .join(Utilisateur, Utilisateur.id == Eleve.utilisateur_id)
        .join(Etablissement, Etablissement.id == Eleve.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .outerjoin(
            Adhesion,
            and_(Adhesion.eleve_id == Eleve.utilisateur_id, Adhesion.etat == EtatAdhesion.active),
        )
        .outerjoin(club, club.id == Adhesion.club_id)
        .where(
            Utilisateur.role == Role.eleve,
            Utilisateur.statut == StatutCompte.actif,
            points.c.points != 0,
        )
    )
    if periode is Periode.semestre:
        # Un ancien élève garde ses archives et le total historique, jamais le classement du semestre.
        requete = requete.where(Utilisateur.ancien_eleve_le.is_(None))
    if dre_code is not None:
        requete = requete.where(Dre.code == dre_code)
    return requete


def _base_encadreurs(points: Select, dre_code: str | None) -> Select:
    club = aliased(Club)
    requete = (
        select(
            Encadreur.utilisateur_id,
            Utilisateur.prenom,
            Utilisateur.nom,
            club.nom.label("club"),
            Dre.nom.label("dre"),
            points.c.points,
        )
        .join(points, points.c.utilisateur_id == Encadreur.utilisateur_id)
        .join(Utilisateur, Utilisateur.id == Encadreur.utilisateur_id)
        .join(Etablissement, Etablissement.id == Encadreur.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .outerjoin(
            Rattachement,
            and_(
                Rattachement.encadreur_id == Encadreur.utilisateur_id,
                Rattachement.etat == EtatRattachement.actif,
            ),
        )
        .outerjoin(club, club.id == Rattachement.club_id)
        .where(
            Utilisateur.role == Role.encadreur,
            Utilisateur.statut == StatutCompte.actif,
            Encadreur.etat == EtatVerification.actif,
            points.c.points != 0,
        )
    )
    if dre_code is not None:
        requete = requete.where(Dre.code == dre_code)
    return requete


def _base_clubs(periode: Periode, semestre: Semestre | None, dre_code: str | None) -> Select:
    requete = (
        select(
            Club.id.label("club_id"),
            Club.nom.label("nom"),
            Etablissement.nom.label("etablissement"),
            Dre.nom.label("dre"),
            func.sum(MouvementPoints.demi_points_club).label("demi_points"),
        )
        .join(MouvementPoints, MouvementPoints.club_id == Club.id)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .where(activation.en_service(), MouvementPoints.demi_points_club.is_not(None))
        .group_by(Club.id, Club.nom, Etablissement.nom, Dre.nom)
        .having(func.sum(MouvementPoints.demi_points_club) != 0)
    )
    if periode is Periode.semestre and semestre is not None:
        requete = requete.where(MouvementPoints.semestre_id == semestre.id)
    if dre_code is not None:
        requete = requete.where(Dre.code == dre_code)
    return requete


async def _compter(db: AsyncSession, requete: Select) -> int:
    return int(await db.scalar(select(func.count()).select_from(requete.subquery())) or 0)


async def classement_public(
    db: AsyncSession,
    *,
    categorie: Categorie = Categorie.eleves,
    niveau: Niveau = Niveau.national,
    dre_code: str | None = None,
    periode: Periode = Periode.semestre,
    page: int = 1,
    par_page: int = 50,
) -> Classement:
    dre = await _resoudre_dre(db, niveau, dre_code)
    semestre = await semestre_en_cours(db)
    if periode is Periode.semestre and semestre is None:
        return Classement(categorie, niveau, dre, periode, None, 0, [])

    if categorie is Categorie.clubs:
        base = _base_clubs(periode, semestre, dre.code if dre else None)
        sous = base.subquery()
        requete = select(
            sous.c.club_id,
            sous.c.nom,
            sous.c.etablissement,
            sous.c.dre,
            sous.c.demi_points,
            func.rank().over(order_by=sous.c.demi_points.desc()).label("rang"),
        ).order_by(
            sous.c.demi_points.desc(),
            func.lower(sous.c.nom),
            sous.c.club_id,
        )
        total = await _compter(db, base)
        lignes = [
            LigneClassement(
                rang=int(ligne.rang),
                nom=ligne.nom,
                club=None,
                dre=ligne.dre,
                points=float(ligne.demi_points) / 2,
                club_id=ligne.club_id,
                etablissement=ligne.etablissement,
            )
            for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
        ]
        return Classement(categorie, niveau, dre, periode, semestre, total, lignes)

    points = _points_par_utilisateur(periode, semestre)
    if categorie is Categorie.eleves:
        base = _base_eleves(points, periode, dre.code if dre else None)
        sous = base.subquery()
        requete = select(
            sous.c.utilisateur_id,
            sous.c.nom,
            sous.c.club,
            sous.c.dre,
            sous.c.points,
            func.rank().over(order_by=sous.c.points.desc()).label("rang"),
        ).order_by(
            sous.c.points.desc(),
            func.lower(sous.c.nom),
            func.coalesce(sous.c.club, ""),
            sous.c.utilisateur_id,
        )
        total = await _compter(db, base)
        lignes = [
            LigneClassement(
                rang=int(ligne.rang),
                nom=ligne.nom,
                club=ligne.club,
                dre=ligne.dre,
                points=int(ligne.points),
                utilisateur_id=ligne.utilisateur_id,
            )
            for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
        ]
        return Classement(categorie, niveau, dre, periode, semestre, total, lignes)

    base = _base_encadreurs(points, dre.code if dre else None)
    sous = base.subquery()
    requete = select(
        sous.c.utilisateur_id,
        sous.c.prenom,
        sous.c.nom,
        sous.c.club,
        sous.c.dre,
        sous.c.points,
        func.rank().over(order_by=sous.c.points.desc()).label("rang"),
    ).order_by(
        sous.c.points.desc(),
        func.lower(sous.c.prenom),
        func.lower(sous.c.nom),
        sous.c.utilisateur_id,
    )
    total = await _compter(db, base)
    lignes = [
        LigneClassement(
            rang=int(ligne.rang),
            nom=_nom_encadreur(ligne.prenom, ligne.nom),
            club=ligne.club,
            dre=ligne.dre,
            points=int(ligne.points),
            utilisateur_id=ligne.utilisateur_id,
        )
        for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
    ]
    return Classement(categorie, niveau, dre, periode, semestre, total, lignes)
