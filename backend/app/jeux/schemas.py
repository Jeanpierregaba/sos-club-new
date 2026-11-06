from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.jeux.quel_axe import CodeAxe, Lettre


class ReponseQuelAxe(BaseModel):
    id: Lettre
    libelle: str


class QuestionQuelAxe(BaseModel):
    numero: int
    libelle: str
    # Sans les axes associés : le calcul reste dans l'API.
    reponses: list[ReponseQuelAxe]


class QuestionnaireQuelAxe(BaseModel):
    questions: list[QuestionQuelAxe]


class ReponsesQuelAxe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reponses: Annotated[list[Lettre], Field(min_length=5, max_length=5)]


class ResultatQuelAxe(BaseModel):
    principal: CodeAxe
    autres: list[CodeAxe]
    scores: dict[CodeAxe, int]


class CorrectionDefi(BaseModel):
    choix: int
    correcte: bool
    bonne_reponse: int
    explication: str
    # Points gagnés par cette réponse ; 0 si elle est fausse, déjà comptée, ou d'un visiteur.
    points: int = 0
    # Vrai si l'élève avait déjà répondu aujourd'hui : c'est sa première réponse qui est renvoyée.
    deja_repondu: bool = False


class DefiDuJour(BaseModel):
    # Sans la bonne réponse : elle vient de la correction.
    id: UUID
    categorie: str
    question: str
    options: list[str]
    # Pour un élève qui a déjà répondu aujourd'hui : sa réponse et la correction, rien d'autre à jouer.
    ma_reponse: CorrectionDefi | None = None


class ReponseDefi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    choix: Annotated[int, Field(ge=0, le=3)]
