"""Cartes numériques (spec 040) : la table des cartes, la séquence des numéros, et la délivrance aux comptes existants.

Non destructive : une table et une séquence neuves. Chaque élève reçoit sa carte membre, chaque encadreur vérifié sa
carte encadreur, dans l'ordre de création des comptes. Le code du QR est produit en SQL natif, sans extension :
32 caractères URL-sûrs tirés de deux `gen_random_uuid()`, la forme de `secrets.token_urlsafe(24)`.

Revision ID: 4618adf52b56
Revises: 865d24f039ea
Create Date: 2026-11-16 19:09:37.992911

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4618adf52b56"
down_revision: str | Sequence[str] | None = "865d24f039ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CODE = (
    "translate(left(encode(sha256((gen_random_uuid()::text || gen_random_uuid()::text)::bytea), 'base64'), 32),"
    " '+/', '-_')"
)


def _delivrer(type_carte: str, prefixe: str, comptes: str) -> None:
    op.execute(
        f"""
        INSERT INTO carte (id, utilisateur_id, type, numero, code)
        SELECT gen_random_uuid(), compte.id, '{type_carte}',
               '{prefixe}-' || lpad(nextval('carte_numero_seq')::text, 6, '0'), {CODE}
        FROM (SELECT utilisateur.id FROM utilisateur {comptes} ORDER BY utilisateur.cree_le, utilisateur.id) AS compte
        """
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "carte",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=True),
        sa.Column(
            "type",
            sa.Enum("membre", "encadreur", name="type_carte", native_enum=False, create_constraint=True, length=10),
            nullable=False,
        ),
        sa.Column("numero", sa.String(length=14), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("delivree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("suspendue_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspendue_par", sa.Uuid(), nullable=True),
        sa.Column("motif_suspension", sa.Text(), nullable=True),
        sa.CheckConstraint("code ~ '^[A-Za-z0-9_-]{32}$'", name=op.f("ck_carte_code_format")),
        sa.CheckConstraint(
            "(suspendue_le IS NULL) = (motif_suspension IS NULL)", name=op.f("ck_carte_motif_si_suspendue")
        ),
        sa.ForeignKeyConstraint(
            ["suspendue_par"], ["utilisateur.id"], name=op.f("fk_carte_suspendue_par_utilisateur"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_carte_utilisateur_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_carte")),
        sa.UniqueConstraint("code", name=op.f("uq_carte_code")),
        sa.UniqueConstraint("numero", name=op.f("uq_carte_numero")),
        sa.UniqueConstraint("utilisateur_id", name=op.f("uq_carte_utilisateur_id")),
    )
    op.execute("CREATE SEQUENCE carte_numero_seq")
    _delivrer("membre", "CS-M", "JOIN eleve ON eleve.utilisateur_id = utilisateur.id")
    _delivrer(
        "encadreur",
        "CS-E",
        "JOIN encadreur ON encadreur.utilisateur_id = utilisateur.id WHERE encadreur.etat = 'actif'",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("carte")
    op.execute("DROP SEQUENCE carte_numero_seq")
