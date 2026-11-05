"""Helpers partagés par les deux seeds : comptes de développement (base locale) et comptes de test
(préproduction).

Un compte de test se prépare toujours pareil : compte actif et mot de passe neuf, profil lié au rôle,
points de bienvenue, double authentification si le rôle est sensible. Les seeds ne font que choisir les
identifiants, les profils et l'établissement.

Ces helpers ne servent qu'aux seeds : jamais depuis une route de l'API.
"""

import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pyotp
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import DROITS_DES_ROLES, SENSIBLES, RoleDepart
from app.admin.double_auth import regenerer_codes_secours
from app.admin.models import Collaborateur, DoubleAuth, Permission
from app.comptes.models import Role, Session, StatutCompte, Utilisateur
from app.comptes.motdepasse import hacher
from app.config import settings
from app.eleves import pseudonyme
from app.eleves.models import Classe, Eleve
from app.encadreurs.models import Encadreur, EtatVerification, Fonction
from app.points import service as points
from app.points.bareme import BIENVENUE_ELEVE, BIENVENUE_ENCADREUR
from app.points.models import Semestre

DUREE_SEMESTRE = timedelta(days=180)


def mot_de_passe_aleatoire() -> str:
    """Un mot de passe à usage unique : chaque lancement du seed en change."""
    return secrets.token_urlsafe(15)


async def preparer_semestre(db: AsyncSession) -> None:
    """Un semestre en cours, pour que les points de démonstration comptent au semestre. Rien si un semestre
    occupe déjà la période."""
    debut = points.aujourd_hui()
    fin = debut + DUREE_SEMESTRE
    if await db.scalar(select(Semestre.id).where(Semestre.debut <= fin, Semestre.fin >= debut)):
        return
    db.add(Semestre(libelle=f"Semestre de démonstration {debut.year}", debut=debut, fin=fin))
    await db.flush()


async def preparer_compte(
    db: AsyncSession,
    identifiant: str,
    prenom: str,
    nom: str,
    role: Role,
    mot_de_passe: str,
    email: str | None = None,
) -> Utilisateur:
    """Crée le compte, ou le remet actif avec un nouveau mot de passe (et l'e-mail donné, s'il y en a un) ;
    ses anciennes sessions sont coupées."""
    utilisateur = await db.scalar(select(Utilisateur).where(Utilisateur.identifiant == identifiant))
    if utilisateur is None:
        utilisateur = Utilisateur(
            identifiant=identifiant, role=role, email=email, prenom=prenom, nom=nom, mot_de_passe_hash=""
        )
        db.add(utilisateur)
    elif email is not None:
        utilisateur.email = email
    utilisateur.mot_de_passe_hash = await hacher(mot_de_passe)
    utilisateur.statut = StatutCompte.actif
    await db.flush()
    await db.execute(delete(Session).where(Session.utilisateur_id == utilisateur.id))
    return utilisateur


async def preparer_collaborateur(
    db: AsyncSession, utilisateur: Utilisateur, role_depart: RoleDepart | None, dre: str | None
) -> bool:
    """Profil et droits du préréglage. Renvoie True si le compte a des droits sensibles."""
    collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == utilisateur.id))
    if collaborateur is None:
        collaborateur = Collaborateur(
            utilisateur_id=utilisateur.id, email=utilisateur.email or "", prenom=utilisateur.prenom, nom=utilisateur.nom
        )  # fmt: skip
        db.add(collaborateur)
    collaborateur.super_admin = role_depart is None
    collaborateur.role_depart = role_depart
    collaborateur.perimetre_dre = dre
    collaborateur.fin_acces = None
    collaborateur.revu_le = datetime.now(UTC)
    await db.flush()
    await db.execute(delete(Permission).where(Permission.collaborateur_id == collaborateur.id))
    droits = DROITS_DES_ROLES[role_depart] if role_depart else set()
    for module, action in droits:
        db.add(Permission(collaborateur_id=collaborateur.id, module=module, action=action))
    return collaborateur.super_admin or bool(droits & SENSIBLES)


async def activer_double_auth(db: AsyncSession, utilisateur: Utilisateur) -> tuple[str, list[str]]:
    """Double authentification active d'office : le secret et les codes de secours sont rendus à l'opérateur."""
    secret = pyotp.random_base32()
    await db.execute(delete(DoubleAuth).where(DoubleAuth.utilisateur_id == utilisateur.id))
    db.add(
        DoubleAuth(
            utilisateur_id=utilisateur.id,
            secret_chiffre=settings.fernet().encrypt(secret.encode()).decode(),
            active_le=datetime.now(UTC),
        )
    )
    return secret, await regenerer_codes_secours(db, utilisateur)


async def preparer_eleve(
    db: AsyncSession, utilisateur: Utilisateur, affiche: str, classe: Classe, etablissement_id: UUID
) -> None:
    """Profil élève et points de bienvenue. Relancé : ni second profil, ni second crédit."""
    if await db.get(Eleve, utilisateur.id) is None:
        db.add(
            Eleve(
                utilisateur_id=utilisateur.id,
                pseudonyme=affiche,
                pseudonyme_normalise=pseudonyme.cle(affiche),
                classe=classe,
                etablissement_id=etablissement_id,
                charte_version=settings.version_charte,
            )
        )  # fmt: skip
        utilisateur.consentement_le = datetime.now(UTC)
        await db.flush()
    await points.crediter(db, BIENVENUE_ELEVE, utilisateur.id, f"bienvenue:{utilisateur.id}")


async def preparer_encadreur(
    db: AsyncSession,
    utilisateur: Utilisateur,
    fonction: Fonction,
    etablissement_id: UUID,
    etat: EtatVerification,
) -> None:
    """Profil encadreur ; points de bienvenue seulement s'il est actif. Relancé : ni second profil, ni second crédit."""
    if await db.get(Encadreur, utilisateur.id) is None:
        actif = etat is EtatVerification.actif
        db.add(
            Encadreur(
                utilisateur_id=utilisateur.id,
                etablissement_id=etablissement_id,
                fonction=fonction,
                etat=etat,
                demande_le=datetime.now(UTC),
                decide_le=datetime.now(UTC) if actif else None,
                charte_version=settings.version_charte,
            )
        )  # fmt: skip
        utilisateur.consentement_le = datetime.now(UTC)
        await db.flush()
    if etat is EtatVerification.actif:
        await points.crediter(db, BIENVENUE_ENCADREUR, utilisateur.id, f"bienvenue:{utilisateur.id}")


def ecrire_fichier(acces: list[dict[str, str]], chemin: Path, entete: list[str]) -> None:
    """Les accès dans un fichier privé (600) : les mots de passe ne passent jamais par l'historique du terminal."""
    lignes = [*entete, ""]
    for ligne in acces:
        lignes.append(
            f"[{ligne['identifiant']}] {ligne['profil']}" + (f" · {ligne['perimetre']}" if "perimetre" in ligne else "")
        )
        lignes.append(f"  identifiant    : {ligne['identifiant']}")
        if "email" in ligne:
            lignes.append(f"  e-mail         : {ligne['email']}")
        lignes.append(f"  mot de passe   : {ligne['mot_de_passe']}")
        if "secret_totp" in ligne:
            lignes.append(f"  secret 2FA     : {ligne['secret_totp']}")
            lignes.append(f"  codes secours  : {ligne['codes_secours']}")
        lignes.append("")
    chemin.write_text("\n".join(lignes), encoding="utf-8")
    chemin.chmod(0o600)
