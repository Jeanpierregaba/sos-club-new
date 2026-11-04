"""Les encadreurs dans les écrans admin existants (spec 018) : fiche d'un inscrit, recherche, tableau de bord,
compteur du menu, établissements."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from app.config import settings
from app.encadreurs.models import Encadreur
from app.referentiel.models import Etablissement, Iesg
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin

INSCRITS = "/api/admin/inscrits"
ETABLISSEMENTS = "/api/admin/referentiel/etablissements"
FILE = "/api/admin/encadreurs"
VERIFICATION = {("tableau_de_bord", "consulter"), ("encadreurs", "consulter"), ("encadreurs", "approuver")}
GESTION = VERIFICATION | {("inscrits", "consulter"), ("clubs", "consulter"), ("clubs", "modifier")}

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


def id_de(en_base: Callable[..., Any], modele: Any, nom: str) -> str:
    return str(en_base(lambda db: db.scalar(select(modele.id).where(modele.nom == nom))))


def inscrire(navigateur: Any, en_base: Callable[..., Any], numero: int, **champs: Any) -> dict[str, Any]:
    corps = {
        "prenom": "Kossi", "nom": "Agbeko", "email": f"prof{numero}@ecole.tg", "telephone": "+228 90 12 34 56",
        "identifiant": f"prof{numero}", "mot_de_passe": MOT_DE_PASSE, "fonction": "enseignant", "charte": True,
        "consentement": True, "etablissement_id": id_de(en_base, Etablissement, "Lycée de Tokoin I"),
    } | champs  # fmt: skip
    reponse = navigateur.post("/api/encadreurs/inscription", json=corps)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=GESTION, double_auth=True)
    connecter_admin(client, "gestion")
    return client


def test_la_fiche_dun_encadreur_montre_son_profil_et_sa_verification(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    encadreur = inscrire(Navigateur(gestionnaire), en_base, 1)
    gestionnaire.post(f"{FILE}/{encadreur['id']}/activer")

    fiche = gestionnaire.get(f"{INSCRITS}/{encadreur['id']}").json()

    profil = fiche["encadreur"]
    assert (profil["fonction"], profil["etat"]) == ("enseignant", "actif")
    assert profil["etablissement"]["nom"] == "Lycée de Tokoin I"
    assert profil["decide_par"] == "Jean Kodjo"
    assert profil["points"]["total"] == 100
    assert fiche["eleve"] is None
    assert [e["action"] for e in fiche["historique"]] == ["encadreur_active", "inscription_encadreur"]


def test_la_recherche_trouve_un_telephone_saisi_avec_des_espaces(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    inscrire(Navigateur(gestionnaire), en_base, 1)

    trouves = gestionnaire.get(INSCRITS, params={"recherche": "90 12 34"}).json()["inscrits"]
    peu_de_chiffres = gestionnaire.get(INSCRITS, params={"recherche": "9"}).json()["inscrits"]

    assert [i["identifiant"] for i in trouves] == ["prof1"]
    assert peu_de_chiffres == []


def test_le_tableau_de_bord_et_le_menu_comptent_les_demandes_du_perimetre(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    inscrire(Navigateur(client), en_base, 1)
    kara = str(
        en_base(
            lambda db: db.scalar(
                select(Etablissement.id).join(Iesg, Iesg.id == Etablissement.iesg_id).where(Iesg.dre_code == "kara")
                .limit(1)
            )
        )
    )  # fmt: skip
    inscrire(Navigateur(client), en_base, 2, etablissement_id=kara)
    creer_collaborateur("national", droits=VERIFICATION, double_auth=True)
    creer_collaborateur("kara", droits=VERIFICATION, perimetre_dre="kara", double_auth=True)
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})

    comptes = {}
    for identifiant in ("national", "kara", "autre"):
        navigateur = Navigateur(client)
        connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
        comptes[identifiant] = (
            navigateur.get("/api/admin/tableau-de-bord").json()["encadreurs_a_verifier"],
            navigateur.get("/api/admin/moi").json()["encadreurs_a_verifier"],
        )

    assert comptes == {"national": (2, 2), "kara": (1, 1), "autre": (None, None)}


def test_la_liste_des_etablissements_compte_les_encadreurs(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    inscrire(Navigateur(gestionnaire), en_base, 1)

    page = gestionnaire.get(ETABLISSEMENTS, params={"recherche": "Lycée de Tokoin I"}).json()

    lycee = next(e for e in page["etablissements"] if e["nom"] == "Lycée de Tokoin I")
    assert (lycee["nb_eleves"], lycee["nb_encadreurs"]) == (0, 1)


def test_remplacer_une_proposition_deplace_aussi_ses_encadreurs(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    iesg = id_de(en_base, Iesg, "IESG Golfe")
    inscrire(
        Navigateur(gestionnaire),
        en_base,
        1,
        etablissement_id=None,
        proposition={"iesg_id": iesg, "nom": "Lycee Tokoin 1"},
    )
    page = gestionnaire.get(ETABLISSEMENTS, params={"recherche": "Lycee Tokoin 1", "statut": "propose"}).json()
    proposition = page["etablissements"][0]
    cible = id_de(en_base, Etablissement, "Lycée de Tokoin I")

    reponse = gestionnaire.post(
        f"{ETABLISSEMENTS}/{proposition['id']}/remplacer", json={"version": proposition["version"], "cible_id": cible}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["nb_encadreurs"] == 1
    # La version monte : un profil ouvert avant le remplacement ne l'écrase pas.
    assert en_base(lambda db: db.scalar(select(Encadreur.version))) == 2
    assert str(en_base(lambda db: db.scalar(select(Encadreur.etablissement_id)))) == cible
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "etablissement_remplace"))
    ).all()
    assert entree.details["nb_encadreurs"] == 1
