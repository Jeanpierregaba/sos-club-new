"""Actions de l'espace admin sur les élèves (spec 017) : fiche, pseudonyme imposé, mot de passe réinitialisé,
établissements proposés."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from app.config import settings
from app.referentiel.models import Etablissement, Iesg
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin

INSCRITS = "/api/admin/inscrits"
ETABLISSEMENTS = "/api/admin/referentiel/etablissements"
GESTION_INSCRITS = {("tableau_de_bord", "consulter"), ("inscrits", "consulter"), ("inscrits", "modifier")}
CLUBS = {("tableau_de_bord", "consulter"), ("clubs", "consulter"), ("clubs", "modifier")}

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


def id_de(en_base: Callable[..., Any], modele: Any, nom: str) -> str:
    return str(en_base(lambda db: db.scalar(select(modele.id).where(modele.nom == nom))))


def inscrire(navigateur: Any, en_base: Callable[..., Any], numero: int, **champs: Any) -> dict[str, Any]:
    corps = {
        "prenom": "Aya", "nom": "Mensah", "pseudonyme": f"Pseudo {numero}", "identifiant": f"eleve{numero}",
        "mot_de_passe": MOT_DE_PASSE, "classe": "3e", "charte": True, "consentement_parent": True,
        "etablissement_id": id_de(en_base, Etablissement, "Lycée de Tokoin I"),
    } | champs  # fmt: skip
    reponse = navigateur.post("/api/eleves/inscription", json=corps)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=GESTION_INSCRITS, double_auth=True)
    connecter_admin(client, "gestion")
    return client


# Fiche d'un élève ---------------------------------------------------------------------------------------------


def test_la_fiche_dun_eleve_montre_son_profil_et_ses_points(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    eleve = inscrire(Navigateur(gestionnaire), en_base, 1)

    fiche = gestionnaire.get(f"{INSCRITS}/{eleve['id']}").json()

    assert fiche["eleve"]["pseudonyme"] == "Pseudo 1"
    assert fiche["eleve"]["etablissement"]["dre"] == "Grand Lomé"
    assert fiche["eleve"]["points"]["total"] == 100
    assert [e["action"] for e in fiche["historique"]] == ["inscription_eleve"]


def test_la_recherche_trouve_un_pseudonyme(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(Navigateur(gestionnaire), en_base, 1, pseudonyme="Étoile Filante")

    page = gestionnaire.get(INSCRITS, params={"recherche": "filante"}).json()

    assert [i["identifiant"] for i in page["inscrits"]] == ["eleve1"]


# Pseudonyme ---------------------------------------------------------------------------------------------------


def test_imposer_un_pseudonyme(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    eleve = inscrire(Navigateur(gestionnaire), en_base, 1)

    reponse = gestionnaire.post(
        f"{INSCRITS}/{eleve['id']}/pseudonyme", json={"pseudonyme": "Nouveau Nom", "motif": "Signalé par un élève"}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["eleve"]["pseudonyme"] == "Nouveau Nom"
    (entree,) = journal(en_base, "pseudonyme_impose")
    assert entree.details == {"avant": "Pseudo 1", "apres": "Nouveau Nom", "motif": "Signalé par un élève"}


@pytest.mark.parametrize(
    ("pseudonyme", "statut"), [("PSEUDO-2", 409), ("Admin", 422), ("Eleve1", 422), ("Pseudo 1", 409)]
)
def test_un_pseudonyme_impose_suit_les_memes_regles(
    gestionnaire: TestClient, en_base: Callable[..., Any], pseudonyme: str, statut: int
) -> None:
    eleve = inscrire(Navigateur(gestionnaire), en_base, 1)
    inscrire(Navigateur(gestionnaire), en_base, 2)

    reponse = gestionnaire.post(
        f"{INSCRITS}/{eleve['id']}/pseudonyme", json={"pseudonyme": pseudonyme, "motif": "Test"}
    )

    assert reponse.status_code == statut


def test_imposer_un_pseudonyme_exige_le_droit_et_un_motif(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = inscrire(Navigateur(client), en_base, 1)
    creer_collaborateur("lecteur", droits={("inscrits", "consulter")})
    connecter_admin(client, "lecteur")

    reponse = client.post(f"{INSCRITS}/{eleve['id']}/pseudonyme", json={"pseudonyme": "Autre Nom", "motif": "Test"})

    assert reponse.status_code == 403


def test_un_motif_est_obligatoire(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    eleve = inscrire(Navigateur(gestionnaire), en_base, 1)

    reponse = gestionnaire.post(f"{INSCRITS}/{eleve['id']}/pseudonyme", json={"pseudonyme": "Autre Nom", "motif": ""})

    assert reponse.status_code == 422


# Mot de passe -------------------------------------------------------------------------------------------------


def test_reinitialiser_le_mot_de_passe(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    navigateur = Navigateur(gestionnaire)
    eleve = inscrire(navigateur, en_base, 1)

    reponse = gestionnaire.post(f"{INSCRITS}/{eleve['id']}/mot-de-passe", json={"motif": "Mot de passe oublié"})

    assert reponse.status_code == 200, reponse.text
    provisoire = reponse.json()["mot_de_passe"]
    assert len(provisoire) == 12
    # Les sessions de l'élève sont coupées ; le nouveau mot de passe fonctionne, l'ancien non.
    assert navigateur.get("/api/eleves/moi").status_code == 401
    ancien = navigateur.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": MOT_DE_PASSE})
    nouveau = navigateur.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": provisoire})
    assert (ancien.status_code, nouveau.status_code) == (401, 200)
    (entree,) = journal(en_base, "mot_de_passe_reinitialise")
    assert provisoire not in str(entree.details)


def test_on_ne_reinitialise_que_le_mot_de_passe_dun_eleve(
    gestionnaire: TestClient, creer_utilisateur: Callable[..., Any]
) -> None:
    from app.comptes.models import Role

    prof = creer_utilisateur("prof", Role.encadreur, email="prof@ecole.tg")

    assert gestionnaire.post(f"{INSCRITS}/{prof.id}/mot-de-passe", json={"motif": "Oubli"}).status_code == 404


# Établissements proposés --------------------------------------------------------------------------------------


@pytest.fixture
def gestionnaire_clubs(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("clubs", droits=CLUBS)
    connecter_admin(client, "clubs")
    return client


def proposer(client: TestClient, en_base: Callable[..., Any], numero: int, nom: str, iesg: str = "IESG Golfe") -> None:
    inscrire(
        Navigateur(client), en_base, numero, etablissement_id=None,
        proposition={"iesg_id": id_de(en_base, Iesg, iesg), "nom": nom},
    )  # fmt: skip


def la_proposition(client: TestClient, nom: str) -> dict[str, Any]:
    page = client.get(ETABLISSEMENTS, params={"statut": "propose"}).json()
    return next(e for e in page["etablissements"] if e["nom"] == nom)


def test_la_liste_compte_les_eleves_dune_proposition(
    gestionnaire_clubs: TestClient, en_base: Callable[..., Any]
) -> None:
    proposer(gestionnaire_clubs, en_base, 1, "CEG des Étoiles")
    proposer(gestionnaire_clubs, en_base, 2, "CEG des Etoiles")

    assert la_proposition(gestionnaire_clubs, "CEG des Étoiles")["nb_eleves"] == 2


def test_accepter_une_proposition(gestionnaire_clubs: TestClient, en_base: Callable[..., Any]) -> None:
    proposer(gestionnaire_clubs, en_base, 1, "CEG des Étoiles")
    proposition = la_proposition(gestionnaire_clubs, "CEG des Étoiles")

    reponse = gestionnaire_clubs.patch(
        f"{ETABLISSEMENTS}/{proposition['id']}",
        json={"version": proposition["version"], "statut": "actif", "type": "college"},
    )

    assert reponse.status_code == 200, reponse.text
    trouves = gestionnaire_clubs.get("/api/referentiel/etablissements", params={"recherche": "etoiles"}).json()
    assert [e["nom"] for e in trouves] == ["CEG des Étoiles"]


def test_remplacer_une_proposition_deplace_ses_eleves(
    gestionnaire_clubs: TestClient, en_base: Callable[..., Any]
) -> None:
    proposer(gestionnaire_clubs, en_base, 1, "Lycee Tokoin 1")
    proposition = la_proposition(gestionnaire_clubs, "Lycee Tokoin 1")
    cible = id_de(en_base, Etablissement, "Lycée de Tokoin I")

    reponse = gestionnaire_clubs.post(
        f"{ETABLISSEMENTS}/{proposition['id']}/remplacer", json={"version": proposition["version"], "cible_id": cible}
    )

    assert reponse.status_code == 200, reponse.text
    assert (reponse.json()["id"], reponse.json()["nb_eleves"]) == (cible, 1)
    statut = en_base(lambda db: db.scalar(select(Etablissement.statut).where(Etablissement.id == proposition["id"])))
    assert statut.value == "inactif"
    (entree,) = journal(en_base, "etablissement_remplace")
    assert entree.details["avant"]["nom"] == "Lycee Tokoin 1"
    assert entree.details["apres"]["etablissement_id"] == cible
    assert entree.details["nb_eleves"] == 1


def test_on_ne_remplace_quune_proposition_par_un_etablissement_actif(
    gestionnaire_clubs: TestClient, en_base: Callable[..., Any]
) -> None:
    proposer(gestionnaire_clubs, en_base, 1, "CEG des Étoiles")
    proposer(gestionnaire_clubs, en_base, 2, "CEG Lune")
    proposition = la_proposition(gestionnaire_clubs, "CEG des Étoiles")
    autre_proposition = la_proposition(gestionnaire_clubs, "CEG Lune")
    actif = id_de(en_base, Etablissement, "Lycée de Tokoin I")
    page = gestionnaire_clubs.get(ETABLISSEMENTS, params={"recherche": "Lycée de Tokoin I"}).json()
    lycee = page["etablissements"][0]

    vers_proposition = gestionnaire_clubs.post(
        f"{ETABLISSEMENTS}/{proposition['id']}/remplacer",
        json={"version": proposition["version"], "cible_id": autre_proposition["id"]},
    )
    depuis_actif = gestionnaire_clubs.post(
        f"{ETABLISSEMENTS}/{lycee['id']}/remplacer", json={"version": lycee["version"], "cible_id": actif}
    )

    assert (vers_proposition.status_code, depuis_actif.status_code) == (400, 409)


def test_remplacer_hors_de_son_perimetre_est_refuse(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    proposer(client, en_base, 1, "CEG des Étoiles")
    creer_collaborateur("kara", droits=CLUBS, perimetre_dre="kara")
    connecter_admin(client, "kara")
    proposition_id = id_de(en_base, Etablissement, "CEG des Étoiles")

    reponse = client.post(
        f"{ETABLISSEMENTS}/{proposition_id}/remplacer",
        json={"version": 1, "cible_id": id_de(en_base, Etablissement, "Lycée de Tokoin I")},
    )

    assert reponse.status_code == 403


def test_un_pseudonyme_impose_ne_reprend_pas_le_nom_complet(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    eleve = inscrire(Navigateur(gestionnaire), en_base, 1)

    reponse = gestionnaire.post(
        f"{INSCRITS}/{eleve['id']}/pseudonyme", json={"pseudonyme": "Aya Mensah", "motif": "Test"}
    )

    assert reponse.status_code == 422
