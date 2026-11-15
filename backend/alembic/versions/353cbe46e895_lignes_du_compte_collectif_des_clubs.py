"""Lignes du compte collectif des clubs (spec 038, note de l'ADR-0012).

Une ligne du registre peut créditer un club sans personne : `utilisateur_id` devient nullable, réservé aux actions
`club.*` comptées au double en demi-points. Non destructive. La descente est refusée s'il existe déjà une ligne de
club, plutôt que de l'effacer.

Revision ID: 353cbe46e895
Revises: a488bad88446
Create Date: 2026-11-15 02:05:04.369165
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "353cbe46e895"
down_revision: str | Sequence[str] | None = "a488bad88446"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MOITIE = "demi_points_club IS NULL OR demi_points_club = montant"
LIGNE_DE_CLUB = (
    "utilisateur_id IS NOT NULL OR (club_id IS NOT NULL AND action LIKE 'club.%' AND demi_points_club = 2 * montant)"
)


def upgrade() -> None:
    op.alter_column("mouvement_points", "utilisateur_id", existing_type=sa.UUID(), nullable=True)
    op.drop_constraint(op.f("ck_mouvement_points_part_du_club_moitie"), "mouvement_points", type_="check")
    op.create_check_constraint(
        op.f("ck_mouvement_points_part_du_club_moitie"), "mouvement_points", f"{MOITIE} OR utilisateur_id IS NULL"
    )
    op.create_check_constraint(op.f("ck_mouvement_points_ligne_de_club"), "mouvement_points", LIGNE_DE_CLUB)


def downgrade() -> None:
    connexion = op.get_bind()
    if connexion.scalar(sa.text("SELECT count(*) FROM mouvement_points WHERE utilisateur_id IS NULL")):
        raise RuntimeError("Des lignes du compte collectif des clubs existent : la migration ne les efface pas.")
    op.drop_constraint(op.f("ck_mouvement_points_ligne_de_club"), "mouvement_points", type_="check")
    op.drop_constraint(op.f("ck_mouvement_points_part_du_club_moitie"), "mouvement_points", type_="check")
    op.create_check_constraint(op.f("ck_mouvement_points_part_du_club_moitie"), "mouvement_points", MOITIE)
    op.alter_column("mouvement_points", "utilisateur_id", existing_type=sa.UUID(), nullable=False)
