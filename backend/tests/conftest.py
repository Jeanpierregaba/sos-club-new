import asyncio
import os
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# Toujours cette base locale, jamais celle de l'environnement : les tests effacent toutes ses données.
URL_BASE_TEST = "postgresql+asyncpg://sosclub@127.0.0.1:5435/sosclub_test"
os.environ["DATABASE_URL"] = URL_BASE_TEST

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.comptes.models import Role, Utilisateur
from app.comptes.motdepasse import hacher
from app.db import Base
from app.main import app

MOT_DE_PASSE = "mot-de-passe-de-test"
# NullPool : chaque appel ouvre sa connexion, car asyncio.run crée une nouvelle boucle à chaque fois.
moteur_test = create_async_engine(URL_BASE_TEST, poolclass=NullPool)


async def _recreer_base() -> None:
    url = make_url(URL_BASE_TEST)
    moteur_admin = create_async_engine(url.set(database="sosclub"), isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with moteur_admin.connect() as connexion:
        await connexion.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        await connexion.execute(text(f'CREATE DATABASE "{url.database}"'))
    await moteur_admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def base_de_test() -> None:
    asyncio.run(_recreer_base())
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
    # L'aller et le retour : une migration qui ne sait pas revenir en arrière fait échouer les tests.
    command.upgrade(configuration, "head")
    command.downgrade(configuration, "base")
    command.upgrade(configuration, "head")


async def _vider_tables() -> None:
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with moteur_test.begin() as connexion:
        await connexion.execute(text(f"TRUNCATE {tables} CASCADE"))


@pytest.fixture(autouse=True)
def tables_vides() -> None:
    asyncio.run(_vider_tables())


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def en_base() -> Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any]:
    """Exécute une fonction asynchrone sur la base de test, dans une transaction validée."""

    def executer(fonction: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
        async def _executer() -> Any:
            async with AsyncSession(moteur_test, expire_on_commit=False) as db:
                resultat = await fonction(db)
                await db.commit()
                return resultat

        return asyncio.run(_executer())

    return executer


@pytest.fixture
def creer_utilisateur(en_base: Callable[..., Any]) -> Callable[..., Utilisateur]:
    def creer(
        identifiant: str = "jeank",
        role: Role = Role.eleve,
        email: str | None = None,
        mot_de_passe: str = MOT_DE_PASSE,
        **champs: Any,
    ) -> Utilisateur:
        async def inserer(db: AsyncSession) -> Utilisateur:
            utilisateur = Utilisateur(
                identifiant=identifiant,
                role=role,
                email=email,
                prenom=champs.pop("prenom", "Jean"),
                nom=champs.pop("nom", "Kodjo"),
                mot_de_passe_hash=await hacher(mot_de_passe),
                **champs,
            )
            db.add(utilisateur)
            return utilisateur

        return en_base(inserer)

    return creer
