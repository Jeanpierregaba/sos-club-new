from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.comptes.service import LONGUEUR_MAX_MOT_DE_PASSE
from app.eleves.models import Classe
from app.points.schemas import ResumePoints
from app.referentiel.schemas import EtablissementRattache, Proposition


class EtatInscription(BaseModel):
    ouvertes: bool
    version_charte: str


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


class EspaceEleve(BaseModel):
    pseudonyme: str
    classe: Classe
    email: str | None
    etablissement: EtablissementRattache
    version: int
    points: ResumePoints


class ProfilModification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Annotated[int, Field(ge=1)]
    classe: Classe | None = None
    etablissement_id: UUID | None = None
    # Une chaîne vide efface l'email.
    email: str | None = Field(default=None, max_length=254)
