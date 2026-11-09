import logging
from pathlib import Path
from typing import Literal, Self

from cryptography.fernet import Fernet
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RACINE_PROJET = Path(__file__).resolve().parents[2]
BASE_LOCALE = "postgresql+asyncpg://sosclub@127.0.0.1:5435/sosclub"
# Hors production uniquement : une clé créée au premier lancement, ignorée par git (*.key).
FICHIER_CLE_LOCALE = RACINE_PROJET / "backend" / ".cle-chiffrement-locale.key"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Le .env de la racine contient aussi les variables du site : celles qui ne concernent pas l'API sont ignorées.
    # Une variable laissée vide, comme dans .env.example, garde sa valeur par défaut.
    model_config = SettingsConfigDict(env_file=RACINE_PROJET / ".env", extra="ignore", env_ignore_empty=True)

    # Base locale de docker-compose.yml, sans mot de passe. En production, DATABASE_URL la remplace.
    database_url: str = BASE_LOCALE

    # Adresse du site vue par le navigateur (ADR-0006). En production, SITE_ORIGINE la remplace.
    site_origine: str = "http://localhost:3000"

    cookie_session: str = "session_sosclub"
    duree_session_jours: int = 30
    duree_session_admin_heures: int = 12

    fenetre_essais_minutes: int = 15
    essais_max_identifiant: int = 5
    # Une classe peut partager une même adresse réseau : ce seuil reste bien plus haut que par identifiant.
    essais_max_adresse: int = 50

    # Espace administrateur (spec 015).
    duree_invitation_heures: int = 72
    duree_etape_code_minutes: int = 5
    duree_lien_export_minutes: int = 15
    duree_fichier_export_heures: int = 24
    export_lignes_max: int = 50_000

    # Fichiers (spec 024, ADR-0010) : sur le disque du VPS, dans un volume Docker. Hors du dépôt en local.
    dossier_fichiers: Path = RACINE_PROJET / "backend" / "var" / "fichiers"
    photo_octets_max: int = 8 * 1024 * 1024
    # Un PDF de la bibliothèque (spec 028) ; le proxy laisse passer 25 Mo pour l'enveloppe du formulaire.
    ressource_octets_max: int = 20 * 1024 * 1024

    # Inscription des élèves (spec 017). None : ouvertes en local, fermées dès que le site est en HTTPS, car aucune
    # vraie donnée d'élève ne doit entrer avant le récépissé de l'IPDCP (docs/RULES.md). La préproduction les ouvre.
    inscriptions_ouvertes: bool | None = None
    # Une salle informatique partage souvent une seule adresse réseau.
    inscriptions_max_adresse: int = 20
    # Version de la charte acceptée à l'inscription : à changer avec le texte de la page /charte.
    version_charte: str = "2026-11-provisoire"

    # Clé Fernet qui chiffre les secrets de double authentification. Obligatoire en production.
    cle_chiffrement: str | None = None

    # Environnement de déploiement : « develop » en local, « preprod » ou « prod » sur le VPS (deploy/compose.yaml).
    # Sert à autoriser les comptes de test uniquement en préproduction (docs/RULES.md).
    environnement: Literal["develop", "preprod", "prod"] = "develop"

    # Envoi des e-mails. Sans hôte, hors production, les liens sont seulement écrits dans le terminal.
    smtp_hote: str | None = None
    smtp_port: int = 587
    smtp_securite: Literal["starttls", "ssl", "aucune"] = "starttls"
    smtp_utilisateur: str | None = None
    smtp_mot_de_passe: str | None = None
    smtp_expediteur: str | None = None

    @field_validator("site_origine")
    @classmethod
    def origine_sans_barre_finale(cls, valeur: str) -> str:
        return valeur.rstrip("/")

    @model_validator(mode="after")
    def production_sans_base_locale(self) -> Self:
        if self.cookie_secure and self.database_url == BASE_LOCALE:
            raise ValueError("DATABASE_URL est obligatoire quand le site est en HTTPS.")
        if self.cookie_secure and not self.cle_chiffrement:
            raise ValueError("CLE_CHIFFREMENT est obligatoire quand le site est en HTTPS.")
        if self.cle_chiffrement:
            Fernet(self.cle_chiffrement)  # Une clé mal formée doit bloquer le démarrage, pas la première connexion.
        return self

    @property
    def inscriptions_actives(self) -> bool:
        return self.inscriptions_ouvertes if self.inscriptions_ouvertes is not None else not self.cookie_secure

    @property
    def cookie_secure(self) -> bool:
        return self.site_origine.startswith("https://")

    @property
    def production(self) -> bool:
        return self.cookie_secure

    def fernet(self) -> Fernet:
        if self.cle_chiffrement:
            return Fernet(self.cle_chiffrement)
        if not FICHIER_CLE_LOCALE.exists():
            FICHIER_CLE_LOCALE.write_bytes(Fernet.generate_key())
            FICHIER_CLE_LOCALE.chmod(0o600)
            logger.warning("Clé de chiffrement locale créée : %s", FICHIER_CLE_LOCALE.name)
        return Fernet(FICHIER_CLE_LOCALE.read_bytes())


settings = Settings()
