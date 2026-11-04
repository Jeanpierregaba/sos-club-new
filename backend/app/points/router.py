"""Administration des points (spec 017) : semestres et barème, sous /admin/points."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.db import get_session
from app.points import administration
from app.points.schemas import (
    LigneBaremeAdmin,
    LigneBaremeModification,
    SemestreAdmin,
    SemestreCreation,
    SemestreModification,
)
from app.referentiel.administration import Introuvable, Refus

Base = Annotated[AsyncSession, Depends(get_session)]

router_admin = APIRouter(prefix="/admin/points", tags=["admin"])

Lecteur = Annotated[Acces, Depends(exiger_permission("points", Action.consulter))]
# Les semestres et le barème valent pour tout le pays : un responsable de DRE ne les change pas.
Modificateur = Annotated[Acces, Depends(exiger_permission("points", Action.modifier, national=True))]


@contextmanager
def _traduire_refus() -> Iterator[None]:
    try:
        yield
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Élément introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_admin.get("/semestres")
async def lister_semestres(_: Lecteur, db: Base) -> list[SemestreAdmin]:
    return await administration.lister_semestres(db)


@router_admin.post("/semestres", status_code=status.HTTP_201_CREATED)
async def creer_semestre(entree: SemestreCreation, request: Request, acces: Modificateur, db: Base) -> SemestreAdmin:
    with _traduire_refus():
        return await administration.creer_semestre(db, acces, entree, adresse_ip(request))


@router_admin.patch("/semestres/{semestre_id}")
async def modifier_semestre(
    semestre_id: UUID, entree: SemestreModification, request: Request, acces: Modificateur, db: Base
) -> SemestreAdmin:
    with _traduire_refus():
        return await administration.modifier_semestre(db, acces, semestre_id, entree, adresse_ip(request))


@router_admin.get("/bareme")
async def lister_bareme(_: Lecteur, db: Base) -> list[LigneBaremeAdmin]:
    return await administration.lister_bareme(db)


@router_admin.patch("/bareme/{code}")
async def modifier_bareme(
    code: str, entree: LigneBaremeModification, request: Request, acces: Modificateur, db: Base
) -> LigneBaremeAdmin:
    with _traduire_refus():
        return await administration.modifier_bareme(db, acces, code, entree, adresse_ip(request))
