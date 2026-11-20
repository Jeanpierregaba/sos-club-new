"""Temps passés sur les quiz et la certification d'un inscrit (spec 046)."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import uuid7

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification.models import BadgeObtenu, Certificat, EtatCertificat, PlaceReussie
from app.quiz.models import EtatQuiz, EtatTentative, QuestionQuiz, Quiz, ReponseQuiz, TentativeQuiz
from tests.certification import creer_parcours
from tests.conftest import connecter_admin
from tests.quiz import DEBUT, creer_quiz
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


# Détail d'une tentative ---------------------------------------------------------------------------------------


def repondre(
    en_base: Callable[..., Any], essai: TentativeQuiz, quiz: Quiz,
    lignes: list[tuple[float | None, float | None, int | None, bool | None]],
) -> None:  # fmt: skip
    """Des réponses à la tentative : (envoi, réponse) en secondes après DEBUT, choix et justesse, par rang."""

    async def inserer(db: AsyncSession) -> None:
        questions = (
            await db.scalars(select(QuestionQuiz).where(QuestionQuiz.quiz_id == quiz.id).order_by(QuestionQuiz.ordre))
        ).all()
        for rang, (envoi, reponse, choix, correcte) in enumerate(lignes, start=1):
            db.add(
                ReponseQuiz(
                    tentative_id=essai.id, rang=rang, question_id=questions[rang - 1].id, ordre_choix=[0, 1, 2],
                    envoyee_le=DEBUT + timedelta(seconds=envoi) if envoi is not None else None,
                    repondue_le=DEBUT + timedelta(seconds=reponse) if reponse is not None else None,
                    choix=choix, correcte=correcte,
                )
            )  # fmt: skip

    en_base(inserer)


def test_le_detail_dune_tentative_question_par_question(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, questions=5, niveau="debutant", numero=1)
    essai = tentative(en_base, eleve.id, quiz, reussie=False, score=1, duree=60)
    repondre(
        en_base, essai, quiz,
        [(0, 4.24, 0, True), (5, 12, 1, False), (13, None, None, False), (40, 70, None, False), (None, None, None, None)],
    )  # fmt: skip

    reponse = lecteur.get(f"{INSCRITS}/{eleve.id}/tentatives/{essai.id}")

    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["cache-control"] == "no-store"
    donnees = reponse.json()
    assert donnees["tentative"]["id"] == str(essai.id)
    imparti = donnees["temps_imparti_s"]
    assert imparti > 0
    assert [(q["rang"], q["etat"], q["reponse"], q["secondes"]) for q in donnees["questions"]] == [
        (1, "juste", "Juste 1", 4.2),
        (2, "fausse", "Faux A 2", 7.0),
        (3, "temps_ecoule", None, imparti),
        (4, "temps_ecoule", None, imparti),
        (5, "non_posee", None, None),
    ]
    assert donnees["questions"][0]["enonce"] == "Question 1 ?"
    # La bonne réponse d'une question non répondue ne sort jamais.
    assert "Juste 3" not in reponse.text
    assert "bonne_reponse" not in reponse.text


def test_une_question_affichee_en_cours_de_partie(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, questions=2, niveau="debutant", numero=1)
    essai = tentative(en_base, eleve.id, quiz, reussie=None, etat=EtatTentative.en_cours)
    repondre(en_base, essai, quiz, [(0, 3, 0, True), (5, None, None, None)])

    questions = lecteur.get(f"{INSCRITS}/{eleve.id}/tentatives/{essai.id}").json()["questions"]

    assert [q["etat"] for q in questions] == ["juste", "en_cours"]


def test_la_tentative_dun_autre_joueur_est_introuvable(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    autre = creer_eleve("eleve2", affiche="Autre Pseudo")
    quiz = creer_quiz(en_base, niveau="debutant", numero=1)
    essai = tentative(en_base, autre.id, quiz, reussie=True)

    assert lecteur.get(f"{INSCRITS}/{eleve.id}/tentatives/{essai.id}").status_code == 404
    assert lecteur.get(f"{INSCRITS}/{eleve.id}/tentatives/{uuid7()}").status_code == 404
    assert lecteur.get(f"{INSCRITS}/{autre.id}/tentatives/{essai.id}").status_code == 200


@pytest.mark.parametrize(("droits", "dre"), [({("tableau_de_bord", "consulter")}, None), (LECTURE, "grand-lome")])
def test_le_detail_exige_le_droit_national(
    client: TestClient, creer_collaborateur: Callable[..., Any], creer_eleve: Callable[..., Any],
    en_base: Callable[..., Any], droits: set[tuple[str, str]], dre: str | None,
) -> None:  # fmt: skip
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, niveau="debutant", numero=1)
    essai = tentative(en_base, eleve.id, quiz, reussie=True)
    creer_collaborateur("sans", droits=droits, perimetre_dre=dre, double_auth=True)
    connecter_admin(client, "sans")

    assert client.get(f"{INSCRITS}/{eleve.id}/tentatives/{essai.id}").status_code == 403


# Certification ------------------------------------------------------------------------------------------------


def reussir(en_base: Callable[..., Any], joueur_id: Any, place: int, essai: TentativeQuiz) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(
            PlaceReussie(
                utilisateur_id=joueur_id, place=place, quiz_id=essai.quiz_id, tentative_id=essai.id,
                reussie_le=essai.terminee_le,
            )
        )  # fmt: skip

    en_base(inserer)


def test_les_temps_des_places_des_badges_et_du_certificat(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    parcours = creer_parcours(en_base, places=[1, 2, 3])
    ancien = creer_quiz(en_base, titre="Place 2 retirée", place=2, etat=EtatQuiz.depublie)
    # Place 1 : un échec puis la réussite comptent, pas la partie rejouée après ni l'essai de l'équipe.
    tentative(en_base, eleve.id, parcours[1], reussie=False, duree=30, decalage=0)
    reussie = tentative(en_base, eleve.id, parcours[1], reussie=True, duree=40, decalage=10)
    reussir(en_base, eleve.id, 1, reussie)
    tentative(en_base, eleve.id, parcours[1], reussie=True, duree=50, decalage=20)
    tentative(en_base, eleve.id, parcours[1], reussie=True, duree=999, decalage=21, essai=True)
    # Place 2 : les tentatives sur le quiz qui l'occupait avant comptent aussi. Pas encore réussie.
    tentative(en_base, eleve.id, ancien, reussie=False, duree=20, decalage=30)
    tentative(en_base, eleve.id, parcours[2], reussie=False, duree=5, decalage=35)
    # Les jeux n'entrent pas dans la certification.
    tentative(en_base, eleve.id, creer_quiz(en_base, niveau="debutant", numero=1), reussie=True, duree=500)

    async def decerner(db: AsyncSession) -> None:
        for rang, minutes in ((1, 15), (2, 60)):
            db.add(
                BadgeObtenu(
                    utilisateur_id=eleve.id, rang=rang, nom=f"Badge {rang}", palier=rang, regles_version=1,
                    obtenu_le=DEBUT + timedelta(minutes=minutes),
                )
            )  # fmt: skip
        db.add(
            Certificat(
                numero="GI-AAAA-BBBB-CCCC", utilisateur_id=eleve.id, role="eleve", titulaire_prenom="Jean",
                titulaire_nom="Kodjo", etat=EtatCertificat.valide, delivre_le=DEBUT + timedelta(minutes=60),
            )
        )  # fmt: skip

    en_base(decerner)

    donnees = lecteur.get(f"{INSCRITS}/{eleve.id}/certification").json()

    places = {p["place"]: (p["temps_s"], p["tentatives"]) for p in donnees["places"]}
    assert places[1] == (70, 2)
    assert places[2] == (25, 2)
    assert places[3] == (0, 0)
    badges = [(b["rang"], b["temps_s"], b["temps_cumule_s"], b["duree_calendaire_s"]) for b in donnees["badges"]]
    # Badge 1 : 30 + 40 s avant la 15e minute ; badge 2 : 50 + 20 + 5 s ensuite. Le premier part de la première
    # tentative de certification, le second du badge précédent.
    assert badges == [(1, 70, 70, 15 * 60), (2, 75, 145, 45 * 60)]
    (certificat,) = donnees["certificats"]
    assert (certificat["temps_cumule_s"], certificat["duree_calendaire_s"]) == (145, 3600)


def test_un_badge_sans_tentative_retrouvee(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()

    async def decerner(db: AsyncSession) -> None:
        db.add(BadgeObtenu(utilisateur_id=eleve.id, rang=1, nom="Ancien", palier=3, regles_version=1, obtenu_le=DEBUT))

    en_base(decerner)

    donnees = lecteur.get(f"{INSCRITS}/{eleve.id}/certification").json()

    (badge,) = donnees["badges"]
    assert (badge["temps_s"], badge["temps_cumule_s"], badge["duree_calendaire_s"]) == (0, 0, None)
    assert all((p["temps_s"], p["tentatives"]) == (0, 0) for p in donnees["places"])
