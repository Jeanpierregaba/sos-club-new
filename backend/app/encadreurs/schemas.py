import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.comptes.service import LONGUEUR_MAX_MOT_DE_PASSE
from app.encadreurs.models import EtatVerification, Fonction
from app.points.schemas import ResumePoints
from app.referentiel.schemas import EtablissementRattache, Proposition

SEPARATEURS = re.compile(r"[\s().-]")
FORMAT_TELEPHONE = re.compile(r"\+?[0-9]{8,15}")


def normaliser_telephone(valeur: str | None) -> str | None:
    """« +228 90 12-34-56 » devient « +22890123456 ». Un champ vide redevient nul."""
    if valeur is None:
        return None
    propre = SEPARATEURS.sub("", valeur)
    if not propre:
        return None
    if not FORMAT_TELEPHONE.fullmatch(propre):
        raise ValueError("Ce téléphone n'est pas valide : de 8 à 15 chiffres, avec « + » au début si besoin")
    return propre


def _precision(valeur: str | None) -> str | None:
    if valeur is None:
        return None
    return " ".join(valeur.split()) or None


def _motif(valeur: str) -> str:
    propre = " ".join(valeur.split())
    if len(propre) < 3:
        raise ValueError("Indique un motif d'au moins 3 caractères")
    return propre


Motif = Annotated[str, Field(max_length=500), AfterValidator(_motif)]
Telephone = Annotated[str | None, Field(max_length=30), AfterValidator(normaliser_telephone)]
Precision = Annotated[str | None, Field(max_length=100), AfterValidator(_precision)]


# Inscription et espace de l'encadreur ---------------------------------------------------------------------------


class InscriptionEncadreur(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prenom: str = Field(max_length=100)
    nom: str = Field(max_length=100)
    email: str = Field(max_length=254)
    telephone: Telephone = None
    identifiant: str = Field(max_length=60)
    mot_de_passe: str = Field(max_length=LONGUEUR_MAX_MOT_DE_PASSE)
    fonction: Fonction
    fonction_precision: Precision = None
    # Les deux cases du formulaire : vérifiées ici, pas seulement par le site.
    charte: Literal[True]
    consentement: Literal[True]
    etablissement_id: UUID | None = None
    proposition: Proposition | None = None

    @model_validator(mode="after")
    def coherent(self) -> InscriptionEncadreur:
        if (self.etablissement_id is None) == (self.proposition is None):
            raise ValueError("Choisis un établissement de la liste ou propose le tien")
        if self.fonction is Fonction.autre and not self.fonction_precision:
            raise ValueError("Précise ta fonction")
        if self.fonction is not Fonction.autre:
            self.fonction_precision = None
        return self


class EspaceEncadreur(BaseModel):
    etat: EtatVerification
    demande_le: datetime
    decide_le: datetime | None
    motif_refus: str | None
    fonction: Fonction
    fonction_precision: str | None
    email: str | None
    telephone: str | None
    etablissement: EtablissementRattache
    version: int
    # Seulement pour un compte actif : rien n'est gagné avant la vérification.
    points: ResumePoints | None


class ProfilEncadreurModification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Annotated[int, Field(ge=1)]
    # Une chaîne vide efface le téléphone.
    telephone: Telephone = None
    etablissement_id: UUID | None = None
    fonction: Fonction | None = None
    fonction_precision: Precision = None


# Vérification par l'espace admin -------------------------------------------------------------------------------


class DemandeEncadreur(BaseModel):
    """Une ligne de la file : tout ce qu'il faut pour vérifier la personne, sans ouvrir sa fiche."""

    id: UUID
    identifiant: str
    prenom: str
    nom: str
    email: str | None
    telephone: str | None
    fonction: Fonction
    fonction_precision: str | None
    etablissement: EtablissementRattache
    etat: EtatVerification
    demande_le: datetime
    decide_le: datetime | None
    motif_refus: str | None
    # Celle du profil vérifié : l'activation la renvoie, pour ne pas activer un profil modifié entre-temps.
    version: int


class FileEncadreurs(BaseModel):
    total: int
    demandes: list[DemandeEncadreur]


class ActivationEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Annotated[int, Field(ge=1)] | None = None


class RefusEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Motif
    # Celle du profil vérifié : même garde-fou qu'à l'activation.
    version: Annotated[int, Field(ge=1)] | None = None
