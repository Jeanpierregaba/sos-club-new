"""Purge du suivi d'activité (spec 051) : une fois au démarrage, puis toutes les heures. Idempotente.

- Les événements de plus de 90 jours sont comptés par jour dans `total_activite_jour`, leurs visiteurs distincts dans
  `visiteurs_jour` et, par regroupement de la page, dans `visiteurs_groupe_jour`, puis effacés : les chiffres d'une
  période ne changent pas.
- Un mot cherché par moins de 3 visiteurs le même jour est effacé dès le lendemain : un nom tapé une fois ne reste
  pas.
- Les sels des jours passés et les présences de plus de 26 semaines sont effacés.
"""

import asyncio
import contextlib
import logging
from datetime import date, timedelta

from sqlalchemy import Integer, String, delete, func, insert, literal, select, tuple_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite import service
from app.activite.models import (
    DIMENSIONS_VISITEURS,
    SEPARATEUR,
    EvenementActivite,
    PresenceSemaine,
    SelActivite,
    TotalActiviteJour,
    TypeEvenement,
    VisiteursGroupeJour,
    VisiteursJour,
)
from app.db import SessionLocal

journal = logging.getLogger(__name__)

GARDE_JOURS = 90
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
        func.count().cast(Integer),
    ).where(anciens).group_by(*groupe)  # fmt: skip
    colonnes = ["jour", "type", "chemin", "detail", "provenance", "appareil", "navigateur", "connecte"]
    await db.execute(insert(TotalActiviteJour).from_select([*colonnes, "evenements"], totaux))
    for dimensions in DIMENSIONS_VISITEURS:
        valeurs = [func.coalesce(getattr(E, d).cast(String), "") for d in dimensions]
        await db.execute(
            insert(VisiteursGroupeJour).from_select(
                ["jour", "type", "dimensions", "valeurs", "visiteurs"],
                select(
                    E.jour, E.type, literal(",".join(dimensions)),
                    func.concat_ws(SEPARATEUR, *valeurs) if valeurs else literal(""),
                    func.count(E.visiteur.distinct()).cast(Integer),
                ).where(anciens).group_by(E.jour, E.type, *valeurs),
            )
        )  # fmt: skip
    await db.execute(
        insert(VisiteursJour).from_select(
            ["jour", "visiteurs"],
            select(E.jour, func.count(E.visiteur.distinct()).cast(Integer)).where(anciens).group_by(E.jour),
        )
    )
    resultat = await db.execute(delete(E).where(anciens))
    return int(getattr(resultat, "rowcount", 0) or 0)


async def _recherches_rares(db: AsyncSession, aujourdhui: date) -> None:
    """Un jour fini, ses recherches faites par moins de 3 visiteurs sont effacées."""
    frequentes = (
        select(E.jour, E.detail)
        .where(E.type == TypeEvenement.recherche, E.jour < aujourdhui)
        .group_by(E.jour, E.detail)
        .having(func.count(E.visiteur.distinct()) >= literal(SEUIL_RECHERCHE))
    )
    await db.execute(
        delete(E).where(
            E.type == TypeEvenement.recherche,
            E.jour < aujourdhui,
            tuple_(E.jour, E.detail).not_in(frequentes),
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
