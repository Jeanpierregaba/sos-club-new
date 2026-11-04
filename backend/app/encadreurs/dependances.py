"""Accès réservé aux encadreurs vérifiés (spec 018). Aucune route de R3 n'en a besoin : les clubs (R4) et les
rattachements (R5) s'en serviront, pour qu'un encadreur en attente n'accède à aucune donnée d'élève."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, Utilisateur
from app.db import get_session
from app.encadreurs.models import Encadreur, EtatVerification


async def encadreur_actif(
    utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Utilisateur:
    if utilisateur.role is not Role.encadreur:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux encadreurs.")
    encadreur = await db.get(Encadreur, utilisateur.id)
    if encadreur is None or encadreur.etat is not EtatVerification.actif:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Ton compte encadreur doit d'abord être vérifié par l'équipe des Clubs Santé."
        )
    return utilisateur


EncadreurActif = Annotated[Utilisateur, Depends(encadreur_actif)]
