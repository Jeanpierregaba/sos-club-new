"""Rapports (spec 038) : dépôt et lecture par les encadreurs et le président du club, sous /rapports.

Aucune route publique : un rapport n'existe que pour son auteur, les encadreurs de son club et, pour un rapport
d'activité, le président (404 pour tout autre)."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import adresse_ip
from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.config import settings
from app.db import get_session
from app.fichiers import reponse
from app.moderation.service import Introuvable
from app.points.models import Semestre
from app.points.service import aujourd_hui, maintenant
from app.rapports import export_pdf, pieces, service
from app.rapports import types as _types  # noqa: F401 : déclare les trois types au moteur de modération
from app.rapports.models import PieceRapport
from app.rapports.schemas import (
    Creation,
    MesRapports,
    Modification,
    RapportDetail,
    SemestreRapport,
    TypeActivite,
    VersionEntree,
)

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/rapports", tags=["rapports"])


@contextmanager
def _traduire() -> Iterator[None]:
    try:
        yield
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce rapport est introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router.get("")
async def lister(utilisateur: Connecte, db: Base) -> MesRapports:
    with _traduire():
        return await service.mes_rapports(db, utilisateur)


@router.get("/types-activite")
async def types_activite(_: Connecte, db: Base) -> list[TypeActivite]:
    return [TypeActivite(code=t.code, libelle=t.libelle) for t in await service.types_activite(db)]


@router.get("/semestres")
async def semestres(_: Connecte, db: Base) -> list[SemestreRapport]:
    """Les semestres commencés, du plus récent au plus ancien : ceux qu'un bilan peut couvrir."""
    lignes = await db.scalars(
        select(Semestre).where(Semestre.debut <= aujourd_hui()).order_by(Semestre.debut.desc()).limit(6)
    )
    return [SemestreRapport(id=s.id, libelle=s.libelle, debut=s.debut, fin=s.fin) for s in lignes.all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def creer(entree: Creation, utilisateur: Connecte, db: Base) -> RapportDetail:
    with _traduire():
        return await service.creer(db, utilisateur, entree.modele)


@router.get("/{contenu_id}")
async def lire(contenu_id: UUID, utilisateur: Connecte, db: Base) -> RapportDetail:
    with _traduire():
        return await service.lire(db, utilisateur, contenu_id)


@router.put("/{contenu_id}")
async def modifier(contenu_id: UUID, entree: Modification, utilisateur: Connecte, db: Base) -> RapportDetail:
    with _traduire():
        return await service.modifier(db, utilisateur, contenu_id, entree.version, entree.donnees)


@router.delete("/{contenu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer(contenu_id: UUID, utilisateur: Connecte, db: Base) -> Response:
    with _traduire():
        await service.supprimer(db, utilisateur, contenu_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{contenu_id}/soumission")
async def soumettre(
    contenu_id: UUID, entree: VersionEntree, request: Request, utilisateur: Connecte, db: Base
) -> RapportDetail:
    with _traduire():
        return await service.soumettre(db, utilisateur, contenu_id, entree.version, adresse_ip(request))


# Justificatifs ---------------------------------------------------------------------------------------------------


def document(piece: PieceRapport, octets: bytes) -> Response:
    """Toujours en pièce jointe, jamais affiché dans le navigateur ni gardé en cache."""
    return Response(
        content=octets,
        media_type=pieces.TYPES_MEDIA[piece.type],
        headers={
            "Content-Disposition": f'attachment; filename="{piece.nom}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
        },
    )


@router.post("/{contenu_id}/documents")
async def ajouter_document(
    contenu_id: UUID,
    utilisateur: Connecte,
    db: Base,
    fichier: Annotated[UploadFile, File()],
    version: Annotated[int, Form()],
) -> RapportDetail:
    octets = await fichier.read(pieces.OCTETS_MAX + 1)
    if len(octets) > pieces.OCTETS_MAX:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Ce document dépasse 10 Mo.")
    with _traduire():
        return await pieces.ajouter_document(db, utilisateur, contenu_id, version, fichier.filename, octets)


@router.delete("/{contenu_id}/documents/{piece_id}")
async def retirer_document(
    contenu_id: UUID, piece_id: UUID, version: int, utilisateur: Connecte, db: Base
) -> RapportDetail:
    with _traduire():
        return await pieces.retirer_document(db, utilisateur, contenu_id, piece_id, version)


@router.get("/{contenu_id}/documents/{piece_id}", response_class=Response)
async def lire_document(contenu_id: UUID, piece_id: UUID, utilisateur: Connecte, db: Base) -> Response:
    with _traduire():
        piece, octets = await pieces.lire_document(db, utilisateur, contenu_id, piece_id)
    return document(piece, octets)


@router.post("/{contenu_id}/photos")
async def ajouter_photo(
    contenu_id: UUID,
    request: Request,
    utilisateur: Connecte,
    db: Base,
    fichier: Annotated[UploadFile, File()],
    version: Annotated[int, Form()],
    attestation: Annotated[bool, Form()] = False,
    legende: Annotated[str | None, Form(max_length=200)] = None,
) -> RapportDetail:
    if not attestation:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Coche l'attestation : les personnes photographiées, ou leurs parents pour les mineurs, ont accepté la "
            "prise de vue.",
        )
    octets = await fichier.read(settings.photo_octets_max + 1)
    if len(octets) > settings.photo_octets_max:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Cette photo dépasse {settings.photo_octets_max // (1024 * 1024)} Mo : réduis-la avant de l'envoyer.",
        )
    with _traduire():
        return await pieces.ajouter_photo(
            db, utilisateur, contenu_id, version, octets, (legende or "").strip() or None, adresse_ip(request)
        )


@router.delete("/{contenu_id}/photos/{photo_id}")
async def retirer_photo(
    contenu_id: UUID, photo_id: UUID, version: int, request: Request, utilisateur: Connecte, db: Base
) -> RapportDetail:
    with _traduire():
        return await pieces.retirer_photo(db, utilisateur, contenu_id, photo_id, version, adresse_ip(request))


@router.get("/{contenu_id}/photos/{photo_id}/{taille}", response_class=Response)
async def lire_photo(
    contenu_id: UUID, photo_id: UUID, taille: Literal["grande", "vignette"], utilisateur: Connecte, db: Base
) -> Response:
    with _traduire():
        octets = await pieces.lire_photo(db, utilisateur, contenu_id, photo_id, taille)
    return reponse.image(octets, publique=False)


@router.get("/{contenu_id}/export.pdf", response_class=Response)
async def exporter_pdf(contenu_id: UUID, utilisateur: Connecte, db: Base) -> Response:
    """Le PDF d'un rapport approuvé, pour ses lecteurs ; il n'est jamais stocké."""
    with _traduire():
        rapport = await service.pour_export(db, utilisateur, contenu_id)
    return pdf_de(rapport)


def pdf_de(rapport: RapportDetail) -> Response:
    octets = export_pdf.generer(rapport, maintenant())
    return Response(
        content=octets,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{rapport.reference or "rapport"}.pdf"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
