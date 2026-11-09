"""Bibliothèque (spec 028) : magazines, guides, fiches, affiches et fascicules en PDF, publiés à deux personnes.

Le PDF et la couverture vivent dans le stockage (ADR-0010) sous des clés tirées par l'API ; la ligne ne garde que
ces clés. Un fichier remplacé change de clé : aucune adresse ne sert l'ancien contenu.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as UUIDPg
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi


class CategorieRessource(StrEnum):
    magazine = "magazine"
    guide = "guide"
    fiche = "fiche"
    affiche = "affiche"
    fascicule = "fascicule"


class EtatRessource(StrEnum):
    brouillon = "brouillon"
    soumis = "soumis"
    publie = "publie"
    depublie = "depublie"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class Ressource(Suivi, Base):
    __tablename__ = "ressource"
    __table_args__ = (
        CheckConstraint(
            "etat <> 'publie' OR (validateur_nom IS NOT NULL AND validateur_qualite IS NOT NULL "
            "AND fichier_cle IS NOT NULL)",
            name="publiee_complete",
        ),
        CheckConstraint("telechargements >= 0", name="telechargements_positifs"),
        Index("ix_ressource_etat_publie_le", "etat", "publie_le"),
        Index("ix_ressource_categorie_etat_publie_le", "categorie", "etat", "publie_le"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    titre: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(500), server_default="")
    categorie: Mapped[CategorieRessource] = mapped_column(_enum_texte(CategorieRessource, "categorie"))
    axe_code: Mapped[str | None] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"))
    # Numéro ou date de parution d'un magazine.
    parution: Mapped[str | None] = mapped_column(String(60))
    etat: Mapped[EtatRessource] = mapped_column(_enum_texte(EtatRessource, "etat"), default=EtatRessource.brouillon)
    # « Contenu de test » : chargé par seed_dev, jamais en prod (RULES).
    contenu_de_test: Mapped[bool] = mapped_column(server_default=text("false"))
    # Tous ceux qui l'ont créée, modifiée, y ont déposé un fichier ou l'ont soumise : aucun ne peut l'approuver.
    contributeurs: Mapped[list[UUID]] = mapped_column(ARRAY(UUIDPg(as_uuid=True)), server_default="{}")

    fichier_cle: Mapped[str | None] = mapped_column(String(120))
    fichier_octets: Mapped[int | None] = mapped_column(Integer)
    pages: Mapped[int | None] = mapped_column(Integer)
    couverture_grande: Mapped[str | None] = mapped_column(String(120))
    couverture_vignette: Mapped[str | None] = mapped_column(String(120))
    # Un simple compteur : on ne garde pas qui a téléchargé.
    telechargements: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    soumis_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    soumis_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Motif du dernier refus ou de la dépublication.
    motif: Mapped[str | None] = mapped_column(String(500))
    # La personne qui a validé le contenu (Q11), nommée à l'approbation.
    validateur_nom: Mapped[str | None] = mapped_column(String(120))
    validateur_qualite: Mapped[str | None] = mapped_column(String(120))
    # Date de la dernière publication : l'ordre de la bibliothèque et de « À la Une ».
    publie_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Une ressource déjà publiée ne se supprime plus : elle se dépublie.
    deja_publiee: Mapped[bool] = mapped_column(server_default=text("false"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012
