"""Le certificat Génie Imhotep en PDF (spec 029), produit à la demande pour son seul titulaire et jamais stocké.

Les textes viennent des champs figés à la délivrance et passent par `drawString` (aucune interprétation). Le QR
code mène à la page publique de vérification, qui ne montre pas le nom complet.
"""

import io
from datetime import datetime

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.certification.models import Certificat
from app.config import settings

BLEU = HexColor("#1e3a6e")
VERT = HexColor("#1f8a4c")
ROUGE = HexColor("#c8322b")
GRIS = HexColor("#4b5563")
MOIS = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)  # fmt: skip


def date_longue(moment: datetime) -> str:
    jour = "1er" if moment.day == 1 else str(moment.day)
    return f"{jour} {MOIS[moment.month - 1]} {moment.year}"


def adresse_de_verification(numero: str) -> str:
    return f"{settings.site_origine.rstrip('/')}/certificats/{numero}"


def _centrer(c: canvas.Canvas, texte: str, y: float, police: str, taille: float, couleur: HexColor) -> None:
    c.setFont(police, taille)
    c.setFillColor(couleur)
    c.drawCentredString(landscape(A4)[0] / 2, y, texte)


def generer(certificat: Certificat) -> bytes:
    largeur, hauteur = landscape(A4)
    flux = io.BytesIO()
    c = canvas.Canvas(flux, pagesize=(largeur, hauteur), pageCompression=1)
    c.setTitle(f"Certificat Génie Imhotep {certificat.numero}")
    c.setAuthor("Clubs Santé scolaires du Togo")

    # Double cadre.
    c.setStrokeColor(BLEU)
    c.setLineWidth(4)
    c.rect(24, 24, largeur - 48, hauteur - 48)
    c.setStrokeColor(VERT)
    c.setLineWidth(1.5)
    c.rect(34, 34, largeur - 68, hauteur - 68)

    nom = f"{certificat.titulaire_prenom} {certificat.titulaire_nom}"
    _centrer(c, "CLUBS SANTÉ SCOLAIRES DU TOGO", hauteur - 95, "Helvetica-Bold", 13, ROUGE)
    _centrer(c, "Certificat Génie Imhotep", hauteur - 150, "Helvetica-Bold", 40, BLEU)
    _centrer(c, "décerné à", hauteur - 205, "Helvetica-Oblique", 16, GRIS)
    # Un nom long est réduit pour tenir dans le cadre.
    taille = 32.0
    while taille > 12 and stringWidth(nom, "Helvetica-Bold", taille) > largeur - 140:
        taille -= 1
    _centrer(c, nom, hauteur - 255, "Helvetica-Bold", taille, VERT)
    _centrer(
        c, "pour avoir réussi les 12 quiz du parcours officiel de certification Génie Imhotep,",
        hauteur - 305, "Helvetica", 15, GRIS,
    )  # fmt: skip
    _centrer(
        c, "dont chaque quiz est validé par un professionnel de santé.", hauteur - 326, "Helvetica", 15, GRIS
    )  # fmt: skip
    _centrer(c, f"Délivré le {date_longue(certificat.delivre_le)}", hauteur - 380, "Helvetica-Bold", 14, BLEU)

    # Numéro et vérification, en bas.
    c.setFont("Helvetica", 11)
    c.setFillColor(GRIS)
    c.drawString(70, 90, f"Numéro : {certificat.numero}")
    c.drawString(70, 72, "Vérifie ce certificat en scannant le QR code ou sur :")
    c.setFillColor(BLEU)
    c.drawString(70, 54, adresse_de_verification(certificat.numero))

    qr = QrCodeWidget(adresse_de_verification(certificat.numero), barLevel="M")
    x0, y0, x1, y1 = qr.getBounds()
    cote = 110
    dessin = Drawing(cote, cote, transform=[cote / (x1 - x0), 0, 0, cote / (y1 - y0), 0, 0])
    dessin.add(qr)
    renderPDF.draw(dessin, c, largeur - 70 - cote, 48)

    c.showPage()
    c.save()
    return flux.getvalue()
