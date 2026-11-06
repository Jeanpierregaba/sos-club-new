"""Jeux de découverte de l'accueil (spec 021) : « Quel axe est fait pour toi ? », réservé aux élèves actifs.
Aucun point n'est gagné et rien n'est enregistré."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.jeux import quel_axe
from app.jeux.schemas import (
    QuestionnaireQuelAxe,
    QuestionQuelAxe,
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
