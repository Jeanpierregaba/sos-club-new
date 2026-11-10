"""Chrono des quiz « jeux » à 20 secondes par question (demande du 2026-11-10).

Les paramètres sont versionnés et jamais modifiés : on ajoute une version qui reprend la dernière avec
20 000 ms. Les parties déjà commencées gardent leur version. La certification n'est pas touchée.

Revision ID: 15ac5cbf557f
Revises: 7b2a41396d51
Create Date: 2026-11-10 14:52:50.700206

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15ac5cbf557f"
down_revision: str | Sequence[str] | None = "7b2a41396d51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEMPS_MS = 20000

# Rien à faire si le parcours n'a encore aucun paramètre : la version 1 sera créée avec la valeur par défaut.
AJOUTER = f"""
INSERT INTO parametres_quiz (id, parcours, version, nb_questions, temps_ms, tolerance_ms, seuil, tentatives_par_jour)
SELECT gen_random_uuid(), parcours, version + 1, nb_questions, {TEMPS_MS}, tolerance_ms, seuil, tentatives_par_jour
FROM parametres_quiz
WHERE parcours = 'jeux' AND temps_ms <> {TEMPS_MS}
  AND version = (SELECT max(version) FROM parametres_quiz WHERE parcours = 'jeux')
"""

# Retire la version ajoutée, sauf si une partie l'utilise déjà (elle doit garder ses paramètres) : dans ce cas la
# descente est volontairement incomplète et le chrono reste à 20 s. Une version 1 créée par défaut n'est pas touchée.
RETIRER = f"""
DELETE FROM parametres_quiz p
WHERE p.parcours = 'jeux' AND p.temps_ms = {TEMPS_MS} AND p.cree_par IS NULL
  AND p.version = (SELECT max(version) FROM parametres_quiz WHERE parcours = 'jeux')
  AND p.version > 1
  AND NOT EXISTS (SELECT 1 FROM tentative_quiz t WHERE t.parametres_id = p.id)
"""


def upgrade() -> None:
    op.execute(AJOUTER)


def downgrade() -> None:
    op.execute(RETIRER)
