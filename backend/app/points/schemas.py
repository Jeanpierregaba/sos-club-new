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
    # Sans semestre en cours, l'espace dit « Aucun semestre en cours » au lieu de « Pas encore classé ».
    semestre_en_cours: SemestrePublic | None
    semestre: RangPersonnel
    historique: RangPersonnel
    # Les distinctions de fin de semestre (spec 037), du plus récent au plus ancien ; vide pour qui n'en a pas.
    distinctions: list[Distinction]


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


# Registre, recherche et correction (spec 036) ---------------------------------------------------------------------


class AuteurRegistre(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: str
    identifiant: str


class LigneRegistre(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    cree_le: datetime
    utilisateur_id: UUID
    role: str
    identifiant: str
    prenom: str
    nom: str
    pseudonyme: str | None
    action: str
    action_libelle: str
    montant: int
    points_club: float | None
    semestre: str | None
    annee: str | None
    club: ClubClasse | None
    cle: str
    valide_par: AuteurRegistre | None
    motif: str | None
    annule_id: UUID | None
    est_annulation: bool
    est_correction: bool
    annulee: bool


class PageRegistre(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    page: int
    par_page: int
    lignes: list[LigneRegistre]


class BeneficiairePoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    role: Literal["eleve", "encadreur"]
    nom_public: str
    identifiant: str
    club: str | None
    points_total: int


class CorrectionPoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utilisateur_id: UUID
    montant: int = Field(ge=-MONTANT_MAX, le=MONTANT_MAX)
    motif: str = Field(min_length=10, max_length=500)
    cle: UUID


class AnnulationPoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: str = Field(min_length=10, max_length=500)


# Clôtures de semestre et palmarès (spec 037) -------------------------------------------------------------------


class MotifCloture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: str = Field(min_length=10, max_length=500)


class ClotureResume(BaseModel):
    semestre_id: UUID
    libelle: str
    debut: date
    fin: date
    termine: bool
    etat: Literal["ouvert", "gele", "valide", "publie"]
    publie_le: datetime | None


class SemestreCloture(BaseModel):
    id: UUID
    libelle: str
    debut: date
    fin: date


class EtapesCloture(BaseModel):
    gele_le: datetime
    gele_par: str
    valide_le: datetime | None
    valide_par: str | None
    publie_le: datetime | None
    publie_par: str | None


class CandidatAdmin(BaseModel):
    utilisateur_id: UUID
    rang: int
    rang_brut: int
    pseudonyme: str
    identifiant: str
    statut: str
    club: str | None
    dre: str
    points: int
    atteint_le: datetime
    corrections: int
    annulations: int
    ecarte: bool
    motif_ecart: str | None
    ecarte_le: datetime | None
    ecarte_par: str | None


class LaureatAdmin(BaseModel):
    utilisateur_id: UUID
    place: int | None
    distinction: str
    pseudonyme: str
    club: str | None
    dre: str
    points: int


class ChangementActuel(BaseModel):
    """`points_actuels` vaut None si l'élève n'est plus classable (suspendu, ancien, total nul) ; `hors_photo`
    signale un élève toujours classé, mais au-delà des 50 premiers."""

    pseudonyme: str
    points_gel: int | None
    points_actuels: int | None
    hors_photo: bool = False


class EcartActuel(BaseModel):
    top3_different: bool
    changements: list[ChangementActuel]


class ClotureDetail(BaseModel):
    semestre: SemestreCloture
    etat: Literal["gele", "valide", "publie"]
    etapes: EtapesCloture
    candidats: list[CandidatAdmin]
    top3: list[LaureatAdmin]
    ecart_actuel: EcartActuel


class LaureatPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    place: int
    distinction: str
    pseudonyme: str
    club: str | None
    dre: str
    points: int


class SemestrePalmares(BaseModel):
    model_config = ConfigDict(extra="forbid")

    libelle: str
    debut: date
    fin: date
    laureats: list[LaureatPublic]


class PalmaresPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semestres: list[SemestrePalmares]


class Distinction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semestre: str
    place: int
    distinction: str
    points: int


ClassementPersonnel.model_rebuild()
