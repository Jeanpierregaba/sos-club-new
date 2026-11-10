"""Schémas du joueur (spec 027). Aucun ne porte la bonne réponse, l'explication ni le détail des réponses : la
banque a ses propres schémas (`schemas_banque.py`), sans champ commun pour les réponses."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuestionJoueur(BaseModel):
    rang: int
    enonce: str
    # Les textes des choix, dans l'ordre mélangé propre à cette tentative.
    choix: list[str]
    # Temps affiché pour répondre ; le serveur accorde en plus une tolérance réseau qu'il ne dit pas.
    temps_ms: int
    restant_ms: int


class CorrectionReponse(BaseModel):
    """La correction de la question à laquelle le joueur vient de répondre (quiz des jeux, 2026-11-10). Elle n'arrive
    qu'après sa réponse : la question en cours ne porte jamais la sienne (ADR-0004)."""

    rang: int
    juste: bool
    # Index, dans l'ordre affiché, du choix du joueur ; None s'il n'a pas répondu à temps.
    choix_joueur: int | None
    choix_attendu: int


class ErreurPartie(BaseModel):
    """Une question ratée, dans le récapitulatif de fin de partie des quiz des jeux."""

    rang: int
    enonce: str
    # Le texte du choix du joueur ; None s'il n'a pas répondu à temps.
    ta_reponse: str | None
    reponse_attendue: str
    explication: str | None


class ResultatPartie(BaseModel):
    score: int
    total: int
    seuil: int
    reussie: bool
    # Points gagnés par cette tentative : 0 si le quiz était déjà réussi, pour un encadreur, ou en mode test.
    points: int
    # Les questions ratées et leurs bonnes réponses (quiz des jeux) ; None pour la certification, qui n'en montre pas.
    erreurs: list[ErreurPartie] | None = None


class EtatPartie(BaseModel):
    tentative_id: UUID
    quiz_id: UUID
    titre: str
    total: int
    # La question en cours, ou None une fois la partie terminée.
    question: QuestionJoueur | None
    resultat: ResultatPartie | None
    # Après une réponse à un quiz des jeux : la correction de cette réponse. None sinon.
    correction: CorrectionReponse | None = None


class ReponseJoueur(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rang: Annotated[int, Field(ge=1)]
    # Index dans l'ordre affiché ; le serveur refuse un index hors des choix de la question (422).
    choix: Annotated[int, Field(ge=0)]


class QuizJoueur(BaseModel):
    id: UUID
    titre: str
    description: str
    axe_code: str
    contenu_de_test: bool
    publie_le: datetime | None
    reussi: bool
    meilleur_score: int | None
    tentatives_restantes: int
    # La partie en cours du joueur sur ce quiz, à reprendre (la liste clôt d'abord les parties abandonnées).
    tentative_en_cours: UUID | None = None


class ListeQuiz(BaseModel):
    nb_questions: int
    seuil: int
    quiz: list[QuizJoueur]
