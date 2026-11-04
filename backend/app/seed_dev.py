"""Comptes de démonstration pour la base LOCALE : un par profil, pour tester l'espace admin et les rôles.

    cd backend && uv run python -m app.seed_dev

Chaque lancement crée les comptes `dev.*` manquants, leur donne de nouveaux mots de passe aléatoires et écrit
les accès dans `.comptes-dev.local` à la racine du projet (ignoré par git). Les comptes à droits sensibles ont
une double authentification déjà active : leur secret et leurs codes de secours sont dans le même fichier.
Refusé en production : aucune base réelle ne doit recevoir ces comptes (docs/RULES.md).
"""

import asyncio
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

import pyotp
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import DROITS_DES_ROLES, LIBELLES_ROLES, SENSIBLES, RoleDepart
from app.admin.double_auth import regenerer_codes_secours
from app.admin.journal import journaliser
from app.admin.models import Collaborateur, DoubleAuth, Permission
from app.comptes.models import Role, Session, StatutCompte, Utilisateur
from app.comptes.motdepasse import hacher
from app.config import RACINE_PROJET, settings
from app.db import SessionLocal, engine

FICHIER_ACCES = RACINE_PROJET / ".comptes-dev.local"
DOMAINE = "exemple.tg"

# identifiant, prénom, nom, rôle de compte, rôle de collaborateur (None : super-administrateur), DRE
COMPTES: list[tuple[str, str, str, Role, RoleDepart | None | str, str | None]] = [
    ("dev.superadmin", "Sena", "Superadmin", Role.admin, None, None),
    ("dev.national", "Kossi", "National", Role.admin, RoleDepart.admin_national, None),
    ("dev.moderateur", "Afi", "Moderatrice", Role.admin, RoleDepart.moderateur, None),
    ("dev.contenus", "Edem", "Contenus", Role.admin, RoleDepart.gestionnaire_contenus, None),
    ("dev.pedagogie", "Yawa", "Pedagogie", Role.admin, RoleDepart.gestionnaire_pedagogique, None),
    ("dev.clubs.kara", "Komla", "Clubs", Role.admin, RoleDepart.gestionnaire_clubs, "kara"),
    ("dev.agenda", "Ablavi", "Agenda", Role.admin, RoleDepart.gestionnaire_agenda, None),
    ("dev.analyste", "Mawuli", "Analyste", Role.admin, RoleDepart.analyste, None),
    ("dev.encadreur", "Kafui", "Encadreur", Role.encadreur, "", None),
    ("dev.eleve1", "Ama", "Eleve", Role.eleve, "", None),
    ("dev.eleve2", "Kofi", "Eleve", Role.eleve, "", None),
]


class ProductionRefusee(Exception):
    pass


def _mot_de_passe() -> str:
    return secrets.token_urlsafe(15)


async def _preparer_compte(
    db: AsyncSession, identifiant: str, prenom: str, nom: str, role: Role, mot_de_passe: str
) -> Utilisateur:
    """Crée le compte, ou le remet actif avec un nouveau mot de passe ; ses anciennes sessions sont coupées."""
    email = None if role is Role.eleve else f"{identifiant}@{DOMAINE}"
    utilisateur = await db.scalar(select(Utilisateur).where(Utilisateur.identifiant == identifiant))
    if utilisateur is None:
        utilisateur = Utilisateur(
            identifiant=identifiant, role=role, email=email, prenom=prenom, nom=nom, mot_de_passe_hash=""
        )
        db.add(utilisateur)
    utilisateur.mot_de_passe_hash = await hacher(mot_de_passe)
    utilisateur.statut = StatutCompte.actif
    await db.flush()
    await db.execute(delete(Session).where(Session.utilisateur_id == utilisateur.id))
    return utilisateur


async def _preparer_collaborateur(
    db: AsyncSession, utilisateur: Utilisateur, role_depart: RoleDepart | None, dre: str | None
) -> bool:
    """Profil et droits du préréglage. Renvoie True si le compte a des droits sensibles."""
    collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == utilisateur.id))
    if collaborateur is None:
        collaborateur = Collaborateur(
            utilisateur_id=utilisateur.id, email=utilisateur.email or "", prenom=utilisateur.prenom, nom=utilisateur.nom
        )
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


async def _activer_double_auth(db: AsyncSession, utilisateur: Utilisateur) -> tuple[str, list[str]]:
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


async def semer(db: AsyncSession) -> list[dict[str, str]]:
    """Prépare tous les comptes `dev.*` et renvoie leurs accès. Valide la transaction."""
    if settings.production:
        raise ProductionRefusee
    acces: list[dict[str, str]] = []
    for identifiant, prenom, nom, role, role_depart, dre in COMPTES:
        mot_de_passe = _mot_de_passe()
        utilisateur = await _preparer_compte(db, identifiant, prenom, nom, role, mot_de_passe)
        ligne = {"identifiant": identifiant, "mot_de_passe": mot_de_passe}
        if utilisateur.email:
            ligne["email"] = utilisateur.email
        if role is Role.admin:
            depart = role_depart if isinstance(role_depart, RoleDepart) else None
            sensible = await _preparer_collaborateur(db, utilisateur, depart, dre)
            ligne["profil"] = LIBELLES_ROLES[depart] if depart else "Super-administrateur"
            ligne["perimetre"] = f"DRE {dre}" if dre else "National"
            if sensible:
                secret, codes = await _activer_double_auth(db, utilisateur)
                ligne["secret_totp"] = secret
                ligne["codes_secours"] = ", ".join(codes)
            else:
                await db.execute(delete(DoubleAuth).where(DoubleAuth.utilisateur_id == utilisateur.id))
        else:
            ligne["profil"] = "Encadreur" if role is Role.encadreur else "Élève"
        acces.append(ligne)
    journaliser(db, "comptes_de_developpement_prepares", details={"comptes": [c[0] for c in COMPTES]})
    await db.commit()
    return acces


def ecrire_fichier(acces: list[dict[str, str]], chemin: Path = FICHIER_ACCES) -> None:
    lignes = [
        "# Comptes de développement — base LOCALE uniquement (créés par `python -m app.seed_dev`).",
        "# Ce fichier est ignoré par git. Chaque lancement du seed change les mots de passe.",
        "# Double authentification : ajoute le secret dans ton application (saisie manuelle de la clé),",
        "# ou utilise un code de secours (chacun ne sert qu'une fois).",
        "# Connexion sur /connexion avec l'identifiant ou l'e-mail, puis le mot de passe.",
        "",
    ]
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


async def _principal() -> list[dict[str, str]]:
    try:
        async with SessionLocal() as db:
            return await semer(db)
    finally:
        await engine.dispose()


def main() -> int:
    try:
        acces = asyncio.run(_principal())
    except ProductionRefusee:
        print("Refusé : ces comptes de démonstration ne vont jamais sur une base de production.", file=sys.stderr)
        return 1
    ecrire_fichier(acces)
    # Les mots de passe ne s'affichent pas : ils restent dans le fichier, hors de l'historique du terminal.
    print(f"{len(acces)} comptes prêts. Accès dans {FICHIER_ACCES.name} (racine du projet, ignoré par git).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
