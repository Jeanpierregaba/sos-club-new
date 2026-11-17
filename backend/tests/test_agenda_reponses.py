"""Réponses des membres, liste des réponses et pointage des présents (spec 041).

Partie critique (données d'élèves, places sous concurrence), écrite avant le code (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda import reponses
from app.agenda.models import Evenement, Reponse
from app.clubs.models import Adhesion, EtatAdhesion
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from tests.agenda import CLUB, club, connecter, publie
from tests.conftest import moteur_test
from tests.espace_club import adherer

__all__ = ["club"]

pytestmark = pytest.mark.usefixtures("annuaire")


def repondre(navigateur: Any, evenement_id: str, reponse: str) -> Any:
    return navigateur.put(f"/api/agenda/{evenement_id}/reponse", json={"reponse": reponse})


def commencer(en_base: Callable[..., Any], evenement_id: str, il_y_a: timedelta = timedelta(hours=1)) -> None:
    debut = datetime.now(UTC) - il_y_a
    en_base(
        lambda db: db.execute(
            update(Evenement)
            .where(Evenement.id == UUID(evenement_id))
            .values(debut=debut, fin=debut + timedelta(hours=2))
        )
    )


@pytest.fixture
def evenement(client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]) -> dict[str, Any]:
    return publie(client, creer_collaborateur)


# Réponses ------------------------------------------------------------------------------------------------------


def test_un_membre_repond_et_change_davis(client: TestClient, evenement: dict[str, Any]) -> None:
    membre = connecter(client, "membre")

    assert membre.get(f"/api/agenda/{evenement['id']}").json()["peut_repondre"] is True
    assert repondre(membre, evenement["id"], "participe").json()["ma_reponse"] == "participe"
    vue = repondre(membre, evenement["id"], "peut_etre").json()

    assert (vue["ma_reponse"], vue["participants"]) == ("peut_etre", 0)
    (prochain,) = membre.get("/api/agenda/mes-evenements").json()
    assert prochain["id"] == evenement["id"] and prochain["ma_reponse"] == "peut_etre"


@pytest.mark.parametrize("qui", ["simple", "prof", "ailleurs", "autre-presidente"])
def test_un_non_membre_ne_repond_pas(client: TestClient, evenement: dict[str, Any], qui: str) -> None:
    navigateur = connecter(client, qui)

    assert repondre(navigateur, evenement["id"], "participe").status_code == 403
    assert navigateur.get(f"/api/agenda/{evenement['id']}").json()["peut_repondre"] is False


def test_un_visiteur_anonyme_ne_repond_pas(client: TestClient, evenement: dict[str, Any]) -> None:
    client.cookies.clear()
    assert repondre(client, evenement["id"], "participe").status_code == 401


def test_apres_le_debut_les_reponses_sont_closes(
    client: TestClient, evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    commencer(en_base, evenement["id"])

    reponse = repondre(connecter(client, "membre"), evenement["id"], "participe")

    assert reponse.status_code == 409
    assert "commencé" in reponse.json()["detail"]


def test_un_eleve_qui_rejoint_le_club_peut_repondre(
    client: TestClient, club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    adherer(en_base, club["simple"], club["club"])

    assert repondre(connecter(client, "simple"), evenement["id"], "participe").status_code == 200


def test_un_membre_parti_nest_plus_compte(
    client: TestClient, club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    repondre(connecter(client, "membre"), evenement["id"], "participe")
    assert client.get(f"/api/agenda/{evenement['id']}").json()["participants"] == 1

    en_base(
        lambda db: db.execute(
            update(Adhesion).where(Adhesion.eleve_id == club["membre"].id).values(etat=EtatAdhesion.retiree)
        )
    )

    assert client.get(f"/api/agenda/{evenement['id']}").json()["participants"] == 0
    assert repondre(connecter(client, "membre"), evenement["id"], "participe").status_code == 403


def test_au_dela_des_places_cest_complet(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur, places=1)
    assert repondre(connecter(client, "membre"), evenement["id"], "participe").status_code == 200

    refus = repondre(connecter(client, "membre2"), evenement["id"], "participe")

    assert refus.status_code == 409
    assert "complet" in refus.json()["detail"]
    assert repondre(connecter(client, "membre2"), evenement["id"], "peut_etre").status_code == 200
    vue = client.get(f"/api/agenda/{evenement['id']}").json()
    assert (vue["participants"], vue["complet"]) == (1, True)
    # Celui qui a la place peut confirmer de nouveau sans être refusé.
    assert repondre(connecter(client, "membre"), evenement["id"], "participe").status_code == 200


def test_deux_reponses_simultanees_ne_prennent_pas_deux_fois_la_derniere_place(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur, places=1)

    async def une_reponse(eleve_id: UUID) -> bool:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            eleve = await db.get(Utilisateur, eleve_id)
            assert eleve is not None
            try:
                await reponses.repondre(db, eleve, UUID(evenement["id"]), Reponse.participe)
            except Refus as refus:
                assert refus.statut == 409
                return False
            return True

    async def scenario() -> list[bool]:
        return await asyncio.gather(une_reponse(club["membre"].id), une_reponse(club["membre2"].id))

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert client.get(f"/api/agenda/{evenement['id']}").json()["participants"] == 1


# Liste des réponses et pointage -----------------------------------------------------------------------------


@pytest.mark.parametrize("qui", ["prof", "collegue", "presidente"])
def test_les_gestionnaires_lisent_les_reponses(
    client: TestClient, club: dict[str, Any], evenement: dict[str, Any], qui: str
) -> None:
    repondre(connecter(client, "membre"), evenement["id"], "participe")
    repondre(connecter(client, "membre2"), evenement["id"], "non")

    reponse = connecter(client, qui).get(f"{CLUB}/{evenement['id']}/reponses")

    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["cache-control"] == "no-store"
    corps = reponse.json()
    assert (corps["participe"], corps["non"], corps["sans_reponse"]) == (1, 1, 1)
    attendus = {str(club[nom].id) for nom in ("presidente", "membre", "membre2")}
    assert {m["eleve_id"] for m in corps["membres"]} == attendus


@pytest.mark.parametrize("qui", ["membre", "simple", "ailleurs"])
def test_les_autres_ne_lisent_pas_les_reponses(client: TestClient, evenement: dict[str, Any], qui: str) -> None:
    assert connecter(client, qui).get(f"{CLUB}/{evenement['id']}/reponses").status_code in (403, 404)


def test_le_pointage_souvre_au_debut_et_se_limite_aux_membres(
    client: TestClient, club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    prof = connecter(client, "prof")
    url = f"{CLUB}/{evenement['id']}/presences"
    presences = {str(club["membre"].id): True}

    assert prof.put(url, json={"presences": presences}).status_code == 409
    commencer(en_base, evenement["id"])
    assert prof.put(url, json={"presences": {str(club["simple"].id): True}}).status_code == 422
    reponse = prof.put(url, json={"presences": presences | {str(club["membre2"].id): False}})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["presents"] == 1
    assert connecter(client, "membre").put(url, json={"presences": presences}).status_code in (403, 404)


def test_le_pointage_se_ferme_trente_jours_apres(
    client: TestClient, club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    commencer(en_base, evenement["id"], il_y_a=timedelta(days=32))

    reponse = connecter(client, "prof").put(
        f"{CLUB}/{evenement['id']}/presences", json={"presences": {str(club["membre"].id): True}}
    )

    assert reponse.status_code == 409
