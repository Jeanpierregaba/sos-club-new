"""Préparation d'une photo envoyée (spec 024) : vérifiée, redressée, réduite, ré-encodée en WebP sans aucune
métadonnée. Rien du fichier d'origine n'est jamais servi.

La mémoire compte sur un petit VPS : un JPEG est décodé directement à taille réduite (`draft`), l'image est
redressée et réduite sur place, et la vignette se fait à partir de la grande.
"""

import asyncio
import io
import struct
import threading
from dataclasses import dataclass

from PIL import Image, ImageOps

# MPO : le JPEG « multi-images » de beaucoup de téléphones (carte de gain HDR) ; seule la première image compte.
FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}
ANIMABLES = {"PNG", "WEBP"}
# Contre les « bombes » de décompression, et pour tenir la mémoire : au-delà, la photo est refusée.
PIXELS_MAX = 24_000_000
GRANDE = 1600
VIGNETTE = 480
QUALITE = 80
# Au plus 2 traitements à la fois par processus.
_SEMAPHORE = threading.BoundedSemaphore(2)

Image.MAX_IMAGE_PIXELS = PIXELS_MAX


class ImageRefusee(ValueError):
    """Le message s'affiche tel quel à l'auteur."""


# Ce que Pillow lève sur un fichier abîmé ou trompeur (en-tête tronqué, EXIF mal formé, format inconnu).
LECTURE_IMPOSSIBLE = (
    OSError,
    ValueError,
    SyntaxError,
    struct.error,
    KeyError,
    IndexError,
    TypeError,
    AttributeError,
    ZeroDivisionError,
)
TROP_GRANDE = "Cette photo est trop grande : réduis-la avant de l'envoyer."
ILLISIBLE = "Ce fichier n'est pas une photo lisible."


@dataclass(frozen=True)
class Taille:
    octets: bytes
    largeur: int
    hauteur: int


@dataclass(frozen=True)
class ImagesPreparees:
    grande: Taille
    vignette: Taille


def _encoder(image: Image.Image) -> Taille:
    # Une image neuve, faite des seuls pixels : aucune métadonnée (EXIF, GPS, XMP, ICC) ne peut suivre.
    nette = Image.frombytes(image.mode, image.size, image.tobytes())
    sortie = io.BytesIO()
    nette.save(sortie, "WEBP", quality=QUALITE, method=4)
    return Taille(sortie.getvalue(), nette.width, nette.height)


def _ouvrir(octets: bytes) -> Image.Image:
    """L'image décodée, redressée et réduite à la taille de la grande, en RGB ou RGBA."""
    image = Image.open(io.BytesIO(octets))
    if image.format not in FORMATS:
        raise ImageRefusee("Envoie une photo au format JPEG, PNG ou WebP.")
    if image.format in ANIMABLES and getattr(image, "is_animated", False):
        raise ImageRefusee("Les images animées ne sont pas acceptées : envoie une photo fixe.")
    # Pillow n'arrête qu'au double de MAX_IMAGE_PIXELS : la limite est tenue ici, avant de décoder.
    if image.width * image.height > Image.MAX_IMAGE_PIXELS:
        raise ImageRefusee(TROP_GRANDE)
    if image.format in {"JPEG", "MPO"}:
        # Décodage directement à une taille proche de la cible : bien moins de mémoire.
        image.draft("RGB", (GRANDE, GRANDE))
    image.load()
    ImageOps.exif_transpose(image, in_place=True)
    image.thumbnail((GRANDE, GRANDE), Image.Resampling.LANCZOS)
    mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
    return image if image.mode == mode else image.convert(mode)


def _preparer_seul(octets: bytes) -> ImagesPreparees:
    try:
        image = _ouvrir(octets)
    except ImageRefusee:
        raise
    except Image.DecompressionBombError:
        raise ImageRefusee(TROP_GRANDE) from None
    except LECTURE_IMPOSSIBLE:
        # Fichier tronqué, EXIF malformé, format inconnu : toujours un refus clair, jamais une erreur du serveur.
        raise ImageRefusee(ILLISIBLE) from None
    grande = _encoder(image)
    image.thumbnail((VIGNETTE, VIGNETTE), Image.Resampling.LANCZOS)
    vignette = _encoder(image)
    return ImagesPreparees(grande=grande, vignette=vignette)


def _preparer(octets: bytes) -> ImagesPreparees:
    with _SEMAPHORE:
        return _preparer_seul(octets)


async def preparer(octets: bytes) -> ImagesPreparees:
    return await asyncio.to_thread(_preparer, octets)
