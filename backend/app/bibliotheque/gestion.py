"""Gestion de la bibliothèque (spec 028) : un collaborateur prépare et soumet ; un autre publie en nommant la
personne qui a validé le contenu (Q11). Seuls les droits `bibliotheque` y donnent accès, vérifiés par les routes.

Chaque opération verrouille la ressource et vérifie son état : de deux décisions simultanées, la seconde reçoit
409. Chaque écriture entre au journal d'audit, dans la même transaction.

Fichiers (ADR-0010) : le PDF est vérifié et la couverture préparée avant le verrou (c'est long). Le nouveau fichier
est écrit avant la validation de la base et effacé aussitôt si elle échoue ; l'ancien n'est effacé qu'après la
validation qui le libère. Les fonctions qui touchent aux fichiers valident donc elles-mêmes la transaction.
"""

import logging
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.bibliotheque.schemas import Approbation, ListeGestion, RessourceEntree, RessourceGestion
from app.fichiers import images
from app.fichiers.pdf import InfosPdf
from app.fichiers.stockage import StockageIndisponible, stockage
from app.notifications.service import notifier
from app.referentiel.models import Axe

logger = logging.getLogger(__name__)


class Introuvable(Exception):
    pass


class EtatInvalide(Exception):
    """L'opération ne vaut pas dans l'état actuel de la ressource (409)."""


class Refuse(Exception):
    """Publication à deux personnes : un contributeur ne publie pas sa propre ressource (403)."""


class Invalide(Exception):
    """Données refusées (422), avec un message pour l'équipe."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class Indisponible(Exception):
    """Stockage indisponible (503)."""


# Lecture ----------------------------------------------------------------------------------------------------------


def vue(ressource: Ressource, acces: Acces) -> RessourceGestion:
    return RessourceGestion(
        id=ressource.id,
        titre=ressource.titre,
        description=ressource.description,
        categorie=ressource.categorie,
        axe_code=ressource.axe_code,
        parution=ressource.parution,
        etat=ressource.etat,
        contenu_de_test=ressource.contenu_de_test,
        fichier_octets=ressource.fichier_octets,
        pages=ressource.pages,
        a_couverture=ressource.couverture_grande is not None,
        telechargements=ressource.telechargements,
        soumis_le=ressource.soumis_le,
        decide_le=ressource.decide_le,
        motif=ressource.motif,
        validateur_nom=ressource.validateur_nom,
        validateur_qualite=ressource.validateur_qualite,
        publie_le=ressource.publie_le,
        deja_publiee=ressource.deja_publiee,
        modifie_le=ressource.modifie_le,
        contributeur=acces.utilisateur.id in (ressource.contributeurs or []),
    )


async def lister(db: AsyncSession, acces: Acces, etat: EtatRessource | None = None) -> ListeGestion:
    requete = select(Ressource)
    if etat is not None:
        requete = requete.where(Ressource.etat == etat)
    toutes = (await db.scalars(requete.order_by(Ressource.modifie_le.desc(), Ressource.id))).all()
    return ListeGestion(ressources=[vue(r, acces) for r in toutes])


async def detail(db: AsyncSession, acces: Acces, ressource_id: UUID) -> RessourceGestion:
    ressource = await db.get(Ressource, ressource_id, populate_existing=True)
    if ressource is None:
        raise Introuvable
    return vue(ressource, acces)


async def charger(db: AsyncSession, ressource_id: UUID) -> Ressource:
    ressource = await db.get(Ressource, ressource_id)
    if ressource is None:
        raise Introuvable
    return ressource


# Préparer ---------------------------------------------------------------------------------------------------------


async def _verrouiller(db: AsyncSession, ressource_id: UUID) -> Ressource:
    ressource = await db.scalar(
        select(Ressource)
        .where(Ressource.id == ressource_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if ressource is None:
        raise Introuvable
    return ressource


def _brouillon(ressource: Ressource) -> None:
    if ressource.etat is not EtatRessource.brouillon:
        raise EtatInvalide("Seule une ressource en brouillon se modifie : reprends-la d'abord en brouillon.")


def _contribue(ressource: Ressource, acces: Acces) -> None:
    if acces.utilisateur.id not in (ressource.contributeurs or []):
        ressource.contributeurs = [*(ressource.contributeurs or []), acces.utilisateur.id]


def _journal(db: AsyncSession, action: str, acces: Acces, ressource: Ressource, ip: str, **details: object) -> None:
    journaliser(
        db, f"bibliotheque_{action}", acces.utilisateur, cible_type="ressource", cible_id=ressource.id,
        perimetre="national", details={"titre": ressource.titre, **details}, adresse_ip=ip,
    )  # fmt: skip


async def _axe_existe(db: AsyncSession, code: str | None) -> None:
    if code is not None and await db.get(Axe, code) is None:
        raise Invalide("Cet axe n'existe pas.")


async def creer(db: AsyncSession, acces: Acces, entree: RessourceEntree, ip: str) -> Ressource:
    await _axe_existe(db, entree.axe_code)
    ressource = Ressource(
        id=uuid7(), **entree.model_dump(), etat=EtatRessource.brouillon, contributeurs=[acces.utilisateur.id]
    )
    db.add(ressource)
    await db.flush()
    _journal(db, "creee", acces, ressource, ip)
    return ressource


async def modifier(db: AsyncSession, acces: Acces, ressource_id: UUID, entree: RessourceEntree, ip: str) -> None:
    ressource = await _verrouiller(db, ressource_id)
    _brouillon(ressource)
    await _axe_existe(db, entree.axe_code)
    for champ, valeur in entree.model_dump().items():
        setattr(ressource, champ, valeur)
    _contribue(ressource, acces)
    _journal(db, "modifiee", acces, ressource, ip)


# Applique un changement de fichiers à la ressource verrouillée ; renvoie les clés qu'il libère.
Appliquer = Callable[[Ressource], list[str]]


async def _remplacer(
    db: AsyncSession, nouvelles: dict[str, bytes], appliquer: Appliquer, ressource_id: UUID
) -> list[str]:
    """Écrit les nouveaux fichiers, applique le changement sous verrou et valide ; renvoie les clés libérées.
    En cas d'échec, les nouveaux fichiers sont effacés et rien ne change."""
    disque = stockage()
    try:
        for cle, octets in nouvelles.items():
            await disque.enregistrer(cle, octets)
        ressource = await _verrouiller(db, ressource_id)
        _brouillon(ressource)
        liberees = appliquer(ressource)
        await db.commit()
    except StockageIndisponible:
        await db.rollback()
        await _effacer(nouvelles)
        raise Indisponible from None
    except BaseException:
        await db.rollback()
        await _effacer(nouvelles)
        raise
    return liberees


