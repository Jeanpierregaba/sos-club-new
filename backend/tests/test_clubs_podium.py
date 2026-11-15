"""Le podium des clubs de l'accueil (spec 021, tâche 3). Le score d'un club est la somme de ses parts dans le
registre (spec 034, ADR-0012) : les tests écrivent de vraies lignes (spec 036)."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.clubs.models import EtatClub
from app.comptes.models import Utilisateur
from app.points import service as points
from app.referentiel.models import Etablissement
from tests.test_classements import point

pytestmark = pytest.mark.usefixtures("annuaire")

PODIUM = "/api/clubs/podium"


def scores(en_base: Callable[..., Any], valeurs: dict[Any, float]) -> None:
    """Crédite chaque club de son score par une ligne de son président : le club reçoit la moitié du gain."""
    for club, score in valeurs.items():
        demi = int(score * 2)
        point(en_base, club.president_id, demi, f"podium:{club.id}", club_id=club.id, demi_points=demi)


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
    client: TestClient, clubs: list[Any], en_base: Callable[..., Any]
) -> None:
    alpha, beta, gamma, delta, _ = clubs
    scores(en_base, {alpha: 120, beta: 450, gamma: 300, delta: 10})

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
    en_base: Callable[..., Any],
) -> None:
    alpha, *_ = clubs
    en_attente = creer_club(
        creer_eleve("demandeur", "Demandeur", dre="maritime"), nom="Club en attente", etat=EtatClub.en_attente
    )
    en_attente_id = en_attente.id
    president = creer_eleve("membre", "Membre", dre="maritime")
    scores(en_base, {alpha: 50})
    point(en_base, president.id, 1800, "attente", club_id=en_attente_id, demi_points=1800)

    assert [c["nom"] for c in client.get(PODIUM).json()] == ["Club Alpha"]


def test_a_egalite_lordre_alphabetique(client: TestClient, clubs: list[Any], en_base: Callable[..., Any]) -> None:
    alpha, _, _, delta, _ = clubs
    scores(en_base, {delta: 100, alpha: 100})

    assert [c["nom"] for c in client.get(PODIUM).json()] == ["Club Alpha", "Club Delta"]


def test_un_score_de_club_garde_sa_decimale(client: TestClient, clubs: list[Any], en_base: Callable[..., Any]) -> None:
    alpha, *_ = clubs
    scores(en_base, {alpha: 2.5})

    assert [c["points"] for c in client.get(PODIUM).json()] == [2.5]


def test_sans_club_aucun_score() -> None:
    import asyncio

    assert asyncio.run(points.scores_des_clubs(None, [])) == {}  # type: ignore[arg-type]
