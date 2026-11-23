"""Les 4 livres de l'Académie Génie Imhotep (spec 050), publiés dans la bibliothèque au déploiement.

Documents officiels fournis par AIMES-AFRIQUE : ils sont publiés avec leur validateur, comme la banque de questions.
Le PDF passe par le même contrôle qu'un dépôt du back office (`fichiers.pdf`) et c'est sa version réécrite qui est
stockée ; la couverture (la première page) est préparée comme une couverture déposée.

Chargement idempotent, par titre : un livre déjà présent, même dépublié ou modifié par l'équipe, n'est ni recréé ni
touché. En prod, le service `migrations` l'enchaîne après les migrations ; un échec ne bloque pas le déploiement
(les quiz déjà migrés doivent aller avec le nouveau site) : il s'affiche dans le journal, et la commande se relance
telle quelle :

    uv run python -m app.bibliotheque.livres_officiels
"""

import asyncio
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Les tables que `ressource` référence (axe, utilisateur), pour un lancement hors de l'API.
import app.comptes.models
import app.referentiel.models  # noqa: F401
from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.db import SessionLocal
from app.fichiers import images, pdf
from app.fichiers.stockage import Stockage, StockageIndisponible, stockage

DOSSIER = Path(__file__).resolve().parent / "livres"
VALIDATEUR = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
QUALITE = "Document officiel de l'Académie Génie Imhotep"
AXE = "genie-imhotep"


@dataclass(frozen=True)
class Livre:
    fichier: str  # sans extension : <fichier>.pdf et sa couverture <fichier>.jpg
    titre: str
    description: str
    parution: str | None = None


LIVRES = (
    Livre(
        "college",
        "Génie Imhotep — Questionnaire du jeu, Collège",
        "Le fascicule du jeu Génie Imhotep pour le collège (secondaire 1) : l'organisation des équipes et des "
        "compétitions, puis le questionnaire, de « État de choc » à « Réanimation », avec l'index des préfixes et "
        "suffixes et des planches anatomiques.",
    ),
    Livre(
        "lycee",
        "Génie Imhotep — Questionnaire du jeu, Lycée",
        "Le fascicule du jeu Génie Imhotep pour le lycée (secondaire 2) : l'organisation des équipes et des "
        "compétitions, puis le questionnaire, de « État de choc » à « Réanimation », avec l'index des préfixes et "
        "suffixes et des planches anatomiques.",
    ),
    Livre(
        "evss",
        "Génie Imhotep — Éducation aux valeurs et santé sexuelle (EVSS)",
        "Le questionnaire du jeu Génie Imhotep consacré à l'éducation aux valeurs et à la santé sexuelle : "
        "l'organisation des compétitions, la fiche officielle de match et les questions.",
    ),
    Livre(
        "emission-saison-1",
        "Génie Imhotep — L'émission sur SOS Docteur TV, saison 1",
        "Le fascicule de la saison 1 de l'émission Génie Imhotep sur SOS Docteur TV : l'organisation du jeu télévisé "
        "et son questionnaire, avec l'index des préfixes et suffixes, des planches anatomiques et la fiche officielle "
        "de match.",
        parution="Saison 1",
    ),
)


async def _publier(db: AsyncSession, disque: Stockage, livre: Livre, maintenant: datetime) -> None:
    infos = await pdf.examiner((DOSSIER / f"{livre.fichier}.pdf").read_bytes())
    couverture = await images.preparer((DOSSIER / f"{livre.fichier}.jpg").read_bytes())
    identifiant = uuid7()
    cles = {
        f"ressources/{identifiant}-document.pdf": infos.octets,
        f"ressources/{identifiant}-grande.webp": couverture.grande.octets,
        f"ressources/{identifiant}-vignette.webp": couverture.vignette.octets,
    }
    document, grande, vignette = cles
    try:
        for cle, octets in cles.items():
            await disque.enregistrer(cle, octets)
        db.add(
            Ressource(
                id=identifiant, titre=livre.titre, description=livre.description,
                categorie=CategorieRessource.fascicule, axe_code=AXE, parution=livre.parution,
                etat=EtatRessource.publie, contenu_de_test=False, fichier_cle=document,
                fichier_octets=len(infos.octets), pages=infos.pages, couverture_grande=grande,
                couverture_vignette=vignette, validateur_nom=VALIDATEUR, validateur_qualite=QUALITE,
                publie_le=maintenant, deja_publiee=True,
            )
        )  # fmt: skip
        await db.commit()
    except BaseException:
        await db.rollback()
        for cle in cles:
            await disque.supprimer(cle)
        raise


async def charger(db: AsyncSession, disque: Stockage | None = None) -> list[str]:
    """Publie les livres absents ; renvoie leurs titres."""
    disque = disque or stockage()
    presents = set(await db.scalars(select(Ressource.titre).where(Ressource.titre.in_([x.titre for x in LIVRES]))))
    maintenant = datetime.now(UTC)
    publies = []
    for livre in LIVRES:
        if livre.titre in presents:
            continue
        await _publier(db, disque, livre, maintenant)
        publies.append(livre.titre)
    return publies


async def _principal() -> int:
    try:
        async with SessionLocal() as db:
            publies = await charger(db)
    except (pdf.PdfRefuse, images.ImageRefusee, StockageIndisponible, OSError) as erreur:
        # Les livres déjà publiés le restent ; la relance reprend là où le chargement s'est arrêté.
        print(f"Spec 050 : livres Génie Imhotep non chargés ({type(erreur).__name__} : {erreur}).", file=sys.stderr)
        return 1
    if publies:
        print(f"Spec 050 : {len(publies)} livre(s) Génie Imhotep publié(s) dans la bibliothèque.")
    else:
        print("Spec 050 : les livres Génie Imhotep sont déjà dans la bibliothèque.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_principal()))
