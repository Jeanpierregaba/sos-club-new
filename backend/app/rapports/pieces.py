"""Justificatifs d'un rapport (spec 038) : documents PDF ou Word, et photos par les tables de la spec 024.

Le type d'un document se reconnaît à son contenu, jamais à son extension. Un document n'est servi qu'aux lecteurs
du rapport, en pièce jointe, et jamais d'une version qu'ils ne voient pas.
"""

import asyncio
import logging
import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.db import SessionLocal
from app.fichiers import docx, pdf
from app.fichiers.stockage import StockageIndisponible, stockage
from app.moderation import photos
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
from app.rapports import service
from app.rapports.models import PieceRapport, TypePiece, VersionPiece
from app.rapports.schemas import RapportDetail

OCTETS_MAX = 10 * 1024 * 1024
DOCUMENTS_MAX = 5
logger = logging.getLogger(__name__)
TYPES_MEDIA = {
    TypePiece.pdf: "application/pdf",
    TypePiece.docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def nom_propre(nom: str | None, type: TypePiece) -> str:
    """Le nom affiché : sans chemin, sans accent ni caractère spécial, avec la bonne extension."""
    base = (nom or "").replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9 _-]+", "", base).strip()[:120] or "document"
    return f"{base}.{type.value}"


async def _examiner(octets: bytes) -> tuple[TypePiece, bytes]:
    if octets.startswith(b"%PDF-"):
        try:
            infos = await pdf.examiner(octets)
        except pdf.PdfRefuse as refus:
            raise Refus(refus.message, 422) from None
        return TypePiece.pdf, infos.octets
    if octets.startswith(b"PK\x03\x04"):
        try:
            await asyncio.to_thread(docx.verifier, octets)
        except docx.DocxRefuse as refus:
            raise Refus(refus.message, 422) from None
        return TypePiece.docx, octets
    raise Refus("Seuls les documents PDF et Word (.docx) sont acceptés.", 422)


async def ajouter_document(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int, nom: str | None, octets: bytes
) -> RapportDetail:
    # Le contrôle d'abord, sans verrou ni transaction : il peut être long, et un refus ne touche à rien.
    type, propres = await _examiner(octets)
    contenu, rapport = await service._du_redacteur(db, utilisateur, contenu_id, version)
    travail = await service.ouvrir_travail(db, contenu)
    nombre = (
        await db.scalar(select(func.count()).select_from(VersionPiece).where(VersionPiece.version_id == travail.id))
    ) or 0
    if nombre >= DOCUMENTS_MAX:
        raise Refus(f"Un rapport compte {DOCUMENTS_MAX} documents au plus : retires-en un avant d'en ajouter.", 409)
    piece_id = uuid7()
    cle = f"rapports/{piece_id}-document.{type.value}"
    try:
        await stockage().enregistrer(cle, propres)
    except StockageIndisponible:
        raise Refus("L'envoi des documents est indisponible pour le moment : réessaie plus tard.", 503) from None
    db.add(
        PieceRapport(
            id=piece_id, contenu_id=contenu.id, auteur_id=utilisateur.id, nom=nom_propre(nom, type), type=type,
            cle_stockage=cle, octets=len(propres),
        )
    )  # fmt: skip
    await db.flush()
    db.add(VersionPiece(version_id=travail.id, piece_id=piece_id, ordre=nombre + 1))
    await db.commit()
    return await service.detail(db, utilisateur, contenu, rapport, "auteur")


async def retirer_document(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, piece_id: UUID, version: int
) -> RapportDetail:
    """Retire le document de la version de travail ; il reste dans les versions déjà soumises, et n'est effacé que
    s'il n'y figure nulle part."""
    contenu, rapport = await service._du_redacteur(db, utilisateur, contenu_id, version)
    travail = await service.ouvrir_travail(db, contenu)
    if await db.get(VersionPiece, (travail.id, piece_id)) is None:
        raise Introuvable
    await db.execute(
        delete(VersionPiece).where(VersionPiece.version_id == travail.id, VersionPiece.piece_id == piece_id)
    )
    a_effacer = None
    if not await db.scalar(select(VersionPiece.piece_id).where(VersionPiece.piece_id == piece_id).limit(1)):
        a_effacer = await db.get(PieceRapport, piece_id)
        if a_effacer is not None:
            await db.delete(a_effacer)
    await db.commit()
    if a_effacer is not None:
        await service.effacer_pieces([a_effacer])
    return await service.detail(db, utilisateur, contenu, rapport, "auteur")


async def lire_document(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, piece_id: UUID
) -> tuple[PieceRapport, bytes]:
    contenu, _, lecteur = await service._charger(db, utilisateur, contenu_id)
    version = await service._version_lue(db, contenu, lecteur)
    return await octets_du_document(db, version.id, contenu_id, piece_id)


