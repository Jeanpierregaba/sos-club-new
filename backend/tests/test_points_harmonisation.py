"""Barème harmonisé (spec 022, tâche 1) : les montants du référentiel du 2026-11-05."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.points.models import LigneBareme

ATTENDU = {
    "eleve.bienvenue": 100,
    "eleve.commentaire": 5,
    "eleve.republication": 10,
    "eleve.article": 50,
    "eleve.partage": 50,
    "eleve.quiz": 50,
    "eleve.question_jour": 20,
    "eleve.badge": 500,
    "eleve.certification": 1000,
    "club.bienvenue_eleve": 50,
    "club.commentaire_eleve": 20,
    "club.republication_eleve": 2,
    "club.article_eleve": 20,
    "club.partage_eleve": 2,
    "club.quiz_eleve": 25,
    "club.question_jour_eleve": 10,
    "club.badge_eleve": 200,
    "club.certification_eleve": 500,
    "club.rapport_activite": 50,
    "club.bilan_semestriel": 100,
    "encadreur.quiz": 0,
}


def montants(en_base: Callable[..., Any]) -> dict[str, int]:
    async def lire(db: AsyncSession) -> dict[str, int]:
        return {code: montant for code, montant in await db.execute(select(LigneBareme.code, LigneBareme.montant))}

    return en_base(lire)


def test_le_bareme_suit_le_referentiel(en_base: Callable[..., Any]) -> None:
    lus = montants(en_base)

    assert {code: lus[code] for code in ATTENDU} == ATTENDU
    assert len(lus) == 37


def test_la_migration_aligne_le_bareme_sans_ecraser_un_montant_regle(en_base: Callable[..., Any]) -> None:
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
    command.downgrade(configuration, "8f4444de8fad")
    try:
        avant = montants(en_base)
        assert (avant["eleve.quiz"], avant["club.quiz_eleve"]) == (25, 10)
        assert "eleve.question_jour" not in avant

        async def regler(db: AsyncSession) -> None:
            # Un montant réglé par l'admin avant la migration.
            await db.execute(text("UPDATE bareme SET montant = 15 WHERE code = 'club.quiz_eleve'"))

        en_base(regler)
    finally:
        command.upgrade(configuration, "head")

    apres = montants(en_base)
    assert apres["eleve.quiz"] == 50
    assert apres["club.quiz_eleve"] == 15
    assert apres["eleve.question_jour"] == 20
    assert len(apres) == 37

    async def ordre(db: AsyncSession) -> list[str]:
        return list(await db.scalars(select(LigneBareme.code).order_by(LigneBareme.ordre)))

    codes = en_base(ordre)
    assert codes.index("eleve.question_jour") == codes.index("eleve.quiz") + 1
