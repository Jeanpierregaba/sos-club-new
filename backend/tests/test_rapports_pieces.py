# ruff: noqa: F811
"""Justificatifs des rapports (spec 038) : types reconnus au contenu, Word sans macro ni bombe ZIP, attestation des
photos, limites, et lecture réservée aux lecteurs du rapport. Partie critique, écrite avant le code."""

import io
import zipfile
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.comptes.models import Utilisateur
from tests.bibliotheque import image, pdf
from tests.espace_club import connecter
from tests.test_rapports import RAPPORTS, brouillon, club, complet, soumettre  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

CONTENT_TYPES = (
    '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
    'wordprocessingml.document.main+xml"/></Types>'
)


def docx(*, macro: bool = False, bombe: bool = False, sans_document: bool = False) -> bytes:
    sortie = io.BytesIO()
    with zipfile.ZipFile(sortie, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml", CONTENT_TYPES.replace("main+xml", "macroEnabled+xml") if macro else CONTENT_TYPES
        )
        if not sans_document:
            archive.writestr("word/document.xml", "<w:document/>")
        if macro:
            archive.writestr("word/vbaProject.bin", b"\x00" * 100)
        if bombe:
            archive.writestr("word/media/rien.txt", b"0" * (5 * 1024 * 1024))
    return sortie.getvalue()


def envoyer(navigateur: Any, rapport: dict, octets: bytes, nom: str = "compte-rendu.pdf") -> Any:
    return navigateur.post(
        f"{RAPPORTS}/{rapport['id']}/documents",
        data={"version": str(rapport["version"])},
        files={"fichier": (nom, octets, "application/octet-stream")},
    )


def photo(navigateur: Any, rapport: dict, *, attestation: bool = True) -> Any:
    return navigateur.post(
        f"{RAPPORTS}/{rapport['id']}/photos",
        data={"version": str(rapport["version"]), "attestation": "true" if attestation else "false"},
        files={"fichier": ("activite.jpg", image(), "image/jpeg")},
    )


def test_un_pdf_et_un_word_sont_joints_et_relus_en_piece_jointe(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof, donnees=complet())

    rapport = envoyer(prof, rapport, pdf(), "Compte rendu été.pdf").json()
    reponse = envoyer(prof, rapport, docx(), "liste.docx")

    assert reponse.status_code == 200, reponse.text
    documents = reponse.json()["documents"]
    assert [(d["nom"], d["type"]) for d in documents] == [("Compte rendu ete.pdf", "pdf"), ("liste.docx", "docx")]
    lu = prof.get(f"{RAPPORTS}/{rapport['id']}/documents/{documents[1]['id']}")
    assert lu.status_code == 200
    assert lu.headers["content-disposition"].startswith("attachment")
    assert lu.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    ("octets", "nom"),
    [
        (docx(macro=True), "macro.docx"),
        (docx(bombe=True), "bombe.docx"),
        (docx(sans_document=True), "faux.docx"),
        (b"MZ\x90\x00 executable", "programme.pdf"),
        (pdf(javascript=True), "piege.pdf"),
        (image(), "photo.pdf"),
    ],
)
def test_un_document_dangereux_ou_dun_autre_type_est_refuse(
    client: TestClient, club: dict[str, Any], octets: bytes, nom: str
) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)

    assert envoyer(prof, rapport, octets, nom).status_code == 422


def test_un_document_trop_lourd_est_refuse(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)

    assert envoyer(prof, rapport, b"%PDF-" + b"0" * (10 * 1024 * 1024)).status_code == 422


def test_six_documents_cest_trop(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)
    for _ in range(5):
        rapport = envoyer(prof, rapport, pdf()).json()

    assert envoyer(prof, rapport, pdf()).status_code == 409


def test_une_photo_exige_lattestation(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)

    assert photo(prof, rapport, attestation=False).status_code == 422
    ajoutee = photo(prof, rapport)
    assert ajoutee.status_code == 200, ajoutee.text
    (vue,) = ajoutee.json()["photos"]
    assert prof.get(f"{RAPPORTS}/{rapport['id']}/photos/{vue['id']}/vignette").status_code == 200


def test_les_justificatifs_suivent_les_droits_du_rapport(
    client: TestClient, club: dict[str, Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    prof = connecter(client, "prof")
    rapport = envoyer(prof, brouillon(prof, donnees=complet()), pdf()).json()
    rapport = photo(prof, rapport).json()
    document, image_ = rapport["documents"][0]["id"], rapport["photos"][0]["id"]
    adresses = (
        f"{RAPPORTS}/{rapport['id']}/documents/{document}",
        f"{RAPPORTS}/{rapport['id']}/photos/{image_}/grande",
    )

    # Brouillon : l'auteur seul.
    for autre in ("collegue", "presidente", "ailleurs"):
        for adresse in adresses:
            assert connecter(client, autre).get(adresse).status_code == 404
    soumettre(prof, rapport)
    for lecteur in ("collegue", "presidente"):
        for adresse in adresses:
            assert connecter(client, lecteur).get(adresse).status_code == 200
    creer_eleve("membre", "Yao")
    for intrus in ("ailleurs", "membre"):
        for adresse in adresses:
            assert connecter(client, intrus).get(adresse).status_code == 404
    for adresse in adresses:
        assert client.get(adresse).status_code == 401
