"""Profil d'un élève (spec 017), lié un à un à son compte. Le prénom et le nom restent dans `utilisateur` et ne
sortent jamais de l'espace admin : hors de celui-ci, un élève n'apparaît que par son pseudonyme (Q20)."""

from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


class Classe(StrEnum):
    sixieme = "6e"
    cinquieme = "5e"
    quatrieme = "4e"
    troisieme = "3e"
    seconde = "2nde"
    premiere = "1re"
    terminale = "tle"


class Eleve(Suivi, Base):
    __tablename__ = "eleve"

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    pseudonyme: Mapped[str] = mapped_column(String(30))
    # Sans accents, majuscules, espaces ni ponctuation : « Aya-K » et « aya k » sont le même pseudonyme.
    pseudonyme_normalise: Mapped[str] = mapped_column(String(30), unique=True)
    classe: Mapped[Classe] = mapped_column(
        Enum(Classe, name="classe", native_enum=False, create_constraint=True, length=10,
             values_callable=lambda enum: [membre.value for membre in enum])
    )  # fmt: skip
    etablissement_id: Mapped[UUID] = mapped_column(ForeignKey("etablissement.id", ondelete="RESTRICT"), index=True)
    # Version de la charte acceptée à l'inscription (`settings.version_charte`).
    charte_version: Mapped[str] = mapped_column(String(20))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012
