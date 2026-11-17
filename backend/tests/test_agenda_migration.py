"""Migration de l'agenda (spec 041) : aller-retour, et retour refusé tant qu'un événement existe."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.agenda.models import Evenement, NiveauEvenement, TypeEvenement
from app.points.models import LigneBareme

AVANT = "4618adf52b56"


def configuration() -> Config:
    return Config(Path(__file__).resolve().parents[1] / "alembic.ini")


def en_service(en_base: Callable[..., Any]) -> bool:
    return en_base(
        lambda db: db.scalar(select(LigneBareme.en_service).where(LigneBareme.code == "encadreur.evenement"))
    )


def test_la_migration_fait_laller_retour(en_base: Callable[..., Any]) -> None:
    assert en_service(en_base) is True

    command.downgrade(configuration(), AVANT)
    try:
        assert en_service(en_base) is False
    finally:
        command.upgrade(configuration(), "head")

    assert en_service(en_base) is True


def test_le_retour_est_refuse_si_un_evenement_existe(en_base: Callable[..., Any]) -> None:
    debut = datetime.now(UTC) + timedelta(days=3)

    async def inserer(db: AsyncSession) -> None:
        db.add(
            Evenement(
                niveau=NiveauEvenement.national,
                type=TypeEvenement.concours,
                titre="Finale nationale",
                description="La finale du concours.",
                debut=debut,
                fin=debut + timedelta(hours=3),
                publie=True,
            )
        )

    en_base(inserer)

    with pytest.raises(RuntimeError, match="Des événements existent"):
        command.downgrade(configuration(), AVANT)
    command.upgrade(configuration(), "head")
