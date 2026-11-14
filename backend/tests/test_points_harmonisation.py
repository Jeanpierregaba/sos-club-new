"""Barème harmonisé (spec 022, tâche 1), puis spec 034 : les lignes `club.*_eleve` sont désactivées au profit de la
part du club à 50 % (ADR-0012)."""

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
    # La ligne technique `admin.correction` (spec 036) s'ajoute aux 46 actions du barème.
    assert len(set(lus) - {"admin.correction"}) == 46


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
    # La spec 034 désactive ensuite la ligne, sans toucher au montant réglé par l'admin.
    assert apres["club.quiz_eleve"] == 15
    assert apres["eleve.question_jour"] == 20
    assert len(set(apres) - {"admin.correction"}) == 46

    async def ordre(db: AsyncSession) -> list[str]:
        return list(await db.scalars(select(LigneBareme.code).order_by(LigneBareme.ordre)))

    codes = en_base(ordre)
    # Ordre de la spec 034 : la question du jour avec la vie du site, avant les quiz.
    assert codes.index("eleve.question_jour") == codes.index("eleve.partage") + 1
