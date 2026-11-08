"""Côté auteur du moteur de modération (ADR-0009) : créer, modifier, soumettre, retirer, supprimer.

Chaque opération verrouille l'en-tête (`FOR UPDATE`) et contrôle sa version : l'auteur et un modérateur qui
agissent en même temps ne s'écrasent jamais. Une version soumise ne change plus ; pour un contenu publié, une
modification ouvre une nouvelle version, et l'ancienne reste en ligne jusqu'à la décision.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import Uuid, func, insert, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.moderation.models import Contenu, EtatContenu, EtatVersion, Photo, VersionContenu, VersionPhoto
from app.moderation.types import type_de
from app.referentiel.models import Etablissement, Iesg

MAX_EN_ATTENTE = 3
MAX_BROUILLONS = 20
MESSAGE_VERSION = "Ce contenu a été modifié entre-temps : recharge la page."


class Introuvable(Exception):
    pass


# Ce que l'auteur peut faire, selon l'état de l'en-tête.
MODIFIABLES = {EtatContenu.brouillon, EtatContenu.a_corriger, EtatContenu.publie, EtatContenu.depublie}
SOUMETTABLES = {EtatContenu.brouillon, EtatContenu.a_corriger}


async def contenu_de(
    db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, type: str, *, verrouiller: bool = False
) -> Contenu:
    """Le contenu de cet auteur, sinon Introuvable : un contenu d'un autre répond comme s'il n'existait pas."""
    contenu = await db.get(Contenu, contenu_id, with_for_update=verrouiller, populate_existing=verrouiller)
    if contenu is None or contenu.auteur_id != auteur.id or contenu.type != type:
        raise Introuvable
    return contenu


def verifier_version(contenu: Contenu, version: int | None) -> None:
    if version is None or contenu.version != version:
        raise Refus(MESSAGE_VERSION, 409)


async def version(db: AsyncSession, version_id: UUID | None) -> VersionContenu | None:
    return await db.get(VersionContenu, version_id) if version_id else None


async def version_visible_auteur(db: AsyncSession, contenu: Contenu) -> VersionContenu:
    """La version de travail si elle existe, sinon celle en ligne, sinon (contenu dépublié) la dernière."""
    courante = await version(db, contenu.version_travail_id or contenu.version_publiee_id)
    if courante is None:
        courante = await db.scalar(
            select(VersionContenu)
            .where(VersionContenu.contenu_id == contenu.id)
            .order_by(VersionContenu.numero.desc())
            .limit(1)
        )
    assert courante is not None
    return courante


async def _nouvelle_version(db: AsyncSession, contenu: Contenu, donnees: dict[str, Any]) -> VersionContenu:
    """Une version de travail, qui reprend les photos de la version qu'elle remplace (spec 024)."""
    numero = (
        await db.scalar(select(func.max(VersionContenu.numero)).where(VersionContenu.contenu_id == contenu.id))
    ) or 0
    precedente = (await version_visible_auteur(db, contenu)).id if numero else None
    nouvelle = VersionContenu(id=uuid7(), contenu_id=contenu.id, numero=numero + 1, donnees=donnees)
    db.add(nouvelle)
    await db.flush()
    if precedente:
        await db.execute(
            insert(VersionPhoto).from_select(
                ["version_id", "photo_id", "ordre", "legende", "couverture"],
                select(
                    literal(nouvelle.id, type_=Uuid), VersionPhoto.photo_id, VersionPhoto.ordre, VersionPhoto.legende,
                    VersionPhoto.couverture,
                )
                .join(Photo, Photo.id == VersionPhoto.photo_id)
                # Une photo dont les fichiers sont effacés (refus ancien) n'est jamais reprise.
                .where(VersionPhoto.version_id == precedente, Photo.efface_le.is_(None)),
            )
        )  # fmt: skip
    contenu.version_travail_id = nouvelle.id
    return nouvelle


async def verrouiller_auteur(db: AsyncSession, auteur: Utilisateur) -> None:
    """Sérialise les créations et soumissions d'un même auteur : les plafonds se comptent sans course."""
    await db.execute(select(Utilisateur.id).where(Utilisateur.id == auteur.id).with_for_update())


async def dre_de(db: AsyncSession, auteur: Utilisateur) -> str | None:
    """DRE de l'établissement de l'auteur : elle fixe le périmètre de la file."""
    profil: type[Eleve | Encadreur] = Eleve if auteur.role is Role.eleve else Encadreur
    return await db.scalar(
        select(Iesg.dre_code)
        .join(Etablissement, Etablissement.iesg_id == Iesg.id)
        .join(profil, profil.etablissement_id == Etablissement.id)
        .where(profil.utilisateur_id == auteur.id)
    )


async def creer(
    db: AsyncSession, auteur: Utilisateur, type: str, donnees: dict[str, Any], *, parent_id: UUID | None = None
) -> Contenu:
    await verrouiller_auteur(db, auteur)
    brouillons = await db.scalar(
        select(func.count())
        .select_from(Contenu)
        .where(
            Contenu.auteur_id == auteur.id,
            Contenu.type == type,
            Contenu.etat == EtatContenu.brouillon,
            Contenu.version_publiee_id.is_(None),
        )
    )
    if (brouillons or 0) >= MAX_BROUILLONS:
        raise Refus(
            f"Tu as déjà {MAX_BROUILLONS} brouillons : termine ou supprime-en un avant d'en commencer un autre.", 409
        )
    contenu = Contenu(id=uuid7(), type=type, auteur_id=auteur.id, etat=EtatContenu.brouillon, parent_id=parent_id)
    db.add(contenu)
    await db.flush()
    await _nouvelle_version(db, contenu, donnees)
    return contenu


