"""Route publique de la collecte d'activité (spec 051)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite import service
from app.activite.schemas import CHEMINS_RECHERCHE, EvenementSite, nettoyer_recherche
from app.db import get_session

Base = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/activite", tags=["activite"])


@router.post("/evenements", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def recevoir(evenement: EvenementSite, request: Request, db: Base) -> Response:
    """Enregistre un événement anonyme du site. Toujours 204 : le visiteur n'apprend jamais s'il a été compté."""
    if service.ne_pas_suivre(request):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    detail = evenement.detail[:60] if evenement.detail else None
    if evenement.type == "erreur":
        chemin = service.segment_introuvable(evenement.chemin)
    else:
        chemin = service.gabarit(evenement.chemin)
    if evenement.type == "recherche":
        detail = nettoyer_recherche(evenement.detail or "")
        if detail is None or chemin not in CHEMINS_RECHERCHE:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    if not service.accepter(request):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    await service.ecrire(
        db,
        request,
        evenement.type_evenement,
        chemin,
        detail,
        referent=evenement.referent,
        utm=evenement.utm_source,
        entree=evenement.entree and evenement.type == "page_vue",
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
