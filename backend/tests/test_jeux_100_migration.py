"""Migration de la spec 050 : les 80 quiz Jeux de la spec 049 recomposés en 100 quiz sur les 1 000 questions."""

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.comptes.models import Utilisateur
from app.quiz import parametres
from app.quiz.models import EtatQuiz, EtatTentative, QuestionQuiz, Quiz, TentativeQuiz
from tests.quiz import DEBUT, creer_quiz
from tests.test_ouverture_migration import AIMES, AVANT, configuration

BANQUE_049 = "c5f1a8e3d920"
DONNEES = Path(__file__).resolve().parents[1] / "alembic" / "donnees"
JEUX_100 = json.loads((DONNEES / "jeux_100.json").read_text(encoding="utf-8"))
BANQUE = json.loads((DONNEES / "banque_officielle.json").read_text(encoding="utf-8"))
MOTIF = "Recomposés en 100 quiz sur les 1 000 questions (spec 050)."


def _publies(en_base: Callable[..., Any], parcours: str) -> list[Quiz]:
    return en_base(
        lambda db: db.scalars(select(Quiz).where(Quiz.parcours == parcours, Quiz.etat == EtatQuiz.publie))
    ).all()


def _tentative(quiz_id: UUID, joueur_id: UUID, parametres_id: UUID, etat: EtatTentative) -> TentativeQuiz:
    finie = etat is EtatTentative.terminee
    return TentativeQuiz(
        quiz_id=quiz_id, joueur_id=joueur_id, parametres_id=parametres_id, etat=etat, jour=DEBUT.date(),
        commencee_le=DEBUT, derniere_activite=DEBUT, terminee_le=DEBUT if finie else None,
        score=10 if finie else None, reussie=True if finie else None,
    )  # fmt: skip


@pytest.fixture
def banque_049(en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur]) -> dict[str, Any]:
    """Une base passée par la spec 049 (ses 80 quiz Jeux), où un élève a réussi un quiz et en a un en cours."""
    defi = creer_quiz(en_base, titre="Défi 1", niveau="debutant", numero=1)
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == defi.id).values(validateur_nom=AIMES)))
    command.downgrade(configuration(), AVANT)
    command.upgrade(configuration(), BANQUE_049)
    eleve = creer_eleve("ama")
    jeux = sorted(_publies(en_base, "jeux"), key=lambda q: q.numero or 0)
    assert len(jeux) == 80

    async def jouer(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, "jeux")
        db.add(_tentative(jeux[0].id, eleve.id, p.id, EtatTentative.terminee))
        db.add(_tentative(jeux[1].id, eleve.id, p.id, EtatTentative.en_cours))

    en_base(jouer)
    return {"eleve": eleve, "jeux": jeux, "certification": {q.id for q in _publies(en_base, "certification")}}


def test_recompose_les_100_quiz(en_base: Callable[..., Any], banque_049: dict[str, Any]) -> None:
    command.upgrade(configuration(), "head")

    jeux = sorted(_publies(en_base, "jeux"), key=lambda q: q.numero or 0)
    assert [q.numero for q in jeux] == list(range(1, 101))
    assert Counter(q.niveau for q in jeux) == {"debutant": 40, "intermediaire": 30, "avance": 20, "expert": 10}
    assert [q.titre for q in jeux] == [q["titre"] for q in JEUX_100]

    enonces = en_base(
        lambda db: db.scalars(select(QuestionQuiz.enonce).where(QuestionQuiz.quiz_id.in_([q.id for q in jeux])))
    ).all()
    tous = [x["enonce"] for q in BANQUE["jeux"] + BANQUE["certification"] for x in q["questions"]]
    assert len(enonces) == 1000 and sorted(enonces) == sorted(tous)

    # Les 80 quiz : dépubliés avec un motif ; la partie jouée reste, celle en cours est close.
    anciens = en_base(lambda db: db.scalars(select(Quiz).where(Quiz.id.in_([q.id for q in banque_049["jeux"]])))).all()
    assert {(q.etat, q.motif) for q in anciens} == {(EtatQuiz.depublie, MOTIF)}
    tentatives = en_base(
        lambda db: db.scalars(select(TentativeQuiz).where(TentativeQuiz.joueur_id == banque_049["eleve"].id))
    ).all()
    assert sorted((t.etat, t.reussie) for t in tentatives) == [
        (EtatTentative.terminee, False),
        (EtatTentative.terminee, True),
    ]
    # La certification ne bouge pas.
    assert {q.id for q in _publies(en_base, "certification")} == banque_049["certification"]


def test_rejouer_ne_change_rien(en_base: Callable[..., Any], banque_049: dict[str, Any]) -> None:
    command.upgrade(configuration(), "head")
    premiers = {q.id for q in _publies(en_base, "jeux")}

    command.stamp(configuration(), BANQUE_049)
    command.upgrade(configuration(), "head")

    assert {q.id for q in _publies(en_base, "jeux")} == premiers


def test_retour_arriere_puis_remontee(en_base: Callable[..., Any], banque_049: dict[str, Any]) -> None:
    command.upgrade(configuration(), "head")
    command.downgrade(configuration(), BANQUE_049)

    assert {q.id for q in _publies(en_base, "jeux")} == {q.id for q in banque_049["jeux"]}

    command.upgrade(configuration(), "head")
    assert len(_publies(en_base, "jeux")) == 100


def test_retour_arriere_refuse_une_fois_joues(en_base: Callable[..., Any], banque_049: dict[str, Any]) -> None:
    command.upgrade(configuration(), "head")
    quiz = _publies(en_base, "jeux")[0]

    async def jouer(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, "jeux")
        db.add(_tentative(quiz.id, banque_049["eleve"].id, p.id, EtatTentative.terminee))

    en_base(jouer)

    with pytest.raises(RuntimeError, match="ne se retirent plus"):
        command.downgrade(configuration(), BANQUE_049)
    assert len(_publies(en_base, "jeux")) == 100


def test_rien_sans_les_80_quiz(en_base: Callable[..., Any]) -> None:
    command.downgrade(configuration(), BANQUE_049)
    test = creer_quiz(en_base, titre="Quiz Jeux de test", niveau="debutant", numero=1)

    command.upgrade(configuration(), "head")

    assert [q.id for q in _publies(en_base, "jeux")] == [test.id]


def test_un_ancien_defi_republie_laisse_son_numero(en_base: Callable[..., Any], banque_049: dict[str, Any]) -> None:
    """L'équipe a republié un ancien défi avec le numéro 90 : il est dépublié pour le nouveau quiz 90."""
    defi = creer_quiz(en_base, titre="Ancien défi 90", niveau="expert", numero=90)

    command.upgrade(configuration(), "head")

    jeux = _publies(en_base, "jeux")
    assert sorted(q.numero for q in jeux) == list(range(1, 101))
    assert defi.id not in {q.id for q in jeux}
    assert en_base(lambda db: db.get(Quiz, defi.id)).motif == MOTIF
