import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.comptes import creer_compte
from app.comptes.models import Utilisateur
from app.comptes.service import CompteInvalide
from tests.test_connexion import se_connecter

MOT_DE_PASSE = "mot-de-passe-secret"


def lancer(mot_de_passe: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "app.comptes.creer_compte", *arguments],
        cwd=Path(__file__).resolve().parents[1],
        input=f"{mot_de_passe}\n",
        capture_output=True,
        text=True,
        check=False,
    )


ADMIN = ("--role", "admin", "--identifiant", "chef", "--prenom", "Ama", "--nom", "Kodom", "--email", "Ama@Exemple.tg")


def compter(en_base: Callable[..., Any]) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(Utilisateur)))


def test_la_commande_cree_un_admin_qui_peut_se_connecter(client: TestClient) -> None:
    resultat = lancer(MOT_DE_PASSE, *ADMIN)

    assert resultat.returncode == 0, resultat.stderr
    assert MOT_DE_PASSE not in resultat.stdout + resultat.stderr

    reponse = se_connecter(client, "chef", MOT_DE_PASSE)
    assert reponse.status_code == 200
    assert reponse.json()["role"] == "admin"
    assert se_connecter(client, "ama@exemple.tg", MOT_DE_PASSE).status_code == 200


def test_un_admin_cree_en_ligne_de_commande_est_super_administrateur(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    from app.admin.models import Collaborateur

    assert lancer(MOT_DE_PASSE, *ADMIN).returncode == 0

    collaborateur = en_base(lambda db: db.scalar(select(Collaborateur)))
    assert collaborateur.super_admin and collaborateur.perimetre_dre is None
    se_connecter(client, "chef", MOT_DE_PASSE)
    # Super-administrateur : la double authentification est à activer avant toute autre page.
    assert client.get("/api/admin/moi").json()["double_auth_requise"] is True


def test_la_commande_cree_un_eleve_sans_email(client: TestClient) -> None:
    resultat = lancer(MOT_DE_PASSE, "--role", "eleve", "--identifiant", "Jean.K", "--prenom", "Jean", "--nom", "K")

    assert resultat.returncode == 0, resultat.stderr
    assert se_connecter(client, "jean.k", MOT_DE_PASSE).status_code == 200


@pytest.mark.parametrize(
    ("mot_de_passe", "arguments", "message"),
    [
        ("court", ADMIN, "8 caractères"),
        ("x" * 257, ADMIN, "256 caractères"),
        (MOT_DE_PASSE, ("--role", "admin", "--identifiant", "chef", "--prenom", "A", "--nom", "B"), "email"),
        (MOT_DE_PASSE, ("--role", "eleve", "--identifiant", "a@b", "--prenom", "A", "--nom", "B"), "identifiant"),
        (MOT_DE_PASSE, ("--role", "eleve", "--identifiant", "ab", "--prenom", "A", "--nom", "B"), "identifiant"),
        (MOT_DE_PASSE, ("--role", "eleve", "--identifiant", "abc", "--prenom", " ", "--nom", "B"), "prénom"),
        (MOT_DE_PASSE, (*ADMIN[:-1], "pas-un-email"), "email"),
        (MOT_DE_PASSE, (*ADMIN, "--telephone", "1" * 40), "téléphone"),
    ],
)
def test_la_commande_refuse_les_comptes_invalides(
    en_base: Callable[..., Any], mot_de_passe: str, arguments: tuple[str, ...], message: str
) -> None:
    resultat = lancer(mot_de_passe, *arguments)

    assert resultat.returncode == 1
    assert message in resultat.stderr
    assert mot_de_passe not in resultat.stdout + resultat.stderr
    assert compter(en_base) == 0


def test_la_commande_ne_cree_pas_dencadreur(en_base: Callable[..., Any]) -> None:
    arguments = ("--role", "encadreur", "--identifiant", "prof", "--prenom", "A", "--nom", "B", "--email", "p@e.tg")

    resultat = lancer(MOT_DE_PASSE, *arguments)

    assert resultat.returncode == 2
    assert "--role" in resultat.stderr
    assert compter(en_base) == 0


def test_la_commande_refuse_un_identifiant_deja_pris(en_base: Callable[..., Any]) -> None:
    assert lancer(MOT_DE_PASSE, *ADMIN).returncode == 0

    resultat = lancer(MOT_DE_PASSE, "--role", "eleve", "--identifiant", "CHEF", "--prenom", "A", "--nom", "B")

    assert resultat.returncode == 1
    assert "identifiant" in resultat.stderr
    assert compter(en_base) == 1


def test_la_commande_refuse_un_email_deja_pris(en_base: Callable[..., Any]) -> None:
    assert lancer(MOT_DE_PASSE, *ADMIN).returncode == 0

    resultat = lancer(
        MOT_DE_PASSE,
        *("--role", "admin", "--identifiant", "autre", "--prenom", "A", "--nom", "B", "--email", "ama@exemple.tg"),
    )

    assert resultat.returncode == 1
    assert "email" in resultat.stderr
    assert compter(en_base) == 1


def test_en_interactif_le_mot_de_passe_est_lu_sans_affichage(monkeypatch: pytest.MonkeyPatch) -> None:
    saisies = iter([MOT_DE_PASSE, MOT_DE_PASSE])
    monkeypatch.setattr(creer_compte.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(creer_compte.getpass, "getpass", lambda _: next(saisies))

    assert creer_compte._lire_mot_de_passe() == MOT_DE_PASSE


def test_en_interactif_deux_saisies_differentes_sont_refusees(monkeypatch: pytest.MonkeyPatch) -> None:
    saisies = iter([MOT_DE_PASSE, "autre-mot-de-passe"])
    monkeypatch.setattr(creer_compte.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(creer_compte.getpass, "getpass", lambda _: next(saisies))

    with pytest.raises(CompteInvalide, match="différents"):
        creer_compte._lire_mot_de_passe()
