"""points et eleves : registre des points, semestres, barème et profil des élèves (spec 017)

Revision ID: 995338790b20
Revises: d6cbed387764
Create Date: 2026-11-04 05:36:20.519460

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "995338790b20"
down_revision: str | Sequence[str] | None = "d6cbed387764"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Copie figée de la grille du PRD (`app/points/bareme.py` peut évoluer sans changer ce qu'a fait cette migration) :
# code, bénéficiaire, libellé, montant, montant encore proposé.
BAREME = [
    ("eleve.bienvenue", "eleve", "Compte créé", 100, False),
    ("eleve.commentaire", "eleve", "Commentaire approuvé", 5, False),
    ("eleve.republication", "eleve", "Republication d'un article du site, vérifiée", 10, False),
    ("eleve.article", "eleve", "Article personnel approuvé", 50, False),
    ("eleve.partage", "eleve", "Partage de son article, par réseau, vérifié", 50, False),
    ("eleve.quiz", "eleve", "Quiz réussi, première fois", 25, False),
    ("eleve.certification", "eleve", "Certification Génie Imhotep", 1000, False),
    ("encadreur.bienvenue", "encadreur", "Compte validé", 100, True),
    ("encadreur.commentaire", "encadreur", "Commentaire approuvé", 5, True),
    ("encadreur.republication", "encadreur", "Republication d'un article du site, vérifiée", 10, True),
    ("encadreur.article", "encadreur", "Article personnel approuvé", 50, True),
    ("encadreur.partage", "encadreur", "Partage de son article, par réseau, vérifié", 50, True),
    ("encadreur.quiz", "encadreur", "Quiz réussi, première fois", 25, True),
    ("encadreur.certification", "encadreur", "Certification Génie Imhotep", 1000, True),
    ("encadreur.sujet_forum", "encadreur", "Sujet de forum validé", 30, True),
    ("encadreur.discussion", "encadreur", "Discussion animée et attestée", 50, True),
    ("encadreur.reponse_utile", "encadreur", "Réponse utile validée à un élève", 10, True),
    ("encadreur.evenement", "encadreur", "Événement approuvé dans l'agenda", 30, True),
    ("encadreur.rapport_activite", "encadreur", "Rapport d'activité validé", 100, True),
    ("encadreur.rapport_mensuel", "encadreur", "Rapport mensuel validé", 75, True),
    ("encadreur.bilan_semestriel", "encadreur", "Bilan semestriel validé", 200, True),
    ("encadreur.projet_eleves", "encadreur", "Projet d'élèves accompagné et réalisé", 150, True),
    ("encadreur.certification_eleve", "encadreur", "Élève accompagné jusqu'à la certification", 50, True),
    ("encadreur.mobilisation", "encadreur", "Mobilisation vérifiée de 10 participants", 50, True),
    ("club.article_eleve", "club", "Article approuvé d'un élève affilié", 20, False),
    ("club.quiz_eleve", "club", "Quiz réussi par un élève affilié", 10, False),
    ("club.certification_eleve", "club", "Certification d'un élève affilié", 100, False),
    ("club.rapport_activite", "club", "Rapport d'activité validé", 50, True),
    ("club.bilan_semestriel", "club", "Bilan semestriel validé", 100, True),
]
EN_SERVICE = {"eleve.bienvenue"}


def _suivi() -> list[sa.Column]:
    return [
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modifie_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "semestre",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("libelle", sa.String(length=60), nullable=False),
        sa.Column("debut", sa.Date(), nullable=False),
        sa.Column("fin", sa.Date(), nullable=False),
        *_suivi(),
        sa.CheckConstraint("fin >= debut", name=op.f("ck_semestre_dates_ordonnees")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_semestre")),
        sa.UniqueConstraint("libelle", name=op.f("uq_semestre_libelle")),
    )
    op.execute(
        "ALTER TABLE semestre ADD CONSTRAINT ex_semestre_sans_chevauchement "
        "EXCLUDE USING gist (daterange(debut, fin, '[]') WITH &&)"
    )

    bareme = op.create_table(
        "bareme",
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column(
            "beneficiaire",
            sa.Enum("eleve", "encadreur", "club", name="beneficiaire", native_enum=False, create_constraint=True,
                    length=20),
            nullable=False,
        ),
        sa.Column("libelle", sa.String(length=120), nullable=False),
        sa.Column("montant", sa.Integer(), nullable=False),
        sa.Column("propose", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("en_service", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("actif", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False),
        *_suivi(),
        sa.CheckConstraint("montant BETWEEN 0 AND 10000", name=op.f("ck_bareme_montant_borne")),
        sa.CheckConstraint("code ~ '^[a-z]+\\.[a-z_]+$'", name=op.f("ck_bareme_code_format")),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_bareme")),
    )  # fmt: skip
    op.bulk_insert(
        bareme,
        [
            {"code": code, "beneficiaire": pour, "libelle": libelle, "montant": montant, "propose": propose,
             "en_service": code in EN_SERVICE, "ordre": ordre}
            for ordre, (code, pour, libelle, montant, propose) in enumerate(BAREME, start=1)
        ],
    )  # fmt: skip

    op.create_table(
        "mouvement_points",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("montant", sa.Integer(), nullable=False),
        sa.Column("semestre_id", sa.Uuid(), nullable=True),
        sa.Column("cle", sa.String(length=200), nullable=False),
        sa.Column("valide_par", sa.Uuid(), nullable=True),
        sa.Column("annule_id", sa.Uuid(), nullable=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(annule_id IS NULL AND montant > 0) OR (annule_id IS NOT NULL AND montant < 0)",
            name=op.f("ck_mouvement_points_montant_signe"),
        ),
        sa.ForeignKeyConstraint(["action"], ["bareme.code"], name=op.f("fk_mouvement_points_action_bareme"),
                                ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["annule_id"], ["mouvement_points.id"],
                                name=op.f("fk_mouvement_points_annule_id_mouvement_points"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["semestre_id"], ["semestre.id"], name=op.f("fk_mouvement_points_semestre_id_semestre"),
                                ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"],
                                name=op.f("fk_mouvement_points_utilisateur_id_utilisateur"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["valide_par"], ["utilisateur.id"],
                                name=op.f("fk_mouvement_points_valide_par_utilisateur"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mouvement_points")),
        sa.UniqueConstraint("annule_id", name=op.f("uq_mouvement_points_annule_id")),
        sa.UniqueConstraint("cle", name=op.f("uq_mouvement_points_cle")),
    )  # fmt: skip
    op.create_index(
        "ix_mouvement_points_utilisateur_id_semestre_id", "mouvement_points", ["utilisateur_id", "semestre_id"]
    )

    op.create_table(
        "eleve",
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("pseudonyme", sa.String(length=30), nullable=False),
        sa.Column("pseudonyme_normalise", sa.String(length=30), nullable=False),
        sa.Column(
            "classe",
            sa.Enum("6e", "5e", "4e", "3e", "2nde", "1re", "tle", name="classe", native_enum=False,
                    create_constraint=True, length=10),
            nullable=False,
        ),
        sa.Column("etablissement_id", sa.Uuid(), nullable=False),
        sa.Column("charte_version", sa.String(length=20), nullable=False),
        *_suivi(),
        sa.ForeignKeyConstraint(["etablissement_id"], ["etablissement.id"],
                                name=op.f("fk_eleve_etablissement_id_etablissement"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"], name=op.f("fk_eleve_utilisateur_id_utilisateur"),
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("utilisateur_id", name=op.f("pk_eleve")),
        sa.UniqueConstraint("pseudonyme_normalise", name=op.f("uq_eleve_pseudonyme_normalise")),
    )  # fmt: skip
    op.create_index(op.f("ix_eleve_etablissement_id"), "eleve", ["etablissement_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_eleve_etablissement_id"), table_name="eleve")
    op.drop_table("eleve")
    op.drop_index("ix_mouvement_points_utilisateur_id_semestre_id", table_name="mouvement_points")
    op.drop_table("mouvement_points")
    op.drop_table("bareme")
    op.drop_table("semestre")
