"""jeux : 100 quiz sur les 1 000 questions (spec 050)

Les 80 quiz Jeux de la banque officielle (spec 049) sont dépubliés, avec un motif, et remplacés par les 100 quiz de
`alembic/donnees/jeux_100.json`, qui couvrent les 1 000 questions : les 200 questions de la certification y figurent
aussi. Un quiz Jeux numéroté encore publié hors des 80 (un ancien défi republié) est dépublié lui aussi.
Les parties en cours sur ces quiz sont closes sans réussite ; les parties jouées et les points restent. Les
20 quiz de certification ne changent pas.

Rien n'est fait sur une base sans les 80 quiz de la spec 049, ni sur une base qui a déjà les 100 quiz.

Le retour arrière retire les 100 quiz et republie les 80, tant qu'aucun des 100 n'a été joué.

Revision ID: d7b3e9f14a62
Revises: c5f1a8e3d920
Create Date: 2026-11-23

"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d7b3e9f14a62"
down_revision: str | Sequence[str] | None = "c5f1a8e3d920"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FICHIER = Path(__file__).resolve().parents[1] / "donnees" / "jeux_100.json"
VALIDATEUR = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
QUALITE = "Document officiel « Banque de 1 000 questions – Quiz santé des Clubs Santé »"
DESCRIPTION_80 = "Banque officielle des Clubs Santé (spec 049)"
DESCRIPTION_100 = "Banque officielle des Clubs Santé, 100 quiz (spec 050)"
MOTIF = "Recomposés en 100 quiz sur les 1 000 questions (spec 050)."

quiz = sa.table(
    "quiz",
    sa.column("id", sa.Uuid()),
    sa.column("titre", sa.String()),
    sa.column("description", sa.String()),
    sa.column("axe_code", sa.String()),
    sa.column("etat", sa.String()),
    sa.column("parcours", sa.String()),
    sa.column("niveau", sa.String()),
    sa.column("numero", sa.Integer()),
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
    sa.column("explication", sa.String()),
    sa.column("ordre", sa.Integer()),
)

LES_80 = "parcours = 'jeux' AND description LIKE :d80"
LES_100 = "parcours = 'jeux' AND description LIKE :d100"
MOTIFS = {"d80": f"{DESCRIPTION_80}%", "d100": f"{DESCRIPTION_100}%"}


def _existe(connexion: sa.Connection, condition: str) -> bool:
    return bool(connexion.execute(sa.text(f"SELECT 1 FROM quiz WHERE {condition} LIMIT 1"), MOTIFS).first())


def upgrade() -> None:
    connexion = op.get_bind()
    if _existe(connexion, LES_100):
        print("Spec 050 : les 100 quiz Jeux sont déjà là.")
        return
    if not _existe(connexion, f"{LES_80} AND etat = 'publie'"):
        print("Spec 050 : aucun des 80 quiz de la banque officielle n'est publié, rien à recomposer.")
        return
    maintenant = datetime.now(UTC)
    # D'abord la dépublication : elle attend les lancements de partie en cours (qui verrouillent la ligne du quiz), et
    # les suivants trouvent le quiz dépublié. Tout quiz Jeux numéroté encore publié (un ancien défi republié par
    # l'équipe) laisse aussi sa place : les numéros 1 à 100 reviennent aux nouveaux quiz.
    connexion.execute(
        sa.text(
            "UPDATE quiz SET etat = 'depublie', motif = :motif, version = version + 1, modifie_le = :maintenant "
            "WHERE parcours = 'jeux' AND etat = 'publie' AND numero IS NOT NULL"
        ),
        {"motif": MOTIF, "maintenant": maintenant},
    )
    # Puis les parties restées en cours sur ces quiz : closes sans réussite, aucune nouvelle ne peut plus démarrer.
    connexion.execute(sa.text("LOCK TABLE tentative_quiz IN SHARE ROW EXCLUSIVE MODE"))
    connexion.execute(
        sa.text(
            "UPDATE tentative_quiz SET etat = 'terminee', reussie = false, terminee_le = :maintenant "
            "WHERE etat = 'en_cours' AND quiz_id IN (SELECT id FROM quiz WHERE parcours = 'jeux' AND motif = :motif)"
        ),
        {"motif": MOTIF, "maintenant": maintenant},
    )
    for entree in json.loads(FICHIER.read_text(encoding="utf-8")):
        quiz_id = uuid7()
        connexion.execute(
            quiz.insert().values(
                id=quiz_id,
                titre=entree["titre"],
                description=entree["description"],
                axe_code=entree["axe"],
                etat="publie",
                parcours="jeux",
                niveau=entree["niveau"],
                numero=entree["numero"],
                contenu_de_test=False,
                validateur_nom=VALIDATEUR,
                validateur_qualite=QUALITE,
                publie_le=maintenant,
            )
        )
        connexion.execute(
            question.insert(),
            [
                {
                    "id": uuid7(),
                    "quiz_id": quiz_id,
                    "enonce": q["enonce"],
                    "choix": q["choix"],
                    "bonne_reponse": q["bonne"],
                    "explication": None,
                    "ordre": rang,
                }
                for rang, q in enumerate(entree["questions"], start=1)
            ],
        )
    print("Spec 050 : 100 quiz Jeux publiés sur les 1 000 questions, les 80 précédents dépubliés.")


def downgrade() -> None:
    connexion = op.get_bind()
    # Aucune partie ne démarre sur un des 100 quiz entre la vérification et leur retrait.
    connexion.execute(sa.text("LOCK TABLE tentative_quiz IN SHARE ROW EXCLUSIVE MODE"))
    joues = connexion.execute(
        sa.text(f"SELECT 1 FROM tentative_quiz t JOIN quiz ON quiz.id = t.quiz_id WHERE {LES_100} LIMIT 1"), MOTIFS
    ).first()
    if joues:
        raise RuntimeError("Les 100 quiz Jeux de la spec 050 ont été joués : ils ne se retirent plus.")
    if not _existe(connexion, LES_100):
        return
    connexion.execute(
        sa.text(f"DELETE FROM question_quiz WHERE quiz_id IN (SELECT id FROM quiz WHERE {LES_100})"), MOTIFS
    )
    connexion.execute(sa.text(f"DELETE FROM quiz WHERE {LES_100}"), MOTIFS)
    connexion.execute(
        sa.text(
            "UPDATE quiz SET etat = 'publie', motif = NULL, version = version + 1, modifie_le = now() "
            f"WHERE {LES_80} AND etat = 'depublie' AND motif = :motif"
        ),
        MOTIFS | {"motif": MOTIF},
    )