async def _effacer(cles: Iterable[str]) -> None:
    """Appelée hors transaction : un fichier qui résiste est journalisé, l'opération reste réussie."""
    disque = stockage()
    for cle in cles:
        try:
            await disque.supprimer(cle)
        except OSError:
            logger.exception("Fichier %s non effacé : à reprendre par le balayage des orphelins", cle)


async def deposer_fichier(
    db: AsyncSession, acces: Acces, ressource_id: UUID, octets: bytes, infos: InfosPdf, ip: str
) -> None:
    cle = f"ressources/{uuid7()}-document.pdf"

    def appliquer(ressource: Ressource) -> list[str]:
        ancienne = ressource.fichier_cle
        ressource.fichier_cle, ressource.fichier_octets, ressource.pages = cle, len(octets), infos.pages
        _contribue(ressource, acces)
        _journal(db, "fichier_depose", acces, ressource, ip, octets=len(octets), pages=infos.pages)
        return [ancienne] if ancienne else []

    await _effacer(await _remplacer(db, {cle: octets}, appliquer, ressource_id))


async def deposer_couverture(
    db: AsyncSession, acces: Acces, ressource_id: UUID, preparees: images.ImagesPreparees, ip: str
) -> None:
    base = uuid7()
    grande, vignette = f"ressources/{base}-grande.webp", f"ressources/{base}-vignette.webp"

    def appliquer(ressource: Ressource) -> list[str]:
        anciennes = [c for c in (ressource.couverture_grande, ressource.couverture_vignette) if c]
        ressource.couverture_grande, ressource.couverture_vignette = grande, vignette
        _contribue(ressource, acces)
        _journal(db, "couverture_deposee", acces, ressource, ip)
        return anciennes

    nouvelles = {grande: preparees.grande.octets, vignette: preparees.vignette.octets}
    await _effacer(await _remplacer(db, nouvelles, appliquer, ressource_id))


async def retirer_couverture(db: AsyncSession, acces: Acces, ressource_id: UUID, ip: str) -> None:
    def appliquer(ressource: Ressource) -> list[str]:
        anciennes = [c for c in (ressource.couverture_grande, ressource.couverture_vignette) if c]
        ressource.couverture_grande = ressource.couverture_vignette = None
        _contribue(ressource, acces)
        _journal(db, "couverture_retiree", acces, ressource, ip)
        return anciennes

    await _effacer(await _remplacer(db, {}, appliquer, ressource_id))


