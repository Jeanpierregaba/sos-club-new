"""Clubs et présidence (spec 019) : demande, validation, fiche publique, passation.

Un club est une entité collective rattachée à un établissement : il n'a jamais de compte. Son président,
un élève, le gère avec son compte. Aucune ligne de points n'est écrite ici : le score du club viendra
avec les specs qui en créditent (quiz, publications, rapports).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class EtatClub(StrEnum):
    en_attente = "en_attente"
    actif = "actif"
    refuse = "refuse"


class EtatPassation(StrEnum):
    en_attente = "en_attente"
    validee = "validee"
    refusee = "refusee"


class Club(Suivi, Base):
    __tablename__ = "club"
    __table_args__ = (
        # Un refus porte toujours un motif ; aucun autre état n'en a.
        CheckConstraint("(etat = 'refuse') = (motif_refus IS NOT NULL)", name="motif_si_refuse"),
        UniqueConstraint("etablissement_id", "nom_normalise"),
        # Un seul club actif par établissement : la base tranche, même entre deux activations simultanées.
        Index("uq_club_actif_par_etablissement", "etablissement_id", unique=True, postgresql_where="etat = 'actif'"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    etablissement_id: Mapped[UUID] = mapped_column(ForeignKey("etablissement.id", ondelete="RESTRICT"), index=True)
    nom: Mapped[str] = mapped_column(String(150))
    # Sans accents, majuscules ni ponctuation : « Club Santé de Tokoin » et « club sante de to-k oin » se confondent.
    nom_normalise: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(String(300))
    demandeur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    # Gestionnaire courant : posé à l'activation, nul tant que la demande est en attente.
    president_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    # Encadreurs associés cités à titre déclaratif : jamais des comptes, jamais des droits.
    encadreurs_associes: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    etat: Mapped[EtatClub] = mapped_column(
        _enum_texte(EtatClub, "etat_club"), default=EtatClub.en_attente, server_default=EtatClub.en_attente.value
    )
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    demande_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actif_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class ClubAxe(Base):
    __tablename__ = "club_axe"

    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="CASCADE"), primary_key=True)
    axe_code: Mapped[str] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"), primary_key=True)


class ClubPassation(Suivi, Base):
    __tablename__ = "club_passation"
    __table_args__ = (
        CheckConstraint("(etat = 'refusee') = (motif_refus IS NOT NULL)", name="motif_si_refusee"),
        # Une seule proposition en attente par club.
        Index("uq_club_passation_en_attente", "club_id", unique=True, postgresql_where="etat = 'en_attente'"),
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
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012
