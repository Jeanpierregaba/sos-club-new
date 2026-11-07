"""Articles (spec 023). Le texte est un sous-ensemble de Markdown, stocké tel quel : le site n'en interprète que
les paragraphes, intertitres, gras, italique et listes, jamais de HTML ni de lien."""

import re
from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.moderation.models import EtatContenu, TypeDecision

# Caractères de contrôle, sauf la tabulation et le retour à la ligne.
_CONTROLE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _propre(texte: str) -> str:
    texte = texte.replace("\r\n", "\n").replace("\r", "\n")
    if _CONTROLE.search(texte):
        raise ValueError("Le texte contient des caractères non autorisés.")
    return texte


def _une_ligne(texte: str) -> str:
    if "\n" in texte:
        raise ValueError("Ce champ tient sur une seule ligne.")
    return texte


Titre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=120), AfterValidator(_propre),
                  AfterValidator(_une_ligne)]  # fmt: skip
Chapo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=300), AfterValidator(_propre)]
Texte = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20_000), AfterValidator(_propre)
]


class ChampsArticle(BaseModel):
    """Les champs d'une version, stockés en JSONB (`version_contenu.donnees`)."""

    titre: Titre
    chapo: Chapo
    texte: Texte
    axe_code: str = Field(max_length=40)
    # Pour un élève : son club apparaît avec son pseudonyme (Q20). Sans effet pour un encadreur.
    afficher_club: bool = True


class ArticleEcriture(ChampsArticle):
    """Création et modification. `version` (verrou optimiste) est exigée pour une modification."""

    version: int | None = None


class VersionEntree(BaseModel):
    version: int


class DerniereDecision(BaseModel):
    decision: TypeDecision
    motif: str | None
    decide_le: datetime


Legende = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=200), AfterValidator(_propre), AfterValidator(_une_ligne)
]


class PhotoAuteur(BaseModel):
    id: UUID
    legende: str | None
    couverture: bool
    ordre: int
    largeur: int
    hauteur: int
    # Fichiers effacés 90 jours après un refus : il ne reste que la légende et l'attestation.
    effacee: bool


class PhotoModification(BaseModel):
    version: int
    legende: Legende | None = None
    couverture: bool | None = None
    ordre: int | None = Field(default=None, ge=0, le=100)


class ArticleAuteur(BaseModel):
    id: UUID
    etat: EtatContenu
    version: int
    # La version que l'auteur voit et modifie : celle de travail, sinon celle en ligne.
    champs: ChampsArticle
    # Une version approuvée est en ligne, même pendant la modération d'une nouvelle version.
    en_ligne: bool
    adresse: str | None
    modifiable: bool
    soumettable: bool
    supprimable: bool
    derniere_decision: DerniereDecision | None
    photos: list[PhotoAuteur]
    soumis_le: datetime | None
    publie_le: datetime | None
    modifie_le: datetime


class ResumeArticleAuteur(BaseModel):
    id: UUID
    titre: str
    etat: EtatContenu
    en_ligne: bool
    adresse: str | None
    modifie_le: datetime


class MesArticles(BaseModel):
    articles: list[ResumeArticleAuteur]


# Lecture publique ----------------------------------------------------------------------------------------------


class Signature(BaseModel):
    """Jamais de nom complet : un élève par son pseudonyme (et son club s'il l'a choisi), un encadreur par son
    prénom, l'initiale de son nom et sa fonction."""

    profil: str
    nom: str
    club: str | None = None
    fonction: str | None = None


class AxeArticle(BaseModel):
    code: str
    libelle: str


class PhotoPublique(BaseModel):
    id: UUID
    legende: str | None
    largeur: int
    hauteur: int


class ResumeArticle(BaseModel):
    adresse: str
    titre: str
    chapo: str
    axe: AxeArticle
    signature: Signature
    couverture: PhotoPublique | None
    publie_le: date


class ArticlesPublics(BaseModel):
    articles: list[ResumeArticle]
    page: int
    pages: int
    total: int


class ArticlePublic(ResumeArticle):
    texte: str
    # Les autres photos, en galerie sous le texte (spec 024).
    photos: list[PhotoPublique]
