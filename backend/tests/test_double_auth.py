"""Double authentification de l'espace administrateur (spec 015, ADR-0008)."""

import time
from collections.abc import Callable
from typing import Any

import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.models import CodeSecours, DoubleAuth
from app.comptes.models import Session
from tests.conftest import MOT_DE_PASSE, code_totp, connecter_admin

CONNEXION = "/api/comptes/connexion"
CODE = "/api/comptes/connexion/code"
ANALYSTE = {("tableau_de_bord", "consulter"), ("statistiques", "consulter")}


def etape(client: TestClient, identifiant: str = "chef") -> str:
    reponse = client.post(CONNEXION, json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["etape"] == "code"
    return corps["jeton"]


def compter_sessions(en_base: Callable[..., Any]) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(Session)))


# Connexion en deux étapes ---------------------------------------------------------------------------------------


def test_mot_de_passe_juste_ne_suffit_pas(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)

    etape(client)

    assert compter_sessions(en_base) == 0
    assert "session_sosclub" not in client.cookies
    assert client.get("/api/admin/moi").status_code == 401


def test_code_juste_ouvre_la_session(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    jeton = etape(client)

    reponse = client.post(CODE, json={"jeton": jeton, "code": code_totp()})

    assert reponse.status_code == 200
    assert reponse.json()["identifiant"] == "chef"
    assert client.get("/api/admin/moi").status_code == 200


def test_code_faux_refuse(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    jeton = etape(client)

    reponse = client.post(CODE, json={"jeton": jeton, "code": "000000" if code_totp() != "000000" else "111111"})

    assert reponse.status_code == 401
    assert compter_sessions(en_base) == 0


def test_un_code_ne_sert_qu_une_fois(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    code = code_totp()
    assert client.post(CODE, json={"jeton": etape(client), "code": code}).status_code == 200

    client.cookies.clear()
    reponse = client.post(CODE, json={"jeton": etape(client), "code": code})

    assert reponse.status_code == 401


def test_jeton_d_etape_inconnu(client: TestClient) -> None:
    reponse = client.post(CODE, json={"jeton": "inconnu", "code": "123456"})

    assert reponse.status_code == 401
    assert "Reconnecte-toi" in reponse.json()["detail"]


def test_le_jeton_d_etape_ne_sert_qu_une_fois(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    jeton = etape(client)
    assert client.post(CODE, json={"jeton": jeton, "code": code_totp()}).status_code == 200

    assert client.post(CODE, json={"jeton": jeton, "code": code_totp(1)}).status_code == 401


def test_cinq_codes_faux_bloquent_l_etape(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    faux = "000000" if code_totp() != "000000" else "111111"
    for _ in range(5):
        jeton = etape(client)
        assert client.post(CODE, json={"jeton": jeton, "code": faux}).status_code == 401

    reponse = client.post(CODE, json={"jeton": etape(client), "code": code_totp()})

    assert reponse.status_code == 429


# Enrôlement -----------------------------------------------------------------------------------------------------


def enroler(client: TestClient) -> tuple[str, list[str]]:
    reponse = client.post("/api/admin/double-auth/enrolement")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["qr_svg"].startswith("<svg")
    secret = corps["secret"]
    confirmation = client.post("/api/admin/double-auth/confirmer", json={"code": pyotp.TOTP(secret).now()})
    assert confirmation.status_code == 200
    return secret, confirmation.json()["codes"]


def test_enrolement_puis_acces(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True)
    connecter_admin(client)
    assert client.get("/api/admin/moi").json()["double_auth_requise"] is True

    _, codes = enroler(client)

    assert len(codes) == 10
    assert len(set(codes)) == 10
    assert client.get("/api/admin/moi").json()["double_auth_requise"] is False
    assert client.get("/api/admin/collaborateurs").status_code == 200


def test_le_secret_est_chiffre_en_base(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    chef = creer_collaborateur(super_admin=True)
    connecter_admin(client)
    secret, _ = enroler(client)

    stocke = en_base(
        lambda db: db.scalar(select(DoubleAuth.secret_chiffre).where(DoubleAuth.utilisateur_id == chef.id))
    )

    assert secret not in stocke


def test_codes_de_secours_hashes_et_a_usage_unique(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True)
    connecter_admin(client)
    _, codes = enroler(client)
    empreintes = en_base(lambda db: db.scalars(select(CodeSecours.code_hash))).all()
    assert not set(codes) & set(empreintes)
    client.post("/api/comptes/deconnexion")

    assert client.post(CODE, json={"jeton": etape(client), "code": codes[0].upper()}).status_code == 200
    client.post("/api/comptes/deconnexion")
    assert client.post(CODE, json={"jeton": etape(client), "code": codes[0]}).status_code == 401


def test_confirmation_avec_code_faux(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True)
    connecter_admin(client)
    secret = client.post("/api/admin/double-auth/enrolement").json()["secret"]
    faux = pyotp.TOTP(secret).at(time.time() - 3600)

    assert client.post("/api/admin/double-auth/confirmer", json={"code": faux}).status_code == 422
    assert client.get("/api/admin/moi").json()["double_auth_active"] is False


def test_enrolement_refuse_si_deja_active(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)

    assert client.post("/api/admin/double-auth/enrolement").status_code == 409


def test_regenerer_les_codes_exige_le_code(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)

    assert client.post("/api/admin/double-auth/codes-secours", json={"code": "999999"}).status_code == 422
    reponse = client.post("/api/admin/double-auth/codes-secours", json={"code": code_totp(1)})
    assert reponse.status_code == 200
    assert len(reponse.json()["codes"]) == 10


def test_compte_sans_droit_sensible_se_connecte_sans_code(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=ANALYSTE)

    reponse = client.post(CONNEXION, json={"identifiant": "chef", "mot_de_passe": MOT_DE_PASSE})

    assert reponse.status_code == 200
    assert "etape" not in reponse.json()
