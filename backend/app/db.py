from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Le délai de connexion évite qu'une requête reste bloquée une minute quand la base est injoignable.
# Sans hide_parameters, une erreur SQL écrit dans les logs les valeurs de la requête, donc des données personnelles.
engine = create_async_engine(
    settings.database_url, pool_pre_ping=True, connect_args={"timeout": 5}, hide_parameters=True
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe de base des modèles : Alembic s'en sert pour générer les migrations."""

    # Des noms de contraintes stables permettent aux migrations de les retrouver plus tard.
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_N_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
