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


class Moi(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    identifiant: str
    prenom: str
    nom: str
    role: Role


class ComptesParRole(BaseModel):
    eleve: int
    encadreur: int
    admin: int


class ChiffresAdmin(BaseModel):
    comptes: ComptesParRole
