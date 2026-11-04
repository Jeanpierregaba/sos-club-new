from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.double_auth import verifier_code
from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Utilisateur
from app.comptes.schemas import CodeEntree, ConnexionEntree, EtapeCode, Moi, MotDePasseEntree
from app.comptes.service import (
    AccesTermine,
    CodeIncorrect,
    CompteInvalide,
    CompteSuspendu,
    EtapeInvalide,
    IdentifiantsIncorrects,
    MotDePasseIncorrect,
    TropDEssais,
    changer_mot_de_passe,
    cle_adresse,
    connecter,
    connecter_avec_code,
    deconnecter,
    duree_session,
)
from app.config import settings
from app.db import get_session

router = APIRouter(prefix="/comptes", tags=["comptes"])

Base = Annotated[AsyncSession, Depends(get_session)]


TROP_D_ESSAIS = "Trop d'essais. Réessaie dans 15 minutes."


def _poser_cookie(response: Response, utilisateur: Utilisateur, jeton: str) -> None:
    response.set_cookie(
        settings.cookie_session,
        jeton,
        max_age=int(duree_session(utilisateur.role).total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post("/connexion")
async def connexion(entree: ConnexionEntree, request: Request, response: Response, db: Base) -> Moi | EtapeCode:
    adresse_ip = cle_adresse(request.client.host if request.client else None)
    try:
        resultat = await connecter(
            db, entree.identifiant, entree.mot_de_passe, adresse_ip, request.cookies.get(settings.cookie_session)
        )
    except TropDEssais:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, TROP_D_ESSAIS) from None
    except IdentifiantsIncorrects:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiant ou mot de passe incorrect") from None
    except CompteSuspendu:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Ce compte est suspendu. Contacte un encadreur ou l'équipe nationale."
        ) from None
    except AccesTermine:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ton accès à l'espace admin a pris fin.") from None

    if resultat.jeton_etape:
        return EtapeCode(jeton=resultat.jeton_etape)
    assert resultat.jeton_session
    _poser_cookie(response, resultat.utilisateur, resultat.jeton_session)
    return Moi.model_validate(resultat.utilisateur)


@router.post("/connexion/code")
async def connexion_code(entree: CodeEntree, request: Request, response: Response, db: Base) -> Moi:
    adresse_ip = cle_adresse(request.client.host if request.client else None)
    try:
        resultat = await connecter_avec_code(
            db, entree.jeton, entree.code, adresse_ip, verifier_code, request.cookies.get(settings.cookie_session)
        )
    except EtapeInvalide:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ce délai est dépassé. Reconnecte-toi.") from None
    except AccesTermine:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ton accès à l'espace admin a pris fin.") from None
    except TropDEssais:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, TROP_D_ESSAIS) from None
    except CodeIncorrect:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Code incorrect.") from None

    assert resultat.jeton_session
    _poser_cookie(response, resultat.utilisateur, resultat.jeton_session)
    return Moi.model_validate(resultat.utilisateur)


@router.post("/deconnexion", status_code=status.HTTP_204_NO_CONTENT)
async def deconnexion(request: Request, response: Response, db: Base) -> None:
    jeton = request.cookies.get(settings.cookie_session)
    if jeton:
        await deconnecter(db, jeton)
    response.delete_cookie(settings.cookie_session, httponly=True, secure=settings.cookie_secure, samesite="lax")


@router.get("/moi")
async def moi(utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)]) -> Moi:
    return Moi.model_validate(utilisateur)


@router.post("/mot-de-passe", status_code=status.HTTP_204_NO_CONTENT)
async def changer_mon_mot_de_passe(
    entree: MotDePasseEntree,
    request: Request,
    utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    db: Base,
) -> None:
    jeton = request.cookies.get(settings.cookie_session, "")
    adresse_ip = cle_adresse(request.client.host if request.client else None)
    try:
        await changer_mot_de_passe(db, utilisateur, entree.actuel, entree.nouveau, jeton, adresse_ip)
    except MotDePasseIncorrect:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ton mot de passe actuel est incorrect.") from None
    except TropDEssais:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, TROP_D_ESSAIS) from None
    except CompteInvalide as erreur:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erreur)) from None
