"""encadreurs : profil et vérification des encadreurs, bienvenue encadreur en service (spec 018)

Revision ID: bbb78f046dd0
Revises: 995338790b20
Create Date: 2026-11-04 15:01:04.722430

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "bbb78f046dd0"
down_revision: str | Sequence[str] | None = "995338790b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "encadreur",
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("etablissement_id", sa.Uuid(), nullable=False),
        sa.Column(
            "fonction",
            sa.Enum(
                "enseignant",
                "responsable",
                "sante",
                "accompagnateur",
                "autre",
                name="fonction",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("fonction_precision", sa.String(length=100), nullable=True),
        sa.Column(
            "etat",
            sa.Enum(
                "en_attente",
                "actif",
                "refuse",
                name="etat_verification",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("demande_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("decide_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decide_par", sa.Uuid(), nullable=True),
        sa.Column("motif_refus", sa.String(length=500), nullable=True),
        sa.Column("charte_version", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modifie_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("(etat = 'refuse') = (motif_refus IS NOT NULL)", name=op.f("ck_encadreur_motif_si_refuse")),
        sa.CheckConstraint(
            "(fonction = 'autre') = (fonction_precision IS NOT NULL)", name=op.f("ck_encadreur_precision_si_autre")
        ),
        sa.ForeignKeyConstraint(
            ["decide_par"], ["utilisateur.id"], name=op.f("fk_encadreur_decide_par_utilisateur"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["etablissement_id"],
            ["etablissement.id"],
            name=op.f("fk_encadreur_etablissement_id_etablissement"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_encadreur_utilisateur_id_utilisateur"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("utilisateur_id", name=op.f("pk_encadreur")),
    )
    op.create_index(op.f("ix_encadreur_etablissement_id"), "encadreur", ["etablissement_id"], unique=False)
    op.create_index(
        "ix_encadreur_file", "encadreur", ["demande_le"], unique=False, postgresql_where=sa.text("etat = 'en_attente'")
    )
    # L'activation d'un encadreur écrit désormais sa ligne de bienvenue.
    op.execute("UPDATE bareme SET en_service = true WHERE code = 'encadreur.bienvenue'")


def downgrade() -> None:
    op.execute("UPDATE bareme SET en_service = false WHERE code = 'encadreur.bienvenue'")
    op.drop_index("ix_encadreur_file", table_name="encadreur", postgresql_where=sa.text("etat = 'en_attente'"))
    op.drop_index(op.f("ix_encadreur_etablissement_id"), table_name="encadreur")
    op.drop_table("encadreur")
