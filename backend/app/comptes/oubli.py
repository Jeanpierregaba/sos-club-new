"""« Mot de passe oublié » par e-mail (spec 039).

Un lien n'est envoyé qu'à une adresse fiable : un visiteur dont l'adresse est confirmée par code (spec 030), ou un
encadreur activé par l'équipe. Jamais à un élève (adresse facultative, non vérifiée), à un collaborateur de l'admin
ou à un compte suspendu. La réponse est la même dans tous les cas. Le jeton n'est gardé qu'en empreinte ; le lien
sert une fois, pendant 30 minutes, et un lien plus récent annule le précédent.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.comptes.models import LienMotDePasse, Role, StatutCompte, TentativeConnexion, Utilisateur
from app.comptes.motdepasse import hacher
from app.comptes.service import (
    LONGUEUR_MAX_MOT_DE_PASSE,
    LONGUEUR_MIN_MOT_DE_PASSE,
    CompteInvalide,
    TropDEssais,
    couper_sessions,
    empreinte,
)
from app.config import settings
from app.courriel import messages
from app.courriel.envoi import EnvoiImpossible, envoyer
from app.courriel.gabarit import Courriel
from app.encadreurs.models import Encadreur, EtatVerification

logger = logging.getLogger(__name__)

DUREE = timedelta(minutes=30)
PAR_HEURE = 3
CONSERVATION = timedelta(days=7)


class LienInvalide(Exception):
    """Lien inconnu, expiré, déjà utilisé, remplacé, ou compte devenu inéligible."""


@dataclass(frozen=True)
class Envoi:
    destinataire: str
    courriel: Courriel


async def eligible(db: AsyncSession, utilisateur: Utilisateur) -> bool:
    if utilisateur.statut is not StatutCompte.actif or not utilisateur.email:
        return False
    if utilisateur.role is Role.visiteur:
        return utilisateur.email_confirme_le is not None
    if utilisateur.role is Role.encadreur:
        encadreur = await db.get(Encadreur, utilisateur.id)
        return encadreur is not None and encadreur.etat is EtatVerification.actif
    return False


async def _limiter_adresse(db: AsyncSession, adresse_ip: str) -> None:
    """Une limite propre aux demandes de lien, par adresse IP : une école derrière une seule adresse garde de la
    marge, et les connexions ne sont pas touchées. La clé est en majuscules : aucune saisie d'identifiant, toujours
    mise en minuscules, ne peut la produire pour bloquer une adresse à distance."""
    cle = empreinte(f"OUBLI:{adresse_ip}")
    # Adresse préfixée et essai « en cours » : ces lignes ne comptent jamais parmi les échecs de connexion.
    db.add(TentativeConnexion(cle_hash=cle, adresse_ip=f"oubli:{adresse_ip}"[:45]))
    await db.commit()
    debut = datetime.now(UTC) - timedelta(minutes=settings.fenetre_essais_minutes)
    nombre = await db.scalar(
        select(func.count())
        .select_from(TentativeConnexion)
        .where(TentativeConnexion.cle_hash == cle, TentativeConnexion.cree_le > debut)
    )
    if (nombre or 0) > settings.oubli_max_adresse:
        raise TropDEssais


async def demander(db: AsyncSession, email: str, adresse_ip: str) -> Envoi | None:
    """Prépare le lien si l'adresse est fiable ; sinon ne fait rien. L'appelant répond toujours la même chose et
    envoie l'e-mail après la réponse."""
    await _limiter_adresse(db, adresse_ip)
    maintenant = datetime.now(UTC)
    try:
        adresse = validate_email(email.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        return None
    await db.execute(delete(LienMotDePasse).where(LienMotDePasse.cree_le < maintenant - CONSERVATION))
    utilisateur = await db.scalar(select(Utilisateur).where(Utilisateur.email == adresse).with_for_update())
    if utilisateur is None or not await eligible(db, utilisateur):
        await db.commit()
        return None
    recents = await db.scalar(
        select(func.count())
        .select_from(LienMotDePasse)
        .where(
            LienMotDePasse.utilisateur_id == utilisateur.id, LienMotDePasse.cree_le > maintenant - timedelta(hours=1)
        )
    )
    if (recents or 0) >= PAR_HEURE:
        await db.commit()
        return None
    await db.execute(
        update(LienMotDePasse)
        .where(
            LienMotDePasse.utilisateur_id == utilisateur.id,
            LienMotDePasse.utilise_le.is_(None),
            LienMotDePasse.remplace_le.is_(None),
        )
        .values(remplace_le=maintenant)
    )
    jeton = secrets.token_urlsafe(32)
    db.add(
        LienMotDePasse(
            utilisateur_id=utilisateur.id, jeton_hash=empreinte(jeton), cree_le=maintenant, expire_le=maintenant + DUREE
        )
    )
    journaliser(
        db, "lien_mot_de_passe_envoye", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        adresse_ip=adresse_ip,
    )  # fmt: skip
    await db.commit()
    lien = f"{settings.site_origine.rstrip('/')}/mot-de-passe/nouveau?jeton={jeton}"
    minutes = int(DUREE.total_seconds() // 60)
    return Envoi(utilisateur.email or "", messages.lien_mot_de_passe(utilisateur.prenom, lien, minutes))


async def expedier(envoi: Envoi) -> None:
    """Après la réponse : un échec ne change rien pour la personne, qui peut réessayer. Rien de personnel au log."""
    try:
        await envoyer(envoi.destinataire, envoi.courriel.sujet, envoi.courriel.texte, envoi.courriel.html)
    except EnvoiImpossible:
        logger.error("Le lien « mot de passe oublié » n'a pas pu partir.")


async def _lien(db: AsyncSession, jeton: str, *, verrouiller: bool = False) -> tuple[LienMotDePasse, Utilisateur]:
    requete = select(LienMotDePasse).where(LienMotDePasse.jeton_hash == empreinte(jeton))
    lien = await db.scalar(requete.with_for_update() if verrouiller else requete)
    if (
        lien is None
        or lien.utilise_le is not None
        or lien.remplace_le is not None
        or lien.expire_le <= datetime.now(UTC)
    ):
        raise LienInvalide
    utilisateur = await db.get(Utilisateur, lien.utilisateur_id, with_for_update=verrouiller)
    if utilisateur is None or not await eligible(db, utilisateur):
        raise LienInvalide
    return lien, utilisateur


async def lien_valide(db: AsyncSession, jeton: str) -> bool:
    try:
        await _lien(db, jeton)
    except LienInvalide:
        return False
    return True


async def choisir(db: AsyncSession, jeton: str, nouveau: str, adresse_ip: str) -> None:
    if not LONGUEUR_MIN_MOT_DE_PASSE <= len(nouveau) <= LONGUEUR_MAX_MOT_DE_PASSE:
        raise CompteInvalide(f"Le mot de passe doit contenir au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères.")
    lien, utilisateur = await _lien(db, jeton, verrouiller=True)
    maintenant = datetime.now(UTC)
    utilisateur.mot_de_passe_hash = await hacher(nouveau)
    utilisateur.mot_de_passe_provisoire_le = None
    # Ouvrir le lien prouve que la personne lit cette adresse.
    utilisateur.email_confirme_le = utilisateur.email_confirme_le or maintenant
    lien.utilise_le = maintenant
    await couper_sessions(db, utilisateur.id)
    journaliser(
        db, "mot_de_passe_choisi", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        adresse_ip=adresse_ip,
    )  # fmt: skip
    await db.commit()
