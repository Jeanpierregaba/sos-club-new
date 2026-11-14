"""Schémas de l'API des clubs (spec 019)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.articles.schemas import ResumeArticle, ResumeArticleAuteur
from app.eleves.models import Classe
from app.encadreurs.models import Fonction
from app.moderation.models import EtatContenu
from app.referentiel.schemas import EtablissementRattache


def _motif(valeur: str) -> str:
    propre = " ".join(valeur.split())
    if len(propre) < 3:
        raise ValueError("Indique un motif d'au moins 3 caractères")
    return propre


Motif = Annotated[str, Field(max_length=500), AfterValidator(_motif)]


# Vues côté élève -------------------------------------------------------------------------------------------


class PassationApercu(BaseModel):
    id: UUID
    # en_attente_encadreur (Q19, spec 020), en_attente (l'admin), validee, refusee.
    etat: str
    successeur_pseudonyme: str
    propose_le: datetime
    # La confirmation par un encadreur rattaché, s'il y en a un.
    confirmee_le: datetime | None = None
    decide_le: datetime | None
    motif_refus: str | None
    version: int


# Statut d'un club tel qu'on le montre (spec 033) : l'échéance passée d'une régularisation se lit « suspendu ».
StatutClub = Literal["en_constitution", "actif", "en_regularisation", "suspendu"]


class ClubResume(BaseModel):
    """Le club de l'établissement de l'élève, vu par lui (spec 033)."""

    id: UUID
    nom: str
    description: str | None
    etablissement: EtablissementRattache
    axes: list[str]
    statut: StatutClub
    actif_le: datetime | None
    regularisation_jusquau: datetime | None
    president: bool
    version: int


class ClubPublic(BaseModel):
    id: UUID
    nom: str
    etablissement: EtablissementRattache
    axes: list[str]
    statut: StatutClub
    actif_le: datetime | None


class ClubFiche(BaseModel):
    id: UUID
    nom: str
    description: str | None
    etablissement: EtablissementRattache
    axes: list[str]
    statut: StatutClub
    actif_le: datetime | None
    # Les dernières actualités publiées du club (spec 026).
    actualites: list[ResumeArticle] = []


# Passation --------------------------------------------------------------------------------------------------


class PassationEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pseudonyme: str = Field(min_length=1, max_length=60)
    version: int = Field(ge=1)


class MonClub(BaseModel):
    club: ClubResume | None
    # L'affiliation en cours de l'élève, sinon la dernière terminée (motif lisible).
    affiliation: AdhesionResume | None = None
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


class DecisionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)


class RefusDemandeEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Motif
    version: int = Field(ge=1)


class PassationAConfirmer(BaseModel):
    """Une passation qu'un encadreur rattaché au club doit confirmer (Q19)."""

    id: UUID
    club_id: UUID
    club_nom: str
    successeur_pseudonyme: str
    president_sortant_pseudonyme: str
    propose_le: datetime
    version: int


class AffiliationAValider(BaseModel):
    """Une affiliation à confirmer, dans la file d'un collaborateur (à la place d'un encadreur du club)."""

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


class FileAffiliations(BaseModel):
    total: int
    demandes: list[AffiliationAValider]


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


class MembreClub(BaseModel):
    """Un membre, dans la liste du club : son pseudonyme seulement, jamais son nom ni sa classe (docs/RULES.md).
    `id` et `version` sont ceux de l'adhésion : le président s'en sert pour retirer un membre."""

    id: UUID
    pseudonyme: str
    depuis: datetime
    president: bool
    version: int


class EncadreurDuClub(BaseModel):
    """Un encadreur rattaché au club : un adulte, identifié par son nom et sa fonction."""

    id: UUID
    prenom: str
    nom: str
    fonction: str
    version: int


class MembresDuClub(BaseModel):
    membres: list[MembreClub]
    encadreurs: list[EncadreurDuClub]


class ClubPodium(BaseModel):
    """Un club du podium de l'accueil (spec 021) : public, sans aucun élève."""

    rang: int
    id: UUID
    nom: str
    etablissement: str
    dre: str
    # Demi-points possibles : la moitié de chaque gain d'un élève (spec 034).
    points: float


# Espace du président (spec 026) -----------------------------------------------------------------------------


class PropositionFicheEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=300)] = None
    axes: Annotated[list[str], Field(min_length=1, max_length=3)]

    @field_validator("description")
    @classmethod
    def _vide(cls, valeur: str | None) -> str | None:
        return valeur or None

    @field_validator("axes")
    @classmethod
    def _uniques(cls, valeur: list[str]) -> list[str]:
        if len(set(valeur)) != len(valeur):
            raise ValueError("Chaque axe ne compte qu'une fois.")
        return valeur


class PropositionFiche(BaseModel):
    id: UUID
    etat: EtatContenu
    description: str | None
    axes: list[str]
    motif: str | None
    soumis_le: datetime | None
    version: int


class ClubEspace(BaseModel):
    id: UUID
    nom: str
    description: str | None
    etablissement: EtablissementRattache
    axes: list[str]
    actif_le: datetime | None


class IndicateursClub(BaseModel):
    membres: int
    encadreurs: int
    actualites: int


class SuiviClub(BaseModel):
    propositions: list[PropositionFiche]
    actualites: list[ResumeArticleAuteur]


class EspaceClub(BaseModel):
    """La vue « Mon club » : le suivi pour le président seul ; la lecture pour les membres et les encadreurs
    rattachés."""

    club: ClubEspace
    statut: StatutClub
    role: Literal["president", "membre", "encadreur"]
    indicateurs: IndicateursClub
    actualites: list[ResumeArticle]
    membres: MembresDuClub
    suivi: SuiviClub | None


