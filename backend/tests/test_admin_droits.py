"""Droits de l'espace administrateur (spec 015) : écrits avant le code, comme le demande docs/TESTING.md."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.models import JournalAudit
from app.comptes.models import Role, Session, StatutCompte, Utilisateur
from tests.conftest import connecter_admin
from tests.test_connexion import se_connecter

MOI = "/api/admin/moi"
TABLEAU = "/api/admin/tableau-de-bord"
INSCRITS = "/api/admin/inscrits"
JOURNAL = "/api/admin/journal"
COLLABORATEURS = "/api/admin/collaborateurs"
EXPORTS = "/api/admin/exports"

ANALYSTE = {("tableau_de_bord", "consulter"), ("statistiques", "consulter"), ("statistiques", "exporter")}
CONTENUS = {("tableau_de_bord", "consulter"), ("contenus", "consulter"), ("contenus", "creer")}
LECTEUR_INSCRITS = {("tableau_de_bord", "consulter"), ("inscrits", "consulter")}


def compter_refus(en_base: Callable[..., Any]) -> int:
    requete = select(func.count()).select_from(JournalAudit).where(JournalAudit.action == "acces_refuse")
    return en_base(lambda db: db.scalar(requete))


# Qui entre dans l'espace admin ----------------------------------------------------------------------------------


@pytest.mark.parametrize("route", [MOI, TABLEAU, INSCRITS, JOURNAL, COLLABORATEURS, EXPORTS])
def test_visiteur_refuse(client: TestClient, route: str) -> None:
    assert client.get(route).status_code == 401


@pytest.mark.parametrize("role", [Role.eleve, Role.encadreur])
@pytest.mark.parametrize("route", [MOI, TABLEAU, INSCRITS, JOURNAL, COLLABORATEURS, EXPORTS])
def test_eleve_et_encadreur_refuses(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], role: Role, route: str
) -> None:
    creer_utilisateur(role=role, email="prof@ecole.tg" if role is Role.encadreur else None)
    se_connecter(client)

    assert client.get(route).status_code == 403


def test_admin_sans_profil_de_collaborateur_refuse(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("orphelin", Role.admin, email="orphelin@aimes.tg")
    se_connecter(client, "orphelin")

    assert client.get(MOI).status_code == 403


def test_super_admin_voit_son_profil(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)

    corps = client.get(MOI).json()

    assert corps["super_admin"] is True
    assert corps["perimetre_dre"] is None
    assert corps["double_auth_active"] is True
    assert corps["double_auth_requise"] is False


def test_moi_liste_les_droits(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)

    droits = {(d["module"], d["action"]) for d in client.get(MOI).json()["droits"]}

    assert droits == ANALYSTE


# Droits par module ----------------------------------------------------------------------------------------------


def test_analyste_voit_le_tableau_de_bord_mais_pas_les_inscrits(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)

    assert client.get(TABLEAU).status_code == 200
    assert client.get(INSCRITS).status_code == 403
    assert client.get(JOURNAL).status_code == 403
    assert client.get(COLLABORATEURS).status_code == 403


def test_gestionnaire_de_contenus_ne_gere_pas_les_collaborateurs(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=CONTENUS)
    connecter_admin(client)

    invitation = {"email": "x@aimes.tg", "prenom": "X", "nom": "Y", "droits": [], "perimetre_dre": None}
    assert client.post(COLLABORATEURS, json=invitation).status_code == 403
    assert client.get(COLLABORATEURS).status_code == 403
    assert compter_refus(en_base) == 2


def test_un_refus_est_journalise_avec_son_auteur(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    analyste = creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)

    client.get(INSCRITS)

    entree = en_base(lambda db: db.scalar(select(JournalAudit).where(JournalAudit.action == "acces_refuse")))
    assert entree.auteur_id == analyste.id
    assert entree.details["droit"] == "inscrits:consulter"


def test_meme_avec_tous_les_droits_seul_le_super_admin_gere_les_collaborateurs(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    from app.admin.catalogue import tous_les_droits

    creer_collaborateur(droits={(m, a.value) for m, a in tous_les_droits()}, double_auth=True)
    connecter_admin(client)

    assert client.get(COLLABORATEURS).status_code == 403


# Périmètre ------------------------------------------------------------------------------------------------------


def test_un_collaborateur_limite_a_une_dre_n_accede_pas_a_l_annuaire_national(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=LECTEUR_INSCRITS, perimetre_dre="kara")
    connecter_admin(client)

    assert client.get(INSCRITS).status_code == 403


def test_le_meme_droit_au_niveau_national_ouvre_l_annuaire(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=LECTEUR_INSCRITS)
    connecter_admin(client)

    assert client.get(INSCRITS).status_code == 200


# Fin d'accès et suspension --------------------------------------------------------------------------------------


def test_fin_d_acces_passee_refuse_la_connexion(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(droits=ANALYSTE, fin_acces=datetime.now(UTC) - timedelta(minutes=1))

    assert connecter_admin(client).status_code == 403


def test_fin_d_acces_atteinte_pendant_la_session_coupe_les_sessions(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.admin.models import Collaborateur

    analyste = creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)
    assert client.get(TABLEAU).status_code == 200

    async def expirer(db: Any) -> None:
        collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == analyste.id))
        collaborateur.fin_acces = datetime.now(UTC) - timedelta(seconds=1)

    en_base(expirer)

    assert client.get(TABLEAU).status_code == 401
    sessions = select(func.count()).select_from(Session).where(Session.utilisateur_id == analyste.id)
    assert en_base(lambda db: db.scalar(sessions)) == 0


def test_suspension_en_cours_de_session(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    analyste = creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)

    async def suspendre(db: Any) -> None:
        (await db.get(Utilisateur, analyste.id)).statut = StatutCompte.suspendu

    en_base(suspendre)

    assert client.get(TABLEAU).status_code == 401


# Double authentification requise --------------------------------------------------------------------------------


def test_droit_sensible_sans_double_auth_bloque_tout_sauf_moi(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=LECTEUR_INSCRITS | {("inscrits", "exporter")})
    connecter_admin(client)

    moi = client.get(MOI)
    assert moi.status_code == 200
    assert moi.json()["double_auth_requise"] is True

    refus = client.get(TABLEAU)
    assert refus.status_code == 403
    assert "double authentification" in refus.json()["detail"]


def test_super_admin_sans_double_auth_doit_l_activer(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur(super_admin=True)
    connecter_admin(client)

    assert client.get(MOI).json()["double_auth_requise"] is True
    assert client.get(COLLABORATEURS).status_code == 403


def test_droits_non_sensibles_sans_double_auth(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)

    assert client.get(MOI).json()["double_auth_requise"] is False
    assert client.get(TABLEAU).status_code == 200
