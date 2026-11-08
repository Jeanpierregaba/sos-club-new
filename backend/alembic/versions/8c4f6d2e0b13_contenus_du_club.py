"""Contenus du club (spec 026) : actualités et propositions de fiche, rattachées au club.

Non destructive : une colonne nulle, des contraintes élargies et deux index. Le retour en arrière échoue s'il
existe des contenus du club : il faut d'abord les supprimer.

Revision ID: 8c4f6d2e0b13
Revises: 7b3e5c1d9a42
Create Date: 2026-11-08 05:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c4f6d2e0b13"
down_revision: str | Sequence[str] | None = "7b3e5c1d9a42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ADRESSE = "version_publiee_id IS NULL OR adresse IS NOT NULL OR parent_id IS NOT NULL"


def _adresse(condition: str) -> None:
    op.drop_constraint(op.f("ck_contenu_adresse_si_publie"), "contenu", type_="check")
    op.create_check_constraint(op.f("ck_contenu_adresse_si_publie"), "contenu", condition)


def upgrade() -> None:
    op.add_column("contenu", sa.Column("club_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_contenu_club_id_club", "contenu", "club", ["club_id"], ["id"], ondelete="RESTRICT")
    _adresse(f"{ADRESSE} OR type = 'fiche_club'")
    op.create_check_constraint(
        op.f("ck_contenu_contenu_du_club"), "contenu", "(type IN ('actualite', 'fiche_club')) = (club_id IS NOT NULL)"
    )
    op.create_index("ix_contenu_club_id_type", "contenu", ["club_id", "type"])
    op.create_index(
        "uq_contenu_fiche_en_attente",
        "contenu",
        ["club_id"],
        unique=True,
        postgresql_where=sa.text("type = 'fiche_club' AND etat = 'en_attente'"),
    )


def downgrade() -> None:
    op.drop_index("uq_contenu_fiche_en_attente", table_name="contenu")
    op.drop_index("ix_contenu_club_id_type", table_name="contenu")
    op.drop_constraint(op.f("ck_contenu_contenu_du_club"), "contenu", type_="check")
    _adresse(ADRESSE)
    op.drop_constraint("fk_contenu_club_id_club", "contenu", type_="foreignkey")
    op.drop_column("contenu", "club_id")
