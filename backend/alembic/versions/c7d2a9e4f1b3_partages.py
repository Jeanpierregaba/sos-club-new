"""partages

Spec 044 (R17) : une déclaration de partage est un contenu du moteur de modération, rattaché à son article comme un
commentaire. Un index sur le lien des versions sert au contrôle des liens déjà déclarés.

Revision ID: c7d2a9e4f1b3
Revises: 4dc45a4fff16
Create Date: 2026-11-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7d2a9e4f1b3"
down_revision: str | Sequence[str] | None = "4dc45a4fff16"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Rejouable : certains tests marquent une révision antérieure puis remontent à la tête.
def upgrade() -> None:
    op.execute("ALTER TABLE contenu DROP CONSTRAINT IF EXISTS ck_contenu_commentaire_a_un_parent")
    op.execute("ALTER TABLE contenu DROP CONSTRAINT IF EXISTS ck_contenu_contenu_a_un_parent")
    op.execute(
        "ALTER TABLE contenu ADD CONSTRAINT ck_contenu_contenu_a_un_parent "
        "CHECK ((type IN ('commentaire', 'partage')) = (parent_id IS NOT NULL))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_version_contenu_lien_partage ON version_contenu ((donnees ->> 'cle_lien')) "
        "WHERE donnees ? 'cle_lien' AND etat <> 'travail'"
    )


def downgrade() -> None:
    # On ne supprime rien : un retour arrière avec des partages enregistrés est refusé.
    if op.get_bind().execute(sa.text("SELECT 1 FROM contenu WHERE type = 'partage' LIMIT 1")).first() is not None:
        raise RuntimeError("Des partages sont enregistrés : le retour arrière les rendrait invalides.")
    op.execute("DROP INDEX IF EXISTS ix_version_contenu_lien_partage")
    op.execute("ALTER TABLE contenu DROP CONSTRAINT IF EXISTS ck_contenu_contenu_a_un_parent")
    op.execute("ALTER TABLE contenu DROP CONSTRAINT IF EXISTS ck_contenu_commentaire_a_un_parent")
    op.execute(
        "ALTER TABLE contenu ADD CONSTRAINT ck_contenu_commentaire_a_un_parent "
        "CHECK ((type = 'commentaire') = (parent_id IS NOT NULL))"
    )
