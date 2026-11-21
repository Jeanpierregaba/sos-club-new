"""Garde de maintenance (spec 047) : bloque le site sauf exemptions et super-administrateurs."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import Collaborateur
from app.comptes.models import Role, StatutCompte
from app.comptes.service import utilisateur_de_la_session
from app.config import settings
from app.db import get_session
from app.maintenance import service

MESSAGE_MAINTENANCE = "Le site est en maintenance. Réessaie plus tard."

# Chemins API autorisés pendant la maintenance pour permettre à un super-admin de se connecter.
_EXEMPTIONS = {
    ("POST", "/api/comptes/connexion"),
    ("POST", "/api/comptes/connexion/code"),
    ("POST", "/api/comptes/deconnexion"),
    ("GET", "/api/comptes/moi"),
    ("GET", "/api/etat-site"),
}


def _maintenance() -> HTTPException:
    # `raison` permet au client de distinguer la maintenance d'une indisponibilité ordinaire.
    return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, MESSAGE_MAINTENANCE, headers={"X-Raison": "maintenance"})


async def _est_super_admin_bypass(db: AsyncSession, request: Request) -> bool:
    jeton = request.cookies.get(settings.cookie_session)
    if not jeton:
        return False
    utilisateur = await utilisateur_de_la_session(db, jeton)
    if utilisateur is None or utilisateur.role is not Role.admin or utilisateur.statut is not StatutCompte.actif:
        return False
    collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == utilisateur.id))
    if collaborateur is None or not collaborateur.super_admin:
        return False
    return collaborateur.fin_acces is None or collaborateur.fin_acces > datetime.now(UTC)


async def verifier_maintenance(request: Request, db: Annotated[AsyncSession, Depends(get_session)]) -> None:
    try:
        active = await service.maintenance_active(db)
    except Exception:  # noqa: BLE001 - échec fermé : ne jamais ouvrir le site sur erreur inattendue
        raise _maintenance() from None
    if not active:
        return
    if (request.method, request.url.path) in _EXEMPTIONS:
        return
    try:
        if await _est_super_admin_bypass(db, request):
            return
    except Exception:  # noqa: BLE001 - échec fermé : ne jamais ouvrir le site sur erreur inattendue
        raise _maintenance() from None
    raise _maintenance()
