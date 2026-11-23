"""Événements vus par l'API elle-même (spec 051) : étapes d'inscription, téléchargements, présence, erreurs."""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.activite import service, suivi
from app.activite.models import EvenementActivite, PresenceSemaine
from app.config import settings
from app.main import app
from tests.bibliotheque import creer_ressource
from tests.conftest import connecter_admin
from tests.test_connexion import se_connecter
from tests.test_eleves_inscription import INSCRIPTION, formulaire

pytestmark = pytest.mark.usefixtures("annuaire")
AGENT = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) Chrome/120.0 Mobile Safari/537.36"}


@pytest.fixture(autouse=True)
def presences_oubliees() -> Iterator[None]:
    suivi.oublier_presences()
    yield
    suivi.oublier_presences()


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


def evenements(en_base: Callable[..., Any]) -> list[tuple[str, str, str | None]]:
    async def lire(db: Any) -> list[tuple[str, str, str | None]]:
        lignes = await db.execute(
            select(EvenementActivite.type, EvenementActivite.chemin, EvenementActivite.detail).order_by(
                EvenementActivite.id
            )
        )
        return [tuple(ligne) for ligne in lignes]

    return en_base(lire)


def test_une_inscription_reussie_est_suivie(client: TestClient, en_base: Callable[..., Any]) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base), headers=AGENT).status_code == 201
    assert evenements(en_base) == [
        ("etape_inscription", "/inscription", "eleve:envoye"),
        ("etape_inscription", "/inscription", "eleve:cree"),
    ]


def test_un_refus_est_suivi_avec_son_motif_jamais_son_message(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base), headers=AGENT)
    client.cookies.clear()
    reponse = client.post(INSCRIPTION, json=formulaire(en_base, identifiant="autre.eleve"), headers=AGENT)
    assert reponse.status_code == 409
    assert evenements(en_base)[-2:] == [
        ("etape_inscription", "/inscription", "eleve:envoye"),
        ("etape_inscription", "/inscription", "eleve:refuse-doublon"),
    ]


def test_inscriptions_fermees(client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", False)
    assert client.post(INSCRIPTION, json=formulaire(en_base), headers=AGENT).status_code == 403
    assert evenements(en_base)[-1] == ("etape_inscription", "/inscription", "eleve:refuse-fermees")


def test_une_panne_du_suivi_ne_casse_pas_l_inscription(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def en_panne(*_: Any, **__: Any) -> bool:
        raise RuntimeError("base du suivi indisponible")

    monkeypatch.setattr(service, "ecrire", en_panne)
    assert client.post(INSCRIPTION, json=formulaire(en_base), headers=AGENT).status_code == 201


def test_ne_pas_me_suivre_vaut_aussi_pour_l_inscription(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base), headers=AGENT | {"Sec-GPC": "1"})
    assert evenements(en_base) == []


def test_lecture_et_telechargement_d_un_document(client: TestClient, en_base: Callable[..., Any]) -> None:
    ressource = creer_ressource(en_base)
    assert client.get(f"/api/bibliotheque/{ressource.id}/fichier", headers=AGENT).status_code == 200
    reponse = client.get(f"/api/bibliotheque/{ressource.id}/fichier?telecharger=1", headers=AGENT)
    assert reponse.status_code == 200
    assert evenements(en_base) == [
        ("telechargement", "/bibliotheque", f"lire:{ressource.id}"),
        ("telechargement", "/bibliotheque", f"telecharger:{ressource.id}"),
    ]


def presences(en_base: Callable[..., Any]) -> list[Any]:
    async def lire(db: Any) -> list[Any]:
        return list(await db.scalars(select(PresenceSemaine.utilisateur_id)))

    return en_base(lire)


def test_la_presence_est_notee_une_fois_par_semaine(
    client: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    eleve = creer_utilisateur()
    se_connecter(client)
    client.get("/api/comptes/moi")
    client.get("/api/comptes/moi")
    suivi.oublier_presences()  # un autre processus de l'API
    client.get("/api/comptes/moi")
    assert presences(en_base) == [eleve.id]


def test_l_equipe_n_a_pas_de_presence(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("chef", super_admin=True)
    connecter_admin(client)
    client.get("/api/comptes/moi")
    assert presences(en_base) == []


def test_une_erreur_serveur_compte_par_le_gabarit_de_sa_route(en_base: Callable[..., Any]) -> None:
    essai = APIRouter()

    @essai.get("/api/essai-erreur/{code}")
    async def planter(code: str) -> None:
        raise RuntimeError(code)

    app.include_router(essai)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            reponse = client.get("/api/essai-erreur/ABC123", headers=AGENT)
    finally:
        app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", "") != "/api/essai-erreur/{code}"]
    assert reponse.status_code == 500
    assert evenements(en_base) == [("erreur", "/api/essai-erreur/{code}", "500")]
