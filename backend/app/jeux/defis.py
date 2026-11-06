"""Le défi du jour (spec 021) : la même question pour tous, qui change à minuit (heure de Lomé, UTC+0).

La question part sans sa réponse ; la correction vient d'une seconde requête (ADR-0004). Aucun point.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jeux.models import DefiQuestion
from app.points.service import aujourd_hui


class AucunDefi(Exception):
    pass


async def du_jour(db: AsyncSession, jour: date | None = None) -> DefiQuestion:
    """La question active de rang (numéro du jour modulo leur nombre), dans l'ordre de la rotation."""
    jour = jour or aujourd_hui()
    actives = select(DefiQuestion).where(DefiQuestion.actif.is_(True))
    nombre = await db.scalar(select(func.count()).select_from(actives.subquery()))
    if not nombre:
        raise AucunDefi
    return await db.scalar(actives.order_by(DefiQuestion.ordre).offset(jour.toordinal() % nombre).limit(1))


async def corriger(db: AsyncSession, defi_id: UUID, choix: int) -> tuple[DefiQuestion, bool]:
    """La correction d'une question active, même si minuit est passé depuis son affichage."""
    defi = await db.get(DefiQuestion, defi_id)
    if defi is None or not defi.actif:
        raise AucunDefi
    if choix >= len(defi.options):
        raise ValueError("Cette réponse n'existe pas.")
    return defi, choix == defi.bonne_reponse