async def octets_du_document(
    db: AsyncSession, version_id: UUID | None, contenu_id: UUID, piece_id: UUID
) -> tuple[PieceRapport, bytes]:
    """Les octets d'un document de ce rapport ; si `version_id` est donné, il doit appartenir à cette version."""
    piece = await db.get(PieceRapport, piece_id)
    if piece is None or piece.contenu_id != contenu_id or piece.efface_le is not None:
        raise Introuvable
    if version_id is not None and await db.get(VersionPiece, (version_id, piece_id)) is None:
        raise Introuvable
    try:
        octets = await stockage().lire(piece.cle_stockage)
    except StockageIndisponible:
        raise Refus("Les documents sont indisponibles pour le moment : réessaie plus tard.", 503) from None
    if octets is None:
        raise Introuvable
    return piece, octets


# Photos --------------------------------------------------------------------------------------------------------


async def ajouter_photo(
    db: AsyncSession,
    utilisateur: Utilisateur,
    contenu_id: UUID,
    version: int,
    octets: bytes,
    legende: str | None,
    ip: str,
) -> RapportDetail:
    preparees = await photos.preparer(octets)
    contenu, rapport = await service._du_redacteur(db, utilisateur, contenu_id, version)
    # Notre version de travail d'abord : elle reprend les documents de la précédente.
    await service.ouvrir_travail(db, contenu)
    await photos.ajouter(db, contenu, utilisateur, preparees, legende, False, ip)
    return await service.detail(db, utilisateur, contenu, rapport, "auteur")


async def retirer_photo(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, photo_id: UUID, version: int, ip: str
) -> RapportDetail:
    contenu, rapport = await service._du_redacteur(db, utilisateur, contenu_id, version)
    await service.ouvrir_travail(db, contenu)
    await photos.retirer(db, contenu, utilisateur, photo_id, ip)
    return await service.detail(db, utilisateur, contenu, rapport, "auteur")


async def lire_photo(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, photo_id: UUID, taille: str
) -> bytes:
    contenu, _, lecteur = await service._charger(db, utilisateur, contenu_id)
    version = await service._version_lue(db, contenu, lecteur)
    return await octets_de_photo(db, version.id, contenu_id, photo_id, taille)


async def octets_de_photo(db: AsyncSession, version_id: UUID, contenu_id: UUID, photo_id: UUID, taille: str) -> bytes:
    photo = await db.get(Photo, photo_id)
    if photo is None or photo.contenu_id != contenu_id or photo.efface_le is not None:
        raise Introuvable
    if await db.get(VersionPhoto, (version_id, photo_id)) is None:
        raise Introuvable
    try:
        octets = await stockage().lire(photo.cle_grande if taille == "grande" else photo.cle_vignette)
    except StockageIndisponible:
        raise Refus("Les photos sont indisponibles pour le moment : réessaie plus tard.", 503) from None
    if octets is None:
        raise Introuvable
    return octets


async def derniere_version_envoyee(db: AsyncSession, contenu_id: UUID) -> VersionContenu | None:
    return await db.scalar(
        select(VersionContenu)
        .where(VersionContenu.contenu_id == contenu_id, VersionContenu.soumise_le.is_not(None))
        .order_by(VersionContenu.numero.desc())
        .limit(1)
    )


# Purge ---------------------------------------------------------------------------------------------------------


async def purger(db: AsyncSession, maintenant: datetime | None = None) -> int:
    """Efface les documents des rapports refusés depuis plus de 90 jours, comme les photos (spec 024) : ceux d'un
    rapport clos par un refus, et ceux que seules des versions refusées utilisent. La ligne reste pour l'historique ;
    la mise à jour conditionnelle désigne un seul processus par document."""
    limite = (maintenant or datetime.now(UTC)) - photos.DELAI_EFFACEMENT
    vivante = (
        select(VersionPiece.piece_id)
        .join(VersionContenu, VersionContenu.id == VersionPiece.version_id)
        .join(Contenu, Contenu.id == VersionContenu.contenu_id)
        .where(VersionContenu.etat != EtatVersion.refusee, Contenu.etat != EtatContenu.refuse)
    )
    refus = select(DecisionModeration.contenu_id).where(DecisionModeration.decision == TypeDecision.refuser)
    refus_recent = refus.where(DecisionModeration.decide_le > limite)
    effaces = list(
        await db.scalars(
            update(PieceRapport)
            .where(
                PieceRapport.efface_le.is_(None),
                PieceRapport.contenu_id.in_(refus),
                PieceRapport.contenu_id.not_in(refus_recent),
                PieceRapport.id.not_in(vivante),
            )
            .values(efface_le=func.now())
            .returning(PieceRapport)
        )
    )
    await db.commit()
    await service.effacer_pieces(effaces)
    return len(effaces)


async def purger_regulierement() -> None:
    """Au démarrage, puis une fois par jour."""
    while True:
        try:
            async with SessionLocal() as db:
                nombre = await purger(db)
            if nombre:
                logger.info("%s document(s) de rapport refusé depuis plus de 90 jours effacé(s)", nombre)
        except Exception:
            logger.exception("Échec de la purge des documents des rapports")
        await asyncio.sleep(86_400)
