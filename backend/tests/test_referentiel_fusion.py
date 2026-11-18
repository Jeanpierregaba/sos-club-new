"""Doublons d'établissements et fusion (spec 042), côté administration : liste des doublons probables, écarts,
fusion. Partie critique (déplace des comptes et des clubs)."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.clubs.models import CLUB_VIVANT, Adhesion, Club, EtatClub
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from tests.activation import ajouter_eleves, ajouter_encadreur, peupler, recalculer
from tests.conftest import connecter_admin

BASE = "/api/admin/referentiel"
ETABLISSEMENTS = f"{BASE}/etablissements"
DOUBLONS = f"{ETABLISSEMENTS}/doublons"

CLUBS = {("tableau_de_bord", "consulter"), ("clubs", "consulter"), ("clubs", "creer"), ("clubs", "modifier")}
LECTURE = {("tableau_de_bord", "consulter"), ("clubs", "consulter")}

pytestmark = pytest.mark.usefixtures("annuaire")


# Aides ----------------------------------------------------------------------------------------------------------


@pytest.fixture
def national(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=CLUBS, double_auth=True)
    connecter_admin(client, "gestion")
    return client


def connecter(
    client: TestClient, creer_collaborateur: Callable[..., Any], nom: str, droits: Any, dre: str | None
) -> None:
    creer_collaborateur(nom, droits=droits, perimetre_dre=dre, double_auth=True)
    client.cookies.clear()
    connecter_admin(client, nom)


def iesg(client: TestClient, nom: str) -> str:
    dre = client.get(f"{BASE}/dre").json()
    return next(i["id"] for d in dre for i in d["iesg"] if i["nom"] == nom)


def etablissement(client: TestClient, nom: str) -> dict[str, Any]:
    page = client.get(ETABLISSEMENTS, params={"recherche": nom, "par_page": 100}).json()
    return next(e for e in page["etablissements"] if e["nom"] == nom)


def creer(client: TestClient, nom: str, inspection: str = "IESG Golfe", **champs: Any) -> dict[str, Any]:
    reponse = client.post(
        ETABLISSEMENTS, json={"iesg_id": iesg(client, inspection), "nom": nom, "type": "lycee"} | champs
    )
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def paires(client: TestClient, **filtres: Any) -> list[dict[str, Any]]:
    reponse = client.get(DOUBLONS, params=filtres)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["paires"]


def noms(liste: list[dict[str, Any]]) -> list[set[str]]:
    return [{p["a"]["nom"], p["b"]["nom"]} for p in liste]


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


TOKOIN = {"Lycée de Tokoin I", "Lycée Tokoin I"}


# Doublons probables ---------------------------------------------------------------------------------------------


def test_un_doublon_cree_est_propose_avec_sa_raison(national: TestClient) -> None:
    creer(national, "Lycée Tokoin I")

    page = national.get(DOUBLONS, params={"dre": "grand-lome"}).json()

    (paire,) = [p for p in page["paires"] if {p["a"]["nom"], p["b"]["nom"]} == TOKOIN]
    assert paire["raison"] == "meme_nom"
    assert paire["ecartee"] is False
    assert paire["a"]["id"] < paire["b"]["id"]
    assert {"nb_eleves", "nb_encadreurs", "club", "iesg", "prefecture"} <= paire["a"].keys()
    assert page["par_dre"]["grand-lome"] >= 1
    assert all(p["a"]["dre_code"] == "grand-lome" for p in page["paires"])


def test_un_collaborateur_de_dre_ne_voit_que_sa_dre(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    connecter(client, creer_collaborateur, "national", CLUBS, None)
    creer(client, "Lycée Tokoin I")
    connecter(client, creer_collaborateur, "kara", LECTURE, "kara")

    page = client.get(DOUBLONS).json()

    assert TOKOIN not in noms(page["paires"])
    assert all(p["a"]["dre_code"] == p["b"]["dre_code"] == "kara" for p in page["paires"])
    assert set(page["par_dre"]) <= {"kara"}


def test_ecarter_puis_retablir_une_paire(national: TestClient, en_base: Callable[..., Any]) -> None:
    creer(national, "Lycée Tokoin I")
    (paire,) = [p for p in paires(national) if {p["a"]["nom"], p["b"]["nom"]} == TOKOIN]
    corps = {"a_id": paire["b"]["id"], "b_id": paire["a"]["id"]}

    assert national.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 204
    assert TOKOIN not in noms(paires(national))
    assert noms(paires(national, ecartees=True)) == [TOKOIN]
    assert paires(national, ecartees=True)[0]["ecartee"] is True
    assert national.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 409

    assert national.post(f"{DOUBLONS}/retablir", json=corps).status_code == 204
    assert TOKOIN in noms(paires(national))
    assert national.post(f"{DOUBLONS}/retablir", json=corps).status_code == 404
    (ecart,) = journal(en_base, "doublon_ecarte")
    assert {ecart.details["a_nom"], ecart.details["b_nom"]} == TOKOIN
    assert len(journal(en_base, "doublon_retabli")) == 1


def test_un_etablissement_inactif_nest_plus_propose(national: TestClient) -> None:
    cree = creer(national, "Lycée Tokoin I")

    national.patch(f"{ETABLISSEMENTS}/{cree['id']}", json={"version": cree["version"], "statut": "inactif"})

    assert TOKOIN not in noms(paires(national))


def test_les_ecarts_sont_reserves_au_droit_de_modifier_et_au_perimetre(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    connecter(client, creer_collaborateur, "national", CLUBS, None)
    cree = creer(client, "Lycée Tokoin I")
    corps = {"a_id": cree["id"], "b_id": etablissement(client, "Lycée de Tokoin I")["id"]}

    assert client.post(f"{DOUBLONS}/ecarter", json={"a_id": cree["id"], "b_id": cree["id"]}).status_code == 422
    connecter(client, creer_collaborateur, "lecteur", LECTURE, None)
    assert client.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 403
    connecter(client, creer_collaborateur, "kara", CLUBS, "kara")
    assert client.post(f"{DOUBLONS}/ecarter", json=corps).status_code == 403


# Fusion ---------------------------------------------------------------------------------------------------------

GARDE = "Lycée de Tokoin I"
ABSORBE = "Lycée Tokoin I"


def fusionner(client: TestClient, garde: str, absorbe: str, nom: str = "garde") -> Any:
    g, a = etablissement(client, garde), etablissement(client, absorbe)
    return client.post(
        f"{ETABLISSEMENTS}/{g['id']}/fusionner",
        json={"absorbe_id": a["id"], "version_garde": g["version"], "version_absorbe": a["version"], "nom": nom},
    )


def apercu(client: TestClient, garde: str, absorbe: str) -> dict[str, Any]:
    g, a = etablissement(client, garde), etablissement(client, absorbe)
    reponse = client.get(f"{ETABLISSEMENTS}/{g['id']}/fusion/{a['id']}")
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


@pytest.fixture
def paire(national: TestClient) -> tuple[UUID, UUID]:
    absorbe = creer(national, ABSORBE, prefecture="Golfe", ordre="public")
    return UUID(etablissement(national, GARDE)["id"]), UUID(absorbe["id"])


def clubs_de(en_base: Callable[..., Any], etablissement_id: UUID) -> list[Club]:
    return en_base(
        lambda db: db.scalars(select(Club).where(Club.etablissement_id == etablissement_id).order_by(Club.cree_le))
    ).all()


def vivant(en_base: Callable[..., Any], etablissement_id: UUID) -> Club | None:
    return next((c for c in clubs_de(en_base, etablissement_id) if c.etat in CLUB_VIVANT), None)


def adhesions(en_base: Callable[..., Any], club_id: UUID) -> list[Adhesion]:
    return en_base(lambda db: db.scalars(select(Adhesion).where(Adhesion.club_id == club_id))).all()


def club_actif(en_base: Callable[..., Any], etablissement_id: UUID) -> UUID:
    effectif = peupler(en_base, etablissement_id, 3, 21)
    assert recalculer(en_base, effectif.club_id) is EtatClub.actif
    return effectif.club_id


def test_sans_club_les_eleves_et_encadreurs_rejoignent_le_garde(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    encadreur = ajouter_encadreur(en_base, absorbe, rattache=False)

    reponse = fusionner(national, GARDE, ABSORBE)

    assert reponse.status_code == 200, reponse.text
    assert (reponse.json()["id"], reponse.json()["nb_encadreurs"]) == (str(garde), 1)
    deplace = en_base(lambda db: db.get(Encadreur, encadreur))
    assert (deplace.etablissement_id, deplace.version) == (garde, 2)
    assert clubs_de(en_base, garde) == clubs_de(en_base, absorbe) == []


def test_le_club_en_constitution_de_labsorbe_rejoint_le_garde_sans_club(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    eleves = ajouter_eleves(en_base, absorbe, 2)
    ancien = vivant(en_base, absorbe)

    assert fusionner(national, GARDE, ABSORBE).status_code == 200

    assert vivant(en_base, absorbe) is None
    assert en_base(lambda db: db.get(Club, ancien.id)).etat is EtatClub.refuse
    nouveau = vivant(en_base, garde)
    assert sorted(a.eleve_id for a in adhesions(en_base, nouveau.id)) == sorted(eleves)
    for eleve in eleves:
        assert en_base(lambda db, e=eleve: db.get(Eleve, e)).etablissement_id == garde


def test_deux_clubs_en_constitution_se_reunissent_dans_celui_du_garde(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    ajouter_eleves(en_base, garde, 2)
    ajouter_eleves(en_base, absorbe, 3)
    club_garde = vivant(en_base, garde)

    assert fusionner(national, GARDE, ABSORBE).status_code == 200

    assert vivant(en_base, garde).id == club_garde.id
    assert len(adhesions(en_base, club_garde.id)) == 5


def test_le_club_en_constitution_rejoint_le_club_actif_du_garde(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    club_garde = club_actif(en_base, garde)
    ajouter_eleves(en_base, absorbe, 2)

    assert fusionner(national, GARDE, ABSORBE).status_code == 200

    restant = vivant(en_base, garde)
    assert (restant.id, restant.etat) == (club_garde, EtatClub.actif)
    assert len(adhesions(en_base, club_garde)) == 23


def test_le_club_actif_de_labsorbe_suit_tel_quel_le_garde_sans_club(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    club = club_actif(en_base, absorbe)

    reponse = fusionner(national, GARDE, ABSORBE)

    assert reponse.status_code == 200, reponse.text
    suivi = en_base(lambda db: db.get(Club, club))
    assert (suivi.etablissement_id, suivi.etat) == (garde, EtatClub.actif)
    assert len(adhesions(en_base, club)) == 21


def test_le_club_actif_de_labsorbe_recueille_le_club_en_constitution_du_garde(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    ajouter_eleves(en_base, garde, 2)
    en_constitution = vivant(en_base, garde)
    club = club_actif(en_base, absorbe)

    assert fusionner(national, GARDE, ABSORBE).status_code == 200

    assert vivant(en_base, garde).id == club
    assert en_base(lambda db: db.get(Club, en_constitution.id)).etat is EtatClub.refuse
    assert len(adhesions(en_base, club)) == 23


def test_deux_vrais_clubs_ne_se_fusionnent_pas(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    club_actif(en_base, garde)
    club = club_actif(en_base, absorbe)

    reponse = fusionner(national, GARDE, ABSORBE)

    assert reponse.status_code == 409
    assert "deux clubs" in reponse.json()["detail"]
    assert en_base(lambda db: db.get(Club, club)).etablissement_id == absorbe
    assert etablissement(national, ABSORBE)["statut"] == "actif"
    assert apercu(national, GARDE, ABSORBE)["refus"] == reponse.json()["detail"]


def test_la_fusion_reprend_le_nom_choisi_et_complete_prefecture_et_ordre(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    garde, absorbe = paire
    eleves = ajouter_eleves(en_base, absorbe, 1)

    reponse = fusionner(national, GARDE, ABSORBE, nom="absorbe")

    assert reponse.status_code == 200, reponse.text
    fiche = reponse.json()
    assert (fiche["nom"], fiche["prefecture"], fiche["ordre"]) == (ABSORBE, "Golfe", "public")
    page = national.get(ETABLISSEMENTS, params={"recherche": "Tokoin I", "statut": "inactif"}).json()
    (ancien,) = [e for e in page["etablissements"] if e["id"] == str(absorbe)]
    assert ancien["fusionne_dans"] == {"id": str(garde), "nom": ABSORBE}
    (entree,) = journal(en_base, "etablissement_fusionne")
    assert entree.cible_id == str(absorbe)
    assert entree.details["eleves"] == [str(e) for e in eleves]
    assert entree.details["apres"]["nom"] == ABSORBE
    assert "Test" not in str(entree.details)


def test_lapercu_annonce_leffet_sans_rien_ecrire(
    national: TestClient, paire: tuple[UUID, UUID], en_base: Callable[..., Any]
) -> None:
    _, absorbe = paire
    ajouter_eleves(en_base, absorbe, 2)

    vu = apercu(national, GARDE, ABSORBE)

    assert vu["refus"] is None
    assert (vu["garde"]["nom"], vu["absorbe"]["nom"], vu["absorbe"]["nb_eleves"]) == (GARDE, ABSORBE, 2)
    assert "2 élèves" in vu["effet"]
    assert etablissement(national, ABSORBE)["statut"] == "actif"
    assert journal(en_base, "etablissement_fusionne") == []


def test_labsorbe_disparait_des_listes_publiques(national: TestClient, paire: tuple[UUID, UUID]) -> None:
    assert fusionner(national, GARDE, ABSORBE).status_code == 200

    national.cookies.clear()
    trouves = national.get("/api/referentiel/etablissements", params={"recherche": "Tokoin I"}).json()
    assert ABSORBE not in [e["nom"] for e in trouves]
    assert GARDE in [e["nom"] for e in trouves]


def test_les_fusions_impossibles_sont_refusees(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    connecter(client, creer_collaborateur, "national", CLUBS, None)
    absorbe = creer(client, ABSORBE)
    garde = etablissement(client, GARDE)
    kara = etablissement(client, "Lycée Kara 1")

    def envoyer(g: dict[str, Any], a: dict[str, Any], **autres: Any) -> int:
        corps = {"absorbe_id": a["id"], "version_garde": g["version"], "version_absorbe": a["version"], "nom": "garde"}
        return client.post(f"{ETABLISSEMENTS}/{g['id']}/fusionner", json=corps | autres).status_code

    assert envoyer(garde, garde) == 422
    assert envoyer(garde, kara) == 422
    assert envoyer(garde, absorbe, version_absorbe=absorbe["version"] + 1) == 409
    inactif = client.patch(f"{ETABLISSEMENTS}/{absorbe['id']}", json={"version": 1, "statut": "inactif"}).json()
    assert envoyer(inactif, garde) == 422
    connecter(client, creer_collaborateur, "lecteur", LECTURE, None)
    assert envoyer(garde, inactif) == 403
    connecter(client, creer_collaborateur, "kara", CLUBS, "kara")
    assert envoyer(garde, inactif) == 403
    assert journal(en_base, "etablissement_fusionne") == []


def test_le_nom_final_deja_pris_dans_lieesg_du_garde_est_refuse(national: TestClient) -> None:
    # « Lycée de Tokoin II » existe déjà sous l'IESG Golfe : le gardé, sous Golfe, ne peut pas prendre ce nom.
    creer(national, "Lycée de Tokoin II", "IESG Agoényivé")
    garde = etablissement(national, GARDE)
    absorbe = next(
        e
        for e in national.get(ETABLISSEMENTS, params={"recherche": "Tokoin II"}).json()["etablissements"]
        if e["iesg"] == "IESG Agoényivé"
    )

    reponse = national.post(
        f"{ETABLISSEMENTS}/{garde['id']}/fusionner",
        json={"absorbe_id": absorbe["id"], "version_garde": garde["version"], "version_absorbe": absorbe["version"],
              "nom": "absorbe"},
    )  # fmt: skip

    assert reponse.status_code == 409
    assert "Lycée de Tokoin II" in reponse.json()["detail"]
    assert etablissement(national, GARDE)["statut"] == "actif"


def test_une_proposition_se_fusionne_comme_avant_le_remplacement(
    national: TestClient, en_base: Callable[..., Any]
) -> None:
    from app.referentiel.models import Etablissement, StatutEtablissement

    absorbe = creer(national, ABSORBE)
    en_base(
        lambda db: db.execute(
            update(Etablissement)
            .where(Etablissement.id == UUID(absorbe["id"]))
            .values(statut=StatutEtablissement.propose)
        )
    )
    ajouter_eleves(en_base, UUID(absorbe["id"]), 1)

    reponse = fusionner(national, GARDE, ABSORBE)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["nb_eleves"] == 1
