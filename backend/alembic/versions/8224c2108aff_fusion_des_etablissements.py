"""Fusion des établissements (spec 042) : le renvoi d'un établissement absorbé vers celui qui le garde, et les paires
que l'équipe a jugées distinctes.

Non destructive : une colonne nullable, une table vide, et l'unicité du nom dans l'IESG réservée aux établissements
non fusionnés. Le retour arrière est refusé dès qu'une fusion a eu lieu,
car le renvoi serait perdu.

Revision ID: 8224c2108aff
Revises: 52c30f73350d
Create Date: 2026-11-18 09:55:38.354812

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8224c2108aff"
down_revision: str | Sequence[str] | None = "52c30f73350d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ecart_doublon",
        sa.Column("etablissement_a_id", sa.Uuid(), nullable=False),
        sa.Column("etablissement_b_id", sa.Uuid(), nullable=False),
        sa.Column("ecarte_par", sa.Uuid(), nullable=True),
        sa.Column("ecarte_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("etablissement_a_id < etablissement_b_id", name=op.f("ck_ecart_doublon_paire_ordonnee")),
        sa.ForeignKeyConstraint(
            ["ecarte_par"],
            ["utilisateur.id"],
            name=op.f("fk_ecart_doublon_ecarte_par_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["etablissement_a_id"],
            ["etablissement.id"],
            name=op.f("fk_ecart_doublon_etablissement_a_id_etablissement"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["etablissement_b_id"],
            ["etablissement.id"],
            name=op.f("fk_ecart_doublon_etablissement_b_id_etablissement"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("etablissement_a_id", "etablissement_b_id", name=op.f("pk_ecart_doublon")),
    )
    op.create_index(op.f("ix_ecart_doublon_etablissement_b_id"), "ecart_doublon", ["etablissement_b_id"], unique=False)
    op.add_column("etablissement", sa.Column("fusionne_dans_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_etablissement_fusionne_dans_id"), "etablissement", ["fusionne_dans_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_etablissement_fusionne_dans_id_etablissement"),
        "etablissement",
        "etablissement",
        ["fusionne_dans_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        op.f("ck_etablissement_fusionne_si_inactif"), "etablissement", "fusionne_dans_id IS NULL OR statut = 'inactif'"
    )
    op.create_check_constraint(op.f("ck_etablissement_fusionne_ailleurs"), "etablissement", "fusionne_dans_id <> id")
    # Un établissement fusionné ne réserve plus son nom : le gardé peut le reprendre.
    op.drop_constraint("uq_etablissement_iesg_id_nom_normalise", "etablissement", type_="unique")
    op.create_index(
        "uq_etablissement_iesg_id_nom_normalise",
        "etablissement",
        ["iesg_id", "nom_normalise"],
        unique=True,
        postgresql_where=sa.text("fusionne_dans_id IS NULL"),
    )


def downgrade() -> None:

    fusions = op.get_bind().scalar(sa.text("SELECT count(*) FROM etablissement WHERE fusionne_dans_id IS NOT NULL"))
    if fusions:
        raise RuntimeError(f"Retour impossible : {fusions} établissement(s) fusionné(s) perdraient leur renvoi.")
    op.drop_index("uq_etablissement_iesg_id_nom_normalise", table_name="etablissement")
    op.create_unique_constraint("uq_etablissement_iesg_id_nom_normalise", "etablissement", ["iesg_id", "nom_normalise"])
    op.drop_constraint(op.f("ck_etablissement_fusionne_ailleurs"), "etablissement", type_="check")
    op.drop_constraint(op.f("ck_etablissement_fusionne_si_inactif"), "etablissement", type_="check")
    op.drop_constraint(op.f("fk_etablissement_fusionne_dans_id_etablissement"), "etablissement", type_="foreignkey")
    op.drop_index(op.f("ix_etablissement_fusionne_dans_id"), table_name="etablissement")
    op.drop_column("etablissement", "fusionne_dans_id")
    op.drop_index(op.f("ix_ecart_doublon_etablissement_b_id"), table_name="ecart_doublon")
    op.drop_table("ecart_doublon")
