import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.config import BASE_LOCALE, Settings

VRAIE_BASE = "postgresql+asyncpg://u:p@db:5432/sosclub"


def test_le_site_en_https_refuse_la_base_locale() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(site_origine="https://exemple.tg", database_url=BASE_LOCALE)


def test_le_site_en_https_accepte_une_vraie_base() -> None:
    reglages = Settings(
        site_origine="https://exemple.tg/", database_url=VRAIE_BASE, cle_chiffrement=Fernet.generate_key().decode()
    )

    assert reglages.site_origine == "https://exemple.tg"
    assert reglages.cookie_secure


def test_le_site_en_https_exige_une_cle_de_chiffrement() -> None:
    with pytest.raises(ValidationError, match="CLE_CHIFFREMENT"):
        Settings(site_origine="https://exemple.tg", database_url=VRAIE_BASE)


def test_une_cle_de_chiffrement_mal_formee_bloque_le_demarrage() -> None:
    with pytest.raises(ValidationError):
        Settings(site_origine="http://localhost:3000", cle_chiffrement="pas-une-cle")


def test_en_local_la_base_locale_reste_acceptee() -> None:
    assert not Settings(site_origine="http://localhost:3000", database_url=BASE_LOCALE).cookie_secure
