"""Contrôle des PDF déposés dans la bibliothèque (spec 028) et lecture en flux du stockage (ADR-0010)."""

import asyncio
import io
from pathlib import Path
from uuid import uuid4

import pytest
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, TextStringObject

from app.fichiers import pdf
from app.fichiers.stockage import CleInvalide, Disque


def ecrire(writer: PdfWriter) -> bytes:
    sortie = io.BytesIO()
    writer.write(sortie)
    return sortie.getvalue()


def document(pages: int = 1) -> PdfWriter:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    return writer


def test_un_pdf_sain_est_accepte_avec_son_nombre_de_pages() -> None:
    assert pdf.verifier(ecrire(document(3))).pages == 3


@pytest.mark.parametrize(
    "octets",
    [
        b"",
        b"Bonjour, je ne suis pas un PDF.",
        b"\x89PNG\r\n\x1a\n" + b"\x00" * 64,
        b"%PDF-1.7\n" + b"\x00" * 64,
    ],
    ids=["vide", "texte", "image", "en-tete-seul"],
)
def test_ce_qui_nest_pas_un_pdf_lisible_est_refuse(octets: bytes) -> None:
    with pytest.raises(pdf.PdfRefuse):
        pdf.verifier(octets)


def test_un_pdf_tronque_est_refuse() -> None:
    octets = ecrire(document(2))

    with pytest.raises(pdf.PdfRefuse):
        pdf.verifier(octets[: len(octets) // 3])


def test_un_pdf_sans_page_est_refuse() -> None:
    with pytest.raises(pdf.PdfRefuse, match="page"):
        pdf.verifier(ecrire(PdfWriter()))


def test_un_pdf_avec_du_javascript_est_refuse() -> None:
    writer = document()
    writer._root_object[NameObject("/OpenAction")] = DictionaryObject(
        {NameObject("/S"): NameObject("/JavaScript"), NameObject("/JS"): TextStringObject("app.alert('coucou');")}
    )

    with pytest.raises(pdf.PdfRefuse, match="JavaScript"):
        pdf.verifier(ecrire(writer))


def test_du_javascript_cache_dans_une_page_est_refuse() -> None:
    writer = document()
    action = DictionaryObject({NameObject("/S"): NameObject("/JavaScript"), NameObject("/JS"): TextStringObject("1")})
    writer.pages[0][NameObject("/AA")] = DictionaryObject({NameObject("/O"): writer._add_object(action)})

    with pytest.raises(pdf.PdfRefuse):
        pdf.verifier(ecrire(writer))


def test_une_action_de_lancement_est_refusee() -> None:
    writer = document()
    writer._root_object[NameObject("/OpenAction")] = DictionaryObject(
        {NameObject("/S"): NameObject("/Launch"), NameObject("/F"): TextStringObject("calc.exe")}
    )

    with pytest.raises(pdf.PdfRefuse):
        pdf.verifier(ecrire(writer))


def test_un_fichier_joint_est_refuse() -> None:
    writer = document()
    writer.add_attachment("joint.exe", b"MZ\x90\x00")

    with pytest.raises(pdf.PdfRefuse, match="joint"):
        pdf.verifier(ecrire(writer))


def test_un_pdf_chiffre_est_refuse() -> None:
    writer = document()
    writer.encrypt("secret", algorithm="RC4-128")

    with pytest.raises(pdf.PdfRefuse, match="protégé"):
        pdf.verifier(ecrire(writer))


def test_un_lien_vers_un_site_reste_permis() -> None:
    writer = document()
    lien = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject([]),
            NameObject("/A"): DictionaryObject(
                {NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject("https://sosdocteur.tv")}
            ),
        }
    )
    writer.pages[0][NameObject("/Annots")] = ArrayObject([writer._add_object(lien)])

    assert pdf.verifier(ecrire(writer)).pages == 1


def test_un_pdf_trop_complexe_est_refuse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdf, "NOEUDS_MAX", 5)

    with pytest.raises(pdf.PdfRefuse, match="complexe"):
        pdf.verifier(ecrire(document(10)))


def test_la_verification_tourne_hors_de_la_boucle() -> None:
    assert asyncio.run(pdf.examiner(ecrire(document()))).pages == 1


# Stockage ---------------------------------------------------------------------------------------------------------


def test_le_disque_garde_un_pdf_et_le_relit_par_morceaux(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Disque, "MORCEAU", 100)
    disque = Disque(tmp_path)
    cle = f"ressources/{uuid4()}-document.pdf"
    octets = ecrire(document(2))

    asyncio.run(disque.enregistrer(cle, octets))

    async def tout_lire() -> tuple[int, list[bytes]]:
        flux = await disque.lire_par_morceaux(cle)
        assert flux is not None
        taille, morceaux = flux
        return taille, [m async for m in morceaux]

    taille, morceaux = asyncio.run(tout_lire())
    assert taille == len(octets)
    assert b"".join(morceaux) == octets
    assert len(morceaux) > 1


def test_un_fichier_absent_se_lit_comme_absent(tmp_path: Path) -> None:
    assert asyncio.run(Disque(tmp_path).lire_par_morceaux(f"ressources/{uuid4()}-document.pdf")) is None


@pytest.mark.parametrize("cle", ["ressources/../secret.pdf", "ressources/x-document.pdf", "ressources/a.exe"])
def test_une_cle_de_pdf_mal_formee_est_refusee(tmp_path: Path, cle: str) -> None:
    with pytest.raises(CleInvalide):
        asyncio.run(Disque(tmp_path).enregistrer(cle, b"%PDF-"))
