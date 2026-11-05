"""Passation confirmée par un encadreur rattaché (Q19, spec 020, tâche 6)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.clubs.models import (
    Adhesion,
    Club,
    ClubPassation,
    EtatAdhesion,
    EtatPassation,
    EtatRattachement,
    Rattachement,
)
from app.comptes.models import Utilisateur
from tests.conftest import MOT_DE_PASSE, Navigateur

pytestmark = pytest.mark.usefixtures("annuaire")

PROPOSER = "/api/clubs/moi/passation"


def connecter(client: Any, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


@pytest.fixture
def club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    return creer_club(creer_eleve("president", "Ama la Présidente"))


@pytest.fixture
def successeur(club: Any, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]) -> Utilisateur:
    """Un membre actif du club, futur président."""
    eleve = creer_eleve("kofi", "Kofi Curieux", etablissement_id=club.etablissement_id)

    async def inserer(db: AsyncSession) -> None:
        db.add(Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.active))

    en_base(inserer)
    return eleve


def rattacher(en_base: Callable[..., Any], encadreur: Utilisateur, club: Any) -> Rattachement:
    async def inserer(db: AsyncSession) -> Rattachement:
        ligne = Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=EtatRattachement.actif)
        db.add(ligne)
        return ligne

    return en_base(inserer)


def proposer(client: TestClient, club: Any, pseudonyme: str = "Kofi Curieux") -> Any:
    connecter(client, "president")
    return client.post(PROPOSER, json={"pseudonyme": pseudonyme, "version": club.version})


def passation_du_club(en_base: Callable[..., Any], club: Any) -> ClubPassation:
    return en_base(lambda db: db.scalar(select(ClubPassation).where(ClubPassation.club_id == club.id)))


@pytest.fixture
def prof(club: Any, creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]) -> Utilisateur:
    encadreur = creer_encadreur("prof", etablissement_id=club.etablissement_id)
    rattacher(en_base, encadreur, club)
    return encadreur


def test_sans_encadreur_rattache_la_passation_va_directement_a_ladmin(
    client: TestClient, club: Any, successeur: Utilisateur
) -> None:
    reponse = proposer(client, club)

    assert reponse.status_code == 201
    assert reponse.json()["etat"] == "en_attente"


def test_le_successeur_doit_etre_membre_du_club(
    client: TestClient, club: Any, creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve("voisin", "Voisin", etablissement_id=club.etablissement_id)

    reponse = proposer(client, club, "Voisin")

    assert reponse.status_code == 422
    assert "membre" in reponse.json()["detail"]


def test_avec_un_encadreur_la_passation_attend_sa_confirmation(
    client: TestClient,
    verificateur_clubs: TestClient,
    club: Any,
    successeur: Utilisateur,
    prof: Utilisateur,
) -> None:
    navigateur = Navigateur(client)
    corps = proposer(navigateur, club).json()
    assert corps["etat"] == "en_attente_encadreur"

    # L'admin ne la voit pas encore : l'encadreur doit d'abord confirmer.
    assert verificateur_clubs.get("/api/admin/clubs/passations").json()["total"] == 0

    connecter(navigateur, "prof")
    a_confirmer = navigateur.get("/api/encadreurs/moi/clubs").json()["passations"]
    assert [(p["successeur_pseudonyme"], p["president_sortant_pseudonyme"]) for p in a_confirmer] == [
        ("Kofi Curieux", "Ama la Présidente")
    ]
    reponse = navigateur.post(f"/api/clubs/{club.id}/passation/confirmer", json={"version": a_confirmer[0]["version"]})
    assert reponse.status_code == 200

    file = verificateur_clubs.get("/api/admin/clubs/passations").json()
    assert file["total"] == 1
    validation = verificateur_clubs.post(f"/api/admin/clubs/passations/{file['passations'][0]['id']}/valider")
    assert validation.status_code == 200


def test_la_confirmation_est_journalisee(
    client: TestClient, club: Any, successeur: Utilisateur, prof: Utilisateur, en_base: Callable[..., Any]
) -> None:
    proposer(client, club)
    connecter(client, "prof")
    version = passation_du_club(en_base, club).version

    client.post(f"/api/clubs/{club.id}/passation/confirmer", json={"version": version})

    passation = passation_du_club(en_base, club)
    assert passation.etat is EtatPassation.en_attente
    assert passation.confirmee_par == prof.id
    actions = en_base(lambda db: db.scalars(select(JournalAudit.action))).all()
    assert "club_passation_confirmee" in actions


def test_lencadreur_refuse_avec_un_motif_que_le_president_lit(
    client: TestClient, club: Any, successeur: Utilisateur, prof: Utilisateur, en_base: Callable[..., Any]
) -> None:
    proposer(client, club)
    connecter(client, "prof")
    version = passation_du_club(en_base, club).version
    url = f"/api/clubs/{club.id}/passation/refuser"

    assert client.post(url, json={"motif": "", "version": version}).status_code == 422
    assert client.post(url, json={"motif": "Kofi vient d'arriver au club.", "version": version}).status_code == 200

    connecter(client, "president")
    passation = client.get("/api/clubs/moi").json()["passation"]
    assert passation["etat"] == "refusee"
    assert passation["motif_refus"] == "Kofi vient d'arriver au club."


def test_seul_un_encadreur_rattache_confirme(
    client: TestClient,
    club: Any,
    successeur: Utilisateur,
    prof: Utilisateur,
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    proposer(client, club)
    version = passation_du_club(en_base, club).version
    url = f"/api/clubs/{club.id}/passation/confirmer"
    creer_encadreur("prof.libre", etablissement_id=club.etablissement_id)

    connecter(client, "prof.libre")
    assert client.post(url, json={"version": version}).status_code == 403
    connecter(client, "kofi")
    assert client.post(url, json={"version": version}).status_code == 403
    connecter(client, "prof")
    assert client.post(url, json={"version": version + 1}).status_code == 409


def test_si_le_dernier_encadreur_part_la_passation_va_a_ladmin(
    client: TestClient, club: Any, successeur: Utilisateur, prof: Utilisateur, en_base: Callable[..., Any]
) -> None:
    proposer(client, club)
    connecter(client, "prof")

    assert client.delete(f"/api/clubs/{club.id}/rattachements/moi").status_code == 200

    assert passation_du_club(en_base, club).etat is EtatPassation.en_attente


def test_le_president_annule_une_passation_qui_attend_lencadreur(
    client: TestClient, club: Any, successeur: Utilisateur, prof: Utilisateur, en_base: Callable[..., Any]
) -> None:
    proposer(client, club)

    assert client.post("/api/clubs/moi/passation/annuler").status_code == 200
    assert passation_du_club(en_base, club).etat is EtatPassation.refusee


def test_un_successeur_qui_a_quitte_le_club_nest_pas_valide(
    client: TestClient,
    verificateur_clubs: TestClient,
    club: Any,
    successeur: Utilisateur,
    en_base: Callable[..., Any],
) -> None:
    navigateur = Navigateur(client)
    corps = proposer(navigateur, club).json()
    connecter(navigateur, "kofi")
    assert navigateur.delete(f"/api/clubs/{club.id}/adhesions/moi").status_code == 200

    reponse = verificateur_clubs.post(f"/api/admin/clubs/passations/{corps['id']}/valider")

    assert reponse.status_code == 409
    assert en_base(lambda db: db.get(Club, club.id)).president_id == club.president_id
