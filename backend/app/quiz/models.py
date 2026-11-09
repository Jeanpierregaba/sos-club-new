"""Quiz chronométrés (spec 027, ADR-0004) : la banque préparée par l'équipe, et les tentatives des joueurs.

La bonne réponse d'une question ne quitte jamais l'API : seuls les schémas de la banque la portent. Une tentative
garde ses questions tirées, l'ordre de leurs choix et l'heure d'envoi de chacune : le serveur arbitre seul.
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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as UUIDPg
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Suivi

PARCOURS_JEUX = "jeux"
# Le parcours Génie Imhotep (spec 029) : 12 places, jouées dans l'ordre.
PARCOURS_CERTIFICATION = "certification"
PARCOURS = (PARCOURS_JEUX, PARCOURS_CERTIFICATION)
PLACES = 12


class EtatQuiz(StrEnum):
    brouillon = "brouillon"
    soumis = "soumis"
    publie = "publie"
    depublie = "depublie"


class EtatTentative(StrEnum):
    en_cours = "en_cours"
    terminee = "terminee"


def _enum_texte(enum: type[StrEnum], nom: str) -> Enum:
    return Enum(enum, name=nom, native_enum=False, create_constraint=True, length=20)


class ParametresQuiz(Base):
    """Une version des paramètres d'un parcours. Jamais modifiée : un changement ajoute une version."""

    __tablename__ = "parametres_quiz"
    __table_args__ = (
        UniqueConstraint("parcours", "version"),
        CheckConstraint("nb_questions BETWEEN 1 AND 50", name="nb_questions_valide"),
        CheckConstraint("seuil BETWEEN 1 AND nb_questions", name="seuil_valide"),
        CheckConstraint("temps_ms > 0 AND tolerance_ms >= 0", name="temps_valide"),
        CheckConstraint("tentatives_par_jour >= 1", name="tentatives_valide"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    parcours: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer)
    nb_questions: Mapped[int] = mapped_column(Integer)
    temps_ms: Mapped[int] = mapped_column(Integer)
    tolerance_ms: Mapped[int] = mapped_column(Integer)
    seuil: Mapped[int] = mapped_column(Integer)
    tentatives_par_jour: Mapped[int] = mapped_column(Integer)
    # Nul pour la version initiale, posée par la migration ou par défaut.
    cree_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Quiz(Suivi, Base):
    __tablename__ = "quiz"
    __table_args__ = (
        CheckConstraint(
            "etat <> 'publie' OR (validateur_nom IS NOT NULL AND validateur_qualite IS NOT NULL)",
            name="publie_avec_validateur",
        ),
        CheckConstraint("parcours IN ('jeux', 'certification')", name="parcours_valide"),
        # Un quiz de certification occupe une place de 1 à 12 ; un quiz de jeux n'en a pas, ni de fascicule.
        CheckConstraint("(parcours = 'certification') = (place IS NOT NULL)", name="place_si_certification"),
        CheckConstraint("place BETWEEN 1 AND 12", name="place_valide"),
        CheckConstraint("parcours = 'certification' OR ressource_id IS NULL", name="fascicule_si_certification"),
        # Une place n'a qu'un quiz publié : la base tranche entre deux approbations simultanées.
        Index("uq_quiz_place_publiee", "place", unique=True, postgresql_where=text("etat = 'publie'")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    titre: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(300), server_default="")
    axe_code: Mapped[str] = mapped_column(ForeignKey("axe.code", ondelete="RESTRICT"), index=True)
    etat: Mapped[EtatQuiz] = mapped_column(_enum_texte(EtatQuiz, "etat"), default=EtatQuiz.brouillon, index=True)
    parcours: Mapped[str] = mapped_column(String(20), server_default=PARCOURS_JEUX, default=PARCOURS_JEUX)
    place: Mapped[int | None] = mapped_column(Integer)
    # Le fascicule de la bibliothèque à lire avant de jouer (certification seulement).
    ressource_id: Mapped[UUID | None] = mapped_column(ForeignKey("ressource.id", ondelete="RESTRICT"))
    # « Contenu de test » : chargé par seed_dev, jamais en prod (RULES).
    contenu_de_test: Mapped[bool] = mapped_column(server_default=text("false"))
    # Tous ceux qui l'ont créé, modifié ou soumis : aucun d'eux ne peut l'approuver (publication à deux).
    contributeurs: Mapped[list[UUID]] = mapped_column(ARRAY(UUIDPg(as_uuid=True)), server_default="{}")
    soumis_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    soumis_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decide_par: Mapped[UUID | None] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    decide_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Motif du dernier refus ou de la dépublication.
    motif: Mapped[str | None] = mapped_column(String(500))
    # La personne qui a validé le contenu médical (Q11), nommée à l'approbation.
    validateur_nom: Mapped[str | None] = mapped_column(String(120))
    validateur_qualite: Mapped[str | None] = mapped_column(String(120))
    publie_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class QuestionQuiz(Suivi, Base):
    __tablename__ = "question_quiz"
    __table_args__ = (
        CheckConstraint("jsonb_array_length(choix) BETWEEN 2 AND 4", name="choix_2_a_4"),
        CheckConstraint(
            "bonne_reponse >= 0 AND bonne_reponse < jsonb_array_length(choix)", name="bonne_reponse_valide"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quiz.id", ondelete="RESTRICT"), index=True)
    enonce: Mapped[str] = mapped_column(String(300))
    choix: Mapped[list[str]] = mapped_column(JSONB)
    # Index de la bonne réponse dans `choix` : jamais envoyé à un joueur.
    bonne_reponse: Mapped[int] = mapped_column(Integer)
    explication: Mapped[str | None] = mapped_column(String(500))
    ordre: Mapped[int] = mapped_column(Integer)
    # Une question déjà tirée ne s'efface pas : la retirer la désactive (hors tirage et hors réserve).
    active: Mapped[bool] = mapped_column(server_default=text("true"))

    __mapper_args__ = {"version_id_col": Suivi.version}  # noqa: RUF012


class TentativeQuiz(Base):
    __tablename__ = "tentative_quiz"
    __table_args__ = (
        # Une seule tentative en cours par joueur et par quiz : la base tranche entre deux lancements.
        Index(
            "uq_tentative_quiz_en_cours",
            "quiz_id",
            "joueur_id",
            unique=True,
            postgresql_where=text("etat = 'en_cours'"),
        ),
        Index("ix_tentative_quiz_joueur_quiz_jour", "joueur_id", "quiz_id", "jour"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quiz.id", ondelete="RESTRICT"))
    joueur_id: Mapped[UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"))
    parametres_id: Mapped[UUID] = mapped_column(ForeignKey("parametres_quiz.id", ondelete="RESTRICT"))
    # Partie de test d'un collaborateur : hors résultats, hors plafond, sans points, effacée à sa fin.
    essai: Mapped[bool] = mapped_column(server_default=text("false"))
    etat: Mapped[EtatTentative] = mapped_column(_enum_texte(EtatTentative, "etat"), default=EtatTentative.en_cours)
    # Le jour de Lomé du lancement, pour le plafond quotidien.
    jour: Mapped[date] = mapped_column(Date)
    commencee_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    derniere_activite: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    terminee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[int | None] = mapped_column(Integer)
    reussie: Mapped[bool | None]
    # La ligne du registre créditée par cette tentative (première réussite d'un élève), nulle sinon.
    mouvement_id: Mapped[UUID | None] = mapped_column(ForeignKey("mouvement_points.id", ondelete="RESTRICT"))


class ReponseQuiz(Base):
    """Une question tirée pour une tentative, et la réponse du joueur."""

    __tablename__ = "reponse_quiz"
    __table_args__ = (UniqueConstraint("tentative_id", "rang"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    tentative_id: Mapped[UUID] = mapped_column(ForeignKey("tentative_quiz.id", ondelete="CASCADE"))
    rang: Mapped[int] = mapped_column(Integer)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("question_quiz.id", ondelete="RESTRICT"), index=True)
    # Permutation : `ordre_choix[i]` est l'index d'origine du i-ème choix montré au joueur.
    ordre_choix: Mapped[list[int]] = mapped_column(JSONB)
    # Nulle tant que la question n'a pas été envoyée : le délai court à partir de l'envoi.
    envoyee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    repondue_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Index d'origine du choix retenu ; nul pour une question ratée faute de réponse à temps.
    choix: Mapped[int | None] = mapped_column(Integer)
    # Nulle tant que la question n'est pas tranchée.
    correcte: Mapped[bool | None]
