"""Registre des points, semestres et barème (spec 017, ADR-0004).

Un score est une somme de lignes du registre. Une ligne ne se modifie ni ne se supprime : une erreur se
corrige par une ligne négative qui pointe vers la ligne annulée.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi

MONTANT_MAX = 10_000


class Beneficiaire(StrEnum):
    eleve = "eleve"
    encadreur = "encadreur"
    club = "club"


class Parcours(StrEnum):
    """Les trois parcours de l'élève (spec 034) ; une action d'encadreur n'en a pas."""

    certification = "certification"
    jeux = "jeux"
    vie = "vie"


class SousCompte(StrEnum):
    """Les Jeux se décomptent en deux : points des quiz et points des étoiles (spec 034)."""

    quiz = "quiz"
    etoiles = "etoiles"


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


class AnneeAcademique(Suivi, Base):
    """L'année académique (spec 034, lot 4), de septembre N à juillet N+1 ; l'équipe en fixe les dates exactes. Les
    compteurs annuels sont des sommes filtrées par année : rien n'est remis à zéro ni effacé. La clôture fige le
    classement régional annuel."""

    __tablename__ = "annee_academique"
    __table_args__ = (
        CheckConstraint("fin >= debut", name="dates_ordonnees"),
        CheckConstraint("(cloturee_le IS NULL) = (cloturee_par IS NULL)", name="cloture_complete"),
        ExcludeConstraint(
            (text("daterange(debut, fin, '[]')"), "&&"), name="ex_annee_sans_chevauchement", using="gist"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    libelle: Mapped[str] = mapped_column(String(20), unique=True)
    debut: Mapped[date] = mapped_column(Date)
    fin: Mapped[date] = mapped_column(Date)
    cloturee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cloturee_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class ClassementAnnuel(Base):
    """Le classement régional des élèves, figé à la clôture d'une année (spec 034) : pseudonyme et club seulement,
    jamais de nom complet (RULES). Une ligne par élève classé, une seule fois par année."""

    __tablename__ = "classement_annuel"
    __table_args__ = (UniqueConstraint("annee_id", "utilisateur_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    annee_id: Mapped[UUID] = mapped_column(ForeignKey("annee_academique.id", ondelete="RESTRICT"), index=True)
    region: Mapped[str] = mapped_column(String(40))
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    pseudonyme: Mapped[str] = mapped_column(String(60))
    club: Mapped[str | None] = mapped_column(String(200))
    points: Mapped[int] = mapped_column(Integer)
    rang: Mapped[int] = mapped_column(Integer)


class LigneBareme(Suivi, Base):
    __tablename__ = "bareme"
    __table_args__ = (
        CheckConstraint(f"montant BETWEEN 0 AND {MONTANT_MAX}", name="montant_borne"),
        CheckConstraint("code ~ '^[a-z]+\\.[a-z_]+$'", name="code_format"),
        CheckConstraint("sous_compte IS NULL OR parcours = 'jeux'", name="sous_compte_des_jeux"),
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
    parcours: Mapped[Parcours | None] = mapped_column(
        Enum(Parcours, name="parcours_points", native_enum=False, create_constraint=True, length=20)
    )
    sous_compte: Mapped[SousCompte | None] = mapped_column(
        Enum(SousCompte, name="sous_compte_points", native_enum=False, create_constraint=True, length=10)
    )

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class MouvementPoints(Base):
    __tablename__ = "mouvement_points"
    __table_args__ = (
        # Un gain est positif ; seule une annulation est négative.
        CheckConstraint(
            "(annule_id IS NULL AND montant > 0) OR (annule_id IS NOT NULL AND montant < 0)", name="montant_signe"
        ),
        Index("ix_mouvement_points_utilisateur_id_semestre_id", "utilisateur_id", "semestre_id"),
        # La part du club (spec 034, ADR-0012) : toujours la moitié du gain de l'élève, en demi-points entiers.
        CheckConstraint("(club_id IS NULL) = (demi_points_club IS NULL)", name="club_et_part"),
        CheckConstraint("demi_points_club IS NULL OR demi_points_club = montant", name="part_du_club_moitie"),
        Index("ix_mouvement_points_club_id", "club_id", postgresql_where=text("club_id IS NOT NULL")),
        Index("ix_mouvement_points_annee_id_utilisateur_id", "annee_id", "utilisateur_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(ForeignKey("bareme.code", ondelete="RESTRICT"))
    # Copié du barème au moment du gain : un total ne dépend jamais du barème actuel.
    montant: Mapped[int] = mapped_column(Integer)
    # Nul hors année : la ligne compte alors dans le total historique seulement (spec 034).
    annee_id: Mapped[UUID | None] = mapped_column(ForeignKey("annee_academique.id", ondelete="RESTRICT"))
    # Nul hors semestre : la ligne compte alors dans le total historique seulement.
    semestre_id: Mapped[UUID | None] = mapped_column(ForeignKey("semestre.id", ondelete="RESTRICT"))
    # Clé d'idempotence, par exemple `bienvenue:<élève>` : une même action n'est jamais créditée deux fois.
    cle: Mapped[str] = mapped_column(String(200), unique=True)
    valide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    annule_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"), unique=True)
    # Le club de l'élève au moment du gain, s'il était affilié à un club en service ; il garde sa part ensuite.
    club_id: Mapped[UUID | None] = mapped_column(ForeignKey("club.id", ondelete="RESTRICT"))
    # La part du club en demi-points : 5 ici valent 2,5 points de club.
    demi_points_club: Mapped[int | None] = mapped_column(Integer)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
