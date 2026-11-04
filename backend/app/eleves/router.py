"""Inscription et espace de l'élève (spec 017), sous /eleves."""

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
from app.eleves import service
from app.eleves.schemas import EspaceEleve, EtatInscription, InscriptionEntree, ProfilModification

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/eleves", tags=["eleves"])


def _adresse(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


@contextmanager
def _traduire_refus() -> Iterator[None]:
    try:
        yield
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None
    except service.PasUnEleve:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux élèves.") from None


@router.get("/inscription")
async def etat_inscription() -> EtatInscription:
    return EtatInscription(ouvertes=settings.inscriptions_actives, version_charte=settings.version_charte)


@router.post("/inscription", status_code=status.HTTP_201_CREATED)
async def inscription(entree: InscriptionEntree, request: Request, response: Response, db: Base) -> Moi:
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
    # La session valide la transaction : le compte, son profil et ses points de bienvenue sont écrits ensemble.
    _poser_cookie(response, utilisateur, await ouvrir_session(db, utilisateur, adresse_ip=_adresse(request)))
    return Moi.model_validate(utilisateur)


@router.get("/moi")
async def mon_espace(utilisateur: Connecte, db: Base) -> EspaceEleve:
    with _traduire_refus():
        return await service.espace(db, utilisateur)


@router.patch("/moi")
async def modifier_mon_profil(
    entree: ProfilModification, request: Request, utilisateur: Connecte, db: Base
) -> EspaceEleve:
    with _traduire_refus():
        return await service.modifier_profil(db, utilisateur, entree, _adresse(request))
