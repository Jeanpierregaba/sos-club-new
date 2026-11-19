"""Sélection des 200 questions de niveau expert de la certification (spec 043), sans base."""

import json
from pathlib import Path

import pytest

from app.certification.regles import NOMS_PAR_DEFAUT, THEMATIQUES, Thematique
from app.certification.selection_expert import (
    PAR_PLACE,
    DefiExpert,
    Insuffisant,
    QuestionBanque,
    selectionner,
)
from app.referentiel.normalisation import normaliser

DONNEES = Path(__file__).resolve().parents[1] / "alembic" / "donnees"


def _q(lot: int, n: int, texte: str | None = None) -> QuestionBanque:
    return QuestionBanque(
        lot=lot, enonce=texte or f"Lot {lot}, question {n} ?", choix=["A", "B", "C"], bonne=n % 3, explication=""
    )


def _banque(lot: int, nombre: int) -> list[QuestionBanque]:
    return [_q(lot, n) for n in range(1, nombre + 1)]


def _thematiques(*lots: tuple[int, ...]) -> tuple[Thematique, ...]:
    return tuple(Thematique(f"Badge {i}", f"axe-{i}", l) for i, l in enumerate(lots, start=1))


def test_les_defis_expert_d_abord_puis_le_meme_lot() -> None:
    banque = _banque(1, 60)
    defi = DefiExpert(numero=8, lot=1, questions=banque[30:50])

    places = selectionner(banque, [defi], _thematiques((1,)))

    assert [p.place for p in places] == [1, 2, 3, 4]
    choisies = [q for p in places for q in p.questions]
    assert len(choisies) == 40
    assert {q.enonce for q in choisies if q.origine == "défi n° 8"} == {q.enonce for q in banque[30:50]}
    # Le complément suit l'ordre du document, sans reprendre une question du défi.
    complement = [q.enonce for q in choisies if q.origine == "lot 1"]
    assert sorted(complement, key=lambda e: int(e.split()[-2])) == [q.enonce for q in banque[:20]]
    # Chaque place mêle défi Expert et complément.
    for place in places:
        assert len(place.questions) == PAR_PLACE
        assert {q.origine for q in place.questions} == {"défi n° 8", "lot 1"}


def test_a_parts_egales_entre_les_defis_expert() -> None:
    banque = _banque(3, 30) + _banque(5, 30)
    defis = [
        DefiExpert(numero=76, lot=3, questions=banque[0:20]),
        DefiExpert(numero=34, lot=5, questions=banque[30:50]),
        DefiExpert(numero=83, lot=3, questions=banque[20:30] + banque[50:60]),
    ]

    places = selectionner(banque, defis, _thematiques((3, 5)))
    origines = [q.origine for p in places for q in p.questions]

    assert len(origines) == 40
    assert all(o.startswith("défi") for o in origines)
    # Tour à tour, dans l'ordre des défis : 34, 76, 83, 34…
    assert {o: origines.count(o) for o in set(origines)} == {"défi n° 34": 14, "défi n° 76": 13, "défi n° 83": 13}


def test_aucune_question_en_double_meme_entre_deux_thematiques() -> None:
    commun = "Quelle est la question commune ?"
    banque = [*_banque(1, 45), _q(1, 99, commun), *_banque(2, 45), _q(2, 99, commun.upper())]
    places = selectionner(
        banque,
        [DefiExpert(1, 1, [banque[45], *banque[:19]]), DefiExpert(2, 2, [banque[-1], *banque[46:65]])],
        _thematiques((1,), (2,)),
    )

    enonces = [normaliser(q.enonce) for p in places for q in p.questions]
    assert len(enonces) == 80
    assert len(set(enonces)) == 80
    assert [p.place for p in places] == list(range(1, 9))


def test_refuse_une_thematique_sans_40_questions() -> None:
    banque = _banque(1, 39)
    with pytest.raises(Insuffisant, match="39"):
        selectionner(banque, [], _thematiques((1,)))


def test_titre_et_axe_de_chaque_place() -> None:
    banque = _banque(1, 40)
    places = selectionner(banque, [], (Thematique("Ambassadeur Santé Junior", "production-tv-medias", (1,)),))
    assert [p.titre for p in places] == [f"Génie Imhotep {n} — Ambassadeur Santé Junior ({n}/4)" for n in range(1, 5)]
    assert {p.axe for p in places} == {"production-tv-medias"}


def test_les_200_questions_commitees() -> None:
    places = json.loads((DONNEES / "certification_expert.json").read_text(encoding="utf-8"))

    assert [p["place"] for p in places] == list(range(1, 21))
    enonces = [normaliser(q["enonce"]) for p in places for q in p["questions"]]
    assert len(enonces) == 200
    assert len(set(enonces)) == 200
    for p in places:
        thematique = THEMATIQUES[(p["place"] - 1) // 4]
        assert p["axe"] == thematique.axe
        assert p["badge"] == thematique.badge == NOMS_PAR_DEFAUT[(p["place"] - 1) // 4]
        assert len(p["questions"]) == PAR_PLACE
        for q in p["questions"]:
            assert len(q["choix"]) >= 2
            assert 0 <= q["bonne"] < len(q["choix"])
    # Places 9 à 20 : uniquement des défis Expert.
    assert all(q["origine"].startswith("défi") for p in places[8:] for q in p["questions"])
    # Places 1 à 8 : 20 questions de défi Expert par thématique, le reste du même lot.
    for debut in (0, 4):
        origines = [q["origine"] for p in places[debut : debut + 4] for q in p["questions"]]
        assert sum(o.startswith("défi") for o in origines) == 20
