"""Certification Génie Imhotep (spec 029) : les règles des badges, la progression des joueurs et les certificats.

La progression est matérialisée : une place réussie, un badge ou un certificat d'origine n'existent qu'une fois
par personne, et la base le garantit (clés primaires et index uniques), même entre deux fins de partie simultanées.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

NB_BADGES = 5


class EtatCertificat(StrEnum):
    valide = "valide"
    revoque = "revoque"
    remplace = "remplace"


class ReglesBadges(Base):
    """Une version des règles des badges. Jamais modifiée : un changement ajoute une version."""

    __tablename__ = "regles_badges"
    __table_args__ = (
        CheckConstraint("cardinality(paliers) = 5 AND jsonb_array_length(noms) = 5", name="cinq_badges"),
        CheckConstraint("paliers[5] = 12", name="dernier_palier_12"),
        CheckConstraint(
            "paliers[1] >= 1 AND paliers[1] < paliers[2] AND paliers[2] < paliers[3] AND paliers[3] < paliers[4] "
            "AND paliers[4] < paliers[5]",
            name="paliers_croissants",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    version: Mapped[int] = mapped_column(Integer, unique=True)
    noms: Mapped[list[str]] = mapped_column(JSONB)
    # Nombre de places réussies qui délivre chaque badge, strictement croissant.
    paliers: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    # Nul pour la version initiale, posée par la migration.
    cree_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlaceReussie(Base):
    """Une place du parcours réussie par un joueur. Elle reste acquise si son quiz est dépublié ou remplacé."""

    __tablename__ = "place_reussie"
    __table_args__ = (CheckConstraint("place BETWEEN 1 AND 12", name="place_valide"),)

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"), primary_key=True)
    place: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quiz.id", ondelete="RESTRICT"))
    tentative_id: Mapped[UUID] = mapped_column(ForeignKey("tentative_quiz.id", ondelete="RESTRICT"))
    reussie_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BadgeObtenu(Base):
    """Un badge délivré. Son nom et son palier sont copiés des règles du moment : une nouvelle version ne le
    change pas."""

    __tablename__ = "badge_obtenu"
    __table_args__ = (
        CheckConstraint("rang BETWEEN 1 AND 5", name="rang_valide"),
        Index("ix_badge_obtenu_obtenu_le", "obtenu_le"),
    )

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"), primary_key=True)
    rang: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(40))
    palier: Mapped[int] = mapped_column(Integer)
    regles_version: Mapped[int] = mapped_column(Integer)
    # Le club de l'élève affilié au moment du badge, pour ses points (R13). Nul sinon.
    club_id: Mapped[UUID | None] = mapped_column(ForeignKey("club.id", ondelete="SET NULL"))
    # La ligne du registre créditée (élève actif) ; nulle pour un encadreur.
    mouvement_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"))
    obtenu_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Certificat(Base):
    __tablename__ = "certificat"
    __table_args__ = (
        # Un seul certificat délivré automatiquement par personne, à jamais : un certificat révoqué n'est pas
        # redélivré par une nouvelle réussite. Seule une réémission (remplace_id renseigné) en crée un autre.
        Index("uq_certificat_origine", "utilisateur_id", unique=True, postgresql_where=text("remplace_id IS NULL")),
        Index("uq_certificat_valide", "utilisateur_id", unique=True, postgresql_where=text("etat = 'valide'")),
        CheckConstraint("etat = 'valide' OR decide_le IS NOT NULL", name="decision_datee"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    # Non devinable : GI-XXXX-XXXX-XXXX, 60 bits aléatoires.
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"), index=True)
    # « eleve » ou « encadreur » à la délivrance.
    role: Mapped[str] = mapped_column(String(20))
    # Figés à la délivrance ; seuls le PDF du titulaire et la liste interne de l'équipe les montrent.
    titulaire_prenom: Mapped[str] = mapped_column(String(100))
    titulaire_nom: Mapped[str] = mapped_column(String(100))
    etat: Mapped[EtatCertificat] = mapped_column(
        Enum(EtatCertificat, name="etat", native_enum=False, create_constraint=True, length=20),
        default=EtatCertificat.valide,
    )
    delivre_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    club_id: Mapped[UUID | None] = mapped_column(ForeignKey("club.id", ondelete="SET NULL"))
    # RULES : un élève n'apparaît publiquement avec son club que s'il le souhaite. Caché par défaut.
    afficher_club: Mapped[bool] = mapped_column(server_default=text("false"), default=False)
    mouvement_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"))
    # Le certificat que celui-ci remplace (réémission).
    remplace_id: Mapped[UUID | None] = mapped_column(ForeignKey("certificat.id", ondelete="RESTRICT"), unique=True)
    # Motif de la révocation ; qui a révoqué ou remplacé ce certificat, et quand.
    motif: Mapped[str | None] = mapped_column(String(500))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
