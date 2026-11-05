"""Comptes de démonstration pour la base LOCALE : un par profil, pour tester l'espace admin et les rôles.

    cd backend && uv run python -m app.seed_dev

Chaque lancement crée les comptes `dev.*` manquants, leur donne de nouveaux mots de passe aléatoires et écrit
les accès dans `.comptes-dev.local` à la racine du projet (ignoré par git). Les comptes à droits sensibles ont
une double authentification déjà active : leur secret et leurs codes de secours sont dans le même fichier.
Refusé en production : aucune base réelle ne doit recevoir ces comptes (docs/RULES.md).
"""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import LIBELLES_ROLES, RoleDepart
from app.admin.journal import journaliser
from app.admin.models import DoubleAuth
from app.clubs.models import Club, ClubAxe, EtatClub
from app.comptes.models import Role, Utilisateur
from app.config import RACINE_PROJET, settings
from app.db import SessionLocal, engine
from app.eleves.models import Classe, Eleve
from app.encadreurs.models import EtatVerification, Fonction
from app.referentiel.models import Etablissement, Iesg, StatutEtablissement
from app.seed_commun import (
    activer_double_auth,
    mot_de_passe_aleatoire,
    preparer_collaborateur,
    preparer_compte,
    preparer_eleve,
    preparer_encadreur,
    preparer_semestre,
)
from app.seed_commun import (
    ecrire_fichier as ecrire_acces,
)

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
    ("dev.encadreur.attente", "Yao", "Attente", Role.encadreur, "", None),
    ("dev.eleve1", "Ama", "Eleve", Role.eleve, "", None),
    ("dev.eleve2", "Kofi", "Eleve", Role.eleve, "", None),
]

# Profils des élèves (spec 017) : pseudonyme, classe, établissement.
PROFILS_ELEVES = {
    "dev.eleve1": ("Ama du Golfe", Classe.seconde, "Lycée de Tokoin I"),
    "dev.eleve2": ("Kofi Curieux", Classe.troisieme, "Lycée Tokoin Est"),
}
# Profils des encadreurs (spec 018) : fonction, DRE de l'établissement, état. Celui en attente est dans la DRE de
# dev.clubs.kara, pour montrer la file vue d'une DRE.
PROFILS_ENCADREURS = {
    "dev.encadreur": (Fonction.enseignant, "grand-lome", EtatVerification.actif),
    "dev.encadreur.attente": (Fonction.sante, "kara", EtatVerification.en_attente),
}

ENTETE = [
    "# Comptes de développement — base LOCALE uniquement (créés par `python -m app.seed_dev`).",
    "# Ce fichier est ignoré par git. Chaque lancement du seed change les mots de passe.",
    "# Double authentification : ajoute le secret dans ton application (saisie manuelle de la clé),",
    "# ou utilise un code de secours (chacun ne sert qu'une fois).",
    "# Connexion sur /connexion avec l'identifiant ou l'e-mail, puis le mot de passe.",
]


class ProductionRefusee(Exception):
    pass


async def _etablissement_eleve(db: AsyncSession, nom_etablissement: str) -> UUID | None:
    """L'établissement demandé s'il est actif ; sinon le premier actif par ordre alphabétique."""
    actifs = select(Etablissement.id).where(Etablissement.statut == StatutEtablissement.actif)
    return await db.scalar(actifs.where(Etablissement.nom == nom_etablissement)) or await db.scalar(
        actifs.order_by(Etablissement.nom_normalise).limit(1)
    )


