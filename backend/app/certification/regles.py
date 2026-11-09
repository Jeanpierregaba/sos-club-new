"""Règles des badges (spec 029, Q24) : la version la plus haute est en cours ; un badge garde la version avec
laquelle il a été délivré."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification.models import ReglesBadges

# Les paliers affichés sur /certification, en attendant les règles de l'équipe pédagogique.
NOMS_PAR_DEFAUT = ["Bronze", "Argent", "Or", "Platine", "Diamant Imhotep"]
PALIERS_PAR_DEFAUT = [3, 5, 7, 9, 12]


async def en_cours(db: AsyncSession) -> ReglesBadges:
    """La dernière version ; la première est créée par défaut si la table est vide (base de test vidée)."""
    requete = select(ReglesBadges).order_by(ReglesBadges.version.desc()).limit(1)
    regles = await db.scalar(requete)
    if regles is None:
        await db.execute(
            insert(ReglesBadges)
            .values(version=1, noms=NOMS_PAR_DEFAUT, paliers=PALIERS_PAR_DEFAUT)
            .on_conflict_do_nothing(index_elements=["version"])
        )
        regles = await db.scalar(requete)
        assert regles is not None
    return regles
