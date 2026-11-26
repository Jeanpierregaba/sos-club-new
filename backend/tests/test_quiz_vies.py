"""Les vies quotidiennes (spec 048, spec 049) : 3 par jour, communes aux jeux et à la certification ; seule une partie ratée en
coûte une ; une partie en cours en réserve une ; recharge à minuit."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Utilisateur
from app.quiz import parametres
from app.quiz.models import EtatTentative, Quiz, TentativeQuiz
from app.quiz.vies import VIES_PAR_JOUR
from tests.certification import creer_parcours
from tests.quiz import DEBUT, QUIZ, Horloge, connecter, creer_quiz, figer_horloge, jouer, lancer

MESSAGE = "Tu as utilisé tes 3 vies aujourd'hui. Reviens demain, elles se rechargent à minuit."


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama")
    connecter(client, "ama")
    return utilisateur


@pytest.fixture
def quiz(en_base: Callable[..., Any]) -> Quiz:
    return creer_quiz(en_base)


def vies(client: TestClient) -> dict[str, int]:
    reponse = client.get(f"{QUIZ}/vies")
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def rater(client: TestClient, quiz: Quiz, fois: int) -> None:
    for _ in range(fois):
        jouer(client, quiz, 0)


def test_un_joueur_commence_la_journee_avec_3_vies(client: TestClient, eleve: Utilisateur, heure: Horloge) -> None:
    assert VIES_PAR_JOUR == 3
    assert vies(client) == {"total": 3, "restantes": 3, "perdues": 0, "en_cours": 0}


def test_apres_3_parties_ratees_le_lancement_est_refuse(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    autre = creer_quiz(en_base, titre="Autre quiz")
    rater(client, quiz, 2)
    rater(client, autre, 1)

    reponse = client.post(f"{QUIZ}/{quiz.id}/tentatives")

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == MESSAGE
    assert vies(client)["restantes"] == 0
    # Tous les quiz sont concernés : les vies se comptent sur la journée.
    assert client.post(f"{QUIZ}/{creer_quiz(en_base, titre='Troisième').id}/tentatives").status_code == 409


def test_une_partie_reussie_ne_coute_aucune_vie(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    rater(client, quiz, 2)
    fin = jouer(client, quiz, 15)

    assert fin["resultat"]["reussie"] is True
    assert fin["vies_restantes"] == 1
    assert vies(client)["perdues"] == 2
    lancer(client, quiz)


def test_la_fin_de_partie_et_la_liste_donnent_les_vies_restantes(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    fin = jouer(client, quiz, 0)

    assert fin["vies_restantes"] == 2
    assert client.get(QUIZ).json()["vies"]["restantes"] == 2


def test_une_partie_en_cours_reserve_une_vie(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    rater(client, quiz, 2)
    lancer(client, quiz)

    assert vies(client) == {"total": 3, "restantes": 0, "perdues": 2, "en_cours": 1}
    autre = creer_quiz(en_base, titre="Autre quiz")
    assert client.post(f"{QUIZ}/{autre.id}/tentatives").status_code == 409


def test_une_partie_abandonnee_ratee_coute_une_vie(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    rater(client, quiz, 2)
    lancer(client, quiz)
    # Partie quittée : close au lancement suivant, sans réussite.
    heure.avancer(11 * 60)

    autre = creer_quiz(en_base, titre="Autre quiz")
    assert client.post(f"{QUIZ}/{autre.id}/tentatives").status_code == 409
    assert vies(client) == {"total": 3, "restantes": 0, "perdues": 3, "en_cours": 0}


def test_les_vies_se_rechargent_le_lendemain(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    rater(client, quiz, 3)
    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 409

    heure.avancer(24 * 3600)

    assert vies(client)["restantes"] == 3
    lancer(client, quiz)


def test_jeux_et_certification_partagent_les_memes_vies(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    parcours = creer_parcours(en_base, places=[1])
    rater(client, quiz, 2)
    fin = jouer(client, parcours[1], 0)

    assert fin["resultat"]["reussie"] is False
    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 409
    assert client.post(f"{QUIZ}/{parcours[1].id}/tentatives").status_code == 409
    assert client.get("/api/certification").json()["vies"]["restantes"] == 0


def test_un_encadreur_a_aussi_3_vies(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur], quiz: Quiz, heure: Horloge
) -> None:
    creer_encadreur("prof")
    connecter(client, "prof")
    rater(client, quiz, 3)

    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 409


# Cas limites relevés à la relecture ----------------------------------------------------------------------------


def test_recommencer_a_zero_vie_garde_la_partie_en_cours(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    rater(client, quiz, 2)
    en_cours = lancer(client, quiz)

    refus = client.post(f"{QUIZ}/{quiz.id}/tentatives")

    assert refus.status_code == 409
    # La clôture que tentait le lancement est annulée : la partie se reprend telle quelle.
    reprise = client.get(f"{QUIZ}/tentatives/{en_cours['tentative_id']}").json()
    assert reprise["question"] is not None
    assert vies(client)["en_cours"] == 1


def test_une_partie_lancee_avant_minuit_compte_pour_la_veille(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    heure.maintenant = heure.maintenant.replace(hour=23, minute=59, second=0)
    etat = lancer(client, quiz)
    heure.avancer(120)
    while etat["question"] is not None:
        etat = client.post(
            f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses",
            json={"rang": etat["question"]["rang"], "choix": 0},
        ).json()

    assert etat["resultat"]["reussie"] is False
    assert vies(client)["restantes"] == 3


def test_un_visiteur_a_aussi_3_vies(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], quiz: Quiz, heure: Horloge
) -> None:
    from datetime import UTC, datetime

    from app.comptes.models import Role

    creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg", email_confirme_le=datetime.now(UTC))
    connecter(client, "passant")

    assert vies(client)["restantes"] == 3
    rater(client, quiz, 3)
    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 409


def test_un_invite_sans_compte_n_a_pas_de_vies(client: TestClient, quiz: Quiz, heure: Horloge) -> None:
    lance = client.post(f"/api/jeux/quiz/{quiz.id}/tentatives")
    assert lance.status_code == 201, lance.text
    etat = lance.json()
    while etat["question"] is not None:
        etat = client.post(
            f"/api/jeux/quiz/tentatives/{etat['tentative_id']}/reponses",
            json={"rang": etat["question"]["rang"], "choix": 0},
        ).json()

    assert etat["vies_restantes"] is None


def test_les_parties_dessai_de_lequipe_ne_coutent_aucune_vie(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    async def essais_rates(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, quiz.parcours)
        for _ in range(VIES_PAR_JOUR):
            db.add(
                TentativeQuiz(
                    quiz_id=quiz.id,
                    joueur_id=eleve.id,
                    parametres_id=p.id,
                    essai=True,
                    etat=EtatTentative.terminee,
                    jour=DEBUT.date(),
                    commencee_le=DEBUT,
                    derniere_activite=DEBUT,
                    terminee_le=DEBUT,
                    score=0,
                    reussie=False,
                )
            )

    en_base(essais_rates)

    assert vies(client) == {"total": 3, "restantes": 3, "perdues": 0, "en_cours": 0}
    lancer(client, quiz)
