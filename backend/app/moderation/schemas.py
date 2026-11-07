from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from app.moderation.models import EtatContenu, TypeDecision

Motif = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ApprobationEntree(BaseModel):
    version: int


class DecisionModerationEntree(BaseModel):
    """Correction, refus ou dépublication : le motif est obligatoire, et l'auteur le lit."""

    version: int
    motif: Motif


class AuteurFile(BaseModel):
    """Le modérateur voit qui écrit (nom complet, établissement) : la file est réservée à l'espace admin."""

    id: UUID
    nom: str
    identifiant: str
    profil: str
    etablissement: str | None
    dre_code: str | None


class ElementFile(BaseModel):
    id: UUID
    type: str
    titre: str
    etat: EtatContenu
    axe_code: str | None
    auteur: AuteurFile
    # Vrai pour une nouvelle version d'un contenu déjà en ligne.
    nouvelle_version: bool
    en_ligne: bool
    adresse: str | None
    soumis_le: datetime | None
    modifie_le: datetime
    version: int


class FileModeration(BaseModel):
    total: int
    contenus: list[ElementFile]


class DecisionPassee(BaseModel):
    decision: TypeDecision
    motif: str | None
    decide_par: str | None
    decide_le: datetime


class ApercuModeration(ElementFile):
    # Les champs de la version soumise (ou de travail), et ceux de la version en ligne : l'admin compare.
    soumise: dict[str, Any] | None
    publiee: dict[str, Any] | None
    decisions: list[DecisionPassee]
