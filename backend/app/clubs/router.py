"""Clubs (spec 019) : demande et espace de l'élève sous /clubs, lecture publique, vérification sous /admin/clubs."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.clubs import service, verification
from app.clubs.models import EtatClub
from app.clubs.schemas import (
    ActivationEntree,
    ClubFiche,
    ClubPublic,
    ClubResume,
    DemandeClub,
    DemandeClubEntree,
    FileClubs,
    FilePassations,
    MonClub,
    Passation,
    PassationApercu,
    PassationEntree,
    RefusEntree,
)
from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.comptes.service import cle_adresse
from app.db import get_session

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/clubs", tags=["clubs"])
router_admin = APIRouter(prefix="/admin/clubs", tags=["admin"])

Lecteur = Annotated[Acces, Depends(exiger_permission("clubs", Action.consulter))]
Decideur = Annotated[Acces, Depends(exiger_permission("clubs", Action.approuver))]


@contextmanager
def _traduire_refus() -> Iterator[None]:
    try:
        yield
    except verification.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce club est introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None
    except service.PasUnEleve:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux élèves.") from None


def _adresse(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


# Élève ------------------------------------------------------------------------------------------------------


@router.post("/demande", status_code=status.HTTP_201_CREATED)
async def demander(entree: DemandeClubEntree, request: Request, utilisateur: Connecte, db: Base) -> ClubResume:
    with _traduire_refus():
        return await service.demarrer(db, utilisateur, entree, _adresse(request))


@router.post("/demande/renvoyer")
async def renvoyer_ma_demande(request: Request, utilisateur: Connecte, db: Base) -> ClubResume:
    with _traduire_refus():
        return await service.renvoyer(db, utilisateur, _adresse(request))


@router.get("/moi")
async def mon_club(utilisateur: Connecte, db: Base) -> MonClub:
    with _traduire_refus():
        return await service.mon_club(db, utilisateur)


@router.post("/moi/passation", status_code=status.HTTP_201_CREATED)
async def proposer_passation(
    entree: PassationEntree, request: Request, utilisateur: Connecte, db: Base
) -> PassationApercu:
    with _traduire_refus():
        return await service.proposer_passation(db, utilisateur, entree, _adresse(request))


@router.post("/moi/passation/annuler")
async def annuler_passation(request: Request, utilisateur: Connecte, db: Base) -> PassationApercu:
    with _traduire_refus():
        return await service.annuler_passation(db, utilisateur, _adresse(request))


# Public -----------------------------------------------------------------------------------------------------


@router.get("")
async def lister_clubs(db: Base) -> list[ClubPublic]:
    return await service.clubs_publics(db)


@router.get("/par-etablissement", response_model=None)
async def club_de_letablissement(etablissement_id: UUID, db: Base) -> ClubPublic | Response:
    club = await service.club_par_etablissement(db, etablissement_id)
    if club is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return club


@router.get("/{club_id}")
async def fiche_club(club_id: UUID, db: Base) -> ClubFiche:
    club = await service.club_public(db, club_id)
    if club is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce club est introuvable.")
    return club


# Vérification par l'espace admin -----------------------------------------------------------------------------


@router_admin.get("")
async def file_attente(
    acces: Lecteur,
    db: Base,
    etat: Literal["en_attente", "refuse"] = "en_attente",
    page: Annotated[int, Query(ge=1)] = 1,
    par_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> FileClubs:
    return await verification.file_attente(db, acces, EtatClub(etat), page, par_page)


@router_admin.get("/passations")
async def file_passations(acces: Lecteur, db: Base) -> FilePassations:
    return await verification.file_passations(db, acces)


@router_admin.post("/passations/{passation_id}/valider")
async def valider_passation(
    passation_id: UUID, request: Request, acces: Decideur, db: Base, entree: ActivationEntree | None = None
) -> Passation:
    with _traduire_refus():
        return await verification.valider_passation(
            db, acces, passation_id, adresse_ip(request), entree.version if entree else None
        )


@router_admin.post("/passations/{passation_id}/refuser")
async def refuser_passation(
    passation_id: UUID, entree: RefusEntree, request: Request, acces: Decideur, db: Base
) -> Passation:
    with _traduire_refus():
        return await verification.refuser_passation(
            db, acces, passation_id, entree.motif, adresse_ip(request), entree.version
        )


@router_admin.post("/{club_id}/activer")
async def activer(
    club_id: UUID, request: Request, acces: Decideur, db: Base, entree: ActivationEntree | None = None
) -> DemandeClub:
    with _traduire_refus():
        return await verification.activer(db, acces, club_id, adresse_ip(request), entree.version if entree else None)


@router_admin.post("/{club_id}/refuser")
async def refuser(club_id: UUID, entree: RefusEntree, request: Request, acces: Decideur, db: Base) -> DemandeClub:
    with _traduire_refus():
        return await verification.refuser(db, acces, club_id, entree.motif, adresse_ip(request), entree.version)
