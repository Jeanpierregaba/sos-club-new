"""Stockage sur disque et préparation des photos (spec 024, ADR-0010)."""

import asyncio
import io
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image

from app.fichiers import images
from app.fichiers.stockage import CleInvalide, Disque


def photo(format: str = "JPEG", taille: tuple[int, int] = (800, 600), **options: object) -> bytes:
    sortie = io.BytesIO()
    mode = "RGBA" if format == "PNG" else "RGB"
    Image.new(mode, taille, (200, 80, 40, 128) if mode == "RGBA" else (200, 80, 40)).save(sortie, format, **options)
    return sortie.getvalue()


def photo_avec_gps(orientation: int = 1, taille: tuple[int, int] = (800, 600)) -> bytes:
    exif = Image.Exif()
    exif[0x0112] = orientation  # Orientation
    exif[0x010F] = "Fabricant"  # Make
    gps = exif.get_ifd(0x8825)
    gps[1] = "N"
    gps[2] = (6.0, 8.0, 0.0)
    return photo("JPEG", taille, exif=exif)


def test_le_disque_enregistre_lit_et_supprime(tmp_path: Path) -> None:
    disque = Disque(tmp_path)
    cle = f"photos/{uuid4()}-grande.webp"

    asyncio.run(disque.enregistrer(cle, b"octets"))
    assert asyncio.run(disque.lire(cle)) == b"octets"
    # Aucun fichier temporaire ne reste à côté.
    assert [p.name for p in (tmp_path / "photos").iterdir()] == [cle.split("/")[1]]

    asyncio.run(disque.supprimer(cle))
    assert asyncio.run(disque.lire(cle)) is None
    asyncio.run(disque.supprimer(cle))


@pytest.mark.parametrize("cle", ["../secret.webp", "photos/../../x.webp", "photos/nom-choisi.webp", "photos/x.png"])
def test_une_cle_hors_format_est_refusee(tmp_path: Path, cle: str) -> None:
    with pytest.raises(CleInvalide):
        asyncio.run(Disque(tmp_path).enregistrer(cle, b"x"))


def test_une_photo_perd_toutes_ses_metadonnees_et_se_redresse() -> None:
    # Orientation 6 : la photo du téléphone doit pivoter d'un quart de tour.
    preparees = asyncio.run(images.preparer(photo_avec_gps(orientation=6)))

    with Image.open(io.BytesIO(preparees.grande.octets)) as resultat:
        assert resultat.format == "WEBP"
        assert resultat.size == (600, 800)
        assert not resultat.getexif()
        assert "exif" not in resultat.info and "xmp" not in resultat.info and "icc_profile" not in resultat.info
    assert b"Fabricant" not in preparees.grande.octets


def test_une_grande_photo_est_reduite_et_a_une_vignette() -> None:
    preparees = asyncio.run(images.preparer(photo(taille=(4000, 3000))))

    assert (preparees.grande.largeur, preparees.grande.hauteur) == (1600, 1200)
    assert (preparees.vignette.largeur, preparees.vignette.hauteur) == (480, 360)


def test_un_png_transparent_garde_sa_transparence() -> None:
    preparees = asyncio.run(images.preparer(photo("PNG")))

    with Image.open(io.BytesIO(preparees.grande.octets)) as resultat:
        assert resultat.mode == "RGBA"


@pytest.mark.parametrize(
    "contenu",
    [
        b"%PDF-1.4 pas une image",
        b"\xff\xd8\xff\xe0 un faux JPEG",
        photo("GIF"),
        photo("BMP"),
    ],
)
def test_un_fichier_qui_nest_pas_une_photo_acceptee_est_refuse(contenu: bytes) -> None:
    with pytest.raises(images.ImageRefusee):
        asyncio.run(images.preparer(contenu))


def test_une_image_animee_est_refusee() -> None:
    sortie = io.BytesIO()
    cadres = [Image.new("RGB", (50, 50), couleur) for couleur in ("red", "blue")]
    cadres[0].save(sortie, "WEBP", save_all=True, append_images=cadres[1:])

    with pytest.raises(images.ImageRefusee, match="animées"):
        asyncio.run(images.preparer(sortie.getvalue()))


def test_une_bombe_de_decompression_est_refusee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1000)

    with pytest.raises(images.ImageRefusee, match="trop grande"):
        asyncio.run(images.preparer(photo(taille=(100, 100))))


def test_une_image_juste_au_dessus_de_la_limite_est_refusee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 9000)

    with pytest.raises(images.ImageRefusee, match="trop grande"):
        asyncio.run(images.preparer(photo(taille=(100, 100))))


def test_un_jpeg_multi_images_de_telephone_est_accepte() -> None:
    sortie = io.BytesIO()
    cadres = [Image.new("RGB", (800, 600), couleur) for couleur in ("green", "black")]
    cadres[0].save(sortie, "MPO", save_all=True, append_images=cadres[1:])
    with Image.open(io.BytesIO(sortie.getvalue())) as essai:
        assert essai.format == "MPO"

    preparees = asyncio.run(images.preparer(sortie.getvalue()))

    assert (preparees.grande.largeur, preparees.grande.hauteur) == (800, 600)


def test_un_exif_malforme_donne_un_refus_et_non_une_erreur(monkeypatch: pytest.MonkeyPatch) -> None:
    import struct

    def casse(*_: object, **__: object) -> None:
        raise struct.error("EXIF mal formé")

    monkeypatch.setattr(images.ImageOps, "exif_transpose", casse)

    with pytest.raises(images.ImageRefusee, match="lisible"):
        asyncio.run(images.preparer(photo()))
