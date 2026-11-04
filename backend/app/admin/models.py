from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.admin.catalogue import DRE, Action, RoleDepart
from app.db import Base


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=30)


class Collaborateur(Base):
    """Profil de gestion d'un compte admin. `utilisateur_id` reste nul tant que l'invitation n'est pas acceptée."""

    __tablename__ = "collaborateur"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_minuscules"),
        CheckConstraint(
            "perimetre_dre IS NULL OR perimetre_dre IN (" + ", ".join(f"'{d}'" for d in DRE) + ")",
            name="perimetre_dre_connue",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    prenom: Mapped[str] = mapped_column(String(100))
    nom: Mapped[str] = mapped_column(String(100))
    role_depart: Mapped[RoleDepart | None] = mapped_column(_enum_texte(RoleDepart, "role_depart"))
    # Nul : périmètre national.
    perimetre_dre: Mapped[str | None] = mapped_column(String(30))
    fin_acces: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    super_admin: Mapped[bool] = mapped_column(default=False)
    invite_par_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    revu_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Permission(Base):
    __tablename__ = "permission"

    collaborateur_id: Mapped[UUID] = mapped_column(ForeignKey("collaborateur.id", ondelete="CASCADE"), primary_key=True)
    module: Mapped[str] = mapped_column(String(30), primary_key=True)
    action: Mapped[Action] = mapped_column(_enum_texte(Action, "action"), primary_key=True)


class EnvoiInvitation(StrEnum):
    envoye = "envoye"
    echec = "echec"


class Invitation(Base):
    __tablename__ = "invitation"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    collaborateur_id: Mapped[UUID] = mapped_column(ForeignKey("collaborateur.id", ondelete="CASCADE"), index=True)
    jeton_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    utilisee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    annulee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    envoi: Mapped[EnvoiInvitation] = mapped_column(_enum_texte(EnvoiInvitation, "envoi"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DoubleAuth(Base):
    """Secret TOTP chiffré (ADR-0008). `active_le` reste nul tant que le premier code n'a pas été confirmé."""

    __tablename__ = "double_auth"

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    secret_chiffre: Mapped[str] = mapped_column(Text)
    active_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Pas de 30 secondes du dernier code accepté : un code déjà utilisé ne sert pas deux fois.
    dernier_pas: Mapped[int | None] = mapped_column(Integer)


class CodeSecours(Base):
    __tablename__ = "code_secours"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(Text)
    utilise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EtapeDoubleAuth(Base):
    """Entre le mot de passe et le code : la session n'est créée qu'après le code."""

    __tablename__ = "etape_double_auth"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    jeton_hash: Mapped[str] = mapped_column(String(64), unique=True)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JournalAudit(Base):
    """Journal en ajout seul : un déclencheur refuse UPDATE et DELETE (ADR-0008).

    Pas de clé étrangère vers `utilisateur` : supprimer un compte ne doit ni modifier ni bloquer le journal.
    L'auteur est donc gardé tel qu'il était au moment de l'action.
    """

    __tablename__ = "journal_audit"
    __table_args__ = (Index("ix_journal_audit_cible", "cible_type", "cible_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    quand: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    auteur_id: Mapped[UUID | None] = mapped_column(index=True)
    auteur_libelle: Mapped[str | None] = mapped_column(String(220))
    action: Mapped[str] = mapped_column(String(50), index=True)
    cible_type: Mapped[str | None] = mapped_column(String(30))
    cible_id: Mapped[str | None] = mapped_column(String(64))
    perimetre: Mapped[str | None] = mapped_column(String(30))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    adresse_ip: Mapped[str | None] = mapped_column(String(45))


class TypeExport(StrEnum):
    agrege = "agrege"
    nominatif = "nominatif"


class FormatExport(StrEnum):
    csv = "csv"
    xlsx = "xlsx"


class StatutExport(StrEnum):
    pret = "pret"
    telecharge = "telecharge"
    expire = "expire"
    echec = "echec"


class Export(Base):
    __tablename__ = "export"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    demandeur_id: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"), index=True)
    type: Mapped[TypeExport] = mapped_column(_enum_texte(TypeExport, "type_export"))
    format: Mapped[FormatExport] = mapped_column(_enum_texte(FormatExport, "format_export"))
    filtres: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    colonnes: Mapped[list[str]] = mapped_column(ARRAY(String(30)), default=list)
    finalite: Mapped[str | None] = mapped_column(Text)
    nb_lignes: Mapped[int] = mapped_column(Integer, default=0)
    statut: Mapped[StatutExport] = mapped_column(_enum_texte(StatutExport, "statut_export"))
    # Effacé dès que le lien a servi ou que le délai de conservation est passé.
    fichier: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    jeton_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    lien_expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fichier_expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    telecharge_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
