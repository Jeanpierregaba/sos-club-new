"""Quiz « jeux » ouverts à tous depuis la page des jeux (spec 031), sous /jeux/quiz.

Un joueur sans compte joue au plus trois quiz, sans points ; ses parties sont arbitrées par le serveur comme les
autres (ADR-0004). Un compte connecté joue depuis /quiz, avec ses règles.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_facultatif
from app.comptes.models import Utilisateur
from app.comptes.service import cle_adresse
from app.config import settings
from app.db import get_session
from app.jeux import invites
from app.quiz import parametres, partie
from app.quiz.models import PARCOURS_JEUX, EtatQuiz, QuestionQuiz, Quiz
from app.quiz.router import ERREURS, erreur_de_partie
from app.quiz.schemas import EtatPartie, ReponseJoueur

router = APIRouter(prefix="/jeux/quiz", tags=["jeux"])

Db = Annotated[AsyncSession, Depends(get_session)]
Facultatif = Annotated[Utilisateur | None, Depends(utilisateur_facultatif)]


class QuizOuvert(BaseModel):
    id: UUID
    titre: str
    description: str
    axe_code: str
    nb_questions_reserve: int


class CatalogueQuiz(BaseModel):
    nb_questions: int
    seuil: int
    temps_ms: int
    # Joueur sans compte : quiz encore jouables ; None pour un compte connecté (pas de limite ici).
    limite: int
    restants: int | None
    connecte: bool
    quiz: list[QuizOuvert]


def _adresse(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


def _poser_cookie(response: Response, jeton: str) -> None:
    response.set_cookie(
        invites.COOKIE,
        jeton,
        max_age=int(invites.DUREE.total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        # Sur tout le site : la page des jeux affiche, dès son rendu, les quiz qui restent.
        path="/",
    )


@router.get("")
async def catalogue(request: Request, db: Db, moi: Facultatif) -> CatalogueQuiz:
    p = await parametres.en_cours(db, PARCOURS_JEUX)
    reserve = func.count(QuestionQuiz.id).label("reserve")
    lignes = (
        await db.execute(
            select(Quiz, reserve)
            .join(QuestionQuiz, (QuestionQuiz.quiz_id == Quiz.id) & QuestionQuiz.active)
            .where(Quiz.parcours == PARCOURS_JEUX, Quiz.etat == EtatQuiz.publie)
            .group_by(Quiz.id)
            .having(reserve >= p.nb_questions)
            .order_by(Quiz.publie_le, Quiz.titre)
        )
    ).all()
    restants: int | None = None
    if moi is None:
        invite = await invites.invite_du_cookie(db, request.cookies.get(invites.COOKIE))
        joues = await invites.quiz_joues(db, invite) if invite else 0
        restants = max(0, invites.LIMITE_QUIZ - joues)
    return CatalogueQuiz(
        nb_questions=p.nb_questions,
        seuil=p.seuil,
        temps_ms=p.temps_ms,
        limite=invites.LIMITE_QUIZ,
        restants=restants,
        connecte=moi is not None,
        quiz=[
            QuizOuvert(id=q.id, titre=q.titre, description=q.description, axe_code=q.axe_code,
                       nb_questions_reserve=n)
            for q, n in lignes
        ],
    )  # fmt: skip


async def _invite(request: Request, db: AsyncSession) -> Utilisateur:
    invite = await invites.invite_du_cookie(db, request.cookies.get(invites.COOKIE))
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette partie est introuvable.")
    return invite


@router.post("/{quiz_id}/tentatives", status_code=status.HTTP_201_CREATED)
async def lancer(quiz_id: UUID, request: Request, response: Response, db: Db, moi: Facultatif) -> EtatPartie:
    if moi is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tu es connecté : joue depuis tes quiz.")
    quiz = await db.get(Quiz, quiz_id)
    if quiz is None or quiz.etat is not EtatQuiz.publie or quiz.parcours != PARCOURS_JEUX:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce quiz est introuvable.")
    invite = await invites.invite_du_cookie(db, request.cookies.get(invites.COOKIE))
    if invite is None:
        try:
            invite, jeton = await invites.nouvel_invite(db, _adresse(request))
        except invites.TropDInvites:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS, "Trop de parties sans compte depuis ce réseau : crée ton compte."
            ) from None
        _poser_cookie(response, jeton)
    try:
        await invites.verifier_limite(db, invite, quiz_id)
        resultat = await partie.lancer(db, invite, quiz_id)
    except invites.LimiteAtteinte:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, invites.MESSAGE_LIMITE, headers=invites.EN_TETE_FIN_ESSAI
        ) from None
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat


@router.get("/tentatives/{tentative_id}")
async def reprendre(tentative_id: UUID, request: Request, db: Db) -> EtatPartie:
    invite = await _invite(request, db)
    try:
        resultat = await partie.etat(db, invite, tentative_id)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat


@router.post("/tentatives/{tentative_id}/reponses")
async def repondre(tentative_id: UUID, entree: ReponseJoueur, request: Request, db: Db) -> EtatPartie:
    invite = await _invite(request, db)
    try:
        resultat = await partie.repondre(db, invite, tentative_id, entree.rang, entree.choix)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat
