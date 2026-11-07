"""Centre de notifications (spec 023) : lecture, compteur, marquage, et isolement entre comptes."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Utilisateur
from app.notifications import service
from tests.conftest import MOT_DE_PASSE, Navigateur

NOTIFICATIONS = "/api/notifications"


def connecter(client: Any, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


@pytest.fixture
def notifier(en_base: Callable[..., Any]) -> Callable[..., Any]:
    def creer(utilisateur: Utilisateur, titre: str) -> Any:
        async def inserer(db: AsyncSession) -> Any:
            return service.notifier(db, utilisateur.id, "test", titre, "Un message.", "/mes-articles").id

        return en_base(inserer)

    return creer


def test_un_compte_lit_ses_notifications_de_la_plus_recente_a_la_plus_ancienne(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], notifier: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    notifier(eleve, "Première")
    notifier(eleve, "Seconde")
    connecter(client, "eleve1")

    reponse = client.get(NOTIFICATIONS).json()

    assert [n["titre"] for n in reponse["notifications"]] == ["Seconde", "Première"]
    assert reponse["non_lues"] == 2
    assert client.get(f"{NOTIFICATIONS}/compte").json() == {"non_lues": 2}


def test_marquer_une_puis_toutes_comme_lues_fait_baisser_le_compteur(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], notifier: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    premiere = notifier(eleve, "Première")
    notifier(eleve, "Seconde")
    connecter(client, "eleve1")

    assert client.post(f"{NOTIFICATIONS}/{premiere}/lue").status_code == 204
    assert client.get(f"{NOTIFICATIONS}/compte").json() == {"non_lues": 1}
    # Marquer deux fois ne change rien.
    assert client.post(f"{NOTIFICATIONS}/{premiere}/lue").status_code == 204

    assert client.post(f"{NOTIFICATIONS}/lues").status_code == 204
    reponse = client.get(NOTIFICATIONS).json()
    assert reponse["non_lues"] == 0
    assert all(n["lue"] for n in reponse["notifications"])


def test_personne_ne_lit_ni_ne_marque_les_notifications_dun_autre(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], notifier: Callable[..., Any]
) -> None:
    autre = creer_eleve("eleve2", "Kofi de Kara", dre="kara")
    secrete = notifier(autre, "Pour l'autre")
    creer_eleve()
    connecter(client, "eleve1")

    assert client.get(NOTIFICATIONS).json() == {"notifications": [], "non_lues": 0}
    assert client.post(f"{NOTIFICATIONS}/{secrete}/lue").status_code == 404
    assert client.post(f"{NOTIFICATIONS}/{uuid4()}/lue").status_code == 404
    client.post(f"{NOTIFICATIONS}/lues")

    navigateur = Navigateur(client)
    connecter(navigateur, "eleve2")
    assert navigateur.get(f"{NOTIFICATIONS}/compte").json() == {"non_lues": 1}


def test_il_faut_etre_connecte(client: TestClient) -> None:
    assert client.get(NOTIFICATIONS).status_code == 401
    assert client.get(f"{NOTIFICATIONS}/compte").status_code == 401
