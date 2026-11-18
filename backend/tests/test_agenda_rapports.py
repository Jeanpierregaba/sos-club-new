"""Lien d'un rapport d'activité avec un événement de l'agenda (spec 041, suite de la spec 038) : un événement publié
et commencé de son club, documenté par un seul rapport. Partie critique (pas de double crédit)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.agenda.models import Evenement
from tests.agenda import club, connecter, propose, publie
from tests.test_rapports import RAPPORTS, brouillon, complet

__all__ = ["club"]

pytestmark = pytest.mark.usefixtures("annuaire")


def commencer(en_base: Callable[..., Any], evenement_id: str) -> None:
    debut = datetime.now(UTC) - timedelta(days=1)
    en_base(
        lambda db: db.execute(
            update(Evenement)
            .where(Evenement.id == UUID(evenement_id))
            .values(debut=debut, fin=debut + timedelta(hours=2))
        )
    )


def lier(navigateur: Any, rapport: dict[str, Any], evenement_id: str) -> Any:
    return navigateur.put(
        f"{RAPPORTS}/{rapport['id']}",
        json={"version": rapport["version"], "donnees": complet(evenement_id=evenement_id)},
    )


@pytest.fixture
def evenement(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> dict[str, Any]:
    evenement = publie(client, creer_collaborateur)
    commencer(en_base, evenement["id"])
    return evenement


def test_un_rapport_se_lie_a_un_evenement_de_son_club(client: TestClient, evenement: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)

    reponse = lier(prof, rapport, evenement["id"])

    assert reponse.status_code == 200, reponse.text
    lie = reponse.json()["evenement"]
    assert (lie["id"], lie["titre"], lie["presents"]) == (evenement["id"], "Causerie sur le paludisme", 0)


def test_un_evenement_ne_se_lie_qua_un_seul_rapport(client: TestClient, evenement: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    assert lier(prof, brouillon(prof), evenement["id"]).status_code == 200
    collegue = connecter(client, "collegue")

    reponse = lier(collegue, brouillon(collegue), evenement["id"])

    assert reponse.status_code == 409


def test_un_evenement_dun_autre_club_non_publie_ou_a_venir_est_refuse(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    a_venir = publie(client, creer_collaborateur)
    en_attente = propose(connecter(client, "collegue"))
    ailleurs = connecter(client, "ailleurs")
    autre = brouillon(ailleurs)
    prof = connecter(client, "prof")

    assert lier(prof, brouillon(prof), a_venir["id"]).status_code == 422
    assert lier(prof, brouillon(prof), en_attente["id"]).status_code == 422
    assert lier(ailleurs, autre, a_venir["id"]).status_code == 422


def test_la_soumission_reverifie_levenement_lie(
    client: TestClient, evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    from tests.test_rapports import soumettre

    prof = connecter(client, "prof")
    rapport = lier(prof, brouillon(prof), evenement["id"]).json()
    en_base(lambda db: db.execute(update(Evenement).where(Evenement.id == UUID(evenement["id"])).values(publie=False)))

    assert soumettre(prof, rapport).status_code == 422


def test_un_rapport_refuse_libere_son_evenement(
    client: TestClient, evenement: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    from tests.agenda import decider, moderateur
    from tests.test_rapports import soumettre

    prof = connecter(client, "prof")
    premier = lier(prof, brouillon(prof), evenement["id"]).json()
    assert soumettre(prof, premier).status_code == 200
    equipe = moderateur(client, creer_collaborateur, "equipe-rapports")
    assert decider(equipe, premier["id"], "refuser", "Rapport incomplet, à refaire.").status_code == 200
    collegue = connecter(client, "collegue")

    assert lier(collegue, brouillon(collegue), evenement["id"]).status_code == 200
