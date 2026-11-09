"""Champs de saisie partagés par les inscriptions (specs 018 et 030) : téléphone et texte court."""

import re
from typing import Annotated

from pydantic import AfterValidator, Field

SEPARATEURS = re.compile(r"[\s().-]")
FORMAT_TELEPHONE = re.compile(r"\+?[0-9]{8,15}")


def normaliser_telephone(valeur: str | None) -> str | None:
    """« +228 90 12-34-56 » devient « +22890123456 ». Un champ vide redevient nul."""
    if valeur is None:
        return None
    propre = SEPARATEURS.sub("", valeur)
    if not propre:
        return None
    if not FORMAT_TELEPHONE.fullmatch(propre):
        raise ValueError("Ce téléphone n'est pas valide : de 8 à 15 chiffres, avec « + » au début si besoin")
    return propre


def _texte(valeur: str | None) -> str | None:
    """Espaces normalisés ; un texte vide redevient nul."""
    if valeur is None:
        return None
    return " ".join(valeur.split()) or None


def _obligatoire(valeur: str | None) -> str:
    if not valeur:
        raise ValueError("Ce champ est obligatoire")
    return valeur


def _telephone_obligatoire(valeur: str | None) -> str:
    if not valeur:
        raise ValueError("Indique un numéro de téléphone")
    return valeur


Telephone = Annotated[str | None, Field(max_length=30), AfterValidator(normaliser_telephone)]
TelephoneObligatoire = Annotated[
    str, Field(max_length=30), AfterValidator(normaliser_telephone), AfterValidator(_telephone_obligatoire)
]


# Textes courts, espaces normalisés : facultatifs (vide = nul) ou obligatoires.
Texte30 = Annotated[str | None, Field(max_length=30), AfterValidator(_texte)]
Texte60 = Annotated[str | None, Field(max_length=60), AfterValidator(_texte)]
Texte100 = Annotated[str | None, Field(max_length=100), AfterValidator(_texte)]
Texte150 = Annotated[str | None, Field(max_length=150), AfterValidator(_texte)]
Requis100 = Annotated[str, Field(max_length=100), AfterValidator(_texte), AfterValidator(_obligatoire)]
Requis150 = Annotated[str, Field(max_length=150), AfterValidator(_texte), AfterValidator(_obligatoire)]
