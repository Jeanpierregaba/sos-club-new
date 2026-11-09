"""Aides des tests de la bibliothèque (spec 028) : PDF et images construits à la volée, ressources en base."""

import io
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid7

from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.fichiers.stockage import stockage

GESTION = "/api/admin/bibliotheque"
PUBLIC = "/api/bibliotheque"
PREPARATION = {
    ("bibliotheque", "consulter"),
    ("bibliotheque", "creer"),
    ("bibliotheque", "modifier"),
    ("bibliotheque", "soumettre"),
}
PUBLICATION = {("bibliotheque", "consulter"), ("bibliotheque", "approuver"), ("bibliotheque", "depublier")}
APPROBATION = {"validateur_nom": "Dr Afi Mensah", "validateur_qualite": "Médecin de santé publique"}


def pdf(pages: int = 1, *, javascript: bool = False) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    if javascript:
        writer._root_object[NameObject("/OpenAction")] = DictionaryObject(
            {NameObject("/S"): NameObject("/JavaScript"), NameObject("/JS"): TextStringObject("app.alert(1);")}
        )
    sortie = io.BytesIO()
    writer.write(sortie)
    return sortie.getvalue()


def image(format: str = "JPEG", taille: tuple[int, int] = (900, 1200)) -> bytes:
    sortie = io.BytesIO()
    Image.new("RGB", taille, (30, 120, 200)).save(sortie, format)
    return sortie.getvalue()


def envoi_pdf(octets: bytes | None = None, nom: str = "guide.pdf") -> dict[str, Any]:
    return {"files": {"fichier": (nom, octets if octets is not None else pdf(), "application/pdf")}}


def envoi_image(octets: bytes | None = None) -> dict[str, Any]:
    return {"files": {"fichier": ("couverture.jpg", octets if octets is not None else image(), "image/jpeg")}}


def creer_ressource(
    en_base: Callable[..., Any],
    *,
    etat: EtatRessource = EtatRessource.publie,
    categorie: CategorieRessource = CategorieRessource.guide,
    titre: str = "Guide du lavage des mains",
    axe_code: str | None = None,
    couverture: bool = False,
    publie_le: datetime | None = None,
    contenu_de_test: bool = False,
    telechargements: int = 0,
) -> Ressource:
    """Une ressource et ses fichiers, écrits dans le stockage du test."""

    async def creer(db: AsyncSession) -> Ressource:
        identifiant = uuid7()
        disque = stockage()
        cle = f"ressources/{identifiant}-document.pdf"
        octets = pdf(2)
        await disque.enregistrer(cle, octets)
        grande = vignette = None
        if couverture:
            grande, vignette = f"ressources/{identifiant}-grande.webp", f"ressources/{identifiant}-vignette.webp"
            await disque.enregistrer(grande, b"RIFF-grande")
            await disque.enregistrer(vignette, b"RIFF-vignette")
        publiee = etat in (EtatRessource.publie, EtatRessource.depublie)
        ressource = Ressource(
            id=identifiant,
            titre=titre,
            description="Les bons gestes, étape par étape.",
            categorie=categorie,
            axe_code=axe_code,
            etat=etat,
            contenu_de_test=contenu_de_test,
            fichier_cle=cle,
            fichier_octets=len(octets),
            pages=2,
            couverture_grande=grande,
            couverture_vignette=vignette,
            telechargements=telechargements,
            validateur_nom=APPROBATION["validateur_nom"] if publiee else None,
            validateur_qualite=APPROBATION["validateur_qualite"] if publiee else None,
            publie_le=(publie_le or datetime.now(UTC)) if publiee else None,
            deja_publiee=publiee,
        )
        db.add(ressource)
        await db.flush()
        return ressource

    return en_base(creer)
