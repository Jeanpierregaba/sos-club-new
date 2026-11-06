"""« Quel axe est fait pour toi ? » (spec 021, tâche 1) : table de correspondance, départages, accès élève."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.comptes.models import Utilisateur
from app.jeux.quel_axe import QUESTIONS, calculer
from app.points.models import MouvementPoints
from tests.conftest import MOT_DE_PASSE, connecter_admin

QUESTIONNAIRE = "/api/jeux/quel-axe"
RESULTAT = "/api/jeux/quel-axe/resultat"

# La table du document fonctionnel, recopiée à la main : (question, réponse) → (axe +3, axe +1).
TABLE = {
    (1, "A"): ("TV", "LM"),
    (1, "B"): ("SS", "SE"),
    (1, "C"): ("LM", "EVSS"),
    (1, "D"): ("GI", "GB"),
    (2, "A"): ("EVSS", "TV"),
    (2, "B"): ("SE", "EVSS"),
    (2, "C"): ("GB", "GI"),
    (2, "D"): ("SS", "LM"),
    (3, "A"): ("TV", "GB"),
    (3, "B"): ("LM", "SS"),
    (3, "C"): ("GI", "GB"),
    (3, "D"): ("EVSS", "SE"),
    (4, "A"): ("GI", "SE"),
    (4, "B"): ("SE", "EVSS"),
    (4, "C"): ("GB", "SS"),
    (4, "D"): ("EVSS", "TV"),
    (5, "A"): ("SS", "SE"),
    (5, "B"): ("TV", "LM"),
    (5, "C"): ("LM", "EVSS"),
    (5, "D"): ("GB", "GI"),
}


def test_les_20_reponses_suivent_la_table_du_document() -> None:
    code = {
        (numero, r.lettre): (r.principal, r.secondaire)
        for numero, question in enumerate(QUESTIONS, start=1)
        for r in question.reponses
    }
    assert code == TABLE


def test_lexemple_du_document() -> None:
    resultat = calculer(["A", "A", "A", "D", "B"])

    assert (resultat.principal, resultat.autres) == ("TV", ("EVSS", "LM"))
    assert (resultat.scores["TV"], resultat.scores["EVSS"], resultat.scores["LM"]) == (11, 6, 2)


def test_a_egalite_laxe_le_plus_souvent_principal_passe_devant() -> None:
    # EVSS et SE ont 7 points ; SE a été deux fois axe principal, EVSS une fois.
    resultat = calculer(["C", "B", "D", "B", "C"])

    assert resultat.scores["EVSS"] == resultat.scores["SE"] == 7
    assert resultat.principal == "SE"


def test_puis_laxe_principal_de_la_question_1_sil_est_ex_aequo() -> None:
    # GI, TV et LM : 4 points et une fois principal chacun ; la question 1 désignait TV.
    resultat = calculer(["A", "A", "B", "A", "D"])

    assert resultat.principal == "TV"
    assert resultat.autres == ("GI", "LM")


def test_enfin_lordre_officiel_des_axes() -> None:
    # EVSS et LM : 7 points, deux fois principal ; la question 1 désignait TV, qui n'est pas ex æquo.
    resultat = calculer(["A", "A", "B", "D", "C"])

    assert (resultat.principal, resultat.autres) == ("EVSS", ("LM", "TV"))


def test_un_eleve_actif_recoit_les_questions_sans_les_axes(
    client: TestClient, creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve("ama", "Ama")
    client.post("/api/comptes/connexion", json={"identifiant": "ama", "mot_de_passe": MOT_DE_PASSE})

    corps = client.get(QUESTIONNAIRE).json()

    assert [q["numero"] for q in corps["questions"]] == [1, 2, 3, 4, 5]
    premiere = corps["questions"][0]["reponses"][0]
    assert premiere == {"id": "A", "libelle": "Réaliser une vidéo ou interviewer des élèves."}


def test_le_resultat_est_calcule_par_lapi_sans_point(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_eleve("ama", "Ama")
    client.post("/api/comptes/connexion", json={"identifiant": "ama", "mot_de_passe": MOT_DE_PASSE})
    avant = en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints)))

    reponse = client.post(RESULTAT, json={"reponses": ["A", "A", "A", "D", "B"]})

    assert reponse.status_code == 200
    assert reponse.json()["principal"] == "TV"
    assert reponse.json()["autres"] == ["EVSS", "LM"]
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints))) == avant


@pytest.mark.parametrize(
    "reponses", [["A", "A", "A", "D"], ["A", "A", "A", "D", "B", "C"], ["A", "A", "A", "D", "E"], []]
)
def test_des_reponses_incompletes_ou_invalides_sont_refusees(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], reponses: list[str]
) -> None:
    creer_eleve("ama", "Ama")
    client.post("/api/comptes/connexion", json={"identifiant": "ama", "mot_de_passe": MOT_DE_PASSE})

    assert client.post(RESULTAT, json={"reponses": reponses}).status_code == 422


def test_un_visiteur_doit_se_connecter(client: TestClient) -> None:
    assert client.get(QUESTIONNAIRE).status_code == 401
    assert client.post(RESULTAT, json={"reponses": ["A"] * 5}).status_code == 401


def test_un_encadreur_na_pas_acces(client: TestClient, creer_encadreur: Callable[..., Utilisateur]) -> None:
    creer_encadreur("prof")
    client.post("/api/comptes/connexion", json={"identifiant": "prof", "mot_de_passe": MOT_DE_PASSE})

    reponse = client.get(QUESTIONNAIRE)

    assert reponse.status_code == 403
    assert reponse.json()["detail"] == "Ce jeu est réservé aux élèves inscrits."
    assert client.post(RESULTAT, json={"reponses": ["A"] * 5}).status_code == 403


def test_un_collaborateur_na_pas_acces(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur("chef", super_admin=True, double_auth=True)
    connecter_admin(client, "chef")

    assert client.get(QUESTIONNAIRE).status_code == 403
