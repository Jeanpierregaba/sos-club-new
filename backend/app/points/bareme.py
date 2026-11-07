"""Grille initiale du barème (PRD, « Barème des points »). Les montants se règlent ensuite dans l'espace admin.

Chaque spec qui écrit une action la met en service par sa migration : l'admin voit ainsi quelles lignes
rapportent déjà des points. Le code ne change jamais, il sert de clé aux lignes du registre.
"""

from typing import Literal, NamedTuple

from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert

from app.points.models import LigneBareme

Beneficiaire = Literal["eleve", "encadreur", "club"]


class Action(NamedTuple):
    code: str
    beneficiaire: Beneficiaire
    libelle: str
    montant: int
    # Montant encore à valider par les organisateurs (Q22).
    propose: bool = False


BIENVENUE_ELEVE = "eleve.bienvenue"
BIENVENUE_ENCADREUR = "encadreur.bienvenue"
QUESTION_JOUR_ELEVE = "eleve.question_jour"
# Article approuvé (spec 023), à la première approbation seulement.
ARTICLE_ELEVE = "eleve.article"
ARTICLE_ENCADREUR = "encadreur.article"
QUESTION_JOUR_CLUB = "club.question_jour_eleve"

# Référentiel « Harmonisation de la gamification » du 2026-11-05 (spec 022). La part du club n'est créditée que
# pour un élève dont l'affiliation est active au moment du crédit.
GRILLE: tuple[Action, ...] = (
    Action(BIENVENUE_ELEVE, "eleve", "Compte créé", 100),
    Action("eleve.commentaire", "eleve", "Commentaire approuvé", 5),
    Action("eleve.republication", "eleve", "Republication d'un article du site, vérifiée", 10),
    Action(ARTICLE_ELEVE, "eleve", "Article personnel approuvé", 50),
    Action("eleve.partage", "eleve", "Partage de son article, par réseau, vérifié", 50),
    Action("eleve.quiz", "eleve", "Quiz santé réussi, première fois", 50),
    Action(QUESTION_JOUR_ELEVE, "eleve", "Bonne réponse à la question du jour", 20),
    Action("eleve.badge", "eleve", "Badge de certification obtenu (5 au plus)", 500),
    Action("eleve.certification", "eleve", "Certification Génie Imhotep", 1000),
    Action("encadreur.bienvenue", "encadreur", "Compte validé", 100, propose=True),
    Action("encadreur.commentaire", "encadreur", "Commentaire approuvé", 5, propose=True),
    Action("encadreur.republication", "encadreur", "Republication d'un article du site, vérifiée", 10, propose=True),
    Action(ARTICLE_ENCADREUR, "encadreur", "Article personnel approuvé", 50, propose=True),
    Action("encadreur.partage", "encadreur", "Partage de son article, par réseau, vérifié", 50, propose=True),
    Action("encadreur.quiz", "encadreur", "Quiz réussi, première fois", 0, propose=True),
    Action("encadreur.certification", "encadreur", "Certification Génie Imhotep", 1000, propose=True),
    Action("encadreur.sujet_forum", "encadreur", "Sujet de forum validé", 30, propose=True),
    Action("encadreur.discussion", "encadreur", "Discussion animée et attestée", 50, propose=True),
    Action("encadreur.reponse_utile", "encadreur", "Réponse utile validée à un élève", 10, propose=True),
    Action("encadreur.evenement", "encadreur", "Événement approuvé dans l'agenda", 30, propose=True),
    Action("encadreur.rapport_activite", "encadreur", "Rapport d'activité validé", 100, propose=True),
    Action("encadreur.rapport_mensuel", "encadreur", "Rapport mensuel validé", 75, propose=True),
    Action("encadreur.bilan_semestriel", "encadreur", "Bilan semestriel validé", 200, propose=True),
    Action("encadreur.projet_eleves", "encadreur", "Projet d'élèves accompagné et réalisé", 150, propose=True),
    Action("encadreur.certification_eleve", "encadreur", "Élève accompagné jusqu'à la certification", 50, propose=True),
    Action("encadreur.mobilisation", "encadreur", "Mobilisation vérifiée de 10 participants", 50, propose=True),
    Action("club.bienvenue_eleve", "club", "Compte validé d'un élève affilié", 50),
    Action("club.commentaire_eleve", "club", "Commentaire approuvé d'un élève affilié", 20),
    Action("club.republication_eleve", "club", "Republication vérifiée par un élève affilié", 2),
    Action("club.article_eleve", "club", "Article approuvé d'un élève affilié", 20),
    Action("club.partage_eleve", "club", "Partage vérifié de son article par un élève affilié, par réseau", 2),
    Action("club.quiz_eleve", "club", "Quiz santé réussi par un élève affilié", 25),
    Action(QUESTION_JOUR_CLUB, "club", "Question du jour réussie par un élève affilié", 10),
    Action("club.badge_eleve", "club", "Badge obtenu par un élève affilié (5 au plus)", 200),
    Action("club.certification_eleve", "club", "Certification d'un élève affilié", 500),
    Action("club.rapport_activite", "club", "Rapport d'activité validé", 50, propose=True),
    Action("club.bilan_semestriel", "club", "Bilan semestriel validé", 100, propose=True),
)


# Actions déjà écrites par une spec livrée. Chaque nouvelle spec ajoute la sienne ici et dans sa migration.
EN_SERVICE: frozenset[str] = frozenset(
    {BIENVENUE_ELEVE, BIENVENUE_ENCADREUR, QUESTION_JOUR_ELEVE, ARTICLE_ELEVE, ARTICLE_ENCADREUR}
)


def lignes_initiales() -> list[dict[str, object]]:
    return [
        action._asdict() | {"ordre": ordre, "en_service": action.code in EN_SERVICE}
        for ordre, action in enumerate(GRILLE, start=1)
    ]


def charger(connexion: Connection) -> None:
    """Remplit le barème sans toucher aux lignes déjà présentes. Sert aux tests et au seed ; la migration a sa
    propre copie figée."""
    table = LigneBareme.__table__
    connexion.execute(insert(table).values(lignes_initiales()).on_conflict_do_nothing(index_elements=["code"]))
