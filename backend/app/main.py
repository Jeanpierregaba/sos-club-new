import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.exports import purger_regulierement
from app.admin.router import router as router_admin
from app.admin.router import router_activation
from app.comptes.dependances import verifier_origine
from app.comptes.router import router as router_comptes
from app.db import engine, get_session
from app.eleves.router import router as router_eleves
from app.points.router import router_admin as router_points_admin
from app.referentiel.router import router_admin as router_referentiel_admin
from app.referentiel.router import router_public as router_referentiel

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Efface les fichiers d'export expirés au démarrage, puis toutes les heures (spec 015).
    purge = asyncio.create_task(purger_regulierement())
    yield
    purge.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await purge
    await engine.dispose()


app = FastAPI(title="API Club Santé SOS Docteur TV", lifespan=lifespan)

# Toutes les routes sous /api sont servies sur le domaine du site (ADR-0006).
api = APIRouter(prefix="/api", dependencies=[Depends(verifier_origine)])
api.include_router(router_comptes)
api.include_router(router_admin)
api.include_router(router_activation)
api.include_router(router_referentiel)
api.include_router(router_referentiel_admin)
api.include_router(router_points_admin)
api.include_router(router_eleves)
app.include_router(api)


@app.middleware("http")
async def interdire_le_cache(request: Request, suivant: Callable[[Request], Awaitable[Response]]) -> Response:
    reponse = await suivant(request)
    if request.url.path.startswith("/api/"):
        reponse.headers["Cache-Control"] = "no-store"
    return reponse


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
