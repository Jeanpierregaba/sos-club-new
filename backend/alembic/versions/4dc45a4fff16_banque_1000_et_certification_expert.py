"""banque 1000 et certification expert

Spec 043 :

- le lot 7 de la banque (`alembic/donnees/quiz_sante_lot7.json`) : les 78 QCM du « Quiz Santé » des Clubs Santé,
  en 15 quiz Jeux dépubliés, réserve comme les 922 QCM du Jeu Quiz Santé ;
- les 20 quiz de certification de niveau expert (`alembic/donnees/certification_expert.json`), publiés sur les
  places 1 à 20. Un vrai quiz déjà publié sur une place y reste ; un quiz de test est dépublié pour laisser la place.

Rien n'est fait sur une base sans la banque (celle des tests), comme pour la migration des 100 défis. Un quiz dont le
titre existe déjà n'est ni dupliqué ni modifié.

Revision ID: 4dc45a4fff16
Revises: 8224c2108aff
Create Date: 2026-11-19

"""

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "4dc45a4fff16"
down_revision: str | Sequence[str] | None = "8224c2108aff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DONNEES = Path(__file__).resolve().parents[1] / "donnees"
LOT7 = DONNEES / "quiz_sante_lot7.json"
CERTIFICATION = DONNEES / "certification_expert.json"
VALIDATEUR = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
QUALITE_LOT7 = "Document officiel « Quiz Santé – 78 questions »"
QUALITE_CERTIFICATION = "Documents officiels « Jeu Quiz Santé », défis Expert"
DESCRIPTION_CERTIFICATION = "Niveau expert · questions des défis Expert du parcours Jeux."
MOTIF_RESERVE = "Réserve de la banque (spec 043)."
MOTIF_TEST = "Place rendue au quiz de niveau expert (spec 043)."
MOTIF_RETOUR = "Retour arrière de la spec 043."

journal = logging.getLogger("alembic.runtime.migration")

