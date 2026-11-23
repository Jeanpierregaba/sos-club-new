"""Purge du suivi d'activité (spec 051) : une fois au démarrage, puis toutes les heures. Idempotente.

- Les événements de plus de 90 jours sont comptés par jour dans `total_activite_jour` et `visiteurs_jour`, puis
  effacés : les totaux d'une période ne changent pas.
- Un mot cherché par moins de 3 visiteurs est effacé au bout de 7 jours : un nom tapé une fois ne reste pas.
- Les sels des jours passés et les présences de plus de 26 semaines sont effacés.
"""

import asyncio
import contextlib
import logging
from datetime import date, timedelta

from sqlalchemy import Integer, delete, func, insert, literal, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite import service
from app.activite.models import (
    EvenementActivite,
    PresenceSemaine,
    SelActivite,
    TotalActiviteJour,
    TypeEvenement,
    VisiteursJour,
)
from app.db import SessionLocal

journal = logging.getLogger(__name__)

GARDE_JOURS = 90
RECHERCHE_JOURS = 7
SEUIL_RECHERCHE = 3
PRESENCE_SEMAINES = 26

E = EvenementActivite


async def _agreger(db: AsyncSession, limite: date) -> int:
    anciens = E.jour < limite
    groupe = (E.jour, E.type, E.chemin, E.detail, E.provenance, E.appareil, E.navigateur, E.connecte)
    totaux = select(
        E.jour, E.type, E.chemin,
        func.coalesce(E.detail, ""), func.coalesce(E.provenance, ""), func.coalesce(E.appareil, ""),
        func.coalesce(E.navigateur, ""), E.connecte,
        func.count().cast(Integer), func.count(E.visiteur.distinct()).cast(Integer),
    ).where(anciens).group_by(*groupe)  # fmt: skip
    colonnes = ["jour", "type", "chemin", "detail", "provenance", "appareil", "navigateur", "connecte"]
    await db.execute(insert(TotalActiviteJour).from_select([*colonnes, "evenements", "visiteurs"], totaux))
    await db.execute(
        insert(VisiteursJour).from_select(
            ["jour", "visiteurs"],
            select(E.jour, func.count(E.visiteur.distinct()).cast(Integer)).where(anciens).group_by(E.jour),
        )
    )
    resultat = await db.execute(delete(E).where(anciens))
    return int(getattr(resultat, "rowcount", 0) or 0)


async def _recherches_rares(db: AsyncSession, aujourdhui: date) -> None:
    frequents = (
        select(E.detail)
        .where(E.type == TypeEvenement.recherche)
        .group_by(E.detail)
        .having(func.count(E.visiteur.distinct()) >= literal(SEUIL_RECHERCHE))
    )
    await db.execute(
        delete(E).where(
            E.type == TypeEvenement.recherche,
            E.jour < aujourdhui - timedelta(days=RECHERCHE_JOURS),
            E.detail.not_in(frequents),
        )
    )


async def purger(db: AsyncSession, aujourdhui: date | None = None) -> int:
    """Renvoie le nombre d'événements bruts comptés puis effacés. Valide la transaction."""
    jour = aujourdhui or service.aujourdhui()
    await _recherches_rares(db, jour)
    nombre = await _agreger(db, jour - timedelta(days=GARDE_JOURS))
    await db.execute(delete(SelActivite).where(SelActivite.jour < jour))
    lundi = jour - timedelta(days=jour.weekday())
    await db.execute(
        delete(PresenceSemaine).where(PresenceSemaine.semaine < lundi - timedelta(weeks=PRESENCE_SEMAINES))
    )
    await db.commit()
    return nombre


async def purger_regulierement() -> None:
    while True:
        with contextlib.suppress(SQLAlchemyError, OSError):
            async with SessionLocal() as db:
                nombre = await purger(db)
                if nombre:
                    journal.info("Suivi d'activité : %s événement(s) de plus de 90 jours comptés par jour.", nombre)
        await asyncio.sleep(3600)
