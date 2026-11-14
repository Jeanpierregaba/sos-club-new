"""Grille initiale du barème (PRD, « Barème des points »). Les montants se règlent ensuite dans l'espace admin.

Chaque spec qui écrit une action la met en service par sa migration : l'admin voit ainsi quelles lignes
rapportent déjà des points. Le code ne change jamais, il sert de clé aux lignes du registre.
"""

from typing import Literal, NamedTuple

from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert

from app.points.models import LigneBareme, Parcours, SousCompte

Beneficiaire = Literal["eleve", "encadreur", "club", "admin"]


class Action(NamedTuple):
    code: str
    beneficiaire: Beneficiaire
    libelle: str
    montant: int
    # Montant encore à valider par les organisateurs (Q22).
    propose: bool = False
    # Parcours de l'élève (spec 034) ; les Jeux ont deux sous-comptes : quiz et étoiles.
    parcours: Parcours | None = None
    sous_compte: SousCompte | None = None
    actif: bool = True


BIENVENUE_ELEVE = "eleve.bienvenue"
BIENVENUE_ENCADREUR = "encadreur.bienvenue"
QUESTION_JOUR_ELEVE = "eleve.question_jour"
# Article approuvé (spec 023), à la première approbation seulement.
ARTICLE_ELEVE = "eleve.article"
ARTICLE_ENCADREUR = "encadreur.article"
COMMENTAIRE_ELEVE = "eleve.commentaire"
COMMENTAIRE_ENCADREUR = "encadreur.commentaire"
# Quiz santé réussi (spec 027), au montant unique d'avant la spec 034 : remplacé par le gain du niveau du quiz.
QUIZ_ELEVE = "eleve.quiz"
# Spec 034 : un quiz Jeux rapporte selon son niveau, et chaque niveau validé débloque son étoile.
QUIZ_NIVEAU: dict[str, str] = {
    niveau: f"eleve.quiz_{niveau}" for niveau in ("debutant", "intermediaire", "avance", "expert")
}
ETOILE_NIVEAU: dict[str, str] = {
    niveau: f"eleve.etoile_{niveau}" for niveau in ("debutant", "intermediaire", "avance", "expert")
}
# Certification Génie Imhotep (spec 029, puis 034 : +50 par quiz validé).
QUIZ_CERTIFICATION_ELEVE = "eleve.quiz_certification"
BADGE_ELEVE = "eleve.badge"
CERTIFICATION_ELEVE = "eleve.certification"
CERTIFICATION_ENCADREUR = "encadreur.certification"
# Ligne technique de la correction manuelle (spec 036) : jamais un gain automatique, masquée du barème.
ACTION_CORRECTION = "admin.correction"

C, J, V = Parcours.certification, Parcours.jeux, Parcours.vie
Q, E = SousCompte.quiz, SousCompte.etoiles

