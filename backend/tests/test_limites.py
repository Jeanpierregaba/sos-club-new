import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes import service
from app.comptes.models import Role, TentativeConnexion, Utilisateur
from app.comptes.service import cle_adresse
from app.db import engine
from app.main import app
from tests.conftest import MOT_DE_PASSE
from tests.test_connexion import se_connecter

FAUX = "mauvais-mot-de-passe"


def espionner(monkeypatch: pytest.MonkeyPatch, nom: str) -> list[str]:
    appels: list[str] = []
    originale = getattr(service, nom)

    async def espion(*arguments: str) -> bool:
        appels.append(arguments[-1])
        return await originale(*arguments)

    monkeypatch.setattr(service, nom, espion)
    return appels


def rafale(client: TestClient, mots_de_passe: list[str], identifiant: str = "jeank") -> list[int]:
    async def envoyer() -> list[int]:
        def une(mot_de_passe: str) -> int:
            return se_connecter(client, identifiant, mot_de_passe).status_code

        return await asyncio.gather(*(asyncio.to_thread(une, m) for m in mots_de_passe))

    return asyncio.run(envoyer())


def test_une_rafale_ne_teste_pas_plus_de_cinq_mots_de_passe(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], monkeypatch: pytest.MonkeyPatch
) -> None:
    creer_utilisateur()
    testes = espionner(monkeypatch, "verifier")

    statuts = rafale(client, [FAUX] * 16)

    assert len(testes) <= 5
    assert statuts.count(401) == len(testes)
    assert statuts.count(401) + statuts.count(429) == 16

    # Une rafale peut refuser trop d'essais, jamais en accepter trop : le total reste de 5 échecs.
    for _ in range(5 - len(testes)):
        assert se_connecter(client, mot_de_passe=FAUX).status_code == 401
    assert se_connecter(client).status_code == 429
    assert len(testes) == 5


