"""Administration des points (spec 017) : semestres, barème, droits et journal."""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from app.points.models import Semestre
from app.points.service import aujourd_hui
from tests.conftest import connecter_admin

SEMESTRES = "/api/admin/points/semestres"
BAREME = "/api/admin/points/bareme"
LECTEUR = {("tableau_de_bord", "consulter"), ("points", "consulter")}
GESTIONNAIRE = LECTEUR | {("points", "modifier")}
JOUR = aujourd_hui()


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("points", droits=GESTIONNAIRE, double_auth=True)
    connecter_admin(client, "points")
    return client


@pytest.fixture
def lecteur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("lecteur", droits=LECTEUR)
    connecter_admin(client, "lecteur")
    return client


def semestre(libelle: str, debut: date, fin: date) -> dict[str, str]:
    return {"libelle": libelle, "debut": debut.isoformat(), "fin": fin.isoformat()}


def inserer_semestre(en_base: Callable[..., Any], libelle: str, debut: date, fin: date) -> Semestre:
    async def inserer(db: Any) -> Semestre:
        element = Semestre(libelle=libelle, debut=debut, fin=fin)
        db.add(element)
        return element

    return en_base(inserer)


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


def ligne(client: TestClient, code: str) -> dict[str, Any]:
    return next(element for element in client.get(BAREME).json() if element["code"] == code)


# Droits -------------------------------------------------------------------------------------------------------


def test_consulter_exige_le_droit_points(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})
    connecter_admin(client, "autre")

    assert client.get(SEMESTRES).status_code == 403
    assert client.get(BAREME).status_code == 403


def test_un_lecteur_voit_mais_ne_modifie_pas(lecteur: TestClient) -> None:
    assert lecteur.get(SEMESTRES).status_code == 200
    bienvenue = ligne(lecteur, "eleve.bienvenue")

    reponse = lecteur.patch(f"{BAREME}/eleve.bienvenue", json={"version": bienvenue["version"], "montant": 200})

    assert reponse.status_code == 403
    assert lecteur.post(SEMESTRES, json=semestre("S1", JOUR, JOUR + timedelta(days=90))).status_code == 403


