"""Comptes collaborateurs : invitation, activation, droits, suspension, révocation (spec 015)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import Collaborateur, Invitation, JournalAudit
from app.comptes.models import Role, Utilisateur
from app.courriel import envoi as courriel
from tests.conftest import Navigateur, connecter_admin

COLLABORATEURS = "/api/admin/collaborateurs"
GESTION_CONTENUS = [
    {"module": "tableau_de_bord", "action": "consulter"},
    {"module": "contenus", "action": "consulter"},
    {"module": "contenus", "action": "creer"},
    {"module": "contenus", "action": "soumettre"},
]


@pytest.fixture
def courriels(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    """Boîte factice : capture les e-mails au lieu de les envoyer."""
    boite: list[tuple[str, str, str]] = []

    async def envoyer(destinataire: str, sujet: str, texte: str, html: str | None = None) -> None:
        boite.append((destinataire, sujet, texte))

    monkeypatch.setattr(courriel, "envoyer", envoyer)
    return boite


@pytest.fixture
def chef(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Utilisateur:
    utilisateur = creer_collaborateur("chef", super_admin=True, double_auth=True)
    assert connecter_admin(client).status_code == 200
    return utilisateur


def inviter(client: TestClient, email: str = "Ama@Aimes.tg", **champs: Any) -> Any:
    corps = {"email": email, "prenom": "Ama", "nom": "Kodom", "droits": GESTION_CONTENUS} | champs
    return client.post(COLLABORATEURS, json=corps)


def jeton_du(texte: str) -> str:
    lien = next(mot for mot in texte.split() if "/activation?jeton=" in mot)
    return parse_qs(urlparse(lien).query)["jeton"][0]


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


# Invitation et activation ---------------------------------------------------------------------------------------


def test_invitation_envoie_un_lien_unique(
    client: TestClient, chef: Utilisateur, courriels: list[Any], en_base: Callable[..., Any]
) -> None:
    reponse = inviter(client)

    assert reponse.status_code == 201
    collaborateur = reponse.json()["collaborateur"]
    assert collaborateur["statut"] == "invitation_envoyee"
    assert collaborateur["email"] == "ama@aimes.tg"
    assert len(courriels) == 1
    destinataire, _, texte = courriels[0]
    assert destinataire == "ama@aimes.tg"
    assert "mot de passe" in texte and len(jeton_du(texte)) >= 40
    assert journal(en_base, "collaborateur_invite")[0].auteur_id == chef.id


def test_activation_cree_le_compte_et_ouvre_la_session(
    client: TestClient, chef: Utilisateur, courriels: list[Any], en_base: Callable[..., Any]
) -> None:
    inviter(client)
    jeton = jeton_du(courriels[0][2])
    invite = Navigateur(client)

    info = invite.post("/api/activation/info", json={"jeton": jeton})
    assert info.status_code == 200
    assert info.json() == {"prenom": "Ama", "email": "ama@aimes.tg", "double_auth_requise": False}

    reponse = invite.post(
        "/api/activation", json={"jeton": jeton, "identifiant": "ama.k", "mot_de_passe": "un-bon-mot-de-passe"}
    )

    assert reponse.status_code == 200
    moi = invite.get("/api/admin/moi").json()
    assert moi["identifiant"] == "ama.k"
    assert {(d["module"], d["action"]) for d in moi["droits"]} >= {("contenus", "creer")}
    assert invite.get("/api/admin/tableau-de-bord").status_code == 200
    # Le gestionnaire de contenus ne gère ni les rôles ni les collaborateurs.
    assert invite.get(COLLABORATEURS).status_code == 403
    assert (
        invite.put(
            f"{COLLABORATEURS}/{reponse.json()['id']}/permissions", json={"droits": [], "motif": "essai"}
        ).status_code
        == 403
    )
    assert len(journal(en_base, "invitation_acceptee")) == 1


def test_le_lien_ne_sert_qu_une_fois(client: TestClient, chef: Utilisateur, courriels: list[Any]) -> None:
    inviter(client)
    jeton = jeton_du(courriels[0][2])
    entree = {"identifiant": "ama.k", "mot_de_passe": "un-bon-mot-de-passe"}
    assert Navigateur(client).post("/api/activation", json={"jeton": jeton} | entree).status_code == 200

    autre = {"identifiant": "pirate", "mot_de_passe": "un-autre-mot-de-passe"}
    assert Navigateur(client).post("/api/activation", json={"jeton": jeton} | autre).status_code == 404


def test_lien_expire(client: TestClient, chef: Utilisateur, courriels: list[Any], en_base: Callable[..., Any]) -> None:
    inviter(client)
    jeton = jeton_du(courriels[0][2])
    en_base(lambda db: db.execute(update(Invitation).values(expire_le=datetime.now(UTC) - timedelta(seconds=1))))

    assert Navigateur(client).post("/api/activation/info", json={"jeton": jeton}).status_code == 404
    collaborateurs = client.get(COLLABORATEURS).json()
    assert [c["statut"] for c in collaborateurs if c["email"] == "ama@aimes.tg"] == ["invitation_expiree"]


def test_renvoyer_annule_l_ancien_lien(client: TestClient, chef: Utilisateur, courriels: list[Any]) -> None:
    identifiant = inviter(client).json()["collaborateur"]["id"]
    ancien = jeton_du(courriels[0][2])

    assert client.post(f"{COLLABORATEURS}/{identifiant}/invitation").status_code == 200

    nouveau = jeton_du(courriels[1][2])
    assert Navigateur(client).post("/api/activation/info", json={"jeton": ancien}).status_code == 404
    assert Navigateur(client).post("/api/activation/info", json={"jeton": nouveau}).status_code == 200


def test_activation_avec_droit_sensible_impose_la_double_auth(
    client: TestClient, chef: Utilisateur, courriels: list[Any]
) -> None:
    inviter(
        client, droits=[{"module": "inscrits", "action": "exporter"}, {"module": "inscrits", "action": "consulter"}]
    )
    jeton = jeton_du(courriels[0][2])
    invite = Navigateur(client)
    assert invite.post("/api/activation/info", json={"jeton": jeton}).json()["double_auth_requise"] is True

    invite.post("/api/activation", json={"jeton": jeton, "identifiant": "ama.k", "mot_de_passe": "un-bon-mot-de-passe"})

    assert invite.get("/api/admin/moi").json()["double_auth_requise"] is True
    assert invite.get("/api/admin/inscrits").status_code == 403
    assert invite.post("/api/admin/double-auth/enrolement").status_code == 200


def test_email_deja_utilise(
    client: TestClient, chef: Utilisateur, courriels: list[Any], creer_utilisateur: Callable[..., Any]
) -> None:
    creer_utilisateur("prof", Role.encadreur, email="prof@ecole.tg")

    assert inviter(client, email="PROF@ecole.tg").status_code == 409
    assert inviter(client).status_code == 201
    assert inviter(client).status_code == 409


def test_droit_inconnu_refuse(client: TestClient, chef: Utilisateur, courriels: list[Any]) -> None:
    reponse = inviter(client, droits=[{"module": "collaborateurs", "action": "consulter"}])

    assert reponse.status_code == 422


def test_dre_inconnue_refusee(client: TestClient, chef: Utilisateur, courriels: list[Any]) -> None:
    assert inviter(client, perimetre_dre="atlantide").status_code == 422


def test_envoi_impossible_marque_l_invitation(
    client: TestClient, chef: Utilisateur, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def panne(*_: Any, **__: Any) -> None:
        raise courriel.EnvoiImpossible

    monkeypatch.setattr(courriel, "envoyer", panne)

    reponse = inviter(client)

    assert reponse.status_code == 201
    assert reponse.json()["collaborateur"]["invitation_envoi"] == "echec"


def test_sans_smtp_hors_production_le_lien_est_rendu(client: TestClient, chef: Utilisateur) -> None:
    reponse = inviter(client)

    assert "/activation?jeton=" in reponse.json()["lien_de_test"]


# Droits, suspension, révocation ---------------------------------------------------------------------------------


@pytest.fixture
def ama(client: TestClient, chef: Utilisateur, courriels: list[Any]) -> tuple[str, Navigateur]:
    """Un gestionnaire de contenus actif, connecté dans son propre navigateur."""
    collaborateur_id = inviter(client).json()["collaborateur"]["id"]
    navigateur = Navigateur(client)
    navigateur.post(
        "/api/activation",
        json={"jeton": jeton_du(courriels[0][2]), "identifiant": "ama.k", "mot_de_passe": "un-bon-mot-de-passe"},
    )
    return collaborateur_id, navigateur


def test_modifier_les_droits_est_journalise(
    client: TestClient, ama: tuple[str, Navigateur], en_base: Callable[..., Any]
) -> None:
    collaborateur_id, _ = ama
    droits = [{"module": "statistiques", "action": "consulter"}, {"module": "tableau_de_bord", "action": "consulter"}]

    reponse = client.put(
        f"{COLLABORATEURS}/{collaborateur_id}/permissions",
        json={"droits": droits, "perimetre_dre": "kara", "motif": "Passage à l'analyse"},
    )

    assert reponse.status_code == 200
    assert reponse.json()["perimetre_dre"] == "kara"
    assert reponse.json()["revu_le"] is not None
    entree = journal(en_base, "droits_modifies")[0]
    assert "statistiques:consulter" in entree.details["ajoutes"]
    assert "contenus:creer" in entree.details["retires"]
    assert entree.details["motif"] == "Passage à l'analyse"


def test_suspension_coupe_la_session_immediatement(client: TestClient, ama: tuple[str, Navigateur]) -> None:
    collaborateur_id, navigateur = ama
    assert navigateur.get("/api/admin/tableau-de-bord").status_code == 200

    reponse = client.post(f"{COLLABORATEURS}/{collaborateur_id}/suspendre", json={"motif": "Départ en congé"})

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "suspendu"
    assert navigateur.get("/api/admin/tableau-de-bord").status_code == 401


def test_reactiver_puis_revoquer(client: TestClient, ama: tuple[str, Navigateur]) -> None:
    collaborateur_id, _ = ama
    client.post(f"{COLLABORATEURS}/{collaborateur_id}/suspendre", json={"motif": "Congé"})

    assert (
        client.post(f"{COLLABORATEURS}/{collaborateur_id}/reactiver", json={"motif": "Retour"}).json()["statut"]
        == "actif"
    )
    assert (
        client.post(f"{COLLABORATEURS}/{collaborateur_id}/revoquer", json={"motif": "Fin de mission"}).json()["statut"]
        == "revoque"
    )
    assert client.post(f"{COLLABORATEURS}/{collaborateur_id}/reactiver", json={"motif": "Erreur"}).status_code == 409


def test_motif_obligatoire(client: TestClient, ama: tuple[str, Navigateur]) -> None:
    collaborateur_id, _ = ama

    assert client.post(f"{COLLABORATEURS}/{collaborateur_id}/suspendre", json={"motif": ""}).status_code == 422


def test_le_super_admin_ne_se_suspend_pas_lui_meme(
    client: TestClient, chef: Utilisateur, en_base: Callable[..., Any]
) -> None:
    mon_id = en_base(lambda db: db.scalar(select(Collaborateur.id).where(Collaborateur.utilisateur_id == chef.id)))

    assert client.post(f"{COLLABORATEURS}/{mon_id}/suspendre", json={"motif": "Essai"}).status_code == 403
    assert (
        client.put(f"{COLLABORATEURS}/{mon_id}/permissions", json={"droits": [], "motif": "Essai"}).status_code == 403
    )


def test_un_super_admin_suspendu_perd_la_main_immediatement(
    client: TestClient, chef: Utilisateur, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    second = creer_collaborateur("second", super_admin=True, double_auth=True)
    second_id = en_base(lambda db: db.scalar(select(Collaborateur.id).where(Collaborateur.utilisateur_id == second.id)))
    chef_id = en_base(lambda db: db.scalar(select(Collaborateur.id).where(Collaborateur.utilisateur_id == chef.id)))

    assert client.post(f"{COLLABORATEURS}/{second_id}/suspendre", json={"motif": "Essai"}).status_code == 200

    # Le second, réactivé puis connecté, est suspendu de nouveau : sa session ne lui sert plus à rien.
    client.post(f"{COLLABORATEURS}/{second_id}/reactiver", json={"motif": "Retour"})
    navigateur = Navigateur(client)
    connecter_admin(navigateur, "second")
    client.post(f"{COLLABORATEURS}/{second_id}/suspendre", json={"motif": "Essai"})
    assert navigateur.post(f"{COLLABORATEURS}/{chef_id}/suspendre", json={"motif": "Essai"}).status_code == 401


def test_dernier_super_admin_protege(
    client: TestClient, chef: Utilisateur, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.admin import collaborateurs as service
    from app.admin.dependances import Acces

    second = creer_collaborateur("second", super_admin=True, double_auth=True)

    async def retirer_le_chef(db: Any) -> str:
        auteur_collab = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == second.id))
        chef_collab = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
        auteur = Acces(utilisateur=await db.get(Utilisateur, second.id), collaborateur=auteur_collab)
        # Le second se suspend d'abord (simulé), puis tente de retirer le chef : refusé, il n'en resterait aucun.
        (await db.get(Utilisateur, second.id)).statut = "suspendu"
        await db.flush()
        try:
            await service.changer_statut(db, auteur, chef_collab.id, "suspendu", "Essai", "127.0.0.1")
        except service.Refus as erreur:
            return str(erreur)
        return "accepté"

    assert "au moins un super-administrateur" in en_base(retirer_le_chef)


def test_reinitialiser_la_double_auth(
    client: TestClient, chef: Utilisateur, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    perdu = creer_collaborateur("perdu", droits={("inscrits", "consulter"), ("inscrits", "exporter")}, double_auth=True)
    perdu_id = en_base(lambda db: db.scalar(select(Collaborateur.id).where(Collaborateur.utilisateur_id == perdu.id)))

    reponse = client.post(f"{COLLABORATEURS}/{perdu_id}/double-auth/reinitialiser", json={"motif": "Téléphone perdu"})

    assert reponse.status_code == 200
    assert reponse.json()["double_auth_active"] is False
    navigateur = Navigateur(client)
    assert connecter_admin(navigateur, "perdu").status_code == 200
    assert navigateur.get("/api/admin/moi").json()["double_auth_requise"] is True


def test_marquer_revu(client: TestClient, ama: tuple[str, Navigateur], en_base: Callable[..., Any]) -> None:
    collaborateur_id, _ = ama

    reponse = client.post(f"{COLLABORATEURS}/{collaborateur_id}/revue")

    assert reponse.json()["revu_le"] is not None
    assert len(journal(en_base, "droits_revus")) == 1


def test_filtres_de_la_liste(client: TestClient, ama: tuple[str, Navigateur]) -> None:
    assert [c["email"] for c in client.get(COLLABORATEURS, params={"recherche": "kodom"}).json()] == ["ama@aimes.tg"]
    assert client.get(COLLABORATEURS, params={"statut": "suspendu"}).json() == []
    assert len(client.get(COLLABORATEURS, params={"perimetre": "national"}).json()) == 2