def test_la_rafale_ne_compte_que_ses_propres_essais_pour_un_autre_compte(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur()
    creer_utilisateur("autre")

    rafale(client, [FAUX] * 16)

    assert se_connecter(client, "autre").status_code == 200


def test_identifiant_et_email_partagent_le_meme_compteur(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("profk", Role.encadreur, email="prof@ecole.tg")
    for _ in range(3):
        assert se_connecter(client, "profk", FAUX).status_code == 401
    for _ in range(2):
        assert se_connecter(client, "prof@ecole.tg", FAUX).status_code == 401

    assert se_connecter(client, "profk").status_code == 429
    assert se_connecter(client, "prof@ecole.tg").status_code == 429


def test_une_reussite_par_email_efface_les_echecs_par_identifiant(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("profk", Role.encadreur, email="prof@ecole.tg")
    for _ in range(4):
        se_connecter(client, "profk", FAUX)

    assert se_connecter(client, "prof@ecole.tg").status_code == 200

    for _ in range(4):
        assert se_connecter(client, "profk", FAUX).status_code == 401


@pytest.mark.parametrize("saisie", ["İ" * 254, "jeank\u0000", "\u0000"])
def test_saisie_piegee_refusee_sans_hachage_ni_erreur_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, saisie: str
) -> None:
    factices = espionner(monkeypatch, "verifier_factice")

    reponse = se_connecter(client, saisie)

    assert reponse.status_code == 422
    assert factices == []


def test_identifiant_de_longueur_maximale_accepte(client: TestClient) -> None:
    assert se_connecter(client, "a" * 254).status_code == 401


def test_les_erreurs_de_base_n_affichent_pas_les_parametres() -> None:
    assert engine.sync_engine.hide_parameters


def test_compte_inconnu_prend_le_temps_d_une_verification(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], monkeypatch: pytest.MonkeyPatch
) -> None:
    creer_utilisateur()
    factices = espionner(monkeypatch, "verifier_factice")

    se_connecter(client, "inconnu", FAUX)
    assert factices == [FAUX]

    se_connecter(client, "jeank", FAUX)
    assert factices == [FAUX]


def test_un_echec_garde_l_adresse_reelle_et_le_seuil_de_50_est_exact(
    creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()

    with TestClient(app, client=("203.0.113.9", 50000)) as client:
        for i in range(49):
            assert se_connecter(client, f"inconnu{i}").status_code == 401
        # Au 49e échec, l'adresse n'est pas encore bloquée : ce 50e essai est encore évalué.
        assert se_connecter(client, "inconnu49").status_code == 401
        assert se_connecter(client).status_code == 429

    adresses = en_base(lambda db: _adresses(db))
    assert adresses == {"203.0.113.9"}

    with TestClient(app, client=("203.0.113.10", 50000)) as autre:
        assert se_connecter(autre).status_code == 200


async def _adresses(db: AsyncSession) -> set[str]:
    return set(await db.scalars(select(TentativeConnexion.adresse_ip)))


def test_les_essais_en_cours_ne_bloquent_pas_une_adresse(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()

    async def inserer(db: AsyncSession) -> None:
        db.add_all(
            TentativeConnexion(cle_hash=f"{i:064}", adresse_ip=cle_adresse("testclient"), en_cours=True)
            for i in range(60)
        )

    en_base(inserer)

    assert se_connecter(client).status_code == 200


def test_une_classe_simultanee_n_est_pas_bloquee(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    empreinte = creer_utilisateur().mot_de_passe_hash
    identifiants = [f"eleve{i}" for i in range(60)]

    async def inserer(db: AsyncSession) -> None:
        db.add_all(
            Utilisateur(identifiant=i, role=Role.eleve, prenom="A", nom="B", mot_de_passe_hash=empreinte)
            for i in identifiants
        )

    en_base(inserer)

    async def envoyer() -> list[int]:
        def une(identifiant: str) -> int:
            return se_connecter(client, identifiant).status_code

        return await asyncio.gather(*(asyncio.to_thread(une, i) for i in identifiants))

    assert set(asyncio.run(envoyer())) == {200}


def test_un_echec_de_14_minutes_compte_encore(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    for _ in range(5):
        se_connecter(client, mot_de_passe=FAUX)

    async def vieillir(db: AsyncSession) -> None:
        await db.execute(update(TentativeConnexion).values(cree_le=datetime.now(UTC) - timedelta(minutes=14)))

    en_base(vieillir)

    assert se_connecter(client).status_code == 429


def test_la_saisie_n_est_pas_gardee_en_clair(client: TestClient, en_base: Callable[..., Any]) -> None:
    # Un élève peut taper son mot de passe dans le champ identifiant par erreur.
    se_connecter(client, "Mon-Secret-Tape-Au-Mauvais-Endroit")

    cles = en_base(lambda db: _cles(db))
    assert len(cles) == 1
    assert "secret" not in cles[0].lower()
    assert len(cles[0]) == 64


async def _cles(db: AsyncSession) -> list[str]:
    return list(await db.scalars(select(TentativeConnexion.cle_hash)))


def test_un_echec_purge_aussi_les_echecs_de_plus_d_une_heure(client: TestClient, en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(
            TentativeConnexion(
                cle_hash="a" * 64,
                adresse_ip="1.2.3.4",
                en_cours=False,
                cree_le=datetime.now(UTC) - timedelta(minutes=61),
            )
        )
        db.add(
            TentativeConnexion(
                cle_hash="b" * 64,
                adresse_ip="1.2.3.4",
                en_cours=False,
                cree_le=datetime.now(UTC) - timedelta(minutes=59),
            )
        )

    en_base(inserer)

    se_connecter(client, "inconnu", FAUX)

    cles = en_base(lambda db: _cles(db))
    assert "a" * 64 not in cles
    assert "b" * 64 in cles


def test_l_empreinte_faible_est_remplacee_a_la_connexion(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    utilisateur = creer_utilisateur()
    faible = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(MOT_DE_PASSE)

    async def affaiblir(db: AsyncSession) -> None:
        await db.execute(update(Utilisateur).values(mot_de_passe_hash=faible))

    en_base(affaiblir)

    assert se_connecter(client).status_code == 200

    nouvelle = en_base(
        lambda db: db.scalar(select(Utilisateur.mot_de_passe_hash).where(Utilisateur.id == utilisateur.id))
    )
    assert nouvelle != faible
    assert se_connecter(client).status_code == 200


@pytest.mark.parametrize(
    ("hote", "cle"),
    [
        ("203.0.113.9", "203.0.113.9"),
        ("2001:db8:1:2:aaaa::1", "2001:db8:1:2::/64"),
        ("2001:db8:1:2:bbbb::9", "2001:db8:1:2::/64"),
        ("x" * 60, "inconnue"),
        ("testclient", "inconnue"),
        (None, "inconnue"),
    ],
)
def test_cle_d_adresse_reseau(hote: str | None, cle: str) -> None:
    assert cle_adresse(hote) == cle
