"""File de modération (spec 023) sous /admin/moderation : lecture, aperçu et quatre décisions."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.comptes.inscription import Refus
from app.comptes.models import Role
from app.db import get_session
from app.moderation import decisions
from app.moderation.models import EtatContenu
from app.moderation.schemas import ApercuModeration, ApprobationEntree, DecisionModerationEntree, FileModeration
from app.moderation.service import Introuvable

Base = Annotated[AsyncSession, Depends(get_session)]

# Pas de périmètre national exigé : la file est filtrée par la DRE du collaborateur (comme les encadreurs).
Lecteur = Annotated[Acces, Depends(exiger_permission("moderation", Action.consulter))]
Decideur = Annotated[Acces, Depends(exiger_permission("moderation", Action.approuver))]
Depublieur = Annotated[Acces, Depends(exiger_permission("moderation", Action.depublier))]

router_admin = APIRouter(prefix="/admin/moderation", tags=["admin"])


@contextmanager
def _traduire() -> Iterator[None]:
    try:
        yield
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce contenu est introuvable.") from None
    except decisions.Interdit:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu ne peux pas décider de ton propre contenu.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_admin.get("")
async def file_moderation(
    db: Base,
    acces: Lecteur,
    etat: EtatContenu = EtatContenu.en_attente,
    type: str | None = None,
    axe: str | None = None,
    dre: str | None = None,
    profil: Literal["eleve", "encadreur"] | None = None,
) -> FileModeration:
    with _traduire():
        return await decisions.file_attente(
            db, acces, etat, type=type, axe=axe, dre=dre, profil=Role(profil) if profil else None
        )


@router_admin.get("/{contenu_id}")
async def apercu(contenu_id: UUID, db: Base, acces: Lecteur) -> ApercuModeration:
    with _traduire():
        return await decisions.apercu(db, acces, contenu_id)


@router_admin.post("/{contenu_id}/approuver")
async def approuver(
    contenu_id: UUID, entree: ApprobationEntree, request: Request, db: Base, acces: Decideur
) -> ApercuModeration:
    with _traduire():
        await decisions.approuver(db, acces, contenu_id, entree.version, adresse_ip(request))
        return await decisions.apercu(db, acces, contenu_id)


@router_admin.post("/{contenu_id}/corriger")
async def corriger(
    contenu_id: UUID, entree: DecisionModerationEntree, request: Request, db: Base, acces: Decideur
) -> ApercuModeration:
    with _traduire():
        await decisions.demander_correction(db, acces, contenu_id, entree.version, entree.motif, adresse_ip(request))
        return await decisions.apercu(db, acces, contenu_id)


@router_admin.post("/{contenu_id}/refuser")
async def refuser(
    contenu_id: UUID, entree: DecisionModerationEntree, request: Request, db: Base, acces: Decideur
) -> ApercuModeration:
    with _traduire():
        await decisions.refuser(db, acces, contenu_id, entree.version, entree.motif, adresse_ip(request))
        return await decisions.apercu(db, acces, contenu_id)


@router_admin.post("/{contenu_id}/depublier")
async def depublier(
    contenu_id: UUID, entree: DecisionModerationEntree, request: Request, db: Base, acces: Depublieur
) -> ApercuModeration:
    with _traduire():
        await decisions.depublier(db, acces, contenu_id, entree.version, entree.motif, adresse_ip(request))
        return await decisions.apercu(db, acces, contenu_id)
