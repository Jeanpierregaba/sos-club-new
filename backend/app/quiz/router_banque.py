"""Routes de la banque de quiz et du mode test (spec 027), dans l'espace admin. Chaque route exige son droit
`quiz` ; approuver et dépublier sont des droits sensibles (double authentification, catalogue des droits)."""

from collections.abc import Awaitable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.db import get_session
from app.quiz import banque, partie
from app.quiz.models import EtatQuiz
from app.quiz.router import ERREURS, erreur_de_partie
from app.quiz.schemas import EtatPartie, ReponseJoueur
from app.quiz.schemas_banque import (
    Approbation,
    HistoriqueParametres,
    ListeBanque,
    Motif,
    ParametresEntree,
    ParametresSortie,
    QuestionEntree,
    QuizDetail,
    QuizEntree,
)

router_banque = APIRouter(prefix="/admin/quiz", tags=["admin"])

Db = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_permission("quiz", Action.consulter))]
Createur = Annotated[Acces, Depends(exiger_permission("quiz", Action.creer))]
Redacteur = Annotated[Acces, Depends(exiger_permission("quiz", Action.modifier))]
Soumetteur = Annotated[Acces, Depends(exiger_permission("quiz", Action.soumettre))]
Decideur = Annotated[Acces, Depends(exiger_permission("quiz", Action.approuver))]
Depublieur = Annotated[Acces, Depends(exiger_permission("quiz", Action.depublier))]


def _erreur(e: Exception) -> HTTPException:
    if isinstance(e, banque.Introuvable):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Ce quiz est introuvable.")
    if isinstance(e, banque.Refuse):
        return HTTPException(
            status.HTTP_403_FORBIDDEN, "Tu as préparé ce quiz : un autre membre de l'équipe doit le publier."
        )
    if isinstance(e, banque.Invalide):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, e.message)
    return HTTPException(status.HTTP_409_CONFLICT, str(e))


ERREURS_BANQUE = (banque.Introuvable, banque.Refuse, banque.Invalide, banque.EtatInvalide)


# Paramètres (avant /{quiz_id} pour que le chemin ne soit pas pris pour un identifiant) -----------------------------


@router_banque.get("/parametres")
async def lire_parametres(db: Db, _: Lecteur) -> HistoriqueParametres:
    resultat = await banque.historique(db)
    await db.commit()
    return resultat


@router_banque.put("/parametres")
async def changer_parametres(entree: ParametresEntree, request: Request, db: Db, acces: Redacteur) -> ParametresSortie:
    try:
        resultat = await banque.changer_parametres(db, acces, entree, adresse_ip(request))
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return resultat


# Mode test : une partie complète dans les conditions réelles, sans trace ------------------------------------------


@router_banque.get("/essais/{tentative_id}")
async def reprendre_essai(tentative_id: UUID, db: Db, acces: Lecteur) -> EtatPartie:
    try:
        resultat = await partie.etat(db, acces.utilisateur, tentative_id, essai=True)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat


@router_banque.post("/essais/{tentative_id}/reponses")
async def repondre_essai(tentative_id: UUID, entree: ReponseJoueur, db: Db, acces: Lecteur) -> EtatPartie:
    try:
        resultat = await partie.repondre(db, acces.utilisateur, tentative_id, entree.rang, entree.choix, essai=True)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat


# La banque -----------------------------------------------------------------------------------------------------------


@router_banque.get("")
async def lister(db: Db, acces: Lecteur, etat: EtatQuiz | None = None) -> ListeBanque:
    resultat = await banque.lister(db, acces, etat)
    await db.commit()
    return resultat


@router_banque.post("", status_code=status.HTTP_201_CREATED)
async def creer(entree: QuizEntree, request: Request, db: Db, acces: Createur) -> QuizDetail:
    try:
        quiz = await banque.creer(db, acces, entree, adresse_ip(request))
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return await banque.detail(db, acces, quiz.id)


