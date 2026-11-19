"""Partages d'articles (spec 044) : déclaration sous /articles/{adresse}/partages, suivi sous /partages/moi."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import adresse_ip
from app.articles.dependances import Auteur
from app.comptes.inscription import Refus
from app.db import get_session
from app.moderation import service as moteur
from app.partages import service
from app.partages.schemas import DeclarationPartage, EtatPartagesArticle, MesPartages, PartageAuteur

Base = Annotated[AsyncSession, Depends(get_session)]

router_article = APIRouter(prefix="/articles", tags=["partages"])
router = APIRouter(prefix="/partages", tags=["partages"])


@contextmanager
def _traduire() -> Iterator[None]:
    try:
        yield
    except moteur.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cet article est introuvable ou n'est plus publié.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_article.post("/{adresse}/partages", status_code=status.HTTP_201_CREATED)
async def declarer(
    adresse: str, entree: DeclarationPartage, request: Request, db: Base, auteur: Auteur
) -> PartageAuteur:
    with _traduire():
        return await service.declarer(db, auteur, adresse, entree.reseau, entree.lien, adresse_ip(request))


@router_article.get("/{adresse}/partages/moi")
async def etat_article(adresse: str, db: Base, auteur: Auteur) -> EtatPartagesArticle:
    with _traduire():
        return await service.etat_article(db, auteur, adresse)


@router.get("/moi")
async def mes_partages(db: Base, auteur: Auteur) -> MesPartages:
    return await service.mes_partages(db, auteur)
