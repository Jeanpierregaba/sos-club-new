"""Articles (spec 023) : rédaction sous /mes-articles. La lecture publique est sous /articles."""

from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from typing import Annotated, Any, Literal
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


Taille = Literal["grande", "vignette"]
_LEGENDE = TypeAdapter(Legende)


def routes_de_redaction(
    router: APIRouter,
    Redacteur: Any,
    type: str,
    club_de: Callable[[AsyncSession, Utilisateur], Awaitable[UUID]] | None = None,
) -> None:
    """Les routes de rédaction d'un contenu de type article : les articles personnels (spec 023) et les actualités
    du club (spec 026), avec leurs photos (spec 024). `Redacteur` dit qui rédige ; `club_de`, au nom de quel club."""

    @router.get("")
    async def mes_articles(db: Base, auteur: Redacteur) -> MesArticles:
        return await service.mes_articles(db, auteur, type=type)

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def creer(entree: ArticleEcriture, db: Base, auteur: Redacteur) -> ArticleAuteur:
        with _traduire():
            return await service.creer(
                db, auteur, entree, type=type, club_id=await club_de(db, auteur) if club_de else None
            )

    @router.get("/{contenu_id}")
    async def lire(contenu_id: UUID, db: Base, auteur: Redacteur) -> ArticleAuteur:
        with _traduire():
            return await service.lire(db, auteur, contenu_id, type=type)

    @router.patch("/{contenu_id}")
    async def modifier(contenu_id: UUID, entree: ArticleEcriture, db: Base, auteur: Redacteur) -> ArticleAuteur:
        with _traduire():
            return await service.modifier(db, auteur, contenu_id, entree, type=type)

    @router.delete("/{contenu_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def supprimer(contenu_id: UUID, db: Base, auteur: Redacteur) -> Response:
        with _traduire():
            await service.supprimer(db, auteur, contenu_id, type=type)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post("/{contenu_id}/soumettre")
    async def soumettre(
        contenu_id: UUID, entree: VersionEntree, request: Request, db: Base, auteur: Redacteur
    ) -> ArticleAuteur:
        with _traduire():
            return await service.soumettre(db, auteur, contenu_id, entree.version, adresse_ip(request), type=type)

    @router.post("/{contenu_id}/retirer")
    async def retirer(
        contenu_id: UUID, entree: VersionEntree, request: Request, db: Base, auteur: Redacteur
    ) -> ArticleAuteur:
        with _traduire():
            return await service.retirer(db, auteur, contenu_id, entree.version, adresse_ip(request), type=type)

        # Photos (spec 024) ------------------------------------------------------------------------------------------

    @router.post("/{contenu_id}/photos")
    async def ajouter_photo(
        contenu_id: UUID,
        request: Request,
        db: Base,
        auteur: Redacteur,
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
                db, auteur, contenu_id, version, octets, legende_propre, couverture, adresse_ip(request), type=type
            )

    @router.patch("/{contenu_id}/photos/{photo_id}")
    async def modifier_photo(
        contenu_id: UUID, photo_id: UUID, entree: PhotoModification, db: Base, auteur: Redacteur
    ) -> ArticleAuteur:
        with _traduire():
            return await service.modifier_photo(db, auteur, contenu_id, photo_id, entree, type=type)

    @router.delete("/{contenu_id}/photos/{photo_id}")
    async def retirer_photo(
        contenu_id: UUID, photo_id: UUID, version: int, request: Request, db: Base, auteur: Redacteur
    ) -> ArticleAuteur:
        with _traduire():
            return await service.retirer_photo(
                db, auteur, contenu_id, photo_id, version, adresse_ip(request), type=type
            )

    # Lire sa propre photo ne demande que d'être connecté : un encadreur redevenu non vérifié revoit ses brouillons.
    @router.get("/{contenu_id}/photos/{photo_id}/{taille}", response_class=Response)
    async def lire_photo(
        contenu_id: UUID,
        photo_id: UUID,
        taille: Taille,
        db: Base,
        utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)],
    ) -> Response:
        with _traduire():
            octets = await photos.lire_pour_auteur(db, utilisateur, contenu_id, type, photo_id, taille)
        return reponse.image(octets, publique=False)


routes_de_redaction(router_auteur, Auteur, service.TYPE)


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
        octets = await photos.lire_publique(db, public.TYPES, adresse, photo_id, taille)
    return reponse.image(octets, publique=True)
