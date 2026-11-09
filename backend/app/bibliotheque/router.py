"""Routes publiques de la bibliothèque (spec 028) : sans connexion. Les règles vivent dans `public.py`."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.bibliotheque import lecture, public
from app.bibliotheque.models import CategorieRessource
from app.bibliotheque.schemas import Bibliotheque
from app.db import get_session

router = APIRouter(prefix="/bibliotheque", tags=["bibliotheque"])

Db = Annotated[AsyncSession, Depends(get_session)]


@router.get("")
async def bibliotheque(db: Db, categorie: CategorieRessource | None = None, axe: str | None = None) -> Bibliotheque:
    return await public.bibliotheque(db, categorie, axe)


@router.get("/{ressource_id}/fichier", response_class=StreamingResponse)
async def fichier(ressource_id: UUID, db: Db, telecharger: bool = False) -> StreamingResponse:
    ressource = await public.publiee(db, ressource_id)
    if ressource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, lecture.INTROUVABLE)
    # Le fichier s'ouvre d'abord : un stockage indisponible ne compte rien.
    reponse = await lecture.pdf(ressource, telecharger=telecharger)
    await public.compter(db, ressource.id)
    return reponse


@router.get("/{ressource_id}/couverture/{taille}", response_class=Response)
async def couverture(ressource_id: UUID, taille: str, db: Db) -> Response:
    ressource = await public.publiee(db, ressource_id)
    if ressource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, lecture.INTROUVABLE)
    return await lecture.couverture(ressource, taille)
