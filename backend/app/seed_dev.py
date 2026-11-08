"""Comptes de démonstration pour la base LOCALE : un par profil, pour tester l'espace admin et les rôles.

    cd backend && uv run python -m app.seed_dev

Chaque lancement crée les comptes `dev.*` manquants, leur donne de nouveaux mots de passe aléatoires et écrit
les accès dans `.comptes-dev.local` à la racine du projet (ignoré par git). Les comptes à droits sensibles ont
une double authentification déjà active : leur secret et leurs codes de secours sont dans le même fichier.
Refusé en production : aucune base réelle ne doit recevoir ces comptes (docs/RULES.md).
"""

import asyncio
import io
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid7

from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import LIBELLES_ROLES, RoleDepart
from app.admin.journal import journaliser
from app.admin.models import DoubleAuth
from app.clubs.adhesions import adhesion_president
from app.clubs.models import Adhesion, Club, ClubAxe, EtatAdhesion, EtatClub
from app.comptes.models import Role, Utilisateur
from app.config import RACINE_PROJET, settings
from app.db import SessionLocal, engine
from app.eleves.models import Classe, Eleve
from app.encadreurs.models import EtatVerification, Fonction
from app.fichiers import images
from app.fichiers.stockage import stockage
from app.jeux import banque_initiale
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
from app.moderation.photos import ATTESTATION
from app.points import service as points
from app.points.bareme import ARTICLE_ELEVE
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
    # Le président est membre de droit de son club (spec 020).
    await adhesion_president(db, actif)
    db.add_all(
        [
            ClubAxe(club_id=actif.id, axe_code="sante-environnement"),
            ClubAxe(club_id=actif.id, axe_code="sport-secourisme"),
            ClubAxe(club_id=attente.id, axe_code="sante-sexuelle-evss"),
        ]
    )


def _article_de_test(titre: str, axe_code: str) -> dict[str, object]:
    """Un article de démonstration, signalé comme tel : aucun contenu de santé inventé n'est présenté comme réel."""
    return {
        "titre": f"Article de test — {titre}",
        "chapo": "Article de démonstration, rédigé pour essayer la plateforme : son contenu n'est pas validé.",
        "texte": "## Ce que nous avons fait\n\nTexte de **démonstration**.\n\n- une étape\n- une autre étape",
        "axe_code": axe_code,
        "afficher_club": True,
    }


async def _preparer_articles(db: AsyncSession) -> None:
    """Un article publié (élève 1), un en attente (encadreur actif), un à corriger (élève 2), une seule fois."""
    if await db.scalar(select(Contenu.id)):
        return
    ids = {
        identifiant: await db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == identifiant))
        for identifiant in ("dev.eleve1", "dev.eleve2", "dev.encadreur")
    }
    if None in ids.values():
        return
    maintenant = datetime.now(UTC)

    async def article(auteur: str, titre: str, axe: str, etat: EtatContenu) -> tuple[Contenu, VersionContenu]:
        contenu = Contenu(
            id=uuid7(), type="article", auteur_id=ids[auteur], etat=EtatContenu.brouillon, dre_code="grand-lome"
        )
        db.add(contenu)
        await db.flush()
        version = VersionContenu(
            id=uuid7(), contenu_id=contenu.id, numero=1, donnees=_article_de_test(titre, axe),
            etat=EtatVersion.soumise, soumise_le=maintenant,
        )  # fmt: skip
        db.add(version)
        await db.flush()
        contenu.version_travail_id = version.id
        contenu.soumis_le = maintenant
        contenu.etat = etat
        return contenu, version

    publie, version = await article(
        "dev.eleve1", "Un point d'eau dans la cour", "sante-environnement", EtatContenu.brouillon
    )
    club_id = await db.scalar(
        select(Adhesion.club_id).where(Adhesion.eleve_id == ids["dev.eleve1"], Adhesion.etat == EtatAdhesion.active)
    )
    version.etat = EtatVersion.approuvee
    publie.adresse = "article-de-test-un-point-d-eau-dans-la-cour"
    publie.axe_code = "sante-environnement"
    publie.publie_le = maintenant
    publie.club_beneficiaire_id = club_id
    publie.version_publiee_id = version.id
    publie.version_travail_id = None
    publie.etat = EtatContenu.publie
    db.add(DecisionModeration(contenu_id=publie.id, version_id=version.id, decision=TypeDecision.approuver))
    await points.crediter(db, ARTICLE_ELEVE, ids["dev.eleve1"], f"article:{publie.id}")

    await article("dev.encadreur", "Le sport, c'est la santé", "sport-secourisme", EtatContenu.en_attente)
    corriger, version = await article(
        "dev.eleve2", "Bien dormir avant les examens", "genie-imhotep", EtatContenu.a_corriger
    )
    version.etat = EtatVersion.a_corriger
    db.add(
        DecisionModeration(
            contenu_id=corriger.id,
            version_id=version.id,
            decision=TypeDecision.corriger,
            motif="Ajoute la source de tes conseils.",
        )
    )


