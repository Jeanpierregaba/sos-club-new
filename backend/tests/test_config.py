import pytest
from pydantic import ValidationError

from app.config import BASE_LOCALE, Settings


def test_le_site_en_https_refuse_la_base_locale() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(site_origine="https://exemple.tg", database_url=BASE_LOCALE)


def test_le_site_en_https_accepte_une_vraie_base() -> None:
    reglages = Settings(site_origine="https://exemple.tg/", database_url="postgresql+asyncpg://u:p@db:5432/sosclub")

    assert reglages.site_origine == "https://exemple.tg"
    assert reglages.cookie_secure


def test_en_local_la_base_locale_reste_acceptee() -> None:
    assert not Settings(site_origine="http://localhost:3000", database_url=BASE_LOCALE).cookie_secure
