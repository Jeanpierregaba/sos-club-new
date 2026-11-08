"""Aides des tests des quiz (spec 027) : une banque minimale, une horloge réglable et une partie jouée."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.points.models import MouvementPoints
from app.quiz import horloge
from app.quiz.models import EtatQuiz, ParametresQuiz, QuestionQuiz, Quiz, TentativeQuiz
from app.referentiel.models import Axe

QUIZ = "/api/quiz"
DEBUT = datetime(2026, 11, 9, 10, 0, tzinfo=UTC)


class Horloge:
    """L'heure du serveur, avancée à la main : 6,9 s et 7,1 s se testent sans attendre."""

    def __init__(self) -> None:
        self.maintenant = DEBUT

    def avancer(self, secondes: float) -> None:
        self.maintenant += timedelta(seconds=secondes)


def figer_horloge(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    h = Horloge()
    monkeypatch.setattr(horloge, "maintenant", lambda: h.maintenant)
    return h


def creer_quiz(
    en_base: Callable[..., Any],
    questions: int = 15,
    etat: EtatQuiz = EtatQuiz.publie,
    titre: str = "Quiz de test",
    axe: str | None = None,
) -> Quiz:
    """Un quiz dont chaque bonne réponse commence par « Juste » : le test la retrouve dans l'ordre mélangé."""

    async def inserer(db: AsyncSession) -> Quiz:
        code = axe or await db.scalar(select(Axe.code).order_by(Axe.code).limit(1))
        publie = etat is EtatQuiz.publie
        quiz = Quiz(
            titre=titre,
            description="Pour les tests.",
            axe_code=code,
            etat=etat,
            contenu_de_test=True,
            validateur_nom="Dr Test" if publie else None,
            validateur_qualite="Médecin" if publie else None,
            publie_le=DEBUT if publie else None,
        )
        db.add(quiz)
        await db.flush()
        for i in range(questions):
            db.add(
                QuestionQuiz(
                    quiz_id=quiz.id,
                    enonce=f"Question {i + 1} ?",
                    choix=[f"Juste {i + 1}", f"Faux A {i + 1}", f"Faux B {i + 1}"],
                    bonne_reponse=0,
                    explication=f"Explication secrète {i + 1}",
                    ordre=i + 1,
                )
            )
        return quiz

    return en_base(inserer)


def regler(en_base: Callable[..., Any], **valeurs: int) -> None:
    """Ajoute une version des paramètres du parcours « jeux », à partir de la dernière."""
    from app.quiz import parametres

    async def ajouter(db: AsyncSession) -> None:
        actuels = await parametres.en_cours(db)
        champs = {
            "nb_questions": actuels.nb_questions,
            "temps_ms": actuels.temps_ms,
            "tolerance_ms": actuels.tolerance_ms,
            "seuil": actuels.seuil,
            "tentatives_par_jour": actuels.tentatives_par_jour,
        } | valeurs
        db.add(ParametresQuiz(parcours="jeux", version=actuels.version + 1, **champs))

    en_base(ajouter)


def bon_choix(question: dict[str, Any]) -> int:
    return next(i for i, texte in enumerate(question["choix"]) if texte.startswith("Juste"))


def mauvais_choix(question: dict[str, Any]) -> int:
    return next(i for i, texte in enumerate(question["choix"]) if not texte.startswith("Juste"))


def lancer(client: Any, quiz: Quiz) -> dict[str, Any]:
    reponse = client.post(f"{QUIZ}/{quiz.id}/tentatives")
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def repondre(client: Any, etat: dict[str, Any], choix: int) -> dict[str, Any]:
    reponse = client.post(
        f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses",
        json={"rang": etat["question"]["rang"], "choix": choix},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def jouer(client: Any, quiz: Quiz, justes: int) -> dict[str, Any]:
    """Une partie complète : `justes` bonnes réponses d'abord, puis des fausses. Renvoie l'état final."""
    etat = lancer(client, quiz)
    n = 0
    while etat["question"] is not None:
        q = etat["question"]
        etat = repondre(client, etat, bon_choix(q) if n < justes else mauvais_choix(q))
        n += 1
    return etat


def gains(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[MouvementPoints]:
    return list(
        en_base(
            lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == utilisateur_id))
        ).all()
    )


def tentatives(en_base: Callable[..., Any]) -> list[TentativeQuiz]:
    return list(en_base(lambda db: db.scalars(select(TentativeQuiz))).all())


def connecter(client: TestClient, identifiant: str) -> None:
    from tests.conftest import MOT_DE_PASSE

    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text
