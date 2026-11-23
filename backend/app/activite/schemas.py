"""Le schéma fermé de la collecte (spec 051) : seuls ces types et ces détails passent."""

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.activite.models import TypeEvenement

# Les endroits du site d'où part un lien d'inscription (composant `LienInscription`).
ENDROITS = frozenset(
    {
        "accueil", "menu", "menu-mobile", "pied-de-page", "jeux", "quiz", "certification", "connexion",
        "genie-imhotep", "club-sante", "bibliotheque", "autre",
    }
)  # fmt: skip
PROFILS = ("eleve", "encadreur", "visiteur")
# Étapes vues par le site seulement ; les suivantes (envoi, refus, création…) sont écrites par l'API.
ETAPES_SITE = frozenset(f"{p}:{e}" for p in PROFILS for e in ("ouvert", "commence"))
CHEMINS_RECHERCHE = frozenset({"/inscription", "/carte-des-clubs"})


def nettoyer_recherche(saisie: str) -> str | None:
    """La recherche en minuscules et espaces simples ; None si elle peut contenir un numéro ou une adresse."""
    texte = " ".join(unicodedata.normalize("NFC", saisie).lower().split())[:60]
    if not texte or "@" in texte or sum(c.isdigit() for c in texte) >= 4:
        return None
    return texte


class EvenementSite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["page_vue", "clic_inscription", "etape_inscription", "recherche", "erreur"]
    chemin: str = Field(min_length=1, max_length=200)
    detail: str | None = Field(default=None, max_length=200)
    referent: str | None = Field(default=None, max_length=500)
    utm_source: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def detail_attendu(self) -> EvenementSite:
        attendu = {
            "page_vue": lambda d: d is None,
            "clic_inscription": lambda d: d in ENDROITS,
            "etape_inscription": lambda d: d in ETAPES_SITE,
            "recherche": lambda d: bool(d),
            "erreur": lambda d: d == "404",
        }[self.type]
        if not attendu(self.detail):
            raise ValueError("Détail inattendu pour ce type d'événement.")
        return self

    @property
    def type_evenement(self) -> TypeEvenement:
        return TypeEvenement(self.type)
