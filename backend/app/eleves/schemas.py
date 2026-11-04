from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.comptes.service import LONGUEUR_MAX_MOT_DE_PASSE
from app.eleves.models import Classe
from app.referentiel.models import StatutEtablissement
from app.referentiel.schemas import Nom


class EtatInscription(BaseModel):
    ouvertes: bool
    version_charte: str


class Proposition(BaseModel):
    """Un établissement absent du référentiel : créé « proposé », invisible du public, validé par l'admin."""

    model_config = ConfigDict(extra="forbid")

    iesg_id: UUID
    nom: Nom


class InscriptionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prenom: str = Field(max_length=100)
    nom: str = Field(max_length=100)
    pseudonyme: str = Field(max_length=60)
    identifiant: str = Field(max_length=60)
    mot_de_passe: str = Field(max_length=LONGUEUR_MAX_MOT_DE_PASSE)
    email: str | None = Field(default=None, max_length=254)
    classe: Classe
    # Les deux cases du formulaire : vérifiées ici, pas seulement par le site.
    charte: Literal[True]
    consentement_parent: Literal[True]
    etablissement_id: UUID | None = None
    proposition: Proposition | None = None

    @model_validator(mode="after")
    def un_seul_etablissement(self) -> InscriptionEntree:
        if (self.etablissement_id is None) == (self.proposition is None):
            raise ValueError("Choisis un établissement de la liste ou propose le tien")
        return self


class EtablissementEleve(BaseModel):
    id: UUID
    nom: str
    statut: StatutEtablissement
    iesg: str
    dre_code: str
    dre: str


class SemestreEleve(BaseModel):
    libelle: str
    debut: date
    fin: date


class LignePoints(BaseModel):
    libelle: str
    montant: int
    cree_le: datetime
    semestre: str | None


class PointsEleve(BaseModel):
    semestre: SemestreEleve | None
    points_semestre: int
    total: int
    lignes: list[LignePoints]


class EspaceEleve(BaseModel):
    pseudonyme: str
    classe: Classe
    email: str | None
    etablissement: EtablissementEleve
    version: int
    points: PointsEleve


class ProfilModification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Annotated[int, Field(ge=1)]
    classe: Classe | None = None
    etablissement_id: UUID | None = None
    # Une chaîne vide efface l'email.
    email: str | None = Field(default=None, max_length=254)