async def _etablissement_dre(db: AsyncSession, dre: str) -> UUID | None:
    """Le premier établissement actif de la DRE, par ordre alphabétique."""
    return await db.scalar(
        select(Etablissement.id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .where(Etablissement.statut == StatutEtablissement.actif, Iesg.dre_code == dre)
        .order_by(Etablissement.nom_normalise)
        .limit(1)
    )


async def _preparer_clubs(db: AsyncSession) -> None:
    """Un club actif pour l'élève 1 et une demande en attente pour l'élève 2 (spec 019), une seule fois."""
    if await db.scalar(select(Club.id)):
        return
    eleve1 = await db.get(
        Eleve, (await db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == "dev.eleve1")))
    )
    eleve2 = await db.get(
        Eleve, (await db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == "dev.eleve2")))
    )
    if eleve1 is None or eleve2 is None:
        return
    actif = Club(
        etablissement_id=eleve1.etablissement_id,
        nom="Club Santé Tokoin",
        nom_normalise="club sante tokoin",
        description="Le club de démonstration, animé par les élèves du lycée.",
        demandeur_id=eleve1.utilisateur_id,
        president_id=eleve1.utilisateur_id,
        etat=EtatClub.actif,
        decide_le=datetime.now(UTC),
        actif_le=datetime.now(UTC),
        encadreurs_associes=[{"nom": "M. Kodjo", "email": "kodjo@exemple.tg"}],
    )
    attente = Club(
        etablissement_id=eleve2.etablissement_id,
        nom="Club Santé Tokoin Est",
        nom_normalise="club sante tokoin est",
        demandeur_id=eleve2.utilisateur_id,
        etat=EtatClub.en_attente,
        encadreurs_associes=[{"nom": "Mme Afi"}],
    )
    db.add_all([actif, attente])
    await db.flush()
    db.add_all(
        [
            ClubAxe(club_id=actif.id, axe_code="sante-environnement"),
            ClubAxe(club_id=actif.id, axe_code="sport-secourisme"),
            ClubAxe(club_id=attente.id, axe_code="sante-sexuelle-evss"),
        ]
    )


async def semer(db: AsyncSession) -> list[dict[str, str]]:
    """Prépare tous les comptes `dev.*` et renvoie leurs accès. Valide la transaction."""
    if settings.production:
        raise ProductionRefusee
    acces: list[dict[str, str]] = []
    await preparer_semestre(db)
    for identifiant, prenom, nom, role, role_depart, dre in COMPTES:
        mot_de_passe = mot_de_passe_aleatoire()
        email = None if role is Role.eleve else f"{identifiant}@{DOMAINE}"
        utilisateur = await preparer_compte(db, identifiant, prenom, nom, role, mot_de_passe, email)
        ligne = {"identifiant": identifiant, "mot_de_passe": mot_de_passe}
        if utilisateur.email:
            ligne["email"] = utilisateur.email
        if role is Role.admin:
            depart = role_depart if isinstance(role_depart, RoleDepart) else None
            sensible = await preparer_collaborateur(db, utilisateur, depart, dre)
            ligne["profil"] = LIBELLES_ROLES[depart] if depart else "Super-administrateur"
            ligne["perimetre"] = f"DRE {dre}" if dre else "National"
            if sensible:
                secret, codes = await activer_double_auth(db, utilisateur)
                ligne["secret_totp"] = secret
                ligne["codes_secours"] = ", ".join(codes)
            else:
                await db.execute(delete(DoubleAuth).where(DoubleAuth.utilisateur_id == utilisateur.id))
        else:
            ligne["profil"] = "Encadreur" if role is Role.encadreur else "Élève"
            if role is Role.eleve:
                affiche, classe, nom_etablissement = PROFILS_ELEVES[identifiant]
                etablissement_id = await _etablissement_eleve(db, nom_etablissement)
                if etablissement_id is not None:
                    await preparer_eleve(db, utilisateur, affiche, classe, etablissement_id)
            else:
                fonction, dre_etablissement, etat = PROFILS_ENCADREURS[identifiant]
                etablissement_id = await _etablissement_dre(db, dre_etablissement)
                if etablissement_id is not None:
                    await preparer_encadreur(db, utilisateur, fonction, etablissement_id, etat)
                ligne["profil"] += " (actif)" if etat is EtatVerification.actif else " (en attente)"
        acces.append(ligne)
    await _preparer_clubs(db)
    journaliser(db, "comptes_de_developpement_prepares", details={"comptes": [c[0] for c in COMPTES]})
    await db.commit()
    return acces


def ecrire_fichier(acces: list[dict[str, str]], chemin: Path = FICHIER_ACCES) -> None:
    ecrire_acces(acces, chemin, ENTETE)


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
