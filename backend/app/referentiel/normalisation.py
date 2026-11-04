"""Clé de comparaison des noms du référentiel (spec 016) : elle porte l'unicité et la recherche, pour que
« CEG Adeho » et « CEG Adého » soient reconnus comme le même établissement."""

import unicodedata

LONGUEUR_MAX = 150


def nettoyer(nom: str, longueur_max: int = LONGUEUR_MAX) -> str:
    """Le texte tel qu'il sera affiché : espaces en trop retirés. Refuse un texte vide ou trop long."""
    propre = " ".join(nom.split())
    if not propre:
        raise ValueError("Le nom est obligatoire")
    if len(propre) > longueur_max:
        raise ValueError(f"Le nom dépasse {longueur_max} caractères")
    return propre


def normaliser(texte: str) -> str:
    """Sans accents, en minuscules, apostrophes et tirets unifiés, espaces réduits."""
    decompose = unicodedata.normalize("NFKD", texte.replace("’", "'").replace("‐", "-"))
    sans_accents = "".join(c for c in decompose if not unicodedata.combining(c))
    return " ".join(sans_accents.casefold().split())
