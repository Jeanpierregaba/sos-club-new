"""Doublons probables d'établissements (spec 042) : les règles de l'analyse du 2026-11-18, en fonctions pures.

Trois raisons de rapprocher deux établissements d'une même DRE et d'une même famille de sigle (un lycée et un CEG
du même quartier sont deux établissements) :

- **même nom** une fois retirés ponctuation, accents, apostrophes et mots de liaison, chiffres romains lus comme
  arabes : « Lycée de Tokoin I » et « Lycée Tokoin I », « CEG Bogou 2 » et « CEG Bogou II » ;
- **même prononciation** : k et c, ou et u, dj, dz et j, lettres doublées (« CEG Ossakré » et « CEG Ossacre ») ;
- **nom proche** : une ou deux lettres d'écart (« CEG Warkanbou » et « CEG Warkambou »).

Deux noms dont les éléments distinctifs diffèrent (numéro, lettre seule, point cardinal, « annexe ») ne sont jamais
rapprochés : « CPL La Fabienne I » et « CPL La Fabienne III », « CEG Bassar Est » et « CEG Bassar Ouest ».
"""

import re
from collections import defaultdict
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum
from itertools import combinations
from typing import Any

from app.referentiel.normalisation import normaliser

SEUIL = 0.88
LONGUEUR_MIN = 5

ROMAINS = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9",
           "x": "10"}  # fmt: skip
LIAISONS = {"de", "du", "des", "la", "le", "les", "et", "a", "au", "aux", "en", "sur", "pour"}
# Les mots qui distinguent deux établissements voisins du même nom.
DISTINCTIFS = {"est", "ouest", "nord", "sud", "centre", "haut", "bas", "annexe"}
# Le premier mot du nom : sa famille. Les sigles des collèges privés (laïc, catholique, protestant…) en forment une
# seule, l'ordre étant souvent mal saisi dans l'un des deux fichiers.
FAMILLES = {
    "ceg": "ceg", "lycee": "lycee", "lpl": "lycee", "college": "college",
    "cpl": "prive", "cpc": "prive", "cpe": "prive", "cpi": "prive", "cpp": "prive", "cpa": "prive",
    "cs": "complexe", "csi": "complexe", "cspl": "complexe", "complexe": "complexe", "groupe": "complexe",
}  # fmt: skip
SONS = (("ou", "u"), ("dj", "j"), ("dz", "j"), ("c", "k"), ("ph", "f"))


class Raison(StrEnum):
    meme_nom = "meme_nom"
    meme_prononciation = "meme_prononciation"
    nom_proche = "nom_proche"


@dataclass(frozen=True)
class Fiche:
    id: Any
    nom: str
    iesg_id: Hashable
    dre_code: str


@dataclass(frozen=True)
class Paire:
    a: Fiche
    b: Fiche
    raison: Raison


def mots(nom: str) -> list[str]:
    """Les mots du nom, sans accents ni ponctuation, élisions (d', l') retirées, apostrophes internes collées
    (« N'Djei » → « ndjei »), chiffres romains en chiffres arabes."""
    texte = re.sub(r"\b[dl]'", " ", normaliser(nom)).replace("'", "")
    return [ROMAINS.get(m, m) for m in re.split(r"[^a-z0-9]+", texte) if m]


def famille(nom: str) -> str:
    premier = (mots(nom) or [""])[0]
    return FAMILLES.get(premier, premier)


def corps(nom: str) -> str:
    """Le nom sans son premier mot (le sigle ou le type) ni les mots de liaison."""
    reste = mots(nom)[1:] or mots(nom)
    return " ".join(m for m in reste if m not in LIAISONS)


def distinctifs(nom: str) -> frozenset[str]:
    return frozenset(m for m in corps(nom).split() if m.isdigit() or len(m) == 1 or m in DISTINCTIFS)


def prononciation(nom: str) -> str:
    texte = corps(nom).replace(" ", "")
    for ecrit, son in SONS:
        texte = texte.replace(ecrit, son)
    texte = re.sub(r"(.)\1+", r"\1", texte)
    return re.sub(r"e$", "", texte)


def _proche(a: str, b: str) -> bool:
    if min(len(a), len(b)) < LONGUEUR_MIN or 2 * min(len(a), len(b)) / (len(a) + len(b)) < SEUIL:
        return False
    comparaison = SequenceMatcher(None, a, b)
    return comparaison.quick_ratio() >= SEUIL and comparaison.ratio() >= SEUIL


def paires(fiches: Iterable[Fiche]) -> list[Paire]:
    """Les paires probablement en double, chacune une seule fois (le plus petit identifiant d'abord), avec la
    raison la plus forte."""
    trouvees: dict[tuple[Any, Any], Paire] = {}

    def ajouter(x: Fiche, y: Fiche, raison: Raison) -> None:
        a, b = (x, y) if x.id < y.id else (y, x)
        if (a.id, b.id) not in trouvees and distinctifs(a.nom) == distinctifs(b.nom):
            trouvees[(a.id, b.id)] = Paire(a, b, raison)

    familles: defaultdict[tuple[str, str], list[tuple[Fiche, str]]] = defaultdict(list)
    for f in fiches:
        familles[(f.dre_code, famille(f.nom))].append((f, corps(f.nom)))

    for groupe in familles.values():
        for raison, cle in ((Raison.meme_nom, corps), (Raison.meme_prononciation, prononciation)):
            memes: defaultdict[str, list[Fiche]] = defaultdict(list)
            for f, _ in groupe:
                memes[cle(f.nom)].append(f)
            for liste in memes.values():
                for x, y in combinations(liste, 2):
                    ajouter(x, y, raison)
        colles = [(f, c.replace(" ", "")) for f, c in groupe]
        for (x, cx), (y, cy) in combinations(colles, 2):
            if cx != cy and _proche(cx, cy):
                ajouter(x, y, Raison.nom_proche)
    return sorted(trouvees.values(), key=lambda p: (p.a.dre_code, str(p.a.iesg_id), normaliser(p.a.nom)))
