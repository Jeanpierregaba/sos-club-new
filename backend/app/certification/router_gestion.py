"""Routes de gestion de la certification (spec 029), dans l'espace admin. Elles reprennent les droits `quiz` :
consulter pour lire ; approuver pour les règles des badges, dépublier pour révoquer et réémettre (droits sensibles,
double authentification). Les paramètres du parcours vivent avec ceux des jeux (`/admin/quiz/parametres`)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission, refuser
from app.certification import gestion, suivi
from app.certification.models import EtatCertificat
from app.certification.schemas import (
    CertificatGestion,
    EtatCandidat,
    ExportCandidats,
    FiltresCandidats,
    HistoriqueRegles,
    ListeBadges,
    ListeCertificats,
    Motif,
    PageCandidats,
    ReglesEntree,
    ReglesSortie,
    RoleCandidat,
    StatistiquesCertification,
)
from app.db import get_session

router_gestion = APIRouter(prefix="/admin/certification", tags=["admin"])

Db = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_permission("quiz", Action.consulter))]
Decideur = Annotated[Acces, Depends(exiger_permission("quiz", Action.approuver))]
Depublieur = Annotated[Acces, Depends(exiger_permission("quiz", Action.depublier))]
# L'export nominatif des candidats (spec 043) suit la règle de l'export des inscrits : national, avec le droit.
Exportateur = Annotated[Acces, Depends(exiger_permission("inscrits", Action.exporter, national=True))]


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
async def lister_certificats(db: Db, acces: Lecteur, etat: EtatCertificat | None = None) -> ListeCertificats:
    return await gestion.lister_certificats(db, etat, acces=acces)


@router_gestion.get("/badges")
async def lister_badges(db: Db, acces: Lecteur) -> ListeBadges:
    return await gestion.lister_badges(db, acces)


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


# Le suivi des certifications (spec 043) ----------------------------------------------------------------------------


@router_gestion.get("/suivi/candidats")
async def lister_candidats(
    db: Db,
    acces: Lecteur,
    dre: str | None = None,
    club_id: UUID | None = None,
    role: RoleCandidat | None = None,
    etat: EtatCandidat | None = None,
    recherche: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    par_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PageCandidats:
    filtres = FiltresCandidats(dre=dre, club_id=club_id, role=role, etat=etat, recherche=recherche or None)
    return await suivi.lister(db, acces, filtres, page=page, par_page=par_page)


@router_gestion.get("/suivi/statistiques")
async def statistiques_certification(db: Db, acces: Lecteur) -> StatistiquesCertification:
    resultat = await suivi.statistiques(db, acces)
    await db.commit()
    return resultat


@router_gestion.post("/suivi/candidats/export", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
async def exporter_candidats(entree: ExportCandidats, request: Request, db: Db, acces: Exportateur) -> Response:
    if not acces.a("quiz", Action.consulter):
        await refuser(db, request, acces, "quiz:consulter")
    try:
        contenu, _ = await suivi.exporter(db, acces, entree.filtres, entree.finalite, adresse_ip(request))
    except suivi.Refus as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from None
    return Response(
        content=contenu,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="suivi-certification.csv"'},
    )
