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

from app.points.models import LigneBareme, MouvementPoints, Semestre
from app.points.schemas import LignePoints, ResumePoints, SemestreResume


class ActionInconnue(Exception):
    """Une erreur de programmation : chaque action écrite par le code existe dans le barème."""


def aujourd_hui() -> date:
    # Lomé est à UTC+0 toute l'année : la date UTC est la date locale.
    return datetime.now(UTC).date()


async def semestre_en_cours(db: AsyncSession, jour: date | None = None) -> Semestre | None:
    jour = jour or aujourd_hui()
    return await db.scalar(select(Semestre).where(Semestre.debut <= jour, Semestre.fin >= jour))


async def crediter(
    db: AsyncSession, action: str, utilisateur_id: UUID, cle: str, *, valide_par: UUID | None = None
) -> MouvementPoints | None:
    """Écrit une ligne au montant actuel du barème. Renvoie None si l'action est désactivée, à 0, ou déjà créditée
    sous cette clé : la base tranche, même entre deux requêtes simultanées."""
    ligne = await db.get(LigneBareme, action)
    if ligne is None:
        raise ActionInconnue(action)
    if not ligne.actif or ligne.montant == 0:
        return None
    semestre = await semestre_en_cours(db)
    requete = (
        insert(MouvementPoints)
        .values(
            id=uuid7(),
            utilisateur_id=utilisateur_id,
            action=action,
            montant=ligne.montant,
            semestre_id=semestre.id if semestre else None,
            cle=cle,
            valide_par=valide_par,
        )
        .on_conflict_do_nothing(index_elements=["cle"])
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