# Barème de la spec 034 (cahier des charges du 2026-11-10) pour l'élève ; le club reçoit la moitié de chaque gain
# d'un élève affilié (ADR-0012), sans ligne à lui. Les actions d'encadreur restent celles de la spec 022.
GRILLE: tuple[Action, ...] = (
    Action(BIENVENUE_ELEVE, "eleve", "Compte créé", 100, parcours=V),
    Action(COMMENTAIRE_ELEVE, "eleve", "Commentaire approuvé", 5, parcours=V),
    Action("eleve.republication", "eleve", "Republication d'un article du site, vérifiée", 10, parcours=V),
    Action(ARTICLE_ELEVE, "eleve", "Article personnel approuvé", 50, parcours=V),
    Action("eleve.partage", "eleve", "Partage de son article, par réseau, vérifié", 50, parcours=V),
    Action(QUESTION_JOUR_ELEVE, "eleve", "Bonne réponse à la question du jour", 20, parcours=V),
    Action(QUIZ_ELEVE, "eleve", "Quiz santé réussi, première fois (avant les niveaux)", 50, parcours=J, sous_compte=Q),
    Action(QUIZ_NIVEAU["debutant"], "eleve", "Quiz Débutant réussi, première fois", 50, parcours=J, sous_compte=Q),
    Action(
        QUIZ_NIVEAU["intermediaire"], "eleve", "Quiz Intermédiaire réussi, première fois", 100, parcours=J,
        sous_compte=Q,
    ),
    Action(QUIZ_NIVEAU["avance"], "eleve", "Quiz Avancé réussi, première fois", 150, parcours=J, sous_compte=Q),
    Action(QUIZ_NIVEAU["expert"], "eleve", "Quiz Expert réussi, première fois", 200, parcours=J, sous_compte=Q),
    Action(ETOILE_NIVEAU["debutant"], "eleve", "Étoile 1 : niveau Débutant validé", 500, parcours=J, sous_compte=E),
    Action(
        ETOILE_NIVEAU["intermediaire"], "eleve", "Étoile 2 : niveau Intermédiaire validé", 1000, parcours=J,
        sous_compte=E,
    ),
    Action(ETOILE_NIVEAU["avance"], "eleve", "Étoile 3 : niveau Avancé validé", 1500, parcours=J, sous_compte=E),
    Action(ETOILE_NIVEAU["expert"], "eleve", "Étoile 4 : niveau Expert validé", 3000, parcours=J, sous_compte=E),
    Action(QUIZ_CERTIFICATION_ELEVE, "eleve", "Quiz de certification validé (10/10)", 50, parcours=C),
    Action(BADGE_ELEVE, "eleve", "Badge de certification obtenu (5 au plus)", 500, parcours=C),
    Action(CERTIFICATION_ELEVE, "eleve", "Certification Génie Imhotep", 1000, parcours=C),
    Action("encadreur.bienvenue", "encadreur", "Compte validé", 100, propose=True),
    Action("encadreur.commentaire", "encadreur", "Commentaire approuvé", 5, propose=True),
    Action("encadreur.republication", "encadreur", "Republication d'un article du site, vérifiée", 10, propose=True),
    Action(ARTICLE_ENCADREUR, "encadreur", "Article personnel approuvé", 50, propose=True),
    Action("encadreur.partage", "encadreur", "Partage de son article, par réseau, vérifié", 50, propose=True),
    Action("encadreur.quiz", "encadreur", "Quiz réussi, première fois", 0, propose=True),
    Action(CERTIFICATION_ENCADREUR, "encadreur", "Certification Génie Imhotep", 1000, propose=True),
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
    # Parts fixes du club de la spec 022, remplacées par la règle des 50 % (spec 034) : gardées, désactivées.
    Action("club.bienvenue_eleve", "club", "Compte validé d'un élève affilié", 50, actif=False),
    Action("club.commentaire_eleve", "club", "Commentaire approuvé d'un élève affilié", 20, actif=False),
    Action("club.republication_eleve", "club", "Republication vérifiée par un élève affilié", 2, actif=False),
    Action("club.article_eleve", "club", "Article approuvé d'un élève affilié", 20, actif=False),
    Action(
        "club.partage_eleve", "club", "Partage vérifié de son article par un élève affilié, par réseau", 2,
        actif=False,
    ),
    Action("club.quiz_eleve", "club", "Quiz santé réussi par un élève affilié", 25, actif=False),
    Action("club.question_jour_eleve", "club", "Question du jour réussie par un élève affilié", 10, actif=False),
    Action("club.badge_eleve", "club", "Badge obtenu par un élève affilié (5 au plus)", 200, actif=False),
    Action("club.certification_eleve", "club", "Certification d'un élève affilié", 500, actif=False),
    # Le compte collectif du club : un référentiel distinct, hors de la règle des 50 % (spec 034).
    Action("club.rapport_activite", "club", "Rapport d'activité validé", 50, propose=True),
    Action("club.bilan_semestriel", "club", "Bilan semestriel validé", 100, propose=True),
    # Spec 036 : une correction manuelle, toujours motivée et écrite par l'admin, jamais un gain automatique.
    Action(ACTION_CORRECTION, "admin", "Correction manuelle du score", 0, actif=False),
)  # fmt: skip


# Actions déjà écrites par une spec livrée. Chaque nouvelle spec ajoute la sienne ici et dans sa migration.
EN_SERVICE: frozenset[str] = frozenset(
    {
        BIENVENUE_ELEVE,
        BIENVENUE_ENCADREUR,
        QUESTION_JOUR_ELEVE,
        ARTICLE_ELEVE,
        ARTICLE_ENCADREUR,
        COMMENTAIRE_ELEVE,
        COMMENTAIRE_ENCADREUR,
        # Spec 034 : les quiz Jeux par niveau et les étoiles (lot 2), le quiz de certification (lot 3).
        *QUIZ_NIVEAU.values(),
        *ETOILE_NIVEAU.values(),
        QUIZ_CERTIFICATION_ELEVE,
        BADGE_ELEVE,
        CERTIFICATION_ELEVE,
        CERTIFICATION_ENCADREUR,
        # Spec 036 : la correction manuelle, utilisée par le registre admin.
        ACTION_CORRECTION,
    }
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
