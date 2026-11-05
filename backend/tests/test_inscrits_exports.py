"""Annuaire des inscrits, exports, journal et tableau de bord (spec 015)."""

import csv
import io
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import select, text, update

from app.admin.models import Export, JournalAudit
from app.comptes.models import Role, Utilisateur
from tests.conftest import Navigateur, connecter_admin

INSCRITS = "/api/admin/inscrits"
EXPORTS = "/api/admin/exports"
ANALYSTE = {("tableau_de_bord", "consulter"), ("statistiques", "consulter"), ("statistiques", "exporter")}
NOMINATIF = {"type": "nominatif", "format": "csv", "colonnes": ["identifiant", "nom", "email"], "finalite": "Bilan DRE"}


@pytest.fixture
def chef(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Utilisateur:
    utilisateur = creer_collaborateur("chef", super_admin=True, double_auth=True)
    connecter_admin(client)
    return utilisateur


@pytest.fixture
def eleves(creer_utilisateur: Callable[..., Utilisateur]) -> list[Utilisateur]:
    return [
        creer_utilisateur("ama", prenom="Ama", nom="Mensah"),
        creer_utilisateur("kofi", prenom="Kofi", nom="=HYPERLINK(1)"),
        creer_utilisateur("prof", Role.encadreur, email="prof@ecole.tg", prenom="Yao", nom="Agbo"),
    ]


def lire_csv(contenu: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(contenu.decode("utf-8-sig")), delimiter=";"))


def exporter(client: Any, corps: dict[str, Any]) -> Any:
    reponse = client.post(EXPORTS, json=corps)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


# Annuaire -------------------------------------------------------------------------------------------------------


def test_annuaire_recherche_et_filtres(client: TestClient, chef: Utilisateur, eleves: list[Utilisateur]) -> None:
    tous = client.get(INSCRITS).json()
    assert tous["total"] == 4
    assert {i["identifiant"] for i in client.get(INSCRITS, params={"profil": "eleve"}).json()["inscrits"]} == {
        "ama",
        "kofi",
    }
    assert [i["identifiant"] for i in client.get(INSCRITS, params={"recherche": "MENS"}).json()["inscrits"]] == ["ama"]
    assert client.get(INSCRITS, params={"recherche": "%"}).json()["total"] == 0
    page = client.get(INSCRITS, params={"par_page": 2, "page": 2}).json()
    assert len(page["inscrits"]) == 2 and page["total"] == 4


def test_suspendre_un_eleve_coupe_sa_session_et_garde_l_historique(
    client: TestClient, chef: Utilisateur, eleves: list[Utilisateur]
) -> None:
    eleve = Navigateur(client)
    eleve.post("/api/comptes/connexion", json={"identifiant": "ama", "mot_de_passe": "mot-de-passe-de-test"})
    assert eleve.get("/api/comptes/moi").status_code == 200

    reponse = client.post(f"{INSCRITS}/{eleves[0].id}/suspendre", json={"motif": "Faux compte signalé"})

    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "suspendu"
    assert reponse.json()["historique"][0]["details"]["motif"] == "Faux compte signalé"
    assert eleve.get("/api/comptes/moi").status_code == 401


def test_un_collaborateur_ne_se_suspend_pas_depuis_l_annuaire(client: TestClient, chef: Utilisateur) -> None:
    assert client.post(f"{INSCRITS}/{chef.id}/suspendre", json={"motif": "Essai"}).status_code == 409


# Exports --------------------------------------------------------------------------------------------------------


def test_export_nominatif_csv_avec_trois_colonnes(
    client: TestClient, chef: Utilisateur, eleves: list[Utilisateur], en_base: Callable[..., Any]
) -> None:
    cree = exporter(client, NOMINATIF)

    fichier = client.get(cree["lien"])

    assert fichier.status_code == 200
    assert fichier.headers["content-disposition"].startswith("attachment")
    lignes = lire_csv(fichier.content)
    assert lignes[0] == ["Identifiant", "Nom", "E-mail"]
    assert len(lignes) == 5
    assert ["kofi", "'=HYPERLINK(1)", ""] in lignes
    actions = en_base(lambda db: db.scalars(select(JournalAudit.action))).all()
    assert "export_demande" in actions and "export_telecharge" in actions
    assert client.get(EXPORTS).json()[0]["statut"] == "telecharge"


def test_export_nominatif_xlsx(client: TestClient, chef: Utilisateur, eleves: list[Utilisateur]) -> None:
    cree = exporter(client, NOMINATIF | {"format": "xlsx", "filtres": {"profil": "eleve"}})

    classeur = load_workbook(io.BytesIO(client.get(cree["lien"]).content))
    lignes = list(classeur.active.iter_rows(values_only=True))

    assert lignes[0] == ("Identifiant", "Nom", "E-mail")
    assert len(lignes) == 3
    assert ("kofi", "'=HYPERLINK(1)", None) in lignes or ("kofi", "'=HYPERLINK(1)", "") in lignes


def test_aucun_secret_dans_les_exports(client: TestClient, chef: Utilisateur, eleves: list[Utilisateur]) -> None:
    colonnes = [
        "identifiant",
        "nom",
        "prenom",
        "email",
        "telephone",
        "profil",
        "statut",
        "date_inscription",
        "consentement",
    ]
    cree = exporter(client, NOMINATIF | {"colonnes": colonnes})
    contenu = client.get(cree["lien"]).content.decode("utf-8-sig")

    assert "$argon2" not in contenu
    assert client.post(EXPORTS, json=NOMINATIF | {"colonnes": ["mot_de_passe_hash"]}).status_code == 422


