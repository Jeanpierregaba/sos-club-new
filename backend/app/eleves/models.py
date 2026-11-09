"""Profil d'un élève (spec 017), lié un à un à son compte. Le prénom et le nom restent dans `utilisateur` et ne
sortent jamais de l'espace admin : hors de celui-ci, un élève n'apparaît que par son pseudonyme (Q20)."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.comptes.models import Sexe
from app.db import Base, Suivi


class Classe(StrEnum):
    sixieme = "6e"
    cinquieme = "5e"
    quatrieme = "4e"
    troisieme = "3e"
    seconde = "2nde"
    premiere = "1re"
    terminale = "tle"


class Eleve(Suivi, Base):
    __tablename__ = "eleve"

    utilisateur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), primary_key=True)
    pseudonyme: Mapped[str] = mapped_column(String(30))
    # Sans accents, majuscules, espaces ni ponctuation : « Aya-K » et « aya k » sont le même pseudonyme.
    pseudonyme_normalise: Mapped[str] = mapped_column(String(30), unique=True)
    classe: Mapped[Classe] = mapped_column(
        Enum(Classe, name="classe", native_enum=False, create_constraint=True, length=10,
             values_callable=lambda enum: [membre.value for membre in enum])
    )  # fmt: skip
    etablissement_id: Mapped[UUID] = mapped_column(ForeignKey("etablissement.id", ondelete="RESTRICT"), index=True)
    # Version de la charte acceptée à l'inscription (`settings.version_charte`).
    charte_version: Mapped[str] = mapped_column(String(20))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class Reseau(StrEnum):
    facebook = "facebook"
    tiktok = "tiktok"
    instagram = "instagram"
    autre = "autre"


class FicheEleve(Suivi, Base):
    """Fiche d'adhésion au Club Santé (spec 030), reprise de la fiche papier.

    Données personnelles d'un mineur : lues par l'élève et par les collaborateurs ayant le droit sensible
    `fiches_eleves:consulter` (journalisé), jamais par un encadreur ni en public. Les colonnes sont nulles pour
    accueillir la fiche partielle d'un ancien élève ; `complete_le` marque la première fiche complète.
    """

    __tablename__ = "fiche_eleve"
    __table_args__ = (
        CheckConstraint(
            "reseaux <@ ARRAY['facebook', 'tiktok', 'instagram', 'autre']::varchar[]", name="reseaux_connus"
        ),
        CheckConstraint("('autre' = ANY(reseaux)) = (reseau_autre IS NOT NULL)", name="reseau_autre_si_autre"),
    )

    utilisateur_id: Mapped[UUID] = mapped_column(
        ForeignKey("eleve.utilisateur_id", ondelete="CASCADE"), primary_key=True
    )
    # « 2026-2027 » : posée par le serveur à la création.
    annee_scolaire: Mapped[str] = mapped_column(String(9))
    numero_adhesion: Mapped[str | None] = mapped_column(String(30))
    prefecture: Mapped[str | None] = mapped_column(String(100))
    commune: Mapped[str | None] = mapped_column(String(100))
    canton: Mapped[str | None] = mapped_column(String(100))
    sexe: Mapped[Sexe | None] = mapped_column(
        Enum(Sexe, name="sexe", native_enum=False, create_constraint=True, length=20)
    )
    date_naissance: Mapped[date | None] = mapped_column(Date)
    lieu_naissance: Mapped[str | None] = mapped_column(String(100))
    telephone: Mapped[str | None] = mapped_column(String(30))
    pere_nom: Mapped[str | None] = mapped_column(String(150))
    pere_profession: Mapped[str | None] = mapped_column(String(100))
    pere_telephone: Mapped[str | None] = mapped_column(String(30))
    mere_nom: Mapped[str | None] = mapped_column(String(150))
    mere_profession: Mapped[str | None] = mapped_column(String(100))
    mere_telephone: Mapped[str | None] = mapped_column(String(30))
    # Le parent ou tuteur responsable : il remplace la signature de la fiche papier.
    responsable_nom: Mapped[str | None] = mapped_column(String(150))
    responsable_telephone: Mapped[str | None] = mapped_column(String(30))
    reseaux: Mapped[list[str]] = mapped_column(ARRAY(String(20)), server_default=text("'{}'"))
    reseau_autre: Mapped[str | None] = mapped_column(String(60))
    engagement_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    complete_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class FicheEleveAxe(Base):
    """Axe(s) choisi(s) sur la fiche : un à trois axes du référentiel."""

    __tablename__ = "fiche_eleve_axe"

    utilisateur_id: Mapped[UUID] = mapped_column(
        ForeignKey("fiche_eleve.utilisateur_id", ondelete="CASCADE"), primary_key=True
    )
    axe_code: Mapped[str] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"), primary_key=True)


class FicheEleveParcours(Base):
    """Club Santé des années antérieures : texte libre, un ancien établissement n'est pas forcément au référentiel."""

    __tablename__ = "fiche_eleve_parcours"
    __table_args__ = (CheckConstraint("rang BETWEEN 1 AND 2", name="rang"),)

    utilisateur_id: Mapped[UUID] = mapped_column(
        ForeignKey("fiche_eleve.utilisateur_id", ondelete="CASCADE"), primary_key=True
    )
    rang: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    annee: Mapped[str] = mapped_column(String(9))
    etablissement: Mapped[str] = mapped_column(String(150))
    iesg: Mapped[str | None] = mapped_column(String(150))