async def _preparer_photo(db: AsyncSession) -> None:
    """Une photo de démonstration (une image unie générée, aucune personne) sur l'article de test publié, une fois."""
    contenu = await db.scalar(select(Contenu).where(Contenu.adresse == "article-de-test-un-point-d-eau-dans-la-cour"))
    if contenu is None or contenu.version_publiee_id is None:
        return
    if await db.scalar(select(VersionPhoto.photo_id).where(VersionPhoto.version_id == contenu.version_publiee_id)):
        return
    sortie = io.BytesIO()
    Image.new("RGB", (1200, 800), (46, 140, 90)).save(sortie, "JPEG")
    preparees = await images.preparer(sortie.getvalue())
    photo_id = uuid7()
    cles = {taille: f"photos/{photo_id}-{taille}.webp" for taille in ("grande", "vignette")}
    await stockage().enregistrer(cles["grande"], preparees.grande.octets)
    await stockage().enregistrer(cles["vignette"], preparees.vignette.octets)
    db.add(
        Photo(
            id=photo_id, contenu_id=contenu.id, auteur_id=contenu.auteur_id, cle_grande=cles["grande"],
            cle_vignette=cles["vignette"], largeur=preparees.grande.largeur, hauteur=preparees.grande.hauteur,
            octets=len(preparees.grande.octets), attestation=ATTESTATION,
        )
    )  # fmt: skip
    await db.flush()
    db.add(
        VersionPhoto(
            version_id=contenu.version_publiee_id, photo_id=photo_id, ordre=1, legende="Photo de test",
            couverture=True,
        )
    )  # fmt: skip


async def _preparer_commentaires(db: AsyncSession) -> None:
    """Deux commentaires de démonstration sur l'article de test publié (spec 025) : un publié (élève 2), un en attente
    (encadreur actif), une seule fois. Signalés comme tests, sans points."""
    article = await db.scalar(select(Contenu).where(Contenu.adresse == "article-de-test-un-point-d-eau-dans-la-cour"))
    if article is None or await db.scalar(select(Contenu.id).where(Contenu.type == "commentaire")):
        return
    ids = {
        identifiant: await db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == identifiant))
        for identifiant in ("dev.eleve2", "dev.encadreur")
    }
    if None in ids.values():
        return
    maintenant = datetime.now(UTC)
    for auteur, texte, publie in (
        ("dev.eleve2", "[Commentaire de test] Bravo au club, on veut faire pareil chez nous !", True),
        ("dev.encadreur", "[Commentaire de test] Pensez à vérifier la qualité de l'eau chaque mois.", False),
    ):
        contenu = Contenu(
            id=uuid7(), type="commentaire", auteur_id=ids[auteur], etat=EtatContenu.brouillon,
            dre_code="grand-lome", parent_id=article.id,
        )  # fmt: skip
        db.add(contenu)
        await db.flush()
        version = VersionContenu(
            id=uuid7(), contenu_id=contenu.id, numero=1, donnees={"texte": texte},
            etat=EtatVersion.approuvee if publie else EtatVersion.soumise, soumise_le=maintenant,
        )  # fmt: skip
        db.add(version)
        await db.flush()
        contenu.soumis_le = maintenant
        if publie:
            contenu.version_publiee_id = version.id
            contenu.publie_le = maintenant
            contenu.etat = EtatContenu.publie
            db.add(DecisionModeration(contenu_id=contenu.id, version_id=version.id, decision=TypeDecision.approuver))
        else:
            contenu.version_travail_id = version.id
            contenu.etat = EtatContenu.en_attente


async def _preparer_contenus_du_club(db: AsyncSession) -> None:
    """Une actualité publiée et une proposition de fiche en attente pour le club de démonstration (spec 026), une
    fois. Leur auteur est le président du club."""
    club = await db.scalar(select(Club).where(Club.nom == "Club Santé Tokoin", Club.etat == EtatClub.actif))
    if club is None or club.president_id is None:
        return
    if await db.scalar(select(Contenu.id).where(Contenu.club_id == club.id)):
        return
    maintenant = datetime.now(UTC)
    contenus = (
        ("actualite", _article_de_test("Atelier de lavage des mains", "sante-environnement"), True),
        (
            "fiche_club",
            {"description": "[Test] Ateliers d'hygiène chaque jeudi à 16 h.", "axes": ["sante-environnement"]},
            False,
        ),
    )
    for type_contenu, donnees, publie in contenus:
        contenu = Contenu(
            id=uuid7(), type=type_contenu, auteur_id=club.president_id, etat=EtatContenu.brouillon,
            dre_code="grand-lome", club_id=club.id,
        )  # fmt: skip
        db.add(contenu)
        await db.flush()
        version = VersionContenu(
            id=uuid7(), contenu_id=contenu.id, numero=1, donnees=donnees,
            etat=EtatVersion.approuvee if publie else EtatVersion.soumise, soumise_le=maintenant,
        )  # fmt: skip
        db.add(version)
        await db.flush()
        contenu.soumis_le = maintenant
        if publie:
            contenu.adresse = "actualite-de-test-atelier-de-lavage-des-mains"
            contenu.axe_code = "sante-environnement"
            contenu.publie_le = maintenant
            contenu.version_publiee_id = version.id
            contenu.etat = EtatContenu.publie
            db.add(DecisionModeration(contenu_id=contenu.id, version_id=version.id, decision=TypeDecision.approuver))
        else:
            contenu.version_travail_id = version.id
            contenu.etat = EtatContenu.en_attente


async def semer(db: AsyncSession) -> list[dict[str, str]]:
    """Prépare tous les comptes `dev.*` et renvoie leurs accès. Valide la transaction."""
    if settings.production:
        raise ProductionRefusee
    acces: list[dict[str, str]] = []
    await preparer_semestre(db)
    await banque_initiale.charger(db)
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
    await _preparer_articles(db)
    await _preparer_photo(db)
    await _preparer_commentaires(db)
    await _preparer_contenus_du_club(db)
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
