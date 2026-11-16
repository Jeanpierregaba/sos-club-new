"""Vérification publique d'une carte par son QR (spec 040, Q30) : statut, numéro, type et club seulement. Partie
critique (données publiques, RULES), écrite avant le code."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.cartes.models import Carte
from app.comptes.models import StatutCompte, Utilisateur
from app.config import settings
from tests.conftest import Navigateur

pytestmark = pytest.mark.usefixtures("annuaire")

VERIFICATION = "/api/cartes/verification"


def carte_de(en_base: Callable[..., Any], utilisateur_id: Any) -> Carte:
    return en_base(lambda db: db.scalar(select(Carte).where(Carte.utilisateur_id == utilisateur_id)))


def verifier(client: TestClient, code: str) -> Any:
    return Navigateur(client).get(f"{VERIFICATION}/{code}")


@pytest.fixture
def membre(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> Utilisateur:
    from tests.espace_club import adherer

    presidente = creer_eleve("presidente", "Ama")
    club = creer_club(presidente, nom="Club Santé Tokoin")
    eleve = creer_eleve("yao", "Yao du Golfe")
    adherer(en_base, eleve, club)
    return eleve


def test_une_carte_valide_ne_montre_que_le_type_le_numero_le_club_et_le_statut(
    client: TestClient, membre: Utilisateur, en_base: Callable[..., Any]
) -> None:
    carte = carte_de(en_base, membre.id)

    reponse = verifier(client, carte.code)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert set(corps) == {"type", "numero", "club", "valide", "verifiee_le"}
    assert (corps["type"], corps["numero"], corps["club"], corps["valide"]) == (
        "membre", carte.numero, "Club Santé Tokoin", True,
    )  # fmt: skip
    for secret in (membre.prenom, membre.nom, "Yao du Golfe", membre.identifiant):
        assert secret not in reponse.text
    assert reponse.headers["cache-control"] == "no-store"
    assert reponse.headers["x-robots-tag"] == "noindex"


def test_une_carte_non_valide_le_dit_sans_motif(
    client: TestClient, membre: Utilisateur, en_base: Callable[..., Any]
) -> None:
    from datetime import UTC, datetime

    en_base(
        lambda db: db.execute(
            update(Carte)
            .where(Carte.utilisateur_id == membre.id)
            .values(suspendue_le=datetime.now(UTC), motif_suspension="Carte prêtée à un tiers.")
        )
    )
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == membre.id).values(statut=StatutCompte.suspendu)
        )
    )

    reponse = verifier(client, carte_de(en_base, membre.id).code)

    assert reponse.status_code == 200 and reponse.json()["valide"] is False
    assert "prêtée" not in reponse.text and "suspendu" not in reponse.text


@pytest.mark.parametrize("code", ["x" * 32, "court", "x" * 31 + "!", "CS-M-000001"])
def test_un_code_inconnu_mal_forme_ou_un_numero_nouvre_rien(client: TestClient, membre: Utilisateur, code: str) -> None:
    reponse = verifier(client, code)

    assert reponse.status_code == 404
    assert reponse.json()["detail"] == "Cette carte n'existe pas."
    assert reponse.headers["cache-control"] == "no-store"
    assert reponse.headers["x-robots-tag"] == "noindex"


def test_le_numero_imprime_ne_permet_pas_de_retrouver_la_carte(
    client: TestClient, membre: Utilisateur, en_base: Callable[..., Any]
) -> None:
    assert verifier(client, carte_de(en_base, membre.id).numero).status_code == 404


def test_une_meme_adresse_ip_est_limitee(
    client: TestClient, membre: Utilisateur, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "verifications_carte_max_adresse", 3)
    code = carte_de(en_base, membre.id).code

    codes = [verifier(client, code).status_code for _ in range(4)]

    assert codes == [200, 200, 200, 429]
    refus = verifier(client, code)
    assert refus.headers["cache-control"] == "no-store" and refus.headers["x-robots-tag"] == "noindex"


def test_un_code_suivi_dun_saut_de_ligne_est_refuse(
    client: TestClient, membre: Utilisateur, en_base: Callable[..., Any]
) -> None:
    assert verifier(client, carte_de(en_base, membre.id).code + "%0A").status_code == 404


def test_une_saisie_didentifiant_ne_peut_pas_bloquer_une_adresse_ip(
    client: TestClient, membre: Utilisateur, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "verifications_carte_max_adresse", 3)
    for _ in range(5):
        Navigateur(client).post("/api/comptes/connexion", json={"identifiant": "CARTE:testclient", "mot_de_passe": "x"})

    assert verifier(client, carte_de(en_base, membre.id).code).status_code == 200
