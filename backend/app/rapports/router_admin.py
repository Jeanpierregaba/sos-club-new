"""Rapports côté équipe (spec 038) : les documents d'un rapport pour le modérateur. La file, l'aperçu et les
décisions sont ceux du moteur de modération (/admin/moderation)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, exiger_permission
from app.db import get_session
from app.moderation.models import Contenu
from app.moderation.service import Introuvable
from app.rapports import pieces
from app.rapports.models import TYPES_CONTENU
from app.rapports.router import document

Base = Annotated[AsyncSession, Depends(get_session)]
Moderateur = Annotated[Acces, Depends(exiger_permission("moderation", Action.consulter))]

router_admin = APIRouter(prefix="/admin/rapports", tags=["admin"])


@router_admin.get("/{contenu_id}/documents/{piece_id}", response_class=Response)
async def lire_document(contenu_id: UUID, piece_id: UUID, acces: Moderateur, db: Base) -> Response:
    """Un document d'une version envoyée par l'auteur, jamais d'une version de travail ; hors de la DRE du
    collaborateur, le rapport n'existe pas."""
    contenu = await db.get(Contenu, contenu_id)
    if (
        contenu is None
        or contenu.type not in TYPES_CONTENU.values()
        or (not acces.national and contenu.dre_code != acces.collaborateur.perimetre_dre)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce document est introuvable.")
    version = await pieces.derniere_version_envoyee(db, contenu_id)
    try:
        if version is None:
            raise Introuvable
        piece, octets = await pieces.octets_du_document(db, version.id, contenu_id, piece_id)
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce document est introuvable.") from None
    return document(piece, octets)