def test_modifier_exige_la_double_authentification(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur("sans2fa", droits=GESTIONNAIRE)
    connecter_admin(client, "sans2fa")

    assert client.get(BAREME).status_code == 403


def test_un_responsable_de_dre_ne_change_pas_le_bareme(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("kara", droits=GESTIONNAIRE, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "kara")
    bienvenue = ligne(client, "eleve.bienvenue")

    reponse = client.patch(f"{BAREME}/eleve.bienvenue", json={"version": bienvenue["version"], "montant": 200})

    assert reponse.status_code == 403


# Semestres ----------------------------------------------------------------------------------------------------


def test_creer_un_semestre_et_le_voir_en_cours(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = gestionnaire.post(SEMESTRES, json=semestre("2026-2027, semestre 1", JOUR, JOUR + timedelta(days=90)))

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["etat"] == "en_cours"
    assert [s["libelle"] for s in gestionnaire.get(SEMESTRES).json()] == ["2026-2027, semestre 1"]
    (entree,) = journal(en_base, "semestre_cree")
    assert entree.details["apres"]["debut"] == JOUR.isoformat()
    assert gestionnaire.get("/api/admin/tableau-de-bord").json()["semestre_en_cours"] == "2026-2027, semestre 1"


def test_sans_semestre_le_tableau_de_bord_le_signale(gestionnaire: TestClient) -> None:
    assert gestionnaire.get("/api/admin/tableau-de-bord").json()["semestre_en_cours"] is None


@pytest.mark.parametrize(
    ("debut", "fin", "statut"),
    [
        (JOUR + timedelta(days=10), JOUR + timedelta(days=5), 422),  # fin avant début
        (JOUR - timedelta(days=1), JOUR + timedelta(days=90), 422),  # commence dans le passé
    ],
)
def test_dates_invalides_refusees(gestionnaire: TestClient, debut: date, fin: date, statut: int) -> None:
    assert gestionnaire.post(SEMESTRES, json=semestre("S", debut, fin)).status_code == statut


def test_un_semestre_qui_chevauche_est_refuse(gestionnaire: TestClient) -> None:
    gestionnaire.post(SEMESTRES, json=semestre("Premier", JOUR, JOUR + timedelta(days=90)))

    reponse = gestionnaire.post(
        SEMESTRES, json=semestre("Second", JOUR + timedelta(days=90), JOUR + timedelta(days=180))
    )

    assert reponse.status_code == 409
    assert "Premier" in reponse.json()["detail"]


def test_un_libelle_deja_pris_est_refuse(gestionnaire: TestClient) -> None:
    gestionnaire.post(SEMESTRES, json=semestre("S1", JOUR, JOUR + timedelta(days=10)))

    reponse = gestionnaire.post(SEMESTRES, json=semestre("S1", JOUR + timedelta(days=20), JOUR + timedelta(days=30)))

    assert reponse.status_code == 409


def test_un_semestre_en_cours_se_prolonge_mais_ne_se_raccourcit_pas(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    en_cours = inserer_semestre(en_base, "En cours", JOUR - timedelta(days=30), JOUR + timedelta(days=30))
    url = f"{SEMESTRES}/{en_cours.id}"

    raccourci = gestionnaire.patch(url, json={"version": 1, "fin": (JOUR + timedelta(days=10)).isoformat()})
    debut_change = gestionnaire.patch(url, json={"version": 1, "debut": JOUR.isoformat()})
    prolonge = gestionnaire.patch(url, json={"version": 1, "fin": (JOUR + timedelta(days=60)).isoformat()})

    assert (raccourci.status_code, debut_change.status_code) == (409, 409)
    assert prolonge.status_code == 200, prolonge.text
    (entree,) = journal(en_base, "semestre_modifie")
    assert entree.details["avant"]["fin"] == (JOUR + timedelta(days=30)).isoformat()


def test_un_semestre_termine_est_fige(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    termine = inserer_semestre(en_base, "Passé", JOUR - timedelta(days=60), JOUR - timedelta(days=30))

    reponse = gestionnaire.patch(
        f"{SEMESTRES}/{termine.id}", json={"version": 1, "fin": (JOUR + timedelta(days=10)).isoformat()}
    )
    renomme = gestionnaire.patch(f"{SEMESTRES}/{termine.id}", json={"version": 1, "libelle": "2025-2026, S2"})

    assert reponse.status_code == 409
    assert renomme.status_code == 200, renomme.text


def test_un_semestre_a_venir_se_modifie_librement(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    a_venir = inserer_semestre(en_base, "Bientôt", JOUR + timedelta(days=30), JOUR + timedelta(days=60))
    url = f"{SEMESTRES}/{a_venir.id}"

    reponse = gestionnaire.patch(url, json={"version": 1, "debut": (JOUR + timedelta(days=1)).isoformat()})
    dans_le_passe = gestionnaire.patch(url, json={"version": 2, "debut": (JOUR - timedelta(days=1)).isoformat()})
    perime = gestionnaire.patch(url, json={"version": 1, "libelle": "Autre"})

    assert reponse.status_code == 200, reponse.text
    assert dans_le_passe.status_code == 422
    assert perime.status_code == 409


def test_prolonger_ne_peut_pas_chevaucher_le_suivant(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    en_cours = inserer_semestre(en_base, "En cours", JOUR - timedelta(days=10), JOUR + timedelta(days=10))
    inserer_semestre(en_base, "Suivant", JOUR + timedelta(days=20), JOUR + timedelta(days=60))

    reponse = gestionnaire.patch(
        f"{SEMESTRES}/{en_cours.id}", json={"version": 1, "fin": (JOUR + timedelta(days=30)).isoformat()}
    )

    assert reponse.status_code == 409
    assert "Suivant" in reponse.json()["detail"]


# Barème -------------------------------------------------------------------------------------------------------


def test_le_bareme_affiche_toute_la_grille_sans_la_correction_manuelle(lecteur: TestClient) -> None:
    grille = lecteur.get(BAREME).json()

    assert len(grille) == 46
    assert all(element["code"] != "admin.correction" for element in grille)
    bienvenue = ligne(lecteur, "eleve.bienvenue")
    assert (bienvenue["montant"], bienvenue["en_service"], bienvenue["propose"]) == (100, True, False)
    assert ligne(lecteur, "encadreur.sujet_forum")["propose"] is True


def test_la_correction_manuelle_ne_se_modifie_pas(gestionnaire: TestClient) -> None:
    reponse = gestionnaire.patch(f"{BAREME}/admin.correction", json={"version": 1, "montant": 100, "propose": False})

    assert reponse.status_code == 422
    assert "technique" in reponse.json()["detail"]


def test_modifier_un_montant_est_journalise(gestionnaire: TestClient, en_base: Callable[..., Any]) -> None:
    bienvenue = ligne(gestionnaire, "eleve.bienvenue")

    reponse = gestionnaire.patch(
        f"{BAREME}/eleve.bienvenue", json={"version": bienvenue["version"], "montant": 120, "propose": False}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["montant"] == 120
    (entree,) = journal(en_base, "bareme_modifie")
    assert entree.details == {"avant": {"montant": 100}, "apres": {"montant": 120}}
    assert entree.cible_id == "eleve.bienvenue"


@pytest.mark.parametrize("montant", [-1, 10_001])
def test_un_montant_hors_bornes_est_refuse(gestionnaire: TestClient, montant: int) -> None:
    bienvenue = ligne(gestionnaire, "eleve.bienvenue")

    reponse = gestionnaire.patch(
        f"{BAREME}/eleve.bienvenue", json={"version": bienvenue["version"], "montant": montant}
    )

    assert reponse.status_code == 422


def test_une_version_perimee_est_refusee(gestionnaire: TestClient) -> None:
    bienvenue = ligne(gestionnaire, "eleve.bienvenue")
    gestionnaire.patch(f"{BAREME}/eleve.bienvenue", json={"version": bienvenue["version"], "montant": 110})

    reponse = gestionnaire.patch(f"{BAREME}/eleve.bienvenue", json={"version": bienvenue["version"], "actif": False})

    assert reponse.status_code == 409


def test_une_action_inconnue_repond_404(gestionnaire: TestClient) -> None:
    assert gestionnaire.patch(f"{BAREME}/eleve.inconnue", json={"version": 1, "montant": 5}).status_code == 404


def test_aucune_route_ne_supprime(gestionnaire: TestClient) -> None:
    assert gestionnaire.delete(f"{BAREME}/eleve.bienvenue").status_code == 405
