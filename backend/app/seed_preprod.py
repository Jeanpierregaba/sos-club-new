"""Comptes de test pour la PRÉPRODUCTION : un administrateur, un encadreur, deux élèves et un club.

    cd /opt/sosclub/preprod && docker compose exec -T api python -m app.seed_preprod

Ces comptes servent aux tests manuels sur la préproduction. Ce sont des données fictives, sans valeur
réelle : le seed est refusé partout ailleurs qu'en préproduction (docs/RULES.md), ni en local, ni en
production. Relancé, il change les mots de passe et coupe les sessions en cours.

Les accès sont écrits dans un fichier privé (par défaut `/tmp/comptes-preprod.txt`, dans le conteneur) :
les mots de passe ne passent jamais par l'historique du terminal.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs.adhesions import adhesion_president
from app.clubs.models import PASSATION_EN_ATTENTE, Club, ClubAxe, ClubPassation, EtatClub
from app.clubs.service import normaliser_nom
from app.comptes.models import Role, Utilisateur
from app.config import settings
from app.db import SessionLocal, engine
from app.eleves.models import Classe
from app.encadreurs.models import EtatVerification, Fonction
from app.referentiel.models import Axe, Etablissement, Iesg, StatutEtablissement
from app.seed_commun import (
    activer_double_auth,
    ecrire_fichier,
    mot_de_passe_aleatoire,
    preparer_collaborateur,
    preparer_compte,
    preparer_eleve,
    preparer_encadreur,
    preparer_semestre,
)

DOMAINE = "preprod.exemple.tg"
# Un établissement de la DRE de Lomé : les élèves et l'encadreur doivent être du même établissement pour
# qu'une affiliation et un rattachement au club de test soient possibles.
DRE = "grand-lome"
FICHIER_PAR_DEFAUT = Path("/tmp/comptes-preprod.txt")
NOM_CLUB = "Club Santé Préprod"

# identifiant, prénom, nom, rôle de compte, profil affiché
COMPTES: list[tuple[str, str, str, Role, str]] = [
    ("preprod.admin", "Sena", "Test", Role.admin, "Super-administrateur"),
    ("preprod.encadreur", "Kafui", "Test", Role.encadreur, "Encadreur (actif)"),
    ("preprod.eleve", "Koffi", "Test", Role.eleve, "Élève"),
    ("preprod.president", "Ama", "Test", Role.eleve, "Élève, président du club de test"),
]
# Profils des élèves : pseudonyme et classe.
PROFILS_ELEVES = {
    "preprod.eleve": ("Koffi Preprod", Classe.seconde),
    "preprod.president": ("Ama Preprod", Classe.terminale),
}

ENTETE = [
    "# Comptes de test — PRÉPRODUCTION uniquement (créés par `python -m app.seed_preprod`).",
    "# Données fictives : à supprimer quand les tests sont terminés.",
    "# Chaque lancement du seed change les mots de passe et coupe les sessions en cours.",
    "# Double authentification : ajoute le secret dans ton application (saisie manuelle de la clé),",
    "# ou utilise un code de secours (chacun ne sert qu'une fois).",
    "# Connexion sur /connexion avec l'identifiant ou l'e-mail, puis le mot de passe.",
]


class PreprodRefusee(Exception):
    """Le seed ne prépare de comptes que sur la préproduction."""


class PreparationImpossible(Exception):
    """La préproduction n'est pas dans un état qui permet de préparer les comptes (référentiel, club de test)."""


