from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy import DateTime, Integer, MetaData, func, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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


class Suivi:
    """Colonnes communes : verrou optimiste et dates. Chaque modèle déclare aussi
    `__mapper_args__ = {"version_id_col": Suivi.version}` : deux collaborateurs ne s'écrasent pas."""

    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modifie_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
