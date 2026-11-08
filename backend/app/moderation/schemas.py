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


class ParentContenu(BaseModel):
    """L'article d'un commentaire (spec 025) : le modérateur juge le commentaire dans son contexte."""

    adresse: str | None
    titre: str


class ClubContenu(BaseModel):
    """Le club au nom duquel le président écrit (spec 026)."""

    id: UUID
    nom: str


class FicheActuelle(BaseModel):
    """La fiche publique du club au moment de la lecture : l'« avant » d'une proposition de fiche."""

    description: str | None
    axes: list[str]


class ElementFile(BaseModel):
    id: UUID
    type: str
    parent: ParentContenu | None = None
    club: ClubContenu | None = None
    depublication_possible: bool = True
    # Faux pour un type sans décision « à corriger » (un commentaire).
    correction_possible: bool = True
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


class PhotoModeration(BaseModel):
    id: UUID
    legende: str | None
    couverture: bool
    ordre: int
    largeur: int
    hauteur: int
    attestation: str
    attestee_le: datetime
    effacee: bool


class ApercuModeration(ElementFile):
    # Les champs de la version soumise (ou de travail), et ceux de la version en ligne : l'admin compare.
    soumise: dict[str, Any] | None
    publiee: dict[str, Any] | None
    photos_soumises: list[PhotoModeration]
    photos_publiees: list[PhotoModeration]
    decisions: list[DecisionPassee]
    fiche_actuelle: FicheActuelle | None = None