async def ouvrir_travail(db: AsyncSession, contenu: Contenu) -> VersionContenu:
    """La version de travail, ouverte au besoin à partir de la version visible (texte et photos). À appeler sur un
    contenu verrouillé, version contrôlée."""
    if contenu.etat not in MODIFIABLES:
        raise Refus(
            "Ce contenu est en cours de modération : retire-le de la file pour le modifier."
            if contenu.etat is EtatContenu.en_attente
            else "Ce contenu a été refusé : il ne peut plus être modifié.",
            409,
        )
    travail = await version(db, contenu.version_travail_id)
    if travail is None or travail.etat is not EtatVersion.travail:
        # Une version à corriger reste dans l'historique ; un contenu publié garde sa version en ligne.
        visible = await version_visible_auteur(db, contenu)
        travail = await _nouvelle_version(db, contenu, dict(visible.donnees))
    if contenu.etat in {EtatContenu.publie, EtatContenu.depublie}:
        contenu.etat = EtatContenu.brouillon
    contenu.modifie_le = datetime.now(UTC)
    return travail


async def modifier(db: AsyncSession, contenu: Contenu, donnees: dict[str, Any]) -> None:
    """À appeler sur un contenu verrouillé, version contrôlée."""
    travail = await ouvrir_travail(db, contenu)
    travail.donnees = donnees


async def soumettre(db: AsyncSession, contenu: Contenu, auteur: Utilisateur, adresse_ip: str) -> None:
    if contenu.etat not in SOUMETTABLES:
        raise Refus("Ce contenu ne peut pas être soumis dans son état actuel.", 409)
    travail = await version(db, contenu.version_travail_id)
    if travail is None or travail.etat is not EtatVersion.travail:
        raise Refus("Corrige ton contenu avant de le soumettre de nouveau.", 409)
    await verrouiller_auteur(db, auteur)
    en_attente = await db.scalar(
        select(func.count())
        .select_from(Contenu)
        .where(Contenu.auteur_id == auteur.id, Contenu.type == contenu.type, Contenu.etat == EtatContenu.en_attente)
    )
    # Compté par type : des commentaires en attente ne bloquent pas un article, et l'inverse.
    if (en_attente or 0) >= MAX_EN_ATTENTE:
        raise Refus(
            f"Tu as déjà {MAX_EN_ATTENTE} {type_de(contenu.type).libelle}s en attente de modération : attends une "
            "décision avant d'en envoyer un autre.",
            409,
        )
    maintenant = datetime.now(UTC)
    travail.etat = EtatVersion.soumise
    travail.soumise_le = maintenant
    contenu.etat = EtatContenu.en_attente
    contenu.soumis_le = maintenant
    contenu.dre_code = await dre_de(db, auteur)
    journaliser(
        db, f"{contenu.type}_soumis", auteur, cible_type="contenu", cible_id=contenu.id,
        perimetre=contenu.dre_code or "national", details={"version": travail.numero}, adresse_ip=adresse_ip,
    )  # fmt: skip


async def retirer(db: AsyncSession, contenu: Contenu, auteur: Utilisateur, adresse_ip: str) -> None:
    if contenu.etat is not EtatContenu.en_attente:
        raise Refus("Ce contenu n'est pas en attente de modération.", 409)
    travail = await version(db, contenu.version_travail_id)
    assert travail is not None
    # `soumise_le` reste : un contenu déjà soumis garde son historique et ne se supprime plus.
    travail.etat = EtatVersion.travail
    contenu.etat = EtatContenu.brouillon
    contenu.soumis_le = None
    journaliser(
        db, f"{contenu.type}_retire", auteur, cible_type="contenu", cible_id=contenu.id,
        perimetre=contenu.dre_code or "national", details={"version": travail.numero}, adresse_ip=adresse_ip,
    )  # fmt: skip


async def retirer_definitivement(db: AsyncSession, contenu: Contenu, auteur: Utilisateur, adresse_ip: str) -> None:
    """L'auteur retire son contenu (un commentaire, spec 025), en attente ou publié : il quitte la file et le site,
    sans décision de modérateur ; ses versions et les points acquis restent. À appeler sur un contenu verrouillé."""
    if contenu.etat not in {EtatContenu.en_attente, EtatContenu.publie}:
        raise Refus("Ce contenu n'est ni en attente ni en ligne : il ne peut plus être retiré.", 409)
    travail = await version(db, contenu.version_travail_id)
    if travail is not None and travail.etat is EtatVersion.soumise:
        travail.etat = EtatVersion.retiree
    contenu.version_travail_id = None
    contenu.version_publiee_id = None
    contenu.etat = EtatContenu.retire
    journaliser(
        db, f"{contenu.type}_retire", auteur, cible_type="contenu", cible_id=contenu.id,
        perimetre=contenu.dre_code or "national", details={}, adresse_ip=adresse_ip,
    )  # fmt: skip


async def jamais_soumis(db: AsyncSession, contenu: Contenu) -> bool:
    soumises = await db.scalar(
        select(func.count())
        .select_from(VersionContenu)
        .where(VersionContenu.contenu_id == contenu.id, VersionContenu.soumise_le.is_not(None))
    )
    return contenu.etat is EtatContenu.brouillon and contenu.version_publiee_id is None and not soumises


async def supprimer(db: AsyncSession, contenu: Contenu) -> None:
    """Seul un brouillon jamais soumis se supprime ; le reste garde son historique de modération."""
    if not await jamais_soumis(db, contenu):
        raise Refus("Seul un brouillon jamais soumis peut être supprimé.", 409)
    contenu.version_travail_id = None
    await db.flush()
    await db.delete(contenu)
