"""Schémas des cartes numériques (spec 040)."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.cartes.models import TypeCarte
from app.cartes.service import Cause, Role


class MaCarte(BaseModel):
    """La carte vue par son titulaire : tout ce qui est imprimé dessus, plus son statut et sa cause."""

    type: TypeCarte
    numero: str
    prenom: str
    nom: str
    role: Role
    etablissement: str | None
    club: str | None
    delivree_le: datetime
    valide: bool
    cause: Cause | None
    adresse_verification: str


class VerificationCarte(BaseModel):
    """La page publique du QR (Q30) : le type, le numéro, le club et le statut. Rien d'autre, jamais."""

    model_config = ConfigDict(extra="forbid")

    type: TypeCarte
    numero: str
    club: str | None
    valide: bool
    verifiee_le: datetime


class EvenementCarte(BaseModel):
    action: Literal["carte_delivree", "carte_suspendue", "carte_reactivee"]
    le: datetime
    motif: str | None = None


class CarteAdmin(BaseModel):
    """La carte dans la fiche d'un inscrit. Le code du QR n'y figure pas."""

    type: TypeCarte
    numero: str
    valide: bool
    cause: Cause | None
    club: str | None
    delivree_le: datetime
    suspendue_le: datetime | None
    motif_suspension: str | None
    historique: list[EvenementCarte]


Motif = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=200)]


class MotifCarte(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Motif
