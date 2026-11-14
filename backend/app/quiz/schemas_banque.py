"""Schémas de la banque de quiz (spec 027), réservés à l'espace admin : eux seuls portent la bonne réponse."""

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.quiz.models import EtatQuiz, NiveauQuiz

Texte = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class QuestionEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enonce: Annotated[Texte, StringConstraints(max_length=300)]
    choix: Annotated[list[Annotated[Texte, StringConstraints(max_length=150)]], Field(min_length=2, max_length=4)]
    bonne_reponse: Annotated[int, Field(ge=0)]
    explication: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=500)] = None

    @model_validator(mode="after")
    def coherente(self) -> Self:
        if self.bonne_reponse >= len(self.choix):
            raise ValueError("La bonne réponse doit être l'un des choix.")
        if len({c.casefold() for c in self.choix}) != len(self.choix):
            raise ValueError("Deux choix sont identiques.")
        if not self.explication:
            self.explication = None
        return self


class QuestionBanque(BaseModel):
    id: UUID
    enonce: str
    choix: list[str]
    bonne_reponse: int
    explication: str | None
    ordre: int
    active: bool


Parcours = Literal["jeux", "certification"]


class QuizEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: Annotated[Texte, StringConstraints(min_length=3, max_length=120)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] = ""
    axe_code: Annotated[str, StringConstraints(max_length=40)]
    parcours: Parcours = "jeux"
    # Certification seulement (spec 029, 034) : la place de 1 à 20 et le fascicule à lire avant de jouer.
    place: Annotated[int | None, Field(ge=1, le=20)] = None
    ressource_id: UUID | None = None
    # Jeux seulement (spec 034) : le niveau fixe les points du quiz et l'étoile à laquelle il compte.
    niveau: NiveauQuiz | None = None

    @model_validator(mode="after")
    def coherente(self) -> Self:
        if self.parcours == "jeux":
            self.place = self.ressource_id = None
        else:
            self.niveau = None
        if self.parcours != "jeux" and self.place is None:
            raise ValueError("Un quiz de certification occupe une place de 1 à 20.")
        return self


class QuizBanque(BaseModel):
    id: UUID
    titre: str
    description: str
    axe_code: str
    etat: EtatQuiz
    parcours: Parcours
    place: int | None
    niveau: NiveauQuiz | None
    numero: int | None
    ressource_id: UUID | None
    ressource_titre: str | None
    contenu_de_test: bool
    questions_actives: int
    soumis_le: datetime | None
    decide_le: datetime | None
    motif: str | None
    validateur_nom: str | None
    validateur_qualite: str | None
    publie_le: datetime | None
    modifie_le: datetime
    # Le collaborateur connecté a créé, modifié ou soumis ce quiz : il ne peut pas l'approuver.
    contributeur: bool


class QuizDetail(QuizBanque):
    questions: list[QuestionBanque]
    questions_requises: int


class ListeBanque(BaseModel):
    questions_requises: int
    quiz: list[QuizBanque]


class Approbation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validateur_nom: Annotated[Texte, StringConstraints(min_length=2, max_length=120)]
    validateur_qualite: Annotated[Texte, StringConstraints(min_length=2, max_length=120)]


class Motif(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motif: Annotated[Texte, StringConstraints(min_length=3, max_length=500)]


class ParametresEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nb_questions: Annotated[int, Field(ge=1, le=50)]
    temps_ms: Annotated[int, Field(ge=1000, le=60000)]
    tolerance_ms: Annotated[int, Field(ge=0, le=30000)]
    seuil: Annotated[int, Field(ge=1)]
    # Nul : aucun plafond quotidien (la certification se recommence jusqu'à réussite, spec 034).
    tentatives_par_jour: Annotated[int, Field(ge=1, le=100)] | None
    # Nul : la valeur de la version en cours est gardée.
    arret_premiere_erreur: bool | None = None

    @model_validator(mode="after")
    def coherents(self) -> Self:
        if self.seuil > self.nb_questions:
            raise ValueError("Le seuil de réussite ne peut pas dépasser le nombre de questions.")
        if self.arret_premiere_erreur and self.seuil != self.nb_questions:
            raise ValueError("L'arrêt à la première erreur demande toutes les bonnes réponses (seuil = nombre).")
        return self


class ParametresSortie(BaseModel):
    version: int
    nb_questions: int
    temps_ms: int
    tolerance_ms: int
    seuil: int
    tentatives_par_jour: int | None
    arret_premiere_erreur: bool
    cree_le: datetime


class HistoriqueParametres(BaseModel):
    en_cours: ParametresSortie
    versions: list[ParametresSortie]
