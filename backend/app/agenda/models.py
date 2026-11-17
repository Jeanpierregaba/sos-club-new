"""Agenda et invitations (spec 041, R16).

Un événement de club est un contenu du moteur de modération (ADR-0009, type `evenement`) : ses brouillons et ses
versions soumises vivent dans les versions, en JSONB. La table `evenement` est la seule que lit l'agenda public :
pour un événement de club, elle reçoit la copie de la version approuvée à chaque approbation ; un événement national
ou régional de l'équipe y est écrit directement, publié dès sa création.

Les invités ne sont pas stockés : ce sont les membres dont l'adhésion au club est active, lus à chaque fois. La table
`reponse_evenement` ne garde que les réponses et le pointage des présents.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class NiveauEvenement(StrEnum):
    national = "national"
    regional = "regional"
    club = "club"


class TypeEvenement(StrEnum):
    formation = "formation"
    sensibilisation = "sensibilisation"
    concours = "concours"
    assainissement = "assainissement"
    campagne = "campagne"
    emission = "emission"
    reunion = "reunion"
    autre = "autre"


class Reponse(StrEnum):
    participe = "participe"
    peut_etre = "peut_etre"
    non = "non"


def _enum(enum: type[StrEnum], nom: str, longueur: int) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=longueur)


class Evenement(Base):
    __tablename__ = "evenement"
    __table_args__ = (
        # Un événement de club a son club et sa DRE ; un régional sa DRE seule ; un national ni l'un ni l'autre.
        CheckConstraint(
            "(niveau = 'club') = (club_id IS NOT NULL) AND (niveau = 'club') = (contenu_id IS NOT NULL)"
            " AND (niveau = 'national') = (dre_code IS NULL)",
            name="rattachement_du_niveau",
        ),
        CheckConstraint("fin > debut", name="fin_apres_debut"),
        CheckConstraint("places IS NULL OR places >= 1", name="places_positives"),
        CheckConstraint("lien IS NULL OR lien LIKE 'https://%'", name="lien_https"),
        CheckConstraint("(annule_le IS NULL) = (motif_annulation IS NULL)", name="motif_si_annule"),
        Index("ix_evenement_publie_debut", "publie", "debut"),
        Index("ix_evenement_club_id_debut", "club_id", "debut"),
        Index("ix_evenement_dre_code_debut", "dre_code", "debut"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    # Le contenu modéré d'un événement de club ; nul pour un événement de l'équipe.
    contenu_id: Mapped[UUID | None] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"), unique=True)
    niveau: Mapped[NiveauEvenement] = mapped_column(_enum(NiveauEvenement, "niveau_evenement", 10))
    club_id: Mapped[UUID | None] = mapped_column(ForeignKey("club.id", ondelete="RESTRICT"))
    dre_code: Mapped[str | None] = mapped_column(ForeignKey("dre.code", ondelete="RESTRICT"))
    type: Mapped[TypeEvenement] = mapped_column(_enum(TypeEvenement, "type_evenement", 20))
    axe_code: Mapped[str | None] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"))
    # Copie de la version approuvée (club) ou saisie de l'équipe : ce que montre l'agenda public.
    titre: Mapped[str] = mapped_column(String(150))
    objectif: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    lieu: Mapped[str | None] = mapped_column(String(200))
    en_ligne: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    lien: Mapped[str | None] = mapped_column(String(500))
    public_vise: Mapped[str | None] = mapped_column(String(200))
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    places: Mapped[int | None] = mapped_column(Integer)
    # Vrai à la première approbation d'un événement de club, ou dès la création par l'équipe ; faux s'il est retiré.
    publie: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    annule_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    annule_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_annulation: Mapped[str | None] = mapped_column(Text)
    # La date (à Lomé) de l'événement au moment où son rappel est parti : un report à un autre jour en rouvre un.
    rappel_pour: Mapped[date | None] = mapped_column(Date)
    cree_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modifie_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReponseEvenement(Base):
    """La réponse d'un membre invité, et le pointage de sa présence après l'événement."""

    __tablename__ = "reponse_evenement"
    __table_args__ = (
        CheckConstraint("(present IS NULL) = (pointe_le IS NULL)", name="pointage_date"),
        Index(
            "ix_reponse_evenement_participants",
            "evenement_id",
            postgresql_where=text("reponse = 'participe'"),
        ),
    )

    evenement_id: Mapped[UUID] = mapped_column(ForeignKey("evenement.id", ondelete="CASCADE"), primary_key=True)
    eleve_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    # Nulle pour un membre pointé présent sans avoir répondu.
    reponse: Mapped[Reponse | None] = mapped_column(_enum(Reponse, "reponse_evenement", 10))
    repondu_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    present: Mapped[bool | None] = mapped_column(Boolean)
    pointe_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    pointe_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
