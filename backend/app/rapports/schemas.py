"""Champs et réponses des rapports (spec 038). Un brouillon peut être incomplet : les champs obligatoires sont
vérifiés à la soumission (`manquants`). Aucun champ ne demande de nom d'élève."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from app.fichiers.youtube import identifiant_youtube
from app.rapports.models import ModeleRapport

Court = Annotated[str, Field(max_length=200)]
Texte = Annotated[str, Field(max_length=5000)]
Nombre = Annotated[int, Field(ge=0, le=100_000)]
Video = Annotated[str, Field(max_length=200), AfterValidator(identifiant_youtube)]
Videos = Annotated[list[Video], Field(max_length=5)]


class _Champs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Participants(_Champs):
    """Le nombre de participants et, si on le souhaite, une répartition agrégée : jamais de nom."""

    total: Nombre | None = None
    filles: Nombre | None = None
    garcons: Nombre | None = None
    eleves_club: Nombre | None = None
    autres: Nombre | None = None

    @model_validator(mode="after")
    def _repartition(self) -> Participants:
        total = self.total or 0
        if (self.filles or 0) + (self.garcons or 0) > total or (self.eleves_club or 0) + (self.autres or 0) > total:
            raise ValueError("La répartition des participants dépasse leur nombre total.")
        return self


class ChampsActivite(_Champs):
    titre: Court = ""
    axe_code: str | None = Field(default=None, max_length=40)
    type_activite: str | None = Field(default=None, max_length=40)
    date_activite: date | None = None
    lieu: Court = ""
    responsable: Court = ""
    contexte: Texte = ""
    objectifs: Texte = ""
    deroulement: Texte = ""
    resultats: Texte = ""
    difficultes: Texte = ""
    recommandations: Texte = ""
    participants: Participants = Participants()
    videos: Videos = []
    # L'événement de l'agenda que ce rapport documente (spec 041), facultatif.
    evenement_id: UUID | None = None


class ChampsMensuel(_Champs):
    mois: date | None = None
    titre: Court = ""
    synthese: Texte = ""
    analyse: Texte = ""
    difficultes: Texte = ""
    perspectives: Texte = ""
    videos: Videos = []

    @model_validator(mode="after")
    def _premier_du_mois(self) -> ChampsMensuel:
        if self.mois is not None:
            self.mois = self.mois.replace(day=1)
        return self


class ChampsBilan(_Champs):
    semestre_id: UUID | None = None
    titre: Court = ""
    synthese: Texte = ""
    resultats: Texte = ""
    analyse: Texte = ""
    recommandations: Texte = ""
    perspectives: Texte = ""
    participants_total: Nombre | None = None
    videos: Videos = []


SCHEMAS: dict[ModeleRapport, type[_Champs]] = {
    ModeleRapport.activite: ChampsActivite,
    ModeleRapport.mensuel: ChampsMensuel,
    ModeleRapport.bilan: ChampsBilan,
}

# Les champs à remplir avant de soumettre, avec leur nom pour le message.
OBLIGATOIRES: dict[ModeleRapport, dict[str, str]] = {
    ModeleRapport.activite: {
        "titre": "le titre", "axe_code": "l'axe", "type_activite": "le type d'activité",
        "date_activite": "la date", "lieu": "le lieu", "responsable": "le responsable", "objectifs": "les objectifs",
        "deroulement": "le déroulement", "resultats": "les résultats",
    },
    ModeleRapport.mensuel: {"mois": "le mois", "synthese": "la synthèse"},
    ModeleRapport.bilan: {"semestre_id": "le semestre", "synthese": "la synthèse", "resultats": "les résultats"},
}  # fmt: skip


def manquants(modele: ModeleRapport, champs: _Champs) -> list[str]:
    noms = [nom for cle, nom in OBLIGATOIRES[modele].items() if getattr(champs, cle) in (None, "")]
    if isinstance(champs, ChampsActivite) and not champs.participants.total:
        noms.append("le nombre de participants")
    return noms


def titre_de(modele: ModeleRapport, donnees: dict[str, object]) -> str:
    titre = str(donnees.get("titre") or "").strip()
    if titre:
        return titre
    return {
        ModeleRapport.activite: "Rapport d'activité",
        ModeleRapport.mensuel: "Rapport mensuel",
        ModeleRapport.bilan: "Bilan semestriel",
    }[modele]


# Entrées -------------------------------------------------------------------------------------------------------


class Creation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modele: ModeleRapport


class Modification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    donnees: dict[str, object]


class VersionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int


# Réponses ------------------------------------------------------------------------------------------------------

EtatRapport = Literal["brouillon", "soumis", "a_corriger", "approuve", "refuse"]


class ClubRapport(BaseModel):
    id: UUID
    nom: str


class Lecture(BaseModel):
    nom: str
    consulte_le: datetime | None


class RapportResume(BaseModel):
    id: UUID
    modele: ModeleRapport
    reference: str | None
    etat: EtatRapport
    titre: str
    periode: str | None
    club: ClubRapport
    auteur: str
    mien: bool
    soumis_le: datetime | None
    modifie_le: datetime
    points: int | None
    doublon_de: str | None
    # Les rapports approuvés comme doublons de celui-ci.
    doublons: list[str]
    lectures: list[Lecture]


class PhotoRapport(BaseModel):
    id: UUID
    legende: str | None


class DocumentRapport(BaseModel):
    id: UUID
    nom: str
    type: str
    octets: int


class DecisionRapport(BaseModel):
    decision: str
    motif: str | None
    decide_le: datetime
    version: int


class EvenementLie(BaseModel):
    id: UUID
    titre: str
    debut: datetime
    fin: datetime
    participants: int
    presents: int


class RapportDetail(RapportResume):
    version: int
    donnees: dict[str, object]
    photos: list[PhotoRapport]
    documents: list[DocumentRapport]
    historique: list[DecisionRapport]
    modifiable: bool
    doublons_probables: list[str]
    # L'événement de l'agenda lié (spec 041) : titre, dates, participants annoncés et présents pointés.
    evenement: EvenementLie | None = None


class TypeActivite(BaseModel):
    code: str
    libelle: str


class MesRapports(BaseModel):
    rapports: list[RapportResume]
    # Nul si l'utilisateur n'a plus de club en service : il garde la liste de ses rapports.
    club: ClubRapport | None
    modeles: list[ModeleRapport]


class SemestreRapport(BaseModel):
    id: UUID
    libelle: str
    debut: date
    fin: date


class LigneArchive(BaseModel):
    id: UUID
    reference: str | None
    modele: ModeleRapport
    etat: EtatRapport
    titre: str
    club: ClubRapport
    dre: str
    auteur: str
    periode: str | None
    type_activite: str | None
    soumis_le: datetime | None
    points_auteur: int | None
    points_club: int | None
    doublon_de: str | None


class PageArchive(BaseModel):
    total: int
    page: int
    par_page: int
    rapports: list[LigneArchive]
