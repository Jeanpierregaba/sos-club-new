"""Suspension et réactivation d'une carte par l'équipe (spec 040) : droit de modifier les inscrits, au national,
avec la double authentification du module."""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action as Droit
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.cartes import administration
from app.cartes.schemas import CarteAdmin, MotifCarte
from app.db import get_session

router_admin = APIRouter(prefix="/admin/inscrits/{utilisateur_id}/carte", tags=["admin"])

Db = Annotated[AsyncSession, Depends(get_session)]
Gestionnaire = Annotated[Acces, Depends(exiger_permission("inscrits", Droit.modifier, national=True))]


Action = Callable[[AsyncSession, Acces, UUID, str, str], Awaitable[CarteAdmin]]


async def _agir(
    action: Action, utilisateur_id: UUID, entree: MotifCarte, acces: Acces, db: AsyncSession, request: Request
) -> CarteAdmin:
    try:
        return await action(db, acces, utilisateur_id, entree.motif, adresse_ip(request))
    except administration.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce compte n'a pas de carte.") from None
    except administration.Refus as refus:
        raise HTTPException(status.HTTP_409_CONFLICT, str(refus)) from None


@router_admin.post("/suspendre")
async def suspendre(
    utilisateur_id: UUID, entree: MotifCarte, acces: Gestionnaire, db: Db, request: Request
) -> CarteAdmin:
    return await _agir(administration.suspendre, utilisateur_id, entree, acces, db, request)


@router_admin.post("/reactiver")
async def reactiver(
    utilisateur_id: UUID, entree: MotifCarte, acces: Gestionnaire, db: Db, request: Request
) -> CarteAdmin:
    return await _agir(administration.reactiver, utilisateur_id, entree, acces, db, request)
