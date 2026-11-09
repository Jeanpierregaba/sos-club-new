"""Quiz santé et joueurs sans compte (spec 031)

Charge les 922 QCM du document officiel « Jeu Quiz Santé » (AIMES-AFRIQUE, Clubs Santé SOS Docteur TV), regroupés
en 34 quiz « jeux » publiés, depuis `alembic/donnees/quiz_sante.json`. Un quiz déjà présent (même titre) n'est ni
dupliqué ni modifié. Ajoute le rôle `invite` : un joueur sans compte, sans e-mail.

Revision ID: ceae698cb3d6
Revises: 088365e0aeb8
Create Date: 2026-11-09 18:34:54.415419

"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "ceae698cb3d6"
down_revision: str | Sequence[str] | None = "088365e0aeb8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FICHIER = Path(__file__).resolve().parents[1] / "donnees" / "quiz_sante.json"
VALIDATEUR = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
QUALITE = "Document officiel « Jeu Quiz Santé » (922 QCM)"

quiz = sa.table(
    "quiz",
    sa.column("id", sa.Uuid()),
    sa.column("titre", sa.String()),
    sa.column("description", sa.String()),
    sa.column("axe_code", sa.String()),
    sa.column("etat", sa.String()),
    sa.column("parcours", sa.String()),
    sa.column("contenu_de_test", sa.Boolean()),
    sa.column("validateur_nom", sa.String()),
    sa.column("validateur_qualite", sa.String()),
    sa.column("publie_le", sa.DateTime(timezone=True)),
)
question = sa.table(
    "question_quiz",
    sa.column("id", sa.Uuid()),
    sa.column("quiz_id", sa.Uuid()),
    sa.column("enonce", sa.String()),
    sa.column("choix", postgresql.JSONB()),
    sa.column("bonne_reponse", sa.Integer()),
    sa.column("ordre", sa.Integer()),
)


def _titres() -> list[str]:
    return [q["titre"] for q in json.loads(FICHIER.read_text(encoding="utf-8"))]


def upgrade() -> None:
    op.drop_constraint(op.f("ck_utilisateur_role"), "utilisateur", type_="check")
    op.create_check_constraint(
        op.f("ck_utilisateur_role"), "utilisateur", "role IN ('eleve', 'encadreur', 'admin', 'visiteur', 'invite')"
    )
    op.drop_constraint(op.f("ck_utilisateur_email_obligatoire_sauf_eleve"), "utilisateur", type_="check")
    op.create_check_constraint(
        op.f("ck_utilisateur_email_obligatoire_sauf_eleve"),
        "utilisateur",
        "email IS NOT NULL OR role IN ('eleve', 'invite')",
    )

    connexion = op.get_bind()
    existants = set(connexion.execute(sa.text("SELECT titre FROM quiz WHERE parcours = 'jeux'")).scalars().all())
    maintenant = datetime.now(UTC)
    for donnees in json.loads(FICHIER.read_text(encoding="utf-8")):
        if donnees["titre"] in existants:
            continue
        quiz_id = uuid7()
        connexion.execute(
            quiz.insert().values(
                id=quiz_id, titre=donnees["titre"], description=donnees["description"], axe_code=donnees["axe"],
                etat="publie", parcours="jeux", contenu_de_test=False, validateur_nom=VALIDATEUR,
                validateur_qualite=QUALITE, publie_le=maintenant,
            )
        )  # fmt: skip
        connexion.execute(
            question.insert(),
            [
                {"id": uuid7(), "quiz_id": quiz_id, "enonce": q["enonce"], "choix": q["choix"],
                 "bonne_reponse": q["bonne"], "ordre": rang}
                for rang, q in enumerate(donnees["questions"], start=1)
            ],
        )  # fmt: skip


def downgrade() -> None:
    """Retire les quiz chargés qui n'ont jamais été joués, et les joueurs sans compte avec leurs parties."""
    connexion = op.get_bind()
    invites = "SELECT id FROM utilisateur WHERE role = 'invite'"
    connexion.execute(
        sa.text(
            f"DELETE FROM reponse_quiz WHERE tentative_id IN (SELECT id FROM tentative_quiz WHERE joueur_id IN ({invites}))"
        )
    )
    connexion.execute(sa.text(f"DELETE FROM tentative_quiz WHERE joueur_id IN ({invites})"))
    connexion.execute(sa.text("DELETE FROM utilisateur WHERE role = 'invite'"))
    titres = sa.bindparam("titres", _titres(), expanding=True)
    jamais_joues = sa.text(
        "SELECT id FROM quiz WHERE parcours = 'jeux' AND titre IN :titres "
        "AND NOT EXISTS (SELECT 1 FROM tentative_quiz t WHERE t.quiz_id = quiz.id)"
    ).bindparams(titres)
    ids = connexion.execute(jamais_joues).scalars().all()
    if ids:
        connexion.execute(sa.text("DELETE FROM question_quiz WHERE quiz_id = ANY(:ids)"), {"ids": list(ids)})
        connexion.execute(sa.text("DELETE FROM quiz WHERE id = ANY(:ids)"), {"ids": list(ids)})

    op.drop_constraint(op.f("ck_utilisateur_email_obligatoire_sauf_eleve"), "utilisateur", type_="check")
    op.create_check_constraint(
        op.f("ck_utilisateur_email_obligatoire_sauf_eleve"), "utilisateur", "email IS NOT NULL OR role = 'eleve'"
    )
    op.drop_constraint(op.f("ck_utilisateur_role"), "utilisateur", type_="check")
    op.create_check_constraint(
        op.f("ck_utilisateur_role"), "utilisateur", "role IN ('eleve', 'encadreur', 'admin', 'visiteur')"
    )
