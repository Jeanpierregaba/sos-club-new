"""Routes de l'équipe pour l'agenda (spec 041) : événements nationaux et régionaux, annulation."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.agenda import administration
from app.agenda.router import traduire
from app.agenda.schemas import AnnulationEntree, EvenementEquipeEntree, EvenementPublic
from app.db import get_session

router_admin = APIRouter(prefix="/admin/agenda", tags=["admin"])

Db = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_permission("agenda", Action.consulter))]
Createur = Annotated[Acces, Depends(exiger_permission("agenda", Action.creer))]
Editeur = Annotated[Acces, Depends(exiger_permission("agenda", Action.modifier))]
# Annuler : « modifier » pour un événement de l'équipe, « dépublier » pour un événement de club (vérifié au service).
Annuleur = Annotated[Acces, Depends(exiger_permission("agenda", Action.consulter))]


@router_admin.get("")
async def lister(db: Db, acces: Lecteur, periode: Literal["a_venir", "passe"] = "a_venir") -> list[EvenementPublic]:
    return await administration.lister(db, acces, periode)


@router_admin.post("", status_code=status.HTTP_201_CREATED)
async def creer(entree: EvenementEquipeEntree, request: Request, db: Db, acces: Createur) -> EvenementPublic:
    with traduire():
        return await administration.creer(db, acces, entree, adresse_ip(request))


@router_admin.put("/{evenement_id}")
async def modifier(
    evenement_id: UUID, entree: EvenementEquipeEntree, request: Request, db: Db, acces: Editeur
) -> EvenementPublic:
    with traduire():
        return await administration.modifier(db, acces, evenement_id, entree, adresse_ip(request))


@router_admin.post("/{evenement_id}/annuler")
async def annuler(
    evenement_id: UUID, entree: AnnulationEntree, request: Request, db: Db, acces: Annuleur
) -> EvenementPublic:
    with traduire():
        return await administration.annuler(db, acces, evenement_id, entree.motif, adresse_ip(request))
