"""Qui voit une photo (spec 024) : écrits avant le code, car une photo d'élève ne doit jamais être visible avant
l'approbation de son article (docs/TESTING.md, modération)."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.comptes.models import Utilisateur
from app.moderation.models import Photo
from tests.conftest import Navigateur, connecter_admin
from tests.photos import (
    ARTICLES,
    FILE,
    MODERATION,
    PUBLICS,
    ajouter,
    champs,
    connecter,
    creer_article,
    decider,
    soumettre,
)

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def auteur(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Navigateur:
    creer_eleve()
    navigateur = Navigateur(client)
    connecter(navigateur, "eleve1")
    return navigateur


@pytest.fixture
def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, "moderateur")  # type: ignore[arg-type]
    return navigateur


def premiere_photo(article: dict[str, Any]) -> str:
    return str(article["photos"][0]["id"])


def publier_avec_photo(auteur: Navigateur, moderateur: Navigateur) -> tuple[str, str, str]:
    article = creer_article(auteur)
    photo = premiere_photo(ajouter(auteur, article["id"], couverture=True))
    soumettre(auteur, article["id"])
    adresse = decider(moderateur, article["id"], "approuver")["adresse"]
    return article["id"], photo, adresse


def test_lauteur_voit_les_photos_de_son_brouillon_et_personne_dautre(
    client: TestClient, auteur: Navigateur, creer_eleve: Callable[..., Utilisateur]
) -> None:
    article = creer_article(auteur)
    photo = premiere_photo(ajouter(auteur, article["id"]))
    creer_eleve("eleve2", "Kofi de Kara", dre="kara")
    autre = Navigateur(client)
    connecter(autre, "eleve2")

    lue = auteur.get(f"{ARTICLES}/{article['id']}/photos/{photo}/grande")
    vignette = auteur.get(f"{ARTICLES}/{article['id']}/photos/{photo}/vignette")

    assert lue.status_code == 200
    assert lue.headers["content-type"] == "image/webp"
    assert "no-store" in lue.headers["cache-control"]
    assert lue.headers["x-content-type-options"] == "nosniff"
    assert vignette.status_code == 200 and len(vignette.content) < len(lue.content)
    assert autre.get(f"{ARTICLES}/{article['id']}/photos/{photo}/grande").status_code == 404
    assert client.get(f"{ARTICLES}/{article['id']}/photos/{photo}/grande").status_code == 401


def test_le_public_ne_voit_aucune_photo_avant_lapprobation(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    article = creer_article(auteur)
    photo = premiere_photo(ajouter(auteur, article["id"]))
    soumettre(auteur, article["id"])

    # Aucune adresse publique n'existe encore : même une adresse devinée ne donne rien.
    assert client.get(f"{PUBLICS}/le-lavage-des-mains-au-lycee/photos/{photo}/grande").status_code == 404
    assert moderateur.get(f"{FILE}/{article['id']}/photos/{photo}/grande").status_code == 200


def test_une_photo_publiee_se_lit_et_se_garde_en_cache(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    _, photo, adresse = publier_avec_photo(auteur, moderateur)

    lue = client.get(f"{PUBLICS}/{adresse}/photos/{photo}/grande")

    assert lue.status_code == 200
    assert lue.headers["content-type"] == "image/webp"
    assert "immutable" in lue.headers["cache-control"] and "public" in lue.headers["cache-control"]
    article = client.get(f"{PUBLICS}/{adresse}").json()
    assert article["couverture"]["id"] == photo


def test_une_photo_ajoutee_dans_une_revision_reste_privee_jusqua_lapprobation(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    article_id, ancienne, adresse = publier_avec_photo(auteur, moderateur)
    nouvelle = next(p["id"] for p in ajouter(auteur, article_id)["photos"] if p["id"] != ancienne)
    soumettre(auteur, article_id)

    assert client.get(f"{PUBLICS}/{adresse}/photos/{nouvelle}/grande").status_code == 404
    assert client.get(f"{PUBLICS}/{adresse}/photos/{ancienne}/grande").status_code == 200
    assert [p["id"] for p in client.get(f"{PUBLICS}/{adresse}").json()["photos"]] == []

    decider(moderateur, article_id, "approuver")

    assert client.get(f"{PUBLICS}/{adresse}/photos/{nouvelle}/grande").status_code == 200


def test_une_photo_retiree_dans_une_revision_reste_en_ligne_jusqua_lapprobation(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    article_id, photo, adresse = publier_avec_photo(auteur, moderateur)
    version = auteur.get(f"{ARTICLES}/{article_id}").json()["version"]
    retrait = auteur.delete(f"{ARTICLES}/{article_id}/photos/{photo}", params={"version": version})
    assert retrait.status_code == 200, retrait.text
    soumettre(auteur, article_id)

    assert client.get(f"{PUBLICS}/{adresse}/photos/{photo}/grande").status_code == 200

    decider(moderateur, article_id, "approuver")

    assert client.get(f"{PUBLICS}/{adresse}/photos/{photo}/grande").status_code == 404
    assert client.get(f"{PUBLICS}/{adresse}").json()["couverture"] is None


def test_les_photos_dun_article_depublie_ne_sont_plus_publiques(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    article_id, photo, adresse = publier_avec_photo(auteur, moderateur)

    decider(moderateur, article_id, "depublier", "Signalé.")

    assert client.get(f"{PUBLICS}/{adresse}/photos/{photo}/grande").status_code == 404
    # L'auteur et le modérateur la voient encore.
    assert auteur.get(f"{ARTICLES}/{article_id}/photos/{photo}/grande").status_code == 200
    assert moderateur.get(f"{FILE}/{article_id}/photos/{photo}/grande").status_code == 200


def test_une_photo_dun_autre_article_ne_se_lit_pas_par_ladresse_dun_article_publie(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    _, _, adresse = publier_avec_photo(auteur, moderateur)
    brouillon = creer_article(auteur, titre="Un autre article")
    privee = premiere_photo(ajouter(auteur, brouillon["id"]))

    assert client.get(f"{PUBLICS}/{adresse}/photos/{privee}/grande").status_code == 404
    assert client.get(f"{PUBLICS}/{adresse}/photos/{uuid4()}/grande").status_code == 404


def test_un_moderateur_hors_perimetre_ou_sans_droit_ne_voit_pas_la_photo(
    client: TestClient, auteur: Navigateur, creer_collaborateur: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    photo = premiere_photo(ajouter(auteur, article["id"]))
    soumettre(auteur, article["id"])
    creer_collaborateur("moderateur.kara", droits=MODERATION, perimetre_dre="kara", double_auth=True)
    kara = Navigateur(client)
    connecter_admin(kara, "moderateur.kara")  # type: ignore[arg-type]
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})
    autre = Navigateur(client)
    connecter_admin(autre, "autre")  # type: ignore[arg-type]

    assert kara.get(f"{FILE}/{article['id']}/photos/{photo}/grande").status_code == 404
    assert autre.get(f"{FILE}/{article['id']}/photos/{photo}/grande").status_code == 403


def test_une_photo_effacee_ou_une_taille_inconnue_repond_404(auteur: Navigateur, en_base: Callable[..., Any]) -> None:
    article = creer_article(auteur)
    photo = premiere_photo(ajouter(auteur, article["id"]))

    assert auteur.get(f"{ARTICLES}/{article['id']}/photos/{photo}/originale").status_code in {404, 422}
    en_base(lambda db: db.execute(update(Photo).values(efface_le=Photo.cree_le)))
    assert auteur.get(f"{ARTICLES}/{article['id']}/photos/{photo}/grande").status_code == 404


def test_un_brouillon_dun_article_publie_montre_ses_nouvelles_photos_a_lauteur_seulement(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    article_id, ancienne, adresse = publier_avec_photo(auteur, moderateur)
    actuel = auteur.get(f"{ARTICLES}/{article_id}").json()
    auteur.request("PATCH", f"{ARTICLES}/{article_id}", json=champs(titre="Brouillon") | {"version": actuel["version"]})
    nouvelle = next(p["id"] for p in ajouter(auteur, article_id)["photos"] if p["id"] != ancienne)

    assert auteur.get(f"{ARTICLES}/{article_id}/photos/{nouvelle}/grande").status_code == 200
    assert client.get(f"{PUBLICS}/{adresse}/photos/{nouvelle}/grande").status_code == 404


def test_un_moderateur_ne_voit_pas_une_photo_dune_version_de_travail(
    auteur: Navigateur, moderateur: Navigateur
) -> None:
    brouillon = creer_article(auteur)
    jamais_soumise = premiere_photo(ajouter(auteur, brouillon["id"]))
    article_id, en_ligne, _ = publier_avec_photo(auteur, moderateur)
    en_travail = next(p["id"] for p in ajouter(auteur, article_id)["photos"] if p["id"] != en_ligne)

    assert moderateur.get(f"{FILE}/{brouillon['id']}/photos/{jamais_soumise}/grande").status_code == 404
    assert moderateur.get(f"{FILE}/{article_id}/photos/{en_travail}/grande").status_code == 404
    assert moderateur.get(f"{FILE}/{article_id}/photos/{en_ligne}/grande").status_code == 200


def test_un_fichier_absent_du_disque_donne_404_et_larticle_reste_lisible(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur, dossier_fichiers: Any
) -> None:
    _, photo, adresse = publier_avec_photo(auteur, moderateur)
    for fichier in (dossier_fichiers / "photos").glob("*.webp"):
        fichier.unlink()

    assert client.get(f"{PUBLICS}/{adresse}/photos/{photo}/grande").status_code == 404
    assert client.get(f"{PUBLICS}/{adresse}").status_code == 200


def test_seules_les_photos_publiques_gardent_leur_cache(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    _, _, adresse = publier_avec_photo(auteur, moderateur)

    assert client.get(f"{PUBLICS}/{adresse}").headers["cache-control"] == "no-store"
    assert client.get(PUBLICS).headers["cache-control"] == "no-store"
