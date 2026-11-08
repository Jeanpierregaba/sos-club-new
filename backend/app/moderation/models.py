"""Moteur commun de modération (spec 023, ADR-0009) : un en-tête par contenu, ses versions et les décisions.

Ce qui est en ligne ne dépend que de `version_publiee_id` : une nouvelle version reste masquée jusqu'à son
approbation, et l'ancienne reste publiée d'ici là. Une version soumise ne change plus ; versions et décisions
forment l'historique de modération et ne se suppriment pas.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


class EtatContenu(StrEnum):
    brouillon = "brouillon"
    en_attente = "en_attente"
    a_corriger = "a_corriger"
    refuse = "refuse"
    publie = "publie"
    depublie = "depublie"
    # Retiré par son auteur (un commentaire, spec 025) : hors ligne et hors de la file, sans décision de modérateur.
    retire = "retire"


class EtatVersion(StrEnum):
    # Modifiable par l'auteur.
    travail = "travail"
    soumise = "soumise"
    approuvee = "approuvee"
    a_corriger = "a_corriger"
    refusee = "refusee"
    # Retirée de la file par l'auteur : une nouvelle version de travail la remplace.
    retiree = "retiree"


class TypeDecision(StrEnum):
    approuver = "approuver"
    corriger = "corriger"
    refuser = "refuser"
    depublier = "depublier"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class Contenu(Suivi, Base):
    __tablename__ = "contenu"
    __table_args__ = (
        # Une adresse publique n'existe qu'une fois le contenu approuvé, et ne change plus ensuite.
        # Un commentaire (spec 025) n'en a pas : il se lit sous son article.
        CheckConstraint(
            "version_publiee_id IS NULL OR adresse IS NOT NULL OR parent_id IS NOT NULL", name="adresse_si_publie"
        ),
        # Un commentaire, et lui seul, a un contenu parent : son article.
        CheckConstraint("(type = 'commentaire') = (parent_id IS NOT NULL)", name="commentaire_a_un_parent"),
        # Un contenu refusé, dépublié ou retiré n'a plus de version en ligne ; un contenu « publié » en a toujours une.
        CheckConstraint(
            "version_publiee_id IS NULL OR etat NOT IN ('refuse', 'depublie', 'retire')", name="hors_ligne_si_retire"
        ),
        CheckConstraint("etat <> 'publie' OR version_publiee_id IS NOT NULL", name="en_ligne_si_publie"),
        Index("ix_contenu_file", "soumis_le", postgresql_where=text("etat = 'en_attente'")),
        Index("ix_contenu_publics", "type", "publie_le", postgresql_where=text("version_publiee_id IS NOT NULL")),
        Index("ix_contenu_auteur_id_etat", "auteur_id", "etat"),
        Index(
            "ix_contenu_commentaires_publics",
            "parent_id",
            "publie_le",
            postgresql_where=text("version_publiee_id IS NOT NULL"),
        ),
        # Les plafonds du jour d'un auteur (spec 025 : 20 commentaires envoyés, 5 rémunérés).
        Index("ix_contenu_auteur_id_type_cree_le", "auteur_id", "type", "cree_le"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    type: Mapped[str] = mapped_column(String(30))
    auteur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    etat: Mapped[EtatContenu] = mapped_column(_enum_texte(EtatContenu, "etat_contenu"), default=EtatContenu.brouillon)
    version_publiee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("version_contenu.id", ondelete="RESTRICT", use_alter=True, name="fk_contenu_version_publiee_id")
    )
    version_travail_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("version_contenu.id", ondelete="RESTRICT", use_alter=True, name="fk_contenu_version_travail_id")
    )
    axe_code: Mapped[str | None] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"), index=True)
    adresse: Mapped[str | None] = mapped_column(String(140), unique=True)
    # Choix de l'élève : son club apparaît à côté de son pseudonyme (Q20).
    # L'article d'un commentaire (spec 025) ; nul pour tout autre contenu.
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("contenu.id", ondelete="RESTRICT"))
    afficher_club: Mapped[bool] = mapped_column(server_default=text("true"))
    # DRE de l'établissement de l'auteur, copiée à chaque soumission : elle fixe le périmètre de la file.
    dre_code: Mapped[str | None] = mapped_column(ForeignKey("dre.code", ondelete="RESTRICT"))
    # Club de l'élève affilié à la première approbation : R13 lui créditera `club.article_eleve`.
    club_beneficiaire_id: Mapped[UUID | None] = mapped_column(ForeignKey("club.id", ondelete="RESTRICT"))
    soumis_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Date de la première publication : l'ordre public ne bouge pas avec une nouvelle version.
    publie_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class VersionContenu(Base):
    __tablename__ = "version_contenu"
    __table_args__ = (UniqueConstraint("contenu_id", "numero"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    contenu_id: Mapped[UUID] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"))
    numero: Mapped[int] = mapped_column(Integer)
    # Les champs du type (titre, texte…), validés par son schéma à chaque écriture.
    donnees: Mapped[dict[str, Any]] = mapped_column(JSONB)
    etat: Mapped[EtatVersion] = mapped_column(_enum_texte(EtatVersion, "etat_version"), default=EtatVersion.travail)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    modifie_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    soumise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DecisionModeration(Base):
    __tablename__ = "decision_moderation"
    __table_args__ = (
        CheckConstraint("decision = 'approuver' OR motif IS NOT NULL", name="motif_sauf_approbation"),
        Index("ix_decision_moderation_contenu_id", "contenu_id", "decide_le"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    contenu_id: Mapped[UUID] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"))
    version_id: Mapped[UUID] = mapped_column(ForeignKey("version_contenu.id", ondelete="CASCADE"))
    decision: Mapped[TypeDecision] = mapped_column(_enum_texte(TypeDecision, "type_decision"))
    motif: Mapped[str | None] = mapped_column(String(1000))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="SET NULL"))
    decide_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Photo(Base):
    """Une photo envoyée par l'auteur d'un contenu (spec 024) : ses fichiers et son attestation (Q8). Son placement
    (légende, ordre, couverture) appartient à chaque version qui l'utilise (`VersionPhoto`)."""

    __tablename__ = "photo"
    __table_args__ = (Index("ix_photo_contenu_id", "contenu_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    contenu_id: Mapped[UUID] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"))
    auteur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    cle_grande: Mapped[str] = mapped_column(String(120))
    cle_vignette: Mapped[str] = mapped_column(String(120))
    largeur: Mapped[int] = mapped_column(Integer)
    hauteur: Mapped[int] = mapped_column(Integer)
    octets: Mapped[int] = mapped_column(Integer)
    # Le texte accepté par l'auteur, copié tel qu'il était affiché.
    attestation: Mapped[str] = mapped_column(String(500))
    attestee_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Fichiers effacés (90 jours après un refus) : la ligne reste pour l'historique.
    efface_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VersionPhoto(Base):
    __tablename__ = "version_photo"
    __table_args__ = (
        Index("uq_version_photo_couverture", "version_id", unique=True, postgresql_where=text("couverture")),
        Index("ix_version_photo_photo_id", "photo_id"),
    )

    version_id: Mapped[UUID] = mapped_column(ForeignKey("version_contenu.id", ondelete="CASCADE"), primary_key=True)
    photo_id: Mapped[UUID] = mapped_column(ForeignKey("photo.id", ondelete="RESTRICT"), primary_key=True)
    ordre: Mapped[int] = mapped_column(Integer)
    legende: Mapped[str | None] = mapped_column(String(200))
    couverture: Mapped[bool] = mapped_column(server_default=text("false"))
