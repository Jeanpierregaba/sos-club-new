"""« Quel axe est fait pour toi ? » (spec 021) : le jeu de découverte des 7 axes, réservé aux élèves.

Questions et table de correspondance du document fonctionnel « Jeu de découverte des 7 axes ». Chaque réponse
donne +3 à son axe principal et +1 à son axe secondaire. Rien n'est enregistré, aucun point n'est gagné : le
résultat oriente, il ne classe pas l'élève.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Literal

CodeAxe = Literal["GI", "EVSS", "TV", "SS", "GB", "LM", "SE"]
Lettre = Literal["A", "B", "C", "D"]

# Dernier départage, déterministe.
ORDRE_AXES: tuple[CodeAxe, ...] = ("GI", "EVSS", "TV", "SS", "GB", "LM", "SE")
POINTS_PRINCIPAL = 3
POINTS_SECONDAIRE = 1


@dataclass(frozen=True)
class Reponse:
    lettre: Lettre
    libelle: str
    principal: CodeAxe
    secondaire: CodeAxe


@dataclass(frozen=True)
class Question:
    libelle: str
    reponses: tuple[Reponse, ...]


QUESTIONS: tuple[Question, ...] = (
    Question(
        "Dans ton établissement, quelle activité te ferait le plus plaisir ?",
        (
            Reponse("A", "Réaliser une vidéo ou interviewer des élèves.", "TV", "LM"),
            Reponse("B", "Organiser une activité sportive ou une initiation aux premiers secours.", "SS", "SE"),
            Reponse("C", "Mobiliser les élèves autour d'un projet.", "LM", "EVSS"),
            Reponse("D", "Participer à un grand concours de culture générale.", "GI", "GB"),
        ),
    ),
    Question(
        "Tu disposes d'une heure pour participer à une activité. Que choisis-tu ?",
        (
            Reponse(
                "A", "Imaginer une campagne pour sensibiliser les jeunes à faire des choix responsables.", "EVSS", "TV"
            ),
            Reponse("B", "Écouter et soutenir un camarade qui traverse une période difficile.", "SE", "EVSS"),
            Reponse("C", "Participer à un jeu-concours pour tenter de remporter un prix.", "GB", "GI"),
            Reponse("D", "Apprendre les gestes qui peuvent sauver une vie.", "SS", "LM"),
        ),
    ),
    Question(
        "Ton Club Santé prépare une grande journée d'activités. Quel rôle aimerais-tu jouer ?",
        (
            Reponse("A", "Filmer les activités et réaliser un reportage.", "TV", "GB"),
            Reponse("B", "Coordonner l'équipe et répartir les responsabilités.", "LM", "SS"),
            Reponse("C", "Préparer les questions d'un quiz de culture générale en santé.", "GI", "GB"),
            Reponse("D", "Animer une discussion sur le respect, les valeurs et la santé sexuelle.", "EVSS", "SE"),
        ),
    ),
    Question(
        "Qu'est-ce qui te rendrait le plus fier ou la plus fière ?",
        (
            Reponse("A", "Avoir appris quelque chose de nouveau et réussi à résoudre un problème.", "GI", "SE"),
            Reponse("B", "Avoir aidé quelqu'un à se sentir mieux.", "SE", "EVSS"),
            Reponse("C", "Avoir remporté un défi après beaucoup d'efforts.", "GB", "SS"),
            Reponse("D", "Avoir convaincu des jeunes d'adopter un comportement responsable.", "EVSS", "TV"),
        ),
    ),
    Question(
        "Si tu pouvais lancer une activité dans ton lycée demain, laquelle choisirais-tu ?",
        (
            Reponse("A", "Une journée sportive avec des démonstrations de premiers secours.", "SS", "SE"),
            Reponse("B", "Une émission vidéo où les élèves partagent leurs idées et leurs talents.", "TV", "LM"),
            Reponse("C", "Un projet collectif où chacun peut prendre des initiatives.", "LM", "EVSS"),
            Reponse("D", "Un grand challenge interclasses avec des jeux, des défis et des récompenses.", "GB", "GI"),
        ),
    ),
)


@dataclass(frozen=True)
class Resultat:
    principal: CodeAxe
    autres: tuple[CodeAxe, CodeAxe]
    scores: dict[CodeAxe, int]


def calculer(lettres: list[Lettre]) -> Resultat:
    """Le classement des axes pour ces 5 réponses, identique pour tous à réponses identiques.

    Départage : total décroissant, puis nombre de fois en axe principal, puis l'axe principal de la question 1
    s'il est parmi les ex æquo, puis l'ordre GI, EVSS, TV, SS, GB, LM, SE."""
    if len(lettres) != len(QUESTIONS):
        raise ValueError("Il faut une réponse à chaque question.")
    choisies = [
        next(r for r in question.reponses if r.lettre == lettre)
        for question, lettre in zip(QUESTIONS, lettres, strict=True)
    ]
    scores: Counter[CodeAxe] = Counter()
    principaux: Counter[CodeAxe] = Counter()
    for reponse in choisies:
        scores[reponse.principal] += POINTS_PRINCIPAL
        scores[reponse.secondaire] += POINTS_SECONDAIRE
        principaux[reponse.principal] += 1
    premier = choisies[0].principal

    def cle(axe: CodeAxe) -> tuple[int, int, int, int]:
        # La règle 3 ne joue qu'entre ex æquo : à total et nombre de « principal » égaux, l'axe principal de la
        # question 1 passe devant ; sinon, elle ne change rien.
        return (-scores[axe], -principaux[axe], 0 if axe == premier else 1, ORDRE_AXES.index(axe))

    classement = sorted(ORDRE_AXES, key=cle)
    return Resultat(
        principal=classement[0],
        autres=(classement[1], classement[2]),
        scores={axe: scores[axe] for axe in ORDRE_AXES},
    )