quiz = sa.table(
    "quiz",
    sa.column("id", sa.Uuid()),
    sa.column("titre", sa.String()),
    sa.column("description", sa.String()),
    sa.column("axe_code", sa.String()),
    sa.column("etat", sa.String()),
    sa.column("parcours", sa.String()),
    sa.column("place", sa.Integer()),
    sa.column("contenu_de_test", sa.Boolean()),
    sa.column("validateur_nom", sa.String()),
    sa.column("validateur_qualite", sa.String()),
    sa.column("publie_le", sa.DateTime(timezone=True)),
    sa.column("motif", sa.String()),
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


def _lire(fichier: Path) -> list[dict]:
    return json.loads(fichier.read_text(encoding="utf-8"))


def _banque_chargee(connexion: sa.Connection) -> bool:
    return (
        connexion.execute(
            sa.text(
                "SELECT 1 FROM quiz WHERE parcours = 'jeux' AND numero IS NULL AND NOT contenu_de_test "
                "AND description ~ '^Lot [1-6] — ' LIMIT 1"
            )
        ).first()
        is not None
    )


def _inserer(connexion: sa.Connection, valeurs: dict, questions: list[dict]) -> None:
    quiz_id = uuid7()
    connexion.execute(quiz.insert().values(id=quiz_id, contenu_de_test=False, validateur_nom=VALIDATEUR, **valeurs))
    connexion.execute(
        question.insert(),
        [
            {"id": uuid7(), "quiz_id": quiz_id, "enonce": q["enonce"], "choix": q["choix"],
             "bonne_reponse": q["bonne"], "explication": q.get("explication") or None, "ordre": rang}
            for rang, q in enumerate(questions, start=1)
        ],
    )  # fmt: skip


def upgrade() -> None:
    connexion = op.get_bind()
    if not _banque_chargee(connexion):
        return
    maintenant = datetime.now(UTC)

    jeux = set(connexion.execute(sa.text("SELECT titre FROM quiz WHERE parcours = 'jeux'")).scalars())
    for theme in _lire(LOT7):
        if theme["titre"] in jeux:
            continue
        _inserer(
            connexion,
            {"titre": theme["titre"], "description": theme["description"], "axe_code": theme["axe"],
             "etat": "depublie", "parcours": "jeux", "validateur_qualite": QUALITE_LOT7, "publie_le": maintenant,
             "motif": MOTIF_RESERVE},
            theme["questions"],
        )  # fmt: skip

    certification = set(connexion.execute(sa.text("SELECT titre FROM quiz WHERE parcours = 'certification'")).scalars())
    for place in _lire(CERTIFICATION):
        if place["titre"] in certification:
            continue
        occupants = connexion.execute(
            sa.text(
                "SELECT id, titre, contenu_de_test FROM quiz "
                "WHERE parcours = 'certification' AND place = :place AND etat = 'publie'"
            ),
            {"place": place["place"]},
        ).all()
        # Un vrai quiz soumis sur cette place ne pourra plus être approuvé (une place, un quiz publié) : on le signale.
        for attente in connexion.execute(
            sa.text(
                "SELECT titre FROM quiz WHERE parcours = 'certification' AND place = :place AND etat = 'soumis' "
                "AND NOT contenu_de_test"
            ),
            {"place": place["place"]},
        ).scalars():
            journal.warning("Place %s : « %s » est soumis ; il faudra dépublier le quiz expert pour l'approuver.",
                            place["place"], attente)  # fmt: skip
        reel = next((o for o in occupants if not o.contenu_de_test), None)
        if reel is not None:
            journal.warning("Place %s laissée à « %s » : déjà occupée par un vrai quiz.", place["place"], reel.titre)
            continue
        if occupants:
            connexion.execute(
                sa.text(
                    "UPDATE quiz SET etat = 'depublie', motif = :motif, version = version + 1 WHERE id = ANY(:ids)"
                ),
                {"motif": MOTIF_TEST, "ids": [o.id for o in occupants]},
            )
        _inserer(
            connexion,
            {"titre": place["titre"], "description": DESCRIPTION_CERTIFICATION, "axe_code": place["axe"],
             "etat": "publie", "parcours": "certification", "place": place["place"],
             "validateur_qualite": QUALITE_CERTIFICATION, "publie_le": maintenant},
            place["questions"],
        )  # fmt: skip


def downgrade() -> None:
    """Retire les quiz chargés jamais joués ; ceux qui ont été joués restent, dépubliés (historique). Les quiz de
    test dépubliés ne sont pas republiés."""
    connexion = op.get_bind()
    titres = [t["titre"] for t in _lire(LOT7)] + [p["titre"] for p in _lire(CERTIFICATION)]
    charges = sa.text(
        "SELECT id FROM quiz WHERE titre = ANY(:titres) AND (parcours = 'certification' OR description ~ '^Lot 7 — ')"
    )
    ids = list(connexion.execute(charges, {"titres": titres}).scalars())
    if not ids:
        return
    joues = set(
        connexion.execute(
            sa.text("SELECT DISTINCT quiz_id FROM tentative_quiz WHERE quiz_id = ANY(:ids)"), {"ids": ids}
        ).scalars()
    )
    jamais_joues = [i for i in ids if i not in joues]
    if jamais_joues:
        connexion.execute(sa.text("DELETE FROM question_quiz WHERE quiz_id = ANY(:ids)"), {"ids": jamais_joues})
        connexion.execute(sa.text("DELETE FROM quiz WHERE id = ANY(:ids)"), {"ids": jamais_joues})
    if joues:
        connexion.execute(
            sa.text(
                "UPDATE quiz SET etat = 'depublie', motif = :motif, version = version + 1 "
                "WHERE id = ANY(:ids) AND etat = 'publie'"
            ),
            {"motif": MOTIF_RETOUR, "ids": list(joues)},
        )
