"""Centre de notifications (spec 023). `notifier` s'appelle dans la transaction de l'événement : la notification
existe si et seulement si l'événement est validé."""

from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification
from app.notifications.schemas import Notifications, NotificationSortie

LIMITE = 50


def notifier(
    db: AsyncSession, utilisateur_id: UUID, type: str, titre: str, message: str | None = None, lien: str | None = None
) -> Notification:
    notification = Notification(
        id=uuid7(), utilisateur_id=utilisateur_id, type=type, titre=titre, message=message, lien=lien
    )
    db.add(notification)
    return notification


async def compter_non_lues(db: AsyncSession, utilisateur_id: UUID) -> int:
    return (
        await db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.utilisateur_id == utilisateur_id, Notification.lue_le.is_(None))
        )
    ) or 0


async def lister(db: AsyncSession, utilisateur_id: UUID) -> Notifications:
    lignes = await db.scalars(
        select(Notification)
        .where(Notification.utilisateur_id == utilisateur_id)
        .order_by(Notification.cree_le.desc(), Notification.id.desc())
        .limit(LIMITE)
    )
    return Notifications(
        notifications=[
            NotificationSortie(
                id=n.id,
                type=n.type,
                titre=n.titre,
                message=n.message,
                lien=n.lien,
                lue=n.lue_le is not None,
                cree_le=n.cree_le,
            )
            for n in lignes
        ],
        non_lues=await compter_non_lues(db, utilisateur_id),
    )


async def marquer_lue(db: AsyncSession, utilisateur_id: UUID, notification_id: UUID) -> bool:
    """Faux si la notification n'existe pas ou appartient à un autre compte : la route répond alors 404."""
    resultat = await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.utilisateur_id == utilisateur_id)
        .values(lue_le=func.coalesce(Notification.lue_le, datetime.now(UTC)))
        .returning(Notification.id)
    )
    trouvee = resultat.scalar_one_or_none() is not None
    await db.commit()
    return trouvee


async def marquer_toutes_lues(db: AsyncSession, utilisateur_id: UUID) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.utilisateur_id == utilisateur_id, Notification.lue_le.is_(None))
        .values(lue_le=datetime.now(UTC))
    )
    await db.commit()
