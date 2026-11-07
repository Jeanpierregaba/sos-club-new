"""Aides partagées des tests des photos (spec 024)."""

import io
from typing import Any

from PIL import Image

from tests.conftest import MOT_DE_PASSE

ARTICLES = "/api/mes-articles"
FILE = "/api/admin/moderation"
PUBLICS = "/api/articles"
MODERATION = {("moderation", "consulter"), ("moderation", "approuver"), ("moderation", "depublier")}


def connecter(client: Any, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


def champs(**autres: Any) -> dict[str, Any]:
    return {
        "titre": "Le lavage des mains au lycée",
        "chapo": "Notre club a installé trois points d'eau dans la cour.",
        "texte": "Parce que **les mains** transportent les microbes.",
        "axe_code": "sante-environnement",
        "afficher_club": True,
    } | autres


def image(format: str = "JPEG", taille: tuple[int, int] = (800, 600)) -> bytes:
    sortie = io.BytesIO()
    Image.new("RGB", taille, (30, 120, 200)).save(sortie, format)
    return sortie.getvalue()


def creer_article(auteur: Any, **autres: Any) -> dict[str, Any]:
    reponse = auteur.post(ARTICLES, json=champs(**autres))
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def envoyer(
    auteur: Any,
    article_id: str,
    *,
    version: int | None = None,
    attestation: bool = True,
    contenu: bytes | None = None,
    legende: str | None = "Les élèves au point d'eau",
    couverture: bool = False,
) -> Any:
    if version is None:
        version = auteur.get(f"{ARTICLES}/{article_id}").json()["version"]
    donnees: dict[str, str] = {"version": str(version), "couverture": "true" if couverture else "false"}
    if attestation:
        donnees["attestation"] = "true"
    if legende is not None:
        donnees["legende"] = legende
    return auteur.post(
        f"{ARTICLES}/{article_id}/photos",
        data=donnees,
        files={"fichier": ("photo.jpg", contenu if contenu is not None else image(), "image/jpeg")},
    )


def ajouter(auteur: Any, article_id: str, **options: Any) -> dict[str, Any]:
    reponse = envoyer(auteur, article_id, **options)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def soumettre(auteur: Any, article_id: str) -> dict[str, Any]:
    version = auteur.get(f"{ARTICLES}/{article_id}").json()["version"]
    reponse = auteur.post(f"{ARTICLES}/{article_id}/soumettre", json={"version": version})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def decider(moderateur: Any, contenu_id: str, decision: str, motif: str | None = None) -> dict[str, Any]:
    version = moderateur.get(f"{FILE}/{contenu_id}").json()["version"]
    reponse = moderateur.post(f"{FILE}/{contenu_id}/{decision}", json={"version": version, "motif": motif})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()
