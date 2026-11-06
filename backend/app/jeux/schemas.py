from typing import Annotated

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
