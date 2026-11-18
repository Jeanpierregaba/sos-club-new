"""Migration de la fusion des établissements (spec 042) : aller-retour, et retour refusé après une fusion."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.referentiel.models import Etablissement, StatutEtablissement

AVANT = "52c30f73350d"

pytestmark = pytest.mark.usefixtures("annuaire")


def configuration() -> Config:
    return Config(Path(__file__).resolve().parents[1] / "alembic.ini")


def test_la_migration_fait_laller_retour() -> None:
    command.downgrade(configuration(), AVANT)
    command.upgrade(configuration(), "head")


def test_le_retour_est_refuse_apres_une_fusion(en_base: Callable[..., Any]) -> None:
    async def fusionner(db: AsyncSession) -> None:
        absorbe, garde = (await db.scalars(select(Etablissement.id).order_by(Etablissement.id).limit(2))).all()
        await db.execute(
            update(Etablissement)
            .where(Etablissement.id == absorbe)
            .values(statut=StatutEtablissement.inactif, fusionne_dans_id=garde)
        )

    en_base(fusionner)

    with pytest.raises(RuntimeError, match="perdraient leur renvoi"):
        command.downgrade(configuration(), AVANT)
    command.upgrade(configuration(), "head")


def test_un_etablissement_actif_ne_renvoie_nulle_part(en_base: Callable[..., Any]) -> None:
    from sqlalchemy.exc import IntegrityError

    async def renvoyer(db: AsyncSession) -> None:
        absorbe, garde = (await db.scalars(select(Etablissement.id).order_by(Etablissement.id).limit(2))).all()
        await db.execute(update(Etablissement).where(Etablissement.id == absorbe).values(fusionne_dans_id=garde))

    with pytest.raises(IntegrityError, match="fusionne_si_inactif"):
        en_base(renvoyer)
