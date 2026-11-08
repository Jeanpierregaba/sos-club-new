"""Articles (spec 023) : rédaction sous /mes-articles. La lecture publique est sous /articles."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Request, Response, UploadFile, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import adresse_ip
from app.articles import public, service
from app.articles.dependances import Auteur
from app.articles.schemas import (
    ArticleAuteur,
    ArticleEcriture,
    ArticlePublic,
    ArticlesPublics,
    Legende,
    MesArticles,
    PhotoModification,
    VersionEntree,
)
from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.config import settings
from app.db import get_session
from app.fichiers import reponse
from app.moderation import photos
from app.moderation import service as moteur

Base = Annotated[AsyncSession, Depends(get_session)]

router_auteur = APIRouter(prefix="/mes-articles", tags=["articles"])
router_public = APIRouter(prefix="/articles", tags=["articles"])


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


# Photos (spec 024) ----------------------------------------------------------------------------------------------

Taille = Literal["grande", "vignette"]
_LEGENDE = TypeAdapter(Legende)


@router_auteur.post("/{contenu_id}/photos")
async def ajouter_photo(
    contenu_id: UUID,
    request: Request,
    db: Base,
    auteur: Auteur,
    fichier: Annotated[UploadFile, File()],
    version: Annotated[int, Form()],
    attestation: Annotated[bool, Form()] = False,
    legende: Annotated[str | None, Form(max_length=400)] = None,
    couverture: Annotated[bool, Form()] = False,
) -> ArticleAuteur:
    if not attestation:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Coche l'attestation : tu dois avoir l'accord des personnes reconnaissables sur la photo.",
        )
    try:
        legende_propre = _LEGENDE.validate_python(legende) or None if legende else None
    except ValidationError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La légende tient sur une ligne de 200 caractères au plus."
        ) from None
    # Starlette a déjà reçu le formulaire (dans /tmp) : on n'en lit que la limite + 1 octet pour décider.
    octets = await fichier.read(settings.photo_octets_max + 1)
    if len(octets) > settings.photo_octets_max:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Cette photo dépasse {settings.photo_octets_max // (1024 * 1024)} Mo : réduis-la avant de l'envoyer.",
        )
    with _traduire():
        return await service.ajouter_photo(
            db, auteur, contenu_id, version, octets, legende_propre, couverture, adresse_ip(request)
        )


@router_auteur.patch("/{contenu_id}/photos/{photo_id}")
async def modifier_photo(
    contenu_id: UUID, photo_id: UUID, entree: PhotoModification, db: Base, auteur: Auteur
) -> ArticleAuteur:
    with _traduire():
        return await service.modifier_photo(db, auteur, contenu_id, photo_id, entree)


@router_auteur.delete("/{contenu_id}/photos/{photo_id}")
async def retirer_photo(
    contenu_id: UUID, photo_id: UUID, version: int, request: Request, db: Base, auteur: Auteur
) -> ArticleAuteur:
    with _traduire():
        return await service.retirer_photo(db, auteur, contenu_id, photo_id, version, adresse_ip(request))


# Lire sa propre photo ne demande que d'être connecté : un encadreur redevenu non vérifié revoit ses brouillons.
@router_auteur.get("/{contenu_id}/photos/{photo_id}/{taille}", response_class=Response)
async def lire_photo(
    contenu_id: UUID,
    photo_id: UUID,
    taille: Taille,
    db: Base,
    utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
) -> Response:
    with _traduire():
        octets = await photos.lire_pour_auteur(db, utilisateur, contenu_id, service.TYPE, photo_id, taille)
    return reponse.image(octets, publique=False)


# Lecture publique ----------------------------------------------------------------------------------------------


@router_public.get("")
async def articles(
    db: Base, page: Annotated[int, Query(ge=1, le=1000)] = 1, axe: Annotated[str | None, Query(max_length=40)] = None
) -> ArticlesPublics:
    return await public.lister(db, page, axe)


@router_public.get("/{adresse}")
async def article(adresse: Annotated[str, Path(max_length=140)], db: Base) -> ArticlePublic:
    lu = await public.lire(db, adresse)
    if lu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cet article est introuvable.")
    return lu


@router_public.get("/{adresse}/photos/{photo_id}/{taille}", response_class=Response)
async def photo_publique(
    adresse: Annotated[str, Path(max_length=140)], photo_id: UUID, taille: Taille, db: Base
) -> Response:
    with _traduire():
        octets = await photos.lire_publique(db, service.TYPE, adresse, photo_id, taille)
    return reponse.image(octets, publique=True)
