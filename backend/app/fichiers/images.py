"""Préparation d'une photo envoyée (spec 024) : vérifiée, redressée, réduite, ré-encodée en WebP sans aucune
métadonnée. Rien du fichier d'origine n'est jamais servi."""

import asyncio
import io
import threading
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

FORMATS = {"JPEG", "PNG", "WEBP"}
# Contre les « bombes » de décompression : au-delà, Pillow lève une erreur au lieu de remplir la mémoire.
PIXELS_MAX = 40_000_000
GRANDE = 1600
VIGNETTE = 480
QUALITE = 80
# Décoder une grande photo prend beaucoup de mémoire : au plus 2 traitements à la fois par processus.
_SEMAPHORE = threading.BoundedSemaphore(2)

Image.MAX_IMAGE_PIXELS = PIXELS_MAX


class ImageRefusee(ValueError):
    """Le message s'affiche tel quel à l'auteur."""


@dataclass(frozen=True)
class Taille:
    octets: bytes
    largeur: int
    hauteur: int


@dataclass(frozen=True)
class ImagesPreparees:
    grande: Taille
    vignette: Taille


def _encoder(image: Image.Image, cote: int) -> Taille:
    copie = image.copy()
    copie.thumbnail((cote, cote), Image.Resampling.LANCZOS)
    # Une image neuve, faite des seuls pixels : aucune métadonnée (EXIF, GPS, XMP, ICC) ne peut suivre.
    nette = Image.frombytes(copie.mode, copie.size, copie.tobytes())
    sortie = io.BytesIO()
    nette.save(sortie, "WEBP", quality=QUALITE, method=4)
    return Taille(sortie.getvalue(), nette.width, nette.height)


def _preparer(octets: bytes) -> ImagesPreparees:
    with _SEMAPHORE:
        return _preparer_seul(octets)


def _preparer_seul(octets: bytes) -> ImagesPreparees:
    try:
        with Image.open(io.BytesIO(octets)) as image:
            if image.format not in FORMATS:
                raise ImageRefusee("Envoie une photo au format JPEG, PNG ou WebP.")
            # Pillow n'arrête qu'au double de MAX_IMAGE_PIXELS : la limite est tenue ici, avant de décoder.
            if image.width * image.height > Image.MAX_IMAGE_PIXELS:
                raise ImageRefusee("Cette photo est trop grande : réduis-la avant de l'envoyer.")
            if getattr(image, "is_animated", False):
                raise ImageRefusee("Les images animées ne sont pas acceptées : envoie une photo fixe.")
            image.load()
            redressee = ImageOps.exif_transpose(image)
    except Image.DecompressionBombError:
        raise ImageRefusee("Cette photo est trop grande : réduis-la avant de l'envoyer.") from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as erreur:
        if isinstance(erreur, ImageRefusee):
            raise
        raise ImageRefusee("Ce fichier n'est pas une photo lisible.") from None
    mode = "RGBA" if "A" in redressee.getbands() or "transparency" in redressee.info else "RGB"
    redressee = redressee.convert(mode)
    return ImagesPreparees(grande=_encoder(redressee, GRANDE), vignette=_encoder(redressee, VIGNETTE))


async def preparer(octets: bytes) -> ImagesPreparees:
    return await asyncio.to_thread(_preparer, octets)
