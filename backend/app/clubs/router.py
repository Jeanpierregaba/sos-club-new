"""Clubs (spec 019) : demande et espace de l'élève sous /clubs, lecture publique, vérification sous /admin/clubs.
Affiliations et rattachements (spec 020) : demandes, décisions du président, files des collaborateurs."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.clubs import adhesions, service, verification
from app.clubs.models import EtatClub
from app.clubs.schemas import (
    ActivationEntree,
    AdhesionResume,
    ClubFiche,
    ClubPublic,
    ClubResume,
    DecisionEntree,
    DemandeAdhesion,
    DemandeClub,
    DemandeClubEntree,
    FileClubs,
    FilePassations,
    MonClub,
    Passation,
    PassationApercu,
    PassationEntree,
    RefusDemandeEntree,
    RefusEntree,
    RetraitEntree,
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


# Affiliations (spec 020) : l'élève demande ou se retire, le président confirme, refuse ou retire ---------------


@router.post("/{club_id}/adhesions", status_code=status.HTTP_201_CREATED)
async def demander_adhesion(club_id: UUID, request: Request, utilisateur: Connecte, db: Base) -> AdhesionResume:
    with _traduire_refus():
        return await adhesions.demander(db, utilisateur, club_id, _adresse(request))


@router.delete("/{club_id}/adhesions/moi")
async def quitter_le_club(club_id: UUID, request: Request, utilisateur: Connecte, db: Base) -> AdhesionResume:
    """Annule la demande en cours, ou quitte le club."""
    with _traduire_refus():
        return await adhesions.se_retirer(db, utilisateur, club_id, _adresse(request))


@router.get("/{club_id}/adhesions/demandes")
async def demandes_adhesion(club_id: UUID, utilisateur: Connecte, db: Base) -> list[DemandeAdhesion]:
    with _traduire_refus():
        return await adhesions.demandes_a_confirmer(db, utilisateur, club_id)


@router.post("/{club_id}/adhesions/{adhesion_id}/confirmer")
async def confirmer_adhesion(
    club_id: UUID, adhesion_id: UUID, entree: DecisionEntree, request: Request, utilisateur: Connecte, db: Base
) -> AdhesionResume:
    with _traduire_refus():
        return await adhesions.confirmer(db, utilisateur, club_id, adhesion_id, entree.version, _adresse(request))


@router.post("/{club_id}/adhesions/{adhesion_id}/refuser")
async def refuser_adhesion(
    club_id: UUID, adhesion_id: UUID, entree: RefusDemandeEntree, request: Request, utilisateur: Connecte, db: Base
) -> AdhesionResume:
    with _traduire_refus():
        return await adhesions.refuser(
            db, utilisateur, club_id, adhesion_id, entree.motif, entree.version, _adresse(request)
        )


@router.post("/{club_id}/adhesions/{adhesion_id}/retirer")
async def retirer_membre(
    club_id: UUID, adhesion_id: UUID, entree: RetraitEntree, request: Request, utilisateur: Connecte, db: Base
) -> AdhesionResume:
    with _traduire_refus():
        return await adhesions.retirer(
            db, utilisateur, club_id, adhesion_id, entree.motif, entree.version, _adresse(request)
        )


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
