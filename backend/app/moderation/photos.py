"""Photos des contenus modérés (spec 024, ADR-0010).

Une photo est un fichier attesté par son auteur (Q8) ; son placement (légende, ordre, couverture) appartient à
chaque version. Ajouter, modifier ou retirer une photo ouvre la version de travail : la version en ligne garde
ses photos jusqu'à la décision. Lire une photo exige le droit de lire une version qui l'utilise.

Les fichiers sont écrits avant la validation de la base et effacés aussitôt si elle échoue ; un fichier n'est
effacé du disque qu'après la validation qui le libère.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.db import SessionLocal
from app.fichiers import images
from app.fichiers.stockage import StockageIndisponible, stockage
from app.moderation import service as moteur
from app.moderation.models import (
    Contenu,
    DecisionModeration,
    EtatContenu,
    EtatVersion,
    Photo,
    TypeDecision,
    VersionContenu,
    VersionPhoto,
)
from app.moderation.service import Introuvable

MAX_PHOTOS = 5
# Le texte que l'auteur coche, copié avec chaque photo : il fait foi s'il change un jour.
ATTESTATION = (
    "J'ai l'accord des personnes reconnaissables sur cette photo et, pour un élève mineur, celui de son parent ou "
    "tuteur."
)
DELAI_EFFACEMENT = timedelta(days=90)
TAILLES = ("grande", "vignette")

logger = logging.getLogger(__name__)


async def photos_de(db: AsyncSession, version_id: UUID | None) -> list[tuple[VersionPhoto, Photo]]:
    if version_id is None:
        return []
    lignes = await db.execute(
        select(VersionPhoto, Photo)
        .join(Photo, Photo.id == VersionPhoto.photo_id)
        .where(VersionPhoto.version_id == version_id)
        .order_by(VersionPhoto.couverture.desc(), VersionPhoto.ordre, Photo.cree_le)
    )
    return [(placement, photo) for placement, photo in lignes]


async def couvertures(db: AsyncSession, version_ids: list[UUID]) -> dict[UUID, tuple[VersionPhoto, Photo]]:
    """La couverture de chaque version, en une requête (liste publique des articles)."""
    if not version_ids:
        return {}
    lignes = await db.execute(
        select(VersionPhoto, Photo)
        .join(Photo, Photo.id == VersionPhoto.photo_id)
        .where(VersionPhoto.version_id.in_(version_ids), VersionPhoto.couverture, Photo.efface_le.is_(None))
    )
    return {placement.version_id: (placement, photo) for placement, photo in lignes}


async def _placement(db: AsyncSession, version_id: UUID, photo_id: UUID) -> VersionPhoto:
    placement = await db.get(VersionPhoto, (version_id, photo_id))
    if placement is None:
        raise Introuvable
    return placement


async def _retirer_couverture(db: AsyncSession, version_id: UUID) -> None:
    await db.execute(
        update(VersionPhoto)
        .where(VersionPhoto.version_id == version_id, VersionPhoto.couverture)
        .values(couverture=False)
    )


def _journaliser(db: AsyncSession, action: str, auteur: Utilisateur, contenu: Contenu, photo_id: UUID, ip: str) -> None:
    journaliser(
        db, action, auteur, cible_type="contenu", cible_id=contenu.id,
        perimetre=contenu.dre_code or "national", details={"photo_id": str(photo_id)}, adresse_ip=ip,
    )  # fmt: skip


async def preparer(octets: bytes) -> images.ImagesPreparees:
    try:
        return await images.preparer(octets)
    except images.ImageRefusee as refus:
        raise Refus(str(refus)) from None


async def ajouter(
    db: AsyncSession,
    contenu: Contenu,
    auteur: Utilisateur,
    preparees: images.ImagesPreparees,
    legende: str | None,
    couverture: bool,
    ip: str,
) -> None:
    """Sur un contenu verrouillé, version contrôlée, avec une image déjà préparée (hors verrou : le traitement est
    long et ne doit pas garder une connexion ni le verrou de l'article). Valide la transaction."""
    travail = await moteur.ouvrir_travail(db, contenu)
    nombre = (
        await db.scalar(select(func.count()).select_from(VersionPhoto).where(VersionPhoto.version_id == travail.id))
    ) or 0
    if nombre >= MAX_PHOTOS:
        raise Refus(
            f"Un article ou une actualité compte {MAX_PHOTOS} photos au plus : retires-en une avant d'en ajouter.", 409
        )
    photo_id = uuid7()
    cles = {taille: f"photos/{photo_id}-{taille}.webp" for taille in TAILLES}
    disque = stockage()
    try:
        await disque.enregistrer(cles["grande"], preparees.grande.octets)
        await disque.enregistrer(cles["vignette"], preparees.vignette.octets)
        db.add(
            Photo(
                id=photo_id, contenu_id=contenu.id, auteur_id=auteur.id, cle_grande=cles["grande"],
                cle_vignette=cles["vignette"], largeur=preparees.grande.largeur, hauteur=preparees.grande.hauteur,
                octets=len(preparees.grande.octets), attestation=ATTESTATION,
            )
        )  # fmt: skip
        await db.flush()
        # La première photo devient la couverture si l'auteur n'en a pas encore choisi.
        sans_couverture = not await db.scalar(
            select(exists().where(VersionPhoto.version_id == travail.id, VersionPhoto.couverture))
        )
        if couverture:
            await _retirer_couverture(db, travail.id)
        ordre = (
            await db.scalar(select(func.max(VersionPhoto.ordre)).where(VersionPhoto.version_id == travail.id))
        ) or 0
        db.add(
            VersionPhoto(
                version_id=travail.id, photo_id=photo_id, ordre=ordre + 1, legende=legende,
                couverture=couverture or sans_couverture,
            )
        )  # fmt: skip
        _journaliser(db, "photo_ajoutee", auteur, contenu, photo_id, ip)
        await db.commit()
    except StockageIndisponible:
        await db.rollback()
        for cle in cles.values():
            await disque.supprimer(cle)
        raise Refus("L'enregistrement des photos est indisponible pour le moment : réessaie plus tard.", 503) from None
    except BaseException:
        await db.rollback()
        for cle in cles.values():
            await disque.supprimer(cle)
        raise


async def modifier(
    db: AsyncSession,
    contenu: Contenu,
    photo_id: UUID,
    *,
    legende: str | None,
    changer_legende: bool,
    couverture: bool | None,
    ordre: int | None,
) -> None:
    travail = await moteur.ouvrir_travail(db, contenu)
    placement = await _placement(db, travail.id, photo_id)
    if changer_legende:
        placement.legende = legende
    if couverture:
        await _retirer_couverture(db, travail.id)
        placement.couverture = True
    elif couverture is False and placement.couverture:
        # Une version qui a des photos garde toujours une couverture : la suivante prend la place.
        placement.couverture = False
        await db.flush()
        suivante = await db.scalar(
            select(VersionPhoto)
            .where(VersionPhoto.version_id == travail.id, VersionPhoto.photo_id != photo_id)
            .order_by(VersionPhoto.ordre)
            .limit(1)
        )
        if suivante is None:
            placement.couverture = True
        else:
            suivante.couverture = True
    if ordre is not None:
        placement.ordre = ordre
    await db.commit()


async def _utilisee(db: AsyncSession, photo_id: UUID) -> bool:
    return bool(await db.scalar(select(exists().where(VersionPhoto.photo_id == photo_id))))


async def _effacer_fichiers(photo: Photo) -> None:
    """Appelée après la validation : un fichier qui résiste est journalisé, l'opération reste réussie."""
    disque = stockage()
    for cle in (photo.cle_grande, photo.cle_vignette):
        try:
            await disque.supprimer(cle)
        except OSError:
            logger.exception("Fichier %s non effacé : à reprendre par le balayage des orphelins", cle)


async def retirer(db: AsyncSession, contenu: Contenu, auteur: Utilisateur, photo_id: UUID, ip: str) -> None:
    travail = await moteur.ouvrir_travail(db, contenu)
    placement = await _placement(db, travail.id, photo_id)
    etait_couverture = placement.couverture
    await db.delete(placement)
    await db.flush()
    if etait_couverture:
        # Une autre photo devient la couverture, s'il en reste.
        suivante = await db.scalar(
            select(VersionPhoto).where(VersionPhoto.version_id == travail.id).order_by(VersionPhoto.ordre).limit(1)
        )
        if suivante is not None:
            suivante.couverture = True
    photo = await db.get(Photo, photo_id)
    assert photo is not None
    # Jamais soumise ni publiée (aucune autre version ne l'utilise, et cette version n'a jamais été envoyée) : elle
    # disparaît tout à fait. Sinon, elle reste dans l'historique.
    a_effacer = travail.soumise_le is None and not await _utilisee(db, photo_id)
    if a_effacer:
        await db.delete(photo)
    _journaliser(db, "photo_retiree", auteur, contenu, photo_id, ip)
    await db.commit()
    if a_effacer:
        await _effacer_fichiers(photo)


async def effacer_du_brouillon(db: AsyncSession, contenu: Contenu) -> list[Photo]:
    """Avant la suppression d'un brouillon jamais soumis : ses photos, à effacer du disque après la validation."""
    photos = list(await db.scalars(select(Photo).where(Photo.contenu_id == contenu.id)))
    for photo in photos:
        await db.execute(VersionPhoto.__table__.delete().where(VersionPhoto.photo_id == photo.id))
        await db.delete(photo)
    return photos


async def effacer_fichiers(photos: list[Photo]) -> None:
    for photo in photos:
        await _effacer_fichiers(photo)


# Lecture --------------------------------------------------------------------------------------------------------


async def _octets(db: AsyncSession, contenu_id: UUID, photo_id: UUID, taille: str, *, version_id: UUID | None) -> bytes:
    """Les octets d'une photo de ce contenu ; si `version_id` est donné, la photo doit appartenir à cette version."""
    photo = await db.get(Photo, photo_id)
    if photo is None or photo.contenu_id != contenu_id or photo.efface_le is not None:
        raise Introuvable
    if version_id is not None and await db.get(VersionPhoto, (version_id, photo_id)) is None:
        raise Introuvable
    try:
        octets = await stockage().lire(photo.cle_grande if taille == "grande" else photo.cle_vignette)
    except StockageIndisponible:
        raise Refus("Les photos sont indisponibles pour le moment : réessaie plus tard.", 503) from None
    if octets is None:
        raise Introuvable
    return octets


async def lire_pour_auteur(
    db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, type: str, photo_id: UUID, taille: str
) -> bytes:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type)
    return await _octets(db, contenu.id, photo_id, taille, version_id=None)


