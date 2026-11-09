"""Cas limites de l'espace administrateur relevés à la relecture (spec 015) : périmètre, concurrence, plafonds."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.exports import neutraliser
from app.admin.models import Collaborateur
from app.comptes.models import StatutCompte, Utilisateur
from app.config import settings
from app.courriel import envoi as courriel
from tests.conftest import Navigateur, code_totp, connecter_admin

MODERATEUR_KARA = {
    ("tableau_de_bord", "consulter"),
    ("inscrits", "consulter"),
    ("inscrits", "exporter"),
    ("journal", "consulter"),
}
NOMINATIF = {"type": "nominatif", "format": "csv", "colonnes": ["identifiant"], "finalite": "Bilan régional"}


def id_collaborateur(en_base: Callable[..., Any], utilisateur: Utilisateur) -> Any:
    return en_base(lambda db: db.scalar(select(Collaborateur.id).where(Collaborateur.utilisateur_id == utilisateur.id)))


def en_parallele(*appels: Callable[[], Any]) -> list[Any]:
    async def lancer() -> list[Any]:
        return await asyncio.gather(*(asyncio.to_thread(appel) for appel in appels))

    return asyncio.run(lancer())


@pytest.fixture
def courriels(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    boite: list[str] = []

    async def envoyer(_: str, __: str, texte: str, html: str | None = None) -> None:
        boite.append(texte)

    monkeypatch.setattr(courriel, "envoyer", envoyer)
    return boite


# Périmètre DRE ---------------------------------------------------------------------------------------------------


def test_un_moderateur_dre_ne_fait_pas_d_export_nominatif(
    client: TestClient, creer_collaborateur: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    creer_utilisateur("ama")
    creer_collaborateur("kara", droits=MODERATEUR_KARA, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "kara")

    assert client.post("/api/admin/exports/apercu", json=NOMINATIF).status_code == 403
    assert client.post("/api/admin/exports", json=NOMINATIF).status_code == 403
    # Le journal contient des données nominatives : il est aussi réservé au périmètre national.
    assert client.get("/api/admin/journal").status_code == 403
    assert client.get("/api/admin/tableau-de-bord").json()["derniers_evenements"] is None


# Concurrence -----------------------------------------------------------------------------------------------------


def test_deux_activations_simultanees_du_meme_lien(
    client: TestClient, creer_collaborateur: Callable[..., Any], courriels: list[str], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    client.post("/api/admin/collaborateurs", json={"email": "x@aimes.tg", "prenom": "X", "nom": "Y", "droits": []})
    jeton = next(m for m in courriels[0].split() if "jeton=" in m).split("jeton=")[1]
    client.cookies.clear()

    def activer(identifiant: str) -> int:
        corps = {"jeton": jeton, "identifiant": identifiant, "mot_de_passe": "un-bon-mot-de-passe"}
        return client.post("/api/activation", json=corps).status_code

    statuts = en_parallele(*(lambda i=i: activer(f"invite{i}") for i in range(6)))

    assert statuts.count(200) == 1
    comptes = select(func.count()).select_from(Utilisateur).where(Utilisateur.email == "x@aimes.tg")
    assert en_base(lambda db: db.scalar(comptes)) == 1


def test_deux_super_admins_qui_se_suspendent_en_meme_temps(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    a = creer_collaborateur("alpha", super_admin=True, double_auth=True)
    b = creer_collaborateur("beta", super_admin=True, double_auth=True)
    id_a, id_b = id_collaborateur(en_base, a), id_collaborateur(en_base, b)

    def jeton_de(identifiant: str, decalage: int) -> str:
        navigateur = Navigateur(client)
        reponse = navigateur.post(
            "/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": "mot-de-passe-de-test"}
        )
        navigateur.post(
            "/api/comptes/connexion/code", json={"jeton": reponse.json()["jeton"], "code": code_totp(decalage)}
        )
        return next(c.value for c in navigateur.cookies if c.name == settings.cookie_session)

    jeton_a, jeton_b = jeton_de("alpha", 0), jeton_de("beta", 1)
    client.cookies.clear()

    def suspendre(jeton: str, cible: Any) -> int:
        return client.post(
            f"/api/admin/collaborateurs/{cible}/suspendre",
            json={"motif": "Essai simultané"},
            headers={"Cookie": f"{settings.cookie_session}={jeton}"},
        ).status_code

    statuts = en_parallele(lambda: suspendre(jeton_a, id_b), lambda: suspendre(jeton_b, id_a))

    assert statuts.count(200) <= 1
    actifs = (
        select(func.count())
        .select_from(Utilisateur)
        .where(Utilisateur.id.in_([a.id, b.id]), Utilisateur.statut == StatutCompte.actif)
    )
    assert en_base(lambda db: db.scalar(actifs)) >= 1


# Super-administrateur, invitation, codes --------------------------------------------------------------------------


def test_un_super_admin_n_a_ni_fin_d_acces_ni_perimetre(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur("alpha", super_admin=True, double_auth=True)
    beta = creer_collaborateur("beta", super_admin=True, double_auth=True)
    connecter_admin(client, "alpha")
    url = f"/api/admin/collaborateurs/{id_collaborateur(en_base, beta)}/permissions"
    demain = (datetime.now(UTC) + timedelta(days=1)).isoformat()

    assert client.put(url, json={"droits": [], "fin_acces": demain, "motif": "Essai"}).status_code == 422
    assert client.put(url, json={"droits": [], "perimetre_dre": "kara", "motif": "Essai"}).status_code == 422


def test_annuler_une_invitation(
    client: TestClient, creer_collaborateur: Callable[..., Any], courriels: list[str]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    cree = client.post(
        "/api/admin/collaborateurs", json={"email": "erreur@aimes.tg", "prenom": "E", "nom": "R", "droits": []}
    )
    identifiant = cree.json()["collaborateur"]["id"]
    jeton = next(m for m in courriels[0].split() if "jeton=" in m).split("jeton=")[1]

    reponse = client.post(
        f"/api/admin/collaborateurs/{identifiant}/invitation/annuler", json={"motif": "Mauvaise adresse"}
    )

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "invitation_expiree"
    assert client.post("/api/activation/info", json={"jeton": jeton}).status_code == 404
    assert (
        client.post(f"/api/admin/collaborateurs/{identifiant}/invitation/annuler", json={"motif": "Encore"}).status_code
        == 409
    )


def test_les_codes_redemandes_sont_limites(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    faux = "000000" if code_totp(1) != "000000" else "111111"

    for _ in range(5):
        assert client.post("/api/admin/double-auth/codes-secours", json={"code": faux}).status_code == 422

    assert client.post("/api/admin/double-auth/codes-secours", json={"code": code_totp(1)}).status_code == 429


# Exports -----------------------------------------------------------------------------------------------------------


def test_plafond_de_lignes(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_utilisateur: Callable[..., Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    creer_utilisateur("ama")
    creer_utilisateur("kofi")
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    monkeypatch.setattr(settings, "export_lignes_max", 2)

    reponse = client.post("/api/admin/exports", json=NOMINATIF)

    assert reponse.status_code == 422
    assert "affine les filtres" in reponse.json()["detail"]


@pytest.mark.parametrize("valeur", ["=1+1", "+33", "-2", "@SUM(A1)", "\tcmd", "\rx"])
def test_les_debuts_de_formule_sont_neutralises(valeur: str) -> None:
    assert neutraliser(valeur) == f"'{valeur}"


def test_un_texte_ordinaire_reste_tel_quel() -> None:
    assert neutraliser("Lycée d'Adétikopé") == "Lycée d'Adétikopé"
