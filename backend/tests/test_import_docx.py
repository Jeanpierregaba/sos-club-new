"""Lecture d'un QCM Word (spec 043) : la bonne réponse est la proposition en gras."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from app.quiz.import_docx import AXES_LOT7, Incoherence, lire, vers_lot

DONNEES = Path(__file__).resolve().parents[1] / "alembic" / "donnees"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _paragraphe(texte: str, gras: bool = False) -> str:
    proprietes = "<w:rPr><w:b/></w:rPr>" if gras else ""
    return f'<w:p><w:r>{proprietes}<w:t xml:space="preserve">{texte}</w:t></w:r></w:p>'


def _docx(*paragraphes: str) -> bytes:
    corps = "".join(paragraphes)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>{corps}</w:body></w:document>'
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return tampon.getvalue()


def _question(n: int, bonne: int, nb: int = 3, gras: tuple[int, ...] | None = None) -> list[str]:
    en_gras = gras if gras is not None else (bonne,)
    return [_paragraphe(f"{n}.\tQuestion {n} ?", gras=True)] + [
        _paragraphe(f"{'abcd'[i]})\tRéponse {i}", gras=i in en_gras) for i in range(nb)
    ]


def test_lit_les_themes_les_questions_et_la_reponse_en_gras() -> None:
    document = _docx(
        _paragraphe("QUIZ SANTÉ", gras=True),
        _paragraphe("Thème 1 – Les IST", gras=True),
        *_question(1, 1),
        *_question(2, 2),
        _paragraphe("Thème 2 – Le paludisme", gras=True),
        *_question(3, 0),
    )

    themes = lire(document)

    assert [(t.numero, t.titre) for t in themes] == [(1, "Les IST"), (2, "Le paludisme")]
    assert [(q.n, q.bonne) for q in themes[0].questions] == [(1, 1), (2, 2)]
    assert themes[1].questions[0].choix == ["Réponse 0", "Réponse 1", "Réponse 2"]
    assert themes[1].questions[0].enonce == "Question 3 ?"


def test_l_apostrophe_typographique_devient_droite() -> None:
    document = _docx(_paragraphe("Thème 1 – L’hygiène", gras=True), *_question(1, 0))
    assert lire(document)[0].titre == "L'hygiène"


@pytest.mark.parametrize(
    ("question", "message"),
    [
        (_question(1, 0, gras=(0, 1)), "une seule"),
        (_question(1, 0, gras=()), "une seule"),
        (_question(1, 0, nb=2), "3 propositions"),
        (_question(1, 0, nb=4), "3 propositions"),
    ],
)
def test_refuse_un_qcm_ambigu(question: list[str], message: str) -> None:
    with pytest.raises(Incoherence, match=message):
        lire(_docx(_paragraphe("Thème 1 – IST", gras=True), *question))


def test_refuse_une_numerotation_qui_saute() -> None:
    with pytest.raises(Incoherence, match="numéro"):
        lire(_docx(_paragraphe("Thème 1 – IST", gras=True), *_question(1, 0), *_question(3, 0)))


def test_vers_lot_donne_le_format_de_la_banque() -> None:
    document = _docx(_paragraphe("Thème 1 – Les IST", gras=True), *_question(1, 1))
    lot = vers_lot(lire(document), lot=7, axes={1: "sante-sexuelle-evss"})
    assert lot == [
        {
            "titre": "Quiz Santé des Clubs · Les IST",
            "description": "Lot 7 — Quiz Santé des Clubs · thématique 1 : Les IST (questions 1 à 1).",
            "lot": 7,
            "axe": "sante-sexuelle-evss",
            "questions": [
                {"n": 1, "enonce": "Question 1 ?", "choix": ["Réponse 0", "Réponse 1", "Réponse 2"], "bonne": 1}
            ],
        }
    ]


def test_le_lot_7_commite() -> None:
    lot = json.loads((DONNEES / "quiz_sante_lot7.json").read_text(encoding="utf-8"))
    questions = [q for theme in lot for q in theme["questions"]]

    assert len(lot) == 15
    assert len(questions) == 78
    assert [q["n"] for q in questions] == list(range(1, 79))
    assert all(len(q["choix"]) == 3 and 0 <= q["bonne"] < 3 for q in questions)
    assert {theme["axe"] for theme in lot} == set(AXES_LOT7.values())
    assert {"sante-sexuelle-evss", "sante-environnement", "sport-secourisme"} == set(AXES_LOT7.values())
    assert all(theme["lot"] == 7 and theme["description"].startswith("Lot 7 — ") for theme in lot)

    banque = json.loads((DONNEES / "quiz_sante.json").read_text(encoding="utf-8"))
    titres = {quiz["titre"] for quiz in banque}
    assert not titres & {theme["titre"] for theme in lot}


def test_refuse_un_paragraphe_non_reconnu_ou_une_thematique_vide() -> None:
    with pytest.raises(Incoherence, match="non reconnu"):
        lire(_docx(_paragraphe("Thème 1 – IST", gras=True), *_question(1, 0), _paragraphe("suite de l'énoncé")))
    with pytest.raises(Incoherence, match="aucune question"):
        lire(_docx(_paragraphe("Thème 1 – IST", gras=True), _paragraphe("Thème 2 – VIH", gras=True), *_question(1, 0)))


def test_la_grille_des_reponses_de_l_animateur_termine_la_lecture() -> None:
    document = _docx(
        _paragraphe("Thème 1 – IST", gras=True),
        *_question(1, 2),
        _paragraphe("Grille des réponses (pour l'animateur ou le jury)", gras=True),
        _paragraphe("1"),
        _paragraphe("c"),
    )
    assert [q.bonne for q in lire(document)[0].questions] == [2]
