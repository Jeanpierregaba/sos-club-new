"""Qui peut jouer (spec 027) : un élève au compte actif, ou un encadreur vérifié. Un collaborateur ne joue qu'en
mode test, depuis l'espace admin."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.db import get_session
from app.encadreurs.models import Encadreur, EtatVerification

MESSAGE = "Les quiz sont réservés aux élèves et aux encadreurs inscrits."


async def peut_jouer(db: AsyncSession, utilisateur: Utilisateur) -> bool:
    if utilisateur.statut is not StatutCompte.actif:
        return False
    if utilisateur.role is Role.eleve:
        return True
    if utilisateur.role is Role.encadreur:
        encadreur = await db.get(Encadreur, utilisateur.id)
        return encadreur is not None and encadreur.etat is EtatVerification.actif
    return False


async def joueur_actif(
    utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Utilisateur:
    if not await peut_jouer(db, utilisateur):
        raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE)
    return utilisateur


Joueur = Annotated[Utilisateur, Depends(joueur_actif)]
