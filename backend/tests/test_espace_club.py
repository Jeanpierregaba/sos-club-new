"""Vue « Mon club » (spec 026) : le président gère, les membres et les encadreurs rattachés lisent, les autres ne
voient rien.

Écrits avant le code : les droits se vérifient dans l'API pour chaque route (ADR-0003, docs/TESTING.md)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.clubs.models import Adhesion, EtatAdhesion
from tests.espace_club import ACTUALITES, FICHE, adherer, champs_actualite, espace, scene

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def club(
    client: TestClient,
    creer_eleve: Callable[..., Any],
    creer_club: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    return scene(client, creer_eleve, creer_club, creer_encadreur, creer_collaborateur, en_base)


def test_le_president_voit_la_gestion(
    club: dict[str, Any], creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    # Spec 033 : une affiliation à confirmer ne compte pas parmi les membres, et le président ne la traite plus.
    demandeur = creer_eleve("demandeur", "Yao Sportif", etablissement_id=club["club"].etablissement_id)
    adherer(en_base, demandeur, club["club"], EtatAdhesion.en_attente_validation)

    reponse = club["nav_president"].get(espace(club["club"].id))

    assert reponse.status_code == 200, reponse.text
    vue = reponse.json()
    assert vue["role"] == "president"
    assert vue["club"]["nom"] == "Club Santé du Lycée"
    assert vue["club"]["id"] == str(club["club"].id)
    assert vue["indicateurs"]["membres"] == 2  # le président et Ama
    assert vue["indicateurs"]["encadreurs"] == 1
    assert vue["indicateurs"]["actualites"] == 0
    assert "demandes" not in vue and "demandes" not in vue["indicateurs"]
    assert vue["statut"] == "actif"
    assert vue["suivi"] == {"propositions": [], "actualites": []}
    assert {m["pseudonyme"] for m in vue["membres"]["membres"]} == {"Zoé la Présidente", "Ama du Golfe"}


@pytest.mark.parametrize(("navigateur", "role"), [("nav_membre", "membre"), ("nav_encadreur", "encadreur")])
def test_un_membre_et_un_encadreur_rattache_lisent_sans_gestion(
    club: dict[str, Any], navigateur: str, role: str
) -> None:
    reponse = club[navigateur].get(espace(club["club"].id))

    assert reponse.status_code == 200, reponse.text
    vue = reponse.json()
    assert vue["role"] == role
    assert vue["suivi"] is None
    assert vue["statut"] == "actif"
    assert vue["club"]["nom"] == "Club Santé du Lycée"
    assert len(vue["membres"]["membres"]) == 2


def test_un_eleve_exterieur_et_un_visiteur_ne_voient_rien(client: TestClient, club: dict[str, Any]) -> None:
    assert club["nav_exterieur"].get(espace(club["club"].id)).status_code == 404
    client.cookies.clear()
    assert client.get(espace(club["club"].id)).status_code == 401


def test_un_membre_retire_perd_la_vue(club: dict[str, Any], en_base: Callable[..., Any]) -> None:
    en_base(
        lambda db: db.execute(
            update(Adhesion).where(Adhesion.eleve_id == club["membre"].id).values(etat=EtatAdhesion.retiree)
        )
    )

    assert club["nav_membre"].get(espace(club["club"].id)).status_code == 404


def test_un_club_inexistant_repond_404(club: dict[str, Any]) -> None:
    assert club["nav_president"].get(espace("0190a7f0-0000-7000-8000-000000000000")).status_code == 404


@pytest.mark.parametrize("navigateur", ["nav_membre", "nav_encadreur", "nav_exterieur"])
def test_les_actions_de_gestion_sont_refusees_aux_autres(club: dict[str, Any], navigateur: str) -> None:
    proposition = club[navigateur].post(FICHE, json={"description": "Pirate", "axes": ["sante-environnement"]})
    actualite = club[navigateur].post(ACTUALITES, json=champs_actualite())

    assert proposition.status_code in {403, 404}
    assert actualite.status_code in {403, 404}
    assert club[navigateur].get(ACTUALITES).status_code in {403, 404}
