"""Tables des clubs et des passations (spec 019).

Un club est une entité collective rattachée à un établissement : il n'a jamais de compte. Son président,
un élève, le gère avec son compte. Aucune ligne de points n'est écrite ici : le score du club viendra
avec les specs qui en créditent (quiz, publications, rapports).

Revision ID: c1a2b3d4e5f6
Revises: bbb78f046dd0
Create Date: 2026-11-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: str | Sequence[str] | None = "bbb78f046dd0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "club",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("etablissement_id", sa.Uuid(), nullable=False),
        sa.Column("nom", sa.String(length=150), nullable=False),
        sa.Column("nom_normalise", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("demandeur_id", sa.Uuid(), nullable=False),
        sa.Column("president_id", sa.Uuid(), nullable=True),
        sa.Column("encadreurs_associes", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column(
            "etat",
            sa.Enum(
                "en_attente",
                "actif",
                "refuse",
                name="etat_club",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default=sa.text("'en_attente'"),
            nullable=False,
        ),
        sa.Column("motif_refus", sa.String(length=500), nullable=True),
        sa.Column("decide_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decide_par", sa.Uuid(), nullable=True),
        sa.Column("demande_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actif_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modifie_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("etablissement_id", "nom_normalise"),
        sa.CheckConstraint("(etat = 'refuse') = (motif_refus IS NOT NULL)", name=op.f("ck_club_motif_si_refuse")),
        sa.ForeignKeyConstraint(
            ["etablissement_id"],
            ["etablissement.id"],
            ondelete="RESTRICT",
            name=op.f("fk_club_etablissement_id_etablissement"),
        ),
        sa.ForeignKeyConstraint(
            ["demandeur_id"], ["utilisateur.id"], ondelete="RESTRICT", name=op.f("fk_club_demandeur_id_utilisateur")
        ),
        sa.ForeignKeyConstraint(
            ["president_id"], ["utilisateur.id"], ondelete="RESTRICT", name=op.f("fk_club_president_id_utilisateur")
        ),
        sa.ForeignKeyConstraint(
            ["decide_par"], ["utilisateur.id"], ondelete="SET NULL", name=op.f("fk_club_decide_par_utilisateur")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_club")),
    )
    op.create_index(op.f("ix_club_etablissement_id"), "club", ["etablissement_id"], unique=False)
    op.create_index(
        "uq_club_actif_par_etablissement",
        "club",
        ["etablissement_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'actif'"),
    )

    op.create_table(
        "club_axe",
        sa.Column("club_id", sa.Uuid(), nullable=False),
        sa.Column("axe_code", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["club.id"], ondelete="CASCADE", name=op.f("fk_club_axe_club_id_club")),
        sa.ForeignKeyConstraint(["axe_code"], ["axe.code"], ondelete="RESTRICT", name=op.f("fk_club_axe_axe_code_axe")),
        sa.PrimaryKeyConstraint("club_id", "axe_code", name=op.f("pk_club_axe")),
    )

    op.create_table(
        "club_passation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("club_id", sa.Uuid(), nullable=False),
        sa.Column("successeur_id", sa.Uuid(), nullable=False),
        sa.Column("propose_par", sa.Uuid(), nullable=False),
        sa.Column("propose_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "etat",
            sa.Enum(
                "en_attente",
                "validee",
                "refusee",
                name="etat_passation",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            server_default=sa.text("'en_attente'"),
            nullable=False,
        ),
        sa.Column("motif_refus", sa.String(length=500), nullable=True),
        sa.Column("decide_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decide_par", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modifie_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(etat = 'refusee') = (motif_refus IS NOT NULL)", name=op.f("ck_club_passation_motif_si_refusee")
        ),
        sa.ForeignKeyConstraint(
            ["club_id"], ["club.id"], ondelete="CASCADE", name=op.f("fk_club_passation_club_id_club")
        ),
        sa.ForeignKeyConstraint(
            ["successeur_id"],
            ["utilisateur.id"],
            ondelete="RESTRICT",
            name=op.f("fk_club_passation_successeur_id_utilisateur"),
        ),
        sa.ForeignKeyConstraint(
            ["propose_par"],
            ["utilisateur.id"],
            ondelete="RESTRICT",
            name=op.f("fk_club_passation_propose_par_utilisateur"),
        ),
        sa.ForeignKeyConstraint(
            ["decide_par"],
            ["utilisateur.id"],
            ondelete="SET NULL",
            name=op.f("fk_club_passation_decide_par_utilisateur"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_club_passation")),
    )
    op.create_index(op.f("ix_club_passation_club_id"), "club_passation", ["club_id"], unique=False)
    op.create_index(
        "uq_club_passation_en_attente",
        "club_passation",
        ["club_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'en_attente'"),
    )


def downgrade() -> None:
    op.drop_index("uq_club_passation_en_attente", table_name="club_passation")
    op.drop_index(op.f("ix_club_passation_club_id"), table_name="club_passation")
    op.drop_table("club_passation")
    op.drop_table("club_axe")
    op.drop_index("uq_club_actif_par_etablissement", table_name="club")
    op.drop_index(op.f("ix_club_etablissement_id"), table_name="club")
    op.drop_table("club")
