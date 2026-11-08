"""Commentaires (spec 025) : lecture publique et envoi sous /articles/{adresse}/commentaires, suivi et retrait sous
/mes-commentaires."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import adresse_ip
from app.articles.dependances import Auteur
from app.commentaires import service
from app.commentaires.schemas import CommentaireAuteur, CommentaireEntree, CommentairesPublics, MesCommentaires
from app.comptes.inscription import Refus
from app.db import get_session
from app.moderation import service as moteur

Base = Annotated[AsyncSession, Depends(get_session)]

router_public = APIRouter(prefix="/articles", tags=["commentaires"])
router_auteur = APIRouter(prefix="/mes-commentaires", tags=["commentaires"])


@contextmanager
def _traduire(introuvable: str) -> Iterator[None]:
    try:
        yield
    except moteur.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, introuvable) from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_public.get("/{adresse}/commentaires")
async def commentaires(adresse: str, db: Base, page: Annotated[int, Query(ge=1, le=10_000)] = 1) -> CommentairesPublics:
    with _traduire("Cet article est introuvable."):
        return await service.lister(db, adresse, page)


@router_public.post(
    "/{adresse}/commentaires",
    status_code=status.HTTP_201_CREATED,
    responses={200: {"description": "Double envoi : le commentaire déjà enregistré."}},
)
async def commenter(
    adresse: str, entree: CommentaireEntree, request: Request, response: Response, db: Base, auteur: Auteur
) -> CommentaireAuteur:
    with _traduire("Cet article est introuvable ou n'est plus publié."):
        commentaire, cree = await service.envoyer(db, auteur, adresse, entree.texte, adresse_ip(request))
    if not cree:
        response.status_code = status.HTTP_200_OK
    return commentaire


@router_auteur.get("")
async def mes_commentaires(
    db: Base, auteur: Auteur, article: Annotated[str | None, Query(max_length=140)] = None
) -> MesCommentaires:
    return await service.mes_commentaires(db, auteur, article)


@router_auteur.delete("/{contenu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def retirer(contenu_id: UUID, request: Request, db: Base, auteur: Auteur) -> Response:
    with _traduire("Ce commentaire est introuvable."):
        await service.retirer(db, auteur, contenu_id, adresse_ip(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
