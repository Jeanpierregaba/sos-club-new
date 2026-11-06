"""Banque des défis du jour (spec 021). Une question tirée chaque jour pour tous ; aucun point n'est gagné."""

from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, Integer, String, text
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
