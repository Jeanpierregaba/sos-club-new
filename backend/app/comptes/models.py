from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Role(StrEnum):
    eleve = "eleve"
    encadreur = "encadreur"
    admin = "admin"
    # Compte léger du grand public (spec 030) : quiz « jeux » sans points, ni club ni certification.
    visiteur = "visiteur"
    # Joueur sans compte (spec 031) : créé à sa première partie depuis la page des jeux, sans e-mail ni mot de
    # passe, reconnu par un cookie à part ; trois quiz au plus, puis il crée un compte visiteur. Effacé après 7 jours.
    invite = "invite"


class StatutCompte(StrEnum):
    actif = "actif"
    suspendu = "suspendu"
    # Collaborateur retiré définitivement (spec 015) : ne se réactive pas.
    revoque = "revoque"


class Sexe(StrEnum):
    feminin = "feminin"
    masculin = "masculin"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    # Un texte et une contrainte CHECK : plus simple à faire évoluer qu'un type enum PostgreSQL.
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class Utilisateur(Base):
    __tablename__ = "utilisateur"
    __table_args__ = (
        CheckConstraint("identifiant ~ '^[a-z0-9._-]{3,30}$'", name="identifiant_format"),
        CheckConstraint("email = lower(email)", name="email_minuscules"),
        CheckConstraint("email IS NOT NULL OR role IN ('eleve', 'invite')", name="email_obligatoire_sauf_eleve"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    role: Mapped[Role] = mapped_column(_enum_texte(Role, "role"))
    identifiant: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    telephone: Mapped[str | None] = mapped_column(String(30))
    prenom: Mapped[str] = mapped_column(String(100))
    nom: Mapped[str] = mapped_column(String(100))
    mot_de_passe_hash: Mapped[str] = mapped_column(Text)
    statut: Mapped[StatutCompte] = mapped_column(_enum_texte(StatutCompte, "statut"), default=StatutCompte.actif)
    consentement_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Adresse confirmée par un code (spec 030) : exigée des seuls visiteurs, nulle pour les autres profils.
    email_confirme_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Session(Base):
    __tablename__ = "session"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)
    # Seule l'empreinte du jeton est gardée : une fuite de la base ne donne accès à aucune session.
    jeton_hash: Mapped[str] = mapped_column(String(64), unique=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class TentativeConnexion(Base):
    """Un essai de connexion, réservé avant le hachage, puis effacé si réussi. Gardé au plus une heure."""

    __tablename__ = "tentative_connexion"
    __table_args__ = (
        Index("ix_tentative_connexion_cle_hash_cree_le", "cle_hash", "cree_le"),
        Index("ix_tentative_connexion_adresse_ip_cree_le", "adresse_ip", "cree_le"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    # Une empreinte : un élève peut taper son mot de passe dans le champ identifiant.
    cle_hash: Mapped[str] = mapped_column(String(64))
    adresse_ip: Mapped[str] = mapped_column(String(45))
    en_cours: Mapped[bool] = mapped_column(default=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
