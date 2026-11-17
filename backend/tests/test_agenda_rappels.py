"""Rappel de la veille (spec 041) : à ceux qui participent, une seule fois, rien pour un événement annulé, un
nouveau rappel après un report à un autre jour."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda import rappels
from app.agenda.models import Evenement
from tests.agenda import CLUB, club, connecter, notifications, plus_tard, publie
from tests.conftest import moteur_test

__all__ = ["club"]

pytestmark = pytest.mark.usefixtures("annuaire")


def lancer(maintenant: datetime | None = None) -> int:
    async def une_fois() -> int:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            return await rappels.envoyer(db, maintenant)

    return asyncio.run(une_fois())


def demain_a(heure: int) -> dict[str, str]:
    debut = plus_tard(jours=1, heure=heure)
    return {
        "debut": debut.isoformat(timespec="minutes"),
        "fin": (debut + timedelta(hours=1)).isoformat(timespec="minutes"),
    }


@pytest.fixture
def evenement(client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]) -> dict[str, Any]:
    evenement = publie(client, creer_collaborateur, **demain_a(10))
    connecter(client, "membre").put(f"/api/agenda/{evenement['id']}/reponse", json={"reponse": "participe"})
    connecter(client, "membre2").put(f"/api/agenda/{evenement['id']}/reponse", json={"reponse": "peut_etre"})
    return evenement


def test_la_veille_ceux_qui_participent_recoivent_un_rappel_une_seule_fois(
    club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    assert lancer() == 1
    assert lancer() == 0

    (rappel,) = notifications(en_base, club["membre"], "evenement_rappel")
    assert rappel.titre.startswith("Demain à 10 h 30") and rappel.lien == f"/agenda/{evenement['id']}"
    assert notifications(en_base, club["membre2"], "evenement_rappel") == []


def test_rien_avant_la_veille(evenement: dict[str, Any]) -> None:
    assert lancer(datetime.now(UTC) - timedelta(days=1)) == 0


def test_rien_pour_un_evenement_annule(
    client: TestClient, club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    connecter(client, "prof").post(f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Examens avancés d'un jour"})

    assert lancer() == 0
    assert notifications(en_base, club["membre"], "evenement_rappel") == []


def test_un_report_a_un_autre_jour_rouvre_un_rappel(
    club: dict[str, Any], evenement: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    assert lancer() == 1
    plus_loin = datetime.now(UTC) + timedelta(days=5)
    en_base(
        lambda db: db.execute(
            update(Evenement)
            .where(Evenement.id == UUID(evenement["id"]))
            .values(debut=plus_loin, fin=plus_loin + timedelta(hours=1))
        )
    )

    assert lancer(plus_loin - timedelta(days=1)) == 1
    assert len(notifications(en_base, club["membre"], "evenement_rappel")) == 2
