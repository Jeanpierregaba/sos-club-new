from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.admin.catalogue import Action, RoleDepart
from app.admin.models import FormatExport, StatutExport, TypeExport
from app.comptes.models import Role, StatutCompte

Motif = Field(min_length=3, max_length=500)


class Droit(BaseModel):
    module: str
    action: Action


class AdminMoi(BaseModel):
    id: UUID
    identifiant: str
    prenom: str
    nom: str
    email: str | None
    super_admin: bool
    perimetre_dre: str | None
    droits: list[Droit]
    double_auth_active: bool
    double_auth_requise: bool


class ModuleCatalogue(BaseModel):
    id: str
    libelle: str
    disponible: bool
    actions: list[Action]


class RoleCatalogue(BaseModel):
    id: RoleDepart
    libelle: str
    droits: list[Droit]


class Catalogue(BaseModel):
    modules: list[ModuleCatalogue]
    actions: dict[Action, str]
    sensibles: list[Droit]
    roles: list[RoleCatalogue]
    # Toutes les DRE du référentiel pour afficher un périmètre ; les actives seules pour en choisir un (spec 016).
    dre: dict[str, str]
    dre_actives: list[str]


# Double authentification ------------------------------------------------------------------------------------


class Enrolement(BaseModel):
    secret: str
    qr_svg: str


class CodeSaisi(BaseModel):
    code: str = Field(min_length=6, max_length=40)


class CodesSecours(BaseModel):
    codes: list[str]


# Collaborateurs ---------------------------------------------------------------------------------------------

StatutCollaborateur = Literal["invitation_envoyee", "invitation_expiree", "actif", "suspendu", "revoque"]


class InvitationEntree(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    prenom: str = Field(min_length=1, max_length=100)
    nom: str = Field(min_length=1, max_length=100)
    role_depart: RoleDepart | None = None
    perimetre_dre: str | None = None
    fin_acces: datetime | None = None
    droits: list[Droit] = []


class DroitsEntree(BaseModel):
    droits: list[Droit]
    perimetre_dre: str | None = None
    fin_acces: datetime | None = None
    motif: str = Motif


class MotifEntree(BaseModel):
    motif: str = Motif


class CollaborateurResume(BaseModel):
    id: UUID
    email: str
    prenom: str
    nom: str
    identifiant: str | None
    role_depart: RoleDepart | None
    perimetre_dre: str | None
    super_admin: bool
    statut: StatutCollaborateur
    fin_acces: datetime | None
    double_auth_active: bool
    nb_droits_sensibles: int
    revu_le: datetime | None
    cree_le: datetime


class CollaborateurDetail(CollaborateurResume):
    droits: list[Droit]
    invitation_expire_le: datetime | None
    invitation_envoi: str | None


class InvitationCree(BaseModel):
    collaborateur: CollaborateurDetail
    # Hors production et sans SMTP seulement : le lien à transmettre soi-même.
    lien_de_test: str | None = None


class ActivationInfo(BaseModel):
    prenom: str
    email: str
    double_auth_requise: bool


class JetonEntree(BaseModel):
    jeton: str = Field(min_length=1, max_length=100)


class ActivationEntree(BaseModel):
    jeton: str = Field(min_length=1, max_length=100)
    identifiant: str = Field(min_length=3, max_length=30)
    mot_de_passe: str = Field(min_length=8, max_length=256)


# Inscrits ---------------------------------------------------------------------------------------------------


class Inscrit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    identifiant: str
    prenom: str
    nom: str
    email: str | None
    telephone: str | None
    role: Role
    statut: StatutCompte
    consentement_le: datetime | None
    cree_le: datetime


class PageInscrits(BaseModel):
    total: int
    page: int
    par_page: int
    inscrits: list[Inscrit]


class EvenementJournal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quand: datetime
    auteur_id: UUID | None
    auteur_libelle: str | None
    action: str
    cible_type: str | None
    cible_id: str | None
    perimetre: str | None
    details: dict[str, Any]


class InscritDetail(Inscrit):
    historique: list[EvenementJournal]


class PageJournal(BaseModel):
    total: int
    page: int
    par_page: int
    evenements: list[EvenementJournal]


# Exports ----------------------------------------------------------------------------------------------------

Colonne = Literal[
    "identifiant", "nom", "prenom", "email", "telephone", "profil", "statut", "date_inscription", "consentement"
]


class FiltresInscrits(BaseModel):
    recherche: str | None = Field(default=None, max_length=100)
    profil: Role | None = None
    statut: StatutCompte | None = None
    inscrit_depuis: datetime | None = None
    inscrit_avant: datetime | None = None


class ExportEntree(BaseModel):
    type: TypeExport
    format: FormatExport
    filtres: FiltresInscrits = FiltresInscrits()
    colonnes: list[Colonne] = []
    finalite: str | None = Field(default=None, max_length=500)


class Apercu(BaseModel):
    nb_lignes: int
    plafond: int


class ExportResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: TypeExport
    format: FormatExport
    filtres: dict[str, Any]
    colonnes: list[str]
    finalite: str | None
    nb_lignes: int
    statut: StatutExport
    demandeur_libelle: str | None = None
    lien_expire_le: datetime
    telecharge_le: datetime | None
    cree_le: datetime


class ExportCree(BaseModel):
    export: ExportResume
    # À appeler tel quel : le jeton ne sert qu'une fois et seulement pendant 15 minutes.
    lien: str


# Tableau de bord --------------------------------------------------------------------------------------------


class Indicateur(BaseModel):
    id: str
    libelle: str
    valeur: int | None
    # Pour un module à venir : la valeur reste nulle, jamais inventée.
    disponible_avec: str | None = None


class TableauDeBord(BaseModel):
    calcule_le: datetime
    comptes_par_profil: dict[Role, int]
    comptes_par_statut: dict[StatutCompte, int]
    inscriptions_30_jours: list[tuple[str, int]]
    indicateurs: list[Indicateur]
    derniers_evenements: list[EvenementJournal] | None
