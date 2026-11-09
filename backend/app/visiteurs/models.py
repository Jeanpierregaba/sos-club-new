"""Compte visiteur (spec 030) : un compte léger du grand public, confirmé par un code reçu par e-mail."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comptes.models import Sexe
from app.db import Base


class Region(StrEnum):
    maritime = "maritime"
    plateaux = "plateaux"
    centrale = "centrale"
    kara = "kara"
    savanes = "savanes"
    hors_togo = "hors_togo"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class Visiteur(Base):
    __tablename__ = "visiteur"

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    ville: Mapped[str] = mapped_column(String(100))
    region: Mapped[Region | None] = mapped_column(_enum_texte(Region, "region"))
    sexe: Mapped[Sexe | None] = mapped_column(_enum_texte(Sexe, "sexe"))
    # Étudiant, parent, professionnel… : texte libre.
    statut: Mapped[str | None] = mapped_column(String(100))
    charte_version: Mapped[str] = mapped_column(String(20))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CodeConfirmation(Base):
    """Le code en cours d'un compte : un renvoi remplace le précédent. Seule son empreinte Argon2 est gardée."""

    __tablename__ = "code_confirmation"
    __table_args__ = (CheckConstraint("essais BETWEEN 0 AND 5", name="essais"),)

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    code_hash: Mapped[str] = mapped_column(Text)
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    essais: Mapped[int] = mapped_column(SmallInteger, default=0)
    envoye_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
