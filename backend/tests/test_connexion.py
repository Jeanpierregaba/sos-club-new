import asyncio
import hashlib
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, Session, StatutCompte, TentativeConnexion, Utilisateur
from app.config import settings
from tests.conftest import MOT_DE_PASSE

CONNEXION = "/api/comptes/connexion"
INCORRECT = "Identifiant ou mot de passe incorrect"
TROP_D_ESSAIS = "Trop d'essais. Réessaie dans 15 minutes."


def se_connecter(client: TestClient, identifiant: str = "jeank", mot_de_passe: str = MOT_DE_PASSE, **options: Any):
    return client.post(CONNEXION, json={"identifiant": identifiant, "mot_de_passe": mot_de_passe}, **options)


def test_connexion_avec_identifiant(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    utilisateur = creer_utilisateur()

    reponse = se_connecter(client)

    assert reponse.status_code == 200
    assert reponse.json() == {
        "id": str(utilisateur.id),
        "identifiant": "jeank",
        "prenom": "Jean",
        "nom": "Kodjo",
        "role": "eleve",
    }
    assert reponse.headers["cache-control"] == "no-store"


def test_connexion_avec_email(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur("profk", Role.encadreur, email="prof@ecole.tg")

    assert se_connecter(client, "Prof@Ecole.TG").status_code == 200


@pytest.mark.parametrize("saisie", ["  JeanK ", "JEANK", "jeank\n"])
def test_majuscules_et_espaces_sans_effet(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], saisie: str
) -> None:
    creer_utilisateur()

    assert se_connecter(client, saisie).status_code == 200


def test_mot_de_passe_faux_et_compte_inconnu_donnent_la_meme_reponse(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur()

    faux = se_connecter(client, mot_de_passe="mauvais-mot-de-passe")
    inconnu = se_connecter(client, "inconnu")

    assert faux.status_code == inconnu.status_code == 401
    assert faux.json() == inconnu.json() == {"detail": INCORRECT}
    assert "set-cookie" not in faux.headers


def test_compte_suspendu_refuse_avec_le_bon_mot_de_passe(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur(statut=StatutCompte.suspendu)

    suspendu = se_connecter(client)
    faux = se_connecter(client, mot_de_passe="mauvais-mot-de-passe")

    assert suspendu.status_code == 403
    assert "encadreur" in suspendu.json()["detail"]
    assert "set-cookie" not in suspendu.headers
    # Sans le bon mot de passe, rien ne révèle que le compte est suspendu.
    assert faux.status_code == 401


def test_mot_de_passe_avec_accents_conserve_tel_quel(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur(mot_de_passe="Éléphant 42 !")

    assert se_connecter(client, mot_de_passe="Éléphant 42 !").status_code == 200
    assert se_connecter(client, mot_de_passe="Elephant 42 !").status_code == 401


def test_mot_de_passe_trop_long_refuse_sans_renvoyer_la_saisie(client: TestClient) -> None:
    trop_long = "secret-" + "x" * 256

    reponse = se_connecter(client, mot_de_passe=trop_long)

    assert reponse.status_code == 422
    assert trop_long not in reponse.text


@pytest.mark.parametrize(
    "corps", [{}, {"identifiant": "", "mot_de_passe": "x"}, {"identifiant": "x", "mot_de_passe": ""}]
)
def test_champ_vide_refuse(client: TestClient, corps: dict[str, str]) -> None:
    assert client.post(CONNEXION, json=corps).status_code == 422


def test_erreur_de_validation_ne_renvoie_jamais_le_mot_de_passe(client: TestClient) -> None:
    reponse = client.post(CONNEXION, json={"identifiant": "", "mot_de_passe": "mon-secret"})

    assert reponse.status_code == 422
    assert "mon-secret" not in reponse.text


def test_cookie_de_session_protege(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur()

    cookie = se_connecter(client).headers["set-cookie"].lower()

    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "secure" not in cookie
    assert "max-age=2592000" in cookie


def test_cookie_secure_des_que_le_site_est_en_https(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], monkeypatch: pytest.MonkeyPatch
) -> None:
    creer_utilisateur()
    monkeypatch.setattr(settings, "site_origine", "https://clubsante.tg")

    reponse = se_connecter(client, headers={"origin": "https://clubsante.tg"})

    assert "secure" in reponse.headers["set-cookie"].lower()


def test_la_base_ne_contient_aucun_secret(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    utilisateur = creer_utilisateur()

    jeton = se_connecter(client).cookies[settings.cookie_session]

    async def lire(db: AsyncSession) -> tuple[str, str]:
        session = await db.scalar(select(Session))
        empreinte = await db.scalar(select(Utilisateur.mot_de_passe_hash).where(Utilisateur.id == utilisateur.id))
        return session.jeton_hash, empreinte

    jeton_hash, empreinte = en_base(lire)
    assert jeton_hash == hashlib.sha256(jeton.encode()).hexdigest()
    assert jeton not in jeton_hash
    assert empreinte.startswith("$argon2id$")
    assert MOT_DE_PASSE not in empreinte


def test_cinq_echecs_bloquent_l_identifiant_meme_avec_le_bon_mot_de_passe(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur()
    creer_utilisateur("autre")

    for _ in range(5):
        assert se_connecter(client, mot_de_passe="mauvais-mot-de-passe").status_code == 401

    bloque = se_connecter(client)
    assert bloque.status_code == 429
    assert bloque.json() == {"detail": TROP_D_ESSAIS}
    assert se_connecter(client, "autre").status_code == 200


def test_les_identifiants_inconnus_sont_aussi_limites(client: TestClient) -> None:
    for _ in range(5):
        assert se_connecter(client, "inconnu").status_code == 401

    assert se_connecter(client, "INCONNU ").status_code == 429


def test_le_blocage_prend_fin_apres_la_fenetre(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    for _ in range(5):
        se_connecter(client, mot_de_passe="mauvais-mot-de-passe")

    async def vieillir(db: AsyncSession) -> None:
        await db.execute(update(TentativeConnexion).values(cree_le=datetime.now(UTC) - timedelta(minutes=16)))

    en_base(vieillir)

    assert se_connecter(client).status_code == 200


def test_une_connexion_reussie_efface_les_echecs_de_cet_identifiant(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur()
    for _ in range(4):
        se_connecter(client, mot_de_passe="mauvais-mot-de-passe")
    assert se_connecter(client).status_code == 200

    for _ in range(4):
        assert se_connecter(client, mot_de_passe="mauvais-mot-de-passe").status_code == 401


def test_une_classe_qui_se_connecte_correctement_n_est_jamais_bloquee(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    identifiants = [f"eleve{i}" for i in range(40)]
    empreinte = creer_utilisateur().mot_de_passe_hash

    async def inserer(db: AsyncSession) -> None:
        db.add_all(
            Utilisateur(identifiant=i, role=Role.eleve, prenom="A", nom="B", mot_de_passe_hash=empreinte)
            for i in identifiants
        )

    en_base(inserer)

    for identifiant in identifiants:
        assert se_connecter(client, identifiant).status_code == 200

    assert en_base(lambda db: db.scalar(select(func.count()).select_from(TentativeConnexion))) == 0


def test_les_echecs_de_plus_d_une_heure_sont_purges(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()

    async def inserer_ancien(db: AsyncSession) -> None:
        db.add(
            TentativeConnexion(
                cle_hash="a" * 64, adresse_ip="1.2.3.4", cree_le=datetime.now(UTC) - timedelta(minutes=61)
            )
        )

    en_base(inserer_ancien)

    se_connecter(client)

    assert en_base(lambda db: db.scalar(select(func.count()).select_from(TentativeConnexion))) == 0


def test_double_clic_sans_erreur(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur()

    async def plusieurs() -> list[int]:
        def une() -> int:
            return se_connecter(client).status_code

        return await asyncio.gather(*(asyncio.to_thread(une) for _ in range(2)))

    assert set(asyncio.run(plusieurs())) == {200}
