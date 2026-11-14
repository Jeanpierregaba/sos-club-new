"""cent quiz jeux, niveaux et etoiles

Lot 2 de la spec 034 : les 100 défis du parcours officiel deviennent 100 quiz Jeux publiés, chacun avec son
niveau (40 Débutant, 30 Intermédiaire, 20 Avancé, 10 Expert, par cotation), son numéro et le lot du Jeu Quiz Santé
d'où il tire ses questions (`alembic/donnees/defis_jeux.json`).

Chaque quiz reçoit une réserve de 20 questions copiées des questions actives des quiz de son lot (corrections de
l'équipe comprises) : une fenêtre qui tourne sur le lot, pour que deux quiz voisins ne partagent qu'une partie de
leurs questions. Les 34 quiz Jeux de la spec 031 sont dépubliés ; leurs parties restent dans l'historique.

Les gains par niveau et les étoiles entrent en service ; l'ancien gain unique d'un quiz en sort.

Revision ID: 0b5d089c2f2d
Revises: b202206425b3
Create Date: 2026-11-11

"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0b5d089c2f2d"
down_revision: str | Sequence[str] | None = "b202206425b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FICHIER = Path(__file__).resolve().parents[1] / "donnees" / "defis_jeux.json"
VALIDATEUR = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
QUALITE = "Document officiel « Jeu Quiz Santé » (922 QCM)"
RESERVE = 20
MOTIF = "Remplacé par les 100 quiz du parcours officiel (spec 034)."
EN_SERVICE = [f"eleve.quiz_{n}" for n in ("debutant", "intermediaire", "avance", "expert")] + [
    f"eleve.etoile_{n}" for n in ("debutant", "intermediaire", "avance", "expert")
]

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
    sa.column("niveau", sa.String()),
    sa.column("numero", sa.Integer()),
    sa.column("lot", sa.Integer()),
)
question = sa.table(
    "question_quiz",
    sa.column("id", sa.Uuid()),
    sa.column("quiz_id", sa.Uuid()),
    sa.column("enonce", sa.String()),
    sa.column("choix", postgresql.JSONB()),
    sa.column("bonne_reponse", sa.Integer()),
    sa.column("explication", sa.String()),
    sa.column("ordre", sa.Integer()),
)


def _reserves(connexion: sa.Connection) -> dict[int, list[sa.Row]]:
    """Les questions actives de chaque lot, dans l'ordre du document (titre du quiz, puis rang)."""
    lignes = connexion.execute(
        sa.text(
            "SELECT substring(q.description from '^Lot (\\d+)')::int AS lot, qq.enonce, qq.choix, qq.bonne_reponse, "
            "qq.explication FROM question_quiz qq JOIN quiz q ON q.id = qq.quiz_id "
            "WHERE q.parcours = 'jeux' AND q.etat = 'publie' AND NOT q.contenu_de_test AND q.numero IS NULL "
            "AND qq.active AND q.description ~ '^Lot \\d+' "
            "ORDER BY lot, q.publie_le, q.titre, qq.ordre"
        )
    ).all()
    par_lot: dict[int, list[sa.Row]] = {}
    for ligne in lignes:
        par_lot.setdefault(ligne.lot, []).append(ligne)
    return par_lot


