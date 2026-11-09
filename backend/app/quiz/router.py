"""Routes du joueur (spec 027). Les règles vivent dans `partie.py`."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.quiz import partie
from app.quiz.dependances import MESSAGE_CERTIFICATION, Joueur
from app.quiz.schemas import EtatPartie, ListeQuiz, ReponseJoueur

router = APIRouter(prefix="/quiz", tags=["quiz"])

Db = Annotated[AsyncSession, Depends(get_session)]

INTROUVABLE = "Ce quiz ou cette partie est introuvable."


def erreur_de_partie(erreur: Exception) -> HTTPException:
    """Traduit une erreur de la partie ; sert aussi au mode test de l'espace admin."""
    if isinstance(erreur, partie.PlafondAtteint):
        return HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Tu as joué toutes tes parties du jour à ce quiz : reviens demain."
        )
    if isinstance(erreur, partie.ChoixInvalide):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Ce choix n'existe pas pour cette question.")
    if isinstance(erreur, partie.ReserveCertification):
        return HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_CERTIFICATION)
    if isinstance(erreur, partie.PlaceVerrouillee):
        return HTTPException(status.HTTP_403_FORBIDDEN, "Réussis d'abord la place précédente du parcours.")
    if isinstance(erreur, partie.QuizIncomplet):
        return HTTPException(status.HTTP_409_CONFLICT, "Ce quiz n'a pas assez de questions pour une partie.")
    return HTTPException(status.HTTP_404_NOT_FOUND, INTROUVABLE)


ERREURS = (
    partie.Introuvable,
    partie.PlafondAtteint,
    partie.ChoixInvalide,
    partie.QuizIncomplet,
    partie.PlaceVerrouillee,
    partie.ReserveCertification,
)


@router.get("")
async def lister(db: Db, joueur: Joueur, axe: str | None = None) -> ListeQuiz:
    resultat = await partie.liste(db, joueur, axe)
    await db.commit()
    return resultat


@router.post("/{quiz_id}/tentatives", status_code=status.HTTP_201_CREATED)
async def lancer(quiz_id: UUID, db: Db, joueur: Joueur) -> EtatPartie:
    try:
        resultat = await partie.lancer(db, joueur, quiz_id)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat


@router.get("/tentatives/{tentative_id}")
async def reprendre(tentative_id: UUID, db: Db, joueur: Joueur) -> EtatPartie:
    try:
        resultat = await partie.etat(db, joueur, tentative_id)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat


@router.post("/tentatives/{tentative_id}/reponses")
async def repondre(tentative_id: UUID, entree: ReponseJoueur, db: Db, joueur: Joueur) -> EtatPartie:
    try:
        resultat = await partie.repondre(db, joueur, tentative_id, entree.rang, entree.choix)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat
