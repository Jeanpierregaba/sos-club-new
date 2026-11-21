"""Mode maintenance du site (spec 047) : bascule super-admin, blocage et exemptions."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.comptes.models import Utilisateur
from app.maintenance import service
from app.maintenance.models import EtatSite
from tests.conftest import Navigateur, connecter_admin
from tests.test_connexion import se_connecter

ETAT_SITE = "/api/etat-site"
MAINTENANCE = "/api/admin/maintenance"
PUBLIC = "/api/referentiel/axes"
MOI = "/api/admin/moi"
TABLEAU = "/api/admin/tableau-de-bord"
CONNEXION = "/api/comptes/connexion"
CODE = "/api/comptes/connexion/code"
DECONNEXION = "/api/comptes/deconnexion"
MOI_COMPTE = "/api/comptes/moi"

ANALYSTE = {("tableau_de_bord", "consulter")}


@pytest.fixture(autouse=True)
def cache_maintenance() -> Iterator[None]:
    """Le cache est propre au processus : chaque test repart d'un état lu en base."""
    service.invalider_cache()
    yield
    service.invalider_cache()


def activer_en_base(en_base: Callable[..., Any]) -> None:
    """Active la maintenance sans passer par l'API, pour tester le blocage côté client."""

    async def _activer(db: AsyncSession) -> None:
        etat = await db.get(EtatSite, 1)
        if etat is None:
            etat = EtatSite(id=1)
            db.add(etat)
        etat.maintenance_active = True
        etat.active_le = datetime.now(UTC)

    en_base(_activer)
    service.invalider_cache()


def compter_journal(en_base: Callable[..., Any], action: str) -> int:
    requete = select(func.count()).select_from(JournalAudit).where(JournalAudit.action == action)
    return en_base(lambda db: db.scalar(requete))


def etat_en_base(en_base: Callable[..., Any]) -> EtatSite | None:
    return en_base(lambda db: db.get(EtatSite, 1))


# Lecture publique de l'état ------------------------------------------------------------------------------------


def test_etat_site_public_par_defaut(client: TestClient) -> None:
    reponse = client.get(ETAT_SITE)

    assert reponse.status_code == 200
    assert reponse.json() == {"maintenance": False}


# Bascule par le super-administrateur ---------------------------------------------------------------------------


