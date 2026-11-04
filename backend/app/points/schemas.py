from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.points.models import MONTANT_MAX, Beneficiaire
from app.referentiel.normalisation import nettoyer

Libelle = Annotated[str, AfterValidator(lambda valeur: nettoyer(valeur, 60))]
Version = Annotated[int, Field(ge=1)]
Montant = Annotated[int, Field(ge=0, le=MONTANT_MAX)]


class SemestreAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    libelle: str
    debut: date
    fin: date
    etat: Literal["a_venir", "en_cours", "termine"]
    version: int


class SemestreCreation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    libelle: Libelle
    debut: date
    fin: date

    @model_validator(mode="after")
    def dates_ordonnees(self) -> SemestreCreation:
        if self.fin < self.debut:
            raise ValueError("La fin du semestre précède son début")
        return self


class SemestreModification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Version
    libelle: Libelle | None = None
    debut: date | None = None
    fin: date | None = None


class LigneBaremeAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    beneficiaire: Beneficiaire
    libelle: str
    montant: int
    propose: bool
    en_service: bool
    actif: bool
    version: int


class LigneBaremeModification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Version
    montant: Montant | None = None
    propose: bool | None = None
    actif: bool | None = None


# Résumé des points d'un élève ou d'un encadreur, dans son espace ou sa fiche admin -------------------------------


class SemestreResume(BaseModel):
    libelle: str
    debut: date
    fin: date


class LignePoints(BaseModel):
    libelle: str
    montant: int
    cree_le: datetime
    semestre: str | None


class ResumePoints(BaseModel):
    semestre: SemestreResume | None
    points_semestre: int
    total: int
    lignes: list[LignePoints]
