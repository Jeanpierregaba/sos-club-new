"""« Mot de passe oublié » par e-mail (spec 039) : adresses fiables seulement, réponse identique, lien à usage unique
de 30 minutes stocké en empreinte, sessions coupées. Partie critique (comptes, jetons), écrite avant le code."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.comptes.models import LienMotDePasse, Role, StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from tests.conftest import MOT_DE_PASSE, Navigateur

pytestmark = pytest.mark.usefixtures("annuaire")

OUBLI = "/api/comptes/mot-de-passe-oublie"
REPONSE = "Si cette adresse correspond à un compte, un lien vient d'y être envoyé."


@pytest.fixture
def envois(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Les e-mails partis : (destinataire, texte)."""
    partis: list[tuple[str, str]] = []

    async def envoyer(destinataire: str, sujet: str, texte: str, html: str | None = None) -> None:
        partis.append((destinataire, texte))

    monkeypatch.setattr("app.comptes.oubli.envoyer", envoyer)
    return partis


@pytest.fixture
def comptes(
    creer_encadreur: Callable[..., Utilisateur],
    creer_utilisateur: Callable[..., Utilisateur],
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Utilisateur]:
    comptes = {
        "encadreur": creer_encadreur("prof"),
        "attente": creer_encadreur("nouveau", etat=EtatVerification.en_attente),
        "visiteur": creer_utilisateur("visiteur", Role.visiteur, email="visiteur@exemple.tg"),
        "non_confirme": creer_utilisateur("curieux", Role.visiteur, email="curieux@exemple.tg"),
        "eleve": creer_eleve("eleve1", "Yao"),
        "admin": creer_collaborateur("chef"),
    }
    maintenant = datetime.now(UTC)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == comptes["visiteur"].id).values(email_confirme_le=maintenant)
        )
    )
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == comptes["eleve"].id).values(email="eleve@exemple.tg")
        )
    )
    return comptes


def demander(client: TestClient, email: str) -> Any:
    return Navigateur(client).post(OUBLI, json={"email": email})


def jeton_de(envoi: tuple[str, str]) -> str:
    lien = next(mot for mot in envoi[1].split() if "/mot-de-passe/nouveau" in mot)
    return parse_qs(urlsplit(lien.strip("()<>.")).query)["jeton"][0]


def choisir(client: TestClient, jeton: str, nouveau: str = "un-nouveau-secret") -> Any:
    return Navigateur(client).post(f"{OUBLI}/choix", json={"jeton": jeton, "nouveau": nouveau})


def valide(client: TestClient, jeton: str) -> Any:
    return Navigateur(client).post(f"{OUBLI}/verification", json={"jeton": jeton}).json()


@pytest.mark.parametrize("qui", ["encadreur", "visiteur"])
def test_un_compte_fiable_recoit_un_lien(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, qui: str
) -> None:
    reponse = demander(client, f"  {comptes[qui].email.upper()} ")

    assert reponse.status_code == 202
    assert reponse.json() == {"message": REPONSE}
    ((destinataire, texte),) = envois
    assert destinataire == comptes[qui].email and "30 minutes" in texte


@pytest.mark.parametrize(
    "email",
    ["inconnu@exemple.tg", "eleve@exemple.tg", "curieux@exemple.tg", "nouveau@ecole.tg", "chef@aimes.tg"],
)
def test_aucun_lien_pour_les_autres_et_la_meme_reponse(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, email: str, en_base: Callable[..., Any]
) -> None:
    reponse = demander(client, email)

    assert (reponse.status_code, reponse.json()) == (202, {"message": REPONSE})
    assert envois == []
    assert en_base(lambda db: db.scalars(select(LienMotDePasse))).all() == []


def test_un_compte_suspendu_ne_recoit_rien(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, en_base: Callable[..., Any]
) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == comptes["encadreur"].id).values(statut=StatutCompte.suspendu)
        )
    )

    assert demander(client, "prof@ecole.tg").status_code == 202
    assert envois == []


