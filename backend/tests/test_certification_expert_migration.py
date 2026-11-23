"""Migration de la spec 043 : lot 7 de la banque et 20 quiz de certification de niveau expert."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.comptes.models import Utilisateur
from app.quiz.models import EtatQuiz, QuestionQuiz, Quiz
from tests.quiz import QUIZ, Horloge, connecter, figer_horloge, gains, lancer

AVANT = "8224c2108aff"
APRES = "4dc45a4fff16"  # la migration de la spec 043
DONNEES = Path(__file__).resolve().parents[1] / "alembic" / "donnees"
CERTIFICATION = json.loads((DONNEES / "certification_expert.json").read_text(encoding="utf-8"))
LOT7 = json.loads((DONNEES / "quiz_sante_lot7.json").read_text(encoding="utf-8"))
MAINTENANT = datetime(2026, 11, 19, tzinfo=UTC)


def configuration() -> Config:
    return Config(Path(__file__).resolve().parents[1] / "alembic.ini")


def _quiz(titre: str, **champs: Any) -> Quiz:
    publie = champs.get("etat", EtatQuiz.publie) is EtatQuiz.publie
    return Quiz(
        titre=titre,
        axe_code=champs.pop("axe_code", "production-tv-medias"),
        etat=champs.pop("etat", EtatQuiz.publie),
        validateur_nom="Dr Test" if publie else None,
        validateur_qualite="Médecin" if publie else None,
        publie_le=MAINTENANT,
        **champs,
    )


@pytest.fixture
def banque(en_base: Callable[..., Any]) -> None:
    """Une banque réduite à un quiz « Lot 1 — », un quiz de test sur la place 1 et un vrai quiz sur la place 2."""

    async def inserer(db: AsyncSession) -> None:
        db.add(_quiz("Banque", etat=EtatQuiz.depublie, description="Lot 1 — AIMES-AFRIQUE · questions 1 à 27."))
        db.add(_quiz("[Test] place 1", parcours="certification", place=1, contenu_de_test=True))
        db.add(_quiz("Vrai quiz de la place 2", parcours="certification", place=2))

    en_base(inserer)


def _recharger() -> None:
    command.downgrade(configuration(), AVANT)
    command.upgrade(configuration(), "head")


def _etat(en_base: Callable[..., Any]) -> dict[str, Any]:
    async def lire(db: AsyncSession) -> dict[str, Any]:
        lot7 = (await db.scalars(select(Quiz).where(Quiz.description.like("Lot 7 — %")))).all()
        publies = (
            await db.scalars(
                select(Quiz).where(Quiz.parcours == "certification", Quiz.etat == EtatQuiz.publie).order_by(Quiz.place)
            )
        ).all()
        questions = {
            quiz_id: nombre
            for quiz_id, nombre in (
                await db.execute(select(QuestionQuiz.quiz_id, func.count()).group_by(QuestionQuiz.quiz_id))
            ).all()
        }
        test = await db.scalar(select(Quiz).where(Quiz.titre == "[Test] place 1"))
        return {
            "lot7": [(q.titre, q.etat, questions.get(q.id, 0)) for q in lot7],
            "publies": [(q.place, q.titre, questions.get(q.id, 0)) for q in publies],
            "test": test.etat if test else None,
            "quiz": await db.scalar(select(func.count()).select_from(Quiz)),
        }

    return en_base(lire)


@pytest.mark.usefixtures("banque")
def test_charge_le_lot_7_et_les_20_quiz_de_certification(en_base: Callable[..., Any]) -> None:
    _recharger()
    etat = _etat(en_base)

    assert len(etat["lot7"]) == 15
    assert sum(n for _, _, n in etat["lot7"]) == 78
    assert {e for _, e, _ in etat["lot7"]} == {EtatQuiz.depublie}

    attendus = {p["place"]: p["titre"] for p in CERTIFICATION}
    assert [place for place, _, _ in etat["publies"]] == list(range(1, 21))
    # La place 2 garde son vrai quiz ; les autres reçoivent le quiz de niveau expert, de 10 questions.
    assert etat["publies"][1][1] == "Vrai quiz de la place 2"
    for place, titre, nombre in etat["publies"]:
        if place != 2:
            assert (titre, nombre) == (attendus[place], 10)
    assert etat["test"] is EtatQuiz.depublie


@pytest.mark.usefixtures("banque")
def test_une_seconde_execution_ne_change_rien(en_base: Callable[..., Any]) -> None:
    _recharger()
    avant = _etat(en_base)

    # Les migrations suivantes créent des tables (spec 049) : on les défait avant de rejouer celle de la spec 043.
    command.downgrade(configuration(), APRES)
    command.stamp(configuration(), AVANT)
    command.upgrade(configuration(), "head")

    assert _etat(en_base) == avant


@pytest.mark.usefixtures("banque")
def test_le_retour_arriere_retire_les_quiz_jamais_joues(en_base: Callable[..., Any]) -> None:
    _recharger()
    command.downgrade(configuration(), AVANT)

    etat = _etat(en_base)
    assert etat["lot7"] == []
    assert [titre for _, titre, _ in etat["publies"]] == ["Vrai quiz de la place 2"]
    assert etat["quiz"] == 3
    command.upgrade(configuration(), "head")


def test_rien_sans_la_banque(en_base: Callable[..., Any]) -> None:
    _recharger()
    assert _etat(en_base)["quiz"] == 0


def test_un_eleve_reussit_la_place_1_a_10_sur_10(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(_quiz("Banque", etat=EtatQuiz.depublie, description="Lot 1 — AIMES-AFRIQUE · questions 1 à 27."))

    en_base(inserer)
    _recharger()
    horloge: Horloge = figer_horloge(monkeypatch)
    eleve = creer_eleve("ama")
    connecter(client, "ama")
    quiz = {
        q.place: q
        for q in en_base(
            lambda db: db.scalars(select(Quiz).where(Quiz.parcours == "certification", Quiz.etat == EtatQuiz.publie))
        ).all()
    }
    bonnes = {q["enonce"]: q["choix"][q["bonne"]] for q in CERTIFICATION[0]["questions"]}

    etat = lancer(client, quiz[1])
    while etat["question"] is not None:
        question = etat["question"]
        horloge.avancer(2)
        reponse = client.post(
            f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses",
            json={"rang": question["rang"], "choix": question["choix"].index(bonnes[question["enonce"]])},
        )
        assert reponse.status_code == 200, reponse.text
        etat = reponse.json()

    assert etat["resultat"]["reussie"] is True
    assert etat["resultat"]["score"] == 10
    assert [g.montant for g in gains(en_base, eleve.id)] == [50]
    assert client.post(f"{QUIZ}/{quiz[2].id}/tentatives").status_code == 201


def test_le_lot_7_et_la_selection_ne_se_recouvrent_pas() -> None:
    lot7 = {q["enonce"] for theme in LOT7 for q in theme["questions"]}
    assert not lot7 & {q["enonce"] for p in CERTIFICATION for q in p["questions"]}
