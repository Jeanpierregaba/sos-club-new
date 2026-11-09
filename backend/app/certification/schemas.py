"""Schémas de la certification (spec 029) : « Ma certification » du joueur, la vérification publique et la
gestion par l'équipe."""

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.certification.models import EtatCertificat
from app.encadreurs.models import Fonction

EtatPlace = Literal["verrouillee", "ouverte", "reussie", "bientot"]


# Le joueur --------------------------------------------------------------------------------------------------------


class Fascicule(BaseModel):
    id: UUID
    titre: str


class PlaceParcours(BaseModel):
    place: int
    etat: EtatPlace
    # Le quiz publié sur cette place ; nul s'il n'y en a pas (« bientôt », ou place réussie sur un quiz retiré).
    quiz_id: UUID | None
    titre: str | None
    description: str | None
    contenu_de_test: bool
    fascicule: Fascicule | None
    meilleur_score: int | None
    tentatives_restantes: int | None
    tentative_en_cours: UUID | None


class BadgeParcours(BaseModel):
    rang: int
    nom: str
    palier: int
    obtenu_le: datetime | None


class CertificatJoueur(BaseModel):
    numero: str
    etat: EtatCertificat
    delivre_le: datetime


class MaCertification(BaseModel):
    reussies: int
    places: list[PlaceParcours]
    badges: list[BadgeParcours]
    certificat: CertificatJoueur | None
    nb_questions: int
    seuil: int


# Public -----------------------------------------------------------------------------------------------------------


class TitulaireEleve(BaseModel):
    type: Literal["eleve"] = "eleve"
    pseudonyme: str
    club: str | None


class TitulaireEncadreur(BaseModel):
    type: Literal["encadreur"] = "encadreur"
    prenom: str
    initiale: str
    fonction: Fonction


class Verification(BaseModel):
    numero: str
    etat: EtatCertificat
    delivre_le: datetime
    titulaire: TitulaireEleve | TitulaireEncadreur
    # Le numéro qui remplace un certificat réémis.
    remplace_par: str | None


# Gestion ----------------------------------------------------------------------------------------------------------

NomBadge = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class ReglesEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    noms: Annotated[list[NomBadge], Field(min_length=5, max_length=5)]
    paliers: Annotated[list[Annotated[int, Field(ge=1, le=12)]], Field(min_length=5, max_length=5)]

    @model_validator(mode="after")
    def coherentes(self) -> Self:
        if any(a >= b for a, b in zip(self.paliers, self.paliers[1:], strict=False)):
            raise ValueError("Les paliers doivent être strictement croissants.")
        if self.paliers[-1] != 12:
            raise ValueError("Le dernier badge se délivre à la réussite des 12 quiz.")
        if len({n.casefold() for n in self.noms}) != 5:
            raise ValueError("Deux badges portent le même nom.")
        return self


class ReglesSortie(BaseModel):
    version: int
    noms: list[str]
    paliers: list[int]
    cree_le: datetime


class HistoriqueRegles(BaseModel):
    en_cours: ReglesSortie
    versions: list[ReglesSortie]


class CertificatGestion(BaseModel):
    id: UUID
    numero: str
    etat: EtatCertificat
    role: str
    # Vue interne de l'équipe : le nom figé à la délivrance.
    titulaire: str
    utilisateur_id: UUID
    club: str | None
    delivre_le: datetime
    motif: str | None
    decide_le: datetime | None
    remplace_numero: str | None


class ListeCertificats(BaseModel):
    certificats: list[CertificatGestion]


class BadgeGestion(BaseModel):
    titulaire: str
    role: str
    nom: str
    palier: int
    obtenu_le: datetime


class ListeBadges(BaseModel):
    badges: list[BadgeGestion]


class Motif(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
