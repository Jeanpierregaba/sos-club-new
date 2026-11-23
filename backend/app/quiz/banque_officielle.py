"""La banque officielle de 1 000 questions des Clubs Santé (spec 049) : lecture du document Word et composition des
80 quiz Jeux et des 20 quiz de certification.

Le document a 4 parties (« Partie N – … »), chacune en deux blocs : « Questions moyennement difficiles » (M) puis
« Questions très difficiles » (D). Chaque QCM a 3 propositions, la bonne en gras (lecture de `import_docx`).

Composition :

- 50 questions D par partie sont réservées à la certification, prises à intervalles réguliers dans l'ordre du
  document : 40 pour les 4 places de la partie, 10 pour les places 17 à 20, qui mêlent les 4 parties ;
- les 800 autres font 80 quiz Jeux de 10 questions, chacun d'une seule partie et d'une seule difficulté ;
- les quiz M remplissent les niveaux Débutant (32), Intermédiaire (24) et Avancé (4) ; les quiz D, Avancé (12) et
  Expert (8). Les parties sont alternées dans l'ordre du parcours.

    uv run python -m app.quiz.banque_officielle <document.docx> alembic/donnees/banque_officielle.json
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.certification.regles import NOMS_PAR_DEFAUT
from app.quiz.import_docx import _CHOIX, _QUESTION, NB_CHOIX, Incoherence, Question, _paragraphes, _propre
from app.quiz.models import PLACES_PAR_THEMATIQUE

PAR_QUIZ = 10
RESERVE_CERTIFICATION = 50  # questions D par partie
POUR_LE_MELANGE = 10  # sur ces 50, celles des places 17 à 20
NIVEAUX_M = (("debutant", 32), ("intermediaire", 24), ("avance", 4))
NIVEAUX_D = (("avance", 12), ("expert", 8))
DESCRIPTION = "Banque officielle des Clubs Santé (spec 049)"

# L'axe de chaque partie du document.
AXES: dict[int, str] = {
    1: "sport-secourisme",  # santé publique
    2: "sante-sexuelle-evss",  # santé sexuelle et reproductive
    3: "sante-environnement",  # journées mondiales de la santé
    4: "sante-sexuelle-evss",  # EVSS
}
AXE_MELANGE = "genie-imhotep"

_PARTIE = re.compile(r"^Partie\s+(\d+)\s*[–—-]\s*(.+?)\s*(\(.*\))?$")
_MOYEN = "Questions moyennement difficiles"
_DIFFICILE = "Questions très difficiles"


@dataclass
class Partie:
    numero: int
    titre: str
    moyennes: list[Question] = field(default_factory=list)
    difficiles: list[Question] = field(default_factory=list)


def lire(contenu: bytes) -> list[Partie]:
    parties: list[Partie] = []
    bloc: list[Question] | None = None
    for texte, gras in _paragraphes(contenu):
        if m := _PARTIE.match(texte):
            parties.append(Partie(int(m[1]), _propre(m[2])))
            bloc = None
        elif not parties:
            continue  # titre et consignes du document
        elif texte.startswith(_MOYEN):
            bloc = parties[-1].moyennes
        elif texte.startswith(_DIFFICILE):
            bloc = parties[-1].difficiles
        elif bloc is None:
            raise Incoherence(f"Paragraphe avant le premier bloc de « {parties[-1].titre} » : « {texte[:80]} ».")
        elif m := _QUESTION.match(texte):
            bloc.append(Question(int(m[1]), _propre(m[2])))
        elif (m := _CHOIX.match(texte)) and bloc:
            question = bloc[-1]
            if gras:
                question.en_gras.append(len(question.choix))
            question.choix.append(_propre(m[2]))
        else:
            raise Incoherence(f"Paragraphe non reconnu dans « {parties[-1].titre} » : « {texte[:80]} ».")

    attendu = 1
    for partie in parties:
        if not partie.moyennes or not partie.difficiles:
            raise Incoherence(f"La partie « {partie.titre} » n'a pas ses deux blocs de questions.")
        if partie.numero not in AXES:
            raise Incoherence(f"Partie {partie.numero} inconnue : aucun axe prévu.")
        for q in partie.moyennes + partie.difficiles:
            if q.n != attendu:
                raise Incoherence(f"Question {q.n} : numéro inattendu, la question {attendu} était attendue.")
            if len(q.choix) != NB_CHOIX:
                raise Incoherence(f"Question {q.n} : {len(q.choix)} propositions, il en faut {NB_CHOIX}.")
            if len(q.en_gras) != 1:
                raise Incoherence(f"Question {q.n} : il faut une seule proposition en gras ({len(q.en_gras)}).")
            attendu += 1
    return parties


def _q(q: Question) -> dict:
    return {"n": q.n, "enonce": q.enonce, "choix": q.choix, "bonne": q.bonne}


def _par_dix(questions: list[Question], partie: int) -> list[tuple[int, list[Question]]]:
    if len(questions) % PAR_QUIZ:
        raise Incoherence(f"Partie {partie} : {len(questions)} questions, pas un multiple de {PAR_QUIZ}.")
    return [(partie, questions[i : i + PAR_QUIZ]) for i in range(0, len(questions), PAR_QUIZ)]


def _alterner(groupes: list[list[tuple[int, list[Question]]]]) -> list[tuple[int, list[Question]]]:
    """Les quiz de chaque partie, répartis régulièrement : chacun à sa position relative dans sa partie."""
    positions = [
        ((i + 0.5) / len(g), partie_rang, quiz) for partie_rang, g in enumerate(groupes) for i, quiz in enumerate(g)
    ]
    return [quiz for _, _, quiz in sorted(positions, key=lambda p: (p[0], p[1]))]


def _niveaux(quiz: list, repartition: tuple[tuple[str, int], ...]) -> list[str]:
    niveaux = [niveau for niveau, nombre in repartition for _ in range(nombre)]
    if len(niveaux) != len(quiz):
        raise Incoherence(f"{len(quiz)} quiz pour {len(niveaux)} niveaux prévus.")
    return niveaux


def composer(parties: list[Partie]) -> dict:
    titres = {p.numero: p.titre for p in parties}
    certif_par_partie: dict[int, list[Question]] = {}
    melange_par_partie: dict[int, list[Question]] = {}
    jeux_m: list[list[tuple[int, list[Question]]]] = []
    jeux_d: list[list[tuple[int, list[Question]]]] = []

    for p in parties:
        n = len(p.difficiles)
        if n < RESERVE_CERTIFICATION:
            raise Incoherence(f"Partie {p.numero} : {n} questions très difficiles, il en faut {RESERVE_CERTIFICATION}.")
        indices = [k * n // RESERVE_CERTIFICATION for k in range(RESERVE_CERTIFICATION)]
        reservees = [p.difficiles[i] for i in indices]
        pas = RESERVE_CERTIFICATION // POUR_LE_MELANGE
        melange_par_partie[p.numero] = [q for k, q in enumerate(reservees) if k % pas == pas - 1]
        certif_par_partie[p.numero] = [q for k, q in enumerate(reservees) if k % pas != pas - 1]
        pris = set(indices)
        jeux_m.append(_par_dix(p.moyennes, p.numero))
        jeux_d.append(_par_dix([q for i, q in enumerate(p.difficiles) if i not in pris], p.numero))

    # Les quiz Jeux, numérotés dans l'ordre du parcours.
    ordre_m, ordre_d = _alterner(jeux_m), _alterner(jeux_d)
    niveaux = _niveaux(ordre_m, NIVEAUX_M) + _niveaux(ordre_d, NIVEAUX_D)
    compteurs: dict[int, int] = {}
    jeux = []
    for numero, ((partie, questions), niveau) in enumerate(zip(ordre_m + ordre_d, niveaux, strict=True), start=1):
        compteurs[partie] = compteurs.get(partie, 0) + 1
        difficulte = "très difficiles" if (partie, questions) in ordre_d else "moyennement difficiles"
        jeux.append(
            {
                "numero": numero,
                "niveau": niveau,
                "titre": f"{titres[partie]} — quiz {compteurs[partie]}",
                "description": f"{DESCRIPTION} · partie {partie} : {titres[partie]} · questions {difficulte}.",
                "axe": AXES[partie],
                "questions": [_q(q) for q in questions],
            }
        )

    # Les 20 places : 4 par partie (ses 40 questions, tour à tour), puis 4 places de mélange.
    certification = []
    for rang_theme, p in enumerate(parties):
        for k in range(PLACES_PAR_THEMATIQUE):
            questions = certif_par_partie[p.numero][k::PLACES_PAR_THEMATIQUE]
            certification.append((rang_theme, k, AXES[p.numero], f"partie {p.numero} : {p.titre}", questions))
    melange = [q for groupe in zip(*melange_par_partie.values(), strict=True) for q in groupe]
    for k in range(PLACES_PAR_THEMATIQUE):
        questions = melange[k * PAR_QUIZ : (k + 1) * PAR_QUIZ]
        certification.append((len(parties), k, AXE_MELANGE, "les 4 parties", questions))

    places = []
    for place, (rang_theme, k, axe, origine, questions) in enumerate(certification, start=1):
        if len(questions) != PAR_QUIZ:
            raise Incoherence(f"Place {place} : {len(questions)} questions au lieu de {PAR_QUIZ}.")
        places.append(
            {
                "place": place,
                "titre": f"Génie Imhotep {place} — {NOMS_PAR_DEFAUT[rang_theme]} ({k + 1}/{PLACES_PAR_THEMATIQUE})",
                "description": f"{DESCRIPTION} · niveau expert · questions très difficiles, {origine}.",
                "axe": axe,
                "questions": [_q(q) for q in questions],
            }
        )
    return {"jeux": jeux, "certification": places}


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("document", type=Path)
    parseur.add_argument("sortie", type=Path)
    arguments = parseur.parse_args()
    donnees = composer(lire(arguments.document.read_bytes()))
    arguments.sortie.write_text(json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(
        f"{len(donnees['jeux'])} quiz Jeux et {len(donnees['certification'])} quiz de certification → {arguments.sortie}"
    )


if __name__ == "__main__":
    main()
