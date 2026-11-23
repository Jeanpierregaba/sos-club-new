"""Réponses de la page « Activité » (spec 051) : une même forme pour les 8 blocs, que le site affiche et exporte
sans connaître chaque indicateur. Jamais de ligne par personne : seulement des totaux."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

Unite = Literal["nombre", "pourcent", "secondes", "texte"]
NomBloc = Literal["audience", "inscription", "jeux", "certification", "contenus", "regions", "retention", "erreurs"]


class Chiffre(BaseModel):
    cle: str
    libelle: str
    valeur: float | None
    # La même mesure sur la période précédente de même durée ; None si elle n'a pas de sens.
    precedent: float | None = None
    unite: Unite = "nombre"


class PointSerie(BaseModel):
    jour: date
    valeur: float


class Serie(BaseModel):
    cle: str
    libelle: str
    points: list[PointSerie]


class Colonne(BaseModel):
    cle: str
    libelle: str
    unite: Unite = "nombre"


class Tableau(BaseModel):
    cle: str
    titre: str
    colonnes: list[Colonne]
    lignes: list[dict[str, str | float | None]]


class Grille(BaseModel):
    """Une heatmap jour de la semaine (0 = lundi) × heure (0 à 23, heure de Lomé)."""

    cle: str
    titre: str
    valeurs: list[list[int]]


class Bloc(BaseModel):
    bloc: NomBloc
    du: date
    au: date
    precedent_du: date
    precedent_au: date
    chiffres: list[Chiffre] = []
    series: list[Serie] = []
    tableaux: list[Tableau] = []
    grilles: list[Grille] = []
    notes: list[str] = []
