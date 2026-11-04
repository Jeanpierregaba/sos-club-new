"""Registre des points, semestres et barème (spec 017, ADR-0004).

Un score est une somme de lignes du registre. Une ligne ne se modifie ni ne se supprime : une erreur se
corrige par une ligne négative qui pointe vers la ligne annulée.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi

MONTANT_MAX = 10_000


class Beneficiaire(StrEnum):
    eleve = "eleve"
    encadreur = "encadreur"
    club = "club"


class Semestre(Suivi, Base):
    """Période de classement. Les dates sont celles de Lomé, qui est à UTC+0 toute l'année."""

    __tablename__ = "semestre"
    __table_args__ = (
        CheckConstraint("fin >= debut", name="dates_ordonnees"),
        # La base refuse deux semestres qui se chevauchent, même créés au même instant.
        ExcludeConstraint(
            (text("daterange(debut, fin, '[]')"), "&&"), name="ex_semestre_sans_chevauchement", using="gist"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    libelle: Mapped[str] = mapped_column(String(60), unique=True)
    debut: Mapped[date] = mapped_column(Date)
    fin: Mapped[date] = mapped_column(Date)

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class LigneBareme(Suivi, Base):
    __tablename__ = "bareme"
    __table_args__ = (
        CheckConstraint(f"montant BETWEEN 0 AND {MONTANT_MAX}", name="montant_borne"),
        CheckConstraint("code ~ '^[a-z]+\\.[a-z_]+$'", name="code_format"),
    )

    code: Mapped[str] = mapped_column(String(60), primary_key=True)
    beneficiaire: Mapped[Beneficiaire] = mapped_column(
        Enum(Beneficiaire, name="beneficiaire", native_enum=False, create_constraint=True, length=20)
    )
    libelle: Mapped[str] = mapped_column(String(120))
    montant: Mapped[int] = mapped_column(Integer)
    propose: Mapped[bool] = mapped_column(server_default=text("false"))
    # Vrai quand une spec livrée écrit déjà cette action.
    en_service: Mapped[bool] = mapped_column(server_default=text("false"))
    actif: Mapped[bool] = mapped_column(server_default=text("true"))
    ordre: Mapped[int] = mapped_column(Integer)

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class MouvementPoints(Base):
    __tablename__ = "mouvement_points"
    __table_args__ = (
        # Un gain est positif ; seule une annulation est négative.
        CheckConstraint(
            "(annule_id IS NULL AND montant > 0) OR (annule_id IS NOT NULL AND montant < 0)", name="montant_signe"
        ),
        Index("ix_mouvement_points_utilisateur_id_semestre_id", "utilisateur_id", "semestre_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(ForeignKey("bareme.code", ondelete="RESTRICT"))
    # Copié du barème au moment du gain : un total ne dépend jamais du barème actuel.
    montant: Mapped[int] = mapped_column(Integer)
    # Nul hors semestre : la ligne compte alors dans le total historique seulement.
    semestre_id: Mapped[UUID | None] = mapped_column(ForeignKey("semestre.id", ondelete="RESTRICT"))
    # Clé d'idempotence, par exemple `bienvenue:<élève>` : une même action n'est jamais créditée deux fois.
    cle: Mapped[str] = mapped_column(String(200), unique=True)
    valide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    annule_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"), unique=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
