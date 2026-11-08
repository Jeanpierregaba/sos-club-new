import re
import unicodedata
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.articles.schemas import Signature
from app.moderation.models import EtatContenu

LONGUEUR_MAX = 1000
_RETOURS = re.compile(r"\n{3,}")


def normaliser(texte: str) -> str:
    """Texte simple : retours à la ligne gardés (deux d'affilée au plus), caractères de contrôle retirés, espaces du
    début et de la fin retirés."""
    texte = texte.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    texte = "".join(c for c in texte if c == "\n" or unicodedata.category(c) != "Cc")
    return _RETOURS.sub("\n\n", texte).strip()


class CommentaireEntree(BaseModel):
    # La limite brute empêche un texte énorme d'être traité ; la vraie limite s'applique après normalisation.
    texte: str = Field(max_length=4 * LONGUEUR_MAX)
    afficher_club: bool = True

    @field_validator("texte")
    @classmethod
    def _texte(cls, valeur: str) -> str:
        valeur = normaliser(valeur)
        if not valeur:
            raise ValueError("Écris ton commentaire avant de l'envoyer.")
        if len(valeur) > LONGUEUR_MAX:
            raise ValueError(f"Ton commentaire dépasse {LONGUEUR_MAX} caractères.")
        return valeur


class ArticleCommente(BaseModel):
    adresse: str | None
    titre: str


class CommentaireAuteur(BaseModel):
    """Ce que l'auteur voit de son commentaire : son état et, après un refus ou une dépublication, le motif."""

    id: UUID
    texte: str
    etat: EtatContenu
    cree_le: datetime
    publie_le: datetime | None
    article: ArticleCommente
    motif: str | None


class MesCommentaires(BaseModel):
    commentaires: list[CommentaireAuteur]


class CommentairePublic(BaseModel):
    id: UUID
    texte: str
    signature: Signature
    publie_le: datetime


class CommentairesPublics(BaseModel):
    commentaires: list[CommentairePublic]
    page: int
    pages: int
    total: int
