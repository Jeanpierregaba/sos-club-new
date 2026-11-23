"""La banque officielle de 1 000 questions (spec 049) : lecture du document et composition des quiz."""

import json
from collections import Counter
from pathlib import Path

import pytest

from app.quiz.banque_officielle import AXES, Incoherence, Partie, composer, lire
from app.quiz.import_docx import Question
from tests.test_import_docx import _docx, _paragraphe, _question

FICHIER = Path(__file__).resolve().parents[1] / "alembic" / "donnees" / "banque_officielle.json"
# Les effectifs du document : (moyennement difficiles, très difficiles) par partie.
EFFECTIFS = {1: (180, 120), 2: (150, 100), 3: (120, 80), 4: (150, 100)}


def _questions(debut: int, nombre: int) -> list[Question]:
    return [Question(n, f"Question {n} ?", ["a", "b", "c"], [n % 3]) for n in range(debut, debut + nombre)]


def _banque() -> list[Partie]:
    parties, n = [], 1
    for numero, (m, d) in EFFECTIFS.items():
        parties.append(Partie(numero, f"Partie {numero}", _questions(n, m), _questions(n + m, d)))
        n += m + d
    return parties


def test_lit_les_parties_les_deux_blocs_et_la_reponse_en_gras() -> None:
    document = _docx(
        _paragraphe("BANQUE DE 1 000 QUESTIONS"),
        _paragraphe("Partie 1 – Santé publique (questions 1 à 3)"),
        _paragraphe("Questions moyennement difficiles"),
        *_question(1, 0),
        *_question(2, 2),
        _paragraphe("Questions très difficiles"),
        *_question(3, 1),
        _paragraphe("Partie 2 – EVSS (questions 4 à 5)"),
        _paragraphe("Questions moyennement difficiles"),
        *_question(4, 1),
        _paragraphe("Questions très difficiles"),
        *_question(5, 0),
    )

    parties = lire(document)

    assert [(p.numero, p.titre) for p in parties] == [(1, "Santé publique"), (2, "EVSS")]
    assert [(q.n, q.bonne) for q in parties[0].moyennes] == [(1, 0), (2, 2)]
    assert [(q.n, q.bonne) for q in parties[0].difficiles] == [(3, 1)]
    assert [q.n for q in parties[1].moyennes + parties[1].difficiles] == [4, 5]


@pytest.mark.parametrize(
    "question",
    [_question(1, 0, gras=(0, 1)), _question(1, 0, gras=()), _question(1, 0, nb=2)],
    ids=["deux-en-gras", "aucune-en-gras", "deux-propositions"],
)
def test_refuse_un_qcm_ambigu(question: list[str]) -> None:
    document = _docx(
        _paragraphe("Partie 1 – Santé publique"),
        _paragraphe("Questions moyennement difficiles"),
        *question,
        _paragraphe("Questions très difficiles"),
        *_question(2, 0),
    )
    with pytest.raises(Incoherence):
        lire(document)


def test_refuse_une_partie_sans_bloc_tres_difficile() -> None:
    document = _docx(
        _paragraphe("Partie 1 – Santé publique"), _paragraphe("Questions moyennement difficiles"), *_question(1, 0)
    )
    with pytest.raises(Incoherence, match="deux blocs"):
        lire(document)


def test_composition_80_quiz_jeux_et_20_places_sans_recouvrement() -> None:
    banque = _banque()
    difficiles = {q.n for p in banque for q in p.difficiles}

    donnees = composer(banque)

    jeux, places = donnees["jeux"], donnees["certification"]
    assert Counter(q["niveau"] for q in jeux) == {"debutant": 32, "intermediaire": 24, "avance": 16, "expert": 8}
    assert [q["numero"] for q in jeux] == list(range(1, 81))
    assert [p["place"] for p in places] == list(range(1, 21))
    assert all(len(q["questions"]) == 10 for q in jeux + places)
    n_jeux = {x["n"] for q in jeux for x in q["questions"]}
    n_certif = {x["n"] for p in places for x in p["questions"]}
    assert not n_jeux & n_certif
    assert len(n_jeux) == 800 and len(n_certif) == 200
    assert n_certif <= difficiles
    # Un quiz Jeux ne mêle ni deux parties ni deux difficultés ; les niveaux M passent avant les niveaux D.
    for q in jeux:
        ns = {x["n"] for x in q["questions"]}
        assert ns <= difficiles or not ns & difficiles
    assert all(not {x["n"] for x in q["questions"]} & difficiles for q in jeux[:60])
    assert all({x["n"] for x in q["questions"]} <= difficiles for q in jeux[60:])


def test_places_par_partie_puis_melange() -> None:
    banque = _banque()
    partie_de = {q.n: p.numero for p in banque for q in p.difficiles}

    places = composer(banque)["certification"]

    for place in places[:16]:
        assert {partie_de[x["n"]] for x in place["questions"]} == {(place["place"] - 1) // 4 + 1}
        assert place["axe"] == AXES[(place["place"] - 1) // 4 + 1]
    melange = Counter(partie_de[x["n"]] for p in places[16:] for x in p["questions"])
    assert melange == {1: 10, 2: 10, 3: 10, 4: 10}
    assert places[0]["titre"] == "Génie Imhotep 1 — Ambassadeur Santé Junior (1/4)"
    assert places[19]["titre"] == "Génie Imhotep 20 — Maître Génie Imhotep (4/4)"


def test_refuse_une_partie_trop_courte_pour_la_certification() -> None:
    banque = _banque()
    banque[2].difficiles = banque[2].difficiles[:40]
    with pytest.raises(Incoherence, match="très difficiles"):
        composer(banque)


def test_le_fichier_commite() -> None:
    donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
    jeux, places = donnees["jeux"], donnees["certification"]
    questions = [x for q in jeux + places for x in q["questions"]]

    assert len(jeux) == 80 and len(places) == 20
    assert sorted(x["n"] for x in questions) == list(range(1, 1001))
    assert len({x["enonce"].casefold() for x in questions}) == 1000
    assert all(len(x["choix"]) == 3 and x["bonne"] in (0, 1, 2) for x in questions)
    assert all(len(x["enonce"]) <= 300 for x in questions)
    assert Counter(q["niveau"] for q in jeux) == {"debutant": 32, "intermediaire": 24, "avance": 16, "expert": 8}
    # Les places 1 à 16 puisent dans la partie de leur thématique (numéros du document), les 4 dernières mêlent.
    bornes = {1: (1, 300), 2: (301, 550), 3: (551, 750), 4: (751, 1000)}
    for place in places[:16]:
        debut, fin = bornes[(place["place"] - 1) // 4 + 1]
        assert all(debut <= x["n"] <= fin for x in place["questions"])
