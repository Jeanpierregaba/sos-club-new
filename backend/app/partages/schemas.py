"""Schémas des partages d'articles (spec 044)."""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReseauPartage(StrEnum):
    facebook = "facebook"
    instagram = "instagram"
    tiktok = "tiktok"
    linkedin = "linkedin"


Nature = Literal["republication", "partage"]
LIEN_MAX = 500


class ChampsPartage(BaseModel):
    """La version unique d'une déclaration, dans le moteur de modération."""

    reseau: ReseauPartage
    lien: str
    # Le lien réduit à ce qui désigne la publication (hôte sans « www. », sans paramètres de suivi ni « / » final) :
    # c'est lui qui ne sert qu'une fois.
    cle_lien: str
    nature: Nature


class DeclarationPartage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reseau: ReseauPartage
    lien: str = Field(max_length=LIEN_MAX + 50)

    @field_validator("lien")
    @classmethod
    def _sans_espaces(cls, valeur: str) -> str:
        return valeur.strip()


class PartageAuteur(BaseModel):
    """Une déclaration, vue par son auteur : jamais publique."""

    id: UUID
    article_titre: str
    article_adresse: str | None
    reseau: ReseauPartage
    lien: str
    nature: Nature
    etat: Literal["en_attente", "approuve", "refuse"]
    motif: str | None
    points: int | None
    declare_le: datetime


class MesPartages(BaseModel):
    partages: list[PartageAuteur]


class EtatPartagesArticle(BaseModel):
    """Ce que la personne connectée peut encore déclarer sur un article."""

    nature: Nature
    reseaux_declares: list[ReseauPartage]
    restantes_aujourdhui: int
    # Le montant actuel du barème pour cette déclaration ; nul si l'action est désactivée.
    points: int | None