def test_le_lien_change_le_mot_de_passe_et_coupe_les_sessions(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, en_base: Callable[..., Any]
) -> None:
    ouverte = Navigateur(client)
    ouverte.post("/api/comptes/connexion", json={"identifiant": "prof", "mot_de_passe": MOT_DE_PASSE})
    demander(client, "prof@ecole.tg")
    jeton = jeton_de(envois[0])

    assert valide(client, jeton) == {"valide": True}
    assert choisir(client, jeton).status_code == 204

    assert ouverte.get("/api/comptes/moi").status_code == 401
    nouvelle = Navigateur(client).post(
        "/api/comptes/connexion", json={"identifiant": "prof", "mot_de_passe": "un-nouveau-secret"}
    )
    assert nouvelle.status_code == 200 and nouvelle.json()["mot_de_passe_provisoire"] is False
    assert choisir(client, jeton).status_code == 410
    assert valide(client, jeton) == {"valide": False}
    compte = en_base(lambda db: db.get(Utilisateur, comptes["encadreur"].id))
    assert compte.email_confirme_le is not None
    actions = set(en_base(lambda db: db.scalars(select(JournalAudit.action))).all())
    assert {"lien_mot_de_passe_envoye", "mot_de_passe_choisi"} <= actions


def test_le_jeton_nest_stocke_quen_empreinte(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, en_base: Callable[..., Any]
) -> None:
    demander(client, "prof@ecole.tg")
    jeton = jeton_de(envois[0])

    (lien,) = en_base(lambda db: db.scalars(select(LienMotDePasse))).all()

    assert jeton not in lien.jeton_hash and len(lien.jeton_hash) == 64


def test_un_lien_remplace_ou_expire_est_refuse(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, en_base: Callable[..., Any]
) -> None:
    demander(client, "prof@ecole.tg")
    demander(client, "prof@ecole.tg")
    ancien, recent = jeton_de(envois[0]), jeton_de(envois[1])

    assert choisir(client, ancien).status_code == 410

    en_base(lambda db: db.execute(update(LienMotDePasse).values(expire_le=datetime.now(UTC) - timedelta(seconds=1))))
    assert choisir(client, recent).status_code == 410


def test_un_compte_suspendu_entre_temps_ne_change_rien(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list, en_base: Callable[..., Any]
) -> None:
    demander(client, "prof@ecole.tg")
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == comptes["encadreur"].id).values(statut=StatutCompte.suspendu)
        )
    )

    assert choisir(client, jeton_de(envois[0])).status_code == 410


def test_un_mot_de_passe_trop_court_est_refuse(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list
) -> None:
    demander(client, "prof@ecole.tg")

    assert choisir(client, jeton_de(envois[0]), "court").status_code == 422


def test_la_quatrieme_demande_de_lheure_nenvoie_rien(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list
) -> None:
    for _ in range(4):
        assert demander(client, "prof@ecole.tg").status_code == 202

    assert len(envois) == 3


def test_un_jeton_inconnu_est_refuse(client: TestClient, comptes: dict[str, Utilisateur]) -> None:
    assert choisir(client, "x" * 43).status_code == 410
    assert valide(client, "x" * 43) == {"valide": False}


def test_une_meme_adresse_ip_est_limitee(client: TestClient, comptes: dict[str, Utilisateur], envois: list) -> None:
    from app.config import settings

    codes = [demander(client, f"inconnu{i}@exemple.tg").status_code for i in range(settings.oubli_max_adresse + 1)]

    assert codes[-1] == 429 and set(codes[:-1]) == {202}


def test_une_saisie_didentifiant_ne_peut_pas_bloquer_une_adresse_ip(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list
) -> None:
    """Le compteur des demandes de lien n'est pas joignable par une connexion à l'identifiant forgé."""
    for _ in range(10):
        Navigateur(client).post("/api/comptes/connexion", json={"identifiant": "OUBLI:testclient", "mot_de_passe": "x"})

    assert demander(client, "prof@ecole.tg").status_code == 202
    assert len(envois) == 1


def test_changer_son_mot_de_passe_annule_un_lien_ouvert(
    client: TestClient, comptes: dict[str, Utilisateur], envois: list
) -> None:
    demander(client, "prof@ecole.tg")
    session = Navigateur(client)
    session.post("/api/comptes/connexion", json={"identifiant": "prof", "mot_de_passe": MOT_DE_PASSE})
    session.post("/api/comptes/mot-de-passe", json={"actuel": MOT_DE_PASSE, "nouveau": "un-autre-secret"})

    assert choisir(client, jeton_de(envois[0])).status_code == 410


def test_le_jeton_ne_passe_jamais_dans_ladresse(client: TestClient) -> None:
    from app.main import app

    chemins = {route.path for route in app.routes if "mot-de-passe-oublie" in getattr(route, "path", "")}
    assert all("{" not in chemin for chemin in chemins), chemins
