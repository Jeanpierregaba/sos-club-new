"""Commune de l'encadreur

Revision ID: d8e3b1f5a2c6
Revises: c7d2a9e4f1b3
Create Date: 2026-11-20

Obligatoire à l'inscription depuis le 2026-11-20 ; la colonne reste nullable pour les comptes plus anciens.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d8e3b1f5a2c6"
down_revision: str | None = "c7d2a9e4f1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE encadreur ADD COLUMN IF NOT EXISTS commune VARCHAR(100)")


def downgrade() -> None:
    op.execute("ALTER TABLE encadreur DROP COLUMN IF EXISTS commune")
