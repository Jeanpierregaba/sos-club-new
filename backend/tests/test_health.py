from collections.abc import AsyncIterator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db import get_session
from app.main import app


def test_health_interroge_la_vraie_base(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_repond_503_sans_base(client: TestClient) -> None:
    # Le port 1 est toujours fermé : la connexion échoue comme avec une base arrêtée.
    injoignable = create_async_engine("postgresql+asyncpg://sosclub@127.0.0.1:1/sosclub")

    async def session_injoignable() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(injoignable) as session:
            yield session

    app.dependency_overrides[get_session] = session_injoignable

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Base de données injoignable"}
