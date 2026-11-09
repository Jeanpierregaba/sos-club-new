"""Routes de gestion de la certification (spec 029), dans l'espace admin. Elles reprennent les droits `quiz` :
consulter pour lire ; approuver pour les règles des badges, dépublier pour révoquer et réémettre (droits sensibles,
double authentification). Les paramètres du parcours vivent avec ceux des jeux (`/admin/quiz/parametres`)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.certification import gestion
from app.certification.models import EtatCertificat
from app.certification.schemas import (
    CertificatGestion,
    HistoriqueRegles,
    ListeBadges,
    ListeCertificats,
    Motif,
    ReglesEntree,
    ReglesSortie,
)
from app.db import get_session

router_gestion = APIRouter(prefix="/admin/certification", tags=["admin"])

Db = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_permission("quiz", Action.consulter))]
Decideur = Annotated[Acces, Depends(exiger_permission("quiz", Action.approuver))]
Depublieur = Annotated[Acces, Depends(exiger_permission("quiz", Action.depublier))]


def _erreur(e: Exception) -> HTTPException:
    if isinstance(e, gestion.Introuvable):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Ce certificat est introuvable.")
    return HTTPException(status.HTTP_409_CONFLICT, str(e))


@router_gestion.get("/regles")
async def lire_regles(db: Db, _: Lecteur) -> HistoriqueRegles:
    resultat = await gestion.historique_regles(db)
    await db.commit()
    return resultat


@router_gestion.put("/regles")
async def changer_regles(entree: ReglesEntree, request: Request, db: Db, acces: Decideur) -> ReglesSortie:
    try:
        resultat = await gestion.changer_regles(db, acces, entree, adresse_ip(request))
    except gestion.EtatInvalide as e:
        raise _erreur(e) from None
    await db.commit()
    return resultat


@router_gestion.get("/certificats")
async def lister_certificats(db: Db, _: Lecteur, etat: EtatCertificat | None = None) -> ListeCertificats:
    return await gestion.lister_certificats(db, etat)


@router_gestion.get("/badges")
async def lister_badges(db: Db, _: Lecteur) -> ListeBadges:
    return await gestion.lister_badges(db)


@router_gestion.post("/certificats/{certificat_id}/revoquer")
async def revoquer(
    certificat_id: UUID, entree: Motif, request: Request, db: Db, acces: Depublieur
) -> CertificatGestion:
    try:
        resultat = await gestion.revoquer(db, acces, certificat_id, entree.motif, adresse_ip(request))
    except (gestion.Introuvable, gestion.EtatInvalide) as e:
        raise _erreur(e) from None
    await db.commit()
    return resultat


@router_gestion.post("/certificats/{certificat_id}/reemettre")
async def reemettre(certificat_id: UUID, request: Request, db: Db, acces: Depublieur) -> CertificatGestion:
    try:
        resultat = await gestion.reemettre(db, acces, certificat_id, adresse_ip(request))
    except (gestion.Introuvable, gestion.EtatInvalide) as e:
        raise _erreur(e) from None
    await db.commit()
    return resultat
