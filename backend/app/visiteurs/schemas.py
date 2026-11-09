from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.comptes.champs import Requis100, TelephoneObligatoire, Texte100
from app.comptes.models import Sexe
from app.comptes.service import LONGUEUR_MAX_MOT_DE_PASSE
from app.visiteurs.models import Region

Code = Annotated[str, Field(min_length=1, max_length=20)]


class InscriptionVisiteur(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prenom: str = Field(max_length=100)
    nom: str = Field(max_length=100)
    telephone: TelephoneObligatoire
    ville: Requis100
    email: str = Field(max_length=254)
    region: Region | None = None
    sexe: Sexe | None = None
    statut: Texte100 = None
    mot_de_passe: str = Field(max_length=LONGUEUR_MAX_MOT_DE_PASSE)
    # Les cases du formulaire : vérifiées ici, pas seulement par le site.
    charte: Literal[True]
    majeur_ou_accord: Literal[True]


class CodeEnvoye(BaseModel):
    """Le compte attend son code. `code_de_test` : seulement hors production, sans SMTP configuré."""

    email: str
    code_de_test: str | None = None


class ConfirmationEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    code: Code


class RenvoiEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)


class RenvoiSortie(BaseModel):
    """Même réponse que l'adresse existe ou non."""

    code_de_test: str | None = None


class EspaceVisiteur(BaseModel):
    prenom: str
    nom: str
    email: str
    telephone: str | None
    ville: str
    region: Region | None
    sexe: Sexe | None
    statut: str | None
