"""Routes de gestion de la bibliothèque (spec 028), dans l'espace admin. Chaque route exige son droit
`bibliotheque` ; approuver et dépublier sont des droits sensibles (double authentification)."""

from collections.abc import Awaitable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.bibliotheque import gestion, lecture
from app.bibliotheque.models import EtatRessource
from app.bibliotheque.schemas import Approbation, ListeGestion, Motif, RessourceEntree, RessourceGestion
from app.config import settings
from app.db import get_session
from app.fichiers import images, pdf

router_gestion = APIRouter(prefix="/admin/bibliotheque", tags=["admin"])

Db = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_permission("bibliotheque", Action.consulter))]
Createur = Annotated[Acces, Depends(exiger_permission("bibliotheque", Action.creer))]
Redacteur = Annotated[Acces, Depends(exiger_permission("bibliotheque", Action.modifier))]
Soumetteur = Annotated[Acces, Depends(exiger_permission("bibliotheque", Action.soumettre))]
Decideur = Annotated[Acces, Depends(exiger_permission("bibliotheque", Action.approuver))]
Depublieur = Annotated[Acces, Depends(exiger_permission("bibliotheque", Action.depublier))]
Fichier = Annotated[UploadFile, File()]

ERREURS = (gestion.Introuvable, gestion.Refuse, gestion.Invalide, gestion.EtatInvalide, gestion.Indisponible)


def _erreur(e: Exception) -> HTTPException:
    if isinstance(e, gestion.Introuvable):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Cette ressource est introuvable.")
    if isinstance(e, gestion.Refuse):
        return HTTPException(
            status.HTTP_403_FORBIDDEN, "Tu as préparé cette ressource : un autre membre de l'équipe doit la publier."
        )
    if isinstance(e, gestion.Invalide):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, e.message)
    if isinstance(e, gestion.Indisponible):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, lecture.INDISPONIBLE)
    return HTTPException(status.HTTP_409_CONFLICT, str(e))


async def _lire(fichier: UploadFile, limite: int, quoi: str) -> bytes:
    # Starlette a déjà reçu le formulaire : on n'en lit que la limite + 1 octet pour décider.
    octets = await fichier.read(limite + 1)
    if len(octets) > limite:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"{quoi} dépasse {limite // (1024 * 1024)} Mo : réduis la taille du fichier avant de l'envoyer.",
        )
    return octets


async def _executer(db: AsyncSession, acces: Acces, ressource_id: UUID, action: Awaitable[None]) -> RessourceGestion:
    try:
        await action
    except ERREURS as e:
        raise _erreur(e) from None
    await db.commit()
    return await gestion.detail(db, acces, ressource_id)


@router_gestion.get("")
async def lister(db: Db, acces: Lecteur, etat: EtatRessource | None = None) -> ListeGestion:
    return await gestion.lister(db, acces, etat)


@router_gestion.post("", status_code=status.HTTP_201_CREATED)
async def creer(entree: RessourceEntree, request: Request, db: Db, acces: Createur) -> RessourceGestion:
    try:
        ressource = await gestion.creer(db, acces, entree, adresse_ip(request))
    except ERREURS as e:
        raise _erreur(e) from None
    await db.commit()
    return await gestion.detail(db, acces, ressource.id)


@router_gestion.get("/{ressource_id}")
async def lire(ressource_id: UUID, db: Db, acces: Lecteur) -> RessourceGestion:
    try:
        return await gestion.detail(db, acces, ressource_id)
    except ERREURS as e:
        raise _erreur(e) from None


@router_gestion.put("/{ressource_id}")
async def modifier(
    ressource_id: UUID, entree: RessourceEntree, request: Request, db: Db, acces: Redacteur
) -> RessourceGestion:
    return await _executer(
        db, acces, ressource_id, gestion.modifier(db, acces, ressource_id, entree, adresse_ip(request))
    )


