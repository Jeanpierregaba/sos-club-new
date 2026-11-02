from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RACINE_PROJET = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Le .env de la racine contient aussi les variables du site : celles qui ne concernent pas l'API sont ignorées.
    # Une variable laissée vide, comme dans .env.example, garde sa valeur par défaut.
    model_config = SettingsConfigDict(env_file=RACINE_PROJET / ".env", extra="ignore", env_ignore_empty=True)

    # Base locale de docker-compose.yml, sans mot de passe. En production, DATABASE_URL la remplace.
    database_url: str = "postgresql+asyncpg://sosclub@127.0.0.1:5435/sosclub"

    # Adresse du site vue par le navigateur (ADR-0006). En production, SITE_ORIGINE la remplace.
    site_origine: str = "http://localhost:3000"

    cookie_session: str = "session_sosclub"
    duree_session_jours: int = 30
    duree_session_admin_heures: int = 12

    fenetre_essais_minutes: int = 15
    essais_max_identifiant: int = 5
    # Une classe peut partager une même adresse réseau : ce seuil reste bien plus haut que par identifiant.
    essais_max_adresse: int = 50

    @property
    def cookie_secure(self) -> bool:
        return self.site_origine.startswith("https://")


settings = Settings()
