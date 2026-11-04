from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.referentiel.models import FORMAT_CODE, StatutEtablissement, TypeEtablissement
from app.referentiel.normalisation import nettoyer


def _nettoyer_facultatif(valeur: str | None) -> str | None:
    """Un champ facultatif vidé redevient nul."""
    if valeur is None:
        return None
    return " ".join(valeur.split()) or None


Nom = Annotated[str, Field(max_length=300), AfterValidator(nettoyer)]
NomComplet = Annotated[str, Field(max_length=400), AfterValidator(lambda v: nettoyer(v, 200))]
Description = Annotated[str, Field(max_length=600), AfterValidator(lambda v: nettoyer(v, 300))]
Facultatif = Annotated[str | None, Field(max_length=150), AfterValidator(_nettoyer_facultatif)]
Code = Annotated[str, Field(min_length=2, max_length=30, pattern=FORMAT_CODE)]
Version = Annotated[int, Field(ge=1)]

# Listes publiques : aucun auteur, aucune date (spec 016) --------------------------------------------------------


class IesgPublique(BaseModel):
    id: UUID
    nom: str
    zone: str | None
    nb_etablissements: int


class DrePublique(BaseModel):
    code: str
    nom: str
    nom_complet: str
    nb_etablissements: int
    iesg: list[IesgPublique]


class EtablissementPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nom: str
    type: TypeEtablissement


class IesgAnnuaire(IesgPublique):
    etablissements: list[EtablissementPublic]


class DreAnnuaire(BaseModel):
    code: str
    nom: str
    nom_complet: str
    nb_etablissements: int
    iesg: list[IesgAnnuaire]


class EtablissementTrouve(EtablissementPublic):
    """Un établissement avec de quoi le situer dans un formulaire : son IESG et sa DRE."""

    iesg_id: UUID
    iesg: str
    dre_code: str
    dre: str


class EtablissementRattache(BaseModel):
    """L'établissement d'un élève ou d'un encadreur, vu par lui-même ou par l'admin : avec son statut."""

    id: UUID
    nom: str
    statut: StatutEtablissement
    iesg: str
    dre_code: str
    dre: str


class Proposition(BaseModel):
    """Un établissement absent du référentiel, proposé à l'inscription : créé « proposé », invisible du public, validé par l'admin."""

    model_config = ConfigDict(extra="forbid")

    iesg_id: UUID
    nom: Nom


class AxePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    libelle: str
    description: str


# Espace admin -----------------------------------------------------------------------------------------------


class IesgAdmin(BaseModel):
    id: UUID
    dre_code: str
    nom: str
    zone: str | None
    actif: bool
    version: int
    nb_etablissements: int


class DreAdmin(BaseModel):
    code: str
    nom: str
    nom_complet: str
    ordre: int
    actif: bool
    version: int
    nb_etablissements: int
    iesg: list[IesgAdmin]


class EtablissementAdmin(BaseModel):
    id: UUID
    nom: str
    type: TypeEtablissement
    localite: str | None
    statut: StatutEtablissement
    version: int
    iesg_id: UUID
    iesg: str
    dre_code: str
    dre: str
    modifie_le: datetime
    # Élèves rattachés (spec 017) : utile pour décider du sort d'un établissement proposé.
    nb_eleves: int
    nb_encadreurs: int = 0


class PageEtablissements(BaseModel):
    total: int
    page: int
    par_page: int
    etablissements: list[EtablissementAdmin]


class AxeAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    libelle: str
    description: str
    ordre: int
    actif: bool
    version: int


class _Entree(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DreCreation(_Entree):
    code: Code
    nom: Nom
    nom_complet: NomComplet
    ordre: int | None = Field(default=None, ge=1, le=99)


class DreModification(_Entree):
    """Seuls les champs envoyés changent. `version` est celle que le formulaire a lue."""

    version: Version
    nom: Nom | None = None
    nom_complet: NomComplet | None = None
    ordre: int | None = Field(default=None, ge=1, le=99)
    actif: bool | None = None


class IesgCreation(_Entree):
    dre_code: str = Field(max_length=30)
    nom: Nom
    zone: Facultatif = None


class IesgModification(_Entree):
    version: Version
    nom: Nom | None = None
    zone: Facultatif = None
    dre_code: str | None = Field(default=None, max_length=30)
    actif: bool | None = None


class EtablissementCreation(_Entree):
    iesg_id: UUID
    nom: Nom
    type: TypeEtablissement
    localite: Facultatif = None


class EtablissementModification(_Entree):
    version: Version
    nom: Nom | None = None
    type: TypeEtablissement | None = None
    localite: Facultatif = None
    iesg_id: UUID | None = None
    # « Proposé » vient de la création d'un club (R4) : il ne se choisit pas ici.
    statut: Literal[StatutEtablissement.actif, StatutEtablissement.inactif] | None = None


class AxeCreation(_Entree):
    code: Annotated[str, Field(min_length=2, max_length=40, pattern=FORMAT_CODE)]
    libelle: Nom
    description: Description
    ordre: int | None = Field(default=None, ge=1, le=99)


class AxeModification(_Entree):
    version: Version
    libelle: Nom | None = None
    description: Description | None = None
    ordre: int | None = Field(default=None, ge=1, le=99)
    actif: bool | None = None


class Remplacement(BaseModel):
    """Remplace un établissement proposé par un établissement existant : ses élèves y sont rattachés (spec 017)."""

    model_config = ConfigDict(extra="forbid")

    version: Version
    cible_id: UUID
