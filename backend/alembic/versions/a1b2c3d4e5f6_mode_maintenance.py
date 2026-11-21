"""mode maintenance du site

Spec 047 : une ligne singleton mémorise si la plateforme est en maintenance, pour que l'état survive aux
redémarrages.

Revision ID: a1b2c3d4e5f6
Revises: e4a7c2d9b6f1
Create Date: 2026-11-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "e4a7c2d9b6f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "etat_site",
        sa.Column("id", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("maintenance_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("active_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active_par_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("id = 1", name=op.f("ck_etat_site_ligne_unique")),
        sa.ForeignKeyConstraint(
            ["active_par_id"],
            ["utilisateur.id"],
            name=op.f("fk_etat_site_active_par_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_etat_site")),
    )
    op.execute(sa.text("INSERT INTO etat_site (id, maintenance_active) VALUES (1, false)"))


def downgrade() -> None:
    op.drop_table("etat_site")
