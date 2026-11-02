from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.comptes.models import Utilisateur
from app.config import settings
from tests.conftest import MOT_DE_PASSE
from tests.test_connexion import CONNEXION, se_connecter

IDENTIFIANTS = {"identifiant": "jeank", "mot_de_passe": MOT_DE_PASSE}


@pytest.mark.parametrize("origine", ["https://autre-site.tg", "null", "http://localhost:3000.autre-site.tg"])
def test_ecriture_d_une_autre_origine_refusee(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], origine: str
) -> None:
    creer_utilisateur()

    reponse = client.post(CONNEXION, json=IDENTIFIANTS, headers={"origin": origine})

    assert reponse.status_code == 403
    assert "set-cookie" not in reponse.headers


def test_deconnexion_d_une_autre_origine_refusee(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur()
    se_connecter(client)

    assert client.post("/api/comptes/deconnexion", headers={"origin": "https://autre-site.tg"}).status_code == 403
    assert client.get("/api/comptes/moi").status_code == 200


def test_ecriture_depuis_le_site_acceptee(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur()

    assert client.post(CONNEXION, json=IDENTIFIANTS, headers={"origin": settings.site_origine}).status_code == 200


def test_ecriture_sans_origine_acceptee(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur()

    assert client.post(CONNEXION, json=IDENTIFIANTS).status_code == 200


def test_lecture_d_une_autre_origine_sans_contrainte(client: TestClient) -> None:
    # La lecture ne modifie rien, et le navigateur empêche l'autre site de lire la réponse.
    assert client.get("/api/comptes/moi", headers={"origin": "https://autre-site.tg"}).status_code == 401
