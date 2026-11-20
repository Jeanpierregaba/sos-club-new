"""Index des réussites par quiz

Revision ID: e4a7c2d9b6f1
Revises: d8e3b1f5a2c6
Create Date: 2026-11-20

Spec 046 : la moyenne nationale d'un quiz lit les premières réussites de chaque joueur. Sans cet index, la fiche d'un
inscrit parcourait toute la table des tentatives. Index partiel, sans destruction.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e4a7c2d9b6f1"
down_revision: str | None = "d8e3b1f5a2c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tentative_quiz_reussites ON tentative_quiz (quiz_id, joueur_id, terminee_le) "
        "WHERE etat = 'terminee' AND reussie AND NOT essai"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tentative_quiz_reussites")
