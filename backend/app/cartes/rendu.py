"""La carte numérique en PDF et en PNG (spec 040), produite à la demande pour son seul titulaire et jamais stockée.

Une seule mise en page, décrite en millimètres au format carte bancaire (85,6 × 54 mm), est dessinée deux fois :
par reportlab pour le PDF, par Pillow pour l'image. Les textes passent par `drawString` et `ImageDraw.text`, sans
aucune interprétation ; un texte trop long est réduit puis coupé avec « … ». Le QR code, produit par segno, mène à la
page publique de vérification, qui ne montre aucun nom.
"""

import io
from collections.abc import Iterator
from dataclasses import dataclass

import segno
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.cartes.models import TypeCarte
from app.cartes.service import EtatCarte
from app.certification.certificat_pdf import GRASSE, NORMALE, POLICES, date_longue
from app.config import settings

LARGEUR, HAUTEUR = 85.6, 54.0  # mm
PIXELS_PAR_MM = 1012 / LARGEUR  # 1012 × 638 px : net sur un téléphone, imprimable en 300 dpi
BLEU, ROUGE, ENCRE, GRIS, BLANC = "#1e3a6e", "#c8322b", "#111827", "#4b5563", "#ffffff"
POINT_EN_MM = 25.4 / 72
MARGE = 5.0
QR_COTE = 24.0
BANDEAU = 11.0
ROLES = {"membre": "Membre", "president": "Président du club", "encadreur": "Encadreur"}
FICHIERS_POLICES = {NORMALE: POLICES / "NotoSans-Regular.ttf", GRASSE: POLICES / "NotoSans-Bold.ttf"}


def adresse_de_verification(code: str) -> str:
    return f"{settings.site_origine.rstrip('/')}/carte/{code}"


@dataclass(frozen=True)
class Texte:
    x: float  # mm depuis la gauche
    ligne: float  # mm depuis le haut, ligne de base
    texte: str
    police: str
    taille: float  # points
    couleur: str
    largeur_max: float  # mm


def _ajuster(texte: str, police: str, taille: float, largeur_max: float) -> tuple[str, float]:
    """Réduit la taille jusqu'aux deux tiers, puis coupe avec « … » : un nom long reste lisible et dans la carte."""

    def largeur(t: str, s: float) -> float:
        return stringWidth(t, police, s) * POINT_EN_MM

    plancher = taille * 2 / 3
    while taille > plancher and largeur(texte, taille) > largeur_max:
        taille -= 0.25
    if largeur(texte, taille) > largeur_max:
        while texte and largeur(texte + "…", taille) > largeur_max:
            texte = texte[:-1]
        texte = texte.rstrip() + "…"
    return texte, taille


def _textes(etat: EtatCarte) -> Iterator[Texte]:
    titre = "CARTE MEMBRE" if etat.type is TypeCarte.membre else "CARTE ENCADREUR"
    yield Texte(MARGE, 5.6, titre, GRASSE, 9, BLANC, LARGEUR - 2 * MARGE)
    yield Texte(MARGE, 9.2, "Club Santé SOS Docteur TV", NORMALE, 6.5, BLANC, LARGEUR - 2 * MARGE)
    colonne = LARGEUR - 2 * MARGE - QR_COTE - 3
    nom = f"{etat.prenom or ''} {(etat.nom or '').upper()}".strip()
    yield Texte(MARGE, 19.5, nom, GRASSE, 11, BLEU, colonne)
    yield Texte(MARGE, 24.0, ROLES[etat.role], GRASSE, 7.5, ROUGE, colonne)
    lignes = (
        ("Numéro", etat.numero),
        ("Établissement", etat.etablissement or "—"),
        ("Club", etat.club or "Non affilié"),
        ("Délivrée le", date_longue(etat.delivree_le)),
    )
    for rang, (libelle, valeur) in enumerate(lignes):
        y = 30.5 + rang * 5.6
        yield Texte(MARGE, y, libelle.upper(), NORMALE, 5, GRIS, colonne)
        yield Texte(MARGE, y + 2.7, valeur, GRASSE, 7, ENCRE, colonne)
    yield Texte(
        LARGEUR - MARGE - QR_COTE, BANDEAU + 3 + QR_COTE + 3.2, "Scanne pour vérifier", NORMALE, 5, GRIS, QR_COTE
    )


def _qr(etat: EtatCarte) -> segno.QRCode:
    return segno.make(adresse_de_verification(etat.code), error="m")


def _origine_qr() -> tuple[float, float]:
    """Coin haut gauche du QR, en mm."""
    return LARGEUR - MARGE - QR_COTE, BANDEAU + 3


def pdf(etat: EtatCarte) -> bytes:
    flux = io.BytesIO()
    c = canvas.Canvas(flux, pagesize=(LARGEUR * mm, HAUTEUR * mm), pageCompression=1)
    c.setTitle(f"Carte {etat.numero}")
    c.setAuthor("Clubs Santé scolaires du Togo")

    def bas(y_mm: float) -> float:
        return (HAUTEUR - y_mm) * mm

    c.setFillColor(HexColor(BLEU))
    c.rect(0, bas(BANDEAU), LARGEUR * mm, BANDEAU * mm, stroke=0, fill=1)
    c.setFillColor(HexColor(ROUGE))
    c.rect(0, 0, LARGEUR * mm, 1.2 * mm, stroke=0, fill=1)
    for t in _textes(etat):
        texte, taille = _ajuster(t.texte, t.police, t.taille, t.largeur_max)
        c.setFont(t.police, taille)
        c.setFillColor(HexColor(t.couleur))
        c.drawString(t.x * mm, bas(t.ligne), texte)

    qr = _qr(etat)
    matrice = list(qr.matrix)
    module = QR_COTE / len(matrice)
    x0, y0 = _origine_qr()
    c.setFillColor(HexColor(ENCRE))
    for i, rangee in enumerate(matrice):
        for j, sombre in enumerate(rangee):
            if sombre:
                c.rect((x0 + j * module) * mm, bas(y0 + (i + 1) * module), module * mm, module * mm, stroke=0, fill=1)
    c.showPage()
    c.save()
    return flux.getvalue()


def png(etat: EtatCarte) -> bytes:
    def px(valeur_mm: float) -> int:
        return round(valeur_mm * PIXELS_PAR_MM)

    image = Image.new("RGB", (px(LARGEUR), px(HAUTEUR)), BLANC)
    dessin = ImageDraw.Draw(image)
    dessin.rectangle((0, 0, px(LARGEUR), px(BANDEAU)), fill=BLEU)
    dessin.rectangle((0, px(HAUTEUR - 1.2), px(LARGEUR), px(HAUTEUR)), fill=ROUGE)
    for t in _textes(etat):
        texte, taille = _ajuster(t.texte, t.police, t.taille, t.largeur_max)
        police = ImageFont.truetype(str(FICHIERS_POLICES[t.police]), px(taille * POINT_EN_MM))
        dessin.text((px(t.x), px(t.ligne)), texte, font=police, fill=t.couleur, anchor="ls")

    flux_qr = io.BytesIO()
    _qr(etat).save(flux_qr, kind="png", scale=10, border=0, dark=ENCRE, light=BLANC)
    flux_qr.seek(0)
    cote = px(QR_COTE)
    vignette = Image.open(flux_qr).convert("RGB").resize((cote, cote), Image.Resampling.NEAREST)
    x0, y0 = _origine_qr()
    image.paste(vignette, (px(x0), px(y0)))

    sortie = io.BytesIO()
    image.save(sortie, format="PNG", optimize=True)
    return sortie.getvalue()