def test_super_admin_active_puis_desactive(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    visiteur = Navigateur(client)

    activation = client.put(MAINTENANCE, json={"maintenance_active": True})

    assert activation.status_code == 200
    assert activation.json()["maintenance_active"] is True
    assert activation.json()["active_le"] is not None
    assert visiteur.get(ETAT_SITE).json() == {"maintenance": True}
    assert client.get(MAINTENANCE).json()["maintenance_active"] is True

    # Un visiteur sans session est bloqué, le super-admin connecté ne l'est pas.
    bloque = visiteur.get(PUBLIC)
    assert bloque.status_code == 503
    assert bloque.headers["x-raison"] == "maintenance"
    assert "maintenance" in bloque.json()["detail"].lower()
    assert client.get(PUBLIC).status_code == 200
    # Le suivi de déploiement reste disponible (hors /api).
    assert visiteur.get("/health").status_code == 200

    desactivation = client.put(MAINTENANCE, json={"maintenance_active": False})

    assert desactivation.status_code == 200
    assert desactivation.json()["maintenance_active"] is False
    assert desactivation.json()["active_le"] is None
    assert visiteur.get(PUBLIC).status_code == 200

    etat = etat_en_base(en_base)
    assert etat is not None
    assert etat.maintenance_active is False
    assert etat.active_par_id is None


def test_activation_et_desactivation_journalisees(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    admin = creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)

    client.put(MAINTENANCE, json={"maintenance_active": True})
    client.put(MAINTENANCE, json={"maintenance_active": False})

    async def _entrees(db: AsyncSession) -> list[JournalAudit]:
        resultat = await db.scalars(
            select(JournalAudit)
            .where(JournalAudit.action.in_(["maintenance_activee", "maintenance_desactivee"]))
            .order_by(JournalAudit.quand)
        )
        return list(resultat.all())

    entrees = en_base(_entrees)

    assert [entree.action for entree in entrees] == [
        "maintenance_activee",
        "maintenance_desactivee",
    ]
    assert all(entree.auteur_id == admin.id for entree in entrees)
    assert all(entree.cible_type == "etat_site" for entree in entrees)
    assert all(entree.cible_id == "1" for entree in entrees)


def test_bascule_idempotente_sans_double_journal(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)

    for _ in range(2):
        assert client.put(MAINTENANCE, json={"maintenance_active": True}).status_code == 200
    for _ in range(2):
        assert client.put(MAINTENANCE, json={"maintenance_active": False}).status_code == 200

    assert compter_journal(en_base, "maintenance_activee") == 1
    assert compter_journal(en_base, "maintenance_desactivee") == 1


# Contournement et refus -----------------------------------------------------------------------------------------


def test_super_admin_contourne_la_maintenance(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    activer_en_base(en_base)

    assert client.get(MOI).status_code == 200
    assert client.get(TABLEAU).status_code == 200
    assert client.get(PUBLIC).status_code == 200
    assert client.get(ETAT_SITE).json() == {"maintenance": True}


def test_collaborateur_non_super_admin_ne_peut_pas_basculer(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=ANALYSTE, double_auth=True)
    connecter_admin(client)

    # Maintenance inactive : la route répond 403, sans écrire l'état.
    assert client.put(MAINTENANCE, json={"maintenance_active": True}).status_code == 403
    assert client.get(ETAT_SITE).json() == {"maintenance": False}

    # Maintenance active : le garde bloque avant même la route.
    activer_en_base(en_base)

    assert client.put(MAINTENANCE, json={"maintenance_active": False}).status_code == 503
    assert client.get(MOI).status_code == 503
    assert client.get(TABLEAU).status_code == 503
    assert client.get(PUBLIC).status_code == 503


def test_super_admin_sans_2fa_ne_peut_pas_basculer(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True)
    connecter_admin(client)

    reponse = client.put(MAINTENANCE, json={"maintenance_active": True})

    assert reponse.status_code == 403
    assert "double authentification" in reponse.json()["detail"].lower()


# Exemptions : se connecter, se déconnecter et lire sa session ------------------------------------------------


def test_exemptions_pour_se_connecter_et_se_deconnecter(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur()
    activer_en_base(en_base)

    assert se_connecter(client).status_code == 200
    assert client.get(MOI_COMPTE).status_code == 200
    assert client.post(DECONNEXION).status_code == 204
    assert client.get(MOI_COMPTE).status_code == 401
    assert client.post(CODE, json={"jeton": "inconnu", "code": "123456"}).status_code == 401


def test_super_admin_peut_se_connecter_pendant_la_maintenance(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    activer_en_base(en_base)

    reponse = connecter_admin(client)

    assert reponse.status_code == 200
    assert client.get(MOI).status_code == 200


# Persistance et ressources publiques ---------------------------------------------------------------------------


def test_etat_persiste_apres_redemarrage(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    client.put(MAINTENANCE, json={"maintenance_active": True})

    # Vider le cache simule un redémarrage : l'état est relu en base.
    service.invalider_cache()

    assert client.get(ETAT_SITE).json() == {"maintenance": True}
    etat = etat_en_base(en_base)
    assert etat is not None
    assert etat.maintenance_active is True


def test_photos_publiques_bloquees(client: TestClient, en_base: Callable[..., Any]) -> None:
    activer_en_base(en_base)

    reponse = client.get("/api/articles/inconnu/photos/00000000-0000-0000-0000-000000000000/grande")

    assert reponse.status_code == 503
    assert reponse.headers["x-raison"] == "maintenance"