async def lire_pour_moderateur(db: AsyncSession, acces: Acces, contenu_id: UUID, photo_id: UUID, taille: str) -> bytes:
    """Comme l'aperçu : seulement une photo d'une version envoyée par l'auteur, jamais d'une version de travail."""
    contenu = await db.get(Contenu, contenu_id)
    if contenu is None or (not acces.national and contenu.dre_code != acces.collaborateur.perimetre_dre):
        raise Introuvable
    envoyee = await db.scalar(
        select(VersionPhoto.version_id)
        .join(VersionContenu, VersionContenu.id == VersionPhoto.version_id)
        .where(
            VersionPhoto.photo_id == photo_id,
            VersionContenu.contenu_id == contenu.id,
            VersionContenu.etat != EtatVersion.travail,
        )
        .limit(1)
    )
    if envoyee is None:
        raise Introuvable
    return await _octets(db, contenu.id, photo_id, taille, version_id=None)


async def lire_publique(db: AsyncSession, types: tuple[str, ...], adresse: str, photo_id: UUID, taille: str) -> bytes:
    contenu = await db.scalar(
        select(Contenu).where(
            Contenu.type.in_(types), Contenu.adresse == adresse, Contenu.version_publiee_id.is_not(None)
        )
    )
    if contenu is None:
        raise Introuvable
    return await _octets(db, contenu.id, photo_id, taille, version_id=contenu.version_publiee_id)


