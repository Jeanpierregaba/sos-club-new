"""Décisions sur les partages d'articles (spec 044) : +10 ou +50 au registre à l'approbation seulement, part du club,
refus sans point, ni correction ni retrait, droit `partages:approuver` et périmètre DRE.

Écrits avant le code : la modération crédite des points (docs/TESTING.md)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.comptes.models import Utilisateur
from tests.commentaires import (
    FILE,
    MODERATION,
    connecter,
    contenu,
    decider,
    lignes,
    notifications,
    publier_article,
)
from tests.partages import PARTAGES_MOI, declare, moderateur_partages

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def scene(client: TestClient, creer_eleve: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any]) -> Any:
    redactrice = creer_eleve()
    lecteur = creer_eleve("eleve2", affiche="Kofi des Plateaux")
    navigateur_redactrice = connecter(client, "eleve1")
    admin = moderateur_partages(client, creer_collaborateur)
    return {
        "adresse": publier_article(navigateur_redactrice, admin),
        "redactrice": redactrice,
        "lecteur": lecteur,
        "nav_redactrice": navigateur_redactrice,
        "nav_lecteur": connecter(client, "eleve2"),
        "admin": admin,
    }


def _partages(en_base: Callable[..., Any], utilisateur: Utilisateur) -> list[Any]:
    return [g for g in lignes(en_base, utilisateur.id) if g.action.endswith((".partage", ".republication"))]


def test_la_file_montre_le_partage_et_son_lien(scene: Any) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")

    element = next(c for c in scene["admin"].get(FILE).json()["contenus"] if c["id"] == partage["id"])
    apercu = scene["admin"].get(f"{FILE}/{partage['id']}").json()

    assert element["type"] == "partage"
    assert element["titre"] == "Republication sur Facebook"
    assert element["parent"]["adresse"] == scene["adresse"]
    assert apercu["soumise"]["lien"] == partage["lien"]
    assert apercu["soumise"]["nature"] == "republication"
    assert apercu["correction_possible"] is False


def test_une_republication_approuvee_rapporte_dix_points_une_fois(scene: Any, en_base: Callable[..., Any]) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")

    assert decider(scene["admin"], partage["id"], "approuver").status_code == 200

    gains = _partages(en_base, scene["lecteur"])
    assert [(g.action, g.montant) for g in gains] == [("eleve.republication", 10)]
    assert gains[0].cle.startswith("republication:")
    assert any("est validé" in n.titre for n in notifications(en_base, scene["lecteur"].id))
    mien = scene["nav_lecteur"].get(PARTAGES_MOI).json()["partages"][0]
    assert (mien["etat"], mien["points"]) == ("approuve", 10)


def test_lautrice_gagne_cinquante_points_par_reseau(scene: Any, en_base: Callable[..., Any]) -> None:
    for reseau in ("facebook", "instagram"):
        partage = declare(scene["nav_redactrice"], scene["adresse"], reseau)
        assert decider(scene["admin"], partage["id"], "approuver").status_code == 200

    gains = _partages(en_base, scene["redactrice"])
    assert sorted((g.action, g.montant) for g in gains) == [("eleve.partage", 50), ("eleve.partage", 50)]
    assert len({g.cle for g in gains}) == 2


def test_la_part_du_club_suit_la_regle_des_demi_points(
    scene: Any, creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    club = creer_club(scene["lecteur"], nom="Club Santé du Lycée")
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")

    decider(scene["admin"], partage["id"], "approuver")

    gain = _partages(en_base, scene["lecteur"])[0]
    assert (gain.club_id, gain.demi_points_club) == (club.id, 10)
    assert contenu(en_base, partage["id"]).club_beneficiaire_id == club.id


def test_un_refus_ne_rapporte_rien_et_montre_son_motif(scene: Any, en_base: Callable[..., Any]) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")

    assert decider(scene["admin"], partage["id"], "refuser", "Le lien ne s'ouvre pas.").status_code == 200

    assert _partages(en_base, scene["lecteur"]) == []
    mien = scene["nav_lecteur"].get(PARTAGES_MOI).json()["partages"][0]
    assert (mien["etat"], mien["motif"], mien["points"]) == ("refuse", "Le lien ne s'ouvre pas.", None)


def test_un_partage_ne_se_corrige_ni_ne_se_retire(scene: Any) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")

    assert decider(scene["admin"], partage["id"], "corriger", "Autre lien.").status_code == 409
    decider(scene["admin"], partage["id"], "approuver")
    assert decider(scene["admin"], partage["id"], "depublier", "Retrait.").status_code != 200
    assert scene["admin"].get(f"{FILE}/{partage['id']}").json()["etat"] == "publie"


def test_une_deuxieme_approbation_ne_credite_pas_deux_fois(scene: Any, en_base: Callable[..., Any]) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")
    version = scene["admin"].get(f"{FILE}/{partage['id']}").json()["version"]

    premiere = scene["admin"].post(f"{FILE}/{partage['id']}/approuver", json={"version": version})
    seconde = scene["admin"].post(f"{FILE}/{partage['id']}/approuver", json={"version": version})

    assert premiere.status_code == 200
    assert seconde.status_code == 409
    assert len(_partages(en_base, scene["lecteur"])) == 1


def test_un_article_depublie_rend_lapprobation_impossible(scene: Any, en_base: Callable[..., Any]) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")
    article = scene["admin"].get(FILE, params={"etat": "publie"}).json()["contenus"][0]
    assert decider(scene["admin"], article["id"], "depublier", "Retiré pour le test.").status_code == 200

    reponse = decider(scene["admin"], partage["id"], "approuver")

    assert reponse.status_code == 409
    assert "plus en ligne" in reponse.json()["detail"]
    assert _partages(en_base, scene["lecteur"]) == []
    assert scene["admin"].get(f"{FILE}/{partage['id']}").json()["etat"] == "en_attente"


def test_sans_le_droit_des_partages_on_ne_decide_pas(
    client: TestClient, scene: Any, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")
    simple = moderateur_partages(client, creer_collaborateur, "simple", droits=MODERATION)

    assert decider(simple, partage["id"], "approuver").status_code == 403
    assert _partages(en_base, scene["lecteur"]) == []


def test_un_moderateur_dune_autre_dre_ne_voit_pas_le_partage(
    client: TestClient, scene: Any, creer_collaborateur: Callable[..., Any]
) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")
    regional = moderateur_partages(client, creer_collaborateur, "regional", perimetre_dre="kara")

    assert regional.get(f"{FILE}/{partage['id']}").status_code == 404


def test_un_encadreur_gagne_les_points_des_encadreurs(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    encadreur = creer_encadreur()
    navigateur = connecter(client, "encadreur1")
    adresse = publier_article(navigateur, scene["admin"], "Le sommeil des adolescents")
    partage = declare(navigateur, adresse, "linkedin")
    republication = declare(navigateur, scene["adresse"], "facebook", "https://facebook.com/prof/posts/2")

    decider(scene["admin"], partage["id"], "approuver")
    decider(scene["admin"], republication["id"], "approuver")

    assert sorted((g.action, g.montant) for g in _partages(en_base, encadreur)) == [
        ("encadreur.partage", 50),
        ("encadreur.republication", 10),
    ]


def test_le_lien_nest_jamais_public(client: TestClient, scene: Any) -> None:
    partage = declare(scene["nav_lecteur"], scene["adresse"], "facebook")
    decider(scene["admin"], partage["id"], "approuver")
    client.cookies.clear()

    pages = [
        client.get(f"/api/articles/{scene['adresse']}").text,
        client.get("/api/articles").text,
        client.get(f"/api/articles/{scene['adresse']}/commentaires").text,
    ]

    assert all(partage["lien"] not in page and "facebook.com" not in page for page in pages)
