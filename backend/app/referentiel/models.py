"""Référentiel territorial et thématique (spec 016) : DRE, IESG, établissements et axes.

Rien ne se supprime : un élément se désactive et reste attaché à tout ce qui le référence. `version` sert de verrou
optimiste : deux collaborateurs qui modifient le même élément ne s'écrasent pas.
"""

from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi

FORMAT_CODE = "^[a-z0-9-]+$"


class TypeEtablissement(StrEnum):
    lycee = "lycee"
    college = "college"
    complexe = "complexe"
    autre = "autre"


class StatutEtablissement(StrEnum):
    actif = "actif"
    inactif = "inactif"
    # Proposé par un président à la création de son club, validé avec lui (R4) : jamais dans les listes publiques.
    propose = "propose"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class Dre(Suivi, Base):
    __tablename__ = "dre"
    __table_args__ = (CheckConstraint(f"code ~ '{FORMAT_CODE}'", name="code_format"),)

    # Code stable, utilisé par les périmètres des collaborateurs et les URL : il ne change pas quand on renomme.
    code: Mapped[str] = mapped_column(String(30), primary_key=True)
    nom: Mapped[str] = mapped_column(String(150))
    nom_normalise: Mapped[str] = mapped_column(String(150), unique=True)
    nom_complet: Mapped[str] = mapped_column(String(200))
    ordre: Mapped[int] = mapped_column(Integer)
    actif: Mapped[bool] = mapped_column(server_default=text("true"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class Iesg(Suivi, Base):
    """Inspection de l'enseignement secondaire général : le niveau entre la DRE et l'établissement."""

    __tablename__ = "iesg"
    __table_args__ = (UniqueConstraint("dre_code", "nom_normalise"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    dre_code: Mapped[str] = mapped_column(ForeignKey("dre.code", ondelete="RESTRICT"), index=True)
    nom: Mapped[str] = mapped_column(String(150))
    nom_normalise: Mapped[str] = mapped_column(String(150))
    # La ville ou le secteur couvert, affiché sur la carte : « Golfe (Lomé) ».
    zone: Mapped[str | None] = mapped_column(String(150))
    actif: Mapped[bool] = mapped_column(server_default=text("true"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class Etablissement(Suivi, Base):
    __tablename__ = "etablissement"
    __table_args__ = (UniqueConstraint("iesg_id", "nom_normalise"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    # La DRE se déduit de l'IESG : elle n'est jamais saisie à part (Q2).
    iesg_id: Mapped[UUID] = mapped_column(ForeignKey("iesg.id", ondelete="RESTRICT"), index=True)
    nom: Mapped[str] = mapped_column(String(150))
    nom_normalise: Mapped[str] = mapped_column(String(150), index=True)
    type: Mapped[TypeEtablissement] = mapped_column(_enum_texte(TypeEtablissement, "type_etablissement"))
    localite: Mapped[str | None] = mapped_column(String(150))
    statut: Mapped[StatutEtablissement] = mapped_column(
        _enum_texte(StatutEtablissement, "statut_etablissement"), server_default=StatutEtablissement.actif.value
    )

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class Axe(Suivi, Base):
    """Un des 7 axes d'intervention (Q1) : classe articles, vidéos, quiz, forums, événements et rapports."""

    __tablename__ = "axe"
    __table_args__ = (CheckConstraint(f"code ~ '{FORMAT_CODE}'", name="code_format"),)

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    libelle: Mapped[str] = mapped_column(String(150))
    libelle_normalise: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str] = mapped_column(String(300))
    ordre: Mapped[int] = mapped_column(Integer)
    actif: Mapped[bool] = mapped_column(server_default=text("true"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012
