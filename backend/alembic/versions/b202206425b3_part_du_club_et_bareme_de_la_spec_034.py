"""part du club et bareme de la spec 034

Lot 1 de la spec 034 (ADR-0012) : la part du club, la moitié de chaque gain d'un élève affilié, s'écrit dans la
ligne du gain (`club_id`, `demi_points_club`). Le barème porte le parcours et le sous-compte de chaque action ; les
nouvelles actions (quiz par niveau, étoiles, quiz de certification) sont ajoutées hors service, chaque lot les met
en service. Les lignes `club.*_eleve`, jamais créditées, sont désactivées. Rien n'est recalculé.

Copie figée des valeurs : la grille de `app.points.bareme` peut évoluer après cette migration.

Revision ID: b202206425b3
Revises: 4b93d2491b34
Create Date: 2026-11-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b202206425b3"
down_revision: str | Sequence[str] | None = "4b93d2491b34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (code, libellé, montant, parcours, sous-compte)
AJOUTS = [
    ("eleve.quiz_debutant", "Quiz Débutant réussi, première fois", 50, "jeux", "quiz"),
    ("eleve.quiz_intermediaire", "Quiz Intermédiaire réussi, première fois", 100, "jeux", "quiz"),
    ("eleve.quiz_avance", "Quiz Avancé réussi, première fois", 150, "jeux", "quiz"),
    ("eleve.quiz_expert", "Quiz Expert réussi, première fois", 200, "jeux", "quiz"),
    ("eleve.etoile_debutant", "Étoile 1 : niveau Débutant validé", 500, "jeux", "etoiles"),
    ("eleve.etoile_intermediaire", "Étoile 2 : niveau Intermédiaire validé", 1000, "jeux", "etoiles"),
    ("eleve.etoile_avance", "Étoile 3 : niveau Avancé validé", 1500, "jeux", "etoiles"),
    ("eleve.etoile_expert", "Étoile 4 : niveau Expert validé", 3000, "jeux", "etoiles"),
    ("eleve.quiz_certification", "Quiz de certification validé (10/10)", 50, "certification", None),
]

# Parcours des actions d'élève existantes.
PARCOURS = {
    "eleve.bienvenue": ("vie", None),
    "eleve.commentaire": ("vie", None),
    "eleve.republication": ("vie", None),
    "eleve.article": ("vie", None),
    "eleve.partage": ("vie", None),
    "eleve.question_jour": ("vie", None),
    "eleve.quiz": ("jeux", "quiz"),
    "eleve.badge": ("certification", None),
    "eleve.certification": ("certification", None),
}

# (code, libellé, montant) des lignes de la spec 022 que la règle des 50 % remplace.
RETIREES = [
    ("club.bienvenue_eleve", "Compte validé d'un élève affilié", 50),
    ("club.commentaire_eleve", "Commentaire approuvé d'un élève affilié", 20),
    ("club.republication_eleve", "Republication vérifiée par un élève affilié", 2),
    ("club.article_eleve", "Article approuvé d'un élève affilié", 20),
    ("club.partage_eleve", "Partage vérifié de son article par un élève affilié, par réseau", 2),
    ("club.quiz_eleve", "Quiz santé réussi par un élève affilié", 25),
    ("club.question_jour_eleve", "Question du jour réussie par un élève affilié", 10),
    ("club.badge_eleve", "Badge obtenu par un élève affilié (5 au plus)", 200),
    ("club.certification_eleve", "Certification d'un élève affilié", 500),
]

ORDRE = [
    "eleve.bienvenue",
    "eleve.commentaire",
    "eleve.republication",
    "eleve.article",
    "eleve.partage",
    "eleve.question_jour",
    "eleve.quiz",
    "eleve.quiz_debutant",
    "eleve.quiz_intermediaire",
    "eleve.quiz_avance",
    "eleve.quiz_expert",
    "eleve.etoile_debutant",
    "eleve.etoile_intermediaire",
    "eleve.etoile_avance",
    "eleve.etoile_expert",
    "eleve.quiz_certification",
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


def upgrade() -> None:
    op.add_column("bareme", sa.Column("parcours", sa.String(length=20), nullable=True))
    op.add_column("bareme", sa.Column("sous_compte", sa.String(length=10), nullable=True))
    op.create_check_constraint(
        op.f("ck_bareme_parcours_points"), "bareme", "parcours IN ('certification', 'jeux', 'vie')"
    )
    op.create_check_constraint(op.f("ck_bareme_sous_compte_points"), "bareme", "sous_compte IN ('quiz', 'etoiles')")
    op.create_check_constraint(
        op.f("ck_bareme_sous_compte_des_jeux"), "bareme", "sous_compte IS NULL OR parcours = 'jeux'"
    )

    op.add_column("mouvement_points", sa.Column("club_id", sa.Uuid(), nullable=True))
    op.add_column("mouvement_points", sa.Column("demi_points_club", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_mouvement_points_club_id_club"), "mouvement_points", "club", ["club_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_check_constraint(
        op.f("ck_mouvement_points_club_et_part"), "mouvement_points", "(club_id IS NULL) = (demi_points_club IS NULL)"
    )
    op.create_check_constraint(
        op.f("ck_mouvement_points_part_du_club_moitie"),
        "mouvement_points",
        "demi_points_club IS NULL OR demi_points_club = montant",
    )
    op.create_index(
        "ix_mouvement_points_club_id",
        "mouvement_points",
        ["club_id"],
        postgresql_where=sa.text("club_id IS NOT NULL"),
    )

    for code, (parcours, sous_compte) in PARCOURS.items():
        op.execute(
            sa.text("UPDATE bareme SET parcours = :parcours, sous_compte = :sous_compte WHERE code = :code").bindparams(
                code=code, parcours=parcours, sous_compte=sous_compte
            )
        )
    for code, libelle, montant, parcours, sous_compte in AJOUTS:
        op.execute(
            sa.text(
                "INSERT INTO bareme (code, beneficiaire, libelle, montant, propose, en_service, actif, ordre, "
                "parcours, sous_compte) "
                "VALUES (:code, 'eleve', :libelle, :montant, false, false, true, 0, :parcours, :sous_compte) "
                "ON CONFLICT (code) DO NOTHING"
            ).bindparams(code=code, libelle=libelle, montant=montant, parcours=parcours, sous_compte=sous_compte)
        )
    op.execute(
        sa.text(
            "UPDATE bareme SET libelle = 'Quiz santé réussi, première fois (avant les niveaux)' WHERE code = 'eleve.quiz'"
        )
    )
    # Jamais créditées (R13 devait les brancher) : la règle des 50 % les remplace. Désactivées, pas supprimées
    # (docs/RULES.md : aucune migration destructive sans confirmation).
    op.execute(
        sa.text(
            "UPDATE bareme SET actif = false, en_service = false, version = version + 1 WHERE code IN :codes"
        ).bindparams(sa.bindparam("codes", value=[r[0] for r in RETIREES], expanding=True))
    )
    for ordre, code in enumerate(ORDRE, start=1):
        op.execute(sa.text("UPDATE bareme SET ordre = :ordre WHERE code = :code").bindparams(ordre=ordre, code=code))


def downgrade() -> None:
    op.drop_index("ix_mouvement_points_club_id", table_name="mouvement_points")
    op.drop_constraint(op.f("ck_mouvement_points_part_du_club_moitie"), "mouvement_points", type_="check")
    op.drop_constraint(op.f("ck_mouvement_points_club_et_part"), "mouvement_points", type_="check")
    op.drop_constraint(op.f("fk_mouvement_points_club_id_club"), "mouvement_points", type_="foreignkey")
    op.drop_column("mouvement_points", "demi_points_club")
    op.drop_column("mouvement_points", "club_id")
    # Les crédits déjà écrits pour les actions ajoutées empêchent leur suppression (clé étrangère) : c'est voulu.
    op.execute(
        sa.text("DELETE FROM bareme WHERE code IN :codes").bindparams(
            sa.bindparam("codes", value=[a[0] for a in AJOUTS], expanding=True)
        )
    )
    op.drop_constraint(op.f("ck_bareme_sous_compte_des_jeux"), "bareme", type_="check")
    op.drop_constraint(op.f("ck_bareme_sous_compte_points"), "bareme", type_="check")
    op.drop_constraint(op.f("ck_bareme_parcours_points"), "bareme", type_="check")
    op.drop_column("bareme", "sous_compte")
    op.drop_column("bareme", "parcours")
    # Les lignes de club désactivées redeviennent actives ; l'ancien libellé du quiz revient.
    op.execute(
        sa.text("UPDATE bareme SET actif = true WHERE code IN :codes").bindparams(
            sa.bindparam("codes", value=[r[0] for r in RETIREES], expanding=True)
        )
    )
    op.execute(sa.text("UPDATE bareme SET libelle = 'Quiz santé réussi, première fois' WHERE code = 'eleve.quiz'"))