def upgrade() -> None:
    op.add_column("quiz", sa.Column("niveau", sa.String(length=20), nullable=True))
    op.add_column("quiz", sa.Column("numero", sa.Integer(), nullable=True))
    op.add_column("quiz", sa.Column("lot", sa.Integer(), nullable=True))
    op.create_check_constraint(
        op.f("ck_quiz_niveau"), "quiz", "niveau IN ('debutant', 'intermediaire', 'avance', 'expert')"
    )
    op.create_check_constraint(
        op.f("ck_quiz_niveau_si_jeux"), "quiz", "parcours = 'jeux' OR (niveau IS NULL AND numero IS NULL)"
    )
    op.create_check_constraint(op.f("ck_quiz_numero_valide"), "quiz", "numero BETWEEN 1 AND 100")
    op.create_index(
        "uq_quiz_numero_publie", "quiz", ["numero"], unique=True, postgresql_where=sa.text("etat = 'publie'")
    )
    op.create_table(
        "etoile_obtenue",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("niveau", sa.String(length=20), nullable=False),
        sa.Column("mouvement_id", sa.Uuid(), nullable=True),
        sa.Column("obtenue_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "niveau IN ('debutant', 'intermediaire', 'avance', 'expert')", name=op.f("ck_etoile_obtenue_niveau_valide")
        ),
        sa.ForeignKeyConstraint(
            ["mouvement_id"],
            ["mouvement_points.id"],
            name=op.f("fk_etoile_obtenue_mouvement_id_mouvement_points"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_etoile_obtenue_utilisateur_id_utilisateur"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_etoile_obtenue")),
        sa.UniqueConstraint("utilisateur_id", "niveau", name=op.f("uq_etoile_obtenue_utilisateur_id_niveau")),
    )

    connexion = op.get_bind()
    reserves = _reserves(connexion)
    defis = json.loads(FICHIER.read_text(encoding="utf-8"))
    # Seulement si les questions du Jeu Quiz Santé sont là (une base vide, celle des tests, n'en a pas).
    if reserves:
        connexion.execute(
            sa.text(
                "UPDATE quiz SET etat = 'depublie', motif = :motif, version = version + 1 "
                "WHERE parcours = 'jeux' AND etat = 'publie' AND numero IS NULL AND description ~ '^Lot \\d+'"
            ).bindparams(motif=MOTIF)
        )
        maintenant = datetime.now(UTC)
        par_lot: dict[int, list[dict]] = {}
        for defi in defis:
            par_lot.setdefault(defi["lot"], []).append(defi)
        for lot, du_lot in par_lot.items():
            pool = reserves.get(lot, [])
            if len(pool) < RESERVE:
                raise RuntimeError(f"Le lot {lot} n'a que {len(pool)} questions actives : il en faut {RESERVE}.")
            for i, defi in enumerate(du_lot):
                quiz_id = uuid7()
                connexion.execute(
                    quiz.insert().values(
                        id=quiz_id, titre=defi["titre"], axe_code=defi["axe"], etat="publie", parcours="jeux",
                        description=f"Lot {lot} — {defi['pole']} · défi n° {defi['numero']} du parcours officiel.",
                        contenu_de_test=False, validateur_nom=VALIDATEUR, validateur_qualite=QUALITE,
                        publie_le=maintenant, niveau=defi["niveau"], numero=defi["numero"], lot=lot,
                    )
                )  # fmt: skip
                debut = round(i * len(pool) / len(du_lot))
                fenetre = [pool[(debut + k) % len(pool)] for k in range(RESERVE)]
                connexion.execute(
                    question.insert(),
                    [
                        {"id": uuid7(), "quiz_id": quiz_id, "enonce": q.enonce, "choix": q.choix,
                         "bonne_reponse": q.bonne_reponse, "explication": q.explication, "ordre": rang}
                        for rang, q in enumerate(fenetre, start=1)
                    ],
                )  # fmt: skip

    connexion.execute(
        sa.text("UPDATE bareme SET en_service = true WHERE code IN :codes").bindparams(
            sa.bindparam("codes", value=EN_SERVICE, expanding=True)
        )
    )
    connexion.execute(sa.text("UPDATE bareme SET en_service = false WHERE code = 'eleve.quiz'"))


def downgrade() -> None:
    connexion = op.get_bind()
    connexion.execute(sa.text("UPDATE bareme SET en_service = true WHERE code = 'eleve.quiz'"))
    connexion.execute(
        sa.text("UPDATE bareme SET en_service = false WHERE code IN :codes").bindparams(
            sa.bindparam("codes", value=EN_SERVICE, expanding=True)
        )
    )
    op.drop_table("etoile_obtenue")
    # Les quiz numérotés jamais joués disparaissent ; un quiz joué reste (historique), sans son numéro.
    jamais_joues = (
        connexion.execute(
            sa.text(
                "SELECT id FROM quiz WHERE numero IS NOT NULL "
                "AND NOT EXISTS (SELECT 1 FROM tentative_quiz t WHERE t.quiz_id = quiz.id)"
            )
        )
        .scalars()
        .all()
    )
    if jamais_joues:
        connexion.execute(sa.text("DELETE FROM question_quiz WHERE quiz_id = ANY(:ids)"), {"ids": list(jamais_joues)})
        connexion.execute(sa.text("DELETE FROM quiz WHERE id = ANY(:ids)"), {"ids": list(jamais_joues)})
    connexion.execute(sa.text("UPDATE quiz SET etat = 'depublie' WHERE numero IS NOT NULL AND etat = 'publie'"))
    connexion.execute(
        sa.text("UPDATE quiz SET etat = 'publie', motif = NULL WHERE etat = 'depublie' AND motif = :motif").bindparams(
            motif=MOTIF
        )
    )
    op.drop_index("uq_quiz_numero_publie", table_name="quiz", postgresql_where=sa.text("etat = 'publie'"))
    op.drop_constraint(op.f("ck_quiz_numero_valide"), "quiz", type_="check")
    op.drop_constraint(op.f("ck_quiz_niveau_si_jeux"), "quiz", type_="check")
    op.drop_constraint(op.f("ck_quiz_niveau"), "quiz", type_="check")
    op.drop_column("quiz", "lot")
    op.drop_column("quiz", "numero")
    op.drop_column("quiz", "niveau")
