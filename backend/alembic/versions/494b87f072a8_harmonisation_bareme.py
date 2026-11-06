"""harmonisation du bareme (spec 022)

Aligne le barème sur le référentiel « Harmonisation de la gamification » du 2026-11-05. Un montant déjà réglé
dans l'espace admin n'est pas écrasé : une ligne n'est mise à jour que si elle a encore l'ancienne valeur par
défaut. Copie figée des valeurs : la grille de `app.points.bareme` peut évoluer après cette migration.

Revision ID: 494b87f072a8
Revises: 8f4444de8fad
Create Date: 2026-11-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "494b87f072a8"
down_revision: str | Sequence[str] | None = "8f4444de8fad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (code, ancien montant, nouveau montant, nouveau libellé)
CHANGEMENTS = [
    ("eleve.quiz", 25, 50, "Quiz santé réussi, première fois"),
    ("encadreur.quiz", 25, 0, "Quiz réussi, première fois"),
    ("club.quiz_eleve", 10, 25, "Quiz santé réussi par un élève affilié"),
    ("club.certification_eleve", 100, 500, "Certification d'un élève affilié"),
    ("club.rapport_activite", 50, 500, "Rapport d'activité validé"),
]

# (code, bénéficiaire, libellé, montant, proposé)
AJOUTS = [
    ("eleve.question_jour", "eleve", "Bonne réponse à la question du jour", 20, False),
    ("eleve.badge", "eleve", "Badge de certification obtenu (5 au plus)", 500, False),
    ("club.bienvenue_eleve", "club", "Compte validé d'un élève affilié", 50, False),
    ("club.commentaire_eleve", "club", "Commentaire approuvé d'un élève affilié", 20, False),
    ("club.republication_eleve", "club", "Republication vérifiée par un élève affilié", 2, False),
    ("club.partage_eleve", "club", "Partage vérifié de son article par un élève affilié, par réseau", 2, False),
    ("club.question_jour_eleve", "club", "Question du jour réussie par un élève affilié", 10, False),
    ("club.badge_eleve", "club", "Badge obtenu par un élève affilié (5 au plus)", 200, False),
]

# L'ordre d'affichage du référentiel : chaque action nouvelle à côté des actions voisines.
ORDRE = [
    "eleve.bienvenue",
    "eleve.commentaire",
    "eleve.republication",
    "eleve.article",
    "eleve.partage",
    "eleve.quiz",
    "eleve.question_jour",
    "eleve.badge",
    "eleve.certification",
    "encadreur.bienvenue",
    "encadreur.commentaire",
    "encadreur.republication",
    "encadreur.article",
    "encadreur.partage",
    "encadreur.quiz",
    "encadreur.certification",
    "encadreur.sujet_forum",
    "encadreur.discussion",
    "encadreur.reponse_utile",
    "encadreur.evenement",
    "encadreur.rapport_activite",
    "encadreur.rapport_mensuel",
    "encadreur.bilan_semestriel",
    "encadreur.projet_eleves",
    "encadreur.certification_eleve",
    "encadreur.mobilisation",
    "club.bienvenue_eleve",
    "club.commentaire_eleve",
    "club.republication_eleve",
    "club.article_eleve",
    "club.partage_eleve",
    "club.quiz_eleve",
    "club.question_jour_eleve",
    "club.badge_eleve",
    "club.certification_eleve",
    "club.rapport_activite",
    "club.bilan_semestriel",
]
ANCIEN_ORDRE = [code for code in ORDRE if code not in {a[0] for a in AJOUTS}]


def _ordonner(codes: list[str]) -> None:
    for ordre, code in enumerate(codes, start=1):
        op.execute(sa.text("UPDATE bareme SET ordre = :ordre WHERE code = :code").bindparams(ordre=ordre, code=code))


def upgrade() -> None:
    for code, ancien, nouveau, libelle in CHANGEMENTS:
        op.execute(
            sa.text(
                "UPDATE bareme SET montant = :nouveau, libelle = :libelle, version = version + 1 "
                "WHERE code = :code AND montant = :ancien"
            ).bindparams(code=code, ancien=ancien, nouveau=nouveau, libelle=libelle)
        )
    for code, beneficiaire, libelle, montant, propose in AJOUTS:
        op.execute(
            sa.text(
                "INSERT INTO bareme (code, beneficiaire, libelle, montant, propose, en_service, actif, ordre) "
                "VALUES (:code, :beneficiaire, :libelle, :montant, :propose, false, true, 0) "
                "ON CONFLICT (code) DO NOTHING"
            ).bindparams(code=code, beneficiaire=beneficiaire, libelle=libelle, montant=montant, propose=propose)
        )
    _ordonner(ORDRE)


def downgrade() -> None:
    # Les crédits déjà écrits pour les actions ajoutées empêchent leur suppression (clé étrangère) : c'est voulu.
    op.execute(
        sa.text("DELETE FROM bareme WHERE code IN :codes").bindparams(
            sa.bindparam("codes", value=[a[0] for a in AJOUTS], expanding=True)
        )
    )
    for code, ancien, nouveau, _ in CHANGEMENTS:
        op.execute(
            sa.text(
                "UPDATE bareme SET montant = :ancien, version = version + 1 WHERE code = :code AND montant = :nouveau"
            ).bindparams(code=code, ancien=ancien, nouveau=nouveau)
        )
    _ordonner(ANCIEN_ORDRE)
