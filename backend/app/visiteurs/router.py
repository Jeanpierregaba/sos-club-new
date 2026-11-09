"""Compte visiteur (spec 030), sous /visiteurs."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import InscriptionsFermees, Refus, TropDInscriptions
from app.comptes.models import Utilisateur
from app.comptes.router import _poser_cookie
from app.comptes.schemas import Moi
from app.comptes.service import cle_adresse, ouvrir_session, utilisateur_de_la_session
from app.config import settings
from app.db import get_session
from app.visiteurs import service
from app.visiteurs.schemas import (
    CodeEnvoye,
    ConfirmationEntree,
    EspaceVisiteur,
    InscriptionVisiteur,
    RenvoiEntree,
    RenvoiSortie,
)

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/visiteurs", tags=["visiteurs"])


def _adresse(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


@contextmanager
def _traduire() -> Iterator[None]:
    try:
        yield
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None
    except service.PasUnVisiteur:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux visiteurs.") from None


@router.post("/inscription", status_code=status.HTTP_201_CREATED)
async def inscription(entree: InscriptionVisiteur, request: Request, db: Base) -> CodeEnvoye:
    jeton = request.cookies.get(settings.cookie_session)
    if jeton and await utilisateur_de_la_session(db, jeton):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tu es déjà connecté : déconnecte-toi pour créer un compte.")
    try:
        with _traduire():
            return await service.inscrire(db, entree, _adresse(request))
    except InscriptionsFermees:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Les inscriptions ne sont pas encore ouvertes.") from None
    except TropDInscriptions:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Trop d'inscriptions depuis ce réseau. Réessaie dans une heure."
        ) from None
    except service.ServiceIndisponible:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "L'envoi des e-mails est indisponible pour le moment : réessaie un peu plus tard.",
        ) from None


@router.post("/confirmation")
async def confirmation(entree: ConfirmationEntree, request: Request, response: Response, db: Base) -> Moi:
    with _traduire():
        utilisateur = await service.confirmer(db, entree.email, entree.code, _adresse(request))
    # La session valide la transaction : l'adresse confirmée et la session sont écrites ensemble.
    _poser_cookie(response, utilisateur, await ouvrir_session(db, utilisateur, adresse_ip=_adresse(request)))
    return Moi.model_validate(utilisateur)


@router.post("/confirmation/renvoi")
async def renvoi(entree: RenvoiEntree, db: Base) -> RenvoiSortie:
    return RenvoiSortie(code_de_test=await service.renvoyer(db, entree.email))


@router.get("/moi")
async def mon_espace(utilisateur: Connecte, db: Base) -> EspaceVisiteur:
    with _traduire():
        return await service.espace(db, utilisateur)
