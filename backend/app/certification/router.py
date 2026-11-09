"""Routes de la certification (spec 029) : « Ma certification » et le PDF du titulaire, puis la vérification
publique d'un numéro."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification import certificat_pdf, joueur, verification
from app.certification.schemas import CertificatJoueur, ChoixClub, MaCertification, Verification
from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Utilisateur
from app.db import get_session
from app.quiz.dependances import Candidat

router = APIRouter(prefix="/certification", tags=["certification"])
router_public = APIRouter(prefix="/certificats", tags=["certification"])

Db = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]
SANS_CACHE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


@router.get("")
async def ma_certification(db: Db, utilisateur: Candidat) -> MaCertification:
    resultat = await joueur.ma_certification(db, utilisateur)
    await db.commit()
    return resultat


# RULES : un élève choisit de montrer son club à la vérification publique (caché par défaut).
@router.put("/club")
async def choisir_club(entree: ChoixClub, db: Db, utilisateur: Candidat) -> CertificatJoueur:
    resultat = await joueur.choisir_club(db, utilisateur, entree.afficher)
    if resultat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu n'as pas de certificat valide.")
    await db.commit()
    return resultat


# Réservé au titulaire : le PDF porte son nom complet. Tout compte connecté peut demander le sien (un encadreur
# dont la vérification a changé garde son certificat) ; aucun autre n'est jamais servi.
@router.get("/certificat.pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
async def certificat(db: Db, utilisateur: Connecte) -> Response:
    trouve = await joueur.certificat_valide(db, utilisateur.id)
    if trouve is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu n'as pas de certificat valide.")
    return Response(
        certificat_pdf.generer(trouve),
        media_type="application/pdf",
        headers=SANS_CACHE
        | {"Content-Disposition": f'attachment; filename="certificat-genie-imhotep-{trouve.numero}.pdf"'},
    )


@router_public.get("/{numero}")
async def verifier(numero: str, db: Db, response: Response) -> Verification:
    resultat = await verification.verifier(db, numero)
    if resultat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun certificat ne porte ce numéro.")
    response.headers.update(SANS_CACHE)
    return resultat
