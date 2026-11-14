from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.points.models import MONTANT_MAX, Beneficiaire, Parcours, SousCompte
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
    # Spec 034 : le parcours de l'élève, et pour les Jeux le sous-compte (quiz ou étoiles).
    parcours: Parcours | None
    sous_compte: SousCompte | None
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


# Classements (spec 036) ---------------------------------------------------------------------------------------


class DreResume(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    nom: str


class SemestrePublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    libelle: str
    debut: date
    fin: date


class LignePersonnePublic(BaseModel):
    """Un élève ou un encadreur, sans aucun identifiant ni contact."""

    model_config = ConfigDict(extra="forbid")

    rang: int
    nom: str
    club: str | None
    dre: str
    points: int


class LigneClubPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rang: int
    club_id: UUID
    nom: str
    etablissement: str
    dre: str
    points: float


class ClassementPersonnesPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categorie: Literal["eleves", "encadreurs"]
    niveau: Literal["national", "dre"]
    dre: DreResume | None
    periode: Literal["semestre", "historique"]
    semestre: SemestrePublic | None
    page: int
    par_page: int
    total: int
    lignes: list[LignePersonnePublic]


class ClassementClubsPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categorie: Literal["clubs"]
    niveau: Literal["national", "dre"]
    dre: DreResume | None
    periode: Literal["semestre", "historique"]
    semestre: SemestrePublic | None
    page: int
    par_page: int
    total: int
    lignes: list[LigneClubPublic]


class ClubClasse(BaseModel):
    """Le club d'un classement (spec 036). Un autre nom que `clubs.schemas.ClubResume` : deux schémas de même
    nom seraient renommés dans le schéma de l'API, et le site ne les trouverait plus."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    nom: str


class RangPersonnel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: int
    rang_club: int | None
    rang_dre: int | None
    rang_national: int | None
    classe: bool


class ClassementPersonnel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categorie: Literal["eleves", "encadreurs"]
    club: ClubClasse | None
    semestre: RangPersonnel
    historique: RangPersonnel


class LigneClubInterne(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rang: int
    nom: str
    points: int
    est_moi: bool


class ClassementClubInterne(BaseModel):
    model_config = ConfigDict(extra="forbid")

    club: ClubClasse
    categorie: Literal["eleves", "encadreurs"]
    periode: Literal["semestre", "historique"]
    semestre: SemestrePublic | None
    page: int
    par_page: int
    total: int
    lignes: list[LigneClubInterne]


class LignePersonneAdmin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rang: int
    utilisateur_id: UUID
    nom: str
    club_id: UUID | None
    club: str | None
    dre: str
    points: int


class LigneClubAdmin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rang: int
    club_id: UUID
    nom: str
    etablissement: str
    dre: str
    points: float


class ClassementPersonnesAdmin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categorie: Literal["eleves", "encadreurs"]
    niveau: Literal["national", "dre"]
    dre: DreResume | None
    periode: Literal["semestre", "historique"]
    semestre: SemestrePublic | None
    page: int
    par_page: int
    total: int
    lignes: list[LignePersonneAdmin]


class ClassementClubsAdmin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categorie: Literal["clubs"]
    niveau: Literal["national", "dre"]
    dre: DreResume | None
    periode: Literal["semestre", "historique"]
    semestre: SemestrePublic | None
    page: int
    par_page: int
    total: int
    lignes: list[LigneClubAdmin]


class LigneClubAdminInterne(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rang: int
    utilisateur_id: UUID
    nom: str
    points: int


class ClassementClubAdminInterne(BaseModel):
    model_config = ConfigDict(extra="forbid")

    club: ClubClasse
    statut: str
    categorie: Literal["eleves", "encadreurs"]
    periode: Literal["semestre", "historique"]
    semestre: SemestrePublic | None
    page: int
    par_page: int
    total: int
    lignes: list[LigneClubAdminInterne]
