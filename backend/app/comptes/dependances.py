from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, Utilisateur
from app.comptes.service import utilisateur_de_la_session
from app.config import settings
from app.db import get_session

METHODES_SANS_EFFET = {"GET", "HEAD", "OPTIONS"}


async def verifier_origine(request: Request) -> None:
    """Refuse les écritures venues d'un autre site (CSRF). Un appel sans Origin ne vient pas d'un navigateur."""
    if request.method in METHODES_SANS_EFFET:
        return
    origine = request.headers.get("origin")
    if origine is not None and origine != settings.site_origine:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cette action ne peut venir que du site.")


async def utilisateur_courant(request: Request, db: Annotated[AsyncSession, Depends(get_session)]) -> Utilisateur:
    jeton = request.cookies.get(settings.cookie_session)
    utilisateur = await utilisateur_de_la_session(db, jeton) if jeton else None
    # Le jeton d'un joueur sans compte (spec 031) ne vaut que pour /jeux/quiz, jamais comme session.
    if utilisateur is None or utilisateur.role is Role.invite:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Connecte-toi pour continuer.")
    return utilisateur


def exiger_role(*roles: Role) -> Callable[..., Awaitable[Utilisateur]]:
    async def verifier_role(utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)]) -> Utilisateur:
        if utilisateur.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu n'as pas accès à cette page.")
        return utilisateur

    return verifier_role


async def utilisateur_facultatif(
    request: Request, db: Annotated[AsyncSession, Depends(get_session)]
) -> Utilisateur | None:
    """L'utilisateur connecté, ou None pour un visiteur : pour une route publique qui en fait plus pour un compte."""
    jeton = request.cookies.get(settings.cookie_session)
    utilisateur = await utilisateur_de_la_session(db, jeton) if jeton else None
    return None if utilisateur is None or utilisateur.role is Role.invite else utilisateur