@router_gestion.delete("/{ressource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer(ressource_id: UUID, request: Request, db: Db, acces: Redacteur) -> None:
    try:
        await gestion.supprimer(db, acces, ressource_id, adresse_ip(request))
    except ERREURS as e:
        raise _erreur(e) from None


# Fichiers ---------------------------------------------------------------------------------------------------------


@router_gestion.put("/{ressource_id}/fichier")
async def deposer_fichier(
    ressource_id: UUID, fichier: Fichier, request: Request, db: Db, acces: Redacteur
) -> RessourceGestion:
    octets = await _lire(fichier, settings.ressource_octets_max, "Ce PDF")
    try:
        infos = await pdf.examiner(octets)
    except pdf.PdfRefuse as refus:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, refus.message) from None
    try:
        await gestion.deposer_fichier(db, acces, ressource_id, octets, infos, adresse_ip(request))
    except ERREURS as e:
        raise _erreur(e) from None
    return await gestion.detail(db, acces, ressource_id)


@router_gestion.put("/{ressource_id}/couverture")
async def deposer_couverture(
    ressource_id: UUID, fichier: Fichier, request: Request, db: Db, acces: Redacteur
) -> RessourceGestion:
    octets = await _lire(fichier, settings.photo_octets_max, "Cette image")
    try:
        preparees = await images.preparer(octets)
    except images.ImageRefusee as refus:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(refus)) from None
    try:
        await gestion.deposer_couverture(db, acces, ressource_id, preparees, adresse_ip(request))
    except ERREURS as e:
        raise _erreur(e) from None
    return await gestion.detail(db, acces, ressource_id)


@router_gestion.delete("/{ressource_id}/couverture")
async def retirer_couverture(ressource_id: UUID, request: Request, db: Db, acces: Redacteur) -> RessourceGestion:
    try:
        await gestion.retirer_couverture(db, acces, ressource_id, adresse_ip(request))
    except ERREURS as e:
        raise _erreur(e) from None
    return await gestion.detail(db, acces, ressource_id)


# Relecture, quel que soit l'état : jamais comptée comme un téléchargement.
@router_gestion.get("/{ressource_id}/fichier", response_class=StreamingResponse)
async def relire_fichier(ressource_id: UUID, db: Db, _: Lecteur) -> StreamingResponse:
    try:
        ressource = await gestion.charger(db, ressource_id)
    except ERREURS as e:
        raise _erreur(e) from None
    return await lecture.pdf(ressource, telecharger=False)


@router_gestion.get("/{ressource_id}/couverture/{taille}", response_class=Response)
async def relire_couverture(ressource_id: UUID, taille: str, db: Db, _: Lecteur) -> Response:
    try:
        ressource = await gestion.charger(db, ressource_id)
    except ERREURS as e:
        raise _erreur(e) from None
    return await lecture.couverture(ressource, taille)


# Transitions ------------------------------------------------------------------------------------------------------


@router_gestion.post("/{ressource_id}/soumettre")
async def soumettre(ressource_id: UUID, request: Request, db: Db, acces: Soumetteur) -> RessourceGestion:
    return await _executer(db, acces, ressource_id, gestion.soumettre(db, acces, ressource_id, adresse_ip(request)))


@router_gestion.post("/{ressource_id}/reprendre")
async def reprendre(ressource_id: UUID, request: Request, db: Db, acces: Soumetteur) -> RessourceGestion:
    return await _executer(db, acces, ressource_id, gestion.reprendre(db, acces, ressource_id, adresse_ip(request)))


@router_gestion.post("/{ressource_id}/approuver")
async def approuver(
    ressource_id: UUID, entree: Approbation, request: Request, db: Db, acces: Decideur
) -> RessourceGestion:
    return await _executer(
        db, acces, ressource_id, gestion.approuver(db, acces, ressource_id, entree, adresse_ip(request))
    )


@router_gestion.post("/{ressource_id}/refuser")
async def refuser(ressource_id: UUID, entree: Motif, request: Request, db: Db, acces: Decideur) -> RessourceGestion:
    return await _executer(
        db, acces, ressource_id, gestion.refuser(db, acces, ressource_id, entree.motif, adresse_ip(request))
    )


@router_gestion.post("/{ressource_id}/depublier")
async def depublier(ressource_id: UUID, entree: Motif, request: Request, db: Db, acces: Depublieur) -> RessourceGestion:
    return await _executer(
        db, acces, ressource_id, gestion.depublier(db, acces, ressource_id, entree.motif, adresse_ip(request))
    )
