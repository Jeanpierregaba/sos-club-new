"""Agenda public (spec 041) : seulement les événements publiés, filtres, prochains, et aucun nom ni pseudonyme
d'élève. Partie critique (RULES : rien de public avant l'approbation, élève public par son seul pseudonyme)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.agenda.models import Evenement
from app.eleves.models import Eleve
from tests.agenda import CLUB, club, connecter, propose, publie

__all__ = ["club"]

pytestmark = pytest.mark.usefixtures("annuaire")

AGENDA = "/api/agenda"


def anonyme(client: TestClient) -> TestClient:
    client.cookies.clear()
    return client


def test_rien_nest_public_avant_lapprobation(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    from tests.agenda import brouillon, decider, moderateur

    prof = connecter(client, "prof")
    en_attente = propose(prof)
    un_brouillon = brouillon(prof)
    a_corriger = propose(prof, titre="À corriger")
    refuse = propose(prof, titre="Refusé")
    equipe = moderateur(client, creer_collaborateur)
    assert decider(equipe, a_corriger["id"], "corriger", "Précise le lieu exact.").status_code == 200
    assert decider(equipe, refuse["id"], "refuser", "Hors des activités du club.").status_code == 200

    assert anonyme(client).get(AGENDA).json()["evenements"] == []
    for evenement in (en_attente, un_brouillon, a_corriger, refuse):
        assert client.get(f"{AGENDA}/{evenement['id']}").status_code == 404
    assert client.get(f"{AGENDA}/prochains").json() == []


def test_lagenda_montre_les_evenements_publies_avec_leur_club(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)

    page = anonyme(client).get(AGENDA).json()

    (vu,) = page["evenements"]
    assert vu["id"] == evenement["id"]
    assert (vu["club"], vu["niveau"], vu["dre_code"]) == ("Club Santé Tokoin", "club", "grand-lome")
    assert vu["etablissement"] is not None
    assert client.get(f"{AGENDA}/prochains").json()[0]["id"] == evenement["id"]


def test_les_filtres_et_les_periodes(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    sensibilisation = publie(client, creer_collaborateur)
    formation = publie(client, creer_collaborateur, type="formation", axe_code="genie-imhotep")
    passe = datetime.now(UTC) - timedelta(days=3)
    en_base(
        lambda db: db.execute(
            update(Evenement)
            .where(Evenement.id == UUID(formation["id"]))
            .values(debut=passe, fin=passe + timedelta(hours=2))
        )
    )
    anonyme(client)

    def ids(**filtres: Any) -> list[str]:
        return [e["id"] for e in client.get(AGENDA, params=filtres).json()["evenements"]]

    assert ids() == [sensibilisation["id"]]
    assert ids(periode="passe") == [formation["id"]]
    assert ids(periode="passe", type="formation", axe="genie-imhotep") == [formation["id"]]
    assert ids(type="formation") == []
    assert ids(dre="maritime") == []
    assert ids(club=str(club["club"].id)) == [sensibilisation["id"]]
    assert ids(club=str(club["autre"].id)) == []


def test_aucun_nom_ni_pseudonyme_deleve_dans_lagenda(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur, "presidente")
    connecter(client, "membre").put(f"{AGENDA}/{evenement['id']}/reponse", json={"reponse": "participe"})
    pseudos = en_base(lambda db: db.scalars(select(Eleve.pseudonyme))).all()
    eleves = [club[n] for n in ("presidente", "membre", "membre2")]
    interdits = [*pseudos, *(e.nom for e in eleves), *(e.prenom for e in eleves), *(str(e.id) for e in eleves)]

    anonyme(client)
    textes = [
        client.get(AGENDA).text,
        client.get(f"{AGENDA}/prochains").text,
        client.get(f"{AGENDA}/{evenement['id']}").text,
    ]

    assert client.get(f"{AGENDA}/{evenement['id']}").json()["participants"] == 1
    for texte in textes:
        for interdit in interdits:
            assert interdit not in texte, interdit


def test_un_evenement_annule_reste_visible_et_marque(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)
    connecter(client, "prof").post(f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Examens avancés d'un jour"})

    reponse = anonyme(client).get(f"{AGENDA}/{evenement['id']}")

    # Le motif est écrit sans modération : il n'est jamais public (RULES), seuls les invités le reçoivent.
    assert reponse.json()["annule"] is True
    assert "Examens avancés" not in reponse.text
    assert "Examens avancés" not in client.get(AGENDA).text
    assert client.get(f"{AGENDA}/prochains").json() == []


def test_mes_evenements_est_reserve_aux_eleves(client: TestClient, club: dict[str, Any]) -> None:
    assert connecter(client, "prof").get(f"{AGENDA}/mes-evenements").status_code == 403
    assert connecter(client, "simple").get(f"{AGENDA}/mes-evenements").json() == []
