"""Registre des types de contenu modérés (ADR-0009). Chaque type déclare le schéma de ses champs, l'action du
barème de son auteur selon son rôle, et ce que la file et les notifications en montrent. Le moteur ne connaît
rien d'autre d'un type."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role
from app.moderation.models import Contenu


@dataclass(frozen=True)
class TypeContenu:
    code: str
    # « l'article », pour les messages : « Ton article a été publié ».
    libelle: str
    schema: type[BaseModel]
    # Action du barème créditée à l'auteur à la première approbation, selon son rôle ; absente = aucun point.
    actions_auteur: dict[Role, str]
    # Le titre montré dans la file et dans les notifications.
    titre: Callable[[dict[str, Any]], str]
    # Chemin du site où l'auteur retrouve son contenu.
    lien_auteur: Callable[[UUID], str]
    # Une adresse publique à la première approbation (un article) ; un commentaire se lit sous son article.
    adresse: bool = True
    # La décision « à corriger » : un commentaire est court, son auteur en écrit un autre.
    correction: bool = True
    # Appelée à la première approbation, sous le verrou de l'auteur : faux = publié sans points (plafond du jour).
    points_permis: Callable[[AsyncSession, Contenu], Awaitable[bool]] | None = None
    # Appelée à la première approbation, dans la transaction de la décision (notifier l'auteur de l'article…).
    a_la_publication: Callable[[AsyncSession, Contenu], Awaitable[None]] | None = None


TYPES: dict[str, TypeContenu] = {}


def enregistrer(type_contenu: TypeContenu) -> TypeContenu:
    TYPES[type_contenu.code] = type_contenu
    return type_contenu


def type_de(code: str) -> TypeContenu:
    return TYPES[code]
