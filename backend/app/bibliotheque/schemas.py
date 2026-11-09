"""Schémas de la bibliothèque (spec 028) : la gestion dans l'espace admin, et la bibliothèque publique."""

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.bibliotheque.models import CategorieRessource, EtatRessource

Texte = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# Gestion ----------------------------------------------------------------------------------------------------------


class RessourceEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: Annotated[Texte, StringConstraints(max_length=150)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = ""
    categorie: CategorieRessource
    axe_code: str | None = None
    parution: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=60)] = None

    @model_validator(mode="after")
    def coherente(self) -> Self:
        # Seul un magazine a un numéro ou une date de parution.
        if self.categorie is not CategorieRessource.magazine or not self.parution:
            self.parution = None
        if not self.axe_code:
            self.axe_code = None
        return self


class RessourceGestion(BaseModel):
    id: UUID
    titre: str
    description: str
    categorie: CategorieRessource
    axe_code: str | None
    parution: str | None
    etat: EtatRessource
    contenu_de_test: bool
    fichier_octets: int | None
    pages: int | None
    a_couverture: bool
    telechargements: int
    soumis_le: datetime | None
    decide_le: datetime | None
    motif: str | None
    validateur_nom: str | None
    validateur_qualite: str | None
    publie_le: datetime | None
    deja_publiee: bool
    modifie_le: datetime
    # Le collaborateur connecté a préparé cette ressource : il ne peut pas la publier.
    contributeur: bool


class ListeGestion(BaseModel):
    ressources: list[RessourceGestion]


class Approbation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validateur_nom: Annotated[Texte, StringConstraints(min_length=2, max_length=120)]
    validateur_qualite: Annotated[Texte, StringConstraints(min_length=2, max_length=120)]


class Motif(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Annotated[Texte, StringConstraints(min_length=3, max_length=500)]


# Public -----------------------------------------------------------------------------------------------------------


class RessourcePublique(BaseModel):
    id: UUID
    titre: str
    description: str
    categorie: CategorieRessource
    axe_code: str | None
    parution: str | None
    fichier_octets: int
    pages: int | None
    telechargements: int
    publie_le: datetime
    validateur_nom: str
    validateur_qualite: str
    contenu_de_test: bool
    # Adresse de la vignette (relative à l'API), qui change avec l'image : nulle sans couverture.
    couverture: str | None


class Chiffres(BaseModel):
    documents: int
    telechargements: int


class Bibliotheque(BaseModel):
    a_la_une: list[RessourcePublique]
    ressources: list[RessourcePublique]
    chiffres: Chiffres
