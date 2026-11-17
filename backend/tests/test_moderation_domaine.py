"""Ajouts au moteur de modération pour l'agenda (spec 041) : un droit propre au type, et des crochets appelés à
chaque approbation et au retrait du site. Testés sur l'article, déclaré le temps du test avec le domaine « agenda »."""

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.moderation.models import Contenu
from app.moderation.types import TYPES
from tests.conftest import Navigateur, connecter_admin
from tests.test_moderation_decisions import FILE, MODERATION, auteur, decider, reviser, soumettre

__all__ = ["auteur"]

pytestmark = pytest.mark.usefixtures("annuaire")

AGENDA = {("agenda", "approuver"), ("agenda", "depublier")}


@pytest.fixture
def appels(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Any]]:
    """L'article prend le domaine « agenda » et des crochets espions."""
    journal: list[tuple[str, Any]] = []

    async def a_chaque_approbation(db: AsyncSession, contenu: Contenu, donnees: dict[str, Any], premiere: bool) -> None:
        journal.append(("approbation", (donnees["titre"], premiere)))

    async def au_retrait(db: AsyncSession, contenu: Contenu) -> None:
        journal.append(("retrait", contenu.id))

    monkeypatch.setitem(
        TYPES,
        "article",
        replace(
            TYPES["article"],
            domaine_droit="agenda",
            a_chaque_approbation=a_chaque_approbation,
            au_retrait=au_retrait,
        ),
    )
    return journal


def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any], identifiant: str, droits: set[Any]) -> None:
    creer_collaborateur(identifiant, droits=droits, double_auth=True)
    assert connecter_admin(client, identifiant).status_code == 200


def test_sans_le_droit_du_domaine_on_lit_sans_decider(
    client: TestClient, auteur: Navigateur, creer_collaborateur: Callable[..., Any], appels: list[Any]
) -> None:
    article = soumettre(auteur)
    moderateur(client, creer_collaborateur, "moderateur", MODERATION)

    file = client.get(FILE).json()["contenus"]
    assert [(c["id"], c["decision_possible"]) for c in file] == [(article["id"], False)]
    assert client.get(f"{FILE}/{article['id']}").json()["decision_possible"] is False
    reponse = decider(client, article["id"], "approuver")
    assert reponse.status_code == 403
    assert "type de contenu" in reponse.json()["detail"]
    assert decider(client, article["id"], "refuser", "Hors sujet pour le club").status_code == 403
    assert appels == []


def test_avec_le_droit_du_domaine_chaque_approbation_appelle_le_crochet(
    client: TestClient, auteur: Navigateur, creer_collaborateur: Callable[..., Any], appels: list[Any]
) -> None:
    article = soumettre(auteur)
    moderateur(client, creer_collaborateur, "agendiste", MODERATION | AGENDA)

    assert client.get(f"{FILE}/{article['id']}").json()["decision_possible"] is True
    assert decider(client, article["id"], "approuver").status_code == 200
    reviser(auteur, article["id"], titre="Le lavage des mains, deuxième édition")
    assert decider(client, article["id"], "approuver").status_code == 200

    assert appels == [
        ("approbation", ("Le lavage des mains au lycée", True)),
        ("approbation", ("Le lavage des mains, deuxième édition", False)),
    ]


def test_retirer_exige_le_droit_du_domaine_et_appelle_le_crochet(
    client: TestClient, auteur: Navigateur, creer_collaborateur: Callable[..., Any], appels: list[Any]
) -> None:
    article = soumettre(auteur)
    moderateur(client, creer_collaborateur, "approbateur", MODERATION | {("agenda", "approuver")})
    assert decider(client, article["id"], "approuver").status_code == 200

    assert decider(client, article["id"], "depublier", "Contenu signalé").status_code == 403
    moderateur(client, creer_collaborateur, "agendiste", MODERATION | AGENDA)
    assert decider(client, article["id"], "depublier", "Contenu signalé").status_code == 200

    assert [nom for nom, _ in appels] == ["approbation", "retrait"]


def test_un_type_sans_domaine_ne_change_pas(
    client: TestClient, auteur: Navigateur, creer_collaborateur: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    moderateur(client, creer_collaborateur, "moderateur", MODERATION)

    assert client.get(FILE).json()["contenus"][0]["decision_possible"] is True
    assert decider(client, article["id"], "approuver").status_code == 200
