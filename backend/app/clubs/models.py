"""Clubs et présidence (spec 019) : demande, validation, fiche publique, passation.
Affiliations des élèves et rattachements des encadreurs (spec 020).

Un club est une entité collective rattachée à un établissement : il n'a jamais de compte. Son président,
un élève, le gère avec son compte. Aucune ligne de points n'est écrite ici : le score du club viendra
avec les specs qui en créditent (quiz, publications, rapports).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


def _enum_texte(enum: type[StrEnum], nom: str, longueur: int = 20) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=longueur)


class EtatClub(StrEnum):
    # Statuts calculés par `clubs/activation.py` (spec 033, ADR-0011).
    en_constitution = "en_constitution"
    actif = "actif"
    en_regularisation = "en_regularisation"
    suspendu = "suspendu"
    # Anciens statuts de la spec 019 (demande du président), gardés pour l'historique : aucune ligne nouvelle.
    en_attente = "en_attente"
    refuse = "refuse"


# Un club « vivant » : un seul par établissement. « En service » : il publie et gagne des points.
CLUB_VIVANT = (EtatClub.en_constitution, EtatClub.actif, EtatClub.en_regularisation, EtatClub.suspendu)
CLUB_EN_SERVICE = (EtatClub.actif, EtatClub.en_regularisation)


class EtatPassation(StrEnum):
    # Q19 (spec 020) : si le club a un encadreur rattaché, celui-ci confirme le successeur avant l'admin.
    en_attente_encadreur = "en_attente_encadreur"
    en_attente = "en_attente"
    validee = "validee"
    refusee = "refusee"


# Une passation en attente : de la confirmation de l'encadreur rattaché (Q19), puis de la décision de l'admin.
PASSATION_EN_ATTENTE = (EtatPassation.en_attente_encadreur, EtatPassation.en_attente)


class Club(Suivi, Base):
    __tablename__ = "club"
    __table_args__ = (
        # Un refus porte toujours un motif ; aucun autre état n'en a.
        CheckConstraint("(etat = 'refuse') = (motif_refus IS NOT NULL)", name="motif_si_refuse"),
        CheckConstraint(
            "(etat = 'en_regularisation') = (regularisation_jusquau IS NOT NULL)", name="echeance_si_regularisation"
        ),
        # Un seul club vivant par établissement : la base tranche, même entre deux créations simultanées.
        Index(
            "uq_club_par_etablissement",
            "etablissement_id",
            unique=True,
            postgresql_where="etat IN ('en_constitution', 'actif', 'en_regularisation', 'suspendu')",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    etablissement_id: Mapped[UUID] = mapped_column(ForeignKey("etablissement.id", ondelete="RESTRICT"), index=True)
    nom: Mapped[str] = mapped_column(String(150))
    # Sans accents, majuscules ni ponctuation : « Club Santé de Tokoin » et « club sante de to-k oin » se confondent.
    nom_normalise: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(String(300))
    # L'élève qui avait demandé le club (spec 019) ; nul pour un club créé par le système (spec 033).
    demandeur_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    # Gestionnaire courant : posé à l'activation, nul tant que la demande est en attente.
    president_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    # Encadreurs associés cités à titre déclaratif : jamais des comptes, jamais des droits.
    encadreurs_associes: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    etat: Mapped[EtatClub] = mapped_column(
        _enum_texte(EtatClub, "etat_club"),
        default=EtatClub.en_constitution,
        server_default=EtatClub.en_constitution.value,
    )
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    demande_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Première activation : elle reste quand le club passe ensuite en régularisation ou suspendu.
    actif_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Échéance de la régularisation (J+15) ; nulle hors de ce statut.
    regularisation_jusquau: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Rappels de la régularisation en cours déjà envoyés (J+7, J+14) : 0, 1 ou 2.
    rappels_envoyes: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"))
    # Club existant sur le terrain, posé par l'équipe : une information à part, qui ne donne aucun accès.
    declare_terrain: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    declare_note: Mapped[str | None] = mapped_column(String(300))
    declare_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    declare_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class ClubStatut(Base):
    """Journal des statuts d'un club (spec 033) : une ligne par changement, jamais modifiée."""

    __tablename__ = "club_statut"
    __table_args__ = (Index("ix_club_statut_club_id_cree_le", "club_id", "cree_le"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"))
    # Nul à la création du club.
    ancien: Mapped[EtatClub | None] = mapped_column(_enum_texte(EtatClub, "etat_club_ancien"))
    nouveau: Mapped[EtatClub] = mapped_column(_enum_texte(EtatClub, "etat_club_nouveau"))
    # L'événement déclencheur : `affiliation_confirmee`, `desistement_confirme`, `echeance`, `migration`…
    cause: Mapped[str] = mapped_column(String(40))
    nb_encadreurs: Mapped[int] = mapped_column(SmallInteger)
    nb_eleves: Mapped[int] = mapped_column(Integer)
    # Nul quand le système agit seul (échéance, migration).
    par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EtatSignalement(StrEnum):
    en_attente = "en_attente"
    confirme = "confirme"
    rejete = "rejete"


class SignalementDesistement(Suivi, Base):
    """Un encadreur signale qu'un autre encadreur du club s'est désisté ; l'équipe confirme ou rejette (spec 033)."""

    __tablename__ = "signalement_desistement"
    __table_args__ = (
        CheckConstraint("signale_par <> encadreur_id", name="pas_soi_meme"),
        CheckConstraint("(etat = 'en_attente') = (decide_le IS NULL)", name="decision_datee"),
        CheckConstraint("(etat = 'rejete') = (motif_decision IS NOT NULL)", name="motif_si_rejete"),
        Index(
            "uq_signalement_en_attente",
            "club_id",
            "encadreur_id",
            unique=True,
            postgresql_where="etat = 'en_attente'",
        ),
        Index("ix_signalement_desistement_etat", "etat"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"), index=True)
    # L'encadreur visé.
    encadreur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    signale_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif: Mapped[str] = mapped_column(String(500))
    signale_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    etat: Mapped[EtatSignalement] = mapped_column(
        _enum_texte(EtatSignalement, "etat_signalement"),
        default=EtatSignalement.en_attente,
        server_default=EtatSignalement.en_attente.value,
    )
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motif_decision: Mapped[str | None] = mapped_column(String(500))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class ClubAxe(Base):
    __tablename__ = "club_axe"

    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"), primary_key=True)
    axe_code: Mapped[str] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"), primary_key=True)


class ClubPassation(Suivi, Base):
    __tablename__ = "club_passation"
    __table_args__ = (
        CheckConstraint("(etat = 'refusee') = (motif_refus IS NOT NULL)", name="motif_si_refusee"),
        # Une seule proposition en attente par club, qu'elle attende l'encadreur ou l'admin.
        Index(
            "uq_club_passation_en_attente",
            "club_id",
            unique=True,
            postgresql_where="etat IN ('en_attente_encadreur', 'en_attente')",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"), index=True)
    # L'élève proposé, du même établissement.
    successeur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    # Le président sortant qui propose.
    propose_par: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    propose_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    etat: Mapped[EtatPassation] = mapped_column(
        _enum_texte(EtatPassation, "etat_passation"),
        default=EtatPassation.en_attente,
        server_default=EtatPassation.en_attente.value,
    )
    # L'encadreur rattaché qui a confirmé le successeur (Q19) ; nul quand le club n'a pas d'encadreur rattaché.
    confirmee_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    confirmee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


# Affiliations et rattachements (spec 020) --------------------------------------------------------------------
# Une demande passe par le président (confirmer ou refuser), puis par un collaborateur (valider ou refuser).
# Un lien actif peut être retiré par son titulaire ou par le président. Refus et retrait sont définitifs pour
# la ligne : une nouvelle demande crée une nouvelle ligne, et l'historique reste.


class EtatAdhesion(StrEnum):
    en_attente_president = "en_attente_president"
    en_attente_validation = "en_attente_validation"
    active = "active"
    refusee = "refusee"
    retiree = "retiree"


class EtatRattachement(StrEnum):
    en_attente_president = "en_attente_president"
    en_attente_validation = "en_attente_validation"
    actif = "actif"
    refuse = "refuse"
    retire = "retire"


ADHESION_EN_COURS = (EtatAdhesion.en_attente_president, EtatAdhesion.en_attente_validation, EtatAdhesion.active)
RATTACHEMENT_EN_COURS = (
    EtatRattachement.en_attente_president,
    EtatRattachement.en_attente_validation,
    EtatRattachement.actif,
)


class Adhesion(Suivi, Base):
    """L'affiliation d'un élève au club de son établissement."""

    __tablename__ = "adhesion"
    __table_args__ = (
        CheckConstraint("(etat = 'refusee') = (motif_refus IS NOT NULL)", name="motif_si_refusee"),
        # Une seule adhésion en cours par élève, tous clubs confondus : la base tranche entre deux demandes
        # simultanées. Après un refus ou un retrait, une nouvelle demande reste possible.
        Index(
            "uq_adhesion_en_cours_par_eleve",
            "eleve_id",
            unique=True,
            postgresql_where="etat IN ('en_attente_president', 'en_attente_validation', 'active')",
        ),
        # Les files du président et des collaborateurs se lisent par club et par état.
        Index("ix_adhesion_club_id_etat", "club_id", "etat"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    eleve_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"), index=True)
    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"))
    etat: Mapped[EtatAdhesion] = mapped_column(
        _enum_texte(EtatAdhesion, "etat_adhesion", 25),
        default=EtatAdhesion.en_attente_president,
        server_default=EtatAdhesion.en_attente_president.value,
    )
    demande_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Le président qui a confirmé la demande.
    confirme_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirme_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    # Le président ou le collaborateur qui a pris la décision finale (validation ou refus).
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    # Le retrait : par l'élève lui-même ou par le président (motif facultatif).
    retire_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retire_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_retrait: Mapped[str | None] = mapped_column(String(500))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class Rattachement(Suivi, Base):
    """Le rattachement d'un encadreur à un club ; un encadreur peut en avoir plusieurs (Q16)."""

    __tablename__ = "rattachement"
    __table_args__ = (
        CheckConstraint("(etat = 'refuse') = (motif_refus IS NOT NULL)", name="motif_si_refuse"),
        Index(
            "uq_rattachement_en_cours",
            "encadreur_id",
            "club_id",
            unique=True,
            postgresql_where="etat IN ('en_attente_president', 'en_attente_validation', 'actif')",
        ),
        Index("ix_rattachement_club_id_etat", "club_id", "etat"),
        # Un seul club par encadreur (spec 033, amende Q16).
        Index("uq_rattachement_actif_par_encadreur", "encadreur_id", unique=True, postgresql_where="etat = 'actif'"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    encadreur_id: Mapped[UUID] = mapped_column(ForeignKey("encadreur.utilisateur_id", ondelete="RESTRICT"), index=True)
    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"))
    etat: Mapped[EtatRattachement] = mapped_column(
        _enum_texte(EtatRattachement, "etat_rattachement", 25),
        default=EtatRattachement.en_attente_president,
        server_default=EtatRattachement.en_attente_president.value,
    )
    demande_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirme_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirme_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    retire_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retire_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_retrait: Mapped[str | None] = mapped_column(String(500))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012
