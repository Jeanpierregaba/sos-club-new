"""Routes de l'agenda (spec 041) : l'agenda du club (encadreurs et président), l'agenda public et les réponses des
membres."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.agenda.types  # noqa: F401  (déclare le type « evenement » au moteur de modération)
from app.admin.dependances import adresse_ip
from app.agenda import public, reponses, service
from app.agenda.models import NiveauEvenement, TypeEvenement
from app.agenda.schemas import (
    AgendaDuClub,
    AnnulationEntree,
    EvenementDuClub,
    EvenementPublic,
    ModificationEntree,
    PageAgenda,
    PresencesEntree,
    ReponseEntree,
    ReponsesEvenement,
    VersionEntree,
)
from app.comptes.dependances import utilisateur_courant, utilisateur_facultatif
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.db import get_session
from app.moderation.service import Introuvable

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router_club = APIRouter(prefix="/clubs/moi/agenda", tags=["agenda"])


@contextmanager
def traduire() -> Iterator[None]:
    try:
        yield
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cet événement est introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_club.get("")
async def agenda_du_club(utilisateur: Connecte, db: Base) -> AgendaDuClub:
    with traduire():
        return await service.agenda_du_club(db, utilisateur)


@router_club.post("", status_code=status.HTTP_201_CREATED)
async def creer(champs: dict[str, Any], utilisateur: Connecte, db: Base) -> EvenementDuClub:
    with traduire():
        return await service.creer(db, utilisateur, champs)


@router_club.get("/{evenement_id}")
async def lire(evenement_id: UUID, utilisateur: Connecte, db: Base) -> EvenementDuClub:
    with traduire():
        return await service.evenement_du_club(db, utilisateur, evenement_id)


@router_club.put("/{evenement_id}")
async def modifier(evenement_id: UUID, entree: ModificationEntree, utilisateur: Connecte, db: Base) -> EvenementDuClub:
    with traduire():
        return await service.modifier(db, utilisateur, evenement_id, entree.version, entree.champs)


@router_club.post("/{evenement_id}/soumettre")
async def soumettre(
    evenement_id: UUID, entree: VersionEntree, request: Request, utilisateur: Connecte, db: Base
) -> EvenementDuClub:
    with traduire():
        return await service.soumettre(db, utilisateur, evenement_id, entree.version, adresse_ip(request))


@router_club.post("/{evenement_id}/retirer")
async def retirer(
    evenement_id: UUID, entree: VersionEntree, request: Request, utilisateur: Connecte, db: Base
) -> EvenementDuClub:
    with traduire():
        return await service.retirer(db, utilisateur, evenement_id, entree.version, adresse_ip(request))


@router_club.delete("/{evenement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer(evenement_id: UUID, version: int, utilisateur: Connecte, db: Base) -> Response:
    with traduire():
        await service.supprimer(db, utilisateur, evenement_id, version)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_club.post("/{evenement_id}/annuler")
async def annuler(
    evenement_id: UUID, entree: AnnulationEntree, request: Request, utilisateur: Connecte, db: Base
) -> EvenementDuClub:
    with traduire():
        return await service.annuler_du_club(db, utilisateur, evenement_id, entree.motif, adresse_ip(request))


@router_club.get("/{evenement_id}/reponses")
async def liste_reponses(evenement_id: UUID, utilisateur: Connecte, db: Base, response: Response) -> ReponsesEvenement:
    # Des données d'élèves : ni le navigateur ni un proxy ne les gardent.
    response.headers["Cache-Control"] = "no-store"
    with traduire():
        return await reponses.reponses(db, utilisateur, evenement_id)


@router_club.put("/{evenement_id}/presences")
async def presences(
    evenement_id: UUID, entree: PresencesEntree, utilisateur: Connecte, db: Base, response: Response
) -> ReponsesEvenement:
    response.headers["Cache-Control"] = "no-store"
    with traduire():
        return await reponses.pointer(db, utilisateur, evenement_id, entree.presences)


# Public et membres ---------------------------------------------------------------------------------------------

router = APIRouter(prefix="/agenda", tags=["agenda"])
Facultatif = Annotated[Utilisateur | None, Depends(utilisateur_facultatif)]


@router.get("")
async def agenda(
    db: Base,
    periode: Literal["a_venir", "passe"] = "a_venir",
    dre: str | None = None,
    club: UUID | None = None,
    type: TypeEvenement | None = None,
    axe: str | None = None,
    niveau: NiveauEvenement | None = None,
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
) -> PageAgenda:
    return await public.lister(db, periode=periode, dre=dre, club=club, type=type, axe=axe, niveau=niveau, page=page)


@router.get("/prochains")
async def prochains(db: Base) -> list[EvenementPublic]:
    return await public.prochains(db)


@router.get("/mes-evenements")
async def mes_evenements(utilisateur: Connecte, db: Base, response: Response) -> list[EvenementPublic]:
    response.headers["Cache-Control"] = "no-store"
    if utilisateur.role is not Role.eleve:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux élèves.")
    return await public.mes_evenements(db, utilisateur)


@router.get("/{evenement_id}")
async def evenement(evenement_id: UUID, db: Base, moi: Facultatif, response: Response) -> EvenementPublic:
    if moi is not None:
        # La réponse d'un membre y figure : elle ne se garde pas en cache.
        response.headers["Cache-Control"] = "no-store"
    with traduire():
        return await public.detail(db, evenement_id, moi)


@router.put("/{evenement_id}/reponse")
async def repondre(evenement_id: UUID, entree: ReponseEntree, utilisateur: Connecte, db: Base) -> EvenementPublic:
    with traduire():
        await reponses.repondre(db, utilisateur, evenement_id, entree.reponse)
        return await public.detail(db, evenement_id, utilisateur)
