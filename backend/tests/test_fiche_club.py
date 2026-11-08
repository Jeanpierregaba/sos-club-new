"""Propositions de fiche du club (spec 026) : le président propose une description et des axes, la fiche publique
ne change qu'à l'approbation d'un modérateur.

Écrits avant le code : rien de public sans modération (docs/RULES.md, docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.notifications.models import Notification
from tests.espace_club import FICHE, FILE, decider, espace, moderateur, passer_la_main, scene

pytestmark = pytest.mark.usefixtures("annuaire")

NOUVELLE = {
    "description": "Nous animons des ateliers d'hygiène chaque jeudi.",
    "axes": ["sante-environnement", "sport-secourisme"],
}


@pytest.fixture
def club(
    client: TestClient,
    creer_eleve: Callable[..., Any],
    creer_club: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    return scene(client, creer_eleve, creer_club, creer_encadreur, creer_collaborateur, en_base)


def proposer(club: dict[str, Any], **autres: Any) -> Any:
    return club["nav_president"].post(FICHE, json=NOUVELLE | autres)


def fiche(client: TestClient, club: dict[str, Any]) -> dict[str, Any]:
    return dict(client.get(f"/api/clubs/{club['club'].id}").json())


def test_une_proposition_reste_masquee_jusqua_lapprobation(client: TestClient, club: dict[str, Any]) -> None:
    avant = fiche(client, club)

    reponse = proposer(club)

    assert reponse.status_code == 201, reponse.text
    proposition = reponse.json()
    assert proposition["etat"] == "en_attente"
    assert proposition["description"] == NOUVELLE["description"]
    assert fiche(client, club)["description"] == avant["description"]
    suivi = club["nav_president"].get(espace(club["club"].id)).json()["suivi"]
    assert [p["id"] for p in suivi["propositions"]] == [proposition["id"]]


def test_le_moderateur_voit_lavant_et_lapres(club: dict[str, Any]) -> None:
    proposition = proposer(club).json()

    element = next(c for c in club["admin"].get(FILE).json()["contenus"] if c["id"] == proposition["id"])
    apercu = club["admin"].get(f"{FILE}/{proposition['id']}").json()

    assert element["type"] == "fiche_club"
    assert element["club"] == {"id": str(club["club"].id), "nom": "Club Santé du Lycée"}
    assert apercu["soumise"] == NOUVELLE
    assert apercu["fiche_actuelle"]["axes"] == []
    assert apercu["correction_possible"] is False


def test_lapprobation_change_la_fiche_publique_et_previent_le_president(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    proposition = proposer(club).json()

    assert decider(club["admin"], proposition["id"], "approuver").status_code == 200

    publique = fiche(client, club)
    assert publique["description"] == NOUVELLE["description"]
    assert publique["axes"] == sorted(NOUVELLE["axes"])
    avis = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == club["president"].id))
    )
    assert [a.type for a in avis] == ["fiche_club_approuve"]


def test_le_refus_ne_change_rien_et_donne_le_motif(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    avant = fiche(client, club)
    proposition = proposer(club).json()

    assert decider(club["admin"], proposition["id"], "refuser", "Description trop vague.").status_code == 200

    assert fiche(client, club) == avant
    suivi = club["nav_president"].get(espace(club["club"].id)).json()["suivi"]
    assert suivi["propositions"][0]["etat"] == "refuse"
    assert suivi["propositions"][0]["motif"] == "Description trop vague."


def test_une_seule_proposition_en_attente(club: dict[str, Any]) -> None:
    proposer(club)

    assert proposer(club, description="Une autre idée.").status_code == 409


def test_deux_propositions_simultanees_une_seule_passe(club: dict[str, Any], en_base: Callable[..., Any]) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.clubs import espace as service
    from app.comptes.inscription import Refus
    from app.comptes.models import Utilisateur
    from tests.conftest import moteur_test

    async def deux() -> list[Any]:
        async def une(texte: str) -> Any:
            async with AsyncSession(moteur_test, expire_on_commit=False) as db:
                president = await db.get(Utilisateur, club["president"].id)
                try:
                    return await service.proposer_fiche(db, president, texte, NOUVELLE["axes"], "127.0.0.1")
                except Refus as refus:
                    return refus

        return list(await asyncio.gather(une("Première version."), une("Seconde version.")))

    resultats = asyncio.run(deux())

    assert sum(isinstance(r, Exception) for r in resultats) == 1


def test_le_president_retire_sa_proposition_et_en_fait_une_autre(club: dict[str, Any]) -> None:
    proposition = proposer(club).json()

    assert club["nav_president"].delete(f"{FICHE}/{proposition['id']}").status_code == 204
    assert proposer(club, description="Mieux formulé.").status_code == 201


@pytest.mark.parametrize(
    "corps",
    [
        {"description": "x" * 301, "axes": ["sante-environnement"]},
        {"description": "Bien.", "axes": []},
        {"description": "Bien.", "axes": ["sante-environnement", "sport-secourisme", "genie-imhotep", "inconnu"]},
        {"description": "Bien.", "axes": ["axe-inconnu"]},
    ],
)
def test_une_proposition_invalide_est_refusee(club: dict[str, Any], corps: dict[str, Any]) -> None:
    assert club["nav_president"].post(FICHE, json=corps).status_code == 422


def test_une_proposition_identique_a_la_fiche_est_refusee(client: TestClient, club: dict[str, Any]) -> None:
    proposition = proposer(club).json()
    decider(club["admin"], proposition["id"], "approuver")

    assert proposer(club).status_code == 422


def test_une_fiche_ne_se_corrige_ni_ne_se_depublie(club: dict[str, Any]) -> None:
    proposition = proposer(club).json()

    assert decider(club["admin"], proposition["id"], "corriger", "Reformule.").status_code == 409
    decider(club["admin"], proposition["id"], "approuver")
    assert decider(club["admin"], proposition["id"], "depublier", "Non.").status_code == 409


def test_un_moderateur_dune_autre_dre_ne_voit_pas_la_proposition(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    proposition = proposer(club).json()
    regional = moderateur(client, creer_collaborateur, "regional", perimetre_dre="kara")

    assert regional.get(f"{FILE}/{proposition['id']}").status_code == 404


def test_apres_une_passation_le_nouveau_president_gere_la_proposition(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    from tests.espace_club import connecter

    proposition = proposer(club).json()
    passer_la_main(en_base, club["admin"], club["club"], club["membre"])

    assert club["nav_president"].delete(f"{FICHE}/{proposition['id']}").status_code in {403, 404}
    nouveau = connecter(client, "membre")
    assert nouveau.delete(f"{FICHE}/{proposition['id']}").status_code == 204
