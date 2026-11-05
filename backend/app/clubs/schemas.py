"""Schémas de l'API des clubs (spec 019)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from app.clubs.models import EtatClub
from app.referentiel.schemas import EtablissementRattache


def _motif(valeur: str) -> str:
    propre = " ".join(valeur.split())
    if len(propre) < 3:
        raise ValueError("Indique un motif d'au moins 3 caractères")
    return propre


Motif = Annotated[str, Field(max_length=500), AfterValidator(_motif)]


class EncadreurAssocie(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    telephone: str | None = Field(default=None, max_length=30)


class DemandeClubEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=300)
    axes: list[str] = Field(default_factory=list, max_length=3)
    encadreurs_associes: list[EncadreurAssocie] = Field(default_factory=list, max_length=10)
    # La case « je suis désigné président », vérifiée ici, pas seulement par le site.
    confirmation: Literal[True]

    @field_validator("nom")
    @classmethod
    def nom_non_vide(cls, valeur: str) -> str:
        return " ".join(valeur.split())


class DemandeClub(BaseModel):
    """Copie d'une demande dans la file d'un collaborateur."""

    id: UUID
    nom: str
    description: str | None
    axes: list[str]
    demandeur_pseudonyme: str
    etablissement: EtablissementRattache
    encadreurs_associes: list[EncadreurAssocie]
    etat: EtatClub
    demande_le: datetime
    decide_le: datetime | None
    motif_refus: str | None
    version: int


class FileClubs(BaseModel):
    total: int
    demandes: list[DemandeClub]


# Vues côté élève -------------------------------------------------------------------------------------------


class PassationApercu(BaseModel):
    id: UUID
    etat: str
    successeur_pseudonyme: str
    propose_le: datetime
    decide_le: datetime | None
    motif_refus: str | None
    version: int


class ClubResume(BaseModel):
    id: UUID
    nom: str
    description: str | None
    etablissement: EtablissementRattache
    axes: list[str]
    etat: str
    president: bool
    motif_refus: str | None = None
    version: int


class ClubPublic(BaseModel):
    id: UUID
    nom: str
    etablissement: EtablissementRattache
    axes: list[str]
    actif_le: datetime | None


class ClubFiche(BaseModel):
    id: UUID
    nom: str
    description: str | None
    etablissement: EtablissementRattache
    axes: list[str]
    actif_le: datetime | None


# Passation --------------------------------------------------------------------------------------------------


class PassationEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pseudonyme: str = Field(min_length=1, max_length=60)
    version: int = Field(ge=1)


class MonClub(BaseModel):
    club: ClubResume | None
    # La proposition de passation en attente, visible par le président sortant.
    passation: PassationApercu | None = None


class ActivationEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int | None = Field(default=None, ge=1)


class RefusEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Motif
    version: int | None = Field(default=None, ge=1)


class Passation(BaseModel):
    id: UUID
    club_id: UUID
    club_nom: str
    etablissement: EtablissementRattache
    successeur_pseudonyme: str
    president_sortant_pseudonyme: str
    etat: str
    propose_le: datetime
    decide_le: datetime | None
    motif_refus: str | None
    version: int


class FilePassations(BaseModel):
    total: int
    passations: list[Passation]


# Affiliations et rattachements (spec 020) --------------------------------------------------------------------


class AdhesionResume(BaseModel):
    """Une adhésion, vue par l'élève concerné : son état et, s'il y en a, les motifs de refus ou de retrait."""

    id: UUID
    club_id: UUID
    club_nom: str
    etat: Literal["en_attente_president", "en_attente_validation", "active", "refusee", "retiree"]
    demande_le: datetime
    motif_refus: str | None = None
    motif_retrait: str | None = None
    version: int


class DemandeAdhesion(BaseModel):
    """Une demande d'affiliation, vue par le président : le pseudonyme du demandeur, jamais son nom."""

    id: UUID
    pseudonyme: str
    classe: str
    demande_le: datetime
    version: int


class DecisionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)


class RefusDemandeEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Motif
    version: int = Field(ge=1)


class RetraitEntree(BaseModel):
    """Le retrait d'un membre par le président : le motif est facultatif."""

    model_config = ConfigDict(extra="forbid")

    motif: Annotated[str, Field(max_length=500)] | None = None
    version: int = Field(ge=1)


class RattachementResume(BaseModel):
    """Un rattachement, vu par l'encadreur concerné."""

    id: UUID
    club_id: UUID
    club_nom: str
    etat: Literal["en_attente_president", "en_attente_validation", "actif", "refuse", "retire"]
    # Au-delà du premier club, seule l'équipe nationale peut valider (Q16).
    supplementaire: bool
    demande_le: datetime
    motif_refus: str | None = None
    motif_retrait: str | None = None
    version: int


class DemandeRattachement(BaseModel):
    """Une demande de rattachement, vue par le président : un encadreur est un adulte identifié par son nom."""

    id: UUID
    prenom: str
    nom: str
    fonction: str
    etablissement: str
    demande_le: datetime
    version: int


class MesClubs(BaseModel):
    """L'espace « Mes clubs » d'un encadreur : ses rattachements en cours, puis les derniers terminés."""

    rattachements: list[RattachementResume]


class AffiliationAValider(BaseModel):
    """Une affiliation confirmée par le président, dans la file d'un collaborateur."""

    id: UUID
    pseudonyme: str
    classe: str
    club_id: UUID
    club_nom: str
    etablissement: str
    dre: str
    demande_le: datetime
    confirme_le: datetime | None
    version: int


class RattachementAValider(BaseModel):
    """Un rattachement confirmé par le président, dans la file d'un collaborateur."""

    id: UUID
    prenom: str
    nom: str
    fonction: str
    etablissement_encadreur: str
    club_id: UUID
    club_nom: str
    club_etablissement: str
    dre: str
    supplementaire: bool
    # Faux pour un collaborateur de DRE devant un club supplémentaire : seule l'équipe nationale décide (Q16).
    decidable: bool
    demande_le: datetime
    confirme_le: datetime | None
    version: int


class FileAffiliations(BaseModel):
    total: int
    demandes: list[AffiliationAValider]


class FileRattachements(BaseModel):
    total: int
    demandes: list[RattachementAValider]


class ElementLot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    version: int = Field(ge=1)


class LotEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    elements: list[ElementLot] = Field(min_length=1, max_length=100)


class LotRefusEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    elements: list[ElementLot] = Field(min_length=1, max_length=100)
    motif: Motif


class EchecLot(BaseModel):
    id: UUID
    message: str


class ResultatLot(BaseModel):
    """Chaque demande d'un lot est traitée à part : celles qui échouent n'empêchent pas les autres."""

    reussies: list[UUID]
    echecs: list[EchecLot]
