"""La migration du chrono à 15 s (spec 048) : une nouvelle version par parcours, réglages de l'admin gardés."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command


def dernieres(en_base: Callable[..., Any]) -> dict[str, tuple[int, int, int | None, int]]:
    async def lire(db: AsyncSession) -> dict[str, tuple[int, int, int | None, int]]:
        lignes = await db.execute(
            text(
                "SELECT parcours, version, temps_ms, tentatives_par_jour, seuil FROM parametres_quiz p "
                "WHERE version = (SELECT max(version) FROM parametres_quiz v WHERE v.parcours = p.parcours)"
            )
        )
        return {parcours: (version, temps, tentatives, seuil) for parcours, version, temps, tentatives, seuil in lignes}

    return en_base(lire)


def test_la_migration_passe_les_deux_parcours_a_15_secondes(en_base: Callable[..., Any]) -> None:
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
    command.downgrade(configuration, "a1b2c3d4e5f6")
    try:

        async def avant(db: AsyncSession) -> None:
            # Des réglages de l'admin à 20 s, dont un plafond et un seuil modifiés.
            await db.execute(text("DELETE FROM parametres_quiz"))
            await db.execute(
                text(
                    "INSERT INTO parametres_quiz (id, parcours, version, nb_questions, temps_ms, tolerance_ms, seuil, "
                    "tentatives_par_jour, arret_premiere_erreur) VALUES "
                    "(uuidv7(), 'jeux', 4, 15, 20000, 2000, 11, 8, false), "
                    "(uuidv7(), 'certification', 2, 10, 20000, 2000, 10, NULL, true)"
                )
            )

        en_base(avant)
    finally:
        command.upgrade(configuration, "head")

    assert dernieres(en_base) == {"jeux": (5, 15000, 8, 11), "certification": (3, 15000, None, 10)}

    # Relancée sur des parcours déjà à 15 s, elle n'ajoute rien.
    command.downgrade(configuration, "a1b2c3d4e5f6")
    command.upgrade(configuration, "head")
    assert dernieres(en_base) == {"jeux": (5, 15000, 8, 11), "certification": (3, 15000, None, 10)}
