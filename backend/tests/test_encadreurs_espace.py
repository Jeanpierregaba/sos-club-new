"""Espace de l'encadreur (spec 018) : ses trois états, son profil, sa demande renvoyée, et l'accès réservé aux
encadreurs vérifiés."""

from collections.abc import Callable, Iterator
from typing import Annotated, Any
from uuid import UUID

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.config import settings
from app.encadreurs.dependances import encadreur_actif
from app.encadreurs.models import Encadreur, EtatVerification
from app.main import app
from app.referentiel.models import Etablissement
from tests.conftest import MOT_DE_PASSE, connecter_admin

ESPACE = "/api/encadreurs/moi"
FILE = "/api/admin/encadreurs"
VERIFICATION = {("encadreurs", "consulter"), ("encadreurs", "approuver")}

pytestmark = pytest.mark.usefixtures("annuaire")


def etablissement_id(en_base: Callable[..., Any], nom: str = "Lycée de Tokoin I") -> str:
    return str(en_base(lambda db: db.scalar(select(Etablissement.id).where(Etablissement.nom == nom))))


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


@pytest.fixture
def encadreur(client: TestClient, en_base: Callable[..., Any]) -> dict[str, Any]:
    """Un encadreur inscrit et connecté, en attente."""
    corps = {
        "prenom": "Kossi", "nom": "Agbeko", "email": "kossi@ecole.tg", "telephone": "90123456",
        "identifiant": "kossi.agbeko", "mot_de_passe": MOT_DE_PASSE, "fonction": "enseignant", "charte": True,
        "consentement": True, "etablissement_id": etablissement_id(en_base),
    }  # fmt: skip
    reponse = client.post("/api/encadreurs/inscription", json=corps)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def decider(
    client: TestClient, creer_collaborateur: Callable[..., Any], encadreur: dict[str, Any], decision: str
) -> None:
    """Le collaborateur décide, puis l'encadreur se reconnecte."""
    creer_collaborateur("verif", droits=VERIFICATION, double_auth=True)
    client.cookies.clear()
    connecter_admin(client, "verif")
    corps = {"motif": "Établissement à confirmer"} if decision == "refuser" else None
    assert client.post(f"{FILE}/{encadreur['id']}/{decision}", json=corps).status_code == 200
    client.cookies.clear()
    client.post("/api/comptes/connexion", json={"identifiant": "kossi.agbeko", "mot_de_passe": MOT_DE_PASSE})


# États -----------------------------------------------------------------------------------------------------------


def test_en_attente_lespace_montre_la_demande_sans_points(client: TestClient, encadreur: dict[str, Any]) -> None:
    espace = client.get(ESPACE).json()

    assert espace["etat"] == "en_attente"
    assert espace["demande_le"] is not None
    assert espace["points"] is None
    assert (espace["telephone"], espace["etablissement"]["nom"]) == ("90123456", "Lycée de Tokoin I")


def test_actif_lespace_montre_les_points(
    client: TestClient, creer_collaborateur: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    decider(client, creer_collaborateur, encadreur, "activer")

    espace = client.get(ESPACE).json()

    assert espace["etat"] == "actif"
    assert espace["points"]["total"] == 100
    assert [ligne["libelle"] for ligne in espace["points"]["lignes"]] == ["Compte validé"]


def test_refuse_lespace_montre_le_motif(
    client: TestClient, creer_collaborateur: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    decider(client, creer_collaborateur, encadreur, "refuser")

    espace = client.get(ESPACE).json()

    assert (espace["etat"], espace["motif_refus"]) == ("refuse", "Établissement à confirmer")


def test_un_eleve_na_pas_despace_encadreur(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur("eleve1")
    client.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": MOT_DE_PASSE})

    assert client.get(ESPACE).status_code == 403


def test_un_encadreur_sans_profil_est_invite_a_contacter_lequipe(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("ancien", Role.encadreur, email="ancien@ecole.tg")
    client.post("/api/comptes/connexion", json={"identifiant": "ancien", "mot_de_passe": MOT_DE_PASSE})

    reponse = client.get(ESPACE)

    assert reponse.status_code == 404
    assert "contacte l'équipe" in reponse.json()["detail"]


def test_sans_connexion_lespace_est_refuse(client: TestClient) -> None:
    assert client.get(ESPACE).status_code == 401


# Profil ----------------------------------------------------------------------------------------------------------


def test_modifier_son_profil(client: TestClient, en_base: Callable[..., Any], encadreur: dict[str, Any]) -> None:
    version = client.get(ESPACE).json()["version"]
    autre = etablissement_id(en_base, "Lycée de Tokoin II")

    reponse = client.patch(
        ESPACE,
        json={"version": version, "telephone": "91 00 00 00", "etablissement_id": autre, "fonction": "autre",
              "fonction_precision": "Bibliothécaire", "discipline": "Physique-chimie"},
    )  # fmt: skip

    assert reponse.status_code == 200, reponse.text
    espace = reponse.json()
    assert (espace["telephone"], espace["discipline"]) == ("91000000", "Physique-chimie")
    assert espace["etablissement"]["nom"] == "Lycée de Tokoin II"
    assert (espace["fonction"], espace["fonction_precision"]) == ("autre", "Bibliothécaire")
    assert espace["version"] == version + 1
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "profil_encadreur_modifie"))
    ).all()
    assert entree.details["apres"]["telephone"] == "nouveau"
    assert "90123456" not in str(entree.details) and "91000000" not in str(entree.details)


def test_le_telephone_ne_sefface_plus(client: TestClient, encadreur: dict[str, Any]) -> None:
    version = client.get(ESPACE).json()["version"]

    reponse = client.patch(ESPACE, json={"version": version, "telephone": ""})

    assert reponse.status_code == 422
    assert client.get(ESPACE).json()["telephone"] == "90123456"


def test_ajouter_un_telephone_est_journalise_sans_ancien_numero(
    client: TestClient, en_base: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    # Un encadreur inscrit avant la spec 030 peut n'avoir aucun téléphone.
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.identifiant == "kossi.agbeko").values(telephone=None)
        )
    )
    version = client.get(ESPACE).json()["version"]

    client.patch(ESPACE, json={"version": version, "telephone": "91 00 00 00"})

    dernier = en_base(
        lambda db: db.scalars(
            select(JournalAudit)
            .where(JournalAudit.action == "profil_encadreur_modifie")
            .order_by(JournalAudit.quand.desc())
        )
    ).first()
    assert dernier.details == {"avant": {"telephone": None}, "apres": {"telephone": "nouveau"}}