async def _etablissement(db: AsyncSession) -> UUID:
    """Le premier établissement actif de la DRE, par ordre alphabétique."""
    etablissement_id = await db.scalar(
        select(Etablissement.id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .where(Etablissement.statut == StatutEtablissement.actif, Iesg.dre_code == DRE)
        .order_by(Etablissement.nom_normalise)
        .limit(1)
    )
    if etablissement_id is None:
        raise PreparationImpossible(f"Aucun établissement actif dans la DRE {DRE}.")
    return etablissement_id


async def _preparer_club(db: AsyncSession, president: Utilisateur, etablissement_id: UUID) -> Club:
    """Le club de test, actif et présidé par l'élève `preprod.president`. Sans lui, aucune affiliation ni
    rattachement à essayer. Relancé, le seed le remet en état, même s'il a été refusé ou passé à un autre élève
    pendant les tests."""
    nom_normalise = normaliser_nom(NOM_CLUB)
    club = await db.scalar(
        select(Club).where(Club.etablissement_id == etablissement_id, Club.nom_normalise == nom_normalise)
    )
    # Un seul club actif par établissement : un club créé par un testeur bloquerait le club de test.
    autre_actif = select(Club.nom).where(Club.etablissement_id == etablissement_id, Club.etat == EtatClub.actif)
    if club is not None:
        autre_actif = autre_actif.where(Club.id != club.id)
    if (autre := await db.scalar(autre_actif)) is not None:
        raise PreparationImpossible(
            f"L'établissement de test a déjà un autre club actif (« {autre} ») : refuse-le ou retire-le d'abord."
        )
    if club is None:
        club = Club(
            etablissement_id=etablissement_id,
            nom=NOM_CLUB,
            nom_normalise=nom_normalise,
            description="Club de test de la préproduction.",
            demandeur_id=president.id,
            encadreurs_associes=[],
        )
        db.add(club)
    elif await db.scalar(
        select(ClubPassation.id).where(ClubPassation.club_id == club.id, ClubPassation.etat.in_(PASSATION_EN_ATTENTE))
    ):
        raise PreparationImpossible("Une passation du club de test est en attente : décide-la d'abord.")
    maintenant = datetime.now(UTC)
    if club.etat is not EtatClub.actif:
        club.decide_le = maintenant
        club.actif_le = maintenant
    club.etat = EtatClub.actif
    club.motif_refus = None
    club.president_id = president.id
    await db.flush()
    # Le président est membre de droit de son club (spec 020), même s'il l'avait quitté pendant les tests.
    await adhesion_president(db, club)
    if await db.scalar(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id)) is None:
        axes = list((await db.scalars(select(Axe.code).order_by(Axe.code).limit(2))).all())
        if not axes:
            raise PreparationImpossible("Aucun axe dans le référentiel : le club de test en demande au moins un.")
        for code in axes:
            db.add(ClubAxe(club_id=club.id, axe_code=code))
    return club


async def semer(db: AsyncSession) -> list[dict[str, str]]:
    """Prépare les comptes de test de la préproduction et renvoie leurs accès. Valide la transaction."""
    if settings.environnement != "preprod":
        raise PreprodRefusee
    etablissement_id = await _etablissement(db)
    await preparer_semestre(db)
    acces: list[dict[str, str]] = []
    president: Utilisateur | None = None
    for identifiant, prenom, nom, role, profil in COMPTES:
        mot_de_passe = mot_de_passe_aleatoire()
        email = None if role is Role.eleve else f"{identifiant}@{DOMAINE}"
        utilisateur = await preparer_compte(db, identifiant, prenom, nom, role, mot_de_passe, email)
        if identifiant == "preprod.president":
            president = utilisateur
        ligne = {"identifiant": identifiant, "mot_de_passe": mot_de_passe, "profil": profil}
        if utilisateur.email:
            ligne["email"] = utilisateur.email
        if role is Role.admin:
            ligne["perimetre"] = "National"
            await preparer_collaborateur(db, utilisateur, None, None)
            secret, codes = await activer_double_auth(db, utilisateur)
            ligne["secret_totp"] = secret
            ligne["codes_secours"] = ", ".join(codes)
        elif role is Role.encadreur:
            await preparer_encadreur(db, utilisateur, Fonction.enseignant, etablissement_id, EtatVerification.actif)
        else:
            affiche, classe = PROFILS_ELEVES[identifiant]
            await preparer_eleve(db, utilisateur, affiche, classe, etablissement_id)
        acces.append(ligne)
    assert president is not None  # COMPTES contient toujours preprod.president
    await _preparer_club(db, president, etablissement_id)
    journaliser(db, "comptes_de_test_prepares", details={"comptes": [compte[0] for compte in COMPTES]})
    await db.commit()
    return acces


async def _principal() -> list[dict[str, str]]:
    try:
        async with SessionLocal() as db:
            return await semer(db)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prépare les comptes de test de la préproduction.")
    parser.add_argument(
        "--fichier",
        default=str(FICHIER_PAR_DEFAUT),
        help="Fichier qui recevra les accès (droits 600).",
    )
    arguments = parser.parse_args()

    try:
        acces = asyncio.run(_principal())
    except PreprodRefusee:
        print(
            "Refusé : ces comptes de test ne sont créés que sur la préproduction (ENVIRONNEMENT=preprod).",
            file=sys.stderr,
        )
        return 1
    except PreparationImpossible as erreur:
        print(f"Refusé : {erreur}", file=sys.stderr)
        return 1

    chemin = Path(arguments.fichier)
    ecrire_fichier(acces, chemin, ENTETE)
    # Les mots de passe ne s'affichent pas : ils restent dans le fichier, hors de l'historique du terminal.
    print(f"{len(acces)} comptes de test prêts. Accès dans {chemin}.")
    for ligne in acces:
        print(f"  {ligne['identifiant']} — {ligne['profil']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
