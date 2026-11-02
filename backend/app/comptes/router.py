from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import exiger_role, utilisateur_courant
from app.comptes.models import Role, Utilisateur
from app.comptes.schemas import ChiffresAdmin, ComptesParRole, ConnexionEntree, Moi
from app.comptes.service import (
    CompteSuspendu,
    IdentifiantsIncorrects,
    TropDEssais,
    cle_adresse,
    compter_comptes_par_role,
    connecter,
    deconnecter,
    duree_session,
)
from app.config import settings
from app.db import get_session

router = APIRouter(prefix="/comptes", tags=["comptes"])
router_admin = APIRouter(prefix="/admin", tags=["admin"])

Base = Annotated[AsyncSession, Depends(get_session)]


@router.post("/connexion")
async def connexion(entree: ConnexionEntree, request: Request, response: Response, db: Base) -> Moi:
    adresse_ip = cle_adresse(request.client.host if request.client else None)
    try:
        utilisateur, jeton = await connecter(
            db, entree.identifiant, entree.mot_de_passe, adresse_ip, request.cookies.get(settings.cookie_session)
        )
    except TropDEssais:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Trop d'essais. Réessaie dans 15 minutes.") from None
    except IdentifiantsIncorrects:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiant ou mot de passe incorrect") from None
    except CompteSuspendu:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Ce compte est suspendu. Contacte un encadreur ou l'équipe nationale."
        ) from None

    response.set_cookie(
        settings.cookie_session,
        jeton,
        max_age=int(duree_session(utilisateur.role).total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return Moi.model_validate(utilisateur)


@router.post("/deconnexion", status_code=status.HTTP_204_NO_CONTENT)
async def deconnexion(request: Request, response: Response, db: Base) -> None:
    jeton = request.cookies.get(settings.cookie_session)
    if jeton:
        await deconnecter(db, jeton)
    response.delete_cookie(settings.cookie_session, httponly=True, secure=settings.cookie_secure, samesite="lax")


@router.get("/moi")
async def moi(utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)]) -> Moi:
    return Moi.model_validate(utilisateur)


@router_admin.get("/chiffres", dependencies=[Depends(exiger_role(Role.admin))])
async def chiffres(db: Base) -> ChiffresAdmin:
    return ChiffresAdmin(comptes=ComptesParRole(**await compter_comptes_par_role(db)))
