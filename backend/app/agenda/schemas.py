"""Schémas de l'agenda (spec 041).

Les heures se saisissent à l'heure de Lomé, sans fuseau (`2026-12-05T09:30`). Lomé vit à UTC+0 toute l'année, sans
heure d'été : la conversion est exacte avec un fuseau fixe, sans dépendre de la base des fuseaux de l'image Docker.
Elles sont stockées en UTC et renvoyées avec leur fuseau.
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Annotated, Any, Self
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.agenda.models import NiveauEvenement, Reponse, TypeEvenement
from app.moderation.models import EtatContenu

LOME = timezone(timedelta(0), "Africa/Lome")


def a_lome(instant: datetime) -> datetime:
    """Une heure saisie à Lomé (sans fuseau) ou déjà datée, en UTC."""
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=LOME)
    return instant.astimezone(UTC)


def _https(lien: str | None) -> str | None:
    if lien is not None and not lien.startswith("https://"):
        raise ValueError("le lien doit commencer par https://")
    return lien


Texte = Annotated[str, StringConstraints(strip_whitespace=True)]
Titre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=150)]
Court = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Lien = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500), AfterValidator(_https)]


class ChampsEvenement(BaseModel):
    """Les champs d'un événement : la version d'un événement de club (JSONB), ou la saisie de l'équipe."""

    model_config = ConfigDict(extra="forbid")

    titre: Titre
    type: TypeEvenement
    axe_code: str | None = None
    objectif: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None = None
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=5000)]
    lieu: Court | None = None
    en_ligne: bool = False
    lien: Lien | None = None
    public_vise: Court | None = None
    debut: datetime
    fin: datetime
    places: Annotated[int, Field(ge=1, le=10_000)] | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if a_lome(self.fin) <= a_lome(self.debut):
            raise ValueError("la fin doit venir après le début")
        if self.en_ligne and not self.lien:
            raise ValueError("un événement en ligne a besoin de son lien")
        if not self.en_ligne and not self.lieu:
            raise ValueError("indique le lieu de l'événement")
        return self


class AnnulationEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=200)]


class ModificationEntree(BaseModel):
    """Les champs restent bruts ici : le service les valide et nomme le champ fautif dans son message."""

    model_config = ConfigDict(extra="forbid")

    version: int
    champs: dict[str, Any]


class VersionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int


# Club --------------------------------------------------------------------------------------------------------


class EvenementDuClub(BaseModel):
    """Un événement dans l'agenda du club : ce que voient les encadreurs et le président."""

    id: UUID
    etat: EtatContenu
    version: int
    auteur: str
    de_moi: bool
    champs: dict[str, object]
    publie: bool
    annule_le: datetime | None
    motif_annulation: str | None
    motif_decision: str | None
    participants: int
    peut_modifier: bool


class AgendaDuClub(BaseModel):
    club: str
    evenements: list[EvenementDuClub]


class ReponseMembre(BaseModel):
    eleve_id: UUID
    pseudonyme: str
    nom: str
    reponse: Reponse | None
    present: bool | None


class ReponsesEvenement(BaseModel):
    participe: int
    peut_etre: int
    non: int
    sans_reponse: int
    presents: int
    pointage_ouvert: bool
    membres: list[ReponseMembre]


class PresencesEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    presences: dict[UUID, bool]


class ReponseEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reponse: Reponse


# Public --------------------------------------------------------------------------------------------------------


class EvenementPublic(BaseModel):
    """Ce que montre l'agenda public : aucun nom d'élève, seulement le nombre de participants."""

    id: UUID
    niveau: NiveauEvenement
    type: TypeEvenement
    axe_code: str | None
    titre: str
    objectif: str | None
    description: str
    lieu: str | None
    en_ligne: bool
    lien: str | None
    public_vise: str | None
    debut: datetime
    fin: datetime
    places: int | None
    participants: int
    complet: bool
    # Le motif d'une annulation n'est pas public : il est écrit sans modération (RULES). Les invités le reçoivent.
    annule: bool
    dre_code: str | None
    dre: str | None
    club_id: UUID | None
    club: str | None
    etablissement: str | None
    # Pour un membre connecté du club organisateur : il peut répondre, et voici sa réponse.
    peut_repondre: bool = False
    ma_reponse: Reponse | None = None


class PageAgenda(BaseModel):
    total: int
    evenements: list[EvenementPublic]


# Équipe --------------------------------------------------------------------------------------------------------


class EvenementEquipeEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    niveau: NiveauEvenement
    dre_code: str | None = None
    champs: ChampsEvenement

    @model_validator(mode="after")
    def niveau_coherent(self) -> Self:
        if self.niveau is NiveauEvenement.club:
            raise ValueError("un événement de club est proposé par le club")
        if (self.niveau is NiveauEvenement.regional) != (self.dre_code is not None):
            raise ValueError("un événement régional, et lui seul, a sa DRE")
        return self
