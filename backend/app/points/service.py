"""Seule porte d'écriture du registre des points (ADR-0004) et calcul des totaux.

`crediter` ne valide jamais la transaction : l'appelant le fait, pour que le gain et l'action qui le déclenche
soient écrits ensemble, ou pas du tout.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid7

from sqlalchemy import false, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Adhesion, Club, EtatAdhesion
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.points.models import AnneeAcademique, Beneficiaire, LigneBareme, MouvementPoints, Semestre
from app.points.schemas import LignePoints, ResumePoints, SemestreResume


class ActionInconnue(Exception):
    """Une erreur de programmation : chaque action écrite par le code existe dans le barème."""


def maintenant() -> datetime:
    return datetime.now(UTC)


def aujourd_hui() -> date:
    # Lomé est à UTC+0 toute l'année : la date UTC est la date locale.
    return datetime.now(UTC).date()


async def semestre_en_cours(db: AsyncSession, jour: date | None = None) -> Semestre | None:
    jour = jour or aujourd_hui()
    return await db.scalar(select(Semestre).where(Semestre.debut <= jour, Semestre.fin >= jour))


async def annee_en_cours(db: AsyncSession, jour: date | None = None) -> AnneeAcademique | None:
    """L'année académique ouverte qui contient ce jour (spec 034) ; une année clôturée ne reçoit plus de gain.

    Le verrou partagé (FOR KEY SHARE) tient jusqu'à la fin de la transaction du crédit : une clôture (FOR UPDATE)
    attend les crédits en cours, et un crédit lancé pendant une clôture relit l'année après elle, donc la voit
    clôturée. Les crédits ne se bloquent pas entre eux."""
    jour = jour or aujourd_hui()
    return await db.scalar(
        select(AnneeAcademique)
        .where(AnneeAcademique.debut <= jour, AnneeAcademique.fin >= jour, AnneeAcademique.cloturee_le.is_(None))
        .with_for_update(read=True, key_share=True)
    )


async def club_beneficiaire(db: AsyncSession, eleve_id: UUID) -> UUID | None:
    """Le club qui reçoit la moitié d'un gain de l'élève (spec 034, ADR-0012) : celui de son affiliation active,
    s'il est en service (actif, ou en régularisation dans le délai), et si l'élève est actif. Sinon, aucun."""
    club = await db.scalar(
        select(Club)
        .join(Adhesion, Adhesion.club_id == Club.id)
        .join(Utilisateur, Utilisateur.id == Adhesion.eleve_id)
        .where(
            Adhesion.eleve_id == eleve_id,
            Adhesion.etat == EtatAdhesion.active,
            # Un élève suspendu ne compte plus dans son club (spec 033) : il ne l'alimente plus.
            Utilisateur.role == Role.eleve,
            Utilisateur.statut == StatutCompte.actif,
        )
    )
    return club.id if club is not None and activation.est_en_service(club) else None


async def crediter(
    db: AsyncSession, action: str, utilisateur_id: UUID, cle: str, *, valide_par: UUID | None = None
) -> MouvementPoints | None:
    """Écrit une ligne au montant actuel du barème. Renvoie None si l'action est désactivée, à 0, ou déjà créditée
    sous cette clé : la base tranche, même entre deux requêtes simultanées. Pour une action d'élève, la même ligne
    crédite son club de la moitié du montant, en demi-points (ADR-0012)."""
    ligne = await db.get(LigneBareme, action)
    if ligne is None:
        raise ActionInconnue(action)
    if not ligne.actif or ligne.montant == 0:
        return None
    club_id = None
    if ligne.beneficiaire is Beneficiaire.eleve:
        compte = await db.get(Utilisateur, utilisateur_id)
        # Spec 034 : un ancien élève garde ses archives, sans nouvelle récompense d'élève.
        if compte is not None and compte.ancien_eleve_le is not None:
            return None
        club_id = await club_beneficiaire(db, utilisateur_id)
    semestre = await semestre_en_cours(db)
    annee = await annee_en_cours(db)
    requete = (
        insert(MouvementPoints)
        .values(
            id=uuid7(),
            utilisateur_id=utilisateur_id,
            action=action,
            montant=ligne.montant,
            semestre_id=semestre.id if semestre else None,
            annee_id=annee.id if annee else None,
            cle=cle,
            valide_par=valide_par,
            club_id=club_id,
            # La moitié du montant, comptée en demi-points : exactement le montant de l'élève.
            demi_points_club=ligne.montant if club_id else None,
        )
        .on_conflict_do_nothing(index_elements=["cle"])
        .returning(MouvementPoints)
    )
    return await db.scalar(requete)


async def annuler(
    db: AsyncSession, mouvement: MouvementPoints, *, valide_par: UUID | None = None
) -> MouvementPoints | None:
    """Retire un gain par une ligne négative du même montant, dans le semestre en cours et l'année du gain (le registre ne se
    réécrit jamais). Renvoie None si le gain est déjà annulé : l'unicité de `annule_id` tranche, même entre deux
    requêtes simultanées."""
    semestre = await semestre_en_cours(db)
    requete = (
        insert(MouvementPoints)
        .values(
            id=uuid7(),
            utilisateur_id=mouvement.utilisateur_id,
            # L'annulation reste dans l'année du gain (ADR-0012) : le total de cette année baisse, celui de l'année
            # en cours ne bouge pas. Le classement d'une année clôturée reste figé.
            annee_id=mouvement.annee_id,
            action=mouvement.action,
            montant=-mouvement.montant,
            semestre_id=semestre.id if semestre else None,
            cle=f"annulation:{mouvement.id}",
            valide_par=valide_par,
            annule_id=mouvement.id,
            club_id=mouvement.club_id,
            demi_points_club=-mouvement.demi_points_club if mouvement.demi_points_club is not None else None,
        )
        .on_conflict_do_nothing()
        .returning(MouvementPoints)
    )
    return await db.scalar(requete)


@dataclass(frozen=True)
class Totaux:
    semestre: Semestre | None
    points_semestre: int
    total: int


async def totaux(db: AsyncSession, utilisateur_id: UUID) -> Totaux:
    semestre = await semestre_en_cours(db)
    du_semestre = MouvementPoints.semestre_id == semestre.id if semestre else false()
    total, points_semestre = (
        await db.execute(
            select(
                func.coalesce(func.sum(MouvementPoints.montant), 0),
                func.coalesce(func.sum(MouvementPoints.montant).filter(du_semestre), 0),
            ).where(MouvementPoints.utilisateur_id == utilisateur_id)
        )
    ).one()
    return Totaux(semestre=semestre, points_semestre=points_semestre, total=total)


@dataclass(frozen=True)
class Ligne:
    libelle: str
    montant: int
    cree_le: datetime
    semestre: str | None


async def dernieres_lignes(db: AsyncSession, utilisateur_id: UUID, nombre: int) -> list[Ligne]:
    requete = (
        select(LigneBareme.libelle, MouvementPoints.montant, MouvementPoints.cree_le, Semestre.libelle)
        .join(LigneBareme, LigneBareme.code == MouvementPoints.action)
        .outerjoin(Semestre, Semestre.id == MouvementPoints.semestre_id)
        .where(MouvementPoints.utilisateur_id == utilisateur_id)
        .order_by(MouvementPoints.cree_le.desc(), MouvementPoints.id.desc())
        .limit(nombre)
    )
    return [Ligne(*rangee) for rangee in (await db.execute(requete)).all()]


async def resume(db: AsyncSession, utilisateur_id: UUID, nombre: int) -> ResumePoints:
    """Totaux et dernières lignes, pour l'espace d'un élève ou d'un encadreur et pour sa fiche admin."""
    calcul = await totaux(db, utilisateur_id)
    lignes = await dernieres_lignes(db, utilisateur_id, nombre)
    semestre = calcul.semestre
    return ResumePoints(
        semestre=SemestreResume(libelle=semestre.libelle, debut=semestre.debut, fin=semestre.fin) if semestre else None,
        points_semestre=calcul.points_semestre,
        total=calcul.total,
        lignes=[LignePoints(**ligne.__dict__) for ligne in lignes],
    )


async def scores_des_clubs(db: AsyncSession, club_ids: list[UUID]) -> dict[UUID, float]:
    """Le score de chaque club : la somme de ses parts, la moitié des gains de ses élèves (ADR-0012). Un club sans
    part n'apparaît pas."""
    if not club_ids:
        return {}
    lignes = await db.execute(
        select(MouvementPoints.club_id, func.sum(MouvementPoints.demi_points_club))
        .where(MouvementPoints.club_id.in_(club_ids))
        .group_by(MouvementPoints.club_id)
    )
    return {club_id: demi / 2 for club_id, demi in lignes.all() if club_id is not None}
