"""Demande de création d'un club (spec 019, tâche 3) : établissement du compte, nom normalisé, axes, encadreurs,
confirmation, une seule demande en attente, rien de public et aucun point."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Club, EtatClub
from app.comptes.models import Role, Utilisateur
from app.points.models import MouvementPoints
from tests.conftest import MOT_DE_PASSE, Navigateur, etablissement_de

DEMANDE = "/api/clubs/demande"
MON_CLUB = "/api/clubs/moi"
AXE = "sante-environnement"


def connecter(client: TestClient, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


def corps(**champs: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "nom": "Club Santé de Tokoin",
        "description": "Promouvoir la santé au lycée.",
        "axes": [AXE],
        "encadreurs_associes": [{"nom": "M. Kodjo", "email": "kodjo@ecole.tg"}],
        "confirmation": True,
    }
    base.update(champs)
    return base


@pytest.fixture
def eleve(creer_eleve: Callable[..., Utilisateur], client: TestClient) -> Callable[..., Utilisateur]:
    def creer(identifiant: str = "eleve1", **champs: Any) -> Utilisateur:
        utilisateur = creer_eleve(identifiant, **champs)
        connecter(client, identifiant)
        return utilisateur

    return creer


def club_actif(en_base: Callable[..., Any], eleve: Utilisateur, dre: str = "grand-lome") -> Club:
    etablissement_id = etablissement_de(en_base, dre)

    async def inserer(db: AsyncSession) -> Club:
        club = Club(
            etablissement_id=etablissement_id,
            nom="Club déjà actif",
            nom_normalise="club deja actif",
            demandeur_id=eleve.id,
            president_id=eleve.id,
            etat=EtatClub.actif,
        )
        db.add(club)
        return club

    return en_base(inserer)


def test_une_demande_valide_cree_un_club_en_attente_sans_point_ni_publication(
    client: TestClient, eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    utilisateur = eleve()
    avant = en_base(
        lambda db: db.scalar(select(MouvementPoints.id).where(MouvementPoints.utilisateur_id == utilisateur.id))
    )

    reponse = client.post(DEMANDE, json=corps())

    assert reponse.status_code == 201, reponse.text
    club = reponse.json()
    assert club["etat"] == "en_attente"
    assert club["president"] is False
    assert club["axes"] == [AXE]
    assert club["etablissement"]["dre_code"] == "grand-lome"
    assert club["etablissement"]["nom"]
    assert client.get("/api/clubs").json() == []
    assert client.get(f"/api/clubs/{club['id']}").status_code == 404
    apres = en_base(
        lambda db: db.scalar(select(MouvementPoints.id).where(MouvementPoints.utilisateur_id == utilisateur.id))
    )
    assert avant == apres
    assert client.get(MON_CLUB).json()["club"]["id"] == club["id"]


def test_le_nom_est_normalise_pour_unicite_dans_letablissement(
    client: TestClient, eleve: Callable[..., Utilisateur], creer_eleve: Callable[..., Utilisateur]
) -> None:
    eleve()
    assert client.post(DEMANDE, json=corps(nom="Club Santé de Tokoin")).status_code == 201
    second = Navigateur(client)
    creer_eleve("eleve2", affiche="Kofi Curieux")
    assert (
        second.post("/api/comptes/connexion", json={"identifiant": "eleve2", "mot_de_passe": MOT_DE_PASSE}).status_code
        == 200
    )

    reponse = second.post(DEMANDE, json=corps(nom="  CLUB   Sante de Tokoin "))

    assert reponse.status_code == 409
    assert "déjà demandé" in reponse.json()["detail"]


def test_un_etablissement_qui_a_deja_un_club_actif_refuse_la_demande(
    client: TestClient, eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    utilisateur = eleve()
    club_actif(en_base, utilisateur)

    reponse = client.post(DEMANDE, json=corps(nom="Un autre nom"))

    assert reponse.status_code == 409
    assert "club actif" in reponse.json()["detail"]


def test_un_eleve_ne_peut_avoir_quune_demande_en_attente(client: TestClient, eleve: Callable[..., Utilisateur]) -> None:
    eleve()
    assert client.post(DEMANDE, json=corps()).status_code == 201

    assert client.post(DEMANDE, json=corps(nom="Autre club")).status_code == 409


def test_un_president_dun_club_actif_ne_demande_pas_un_second_club(
    client: TestClient, eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    """Président d'un club d'un autre établissement : refusé par la règle « un seul club présidé »."""
    president = eleve("eleve2", affiche="Kofi Curieux")
    club_actif(en_base, president)

    reponse = client.post(DEMANDE, json=corps(nom="Mon nouveau club"))

    assert reponse.status_code == 409


def test_les_axes_sont_valides(client: TestClient, eleve: Callable[..., Utilisateur]) -> None:
    eleve()
    assert client.post(DEMANDE, json=corps(axes=["a", "b", "c", "d"])).status_code == 422
    assert client.post(DEMANDE, json=corps(axes=["inconnu"])).status_code == 422
    assert client.post(DEMANDE, json=corps(axes=[AXE, AXE])).status_code == 422


def test_les_encadreurs_associes_sont_bornes(client: TestClient, eleve: Callable[..., Utilisateur]) -> None:
    eleve()
    personnes = [{"nom": f"Encadreur {i}"} for i in range(11)]

    assert client.post(DEMANDE, json=corps(encadreurs_associes=personnes)).status_code == 422


def test_la_confirmation_est_obligatoire(client: TestClient, eleve: Callable[..., Utilisateur]) -> None:
    eleve()
    sans = corps()
    sans.pop("confirmation")

    assert client.post(DEMANDE, json=sans).status_code == 422
    assert client.post(DEMANDE, json=corps(confirmation=False)).status_code == 422


def test_letablissement_ne_se_choisit_pas_dans_le_corps(client: TestClient, eleve: Callable[..., Utilisateur]) -> None:
    eleve()

    reponse = client.post(DEMANDE, json=corps(etablissement_id="00000000-0000-7000-8000-000000000000"))

    assert reponse.status_code == 422


def test_un_encadreur_ne_demande_pas_un_club(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur("encadreur1", Role.encadreur, email="encadreur1@ecole.tg")
    connecter(client, "encadreur1")

    assert client.post(DEMANDE, json=corps()).status_code == 403


def test_la_demande_ne_rend_pas_le_president_avant_lactivation(
    client: TestClient, eleve: Callable[..., Utilisateur]
) -> None:
    eleve()
    club = client.post(DEMANDE, json=corps()).json()

    assert club["etat"] == "en_attente"
    assert club["president"] is False
