"""Rapports d'activité, rapports mensuels et bilans semestriels (spec 038, R12).

Chaque rapport est un contenu du moteur de modération (ADR-0009) : ses textes vivent dans les versions, en JSONB.
La table `rapport` porte ce que la base doit filtrer, joindre ou rendre unique : la référence, le club, la date,
le mois ou le semestre, et le lien de doublon. Rien de tout cela n'est public.
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
    Sequence,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi
from app.referentiel.models import FORMAT_CODE


class ModeleRapport(StrEnum):
    activite = "activite"
    mensuel = "mensuel"
    bilan = "bilan"


# Le type du contenu de chaque modèle, dans le moteur de modération.
TYPES_CONTENU = {
    ModeleRapport.activite: "rapport_activite",
    ModeleRapport.mensuel: "rapport_mensuel",
    ModeleRapport.bilan: "bilan_semestriel",
}
PREFIXES = {ModeleRapport.activite: "RA", ModeleRapport.mensuel: "RM", ModeleRapport.bilan: "BS"}
# Une séquence par modèle : deux soumissions simultanées n'obtiennent jamais le même numéro.
SEQUENCES = {modele: Sequence(f"reference_{modele.value}_seq") for modele in ModeleRapport}


class TypeActivite(Suivi, Base):
    """La liste fermée des types d'activité, modifiable par l'admin (spec 038)."""

    __tablename__ = "type_activite"
    __table_args__ = (CheckConstraint(f"code ~ '{FORMAT_CODE}'", name="code_format"),)

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    libelle: Mapped[str] = mapped_column(String(120), unique=True)
    ordre: Mapped[int] = mapped_column(Integer)
    actif: Mapped[bool] = mapped_column(server_default=text("true"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class Rapport(Base):
    __tablename__ = "rapport"
    __table_args__ = (
        # Chaque modèle n'a que sa période : la date et le type d'une activité, le mois d'un mensuel, le semestre
        # d'un bilan. Un brouillon peut l'avoir incomplète.
        CheckConstraint(
            "(modele = 'activite' OR (date_activite IS NULL AND type_activite IS NULL))"
            " AND (modele = 'mensuel' OR mois IS NULL)"
            " AND (modele = 'bilan' OR semestre_id IS NULL)"
            # Un rapport soumis (il a sa référence) a toujours sa période.
            " AND (reference IS NULL OR ((modele <> 'activite' OR (date_activite IS NOT NULL AND type_activite IS NOT NULL))"
            " AND (modele <> 'mensuel' OR mois IS NOT NULL) AND (modele <> 'bilan' OR semestre_id IS NOT NULL)))",
            name="periode_du_modele",
        ),
        CheckConstraint("mois IS NULL OR extract(day FROM mois) = 1", name="mois_au_premier"),
        CheckConstraint("doublon_de_id IS NULL OR doublon_de_id <> contenu_id", name="doublon_dun_autre"),
        Index("ix_rapport_activite_du_jour", "club_id", "date_activite", "type_activite"),
        Index("ix_rapport_mois", "club_id", "mois"),
        Index("ix_rapport_semestre", "club_id", "semestre_id"),
    )

    contenu_id: Mapped[UUID] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"), primary_key=True)
    modele: Mapped[ModeleRapport] = mapped_column(
        Enum(ModeleRapport, name="modele_rapport", native_enum=False, create_constraint=True, length=10)
    )
    # Donnée à la première soumission (RA-2026-000123), puis gardée par les versions suivantes.
    reference: Mapped[str | None] = mapped_column(String(20), unique=True)
    club_id: Mapped[UUID] = mapped_column(ForeignKey("club.id", ondelete="RESTRICT"), index=True)
    date_activite: Mapped[date | None] = mapped_column(Date)
    type_activite: Mapped[str | None] = mapped_column(ForeignKey("type_activite.code", ondelete="RESTRICT"))
    mois: Mapped[date | None] = mapped_column(Date)
    semestre_id: Mapped[UUID | None] = mapped_column(ForeignKey("semestre.id", ondelete="RESTRICT"))
    # Posé à l'approbation « comme doublon » : le rapport est archivé, lié à l'original, sans aucun point.
    doublon_de_id: Mapped[UUID | None] = mapped_column(ForeignKey("rapport.contenu_id", ondelete="RESTRICT"))
    # Ce que ce rapport a crédité à son approbation (le registre reste la source des totaux) : un second mensuel du
    # même mois, ou un doublon, n'a rien crédité.
    points_auteur: Mapped[int | None] = mapped_column(Integer)
    points_club: Mapped[int | None] = mapped_column(Integer)


class TypePiece(StrEnum):
    pdf = "pdf"
    docx = "docx"


class PieceRapport(Base):
    """Un document joint (PDF ou Word) ; les photos passent par les tables de la spec 024."""

    __tablename__ = "piece_rapport"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    contenu_id: Mapped[UUID] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"), index=True)
    auteur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    nom: Mapped[str] = mapped_column(String(150))
    type: Mapped[TypePiece] = mapped_column(
        Enum(TypePiece, name="type_piece", native_enum=False, create_constraint=True, length=10)
    )
    cle_stockage: Mapped[str] = mapped_column(String(120))
    octets: Mapped[int] = mapped_column(Integer)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Fichier effacé (90 jours après un refus) : la ligne reste pour l'historique.
    efface_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VersionPiece(Base):
    """Les documents d'une version : une version soumise garde les siens, même si l'auteur en retire ensuite."""

    __tablename__ = "version_piece"
    __table_args__ = (Index("ix_version_piece_piece_id", "piece_id"),)

    version_id: Mapped[UUID] = mapped_column(ForeignKey("version_contenu.id", ondelete="CASCADE"), primary_key=True)
    piece_id: Mapped[UUID] = mapped_column(ForeignKey("piece_rapport.id", ondelete="RESTRICT"), primary_key=True)
    ordre: Mapped[int] = mapped_column(Integer)


class LectureRapport(Base):
    """« Consulté » : la première ouverture d'un rapport par un encadreur du club."""

    __tablename__ = "lecture_rapport"

    contenu_id: Mapped[UUID] = mapped_column(ForeignKey("contenu.id", ondelete="CASCADE"), primary_key=True)
    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    consulte_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


TYPES_DE_DEPART = [
    ("causerie", "Causerie éducative"),
    ("sensibilisation", "Sensibilisation"),
    ("depistage", "Dépistage"),
    ("campagne", "Campagne"),
    ("concours", "Concours"),
    ("sortie", "Sortie ou visite"),
    ("autre", "Autre activité"),
]


def charger_types(connexion: Connection) -> None:
    """Les types d'activité de départ, sans toucher aux lignes présentes. Sert aux tests et au seed ; la migration a
    sa propre copie figée."""
    lignes = [{"code": c, "libelle": l, "ordre": o} for o, (c, l) in enumerate(TYPES_DE_DEPART, start=1)]
    connexion.execute(insert(TypeActivite.__table__).values(lignes).on_conflict_do_nothing(index_elements=["code"]))
