"""Administration du référentiel (spec 016) : droits, périmètre DRE, garde-fous et journal. Écrits avant le code,
comme le demande docs/TESTING.md."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.models import JournalAudit
from app.referentiel.models import Dre, Etablissement
from tests.conftest import connecter_admin

BASE = "/api/admin/referentiel"
DRE = f"{BASE}/dre"
IESG = f"{BASE}/iesg"
ETABLISSEMENTS = f"{BASE}/etablissements"
AXES = f"{BASE}/axes"

CLUBS = {("tableau_de_bord", "consulter"), ("clubs", "consulter"), ("clubs", "creer"), ("clubs", "modifier")}
ANALYSTE = {("tableau_de_bord", "consulter"), ("statistiques", "consulter")}

pytestmark = pytest.mark.usefixtures("annuaire")


# Aides ----------------------------------------------------------------------------------------------------------


@pytest.fixture
def super_admin(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    return client


@pytest.fixture
def gestionnaire_kara(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=CLUBS, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "gestion")
    return client


@pytest.fixture
def gestionnaire_national(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=CLUBS, double_auth=True)
    connecter_admin(client, "gestion")
    return client


def arbre(client: TestClient) -> list[dict[str, Any]]:
    reponse = client.get(DRE)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def une_dre(client: TestClient, code: str) -> dict[str, Any]:
    return next(d for d in arbre(client) if d["code"] == code)


def une_iesg(client: TestClient, nom: str) -> dict[str, Any]:
    return next(i for d in arbre(client) for i in d["iesg"] if i["nom"] == nom)


def un_etablissement(client: TestClient, nom: str) -> dict[str, Any]:
    page = client.get(ETABLISSEMENTS, params={"recherche": nom}).json()
    return next(e for e in page["etablissements"] if e["nom"] == nom)


def journal(en_base: Callable[..., Any], action: str | None = None) -> list[JournalAudit]:
    requete = select(JournalAudit).order_by(JournalAudit.quand)
    if action:
        requete = requete.where(JournalAudit.action == action)
    return en_base(lambda db: db.scalars(requete)).all()


def creer_dre_vide(client: TestClient, code: str = "oti", nom: str = "Oti") -> dict[str, Any]:
    reponse = client.post(
        DRE, json={"code": code, "nom": nom, "nom_complet": f"Direction régionale {nom}", "region": "kara"}
    )
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


# Droits ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("route", [DRE, ETABLISSEMENTS, AXES])
def test_visiteur_refuse(client: TestClient, route: str) -> None:
    assert client.get(route).status_code == 401


def test_sans_droit_clubs_tout_est_refuse_et_journalise(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(droits=ANALYSTE)
    connecter_admin(client)
    iesg = client.get("/api/referentiel/dre").json()[0]["iesg"][0]["id"]

    assert client.get(DRE).status_code == 403
    assert client.get(ETABLISSEMENTS).status_code == 403
    reponse = client.post(ETABLISSEMENTS, json={"iesg_id": iesg, "nom": "Lycée Neuf", "type": "lycee"})
    assert reponse.status_code == 403
    assert len(journal(en_base, "acces_refuse")) == 3
    assert en_base(lambda db: db.scalar(select(func.count()).where(Etablissement.nom == "Lycée Neuf"))) == 0


def test_le_droit_clubs_ne_permet_pas_de_toucher_aux_dre_iesg_et_axes(
    gestionnaire_national: TestClient, en_base: Callable[..., Any]
) -> None:
    client = gestionnaire_national
    kara = une_dre(client, "kara")
    iesg = kara["iesg"][0]
    axe = client.get(AXES).json()[0]

    refus = [
        client.post(DRE, json={"code": "oti", "nom": "Oti", "nom_complet": "DRE Oti", "region": "kara"}),
        client.patch(f"{DRE}/kara", json={"version": kara["version"], "nom": "Kara Nord"}),
        client.post(IESG, json={"dre_code": "kara", "nom": "IESG Nouvelle"}),
        client.patch(f"{IESG}/{iesg['id']}", json={"version": iesg["version"], "nom": "IESG Renommée"}),
        client.post(AXES, json={"code": "nouvel-axe", "libelle": "Nouvel axe", "description": "Un axe"}),
        client.patch(f"{AXES}/{axe['code']}", json={"version": axe["version"], "libelle": "Autre"}),
    ]

    assert [r.status_code for r in refus] == [403] * 6
    assert une_dre(client, "kara")["nom"] == "Kara"
    assert len(journal(en_base, "acces_refuse")) == 6


def test_le_droit_clubs_permet_de_lire_dre_et_axes(gestionnaire_national: TestClient) -> None:
    assert len(arbre(gestionnaire_national)) == 7
    assert len(gestionnaire_national.get(AXES).json()) == 7


def test_un_gestionnaire_de_dre_ne_voit_que_sa_dre(gestionnaire_kara: TestClient, en_base: Callable[..., Any]) -> None:
    client = gestionnaire_kara
    assert [d["code"] for d in arbre(client)] == ["kara"]

    page = client.get(ETABLISSEMENTS, params={"par_page": 100}).json()
    assert page["total"] == une_dre(client, "kara")["nb_etablissements"]
    assert {e["dre_code"] for e in page["etablissements"]} == {"kara"}
    assert client.get(ETABLISSEMENTS, params={"dre": "savanes"}).json()["total"] == 0


def test_un_gestionnaire_de_dre_ne_modifie_pas_une_autre_dre(
    gestionnaire_kara: TestClient, client: TestClient, en_base: Callable[..., Any]
) -> None:
    autre = client.get("/api/referentiel/etablissements", params={"recherche": "lycee", "dre": "savanes"}).json()[0]
    version = en_base(lambda db: db.scalar(select(Etablissement.version).where(Etablissement.id == autre["id"])))

    reponse = client.patch(f"{ETABLISSEMENTS}/{autre['id']}", json={"version": version, "nom": "Piraté"})

    assert reponse.status_code == 403
    assert en_base(lambda db: db.scalar(select(Etablissement.nom).where(Etablissement.id == autre["id"]))) != "Piraté"
    assert journal(en_base, "acces_refuse")


def test_un_gestionnaire_de_dre_ne_cree_ni_ne_deplace_hors_de_sa_dre(
    gestionnaire_kara: TestClient, en_base: Callable[..., Any]
) -> None:
    client = gestionnaire_kara
    savanes = client.get("/api/referentiel/dre").json()[0]
    assert savanes["code"] == "savanes"
    iesg_savanes = savanes["iesg"][0]["id"]

    creation = client.post(ETABLISSEMENTS, json={"iesg_id": iesg_savanes, "nom": "Lycée Neuf", "type": "lycee"})
    assert creation.status_code == 403

    a_moi = client.get(ETABLISSEMENTS).json()["etablissements"][0]
    deplacement = client.patch(
        f"{ETABLISSEMENTS}/{a_moi['id']}", json={"version": a_moi["version"], "iesg_id": iesg_savanes}
    )
    assert deplacement.status_code == 403

    assert len(journal(en_base, "acces_refuse")) == 2
    assert en_base(lambda db: db.scalar(select(func.count()).where(Etablissement.nom == "Lycée Neuf"))) == 0
    assert un_etablissement(client, a_moi["nom"])["iesg_id"] == a_moi["iesg_id"]


def test_un_gestionnaire_de_dre_cree_et_modifie_dans_sa_dre(
    gestionnaire_kara: TestClient, en_base: Callable[..., Any]
) -> None:
    client = gestionnaire_kara
    iesg = une_dre(client, "kara")["iesg"][0]

    creation = client.post(
        ETABLISSEMENTS, json={"iesg_id": iesg["id"], "nom": "  Lycée   Neuf ", "type": "lycee", "localite": "Kara"}
    )
    assert creation.status_code == 201, creation.text
    cree = creation.json()
    assert cree["nom"] == "Lycée Neuf"
    assert cree["dre_code"] == "kara"
    assert cree["statut"] == "actif"

    modification = client.patch(f"{ETABLISSEMENTS}/{cree['id']}", json={"version": cree["version"], "type": "college"})
    assert modification.status_code == 200, modification.text
    assert modification.json()["type"] == "college"
    assert [e.action for e in journal(en_base) if e.cible_type == "etablissement"] == [
        "referentiel_cree",
        "referentiel_modifie",
    ]


@pytest.mark.parametrize("route", [f"{DRE}/kara", f"{AXES}/genie-imhotep", ETABLISSEMENTS, IESG])
def test_aucune_route_de_suppression(super_admin: TestClient, route: str) -> None:
    assert super_admin.delete(route).status_code in (404, 405)


# Doublons et versions --------------------------------------------------------------------------------------------


def test_un_doublon_dans_la_meme_iesg_est_refuse(super_admin: TestClient) -> None:
    golfe = une_iesg(super_admin, "IESG Golfe")
    reponse = super_admin.post(
        ETABLISSEMENTS, json={"iesg_id": golfe["id"], "nom": "LYCEE  de tokoin i", "type": "lycee"}
    )
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Un établissement du même nom existe déjà dans cette IESG."


def test_le_meme_nom_dans_une_autre_iesg_est_accepte(super_admin: TestClient) -> None:
    agoe = une_iesg(super_admin, "IESG Agoényivé")
    reponse = super_admin.post(
        ETABLISSEMENTS, json={"iesg_id": agoe["id"], "nom": "Lycée de Tokoin I", "type": "lycee"}
    )
    assert reponse.status_code == 201


def test_renommer_en_doublon_est_refuse(super_admin: TestClient) -> None:
    lycee = un_etablissement(super_admin, "Lycée de Tokoin II")
    reponse = super_admin.patch(
        f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "nom": "Lycée de Tokoin I"}
    )
    assert reponse.status_code == 409


def test_une_version_perimee_est_refusee(super_admin: TestClient) -> None:
    lycee = un_etablissement(super_admin, "Lycée de Tokoin I")
    premiere = super_admin.patch(
        f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "localite": "Lomé"}
    )
    assert premiere.status_code == 200
    assert premiere.json()["version"] == lycee["version"] + 1

    seconde = super_admin.patch(f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "nom": "Autre"})

    assert seconde.status_code == 409
    assert "modifié entre-temps" in seconde.json()["detail"]
    assert un_etablissement(super_admin, "Lycée de Tokoin I")["localite"] == "Lomé"


def test_doublons_de_dre_d_iesg_et_d_axes_refuses(super_admin: TestClient) -> None:
    assert (
        super_admin.post(DRE, json={"code": "kara", "nom": "Autre", "nom_complet": "X", "region": "kara"}).status_code
        == 409
    )
    assert (
        super_admin.post(DRE, json={"code": "kara-2", "nom": "KARA", "nom_complet": "X", "region": "kara"}).status_code
        == 409
    )
    assert super_admin.post(IESG, json={"dre_code": "grand-lome", "nom": "iesg golfe"}).status_code == 409
    axe = {"code": "genie-2", "libelle": "génie imhotep", "description": "Doublon"}
    assert super_admin.post(AXES, json=axe).status_code == 409


@pytest.mark.parametrize(
    "corps",
    [
        {"code": "Oti", "nom": "Oti", "nom_complet": "DRE Oti", "region": "kara"},
        {"code": "o ti", "nom": "Oti", "nom_complet": "DRE Oti", "region": "kara"},
        {"code": "oti", "nom": "   ", "nom_complet": "DRE Oti", "region": "kara"},
        {"code": "oti", "nom": "x" * 151, "nom_complet": "DRE Oti", "region": "kara"},
        {"code": "oti", "nom": "Oti", "nom_complet": "DRE Oti", "inconnu": 1},
        {"code": "oti", "nom": "Oti", "nom_complet": "x" * 201},
    ],
)
def test_valeurs_invalides_refusees(super_admin: TestClient, corps: dict[str, Any]) -> None:
    assert super_admin.post(DRE, json=corps).status_code == 422


def test_le_code_ne_se_modifie_pas(super_admin: TestClient) -> None:
    kara = une_dre(super_admin, "kara")
    assert super_admin.patch(f"{DRE}/kara", json={"version": kara["version"], "code": "kara-2"}).status_code == 422


# Garde-fous ------------------------------------------------------------------------------------------------------


def test_desactiver_une_dre_avec_des_iesg_actives_est_refuse(super_admin: TestClient) -> None:
    kara = une_dre(super_admin, "kara")
    reponse = super_admin.patch(f"{DRE}/kara", json={"version": kara["version"], "actif": False})
    assert reponse.status_code == 400
    assert "IESG" in reponse.json()["detail"]


def test_desactiver_une_iesg_avec_des_etablissements_actifs_est_refuse(super_admin: TestClient) -> None:
    golfe = une_iesg(super_admin, "IESG Golfe")
    reponse = super_admin.patch(f"{IESG}/{golfe['id']}", json={"version": golfe["version"], "actif": False})
    assert reponse.status_code == 400
    assert "établissements" in reponse.json()["detail"]


def test_desactiver_une_dre_perimetre_d_un_collaborateur_est_refuse(
    super_admin: TestClient, creer_collaborateur: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    oti = creer_dre_vide(super_admin)
    creer_collaborateur("regional", perimetre_dre="oti")

    reponse = super_admin.patch(f"{DRE}/oti", json={"version": oti["version"], "actif": False})

    assert reponse.status_code == 400
    assert "Jean Kodjo" in reponse.json()["detail"]


def test_une_dre_vide_et_sans_collaborateur_se_desactive_et_quitte_les_listes(super_admin: TestClient) -> None:
    oti = creer_dre_vide(super_admin)

    reponse = super_admin.patch(f"{DRE}/oti", json={"version": oti["version"], "actif": False})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["actif"] is False
    assert "oti" not in [d["code"] for d in super_admin.get("/api/referentiel/dre").json()]
    catalogue = super_admin.get("/api/admin/catalogue").json()
    assert "oti" in catalogue["dre"]
    assert "oti" not in catalogue["dre_actives"]

    invitation = {"email": "x@aimes.tg", "prenom": "X", "nom": "Y", "droits": [], "perimetre_dre": "oti"}
    assert super_admin.post("/api/admin/collaborateurs", json=invitation).status_code == 422


def test_on_ne_desactive_pas_le_dernier_axe(super_admin: TestClient) -> None:
    axes = super_admin.get(AXES).json()
    for axe in axes[:-1]:
        reponse = super_admin.patch(f"{AXES}/{axe['code']}", json={"version": axe["version"], "actif": False})
        assert reponse.status_code == 200, reponse.text

    dernier = axes[-1]
    reponse = super_admin.patch(f"{AXES}/{dernier['code']}", json={"version": dernier["version"], "actif": False})
    assert reponse.status_code == 400


def test_on_ne_deplace_pas_une_iesg_vers_une_dre_inactive(super_admin: TestClient) -> None:
    oti = creer_dre_vide(super_admin)
    super_admin.patch(f"{DRE}/oti", json={"version": oti["version"], "actif": False})
    golfe = une_iesg(super_admin, "IESG Golfe")

    reponse = super_admin.patch(f"{IESG}/{golfe['id']}", json={"version": golfe["version"], "dre_code": "oti"})

    assert reponse.status_code == 400


def test_iesg_inactive_ni_creation_ni_deplacement_ni_reactivation_dessous(super_admin: TestClient) -> None:
    nouvelle = super_admin.post(IESG, json={"dre_code": "kara", "nom": "IESG Vide"}).json()
    super_admin.patch(f"{IESG}/{nouvelle['id']}", json={"version": nouvelle["version"], "actif": False})

    creation = super_admin.post(ETABLISSEMENTS, json={"iesg_id": nouvelle["id"], "nom": "Lycée X", "type": "lycee"})
    assert creation.status_code == 400

    lycee = un_etablissement(super_admin, "Lycée de Tokoin I")
    deplacement = super_admin.patch(
        f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "iesg_id": nouvelle["id"]}
    )
    assert deplacement.status_code == 400

    # Un établissement inactif sous une IESG qu'on désactive ensuite ne peut pas être réactivé seul.
    iesg = super_admin.post(IESG, json={"dre_code": "kara", "nom": "IESG Seconde"}).json()
    ecole = super_admin.post(ETABLISSEMENTS, json={"iesg_id": iesg["id"], "nom": "CEG Y", "type": "college"}).json()
    ecole = super_admin.patch(
        f"{ETABLISSEMENTS}/{ecole['id']}", json={"version": ecole["version"], "statut": "inactif"}
    )
    ecole = ecole.json()
    iesg = une_iesg(super_admin, "IESG Seconde")
    assert (
        super_admin.patch(f"{IESG}/{iesg['id']}", json={"version": iesg["version"], "actif": False}).status_code == 200
    )
    reactivation = super_admin.patch(
        f"{ETABLISSEMENTS}/{ecole['id']}", json={"version": ecole["version"], "statut": "actif"}
    )
    assert reactivation.status_code == 400


def test_le_statut_propose_ne_se_choisit_pas(super_admin: TestClient) -> None:
    lycee = un_etablissement(super_admin, "Lycée de Tokoin I")
    reponse = super_admin.patch(
        f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "statut": "propose"}
    )
    assert reponse.status_code == 422


# Déplacements, renommages et journal ----------------------------------------------------------------------------


def test_deplacer_une_iesg_change_la_dre_de_ses_etablissements(
    super_admin: TestClient, en_base: Callable[..., Any]
) -> None:
    golfe = une_iesg(super_admin, "IESG Golfe")

    reponse = super_admin.patch(f"{IESG}/{golfe['id']}", json={"version": golfe["version"], "dre_code": "maritime"})

    assert reponse.status_code == 200, reponse.text
    assert un_etablissement(super_admin, "Lycée de Tokoin I")["dre_code"] == "maritime"
    publiques = {d["code"]: d for d in super_admin.get("/api/referentiel/dre").json()}
    assert publiques["grand-lome"]["nb_etablissements"] == 18
    assert "IESG Golfe" in [i["nom"] for i in publiques["maritime"]["iesg"]]
    entree = journal(en_base, "referentiel_modifie")[-1]
    assert entree.cible_type == "iesg"
    assert entree.details["avant"]["dre_code"] == "grand-lome"
    assert entree.details["apres"]["dre_code"] == "maritime"


def test_renommer_une_dre_garde_son_code_et_les_perimetres(
    super_admin: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur("regional", perimetre_dre="kara")
    kara = une_dre(super_admin, "kara")

    reponse = super_admin.patch(f"{DRE}/kara", json={"version": kara["version"], "nom": "Kara (DRE)"})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["code"] == "kara"
    assert super_admin.get("/api/admin/catalogue").json()["dre"]["kara"] == "Kara (DRE)"
    assert en_base(lambda db: db.scalar(select(Dre.nom).where(Dre.code == "kara"))) == "Kara (DRE)"


def test_une_modification_est_journalisee_avec_avant_et_apres(
    super_admin: TestClient, en_base: Callable[..., Any]
) -> None:
    lycee = un_etablissement(super_admin, "Lycée de Tokoin I")

    super_admin.patch(f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "nom": "Lycée de Tokoin 1"})

    entree = journal(en_base, "referentiel_modifie")[-1]
    assert entree.auteur_libelle and "chef" in entree.auteur_libelle
    assert entree.cible_type == "etablissement"
    assert entree.cible_id == lycee["id"]
    assert entree.perimetre == "grand-lome"
    assert entree.details == {"avant": {"nom": "Lycée de Tokoin I"}, "apres": {"nom": "Lycée de Tokoin 1"}}


def test_desactiver_puis_reactiver_est_journalise(super_admin: TestClient, en_base: Callable[..., Any]) -> None:
    lycee = un_etablissement(super_admin, "Lycée de Tokoin I")
    inactif = super_admin.patch(
        f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "statut": "inactif"}
    )
    super_admin.patch(f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": inactif.json()["version"], "statut": "actif"})

    actions = [e.action for e in journal(en_base) if e.cible_type == "etablissement"]
    assert actions == ["referentiel_desactive", "referentiel_reactive"]


def test_renommer_un_axe_garde_son_code(super_admin: TestClient) -> None:
    axe = super_admin.get(AXES).json()[0]
    reponse = super_admin.patch(
        f"{AXES}/{axe['code']}", json={"version": axe["version"], "libelle": "Génie Imhotep, l'académie"}
    )
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["code"] == "genie-imhotep"
    publics = super_admin.get("/api/referentiel/axes").json()
    assert publics[0] == {
        "code": "genie-imhotep",
        "libelle": "Génie Imhotep, l'académie",
        "description": axe["description"],
    }


def test_creer_une_iesg_et_un_axe(super_admin: TestClient) -> None:
    iesg = super_admin.post(IESG, json={"dre_code": "kara", "nom": "IESG Nouvelle", "zone": "Pya"})
    assert iesg.status_code == 201, iesg.text
    assert iesg.json()["zone"] == "Pya"
    axe = super_admin.post(AXES, json={"code": "nouvel-axe", "libelle": "Nouvel axe", "description": "Un axe"})
    assert axe.status_code == 201, axe.text
    assert axe.json()["ordre"] == 8


# Liste des établissements -----------------------------------------------------------------------------------------


def test_la_liste_admin_est_paginee_et_filtrable(super_admin: TestClient) -> None:
    page = super_admin.get(ETABLISSEMENTS).json()
    assert page["total"] == 838
    assert page["par_page"] == 50
    assert len(page["etablissements"]) == 50

    lycees_kara = super_admin.get(ETABLISSEMENTS, params={"dre": "kara", "type": "lycee"}).json()
    assert lycees_kara["total"] > 0
    assert {(e["dre_code"], e["type"]) for e in lycees_kara["etablissements"]} == {("kara", "lycee")}


def test_la_liste_admin_montre_les_inactifs(super_admin: TestClient) -> None:
    lycee = un_etablissement(super_admin, "Lycée de Tokoin I")
    super_admin.patch(f"{ETABLISSEMENTS}/{lycee['id']}", json={"version": lycee["version"], "statut": "inactif"})

    inactifs = super_admin.get(ETABLISSEMENTS, params={"statut": "inactif"}).json()

    assert [e["nom"] for e in inactifs["etablissements"]] == ["Lycée de Tokoin I"]


def test_le_tableau_de_bord_compte_dre_et_etablissements_actifs(super_admin: TestClient) -> None:
    indicateurs = {i["id"]: i["valeur"] for i in super_admin.get("/api/admin/tableau-de-bord").json()["indicateurs"]}
    assert indicateurs["dre_actives"] == 7
    assert indicateurs["etablissements_actifs"] == 838


def test_un_nom_complet_long_mais_valide_est_accepte(super_admin: TestClient) -> None:
    reponse = super_admin.post(DRE, json={"code": "oti", "nom": "Oti", "nom_complet": "x" * 200, "region": "kara"})
    assert reponse.status_code == 201, reponse.text


def test_une_description_d_axe_faite_d_espaces_est_refusee(super_admin: TestClient) -> None:
    axe = {"code": "vide", "libelle": "Vide", "description": "   "}
    assert super_admin.post(AXES, json=axe).status_code == 422
    premier = super_admin.get(AXES).json()[0]
    modification = {"version": premier["version"], "description": "  "}
    assert super_admin.patch(f"{AXES}/{premier['code']}", json=modification).status_code == 422


def test_une_ecriture_concurrente_entre_lecture_et_ecriture_est_refusee() -> None:
    """La version est vérifiée avant d'écrire, mais une autre écriture peut passer juste entre les deux : la base
    refuse alors la mise à jour (`version_id_col`), et rien n'est écrasé."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.referentiel import administration
    from tests.conftest import moteur_test

    async def scenario() -> tuple[int, str | None]:
        async with AsyncSession(moteur_test) as premier, AsyncSession(moteur_test) as second:
            lu = await premier.scalar(select(Etablissement).where(Etablissement.nom == "Lycée de Tokoin I"))
            assert lu is not None
            ident = lu.id
            autre = await second.get(Etablissement, ident)
            assert autre is not None
            autre.localite = "Second"
            await second.commit()

            lu.localite = "Premier"
            with pytest.raises(administration.Refus) as refus:
                await administration._ecrire(premier)
        async with AsyncSession(moteur_test) as lecture:
            return refus.value.statut, await lecture.scalar(
                select(Etablissement.localite).where(Etablissement.id == ident)
            )

    import asyncio

    assert asyncio.run(scenario()) == (409, "Second")
