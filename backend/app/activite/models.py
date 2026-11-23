"""Suivi d'activité anonyme (spec 051, ADR-0014).

Aucune de ces tables ne garde d'adresse IP, de texte saisi ni, sauf `presence_semaine`, de lien vers un compte.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TypeEvenement(StrEnum):
    page_vue = "page_vue"
    clic_inscription = "clic_inscription"
    etape_inscription = "etape_inscription"
    telechargement = "telechargement"
    erreur = "erreur"
    recherche = "recherche"


TYPE = Enum(TypeEvenement, name="type_evenement", native_enum=False, create_constraint=True, length=20)


class SelActivite(Base):
    """Le sel du jour de l'empreinte des visiteurs : effacé dès le lendemain, l'empreinte ne se recalcule plus."""

    __tablename__ = "sel_activite"

    jour: Mapped[date] = mapped_column(Date, primary_key=True)
    sel: Mapped[bytes] = mapped_column(LargeBinary(32))


class EvenementActivite(Base):
    """Un événement brut, gardé 90 jours puis compté dans `total_activite_jour`."""

    __tablename__ = "evenement_activite"
    __table_args__ = (Index("ix_evenement_activite_jour_type", "jour", "type"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Jour de Lomé (UTC+0 toute l'année), celui du sel.
    jour: Mapped[date] = mapped_column(Date)
    type: Mapped[TypeEvenement] = mapped_column(TYPE)
    # Empreinte du jour (sel, adresse, navigateur), tronquée : compte un visiteur, ne le reconnaît pas le lendemain.
    visiteur: Mapped[str] = mapped_column(String(16))
    # Gabarit de la route (`/quiz/$id`), jamais une adresse réelle.
    chemin: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str | None] = mapped_column(String(60))
    provenance: Mapped[str | None] = mapped_column(String(30))
    appareil: Mapped[str | None] = mapped_column(String(10))
    navigateur: Mapped[str | None] = mapped_column(String(20))
    connecte: Mapped[bool] = mapped_column(default=False)


class TotalActiviteJour(Base):
    """Les événements de plus de 90 jours, comptés par jour et par groupe. `visiteurs` : empreintes distinctes du
    groupe ce jour-là."""

    __tablename__ = "total_activite_jour"
    __table_args__ = (Index("ix_total_activite_jour_jour_type", "jour", "type"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    jour: Mapped[date] = mapped_column(Date)
    type: Mapped[TypeEvenement] = mapped_column(TYPE)
    chemin: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str] = mapped_column(String(60), default="")
    provenance: Mapped[str] = mapped_column(String(30), default="")
    appareil: Mapped[str] = mapped_column(String(10), default="")
    navigateur: Mapped[str] = mapped_column(String(20), default="")
    connecte: Mapped[bool] = mapped_column(default=False)
    evenements: Mapped[int] = mapped_column(Integer)
    visiteurs: Mapped[int] = mapped_column(Integer)


class VisiteursJour(Base):
    """Visiteurs distincts d'un jour sorti des 90 jours, tous événements confondus."""

    __tablename__ = "visiteurs_jour"

    jour: Mapped[date] = mapped_column(Date, primary_key=True)
    visiteurs: Mapped[int] = mapped_column(Integer)


class PresenceSemaine(Base):
    """Un compte actif une semaine (lundi), pour la rétention seulement : jamais affiché par personne, effacé avec le
    compte et au bout de 26 semaines."""

    __tablename__ = "presence_semaine"

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    semaine: Mapped[date] = mapped_column(Date, primary_key=True)
