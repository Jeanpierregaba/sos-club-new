import asyncio
import contextlib
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite.models import TypeEvenement
from app.activite.purge import purger_regulierement as purger_activite_regulierement
from app.activite.router import router as router_activite
from app.activite.service import enregistrer
from app.admin.exports import purger_regulierement
from app.admin.router import router as router_admin
from app.admin.router import router_activation
from app.agenda.router import router as router_agenda
from app.agenda.router import router_club as router_agenda_club
from app.agenda.router_admin import router_admin as router_agenda_admin
from app.articles.router import router_auteur as router_articles_auteur
from app.articles.router import router_public as router_articles
from app.bibliotheque.router import router as router_bibliotheque
from app.bibliotheque.router_gestion import router_gestion as router_bibliotheque_gestion
from app.cartes.router import router as router_cartes
from app.cartes.router_admin import router_admin as router_cartes_admin
from app.certification.router import router as router_certification
from app.certification.router import router_public as router_certificats
from app.certification.router_gestion import router_gestion as router_certification_gestion
from app.clubs.router import router as router_clubs
from app.clubs.router import router_actualites
from app.clubs.router import router_admin as router_clubs_admin
from app.commentaires.router import router_auteur as router_commentaires_auteur
from app.commentaires.router import router_public as router_commentaires
from app.comptes.dependances import verifier_origine
from app.comptes.router import router as router_comptes
from app.db import engine, get_session
from app.eleves.router import router as router_eleves
from app.encadreurs.router import router as router_encadreurs
from app.encadreurs.router import router_admin as router_encadreurs_admin
from app.jeux.router import router as router_jeux
from app.jeux.router_admin import router as router_jeux_admin
from app.jeux.router_quiz import router as router_jeux_quiz
from app.maintenance.dependances import verifier_maintenance
from app.maintenance.router import router as router_maintenance
from app.maintenance.router import router_admin as router_maintenance_admin
from app.moderation.photos import purger_regulierement as purger_photos_regulierement
from app.moderation.router import router_admin as router_moderation_admin
from app.notifications.router import router as router_notifications
from app.partages.router import router as router_partages
from app.partages.router import router_article as router_partages_article
from app.points.router import router as router_points
from app.points.router import router_admin as router_points_admin
from app.points.router import router_classements, router_palmares
from app.quiz.router import router as router_quiz
from app.quiz.router_banque import router_banque as router_quiz_banque
from app.rapports.pieces import purger_regulierement as purger_pieces_regulierement
from app.rapports.router import router as router_rapports
from app.rapports.router_admin import router_admin as router_rapports_admin
from app.referentiel.router import router_admin as router_referentiel_admin
from app.referentiel.router import router_public as router_referentiel
from app.visiteurs.router import router as router_visiteurs
from app.visiteurs.service import purger_regulierement as purger_visiteurs_regulierement

logger = logging.getLogger(__name__)

PHOTOS_PUBLIQUES = re.compile(r"^/api/articles/[^/]+/photos/[^/]+/[a-z]+$")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Efface les fichiers d'export expirés au démarrage, puis toutes les heures (spec 015), et les photos refusées
    # depuis plus de 90 jours, une fois par jour (spec 024).
    # Les comptes visiteurs jamais confirmés depuis 7 jours, toutes les heures (spec 030).
    purges = [
        asyncio.create_task(purger_regulierement()),
        asyncio.create_task(purger_photos_regulierement()),
        asyncio.create_task(purger_pieces_regulierement()),
        asyncio.create_task(purger_visiteurs_regulierement()),
        # Le suivi d'activité (spec 051) : totaux à 90 jours, sels, recherches rares, présences.
        asyncio.create_task(purger_activite_regulierement()),
    ]
    yield
    for purge in purges:
        purge.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await purge
    await engine.dispose()


app = FastAPI(title="API Club Santé SOS Docteur TV", lifespan=lifespan)

# Toutes les routes sous /api sont servies sur le domaine du site (ADR-0006).
api = APIRouter(prefix="/api", dependencies=[Depends(verifier_origine), Depends(verifier_maintenance)])
api.include_router(router_maintenance)
api.include_router(router_activite)
api.include_router(router_comptes)
api.include_router(router_visiteurs)
api.include_router(router_admin)
api.include_router(router_activation)
api.include_router(router_maintenance_admin)
api.include_router(router_referentiel)
api.include_router(router_referentiel_admin)
api.include_router(router_points_admin)
api.include_router(router_points)
api.include_router(router_classements)
api.include_router(router_palmares)
api.include_router(router_eleves)
api.include_router(router_encadreurs)
api.include_router(router_encadreurs_admin)
api.include_router(router_actualites)
api.include_router(router_agenda_club)
api.include_router(router_agenda)
api.include_router(router_agenda_admin)
api.include_router(router_clubs)
api.include_router(router_clubs_admin)
api.include_router(router_jeux)
api.include_router(router_jeux_quiz)
api.include_router(router_jeux_admin)
api.include_router(router_notifications)
api.include_router(router_articles_auteur)
api.include_router(router_articles)
api.include_router(router_commentaires)
api.include_router(router_commentaires_auteur)
api.include_router(router_partages_article)
api.include_router(router_partages)
api.include_router(router_moderation_admin)
api.include_router(router_quiz)
api.include_router(router_quiz_banque)
api.include_router(router_bibliotheque_gestion)
api.include_router(router_bibliotheque)
api.include_router(router_rapports)
api.include_router(router_rapports_admin)
api.include_router(router_certification)
api.include_router(router_certificats)
api.include_router(router_cartes)
api.include_router(router_cartes_admin)
api.include_router(router_certification_gestion)
app.include_router(api)


@app.middleware("http")
async def interdire_le_cache(request: Request, suivant: Callable[[Request], Awaitable[Response]]) -> Response:
    reponse = await suivant(request)
    # Rien de l'API en cache, sauf les photos publiques (spec 024) : elles seules gardent leur propre en-tête.
    if request.url.path.startswith("/api/") and not PHOTOS_PUBLIQUES.match(request.url.path):
        reponse.headers["Cache-Control"] = "no-store"
    return reponse


@app.exception_handler(Exception)
async def erreur_serveur(request: Request, _: Exception) -> JSONResponse:
    """Une erreur inattendue : compte dans le suivi d'activité (spec 051) par le gabarit de sa route, jamais par
    l'adresse réelle ; l'erreur reste journalisée par le serveur."""
    route = request.scope.get("route")
    await enregistrer(request, TypeEvenement.erreur, getattr(route, "path", "autre")[:120], "500")
    return JSONResponse({"detail": "Erreur interne : réessaie dans un moment."}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.exception_handler(RequestValidationError)
async def erreur_de_validation(_: Request, erreur: RequestValidationError) -> JSONResponse:
    # Le format par défaut renvoie la valeur reçue : il exposerait le mot de passe saisi.
    detail = [
        {"loc": champ["loc"], "msg": "Valeur manquante ou invalide", "type": champ["type"]} for champ in erreur.errors()
    ]
    return JSONResponse({"detail": detail}, status.HTTP_422_UNPROCESSABLE_CONTENT)


@app.get("/health")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    # OSError couvre la connexion refusée et le délai dépassé, que le pilote ne convertit pas en erreur SQLAlchemy.
    except SQLAlchemyError, OSError:
        logger.exception("Base de données injoignable")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Base de données injoignable") from None
    return {"status": "ok", "database": "ok"}