async def supprimer(db: AsyncSession, acces: Acces, ressource_id: UUID, ip: str) -> None:
    """Seule une ressource jamais publiée se supprime, avec ses fichiers ; une autre se dépublie."""
    ressource = await _verrouiller(db, ressource_id)
    _brouillon(ressource)
    if ressource.deja_publiee:
        raise EtatInvalide("Une ressource déjà publiée ne se supprime pas : elle reste dépubliée.")
    cles = [c for c in (ressource.fichier_cle, ressource.couverture_grande, ressource.couverture_vignette) if c]
    _journal(db, "supprimee", acces, ressource, ip)
    await db.delete(ressource)
    await db.commit()
    await _effacer(cles)


async def soumettre(db: AsyncSession, acces: Acces, ressource_id: UUID, ip: str) -> None:
    ressource = await _verrouiller(db, ressource_id)
    _brouillon(ressource)
    if ressource.fichier_cle is None:
        raise Invalide("Dépose d'abord le PDF de la ressource.")
    if ressource.categorie is CategorieRessource.magazine and ressource.couverture_grande is None:
        raise Invalide("Un magazine a besoin d'une couverture : elle s'affiche dans « À la Une ».")
    ressource.etat = EtatRessource.soumis
    ressource.soumis_par = acces.utilisateur.id
    ressource.soumis_le = datetime.now(UTC)
    _contribue(ressource, acces)
    _journal(db, "soumise", acces, ressource, ip)


async def reprendre(db: AsyncSession, acces: Acces, ressource_id: UUID, ip: str) -> None:
    """Une ressource soumise (retirée de la file) ou dépubliée revient en brouillon pour être modifiée."""
    ressource = await _verrouiller(db, ressource_id)
    if ressource.etat not in (EtatRessource.soumis, EtatRessource.depublie):
        raise EtatInvalide("Seule une ressource soumise ou dépubliée se reprend en brouillon.")
    ressource.etat = EtatRessource.brouillon
    _journal(db, "reprise", acces, ressource, ip)


# Décider ----------------------------------------------------------------------------------------------------------


def _prevenir(db: AsyncSession, ressource: Ressource, titre: str, message: str | None) -> None:
    if ressource.soumis_par is not None:
        notifier(
            db, ressource.soumis_par, "bibliotheque_decision", titre, message, f"/admin/bibliotheque/{ressource.id}"
        )


async def approuver(db: AsyncSession, acces: Acces, ressource_id: UUID, entree: Approbation, ip: str) -> None:
    ressource = await _verrouiller(db, ressource_id)
    if acces.utilisateur.id in (ressource.contributeurs or []):
        raise Refuse
    if ressource.etat is not EtatRessource.soumis:
        raise EtatInvalide("Cette ressource n'est plus en attente de publication.")
    maintenant = datetime.now(UTC)
    ressource.etat = EtatRessource.publie
    ressource.decide_par, ressource.decide_le = acces.utilisateur.id, maintenant
    ressource.validateur_nom, ressource.validateur_qualite = entree.validateur_nom, entree.validateur_qualite
    ressource.publie_le = maintenant
    ressource.deja_publiee = True
    ressource.motif = None
    _prevenir(db, ressource, f"Ta ressource « {ressource.titre} » est publiée", None)
    _journal(
        db, "approuvee", acces, ressource, ip,
        validateur_nom=entree.validateur_nom, validateur_qualite=entree.validateur_qualite,
    )  # fmt: skip


async def refuser(db: AsyncSession, acces: Acces, ressource_id: UUID, motif: str, ip: str) -> None:
    ressource = await _verrouiller(db, ressource_id)
    if ressource.etat is not EtatRessource.soumis:
        raise EtatInvalide("Cette ressource n'est plus en attente de publication.")
    ressource.etat = EtatRessource.brouillon
    ressource.decide_par, ressource.decide_le, ressource.motif = acces.utilisateur.id, datetime.now(UTC), motif
    _prevenir(db, ressource, f"Ta ressource « {ressource.titre} » n'est pas publiée", motif)
    _journal(db, "refusee", acces, ressource, ip, motif=motif)


async def depublier(db: AsyncSession, acces: Acces, ressource_id: UUID, motif: str, ip: str) -> None:
    """La ressource disparaît de la bibliothèque et son fichier n'est plus servi au public."""
    ressource = await _verrouiller(db, ressource_id)
    if ressource.etat is not EtatRessource.publie:
        raise EtatInvalide("Cette ressource n'est pas en ligne.")
    ressource.etat = EtatRessource.depublie
    ressource.decide_par, ressource.decide_le, ressource.motif = acces.utilisateur.id, datetime.now(UTC), motif
    _prevenir(db, ressource, f"Ta ressource « {ressource.titre} » est dépubliée", motif)
    _journal(db, "depubliee", acces, ressource, ip, motif=motif)
