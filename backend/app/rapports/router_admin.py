"""Rapports côté équipe (spec 038) : les documents d'un rapport pour le modérateur. La file, l'aperçu et les
décisions sont ceux du moteur de modération (/admin/moderation)."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.db import get_session
from app.moderation.models import Contenu, EtatContenu
from app.moderation.service import Introuvable
from app.rapports import archive, pieces, service
from app.rapports.models import TYPES_CONTENU, ModeleRapport, Rapport
from app.rapports.router import document, pdf_de
from app.rapports.schemas import PageArchive

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


Archiviste = Annotated[Acces, Depends(exiger_permission("rapports", Action.consulter))]
Exportateur = Annotated[Acces, Depends(exiger_permission("rapports", Action.exporter))]


def _filtres(
    modele: ModeleRapport | None = None,
    etat: Literal["soumis", "a_corriger", "approuve", "refuse"] | None = None,
    club_id: UUID | None = None,
    dre: Annotated[str | None, Query(max_length=30)] = None,
    recherche: Annotated[str | None, Query(max_length=100)] = None,
    du: date | None = None,
    au: date | None = None,
) -> archive.Filtres:
    return archive.Filtres(modele=modele, etat=etat, club_id=club_id, dre=dre, recherche=recherche, du=du, au=au)


Filtres = Annotated[archive.Filtres, Depends(_filtres)]


@router_admin.get("")
async def lister(
    acces: Archiviste, db: Base, filtres: Filtres, page: Annotated[int, Query(ge=1, le=1000)] = 1
) -> PageArchive:
    return PageArchive.model_validate(await archive.lister(db, acces, filtres, page))


@router_admin.get("/export.csv", response_class=Response)
async def exporter_csv(acces: Exportateur, request: Request, db: Base, filtres: Filtres) -> Response:
    octets = await archive.exporter_csv(db, acces, filtres, adresse_ip(request))
    return Response(
        content=octets,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="rapports.csv"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router_admin.get("/{contenu_id}/export.pdf", response_class=Response)
async def exporter_pdf(contenu_id: UUID, acces: Archiviste, db: Base) -> Response:
    try:
        contenu = await archive.visible(db, acces, contenu_id)
        if contenu.etat is not EtatContenu.publie:
            raise HTTPException(status.HTTP_409_CONFLICT, "Seul un rapport approuvé s'exporte en PDF.")
        rapport = await db.get(Rapport, contenu_id)
        assert rapport is not None
        detail = await service.detail(db, acces.utilisateur, contenu, rapport, "encadreur")
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce rapport est introuvable.") from None
    return pdf_de(detail)
