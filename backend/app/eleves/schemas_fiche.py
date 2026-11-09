"""Fiche d'adhésion de l'élève (spec 030) : entrée et sortie."""

import re
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.comptes.champs import (
    Requis100,
    Requis150,
    Telephone,
    TelephoneObligatoire,
    Texte30,
    Texte60,
    Texte100,
    Texte150,
)
from app.comptes.models import Sexe
from app.eleves.models import Reseau

AGE_MIN = 8
AGE_MAX = 30
AXES_MAX = 3
FORMAT_ANNEE = re.compile(r"(\d{4})-(\d{4})")


def _annee(valeur: str) -> str:
    correspondance = FORMAT_ANNEE.fullmatch(valeur.strip())
    if not correspondance or int(correspondance[2]) != int(correspondance[1]) + 1:
        raise ValueError("Écris l'année scolaire sous la forme 2025-2026")
    return correspondance[0]


AnneeScolaire = Annotated[str, Field(max_length=9), AfterValidator(_annee)]


class Parent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: Texte150 = None
    profession: Texte100 = None
    telephone: Telephone = None


class Responsable(BaseModel):
    """Le parent ou tuteur responsable : il remplace la signature de la fiche papier."""

    model_config = ConfigDict(extra="forbid")

    nom: Requis150
    telephone: TelephoneObligatoire


class ParcoursAnterieur(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annee: AnneeScolaire
    etablissement: Requis150
    iesg: Texte150 = None


def _age(naissance: date, jour: date) -> int:
    return jour.year - naissance.year - ((jour.month, jour.day) < (naissance.month, naissance.day))


class FicheEntree(BaseModel):
    """Une fiche complète : à l'inscription comme à la correction depuis l'espace."""

    model_config = ConfigDict(extra="forbid")

    numero_adhesion: Texte30 = None
    prefecture: Texte100 = None
    commune: Texte100 = None
    canton: Texte100 = None
    sexe: Sexe
    date_naissance: date
    lieu_naissance: Requis100
    telephone: Telephone = None
    pere: Parent | None = None
    mere: Parent | None = None
    responsable: Responsable
    axes: list[Annotated[str, Field(max_length=40)]] = Field(min_length=1, max_length=AXES_MAX)
    parcours: list[ParcoursAnterieur] = Field(default_factory=list, max_length=2)
    reseaux: list[Reseau] = Field(default_factory=list, max_length=4)
    reseau_autre: Texte60 = None
    # La case d'engagement : vérifiée ici, pas seulement par le site.
    engagement: Literal[True]

    @model_validator(mode="after")
    def coherente(self) -> FicheEntree:
        age = _age(self.date_naissance, date.today())
        if self.date_naissance > date.today() or not AGE_MIN <= age <= AGE_MAX:
            raise ValueError(f"Vérifie ta date de naissance : un élève a entre {AGE_MIN} et {AGE_MAX} ans")
        if len(set(self.axes)) != len(self.axes):
            raise ValueError("Choisis chaque axe une seule fois")
        if len(set(self.reseaux)) != len(self.reseaux):
            raise ValueError("Coche chaque réseau une seule fois")
        if (Reseau.autre in self.reseaux) != (self.reseau_autre is not None):
            raise ValueError("Précise l'autre réseau, seulement si tu as coché « Autre »")
        return self


class FicheModification(FicheEntree):
    # None : l'élève n'a pas encore de fiche (ancien compte).
    version: Annotated[int, Field(ge=1)] | None


class FicheSortie(BaseModel):
    annee_scolaire: str
    numero_adhesion: str | None
    prefecture: str | None
    commune: str | None
    canton: str | None
    sexe: Sexe | None
    date_naissance: date | None
    lieu_naissance: str | None
    telephone: str | None
    pere: Parent | None
    mere: Parent | None
    responsable: Responsable | None
    axes: list[str]
    parcours: list[ParcoursAnterieur]
    reseaux: list[Reseau]
    reseau_autre: str | None
    engagement_le: datetime | None
    complete_le: datetime | None
    cree_le: datetime
    version: int
