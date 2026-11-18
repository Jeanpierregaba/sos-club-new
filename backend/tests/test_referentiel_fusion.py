"""Doublons d'établissements et fusion (spec 042), côté administration : liste des doublons probables, écarts,
fusion. Partie critique (déplace des comptes et des clubs)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from tests.conftest import connecter_admin

BASE = "/api/admin/referentiel"
ETABLISSEMENTS = f"{BASE}/etablissements"
DOUBLONS = f"{ETABLISSEMENTS}/doublons"

CLUBS = {("tableau_de_bord", "consulter"), ("clubs", "consulter"), ("clubs", "creer"), ("clubs", "modifier")}
LECTURE = {("tableau_de_bord", "consulter"), ("clubs", "consulter")}

pytestmark = pytest.mark.usefixtures("annuaire")


# Aides ----------------------------------------------------------------------------------------------------------


@pytest.fixture
def national(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=CLUBS, double_auth=True)
    connecter_admin(client, "gestion")
    return client


def connecter(
    client: TestClient, creer_collaborateur: Callable[..., Any], nom: str, droits: Any, dre: str | None
) -> None:
    creer_collaborateur(nom, droits=droits, perimetre_dre=dre, double_auth=True)
    client.cookies.clear()
    connecter_admin(client, nom)


def iesg(client: TestClient, nom: str) -> str:
    dre = client.get(f"{BASE}/dre").json()
    return next(i["id"] for d in dre for i in d["iesg"] if i["nom"] == nom)


def etablissement(client: TestClient, nom: str) -> dict[str, Any]:
    page = client.get(ETABLISSEMENTS, params={"recherche": nom, "par_page": 100}).json()
    return next(e for e in page["etablissements"] if e["nom"] == nom)


def creer(client: TestClient, nom: str, inspection: str = "IESG Golfe", **champs: Any) -> dict[str, Any]:
    reponse = client.post(
        ETABLISSEMENTS, json={"iesg_id": iesg(client, inspection), "nom": nom, "type": "lycee"} | champs
    )
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def paires(client: TestClient, **filtres: Any) -> list[dict[str, Any]]:
    reponse = client.get(DOUBLONS, params=filtres)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["paires"]


def noms(liste: list[dict[str, Any]]) -> list[set[str]]:
    return [{p["a"]["nom"], p["b"]["nom"]} for p in liste]


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


TOKOIN = {"Lycée de Tokoin I", "Lycée Tokoin I"}


# Doublons probables ---------------------------------------------------------------------------------------------


def test_un_doublon_cree_est_propose_avec_sa_raison(national: TestClient) -> None:
    creer(national, "Lycée Tokoin I")

    page = national.get(DOUBLONS, params={"dre": "grand-lome"}).json()

    (paire,) = [p for p in page["paires"] if {p["a"]["nom"], p["b"]["nom"]} == TOKOIN]
    assert paire["raison"] == "meme_nom"
    assert paire["ecartee"] is False
    assert paire["a"]["id"] < paire["b"]["id"]
    assert {"nb_eleves", "nb_encadreurs", "club", "iesg", "prefecture"} <= paire["a"].keys()
    assert page["par_dre"]["grand-lome"] >= 1
    assert all(p["a"]["dre_code"] == "grand-lome" for p in page["paires"])


def test_un_collaborateur_de_dre_ne_voit_que_sa_dre(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    connecter(client, creer_collaborateur, "national", CLUBS, None)
    creer(client, "Lycée Tokoin I")
    connecter(client, creer_collaborateur, "kara", LECTURE, "kara")

    page = client.get(DOUBLONS).json()

    assert TOKOIN not in noms(page["paires"])
    assert all(p["a"]["dre_code"] == p["b"]["dre_code"] == "kara" for p in page["paires"])
    assert set(page["par_dre"]) <= {"kara"}


def test_ecarter_puis_retablir_une_paire(national: TestClient, en_base: Callable[..., Any]) -> None:
    creer(national, "Lycée Tokoin I")
    (paire,) = [p for p in paires(national) if {p["a"]["nom"], p["b"]["nom"]} == TOKOIN]
    corps = {"a_id": paire["b"]["id"], "b_id": paire["a"]["id"]}

    assert national.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 204
    assert TOKOIN not in noms(paires(national))
    assert noms(paires(national, ecartees=True)) == [TOKOIN]
    assert paires(national, ecartees=True)[0]["ecartee"] is True
    assert national.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 409

    assert national.post(f"{DOUBLONS}/retablir", json=corps).status_code == 204
    assert TOKOIN in noms(paires(national))
    assert national.post(f"{DOUBLONS}/retablir", json=corps).status_code == 404
    (ecart,) = journal(en_base, "doublon_ecarte")
    assert {ecart.details["a_nom"], ecart.details["b_nom"]} == TOKOIN
    assert len(journal(en_base, "doublon_retabli")) == 1


def test_un_etablissement_inactif_nest_plus_propose(national: TestClient) -> None:
    cree = creer(national, "Lycée Tokoin I")

    national.patch(f"{ETABLISSEMENTS}/{cree['id']}", json={"version": cree["version"], "statut": "inactif"})

    assert TOKOIN not in noms(paires(national))


def test_les_ecarts_sont_reserves_au_droit_de_modifier_et_au_perimetre(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    connecter(client, creer_collaborateur, "national", CLUBS, None)
    cree = creer(client, "Lycée Tokoin I")
    corps = {"a_id": cree["id"], "b_id": etablissement(client, "Lycée de Tokoin I")["id"]}

    assert client.post(f"{DOUBLONS}/ecarter", json={"a_id": cree["id"], "b_id": cree["id"]}).status_code == 422
    connecter(client, creer_collaborateur, "lecteur", LECTURE, None)
    assert client.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 403
    connecter(client, creer_collaborateur, "kara", CLUBS, "kara")
    assert client.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 403
