"""Jeux de l'accueil (spec 021) : « Quel axe est fait pour toi ? », réservé aux élèves actifs, sans point ni
enregistrement ; et le défi du jour, ouvert à tous, qui rapporte des points à un élève actif (spec 022)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant, utilisateur_facultatif
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
from app.points.service import aujourd_hui

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
Facultatif = Annotated[Utilisateur | None, Depends(utilisateur_facultatif)]
AUCUN_DEFI = "Aucun défi n'est disponible pour l'instant."


def _correction(c: defis.Correction) -> CorrectionDefi:
    return CorrectionDefi(
        choix=c.choix,
        correcte=c.correcte,
        bonne_reponse=c.defi.bonne_reponse,
        explication=c.defi.explication,
        points=c.points,
        deja_repondu=c.deja_repondu,
    )


@router.get("/defi-du-jour")
async def defi_du_jour(db: Base, utilisateur: Facultatif) -> DefiDuJour:
    try:
        defi = await defis.du_jour(db, utilisateur=utilisateur)
    except defis.AucunDefi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, AUCUN_DEFI) from None
    deja = await defis.reponse_du_jour(db, utilisateur, aujourd_hui())
    # Une réponse d'avant un changement de la banque peut viser une autre question : elle ne vaut que pour la sienne.
    ma_reponse = _correction(deja) if deja is not None and deja.defi.id == defi.id else None
    return DefiDuJour(
        id=defi.id, categorie=defi.categorie, question=defi.question, options=defi.options, ma_reponse=ma_reponse
    )


@router.post("/defis/{defi_id}/reponse")
async def repondre_au_defi(defi_id: UUID, entree: ReponseDefi, db: Base, utilisateur: Facultatif) -> CorrectionDefi:
    """Ouverte à tous ; un élève actif gagne les points du barème à sa première réponse juste du jour."""
    try:
        correction = await defis.corriger(db, defi_id, entree.choix, utilisateur)
    except defis.AucunDefi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce défi est introuvable.") from None
    except ValueError as erreur:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erreur)) from None
    return _correction(correction)
