"""chrono de 15 secondes (spec 048)

Une nouvelle version des paramètres de chaque parcours qui en a déjà une : copie de la version en cours, avec 15 s
par question. Les autres réglages faits dans l'admin sont gardés, et une partie commencée garde sa version (spec 027).
Un parcours sans version prendra les valeurs par défaut du code, déjà à 15 s. Sans effet si la version en cours est
déjà à 15 s.

Revision ID: 9aa1a0ded79b
Revises: a1b2c3d4e5f6
Create Date: 2026-11-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9aa1a0ded79b"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEMPS_MS = 15000


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO parametres_quiz
                (id, parcours, version, nb_questions, temps_ms, tolerance_ms, seuil, tentatives_par_jour,
                 arret_premiere_erreur, cree_par, cree_le)
            SELECT uuidv7(), p.parcours, p.version + 1, p.nb_questions, :temps, p.tolerance_ms, p.seuil,
                   p.tentatives_par_jour, p.arret_premiere_erreur, NULL, now()
            FROM parametres_quiz p
            WHERE p.version = (SELECT max(v.version) FROM parametres_quiz v WHERE v.parcours = p.parcours)
              AND p.temps_ms <> :temps
            """
        ).bindparams(temps=TEMPS_MS)
    )


def downgrade() -> None:
    # Les versions ne se suppriment pas : une partie peut y renvoyer. Revenir à 20 s passe par l'admin.
    pass
