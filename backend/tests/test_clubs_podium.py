"""Le podium des clubs de l'accueil (spec 021, tâche 3). Le registre ne crédite pas encore les clubs (R13) :
les tests remplacent `scores_des_clubs` pour vérifier le classement."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import EtatClub
from app.comptes.models import Utilisateur
from app.points import service as points
from app.referentiel.models import Etablissement

pytestmark = pytest.mark.usefixtures("annuaire")

PODIUM = "/api/clubs/podium"


def scores(monkeypatch: pytest.MonkeyPatch, valeurs: dict[UUID, int]) -> None:
    async def remplacer(db: AsyncSession, club_ids: list[UUID]) -> dict[UUID, int]:
        return {i: valeurs[i] for i in club_ids if i in valeurs}

    monkeypatch.setattr(points, "scores_des_clubs", remplacer)


def etablissements(en_base: Callable[..., Any], nombre: int) -> list[UUID]:
    return list(en_base(lambda db: db.scalars(select(Etablissement.id).order_by(Etablissement.nom).limit(nombre))))


@pytest.fixture
def clubs(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> list[Any]:
    noms = ["Club Alpha", "Club Bêta", "Club Gamma", "Club Delta", "Club en attente"]
    lieux = etablissements(en_base, len(noms))
    return [
        creer_club(
            creer_eleve(f"president{i}", f"Président {i}", etablissement_id=lieu),
            nom=nom,
            etat=EtatClub.en_attente if nom == "Club en attente" else EtatClub.actif,
        )
        for i, (nom, lieu) in enumerate(zip(noms, lieux, strict=True))
    ]


def test_sans_points_le_podium_est_vide(client: TestClient, clubs: list[Any]) -> None:
    assert client.get(PODIUM).json() == []


def test_les_trois_meilleurs_clubs_actifs_tries_par_points(
    client: TestClient, clubs: list[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    alpha, beta, gamma, delta, _ = clubs
    scores(monkeypatch, {alpha.id: 120, beta.id: 450, gamma.id: 300, delta.id: 10})

    podium = client.get(PODIUM).json()

    assert [(c["rang"], c["nom"], c["points"]) for c in podium] == [
        (1, "Club Bêta", 450),
        (2, "Club Gamma", 300),
        (3, "Club Alpha", 120),
    ]
    assert set(podium[0]) == {"rang", "id", "nom", "etablissement", "dre", "points"}


def test_un_club_sans_point_ou_inactif_nest_pas_sur_le_podium(
    client: TestClient,
    clubs: list[Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alpha, *_ = clubs
    en_attente = creer_club(
        creer_eleve("demandeur", "Demandeur", dre="maritime"), nom="Club en attente", etat=EtatClub.en_attente
    )
    scores(monkeypatch, {alpha.id: 50, en_attente.id: 900})

    assert [c["nom"] for c in client.get(PODIUM).json()] == ["Club Alpha"]


def test_a_egalite_lordre_alphabetique(client: TestClient, clubs: list[Any], monkeypatch: pytest.MonkeyPatch) -> None:
    alpha, _, _, delta, _ = clubs
    scores(monkeypatch, {delta.id: 100, alpha.id: 100})

    assert [c["nom"] for c in client.get(PODIUM).json()] == ["Club Alpha", "Club Delta"]


def test_aujourdhui_aucun_club_na_de_points() -> None:
    import asyncio

    assert asyncio.run(points.scores_des_clubs(None, [])) == {}  # type: ignore[arg-type]
