"""Les 200 questions de niveau expert de la certification Génie Imhotep (spec 043).

Pour chaque thématique, dans l'ordre des badges :

1. les questions des réserves des défis Expert des quiz Jeux (spec 034) de ses lots, prises tour à tour d'un défi
   à l'autre, pour que chacun en apporte autant ;
2. s'il en manque pour 40, les autres questions de ses lots, dans l'ordre du document ;
3. jamais deux fois la même question (énoncé normalisé), même d'une thématique à l'autre.

Les 40 questions sont ensuite distribuées tour à tour entre les 4 places de la thématique : chaque quiz mêle
défis Expert et complément.

La commande lit la banque d'une base et écrit le fichier relu puis chargé par la migration :

    uv run python -m app.certification.selection_expert alembic/donnees/certification_expert.json
"""

import argparse
import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import text

from app.certification.regles import THEMATIQUES, Thematique
from app.db import SessionLocal
from app.quiz.models import PLACES_PAR_THEMATIQUE
from app.referentiel.normalisation import normaliser

PAR_PLACE = 10
PAR_THEMATIQUE = PAR_PLACE * PLACES_PAR_THEMATIQUE


class Insuffisant(ValueError):
    """Une thématique n'a pas assez de questions distinctes."""


@dataclass(frozen=True)
class QuestionBanque:
    lot: int
    enonce: str
    choix: list[str]
    bonne: int
    explication: str
    origine: str = ""


@dataclass(frozen=True)
class DefiExpert:
    numero: int
    lot: int
    questions: list[QuestionBanque]


@dataclass
class PlaceExpert:
    place: int
    badge: str
    axe: str
    rang: int  # 1 à 4 dans la thématique
    questions: list[QuestionBanque] = field(default_factory=list)

    @property
    def titre(self) -> str:
        return f"Génie Imhotep {self.place} — {self.badge} ({self.rang}/{PLACES_PAR_THEMATIQUE})"


def _avec_origine(q: QuestionBanque, origine: str) -> QuestionBanque:
    return QuestionBanque(q.lot, q.enonce, q.choix, q.bonne, q.explication, origine)


def selectionner(
    banque: list[QuestionBanque], defis: list[DefiExpert], thematiques: tuple[Thematique, ...] = THEMATIQUES
) -> list[PlaceExpert]:
    vues: set[str] = set()
    places: list[PlaceExpert] = []

    def prendre(q: QuestionBanque, origine: str, choisies: list[QuestionBanque]) -> bool:
        cle = normaliser(q.enonce)
        if cle in vues:
            return False
        vues.add(cle)
        choisies.append(_avec_origine(q, origine))
        return True

    for indice, thematique in enumerate(thematiques):
        choisies: list[QuestionBanque] = []
        files = [
            (f"défi n° {d.numero}", list(d.questions))
            for d in sorted(defis, key=lambda d: d.numero)
            if d.lot in thematique.lots
        ]
        # Tour à tour : chaque défi donne sa prochaine question encore libre.
        while len(choisies) < PAR_THEMATIQUE and any(file for _, file in files):
            for origine, file in files:
                while file and not prendre(file.pop(0), origine, choisies):
                    pass
                if len(choisies) == PAR_THEMATIQUE:
                    break
        for q in banque:
            if len(choisies) == PAR_THEMATIQUE:
                break
            if q.lot in thematique.lots:
                prendre(q, f"lot {q.lot}", choisies)
        if len(choisies) < PAR_THEMATIQUE:
            raise Insuffisant(
                f"« {thematique.badge} » : {len(choisies)} questions distinctes, il en faut {PAR_THEMATIQUE}."
            )

        debut = indice * PLACES_PAR_THEMATIQUE
        du_theme = [
            PlaceExpert(debut + rang, thematique.badge, thematique.axe, rang)
            for rang in range(1, PLACES_PAR_THEMATIQUE + 1)
        ]
        for i, q in enumerate(choisies):
            # Décalage d'une place à chaque tour : deux défis qui alternent se répartissent sur les 4 places.
            du_theme[(i + i // PLACES_PAR_THEMATIQUE) % PLACES_PAR_THEMATIQUE].questions.append(q)
        places.extend(du_theme)
    return places


def vers_json(places: list[PlaceExpert]) -> list[dict]:
    return [
        {
            "place": p.place,
            "badge": p.badge,
            "axe": p.axe,
            "titre": p.titre,
            "questions": [
                {
                    "enonce": q.enonce,
                    "choix": q.choix,
                    "bonne": q.bonne,
                    "explication": q.explication,
                    "origine": q.origine,
                }
                for q in p.questions
            ],
        }
        for p in places
    ]


# Les questions actives de la banque (les quiz « Lot N — » du Jeu Quiz Santé), dans l'ordre du document, comme la
# migration des 100 défis (`0b5d089c2f2d`) les a lues.
_BANQUE = text(
    "SELECT substring(q.description from '^Lot (\\d+)')::int AS lot, qq.enonce, qq.choix, qq.bonne_reponse, "
    "qq.explication FROM question_quiz qq JOIN quiz q ON q.id = qq.quiz_id "
    "WHERE q.parcours = 'jeux' AND NOT q.contenu_de_test AND q.numero IS NULL AND qq.active "
    "AND q.description ~ '^Lot \\d+ — ' ORDER BY lot, q.publie_le, q.titre, qq.ordre"
)
_DEFIS = text(
    "SELECT q.numero, q.lot, qq.enonce, qq.choix, qq.bonne_reponse, qq.explication FROM question_quiz qq "
    "JOIN quiz q ON q.id = qq.quiz_id WHERE q.parcours = 'jeux' AND q.niveau = 'expert' AND q.etat = 'publie' "
    "AND NOT q.contenu_de_test AND qq.active ORDER BY q.numero, qq.ordre"
)


async def _lire() -> tuple[list[QuestionBanque], list[DefiExpert]]:
    async with SessionLocal() as db:
        banque = [
            QuestionBanque(r.lot, r.enonce, list(r.choix), r.bonne_reponse, r.explication or "")
            for r in (await db.execute(_BANQUE)).all()
        ]
        par_defi: dict[tuple[int, int], list[QuestionBanque]] = {}
        for r in (await db.execute(_DEFIS)).all():
            par_defi.setdefault((r.numero, r.lot), []).append(
                QuestionBanque(r.lot, r.enonce, list(r.choix), r.bonne_reponse, r.explication or "")
            )
    return banque, [DefiExpert(numero, lot, questions) for (numero, lot), questions in par_defi.items()]


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("sortie", type=Path)
    arguments = parseur.parse_args()
    banque, defis = asyncio.run(_lire())
    places = selectionner(banque, defis)
    arguments.sortie.write_text(json.dumps(vers_json(places), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{sum(len(p.questions) for p in places)} questions sur {len(places)} places → {arguments.sortie}")


if __name__ == "__main__":
    main()
