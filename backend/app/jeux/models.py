"""Banque des défis du jour (spec 021) et réponses des élèves (spec 022). Une question tirée chaque jour pour
tous ; seule la première réponse du jour d'un élève compte, et rapporte des points si elle est juste."""

from datetime import date, datetime
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
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