def test_le_lien_ne_sert_qu_une_fois_et_qu_au_demandeur(
    client: TestClient, chef: Utilisateur, eleves: list[Utilisateur], creer_collaborateur: Callable[..., Any]
) -> None:
    cree = exporter(client, NOMINATIF)
    autre = Navigateur(client)
    creer_collaborateur("autre", super_admin=True, double_auth=True)
    connecter_admin(autre, "autre")

    assert autre.get(cree["lien"]).status_code == 404
    assert client.get(cree["lien"]).status_code == 200
    assert client.get(cree["lien"]).status_code == 404


def test_lien_sans_session_ou_expire(
    client: TestClient, chef: Utilisateur, eleves: list[Utilisateur], en_base: Callable[..., Any]
) -> None:
    cree = exporter(client, NOMINATIF)
    assert Navigateur(client).get(cree["lien"]).status_code == 401

    en_base(lambda db: db.execute(update(Export).values(lien_expire_le=datetime.now(UTC) - timedelta(seconds=1))))

    assert client.get(cree["lien"]).status_code == 404


def test_finalite_obligatoire_et_export_vide(client: TestClient, chef: Utilisateur, eleves: list[Utilisateur]) -> None:
    assert client.post(EXPORTS, json=NOMINATIF | {"finalite": ""}).status_code == 422
    vide = NOMINATIF | {"filtres": {"recherche": "personne-de-ce-nom"}}
    assert client.post(f"{EXPORTS}/apercu", json=vide).json()["nb_lignes"] == 0
    assert client.post(EXPORTS, json=vide).status_code == 422


def test_analyste_exporte_l_agrege_mais_pas_le_nominatif(
    client: TestClient, creer_collaborateur: Callable[..., Any], eleves: list[Utilisateur]
) -> None:
    creer_collaborateur("analyste", droits=ANALYSTE)
    connecter_admin(client, "analyste")

    cree = exporter(client, {"type": "agrege", "format": "csv"})
    lignes = lire_csv(client.get(cree["lien"]).content)
    assert lignes[0] == ["Profil", "Statut", "Mois d'inscription", "Nombre de comptes"]
    assert sum(int(ligne[3]) for ligne in lignes[1:]) == 4

    assert client.post(EXPORTS, json=NOMINATIF).status_code == 403
    assert all(e["type"] == "agrege" for e in client.get(EXPORTS).json())


def test_purge_des_fichiers_expires(
    client: TestClient, chef: Utilisateur, eleves: list[Utilisateur], en_base: Callable[..., Any]
) -> None:
    from app.admin.exports import purger

    exporter(client, NOMINATIF)
    en_base(lambda db: db.execute(update(Export).values(fichier_expire_le=datetime.now(UTC) - timedelta(seconds=1))))

    assert en_base(purger) == 1
    assert en_base(lambda db: db.scalar(select(Export.fichier))) is None


# Journal et tableau de bord -------------------------------------------------------------------------------------


def test_le_journal_refuse_modification_et_suppression(chef: Utilisateur, en_base: Callable[..., Any]) -> None:
    from sqlalchemy.exc import DBAPIError

    with pytest.raises(DBAPIError, match="ne se modifie pas"):
        en_base(lambda db: db.execute(text("UPDATE journal_audit SET action = 'efface'")))
    with pytest.raises(DBAPIError, match="ne se modifie pas"):
        en_base(lambda db: db.execute(text("DELETE FROM journal_audit")))


def test_le_journal_n_a_aucune_route_d_ecriture(client: TestClient, chef: Utilisateur) -> None:
    from app.main import app

    chemins = {chemin: set(methodes) for chemin, methodes in app.openapi()["paths"].items() if "journal" in chemin}

    assert chemins == {"/api/admin/journal": {"get"}}


def test_journal_filtre(client: TestClient, chef: Utilisateur) -> None:
    corps = client.get("/api/admin/journal", params={"action": "connexion"}).json()

    assert corps["total"] >= 1
    assert all(e["action"] == "connexion" for e in corps["evenements"])
    assert corps["evenements"][0]["auteur_libelle"].startswith("Jean Kodjo")


def test_tableau_de_bord_sur_les_vraies_donnees(
    client: TestClient, chef: Utilisateur, eleves: list[Utilisateur]
) -> None:
    corps = client.get("/api/admin/tableau-de-bord").json()

    assert corps["comptes_par_profil"] == {"eleve": 2, "encadreur": 1, "admin": 1}
    assert len(corps["inscriptions_30_jours"]) == 30
    assert sum(n for _, n in corps["inscriptions_30_jours"]) == 4
    indicateurs = {i["id"]: i for i in corps["indicateurs"]}
    assert indicateurs["collaborateurs_actifs"]["valeur"] == 1
    assert indicateurs["clubs_actifs"]["valeur"] == 0
    assert indicateurs["clubs_actifs"]["disponible_avec"] is None
    assert datetime.fromisoformat(corps["calcule_le"]) <= datetime.now(UTC)