def test_une_version_perimee_est_refusee(client: TestClient, encadreur: dict[str, Any]) -> None:
    version = client.get(ESPACE).json()["version"]
    client.patch(ESPACE, json={"version": version, "telephone": "91000000"})

    reponse = client.patch(ESPACE, json={"version": version, "telephone": "92000000"})

    assert reponse.status_code == 409


def test_passer_a_autre_exige_une_precision(client: TestClient, encadreur: dict[str, Any]) -> None:
    version = client.get(ESPACE).json()["version"]

    assert client.patch(ESPACE, json={"version": version, "fonction": "autre"}).status_code == 422


def test_quitter_autre_efface_la_precision(client: TestClient, encadreur: dict[str, Any]) -> None:
    version = client.get(ESPACE).json()["version"]
    client.patch(ESPACE, json={"version": version, "fonction": "autre", "fonction_precision": "Bibliothécaire"})

    espace = client.patch(ESPACE, json={"version": version + 1, "fonction": "sante"}).json()

    assert (espace["fonction"], espace["fonction_precision"]) == ("sante", None)


def test_le_profil_ne_change_ni_letat_ni_le_role(client: TestClient, encadreur: dict[str, Any]) -> None:
    version = client.get(ESPACE).json()["version"]

    assert client.patch(ESPACE, json={"version": version, "etat": "actif"}).status_code == 422
    assert client.get(ESPACE).json()["etat"] == "en_attente"


# Demande renvoyée ------------------------------------------------------------------------------------------------


def test_un_refuse_renvoie_sa_demande(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    decider(client, creer_collaborateur, encadreur, "refuser")

    reponse = client.post(f"{ESPACE}/renvoyer")

    assert reponse.status_code == 200, reponse.text
    assert (reponse.json()["etat"], reponse.json()["motif_refus"]) == ("en_attente", None)
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "encadreur_redemande"))
    ).all()
    assert entree.details == {"motif_precedent": "Établissement à confirmer"}


def test_seule_une_demande_refusee_se_renvoie(client: TestClient, encadreur: dict[str, Any]) -> None:
    assert client.post(f"{ESPACE}/renvoyer").status_code == 409


# Accès réservé aux encadreurs actifs -----------------------------------------------------------------------------


@pytest.fixture
def route_reservee() -> Iterator[None]:
    """Une route de test protégée par `encadreur_actif`, retirée après le test : le schéma OpenAPI n'en garde
    aucune trace."""

    async def reservee(utilisateur: Annotated[Utilisateur, Depends(encadreur_actif)]) -> dict[str, str]:
        return {"identifiant": utilisateur.identifiant}

    avant = list(app.router.routes)
    app.add_api_route("/api/test/encadreur-actif", reservee, methods=["GET"], include_in_schema=False)
    yield
    app.router.routes[:] = avant


@pytest.mark.usefixtures("route_reservee")
def test_un_encadreur_en_attente_na_pas_les_acces_dun_actif(client: TestClient, encadreur: dict[str, Any]) -> None:
    reponse = client.get("/api/test/encadreur-actif")

    assert reponse.status_code == 403
    assert "vérifié" in reponse.json()["detail"]


@pytest.mark.usefixtures("route_reservee")
def test_un_encadreur_refuse_na_pas_les_acces_dun_actif(
    client: TestClient, creer_collaborateur: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    decider(client, creer_collaborateur, encadreur, "refuser")

    assert client.get("/api/test/encadreur-actif").status_code == 403


@pytest.mark.usefixtures("route_reservee")
def test_un_encadreur_actif_passe(
    client: TestClient, creer_collaborateur: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    decider(client, creer_collaborateur, encadreur, "activer")

    assert client.get("/api/test/encadreur-actif").json() == {"identifiant": "kossi.agbeko"}


@pytest.mark.usefixtures("route_reservee")
def test_un_eleve_na_pas_les_acces_dun_encadreur(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur("eleve1")
    client.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": MOT_DE_PASSE})

    assert client.get("/api/test/encadreur-actif").status_code == 403


def test_un_encadreur_suspendu_ne_se_connecte_plus(
    client: TestClient, en_base: Callable[..., Any], encadreur: dict[str, Any]
) -> None:
    en_base(lambda db: db.execute(update(Utilisateur).values(statut=StatutCompte.suspendu)))
    client.cookies.clear()

    reponse = client.post("/api/comptes/connexion", json={"identifiant": "kossi.agbeko", "mot_de_passe": MOT_DE_PASSE})

    assert reponse.status_code == 403
    assert en_base(lambda db: db.get(Encadreur, UUID(encadreur["id"]))).etat is EtatVerification.en_attente
