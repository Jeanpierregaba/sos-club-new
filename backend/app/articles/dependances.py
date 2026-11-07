"""Qui rédige un article (spec 023) : un élève avec son profil, ou un encadreur vérifié."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, Utilisateur
from app.db import get_session
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification


async def auteur(
    utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Utilisateur:
    if utilisateur.role is Role.eleve and await db.get(Eleve, utilisateur.id) is not None:
        return utilisateur
    if utilisateur.role is Role.encadreur:
        encadreur = await db.get(Encadreur, utilisateur.id)
        if encadreur is not None and encadreur.etat is EtatVerification.actif:
            return utilisateur
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Ton compte encadreur doit d'abord être vérifié par l'équipe des Clubs Santé."
        )
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Seuls les élèves et les encadreurs publient des articles.")


Auteur = Annotated[Utilisateur, Depends(auteur)]
