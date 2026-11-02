from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, Session, StatutCompte, Utilisateur
from app.config import settings
from tests.conftest import MOT_DE_PASSE
from tests.test_connexion import se_connecter

MOI = "/api/comptes/moi"
DECONNEXION = "/api/comptes/deconnexion"


def compter_sessions(en_base: Callable[..., Any]) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(Session)))


def test_moi_renvoie_l_utilisateur_connecte(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur()
    se_connecter(client)

    reponse = client.get(MOI)

    assert reponse.status_code == 200
    assert reponse.json()["identifiant"] == "jeank"
    assert "mot_de_passe_hash" not in reponse.json()
    assert reponse.headers["cache-control"] == "no-store"


def test_moi_sans_session(client: TestClient) -> None:
    assert client.get(MOI).status_code == 401


def test_moi_avec_un_jeton_inconnu(client: TestClient) -> None:
    client.cookies.set(settings.cookie_session, "jeton-invente")

    assert client.get(MOI).status_code == 401


@pytest.mark.parametrize(
    ("role", "email", "duree"),
    [
        (Role.eleve, None, timedelta(days=30)),
        (Role.encadreur, "prof@ecole.tg", timedelta(days=30)),
        (Role.admin, "admin@ecole.tg", timedelta(hours=12)),
    ],
)
def test_duree_de_session_selon_le_role(
    client: TestClient,
    creer_utilisateur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    role: Role,
    email: str | None,
    duree: timedelta,
) -> None:
    creer_utilisateur(role=role, email=email)

    reponse = se_connecter(client)

    expire_le = en_base(lambda db: db.scalar(select(Session.expire_le)))
    assert abs(expire_le - datetime.now(UTC) - duree) < timedelta(minutes=1)
    assert f"max-age={int(duree.total_seconds())}" in reponse.headers["set-cookie"].lower()


def test_session_expiree_refusee(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    se_connecter(client)

    async def expirer(db: AsyncSession) -> None:
        await db.execute(update(Session).values(expire_le=datetime.now(UTC) - timedelta(seconds=1)))

    en_base(expirer)

    assert client.get(MOI).status_code == 401


def test_session_supprimee_refusee_immediatement(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    se_connecter(client)
    assert client.get(MOI).status_code == 200

    async def supprimer(db: AsyncSession) -> None:
        await db.execute(delete(Session))

    en_base(supprimer)

    assert client.get(MOI).status_code == 401


def test_compte_suspendu_perd_l_acces_immediatement(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    se_connecter(client)

    async def suspendre(db: AsyncSession) -> None:
        await db.execute(update(Utilisateur).values(statut=StatutCompte.suspendu))

    en_base(suspendre)

    assert client.get(MOI).status_code == 401


def test_deconnexion_supprime_la_session_en_base(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    jeton = se_connecter(client).cookies[settings.cookie_session]

    reponse = client.post(DECONNEXION)

    assert reponse.status_code == 204
    assert 'session_sosclub=""' in reponse.headers["set-cookie"] or "max-age=0" in reponse.headers["set-cookie"].lower()
    assert compter_sessions(en_base) == 0

    # Réutiliser l'ancien cookie ne rouvre rien.
    client.cookies.set(settings.cookie_session, jeton)
    assert client.get(MOI).status_code == 401


def test_deconnexion_sans_session_ne_provoque_pas_d_erreur(client: TestClient) -> None:
    assert client.post(DECONNEXION).status_code == 204


def ouvrir_deux_appareils(client: TestClient) -> tuple[str, str]:
    jetons = []
    for _ in range(2):
        # Sans cookie, cette connexion ressemble à celle d'un autre appareil.
        client.cookies.clear()
        jetons.append(se_connecter(client).cookies[settings.cookie_session])
    client.cookies.clear()
    return jetons[0], jetons[1]


def statut_avec_jeton(client: TestClient, jeton: str) -> int:
    client.cookies.set(settings.cookie_session, jeton)
    statut = client.get(MOI).status_code
    client.cookies.clear()
    return statut


def test_deconnexion_ne_touche_pas_les_autres_appareils(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur()
    premier, deuxieme = ouvrir_deux_appareils(client)

    client.cookies.set(settings.cookie_session, premier)
    client.post(DECONNEXION)
    client.cookies.clear()

    assert statut_avec_jeton(client, premier) == 401
    assert statut_avec_jeton(client, deuxieme) == 200


def test_deuxieme_appareil_ne_deconnecte_pas_le_premier(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    premier, deuxieme = ouvrir_deux_appareils(client)

    assert statut_avec_jeton(client, premier) == 200
    assert statut_avec_jeton(client, deuxieme) == 200
    assert compter_sessions(en_base) == 2


def test_se_reconnecter_remplace_la_session_du_navigateur(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    premier_jeton = se_connecter(client).cookies[settings.cookie_session]

    deuxieme_jeton = se_connecter(client).cookies[settings.cookie_session]

    assert deuxieme_jeton != premier_jeton
    assert compter_sessions(en_base) == 1


def test_une_connexion_purge_les_sessions_expirees(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    utilisateur = creer_utilisateur()

    async def inserer_expiree(db: AsyncSession) -> None:
        db.add(
            Session(utilisateur_id=utilisateur.id, jeton_hash="x" * 64, expire_le=datetime.now(UTC) - timedelta(days=1))
        )

    en_base(inserer_expiree)

    se_connecter(client, mot_de_passe=MOT_DE_PASSE)

    assert compter_sessions(en_base) == 1
