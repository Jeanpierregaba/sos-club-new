"""Banque des défis du jour (spec 021) et réponses des élèves (spec 022) : une question tirée chaque jour pour tous ;
seule la première réponse du jour d'un élève compte, et rapporte des points si elle est juste. Étoiles des Jeux
(spec 034)."""

from datetime import date, datetime
from uuid import UUID, uuid7

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


class DefiQuestion(Suivi, Base):
    __tablename__ = "defi_question"
    __table_args__ = (
        CheckConstraint("jsonb_array_length(options) BETWEEN 2 AND 4", name="options_2_a_4"),
        CheckConstraint(
            "bonne_reponse >= 0 AND bonne_reponse < jsonb_array_length(options)", name="bonne_reponse_valide"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    # La place dans la rotation : le défi du jour est la question active de rang (jour mod nombre).
    ordre: Mapped[int] = mapped_column(Integer, unique=True)
    categorie: Mapped[str] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(String(300))
    options: Mapped[list[str]] = mapped_column(JSONB)
    # Index de la bonne réponse dans `options` ; jamais envoyé avec la question.
    bonne_reponse: Mapped[int] = mapped_column(Integer)
    explication: Mapped[str] = mapped_column(String(500))
    actif: Mapped[bool] = mapped_column(server_default=text("true"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class DefiReponse(Base):
    """La réponse comptée d'un élève : une par jour (la base refuse la seconde). Jamais modifiée."""

    __tablename__ = "defi_reponse"
    __table_args__ = (UniqueConstraint("eleve_id", "jour"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    eleve_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    defi_id: Mapped[UUID] = mapped_column(ForeignKey("defi_question.id", ondelete="RESTRICT"))
    # Le jour de Lomé où la question était celle du jour.
    jour: Mapped[date] = mapped_column(Date)
    choix: Mapped[int] = mapped_column(Integer)
    correcte: Mapped[bool]
    # La ligne du registre créditée pour une bonne réponse ; nulle sinon (ou si le barème est à 0).
    mouvement_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"))
    repondu_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PartieQuelAxe(Base):
    """Une partie de « Quel axe est fait pour toi ? » (spec 032) : au plus 3 par élève, sur toute la vie du compte,
    et une seule en cours. Effacée avec le compte. Ne rapporte jamais de point."""

    __tablename__ = "partie_quel_axe"
    __table_args__ = (
        UniqueConstraint("eleve_id", "numero"),
        CheckConstraint("numero BETWEEN 1 AND 3", name="numero_1_a_3"),
        CheckConstraint(
            "(terminee_le IS NULL AND principal IS NULL AND autres IS NULL) "
            "OR (terminee_le IS NOT NULL AND principal IS NOT NULL AND autres IS NOT NULL)",
            name="resultat_a_la_fin",
        ),
        Index("uq_partie_quel_axe_en_cours", "eleve_id", unique=True, postgresql_where=text("terminee_le IS NULL")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    eleve_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(SmallInteger)
    version_questionnaire: Mapped[int] = mapped_column(SmallInteger)
    # Une lettre (A à D) ou null par question, dans l'ordre du questionnaire.
    reponses: Mapped[list[str | None]] = mapped_column(JSONB)
    principal: Mapped[str | None] = mapped_column(String(4))
    autres: Mapped[list[str] | None] = mapped_column(JSONB)
    commencee_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    terminee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EtoileObtenue(Base):
    """Une étoile des Jeux (spec 034) : son niveau a tous ses quiz publiés réussis. Une seule par élève et par niveau,
    même entre deux réussites simultanées ; elle reste acquise si un quiz est ensuite ajouté ou dépublié."""

    __tablename__ = "etoile_obtenue"
    __table_args__ = (
        UniqueConstraint("utilisateur_id", "niveau"),
        CheckConstraint("niveau IN ('debutant', 'intermediaire', 'avance', 'expert')", name="niveau_valide"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    niveau: Mapped[str] = mapped_column(String(20))
    # Le bonus crédité ; nul si le barème était à 0 ou désactivé à ce moment.
    mouvement_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"))
    obtenue_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
