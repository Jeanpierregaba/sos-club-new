"""Règles des badges (spec 029, Q24) : la version la plus haute est en cours ; un badge garde la version avec
laquelle il a été délivré."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification.models import ReglesBadges

# Les 5 badges officiels (spec 034) : un par thématique de 4 places, dans l'ordre du parcours.
NOMS_PAR_DEFAUT = [
    "Ambassadeur Santé Junior",
    "Pair Éducateur Santé et Citoyenneté",
    "Sentinelle de la Prévention",
    "Champion de la Santé et EVSS",
    "Maître Génie Imhotep",
]
PALIERS_PAR_DEFAUT = [4, 8, 12, 16, 20]


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
