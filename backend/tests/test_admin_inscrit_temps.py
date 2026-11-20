"""Temps passés sur les quiz et la certification d'un inscrit (spec 046)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import connecter_admin
from tests.quiz import creer_quiz
from tests.test_admin_inscrit_parcours import INSCRITS, LECTURE, tentative

pytestmark = pytest.mark.usefixtures("annuaire")

TROIS_JOURS = 3 * 24 * 3600


@pytest.fixture
def lecteur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("lecteur", droits=LECTURE, double_auth=True)
    connecter_admin(client, "lecteur")
    return client


# Quiz ---------------------------------------------------------------------------------------------------------


def test_une_partie_abandonnee_compte_jusqua_sa_derniere_activite(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, titre="Hygiène", niveau="debutant", numero=1)
    tentative(en_base, eleve.id, quiz, reussie=False, duree=120, cloture=TROIS_JOURS)
    tentative(en_base, eleve.id, quiz, reussie=True, duree=60, decalage=10)

    donnees = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz").json()

    recente, abandonnee = donnees["tentatives"]["tentatives"]
    assert (abandonnee["duree_s"], abandonnee["abandonnee"]) == (120, True)
    assert (recente["duree_s"], recente["abandonnee"]) == (60, False)
    assert donnees["resume"]["temps_total_s"] == 180
    assert donnees["resume"]["temps_moyen_s"] == 90


def test_une_tentative_en_cours_compte_jusqua_maintenant_sa_derniere_activite(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.quiz.models import EtatTentative

    eleve = creer_eleve()
    quiz = creer_quiz(en_base, niveau="debutant", numero=1)
    tentative(en_base, eleve.id, quiz, reussie=None, duree=45, etat=EtatTentative.en_cours)

    donnees = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz").json()

    (en_cours,) = donnees["tentatives"]["tentatives"]
    assert (en_cours["duree_s"], en_cours["abandonnee"]) == (45, False)
    assert donnees["resume"]["temps_total_s"] == 0


def autres_joueurs(creer_eleve: Callable[..., Any], nombre: int) -> list[Any]:
    return [creer_eleve(f"autre{i}", affiche=f"Autre Pseudo {i}") for i in range(nombre)]


def test_la_moyenne_nationale_et_la_pastille_tres_rapide(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, titre="Hygiène", niveau="debutant", numero=1)
    for autre in autres_joueurs(creer_eleve, 5):
        tentative(en_base, autre.id, quiz, reussie=True, duree=100)
        # Ni les échecs, ni les essais des autres n'entrent dans la moyenne.
        tentative(en_base, autre.id, quiz, reussie=False, duree=5, decalage=1)
        tentative(en_base, autre.id, quiz, reussie=True, duree=5, decalage=2, essai=True)
    # La première réussite de l'inscrit compte, pas la suivante ; ses tentatives restent hors de la moyenne.
    tentative(en_base, eleve.id, quiz, reussie=True, duree=40, decalage=10)
    tentative(en_base, eleve.id, quiz, reussie=True, duree=500, decalage=20)

    (valide,) = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz").json()["valides"]

    assert valide["temps_premiere_reussite_s"] == 40
    assert valide["moyenne_nationale_s"] == 100
    assert valide["reussites_nationales"] == 5
    assert valide["tres_rapide"] is True


def test_sous_cinq_reussites_la_moyenne_nationale_est_absente(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, titre="Hygiène", niveau="debutant", numero=1)
    for autre in autres_joueurs(creer_eleve, 4):
        tentative(en_base, autre.id, quiz, reussie=True, duree=100)
    tentative(en_base, eleve.id, quiz, reussie=True, duree=10, decalage=10)

    (valide,) = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz").json()["valides"]

    assert valide["moyenne_nationale_s"] is None
    assert valide["reussites_nationales"] == 4
    assert valide["tres_rapide"] is False


def test_un_temps_proche_de_la_moyenne_nest_pas_tres_rapide(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, titre="Hygiène", niveau="debutant", numero=1)
    for autre in autres_joueurs(creer_eleve, 5):
        tentative(en_base, autre.id, quiz, reussie=True, duree=100)
    tentative(en_base, eleve.id, quiz, reussie=True, duree=50, decalage=10)

    (valide,) = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz").json()["valides"]

    assert valide["tres_rapide"] is False
