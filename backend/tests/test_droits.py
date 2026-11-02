from collections.abc import Callable

from fastapi.testclient import TestClient

from app.comptes.models import Role, Utilisateur
from tests.test_connexion import se_connecter

CHIFFRES = "/api/admin/chiffres"


def test_visiteur_refuse(client: TestClient) -> None:
    assert client.get(CHIFFRES).status_code == 401


def test_eleve_refuse(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur()
    se_connecter(client)

    assert client.get(CHIFFRES).status_code == 403


def test_encadreur_refuse(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur(role=Role.encadreur, email="prof@ecole.tg")
    se_connecter(client)

    assert client.get(CHIFFRES).status_code == 403


def test_admin_voit_le_nombre_de_comptes_par_role(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("chef", Role.admin, email="admin@ecole.tg")
    creer_utilisateur("eleve1")
    creer_utilisateur("eleve2")
    se_connecter(client, "chef")

    reponse = client.get(CHIFFRES)

    assert reponse.status_code == 200
    assert reponse.json() == {"comptes": {"eleve": 2, "encadreur": 0, "admin": 1}}
