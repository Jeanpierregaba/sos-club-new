"""Jeux de l'accueil (spec 021) : « Quel axe est fait pour toi ? », réservé aux élèves actifs, et le défi du
jour, ouvert à tous. Aucun point n'est gagné et rien n'est enregistré."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.db import get_session
from app.jeux import defis, quel_axe
from app.jeux.schemas import (
    CorrectionDefi,
    DefiDuJour,
    QuestionnaireQuelAxe,
    QuestionQuelAxe,
    ReponseDefi,
    ReponseQuelAxe,
    ReponsesQuelAxe,
    ResultatQuelAxe,
)

router = APIRouter(prefix="/jeux", tags=["jeux"])


async def eleve_actif(utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)]) -> Utilisateur:
    """Le jeu est réservé aux élèves inscrits, au compte actif : vérifié ici, pas seulement dans le site."""
    if utilisateur.role is not Role.eleve or utilisateur.statut is not StatutCompte.actif:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ce jeu est réservé aux élèves inscrits.")
    return utilisateur


EleveActif = Annotated[Utilisateur, Depends(eleve_actif)]


@router.get("/quel-axe")
async def questionnaire_quel_axe(_: EleveActif) -> QuestionnaireQuelAxe:
    return QuestionnaireQuelAxe(
        questions=[
            QuestionQuelAxe(
                numero=numero,
                libelle=question.libelle,
                reponses=[ReponseQuelAxe(id=r.lettre, libelle=r.libelle) for r in question.reponses],
            )
            for numero, question in enumerate(quel_axe.QUESTIONS, start=1)
        ]
    )


@router.post("/quel-axe/resultat")
async def resultat_quel_axe(entree: ReponsesQuelAxe, _: EleveActif) -> ResultatQuelAxe:
    resultat = quel_axe.calculer(entree.reponses)
    return ResultatQuelAxe(principal=resultat.principal, autres=list(resultat.autres), scores=resultat.scores)


Base = Annotated[AsyncSession, Depends(get_session)]
AUCUN_DEFI = "Aucun défi n'est disponible pour l'instant."


@router.get("/defi-du-jour")
async def defi_du_jour(db: Base) -> DefiDuJour:
    try:
        defi = await defis.du_jour(db)
    except defis.AucunDefi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, AUCUN_DEFI) from None
    return DefiDuJour(id=defi.id, categorie=defi.categorie, question=defi.question, options=defi.options)


@router.post("/defis/{defi_id}/reponse")
async def repondre_au_defi(defi_id: UUID, entree: ReponseDefi, db: Base) -> CorrectionDefi:
    try:
        defi, correcte = await defis.corriger(db, defi_id, entree.choix)
    except defis.AucunDefi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce défi est introuvable.") from None
    except ValueError as erreur:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erreur)) from None
    return CorrectionDefi(correcte=correcte, bonne_reponse=defi.bonne_reponse, explication=defi.explication)