@router_banque.get("/{quiz_id}")
async def lire(quiz_id: UUID, db: Db, acces: Lecteur) -> QuizDetail:
    try:
        return await banque.detail(db, acces, quiz_id)
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None


@router_banque.put("/{quiz_id}")
async def modifier(quiz_id: UUID, entree: QuizEntree, request: Request, db: Db, acces: Redacteur) -> QuizDetail:
    try:
        await banque.modifier(db, acces, quiz_id, entree, adresse_ip(request))
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return await banque.detail(db, acces, quiz_id)


@router_banque.post("/{quiz_id}/questions", status_code=status.HTTP_201_CREATED)
async def ajouter_question(
    quiz_id: UUID, entree: QuestionEntree, request: Request, db: Db, acces: Redacteur
) -> QuizDetail:
    try:
        await banque.ajouter_question(db, acces, quiz_id, entree, adresse_ip(request))
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return await banque.detail(db, acces, quiz_id)


@router_banque.put("/{quiz_id}/questions/{question_id}")
async def modifier_question(
    quiz_id: UUID, question_id: UUID, entree: QuestionEntree, request: Request, db: Db, acces: Redacteur
) -> QuizDetail:
    try:
        await banque.modifier_question(db, acces, quiz_id, question_id, entree, adresse_ip(request))
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return await banque.detail(db, acces, quiz_id)


@router_banque.delete("/{quiz_id}/questions/{question_id}")
async def retirer_question(quiz_id: UUID, question_id: UUID, request: Request, db: Db, acces: Redacteur) -> QuizDetail:
    try:
        await banque.retirer_question(db, acces, quiz_id, question_id, adresse_ip(request))
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return await banque.detail(db, acces, quiz_id)


async def _transition(db: AsyncSession, acces: Acces, quiz_id: UUID, action: Awaitable[None]) -> QuizDetail:
    try:
        await action
    except ERREURS_BANQUE as e:
        raise _erreur(e) from None
    await db.commit()
    return await banque.detail(db, acces, quiz_id)


@router_banque.post("/{quiz_id}/soumettre")
async def soumettre(quiz_id: UUID, request: Request, db: Db, acces: Soumetteur) -> QuizDetail:
    return await _transition(db, acces, quiz_id, banque.soumettre(db, acces, quiz_id, adresse_ip(request)))


@router_banque.post("/{quiz_id}/reprendre")
async def reprendre(quiz_id: UUID, request: Request, db: Db, acces: Soumetteur) -> QuizDetail:
    return await _transition(db, acces, quiz_id, banque.reprendre(db, acces, quiz_id, adresse_ip(request)))


@router_banque.post("/{quiz_id}/approuver")
async def approuver(quiz_id: UUID, entree: Approbation, request: Request, db: Db, acces: Decideur) -> QuizDetail:
    return await _transition(db, acces, quiz_id, banque.approuver(db, acces, quiz_id, entree, adresse_ip(request)))


@router_banque.post("/{quiz_id}/refuser")
async def refuser(quiz_id: UUID, entree: Motif, request: Request, db: Db, acces: Decideur) -> QuizDetail:
    return await _transition(db, acces, quiz_id, banque.refuser(db, acces, quiz_id, entree.motif, adresse_ip(request)))


@router_banque.post("/{quiz_id}/depublier")
async def depublier(quiz_id: UUID, entree: Motif, request: Request, db: Db, acces: Depublieur) -> QuizDetail:
    return await _transition(
        db, acces, quiz_id, banque.depublier(db, acces, quiz_id, entree.motif, adresse_ip(request))
    )


@router_banque.post("/{quiz_id}/essais", status_code=status.HTTP_201_CREATED)
async def lancer_essai(quiz_id: UUID, db: Db, acces: Lecteur) -> EtatPartie:
    try:
        resultat = await partie.lancer(db, acces.utilisateur, quiz_id, essai=True)
    except ERREURS as e:
        raise erreur_de_partie(e) from None
    await db.commit()
    return resultat
