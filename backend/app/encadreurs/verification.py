"""Vérification des encadreurs par l'espace admin (spec 018) : la file, l'activation et le refus.

Un collaborateur national voit toutes les demandes. Un collaborateur de DRE ne voit et ne décide que celles des
établissements de sa DRE : pour les autres, il reçoit la même réponse que pour une demande inexistante. Le
périmètre se lit sur l'établissement actuel du profil, sous verrou, au moment de la décision.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.comptes.inscription import Refus
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.courriel import envoi as courriel
from app.courriel import messages
from app.courriel.gabarit import Courriel
from app.encadreurs.models import Encadreur, EtatVerification
from app.encadreurs.schemas import DemandeEncadreur, FileEncadreurs
from app.points import service as points
from app.points.bareme import BIENVENUE_ENCADREUR
from app.referentiel.models import Dre, Etablissement, Iesg
from app.referentiel.schemas import EtablissementRattache

logger = logging.getLogger(__name__)

LIMITE_FILE = 200
LIBELLES_ETATS = {
    EtatVerification.en_attente: "en attente",
    EtatVerification.actif: "activée",
    EtatVerification.refuse: "refusée",
}


class Introuvable(Exception):
    pass


def _requete(acces: Acces) -> Select[tuple[Encadreur, Utilisateur, Etablissement, Iesg, Dre]]:
    requete = (
        select(Encadreur, Utilisateur, Etablissement, Iesg, Dre)
        .join(Utilisateur, Utilisateur.id == Encadreur.utilisateur_id)
        .join(Etablissement, Etablissement.id == Encadreur.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .where(Utilisateur.role == Role.encadreur)
    )
    if not acces.national:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    return requete


def _demande(
    encadreur: Encadreur, utilisateur: Utilisateur, etablissement: Etablissement, iesg: Iesg, dre: Dre
) -> DemandeEncadreur:
    return DemandeEncadreur(
        id=utilisateur.id,
        identifiant=utilisateur.identifiant,
        prenom=utilisateur.prenom,
        nom=utilisateur.nom,
        email=utilisateur.email,
        telephone=utilisateur.telephone,
        fonction=encadreur.fonction,
        fonction_precision=encadreur.fonction_precision,
        etablissement=EtablissementRattache(
            id=etablissement.id,
            nom=etablissement.nom,
            statut=etablissement.statut,
            iesg=iesg.nom,
            dre_code=dre.code,
            dre=dre.nom,
        ),
        etat=encadreur.etat,
        demande_le=encadreur.demande_le,
        decide_le=encadreur.decide_le,
        motif_refus=encadreur.motif_refus,
        version=encadreur.version,
    )


async def file_attente(db: AsyncSession, acces: Acces, etat: EtatVerification) -> FileEncadreurs:
    """Seulement les demandes en attente ou refusées : la file n'est pas un annuaire des encadreurs actifs, que
    seul le niveau national consulte, par les inscrits (ADR-0008)."""
    assert etat is not EtatVerification.actif
    requete = _requete(acces).where(Encadreur.etat == etat)
    total = await db.scalar(
        select(func.count()).select_from(requete.with_only_columns(Encadreur.utilisateur_id).subquery())
    )
    # Les refusés les plus récents d'abord ; les demandes en attente dans l'ordre d'arrivée.
    ordre = Encadreur.demande_le.asc() if etat is EtatVerification.en_attente else Encadreur.decide_le.desc()
    lignes = (await db.execute(requete.order_by(ordre, Encadreur.utilisateur_id).limit(LIMITE_FILE))).all()
    return FileEncadreurs(total=total or 0, demandes=[_demande(*ligne) for ligne in lignes])


async def compter_en_attente(db: AsyncSession, acces: Acces) -> int:
    requete = _requete(acces).where(Encadreur.etat == EtatVerification.en_attente)
    return (
        await db.scalar(
            select(func.count()).select_from(requete.with_only_columns(Encadreur.utilisateur_id).subquery())
        )
        or 0
    )


Ligne = tuple[Encadreur, Utilisateur, Etablissement, Iesg, Dre]


async def _a_decider(db: AsyncSession, acces: Acces, utilisateur_id: UUID, version: int | None = None) -> Ligne:
    """La demande, verrouillée : deux décisions simultanées passent l'une après l'autre. Le périmètre se lit sur
    l'établissement actuel : un changement d'établissement concurrent fait sortir la demande du périmètre."""
    ligne = (
        await db.execute(
            _requete(acces)
            .where(Encadreur.utilisateur_id == utilisateur_id)
            .with_for_update(of=[Encadreur, Utilisateur])
        )
    ).one_or_none()
    if ligne is None:
        raise Introuvable
    encadreur = ligne[0]
    if encadreur.etat is not EtatVerification.en_attente:
        raise Refus(f"Cette demande a déjà été traitée : elle est {LIBELLES_ETATS[encadreur.etat]}.", 409)
    if version is not None and version != encadreur.version:
        raise Refus("Ce profil a été modifié depuis que tu l'as ouvert : recharge la page et vérifie-le.", 409)
    return tuple(ligne)


async def _prevenir(utilisateur: Utilisateur, message: Courriel) -> None:
    """Après la validation : un e-mail qui ne part pas ne défait pas la décision."""
    if not utilisateur.email:
        return
    try:
        await courriel.envoyer(utilisateur.email, message.sujet, message.texte, html=message.html)
    except courriel.EnvoiImpossible:
        logger.warning("Avis de vérification non envoyé à l'encadreur %s", utilisateur.id)
    except Exception:
        # La décision est validée : un e-mail qui ne part pas ne doit pas se traduire par une erreur 500.
        logger.exception("Avis de vérification en échec pour l'encadreur %s", utilisateur.id)


async def activer(
    db: AsyncSession, acces: Acces, utilisateur_id: UUID, ip: str, version: int | None = None
) -> DemandeEncadreur:
    """`version` : celle du profil que le collaborateur a vérifié. Le site l'envoie toujours."""
    ligne = await _a_decider(db, acces, utilisateur_id, version)
    encadreur, utilisateur, _, _, dre = ligne
    if utilisateur.statut is not StatutCompte.actif:
        raise Refus("Ce compte est suspendu : réactive-le d'abord depuis sa fiche.", 409)
    encadreur.etat = EtatVerification.actif
    encadreur.decide_le = datetime.now(UTC)
    encadreur.decide_par = acces.utilisateur.id
    # Même clé que pour un élève : la bienvenue ne se gagne qu'une fois par compte, quoi qu'il arrive ensuite.
    await points.crediter(
        db, BIENVENUE_ENCADREUR, utilisateur.id, f"bienvenue:{utilisateur.id}", valide_par=acces.utilisateur.id
    )
    journaliser(
        db, "encadreur_active", acces.utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        perimetre=dre.code, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    await _prevenir(utilisateur, messages.encadreur_active(utilisateur.prenom))
    return _demande(*ligne)


async def refuser(
    db: AsyncSession, acces: Acces, utilisateur_id: UUID, motif: str, ip: str, version: int | None = None
) -> DemandeEncadreur:
    ligne = await _a_decider(db, acces, utilisateur_id, version)
    encadreur, utilisateur, _, _, dre = ligne
    encadreur.etat = EtatVerification.refuse
    encadreur.motif_refus = motif
    encadreur.decide_le = datetime.now(UTC)
    encadreur.decide_par = acces.utilisateur.id
    journaliser(
        db, "encadreur_refuse", acces.utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        perimetre=dre.code, details={"motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    await _prevenir(utilisateur, messages.encadreur_refuse(utilisateur.prenom, motif))
    return _demande(*ligne)