# Effacement à 90 jours ------------------------------------------------------------------------------------------


async def purger(db: AsyncSession, maintenant: datetime | None = None) -> int:
    """Efface les fichiers des photos refusées depuis plus de 90 jours : celles d'un contenu clos par un refus, et
    celles que seules des versions refusées utilisent. Plusieurs processus peuvent la lancer en même temps :
    la mise à jour conditionnelle désigne un seul processus par photo."""
    limite = (maintenant or datetime.now(UTC)) - DELAI_EFFACEMENT
    # Encore utile : dans une version non refusée d'un contenu qui n'est pas clos par un refus.
    vivante = (
        select(VersionPhoto.photo_id)
        .join(VersionContenu, VersionContenu.id == VersionPhoto.version_id)
        .join(Contenu, Contenu.id == VersionContenu.contenu_id)
        .where(VersionContenu.etat != EtatVersion.refusee, Contenu.etat != EtatContenu.refuse)
    )
    refus = select(DecisionModeration.contenu_id).where(DecisionModeration.decision == TypeDecision.refuser)
    # Un refus de moins de 90 jours sur ce contenu : on attend encore.
    refus_recent = refus.where(DecisionModeration.decide_le > limite)
    effacees = list(
        await db.scalars(
            update(Photo)
            .where(
                Photo.efface_le.is_(None),
                Photo.contenu_id.in_(refus),
                Photo.contenu_id.not_in(refus_recent),
                Photo.id.not_in(vivante),
            )
            .values(efface_le=func.now())
            .returning(Photo)
        )
    )
    await db.commit()
    for photo in effacees:
        await _effacer_fichiers(photo)
    return len(effacees)


async def purger_regulierement() -> None:
    """Au démarrage, puis une fois par jour."""
    while True:
        try:
            async with SessionLocal() as db:
                nombre = await purger(db)
            if nombre:
                logger.info("%s photo(s) refusée(s) depuis plus de 90 jours effacée(s)", nombre)
        except Exception:
            logger.exception("Échec de la purge des photos")
        await asyncio.sleep(86_400)
