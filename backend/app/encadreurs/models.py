"""Profil d'un encadreur (spec 018), lié un à un à son compte.

L'état de la vérification vit ici, pas dans `utilisateur.statut` : le statut du compte garde son sens de la
spec 015 (la suspension), qui prime toujours. Un encadreur en attente se connecte, voit son espace et corrige son
profil, sans aucun autre accès.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


class Fonction(StrEnum):
    enseignant = "enseignant"
    # Censeur, directeur, surveillant général…
    responsable = "responsable"
    # Infirmier ou agent de santé scolaire.
    sante = "sante"
    accompagnateur = "accompagnateur"
    autre = "autre"


class EtatVerification(StrEnum):
    en_attente = "en_attente"
    actif = "actif"
    refuse = "refuse"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class Encadreur(Suivi, Base):
    __tablename__ = "encadreur"
    __table_args__ = (
        CheckConstraint("(fonction = 'autre') = (fonction_precision IS NOT NULL)", name="precision_si_autre"),
        CheckConstraint("(etat = 'refuse') = (motif_refus IS NOT NULL)", name="motif_si_refuse"),
        # La file de vérification ne lit que les demandes en attente, de la plus ancienne à la plus récente.
        Index("ix_encadreur_file", "demande_le", postgresql_where=text("etat = 'en_attente'")),
    )

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    etablissement_id: Mapped[UUID] = mapped_column(ForeignKey("etablissement.id", ondelete="RESTRICT"), index=True)
    fonction: Mapped[Fonction] = mapped_column(_enum_texte(Fonction, "fonction"))
    fonction_precision: Mapped[str | None] = mapped_column(String(100))
    # Discipline ou spécialité (spec 030), facultative.
    discipline: Mapped[str | None] = mapped_column(String(100))
    etat: Mapped[EtatVerification] = mapped_column(
        _enum_texte(EtatVerification, "etat_verification"), default=EtatVerification.en_attente
    )
    # Date de la dernière demande : un refusé qui renvoie la sienne repasse en fin de file.
    demande_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    motif_refus: Mapped[str | None] = mapped_column(String(500))
    # Version de la charte acceptée à l'inscription (`settings.version_charte`).
    charte_version: Mapped[str] = mapped_column(String(20))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012
