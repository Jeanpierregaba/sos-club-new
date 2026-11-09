"""Inscription, confirmation et espace du visiteur (spec 030).

Le compte est créé non confirmé ; il ne s'ouvre qu'avec le code reçu par e-mail. Un compte jamais confirmé est
effacé au bout de 7 jours, ce qui libère l'adresse.
"""

import asyncio
import contextlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.comptes.inscription import InscriptionsFermees, Refus, flush, limiter
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.comptes.service import CompteInvalide, DejaPris, normaliser, preparer_utilisateur
from app.config import settings
from app.courriel import envoi
from app.db import SessionLocal
from app.visiteurs import codes
from app.visiteurs.models import Visiteur
from app.visiteurs.schemas import CodeEnvoye, EspaceVisiteur, InscriptionVisiteur

logger = logging.getLogger(__name__)

CONSERVATION_NON_CONFIRMES = timedelta(days=7)
CODE_INCORRECT = "Ce code est incorrect ou expiré. Vérifie-le, ou demande un nouveau code."


class ServiceIndisponible(Exception):
    """En production, sans SMTP ou si l'e-mail ne part pas : aucun compte n'est créé."""


class PasUnVisiteur(Exception):
    pass


def _non_confirmes_perimes(maintenant: datetime) -> list[object]:
    return [
        Utilisateur.role == Role.visiteur,
        Utilisateur.email_confirme_le.is_(None),
        Utilisateur.cree_le < maintenant - CONSERVATION_NON_CONFIRMES,
    ]


async def inscrire(db: AsyncSession, entree: InscriptionVisiteur, adresse_ip: str) -> CodeEnvoye:
    """Crée le compte et envoie le code, dans la même transaction : si l'e-mail ne part pas, rien n'est créé."""
    if not settings.inscriptions_actives:
        raise InscriptionsFermees
    if settings.production and not envoi.smtp_configure():
        raise ServiceIndisponible
    await limiter(db, adresse_ip)

    # Un ancien compte jamais confirmé ne bloque plus l'adresse.
    email = normaliser(entree.email)
    await db.execute(delete(Utilisateur).where(Utilisateur.email == email, *_non_confirmes_perimes(datetime.now(UTC))))
    try:
        utilisateur = await preparer_utilisateur(
            db, Role.visiteur, f"v.{secrets.token_hex(6)}", entree.prenom, entree.nom, entree.mot_de_passe,
            entree.email, entree.telephone,
        )  # fmt: skip
    except DejaPris as erreur:
        raise Refus(str(erreur), 409) from None
    except CompteInvalide as erreur:
        raise Refus(str(erreur)) from None
    utilisateur.consentement_le = datetime.now(UTC)
    await flush(db)
    db.add(
        Visiteur(
            utilisateur_id=utilisateur.id, ville=entree.ville, region=entree.region, sexe=entree.sexe,
            statut=entree.statut, charte_version=settings.version_charte,
        )
    )  # fmt: skip
    await flush(db)
    try:
        code_de_test = await codes.envoyer(db, utilisateur)
    except envoi.EnvoiImpossible:
        await db.rollback()
        raise ServiceIndisponible from None
    journaliser(db, "inscription_visiteur", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
                adresse_ip=adresse_ip)  # fmt: skip
    await db.commit()
    assert utilisateur.email
    return CodeEnvoye(email=utilisateur.email, code_de_test=code_de_test)


async def _a_confirmer(db: AsyncSession, email: str) -> Utilisateur | None:
    return await db.scalar(
        select(Utilisateur).where(
            Utilisateur.email == normaliser(email),
            Utilisateur.role == Role.visiteur,
            Utilisateur.email_confirme_le.is_(None),
            Utilisateur.statut == StatutCompte.actif,
        )
    )


async def confirmer(db: AsyncSession, email: str, code: str, adresse_ip: str) -> Utilisateur:
    """Le bon code confirme l'adresse ; l'appelant ouvre alors la session (qui valide la transaction)."""
    utilisateur = await _a_confirmer(db, email)
    if not await codes.verifier_code(db, utilisateur, code):
        await db.commit()
        raise Refus(CODE_INCORRECT, 400)
    assert utilisateur is not None
    utilisateur.email_confirme_le = datetime.now(UTC)
    journaliser(db, "email_confirme", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
                adresse_ip=adresse_ip)  # fmt: skip
    return utilisateur


async def renvoyer(db: AsyncSession, email: str) -> str | None:
    """Envoie un nouveau code si l'adresse attend une confirmation. Ne dit jamais si elle existe : les limites et
    les échecs d'envoi sont tus. Renvoie le code de test, s'il y a lieu."""
    utilisateur = await _a_confirmer(db, email)
    if utilisateur is None:
        return None
    try:
        code_de_test = await codes.envoyer(db, utilisateur)
    except codes.TropTot, codes.TropDeCodes, envoi.EnvoiImpossible:
        await db.rollback()
        return None
    await db.commit()
    return code_de_test


async def code_a_la_connexion(db: AsyncSession, utilisateur: Utilisateur) -> str | None:
    """Bon mot de passe, adresse non confirmée : un nouveau code part, si les limites le permettent."""
    try:
        code_de_test = await codes.envoyer(db, utilisateur)
    except codes.TropTot, codes.TropDeCodes, envoi.EnvoiImpossible:
        await db.rollback()
        return None
    await db.commit()
    return code_de_test


async def espace(db: AsyncSession, utilisateur: Utilisateur) -> EspaceVisiteur:
    visiteur = await db.get(Visiteur, utilisateur.id) if utilisateur.role is Role.visiteur else None
    if visiteur is None or utilisateur.email is None:
        raise PasUnVisiteur
    return EspaceVisiteur(
        prenom=utilisateur.prenom, nom=utilisateur.nom, email=utilisateur.email, telephone=utilisateur.telephone,
        ville=visiteur.ville, region=visiteur.region, sexe=visiteur.sexe, statut=visiteur.statut,
    )  # fmt: skip


# Purge ------------------------------------------------------------------------------------------------------


async def purger_non_confirmes(db: AsyncSession) -> int:
    """Efface les comptes visiteurs jamais confirmés depuis plus de 7 jours (profil et code partent en cascade)."""
    resultat = await db.execute(delete(Utilisateur).where(*_non_confirmes_perimes(datetime.now(UTC))))
    await db.commit()
    return int(getattr(resultat, "rowcount", 0) or 0)


async def purger_regulierement() -> None:
    """Une fois au démarrage, puis toutes les heures."""
    while True:
        with contextlib.suppress(SQLAlchemyError, OSError):
            async with SessionLocal() as db:
                nombre = await purger_non_confirmes(db)
                if nombre:
                    logger.info("%s compte(s) visiteur non confirmé(s) effacé(s).", nombre)
        await asyncio.sleep(3600)
