from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.comptes.models import Role
from app.comptes.service import LONGUEUR_MAX_IDENTIFIANT_SAISI, LONGUEUR_MAX_MOT_DE_PASSE, normaliser


class ConnexionEntree(BaseModel):
    identifiant: str = Field(min_length=1, max_length=LONGUEUR_MAX_IDENTIFIANT_SAISI)
    # Un plafond évite de faire hacher un texte énorme à Argon2.
    mot_de_passe: str = Field(min_length=1, max_length=LONGUEUR_MAX_MOT_DE_PASSE)

    @field_validator("identifiant")
    @classmethod
    def identifiant_exploitable(cls, valeur: str) -> str:
        # Après normalisation : passer en minuscules peut allonger un texte, et PostgreSQL refuse le caractère NUL.
        normalise = normaliser(valeur)
        if not normalise or len(normalise) > LONGUEUR_MAX_IDENTIFIANT_SAISI or "\x00" in normalise:
            raise ValueError("Identifiant invalide")
        return valeur


class EtapeCode(BaseModel):
    """Mot de passe juste, double authentification active : le code est demandé avant d'ouvrir la session."""

    etape: Literal["code"] = "code"
    jeton: str


class EtapeConfirmation(BaseModel):
    """Visiteur au bon mot de passe dont l'adresse n'est pas confirmée (spec 030) : un code lui est renvoyé."""

    etape: Literal["confirmation"] = "confirmation"
    email: str
    # Seulement hors production, sans SMTP configuré.
    code_de_test: str | None = None


class CodeEntree(BaseModel):
    jeton: str = Field(min_length=1, max_length=100)
    # 6 chiffres, ou un code de secours de 16 caractères, avec ses tirets et espaces éventuels.
    code: str = Field(min_length=1, max_length=40)


class Moi(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    identifiant: str
    prenom: str
    nom: str
    role: Role


class MotDePasseEntree(BaseModel):
    actuel: str = Field(min_length=1, max_length=LONGUEUR_MAX_MOT_DE_PASSE)
    nouveau: str = Field(max_length=LONGUEUR_MAX_MOT_DE_PASSE)
