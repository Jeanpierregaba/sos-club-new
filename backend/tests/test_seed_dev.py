"""Seed des comptes de développement : base locale seulement, accès utilisables tels quels."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.comptes.models import Utilisateur
from app.config import settings
from app.seed_dev import COMPTES, ProductionRefusee, ecrire_fichier, semer

pytestmark = pytest.mark.usefixtures("annuaire")


def acces_de(acces: list[dict[str, str]], identifiant: str) -> dict[str, str]:
    return next(a for a in acces if a["identifiant"] == identifiant)


def test_le_seed_cree_un_compte_par_profil(client: TestClient, en_base: Callable[..., Any]) -> None:
    acces = en_base(semer)

    assert len(acces) == len(COMPTES)
    comptes = select(func.count()).select_from(Utilisateur).where(Utilisateur.identifiant.like("dev.%"))
    assert en_base(lambda db: db.scalar(comptes)) == len(COMPTES)


def test_un_super_admin_se_connecte_avec_le_secret_ecrit(client: TestClient, en_base: Callable[..., Any]) -> None:
    super_admin = acces_de(en_base(semer), "dev.superadmin")

    etape = client.post(
        "/api/comptes/connexion", json={"identifiant": "dev.superadmin", "mot_de_passe": super_admin["mot_de_passe"]}
    ).json()
    code = pyotp.TOTP(super_admin["secret_totp"]).now()
    reponse = client.post("/api/comptes/connexion/code", json={"jeton": etape["jeton"], "code": code})

    assert reponse.status_code == 200
    assert client.get("/api/admin/collaborateurs").status_code == 200


def test_un_analyste_se_connecte_sans_code(client: TestClient, en_base: Callable[..., Any]) -> None:
    analyste = acces_de(en_base(semer), "dev.analyste")

    assert "secret_totp" not in analyste
    client.post(
        "/api/comptes/connexion", json={"identifiant": "dev.analyste", "mot_de_passe": analyste["mot_de_passe"]}
    )
    assert client.get("/api/admin/tableau-de-bord").status_code == 200
    assert client.get("/api/admin/inscrits").status_code == 403


def test_relancer_change_les_mots_de_passe(client: TestClient, en_base: Callable[..., Any]) -> None:
    ancien = acces_de(en_base(semer), "dev.eleve1")["mot_de_passe"]
    nouveau = acces_de(en_base(semer), "dev.eleve1")["mot_de_passe"]

    assert ancien != nouveau
    assert (
        client.post("/api/comptes/connexion", json={"identifiant": "dev.eleve1", "mot_de_passe": ancien}).status_code
        == 401
    )
    assert (
        client.post("/api/comptes/connexion", json={"identifiant": "dev.eleve1", "mot_de_passe": nouveau}).status_code
        == 200
    )


def test_refuse_en_production(en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "site_origine", "https://clubs-sante.tg")

    with pytest.raises(ProductionRefusee):
        en_base(semer)


def test_le_fichier_d_acces_est_prive(en_base: Callable[..., Any], tmp_path: Path) -> None:
    chemin = tmp_path / "acces.local"

    ecrire_fichier(en_base(semer), chemin)

    assert oct(chemin.stat().st_mode & 0o777) == "0o600"
    texte = chemin.read_text()
    assert "[dev.superadmin] Super-administrateur" in texte
    assert "identifiant    : dev.superadmin" in texte
    assert "e-mail         : dev.superadmin@exemple.tg" in texte


def test_un_super_admin_se_connecte_aussi_par_e_mail(client: TestClient, en_base: Callable[..., Any]) -> None:
    super_admin = acces_de(en_base(semer), "dev.superadmin")

    reponse = client.post(
        "/api/comptes/connexion",
        json={"identifiant": super_admin["email"], "mot_de_passe": super_admin["mot_de_passe"]},
    )

    assert reponse.json()["etape"] == "code"


def test_les_eleves_ont_un_profil_et_leur_bienvenue(client: TestClient, en_base: Callable[..., Any]) -> None:
    en_base(semer)
    # Relancé : ni second profil, ni seconde ligne de bienvenue, ni second semestre.
    eleve = acces_de(en_base(semer), "dev.eleve1")
    client.post("/api/comptes/connexion", json={"identifiant": "dev.eleve1", "mot_de_passe": eleve["mot_de_passe"]})

    espace = client.get("/api/eleves/moi").json()

    assert espace["pseudonyme"] == "Ama du Golfe"
    assert espace["etablissement"]["nom"] == "Lycée de Tokoin I"
    assert espace["points"]["semestre"] is not None
    assert (espace["points"]["points_semestre"], espace["points"]["total"]) == (100, 100)
