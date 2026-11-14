"""classements et corrections des points

Spec 036 (R13, ADR-0013) : le registre des points devient consultable et corrigeable par l'admin. Une correction
est une ligne `admin.correction`, toujours motivée, qui ne porte jamais de part de club. Une annulation peut
désormais être positive (celle d'une correction négative). Les classements lisent par semestre et par club : trois
index les servent.

Copie figée des valeurs : la grille de `app.points.bareme` peut évoluer après cette migration.

Revision ID: f3a1c9e7b2d4
Revises: d6d0ef005da8
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a1c9e7b2d4"
down_revision: str | Sequence[str] | None = "d6d0ef005da8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# La ligne technique de la correction : jamais un gain automatique, masquée du barème réglable.
CORRECTION = {
    "code": "admin.correction",
    "beneficiaire": "admin",
    "libelle": "Correction manuelle du score",
    "montant": 0,
    "propose": False,
    "en_service": True,
    "actif": False,
    "ordre": 47,
}

ANCIEN_MONTANT_SIGNE = "(annule_id IS NULL AND montant > 0) OR (annule_id IS NOT NULL AND montant < 0)"
NOUVEAU_MONTANT_SIGNE = (
    "(annule_id IS NULL AND (montant > 0 OR (action = 'admin.correction' AND motif IS NOT NULL)))"
    " OR (annule_id IS NOT NULL AND montant <> 0)"
)
MOTIF_CORRECTION = (
    "(action <> 'admin.correction' OR motif IS NOT NULL)"
    " AND (motif IS NULL OR action = 'admin.correction' OR annule_id IS NOT NULL)"
)
ANCIENS_BENEFICIAIRES = "beneficiaire IN ('eleve', 'encadreur', 'club')"
NOUVEAUX_BENEFICIAIRES = "beneficiaire IN ('eleve', 'encadreur', 'club', 'admin')"


def upgrade() -> None:
    op.add_column("mouvement_points", sa.Column("motif", sa.String(length=500), nullable=True))
    op.drop_constraint(op.f("ck_mouvement_points_montant_signe"), "mouvement_points", type_="check")
    op.create_check_constraint(op.f("ck_mouvement_points_montant_signe"), "mouvement_points", NOUVEAU_MONTANT_SIGNE)
    op.create_check_constraint(op.f("ck_mouvement_points_motif_correction"), "mouvement_points", MOTIF_CORRECTION)

    # Les classements lisent le semestre par bénéficiaire et par club ; le registre trie par date.
    op.create_index(
        "ix_mouvement_points_semestre_id_utilisateur_id",
        "mouvement_points",
        ["semestre_id", "utilisateur_id"],
    )
    op.create_index(
        "ix_mouvement_points_semestre_id_club_id",
        "mouvement_points",
        ["semestre_id", "club_id"],
        postgresql_where=sa.text("club_id IS NOT NULL"),
    )
    op.create_index("ix_mouvement_points_cree_le", "mouvement_points", ["cree_le"])

    op.drop_constraint(op.f("ck_bareme_beneficiaire"), "bareme", type_="check")
    op.create_check_constraint(op.f("ck_bareme_beneficiaire"), "bareme", NOUVEAUX_BENEFICIAIRES)
    op.execute(
        sa.text(
            "INSERT INTO bareme (code, beneficiaire, libelle, montant, propose, en_service, actif, ordre) "
            "VALUES (:code, :beneficiaire, :libelle, :montant, :propose, :en_service, :actif, :ordre) "
            "ON CONFLICT (code) DO NOTHING"
        ).bindparams(**CORRECTION)
    )


def downgrade() -> None:
    connexion = op.get_bind()
    # Ces données n'existaient pas avant R13 : l'ancien schéma ne peut pas les représenter.
    if connexion.scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM mouvement_points WHERE motif IS NOT NULL OR action = 'admin.correction')")
    ):
        raise RuntimeError("Des corrections ou des motifs existent : le retour arrière de la spec 036 est impossible.")

    op.execute(sa.text("DELETE FROM bareme WHERE code = 'admin.correction'"))
    op.drop_constraint(op.f("ck_bareme_beneficiaire"), "bareme", type_="check")
    op.create_check_constraint(op.f("ck_bareme_beneficiaire"), "bareme", ANCIENS_BENEFICIAIRES)

    op.drop_index("ix_mouvement_points_cree_le", table_name="mouvement_points")
    op.drop_index("ix_mouvement_points_semestre_id_club_id", table_name="mouvement_points")
    op.drop_index("ix_mouvement_points_semestre_id_utilisateur_id", table_name="mouvement_points")

    op.drop_constraint(op.f("ck_mouvement_points_motif_correction"), "mouvement_points", type_="check")
    op.drop_constraint(op.f("ck_mouvement_points_montant_signe"), "mouvement_points", type_="check")
    op.create_check_constraint(op.f("ck_mouvement_points_montant_signe"), "mouvement_points", ANCIEN_MONTANT_SIGNE)
    op.drop_column("mouvement_points", "motif")
