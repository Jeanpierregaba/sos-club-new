"""Schémas de la banque de quiz (spec 027), réservés à l'espace admin : eux seuls portent la bonne réponse."""

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.quiz.models import EtatQuiz

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


class QuizEntree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: Annotated[Texte, StringConstraints(min_length=3, max_length=120)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] = ""
    axe_code: Annotated[str, StringConstraints(max_length=40)]


class QuizBanque(BaseModel):
    id: UUID
    titre: str
    description: str
    axe_code: str
    etat: EtatQuiz
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
    tentatives_par_jour: Annotated[int, Field(ge=1, le=100)]

    @model_validator(mode="after")
    def coherents(self) -> Self:
        if self.seuil > self.nb_questions:
            raise ValueError("Le seuil de réussite ne peut pas dépasser le nombre de questions.")
        return self


class ParametresSortie(BaseModel):
    version: int
    nb_questions: int
    temps_ms: int
    tolerance_ms: int
    seuil: int
    tentatives_par_jour: int
    cree_le: datetime


class HistoriqueParametres(BaseModel):
    en_cours: ParametresSortie
    versions: list[ParametresSortie]
