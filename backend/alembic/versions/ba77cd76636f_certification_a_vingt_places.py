"""certification a vingt places

Lot 3 de la spec 034 : la certification Génie Imhotep passe à 20 places (5 thématiques de 4), 10 questions de
20 secondes, réussite à 10/10 avec arrêt à la première erreur et sans plafond de tentatives. Les badges tombent à
4, 8, 12, 16 et 20 places, sous leurs 5 noms officiels. Un quiz de certification validé rapporte +50.

Une nouvelle version des paramètres et des règles est ajoutée : les anciennes restent (un badge garde sa version).

Revision ID: ba77cd76636f
Revises: 0b5d089c2f2d
Create Date: 2026-11-11

"""

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ba77cd76636f"
down_revision: str | Sequence[str] | None = "0b5d089c2f2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOMS = [
    "Ambassadeur Santé Junior",
    "Pair Éducateur Santé et Citoyenneté",
    "Sentinelle de la Prévention",
    "Champion de la Santé et EVSS",
    "Maître Génie Imhotep",
]
PALIERS = [4, 8, 12, 16, 20]


def _remplacer(table: str, nom: str, condition: str) -> None:
    op.drop_constraint(op.f(f"ck_{table}_{nom}"), table, type_="check")
    op.create_check_constraint(op.f(f"ck_{table}_{nom}"), table, condition)


def upgrade() -> None:
    _remplacer("quiz", "place_valide", "place BETWEEN 1 AND 20")
    _remplacer("place_reussie", "place_valide", "place BETWEEN 1 AND 20")
    op.drop_constraint(op.f("ck_regles_badges_dernier_palier_12"), "regles_badges", type_="check")
    op.create_check_constraint(op.f("ck_regles_badges_dernier_palier"), "regles_badges", "paliers[5] IN (12, 20)")

    op.add_column(
        "parametres_quiz",
        sa.Column("arret_premiere_erreur", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.alter_column("parametres_quiz", "tentatives_par_jour", existing_type=sa.Integer(), nullable=True)
    _remplacer("parametres_quiz", "tentatives_valide", "tentatives_par_jour IS NULL OR tentatives_par_jour >= 1")

    connexion = op.get_bind()
    connexion.execute(
        sa.text(
            "INSERT INTO parametres_quiz (id, parcours, version, nb_questions, temps_ms, tolerance_ms, seuil, "
            "tentatives_par_jour, arret_premiere_erreur) "
            "SELECT gen_random_uuid(), 'certification', coalesce(max(version), 0) + 1, 10, 20000, "
            "coalesce((SELECT tolerance_ms FROM parametres_quiz WHERE parcours = 'certification' "
            "ORDER BY version DESC LIMIT 1), 2000), 10, NULL, true "
            "FROM parametres_quiz WHERE parcours = 'certification'"
        )
    )
    connexion.execute(
        sa.text(
            "INSERT INTO regles_badges (id, version, noms, paliers) "
            "SELECT gen_random_uuid(), coalesce(max(version), 0) + 1, CAST(:noms AS jsonb), :paliers FROM regles_badges"
        ).bindparams(noms=json.dumps(NOMS, ensure_ascii=False), paliers=PALIERS)
    )
    connexion.execute(sa.text("UPDATE bareme SET en_service = true WHERE code = 'eleve.quiz_certification'"))


def downgrade() -> None:
    connexion = op.get_bind()
    au_dela = connexion.execute(
        sa.text(
            "SELECT (SELECT count(*) FROM place_reussie WHERE place > 12) + (SELECT count(*) FROM quiz WHERE place > 12)"
            " + (SELECT count(*) FROM badge_obtenu b JOIN regles_badges r ON r.version = b.regles_version"
            " WHERE r.paliers[5] = 20)"
        )
    ).scalar()
    if au_dela:
        raise RuntimeError(
            "Retour à 12 places impossible : des quiz, des places réussies ou des badges dépassent la 12e place."
        )
    connexion.execute(sa.text("UPDATE bareme SET en_service = false WHERE code = 'eleve.quiz_certification'"))
    # Les versions ajoutées ne servent plus si aucun badge ni aucune partie ne s'y rattache ; sinon elles restent.
    connexion.execute(
        sa.text(
            "DELETE FROM regles_badges r WHERE r.paliers[5] = 20 "
            "AND NOT EXISTS (SELECT 1 FROM badge_obtenu b WHERE b.regles_version = r.version)"
        )
    )
    connexion.execute(
        sa.text(
            "DELETE FROM parametres_quiz p WHERE p.arret_premiere_erreur "
            "AND NOT EXISTS (SELECT 1 FROM tentative_quiz t WHERE t.parametres_id = p.id)"
        )
    )
    _remplacer("parametres_quiz", "tentatives_valide", "tentatives_par_jour >= 1")
    connexion.execute(sa.text("UPDATE parametres_quiz SET tentatives_par_jour = 10 WHERE tentatives_par_jour IS NULL"))
    op.alter_column("parametres_quiz", "tentatives_par_jour", existing_type=sa.Integer(), nullable=False)
    op.drop_column("parametres_quiz", "arret_premiere_erreur")
    op.drop_constraint(op.f("ck_regles_badges_dernier_palier"), "regles_badges", type_="check")
    op.create_check_constraint(op.f("ck_regles_badges_dernier_palier_12"), "regles_badges", "paliers[5] = 12")
    _remplacer("place_reussie", "place_valide", "place BETWEEN 1 AND 12")
    _remplacer("quiz", "place_valide", "place BETWEEN 1 AND 12")
