"""Centre de notifications (spec 023) : chaque compte connecté ne lit que les siennes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Utilisateur
from app.db import get_session
from app.notifications import service
from app.notifications.schemas import CompteNotifications, Notifications

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def mes_notifications(db: Base, utilisateur: Connecte) -> Notifications:
    return await service.lister(db, utilisateur.id)


@router.get("/compte")
async def compte(db: Base, utilisateur: Connecte) -> CompteNotifications:
    return CompteNotifications(non_lues=await service.compter_non_lues(db, utilisateur.id))


@router.post("/{notification_id}/lue", status_code=status.HTTP_204_NO_CONTENT)
async def marquer_lue(notification_id: UUID, db: Base, utilisateur: Connecte) -> Response:
    if not await service.marquer_lue(db, utilisateur.id, notification_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette notification est introuvable.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/lues", status_code=status.HTTP_204_NO_CONTENT)
async def tout_marquer_lu(db: Base, utilisateur: Connecte) -> Response:
    await service.marquer_toutes_lues(db, utilisateur.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
