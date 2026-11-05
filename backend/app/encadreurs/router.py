"""Compte encadreur (spec 018) : inscription et espace sous /encadreurs, vérification sous /admin/encadreurs."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.clubs import rattachements
from app.clubs.schemas import MesClubs
from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import InscriptionsFermees, Refus, TropDInscriptions
from app.comptes.models import Utilisateur
from app.comptes.router import _poser_cookie
from app.comptes.schemas import Moi
from app.comptes.service import cle_adresse, ouvrir_session, utilisateur_de_la_session
from app.config import settings
from app.db import get_session
from app.encadreurs import service, verification
from app.encadreurs.models import EtatVerification
from app.encadreurs.schemas import (
    ActivationEntree,
    DemandeEncadreur,
    EspaceEncadreur,
    FileEncadreurs,
    InscriptionEncadreur,
    ProfilEncadreurModification,
    RefusEntree,
)

Base = Annotated[AsyncSession, Depends(get_session)]

Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/encadreurs", tags=["encadreurs"])
router_admin = APIRouter(prefix="/admin/encadreurs", tags=["admin"])

# Pas de périmètre national exigé : la file est filtrée par la DRE du collaborateur (ADR-0008, note du 2026-11-04).
Lecteur = Annotated[Acces, Depends(exiger_permission("encadreurs", Action.consulter))]
Decideur = Annotated[Acces, Depends(exiger_permission("encadreurs", Action.approuver))]


@contextmanager
def _traduire_refus() -> Iterator[None]:
    try:
        yield
    except verification.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette demande est introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None
    except service.PasUnEncadreur:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux encadreurs.") from None
    except service.ProfilAbsent:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Ton profil d'encadreur est incomplet : contacte l'équipe des Clubs Santé."
        ) from None


def _adresse(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


# Inscription et espace -----------------------------------------------------------------------------------------


@router.post("/inscription", status_code=status.HTTP_201_CREATED)
async def inscription(entree: InscriptionEncadreur, request: Request, response: Response, db: Base) -> Moi:
    jeton = request.cookies.get(settings.cookie_session)
    if jeton and await utilisateur_de_la_session(db, jeton):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tu es déjà connecté : déconnecte-toi pour créer un compte.")
    try:
        with _traduire_refus():
            utilisateur = await service.inscrire(db, entree, _adresse(request))
    except InscriptionsFermees:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Les inscriptions ne sont pas encore ouvertes.") from None
    except TropDInscriptions:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Trop d'inscriptions depuis ce réseau. Réessaie dans une heure."
        ) from None
    # La session valide la transaction : le compte et son profil sont écrits ensemble.
    _poser_cookie(response, utilisateur, await ouvrir_session(db, utilisateur, adresse_ip=_adresse(request)))
    return Moi.model_validate(utilisateur)


@router.get("/moi")
async def mon_espace(utilisateur: Connecte, db: Base) -> EspaceEncadreur:
    with _traduire_refus():
        return await service.espace(db, utilisateur)


@router.patch("/moi")
async def modifier_mon_profil(
    entree: ProfilEncadreurModification, request: Request, utilisateur: Connecte, db: Base
) -> EspaceEncadreur:
    with _traduire_refus():
        return await service.modifier_profil(db, utilisateur, entree, _adresse(request))


@router.get("/moi/clubs")
async def mes_clubs(utilisateur: Connecte, db: Base) -> MesClubs:
    """Les rattachements de l'encadreur (spec 020) : en cours, puis les derniers terminés."""
    with _traduire_refus():
        return await rattachements.mes_clubs(db, utilisateur)


@router.post("/moi/renvoyer")
async def renvoyer_ma_demande(request: Request, utilisateur: Connecte, db: Base) -> EspaceEncadreur:
    with _traduire_refus():
        return await service.renvoyer(db, utilisateur, _adresse(request))


# Vérification par l'espace admin --------------------------------------------------------------------------------


@router_admin.get("")
async def file_attente(
    acces: Lecteur, db: Base, etat: Literal["en_attente", "refuse"] = "en_attente"
) -> FileEncadreurs:
    # Pas « actif » : la file n'est pas un annuaire nominatif des encadreurs (ADR-0008).
    return await verification.file_attente(db, acces, EtatVerification(etat))


@router_admin.post("/{utilisateur_id}/activer")
async def activer(
    utilisateur_id: UUID, request: Request, acces: Decideur, db: Base, entree: ActivationEntree | None = None
) -> DemandeEncadreur:
    with _traduire_refus():
        return await verification.activer(
            db, acces, utilisateur_id, adresse_ip(request), entree.version if entree else None
        )


@router_admin.post("/{utilisateur_id}/refuser")
async def refuser(
    utilisateur_id: UUID, entree: RefusEntree, request: Request, acces: Decideur, db: Base
) -> DemandeEncadreur:
    with _traduire_refus():
        return await verification.refuser(db, acces, utilisateur_id, entree.motif, adresse_ip(request), entree.version)
