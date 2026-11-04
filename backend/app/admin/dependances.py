"""Contrôle d'accès de l'espace administrateur (spec 015, ADR-0008). Le site masque ; ici, on refuse."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import SENSIBLES, Action
from app.admin.double_auth import double_auth_active
from app.admin.journal import journaliser
from app.admin.models import Collaborateur, Permission
from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, Utilisateur
from app.comptes.service import cle_adresse, couper_sessions
from app.db import get_session

MESSAGE_REFUS = "Tu n'as pas accès à cette page."
MESSAGE_DOUBLE_AUTH = "Active la double authentification pour continuer."


@dataclass
class Acces:
    utilisateur: Utilisateur
    collaborateur: Collaborateur
    droits: set[tuple[str, Action]] = field(default_factory=set)
    double_auth_active: bool = False

    def a(self, module: str, action: Action) -> bool:
        return self.collaborateur.super_admin or (module, action) in self.droits

    @property
    def double_auth_requise(self) -> bool:
        sensible = self.collaborateur.super_admin or bool(self.droits & SENSIBLES)
        return sensible and not self.double_auth_active

    @property
    def national(self) -> bool:
        return self.collaborateur.perimetre_dre is None


def adresse_ip(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


async def collaborateur_courant(
    request: Request,
    utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Acces:
    if utilisateur.role is not Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_REFUS)
    collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == utilisateur.id))
    if collaborateur is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_REFUS)

    if collaborateur.fin_acces and collaborateur.fin_acces <= datetime.now(UTC):
        await couper_sessions(db, utilisateur.id)
        journaliser(
            db,
            "fin_acces_atteinte",
            utilisateur,
            cible_type="collaborateur",
            cible_id=collaborateur.id,
            adresse_ip=adresse_ip(request),
        )
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ton accès à l'espace admin a pris fin.")

    lignes = await db.execute(
        select(Permission.module, Permission.action).where(Permission.collaborateur_id == collaborateur.id)
    )
    return Acces(
        utilisateur=utilisateur,
        collaborateur=collaborateur,
        droits={(module, Action(action)) for module, action in lignes},
        double_auth_active=await double_auth_active(db, utilisateur.id),
    )


Collaborateur_ = Annotated[Acces, Depends(collaborateur_courant)]


async def refuser(db: AsyncSession, request: Request, acces: Acces, droit: str) -> None:
    """Journalise le refus, puis répond 403."""
    journaliser(
        db,
        "acces_refuse",
        acces.utilisateur,
        perimetre=acces.collaborateur.perimetre_dre or "national",
        details={"droit": droit, "route": f"{request.method} {request.url.path}"},
        adresse_ip=adresse_ip(request),
    )
    await db.commit()
    raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_REFUS)


def exiger_permission(module: str, action: Action, *, national: bool = False) -> Callable[..., Awaitable[Acces]]:
    """Exige le droit (module, action), la double authentification si le collaborateur a un droit sensible et,
    pour les données nominatives, le périmètre national."""

    async def verifier(
        request: Request, acces: Collaborateur_, db: Annotated[AsyncSession, Depends(get_session)]
    ) -> Acces:
        if acces.double_auth_requise:
            raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_DOUBLE_AUTH)
        if not acces.a(module, action) or (national and not acces.national):
            await refuser(db, request, acces, f"{module}:{action.value}")
        return acces

    return verifier


def exiger_super_admin_pour(droit: str) -> Callable[..., Awaitable[Acces]]:
    """Réservé au super-administrateur ; `droit` nomme l'opération dans le journal des refus."""

    async def verifier(
        request: Request, acces: Collaborateur_, db: Annotated[AsyncSession, Depends(get_session)]
    ) -> Acces:
        if acces.double_auth_requise:
            raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_DOUBLE_AUTH)
        if not acces.collaborateur.super_admin:
            await refuser(db, request, acces, droit)
        return acces

    return verifier


# La gestion des collaborateurs et des droits ne se délègue pas dans ce lot (stress-test du 2026-11-04).
exiger_super_admin = exiger_super_admin_pour("collaborateurs:gerer")