# « Mon Club Santé » de l'encadreur (spec 033) ----------------------------------------------------------------


class Seuils(BaseModel):
    encadreurs: int
    eleves: int
    delai_jours: int


class MembreEquipe(BaseModel):
    """Un encadreur du club, vu par les autres encadreurs : un adulte identifié par son nom."""

    utilisateur_id: UUID
    prenom: str
    nom: str
    fonction: Fonction
    moi: bool
    # Un signalement de désistement attend l'équipe pour lui.
    signalement_en_attente: bool


class SignalementResume(BaseModel):
    id: UUID
    encadreur_prenom: str
    encadreur_nom: str
    motif: str
    etat: Literal["en_attente", "confirme", "rejete"]
    signale_le: datetime
    decide_le: datetime | None
    motif_decision: str | None


class MonClubSante(BaseModel):
    id: UUID
    nom: str
    etablissement: EtablissementRattache
    statut: StatutClub
    actif_le: datetime | None
    regularisation_jusquau: datetime | None
    declare_terrain: bool
    seuils: Seuils
    nb_encadreurs: int
    nb_eleves: int
    a_confirmer: int
    equipe: list[MembreEquipe]
    president_pseudonyme: str | None
    # La proposition de président (ou passation) en attente de l'équipe, s'il y en a une.
    president_propose: str | None
    passations_a_confirmer: list[PassationAConfirmer]
    mes_signalements: list[SignalementResume]


class AffiliationDuClub(BaseModel):
    """Un élève du club, vu par ses encadreurs : pseudonyme et classe seulement (décision 4 de la spec 033)."""

    id: UUID
    pseudonyme: str
    classe: Classe
    etat: Literal["en_attente_validation", "active"]
    demande_le: datetime
    depuis: datetime | None
    president: bool
    version: int


class AffiliationsDuClub(BaseModel):
    a_confirmer: list[AffiliationDuClub]
    confirmees: list[AffiliationDuClub]


class DesistementEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    encadreur_id: UUID
    motif: Motif


class PresidentEntree(BaseModel):
    """L'élève proposé comme président, désigné par son affiliation confirmée."""

    model_config = ConfigDict(extra="forbid")

    affiliation_id: UUID


# Suivi des clubs par l'équipe (spec 033) ---------------------------------------------------------------------


class ClubSuivi(BaseModel):
    id: UUID
    nom: str
    etablissement: str
    iesg: str
    dre: str
    region: str
    statut: StatutClub
    nb_encadreurs: int
    nb_eleves: int
    a_confirmer: int
    actif_le: datetime | None
    regularisation_jusquau: datetime | None
    declare_terrain: bool


class PageSuivi(BaseModel):
    total: int
    page: int
    par_page: int
    clubs: list[ClubSuivi]


class LigneJournalClub(BaseModel):
    ancien: str | None
    nouveau: str
    cause: str
    nb_encadreurs: int
    nb_eleves: int
    cree_le: datetime


class EleveDuClub(BaseModel):
    pseudonyme: str
    classe: str


class EncadreurSuivi(BaseModel):
    utilisateur_id: UUID
    prenom: str
    nom: str
    fonction: str


class SignalementAdmin(BaseModel):
    id: UUID
    club_id: UUID
    club_nom: str
    dre: str
    encadreur_prenom: str
    encadreur_nom: str
    signale_par: str | None
    motif: str
    etat: Literal["en_attente", "confirme", "rejete"]
    signale_le: datetime
    decide_le: datetime | None
    motif_decision: str | None
    version: int


class FicheSuivi(BaseModel):
    club: ClubSuivi
    declare_note: str | None
    declare_le: datetime | None
    president_pseudonyme: str | None
    encadreurs: list[EncadreurSuivi]
    eleves: list[EleveDuClub]
    journal: list[LigneJournalClub]
    signalements: list[SignalementAdmin]
    version: int


class FileDesistements(BaseModel):
    total: int
    signalements: list[SignalementAdmin]


class TerrainEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    declare: bool
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None
    version: int = Field(ge=1)


class DecisionSignalementEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)


class RejetSignalementEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Motif
    version: int = Field(ge=1)


# Carte nationale publique (spec 033) : aucun contact, aucun nom, aucun effectif nominatif ----------------------

# Statut public d'un établissement : sans club (ou club sans membre confirmé) « reference » ; une régularisation se
# montre « actif » (le club fonctionne encore).
StatutCarte = Literal["reference", "en_constitution", "actif", "suspendu"]


class CarteEtablissement(BaseModel):
    id: UUID
    nom: str
    localite: str | None
    statut: StatutCarte
    declare_terrain: bool
    club_id: UUID | None


class CarteIesg(BaseModel):
    id: UUID
    nom: str
    zone: str | None
    nb_etablissements: int
    nb_clubs: int
    nb_actifs: int
    etablissements: list[CarteEtablissement]


class CarteDre(BaseModel):
    code: str
    nom: str
    nom_complet: str
    nb_etablissements: int
    nb_clubs: int
    nb_actifs: int
    iesg: list[CarteIesg]


class CarteRegion(BaseModel):
    code: str
    nom: str
    nb_etablissements: int
    nb_clubs: int
    nb_actifs: int
    dres: list[CarteDre]


class ChiffresCarte(BaseModel):
    # Établissements du référentiel officiel.
    etablissements: int
    # Clubs existants : déclarés sur le terrain, ou ayant atteint une fois le seuil (actifs, en régularisation,
    # suspendus), chacun compté une fois.
    clubs: int
    # Clubs actifs sur la plateforme (actifs ou en régularisation).
    clubs_actifs: int


class Carte(BaseModel):
    chiffres: ChiffresCarte
    regions: list[CarteRegion]
