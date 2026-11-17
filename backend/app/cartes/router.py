"""Routes des cartes numériques (spec 040) : « Ma carte » et ses fichiers pour le titulaire, puis la vérification
publique par le code du QR."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import adresse_ip
from app.cartes import rendu, service, verification
from app.cartes.schemas import MaCarte, VerificationCarte
from app.comptes import limite_adresse
from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Utilisateur
from app.db import get_session

router = APIRouter(prefix="/cartes", tags=["cartes"])

Db = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]
SANS_CACHE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
INCONNUE = "Cette carte n'existe pas."
PAS_DE_CARTE = "Tu n'as pas de carte."


async def _mienne(db: AsyncSession, utilisateur: Utilisateur) -> service.EtatCarte:
    # ADR-0003 : seule la carte du compte connecté, jamais un identifiant pris dans l'adresse.
    etat = await service.etat_du_compte(db, utilisateur.id)
    if etat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PAS_DE_CARTE)
    return etat


@router.get("/moi")
async def ma_carte(db: Db, utilisateur: Connecte, response: Response) -> MaCarte:
    etat = await _mienne(db, utilisateur)
    response.headers.update(SANS_CACHE)
    return MaCarte(
        type=etat.type,
        numero=etat.numero,
        prenom=etat.prenom or "",
        nom=etat.nom or "",
        role=etat.role,
        etablissement=etat.etablissement,
        club=etat.club,
        delivree_le=etat.delivree_le,
        valide=etat.valide,
        cause=etat.cause,
        adresse_verification=rendu.adresse_de_verification(etat.code),
    )


async def _fichier(db: AsyncSession, utilisateur: Utilisateur) -> service.EtatCarte:
    etat = await _mienne(db, utilisateur)
    if not etat.valide:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ta carte n'est pas valide : elle ne se télécharge pas.")
    return etat


def _nom_de_fichier(etat: service.EtatCarte, extension: str) -> str:
    return f'attachment; filename="carte-{etat.type.value}-{etat.numero}.{extension}"'


@router.get("/moi.pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
async def ma_carte_pdf(db: Db, utilisateur: Connecte) -> Response:
    etat = await _fichier(db, utilisateur)
    return Response(
        rendu.pdf(etat),
        media_type="application/pdf",
        headers=SANS_CACHE | {"Content-Disposition": _nom_de_fichier(etat, "pdf")},
    )


@router.get("/moi.png", response_class=Response, responses={200: {"content": {"image/png": {}}}})
async def ma_carte_png(db: Db, utilisateur: Connecte) -> Response:
    etat = await _fichier(db, utilisateur)
    return Response(
        rendu.png(etat),
        media_type="image/png",
        headers=SANS_CACHE | {"Content-Disposition": _nom_de_fichier(etat, "png")},
    )


@router.get("/verification/{code}")
async def verifier(code: str, request: Request, db: Db, response: Response) -> VerificationCarte:
    try:
        await verification.limiter(db, adresse_ip(request))
    except limite_adresse.PlafondAtteint:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Trop de vérifications depuis ce réseau. Réessaie dans 15 minutes.",
            headers=SANS_CACHE | {"X-Robots-Tag": "noindex"},
        ) from None
    resultat = await verification.verifier(db, code)
    if resultat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INCONNUE, headers=SANS_CACHE | {"X-Robots-Tag": "noindex"})
    response.headers.update(SANS_CACHE | {"X-Robots-Tag": "noindex"})
    return resultat
