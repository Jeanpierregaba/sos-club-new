"""Articles (spec 023) : rédaction sous /mes-articles. La lecture publique est sous /articles."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import adresse_ip
from app.articles import service
from app.articles.dependances import Auteur
from app.articles.schemas import ArticleAuteur, ArticleEcriture, MesArticles, VersionEntree
from app.comptes.inscription import Refus
from app.db import get_session
from app.moderation import service as moteur

Base = Annotated[AsyncSession, Depends(get_session)]

router_auteur = APIRouter(prefix="/mes-articles", tags=["articles"])


@contextmanager
def _traduire() -> Iterator[None]:
    try:
        yield
    except moteur.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cet article est introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_auteur.get("")
async def mes_articles(db: Base, auteur: Auteur) -> MesArticles:
    return await service.mes_articles(db, auteur)


@router_auteur.post("", status_code=status.HTTP_201_CREATED)
async def creer(entree: ArticleEcriture, db: Base, auteur: Auteur) -> ArticleAuteur:
    with _traduire():
        return await service.creer(db, auteur, entree)


@router_auteur.get("/{contenu_id}")
async def lire(contenu_id: UUID, db: Base, auteur: Auteur) -> ArticleAuteur:
    with _traduire():
        return await service.lire(db, auteur, contenu_id)


@router_auteur.patch("/{contenu_id}")
async def modifier(contenu_id: UUID, entree: ArticleEcriture, db: Base, auteur: Auteur) -> ArticleAuteur:
    with _traduire():
        return await service.modifier(db, auteur, contenu_id, entree)


@router_auteur.delete("/{contenu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer(contenu_id: UUID, db: Base, auteur: Auteur) -> Response:
    with _traduire():
        await service.supprimer(db, auteur, contenu_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_auteur.post("/{contenu_id}/soumettre")
async def soumettre(
    contenu_id: UUID, entree: VersionEntree, request: Request, db: Base, auteur: Auteur
) -> ArticleAuteur:
    with _traduire():
        return await service.soumettre(db, auteur, contenu_id, entree.version, adresse_ip(request))


@router_auteur.post("/{contenu_id}/retirer")
async def retirer(contenu_id: UUID, entree: VersionEntree, request: Request, db: Base, auteur: Auteur) -> ArticleAuteur:
    with _traduire():
        return await service.retirer(db, auteur, contenu_id, entree.version, adresse_ip(request))
