"""Commentaires prémodérés (spec 025) : parent d'un contenu, état « retiré », index des plafonds.

Non destructive : une colonne nulle, un état de plus et des contraintes élargies. Le retour en arrière échoue s'il
existe des commentaires (contraintes d'origine) : il faut d'abord les supprimer.

Revision ID: 7b3e5c1d9a42
Revises: 6ec714321408
Create Date: 2026-11-08 02:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b3e5c1d9a42"
down_revision: str | Sequence[str] | None = "6ec714321408"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIONS_EN_SERVICE = (
    "UPDATE bareme SET en_service = {valeur} WHERE code IN ('eleve.commentaire', 'encadreur.commentaire')"
)
ETATS = "'brouillon', 'en_attente', 'a_corriger', 'refuse', 'publie', 'depublie'"


def _contraintes(etats: str, hors_ligne: str, adresse: str) -> None:
    for nom in ("etat_contenu", "hors_ligne_si_retire", "adresse_si_publie"):
        op.drop_constraint(op.f(f"ck_contenu_{nom}"), "contenu", type_="check")
    op.create_check_constraint(op.f("ck_contenu_etat_contenu"), "contenu", f"etat IN ({etats})")
    op.create_check_constraint(
        op.f("ck_contenu_hors_ligne_si_retire"), "contenu", f"version_publiee_id IS NULL OR etat NOT IN ({hors_ligne})"
    )
    op.create_check_constraint(op.f("ck_contenu_adresse_si_publie"), "contenu", adresse)


def upgrade() -> None:
    op.add_column("contenu", sa.Column("parent_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_contenu_parent_id_contenu", "contenu", "contenu", ["parent_id"], ["id"], ondelete="RESTRICT"
    )
    _contraintes(
        f"{ETATS}, 'retire'",
        "'refuse', 'depublie', 'retire'",
        "version_publiee_id IS NULL OR adresse IS NOT NULL OR parent_id IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_contenu_commentaire_a_un_parent"), "contenu", "(type = 'commentaire') = (parent_id IS NOT NULL)"
    )
    op.create_index(
        "ix_contenu_commentaires_publics",
        "contenu",
        ["parent_id", "publie_le"],
        postgresql_where=sa.text("version_publiee_id IS NOT NULL"),
    )
    op.create_index("ix_contenu_auteur_id_type_cree_le", "contenu", ["auteur_id", "type", "cree_le"])
    op.execute(ACTIONS_EN_SERVICE.format(valeur="true"))


def downgrade() -> None:
    op.execute(ACTIONS_EN_SERVICE.format(valeur="false"))
    op.drop_index("ix_contenu_auteur_id_type_cree_le", table_name="contenu")
    op.drop_index("ix_contenu_commentaires_publics", table_name="contenu")
    op.drop_constraint(op.f("ck_contenu_commentaire_a_un_parent"), "contenu", type_="check")
    _contraintes(ETATS, "'refuse', 'depublie'", "version_publiee_id IS NULL OR adresse IS NOT NULL")
    op.drop_constraint("fk_contenu_parent_id_contenu", "contenu", type_="foreignkey")
    op.drop_column("contenu", "parent_id")
