"""La carte « Partager mon classement » (spec 044) : une image PNG de 1080 × 1350 px, le format portrait des réseaux,
produite à la demande pour son seul titulaire et jamais stockée.

Les textes sont choisis par `textes`, une fonction pure que les tests lisent : le nom affiché (pseudonyme d'un élève,
prénom et initiale d'un encadreur), le rang, les points, le niveau et la période ; le club seulement si la personne
le choisit. Jamais le nom complet, l'établissement, l'identifiant ni une coordonnée (docs/RULES.md). Un classement
du semestre en cours est dit provisoire : seul le palmarès publié à la clôture (spec 037) est officiel.
"""

import io
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont

from app.certification.certificat_pdf import POLICES, date_longue
from app.config import settings

LARGEUR, HAUTEUR = 1080, 1350
MARGE = 90
BLEU, BLEU_NUIT, VERT, ROUGE, SOLEIL, ENCRE, GRIS, BLANC = (
    "#1e3a6e", "#14284d", "#16a34a", "#c8322b", "#fbbf24", "#111827", "#4b5563", "#ffffff",
)  # fmt: skip
NORMALE = POLICES / "NotoSans-Regular.ttf"
GRASSE = POLICES / "NotoSans-Bold.ttf"
PROGRAMME = "Clubs Santé SOS Docteur TV"
# Le logo du programme (tiré de `src/assets/logo.webp`), 600 px de large, sur fond transparent.
LOGO = Path(__file__).parent / "ressources" / "logo.png"


class Vue(StrEnum):
    national = "national"
    dre = "dre"
    club = "club"


@dataclass(frozen=True)
class CarteClassement:
    nom: str
    niveau: str  # une valeur de `Vue`
    dre: str | None
    club: str | None
    periode: str  # « semestre » ou « historique »
    semestre: str | None  # le libellé du semestre en cours
    rang: int
    classes: int
    points: int
    le: datetime


def rang_affiche(rang: int) -> str:
    return "1ᵉʳ" if rang == 1 else f"{rang}ᵉ"


def _nombre(valeur: int) -> str:
    return f"{valeur:,}".replace(",", " ")


def _niveau(carte: CarteClassement) -> str:
    if carte.niveau == Vue.dre:
        return f"DRE {carte.dre}" if carte.dre else "Ma DRE"
    if carte.niveau == Vue.club:
        return "Classement de mon Club Santé"
    return "National"


def _periode(carte: CarteClassement) -> str:
    if carte.periode == "semestre":
        return carte.semestre or "Semestre en cours"
    return "Depuis le début"


def _site() -> str:
    return urlsplit(settings.site_origine).hostname or "clubsante"


def textes(carte: CarteClassement, *, afficher_club: bool) -> list[str]:
    """Tout ce que la carte écrit, dans l'ordre : la seule source des textes du dessin."""
    lignes = [
        PROGRAMME,
        "Mon classement",
        carte.nom,
        rang_affiche(carte.rang),
        f"sur {_nombre(carte.classes)} classés",
        f"{_nombre(carte.points)} points",
        _niveau(carte),
        _periode(carte),
    ]
    if afficher_club and carte.club:
        lignes.append(carte.club)
    lignes.append(
        f"Classement provisoire au {date_longue(carte.le)}"
        if carte.periode == "semestre"
        else "Total depuis mon inscription"
    )
    lignes.append(f"Rejoins le mouvement sur {_site()}")
    return lignes


def _police(chemin: object, taille: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(chemin), taille)


def _centre(dessin: ImageDraw.ImageDraw, y: int, texte: str, chemin: object, taille: int, couleur: str) -> None:
    """Un texte centré ; réduit jusqu'à tenir dans la largeur utile, puis coupé avec « … »."""
    utile = LARGEUR - 2 * MARGE
    police = _police(chemin, taille)
    while taille > 24 and dessin.textlength(texte, font=police) > utile:
        taille -= 2
        police = _police(chemin, taille)
    while len(texte) > 1 and dessin.textlength(texte, font=police) > utile:
        texte = texte[:-2].rstrip() + "…"
    dessin.text((LARGEUR // 2, y), texte, font=police, fill=couleur, anchor="ms")


def png(carte: CarteClassement, *, afficher_club: bool) -> bytes:
    (programme, titre, nom, rang, classes, points, niveau, periode, *suite) = textes(carte, afficher_club=afficher_club)
    *club, mention, site = suite

    image = Image.new("RGB", (LARGEUR, HAUTEUR), BLANC)
    dessin = ImageDraw.Draw(image)
    # Le logo sur une pastille blanche dans le bandeau, la carte centrale, le liseré rouge : la charte de la carte
    # numérique (spec 040).
    dessin.rectangle((0, 0, LARGEUR, 250), fill=BLEU)
    dessin.rectangle((0, HAUTEUR - 24, LARGEUR, HAUTEUR), fill=ROUGE)
    with Image.open(LOGO) as source:
        logo = source.convert("RGBA")
    logo.thumbnail((520, 100))
    pastille = (LARGEUR // 2 - logo.width // 2 - 36, 40, LARGEUR // 2 + logo.width // 2 + 36, 40 + logo.height + 36)
    dessin.rounded_rectangle(pastille, radius=40, fill=BLANC)
    image.paste(logo, (LARGEUR // 2 - logo.width // 2, 58), logo)
    _centre(dessin, 222, titre, GRASSE, 44, SOLEIL)

    dessin.rounded_rectangle((MARGE - 20, 290, LARGEUR - MARGE + 20, 1090), radius=48, fill=BLEU_NUIT)
    _centre(dessin, 400, nom, GRASSE, 64, BLANC)
    _centre(dessin, 640, rang, GRASSE, 220, SOLEIL)
    _centre(dessin, 720, classes, NORMALE, 40, BLANC)
    _centre(dessin, 830, points, GRASSE, 72, BLANC)
    _centre(dessin, 920, niveau, GRASSE, 44, VERT if carte.niveau == Vue.club else SOLEIL)
    _centre(dessin, 980, periode, NORMALE, 38, BLANC)
    if club:
        _centre(dessin, 1045, club[0], NORMALE, 34, BLANC)

    _centre(dessin, 1155, mention, NORMALE, 34, GRIS)
    _centre(dessin, 1220, programme, GRASSE, 38, BLEU)
    _centre(dessin, 1280, site, NORMALE, 32, GRIS)

    sortie = io.BytesIO()
    image.save(sortie, format="PNG", optimize=True)
    return sortie.getvalue()
