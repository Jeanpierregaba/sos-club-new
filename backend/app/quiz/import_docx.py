"""Lecture d'un QCM rédigé sous Word (spec 043) : thématiques, questions numérotées, propositions a), b), c), et la
bonne réponse mise en gras.

Le document est lu tel qu'il est enregistré (`word/document.xml`), avec la bibliothèque standard. Un QCM ambigu
(aucune ou plusieurs propositions en gras, autre chose que 3 propositions, numéro qui saute) est refusé : rien
n'entre dans la banque sans une seule bonne réponse certaine.

    uv run python -m app.quiz.import_docx <document.docx> <sortie.json> [--lot 7]
"""

import argparse
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NB_CHOIX = 3
# Après les questions, le document donne la grille des réponses pour l'animateur ou le jury.
FIN = "Grille des réponses"

# Le document « Quiz Santé – 78 questions » des Clubs Santé (2026-11-19) : l'axe de chacune de ses 15 thématiques.
AXES_LOT7: dict[int, str] = {
    **dict.fromkeys(range(1, 6), "sante-sexuelle-evss"),  # IST, VIH, VPH, grossesses précoces, VBG
    **dict.fromkeys((6, 7, 8), "sante-environnement"),  # drogue, écrans, santé mentale
    9: "sport-secourisme",  # accidents de la voie publique
    **dict.fromkeys(range(10, 16), "sante-environnement"),  # paludisme à affections bucco-dentaires
}

_THEME = re.compile(r"^Thème\s+(\d+)\s*[–—-]\s*(.+)$")
_QUESTION = re.compile(r"^(\d+)\.\s*(.+)$")
_CHOIX = re.compile(r"^([a-z])\)\s*(.+)$")


class Incoherence(ValueError):
    """Le document ne se lit pas sans ambiguïté."""


@dataclass
class Question:
    n: int
    enonce: str
    choix: list[str] = field(default_factory=list)
    en_gras: list[int] = field(default_factory=list)

    @property
    def bonne(self) -> int:
        return self.en_gras[0]


@dataclass
class Theme:
    numero: int
    titre: str
    questions: list[Question] = field(default_factory=list)


def _propre(texte: str) -> str:
    return re.sub(r"\s+", " ", texte.replace("’", "'").replace(" ", " ")).strip()


def _gras(run: ET.Element) -> bool:
    b = run.find(f"{W}rPr/{W}b")
    return b is not None and b.get(f"{W}val", "true") not in ("0", "false")


def _paragraphes(contenu: bytes) -> list[tuple[str, bool]]:
    """Chaque paragraphe : son texte, et s'il porte du texte en gras."""
    with zipfile.ZipFile(io.BytesIO(contenu)) as archive:
        racine = ET.fromstring(archive.read("word/document.xml"))
    sortie = []
    for p in racine.iter(f"{W}p"):
        texte, gras = "", False
        for run in p.iter(f"{W}r"):
            morceau = "".join(t.text or "" for t in run.iter(f"{W}t"))
            texte += morceau
            gras = gras or (bool(morceau.strip()) and _gras(run))
        if texte.strip():
            sortie.append((texte.strip(), gras))
    return sortie


def lire(contenu: bytes) -> list[Theme]:
    themes: list[Theme] = []
    for texte, gras in _paragraphes(contenu):
        if texte.startswith(FIN):
            break  # la grille des réponses de l'animateur : elle redit le gras, contrôlée à part
        if m := _THEME.match(texte):
            themes.append(Theme(int(m[1]), _propre(m[2])))
        elif not themes:
            continue  # titre, sommaire : avant la première thématique
        elif m := _QUESTION.match(texte):
            themes[-1].questions.append(Question(int(m[1]), _propre(m[2])))
        elif (m := _CHOIX.match(texte)) and themes[-1].questions:
            question = themes[-1].questions[-1]
            if gras:
                question.en_gras.append(len(question.choix))
            question.choix.append(_propre(m[2]))
        else:
            # Un énoncé sur deux paragraphes, une note : rien ne se perd sans qu'on le sache.
            raise Incoherence(f"Paragraphe non reconnu dans « {themes[-1].titre} » : « {texte[:80]} ».")

    attendu = 1
    for theme in themes:
        if not theme.questions:
            raise Incoherence(f"La thématique « {theme.titre} » n'a aucune question.")
        for q in theme.questions:
            if q.n != attendu:
                raise Incoherence(f"Question {q.n} : numéro inattendu, la question {attendu} était attendue.")
            if len(q.choix) != NB_CHOIX:
                raise Incoherence(f"Question {q.n} : {len(q.choix)} propositions, il en faut {NB_CHOIX} propositions.")
            if len(q.en_gras) != 1:
                raise Incoherence(f"Question {q.n} : il faut une seule proposition en gras ({len(q.en_gras)}).")
            attendu += 1
    return themes


def vers_lot(themes: list[Theme], *, lot: int, axes: dict[int, str]) -> list[dict]:
    """Le format de `alembic/donnees/quiz_sante.json` : un quiz par thématique."""
    return [
        {
            "titre": f"Quiz Santé des Clubs · {theme.titre}",
            "description": (
                f"Lot {lot} — Quiz Santé des Clubs · thématique {theme.numero} : {theme.titre} "
                f"(questions {theme.questions[0].n} à {theme.questions[-1].n})."
            ),
            "lot": lot,
            "axe": axes[theme.numero],
            "questions": [{"n": q.n, "enonce": q.enonce, "choix": q.choix, "bonne": q.bonne} for q in theme.questions],
        }
        for theme in themes
    ]


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("document", type=Path)
    parseur.add_argument("sortie", type=Path)
    parseur.add_argument("--lot", type=int, default=7)
    arguments = parseur.parse_args()
    themes = lire(arguments.document.read_bytes())
    donnees = vers_lot(themes, lot=arguments.lot, axes=AXES_LOT7)
    arguments.sortie.write_text(json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{sum(len(t.questions) for t in themes)} questions en {len(themes)} thématiques → {arguments.sortie}")


if __name__ == "__main__":
    main()
