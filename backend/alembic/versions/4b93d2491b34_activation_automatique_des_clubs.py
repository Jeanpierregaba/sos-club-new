"""Activation automatique des clubs (spec 033, ADR-0011).

Schéma : région des DRE, statuts calculés du club, journal `club_statut`, `signalement_desistement`, un club vivant par
établissement, un rattachement actif par encadreur. Reprise des données :

1. une seule demande de club en attente survit par établissement, et aucune s'il a déjà un club actif ;
2. chaque établissement qui a un élève ou un encadreur vérifié reçoit son club, « en constitution » ;
3. chaque encadreur vérifié est rattaché au club de son établissement, et à lui seul ;
4. chaque élève sans affiliation en cours en reçoit une « à confirmer » au club de son établissement ;
5. chaque club est recalculé : actif au seuil de 3 encadreurs et 21 élèves, sinon en constitution (décision 3 de la
   spec), avec une ligne `migration` au journal.

Revision ID: 4b93d2491b34
Revises: 15ac5cbf557f
Create Date: 2026-11-10 16:31:09.661863

"""

import unicodedata
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b93d2491b34"
down_revision: str | Sequence[str] | None = "15ac5cbf557f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Copies figées : le code de l'application peut évoluer, la migration non.
SEUIL_ENCADREURS = 3
SEUIL_ELEVES = 21
REGIONS = ("maritime", "plateaux", "centrale", "kara", "savanes")
ETATS_CLUB = ("en_constitution", "actif", "en_regularisation", "suspendu", "en_attente", "refuse")
VIVANTS = "('en_constitution', 'actif', 'en_regularisation', 'suspendu')"


def _normaliser(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte.replace("’", "'").replace("‐", "-"))
    return " ".join("".join(c for c in decompose if not unicodedata.combining(c)).casefold().split())


def _liste(valeurs: Sequence[str]) -> str:
    return ", ".join(f"'{v}'" for v in valeurs)


REGION_DES_DRE = """
UPDATE dre SET region = CASE
    WHEN code IN ('grand-lome', 'maritime') OR code LIKE 'golfe%' OR code LIKE 'lome%' THEN 'maritime'
    WHEN code LIKE 'plateaux%' THEN 'plateaux'
    WHEN code LIKE 'centrale%' THEN 'centrale'
    WHEN code LIKE 'kara%' THEN 'kara'
    WHEN code LIKE 'savanes%' THEN 'savanes'
END
"""

# Une demande en attente ne survit que si l'établissement n'a ni club actif, ni demande plus ancienne.
DEMANDES_EN_TROP = """
UPDATE club c SET etat = 'refuse', motif_refus = 'Remplacé par le club de l''établissement (spec 033).',
    decide_le = now()
WHERE c.etat = 'en_attente' AND EXISTS (
    SELECT 1 FROM club a WHERE a.etablissement_id = c.etablissement_id AND a.id <> c.id AND (
        a.etat = 'actif' OR (a.etat = 'en_attente' AND (a.demande_le, a.id) < (c.demande_le, c.id))
    )
)
"""

ETABLISSEMENTS_SANS_CLUB = f"""
SELECT e.id, e.nom FROM etablissement e
WHERE NOT EXISTS (SELECT 1 FROM club c WHERE c.etablissement_id = e.id AND c.etat IN {VIVANTS})
  AND (
    EXISTS (SELECT 1 FROM eleve el WHERE el.etablissement_id = e.id)
    OR EXISTS (SELECT 1 FROM encadreur en WHERE en.etablissement_id = e.id AND en.etat = 'actif')
  )
"""

CLUB_DE = f"(SELECT c.id FROM club c WHERE c.etablissement_id = {{etab}} AND c.etat IN {VIVANTS})"

RATTACHEMENTS_EN_ATTENTE = """
UPDATE rattachement SET etat = 'retire', retire_le = now(),
    motif_retrait = 'Remplacé par l''affiliation automatique (spec 033).'
WHERE etat IN ('en_attente_president', 'en_attente_validation')
"""

RATTACHEMENTS_AILLEURS = f"""
UPDATE rattachement r SET etat = 'retire', retire_le = now(), motif_retrait = 'Un seul club par encadreur (spec 033).'
FROM encadreur en
WHERE r.etat = 'actif' AND en.utilisateur_id = r.encadreur_id
  AND r.club_id IS DISTINCT FROM {CLUB_DE.format(etab="en.etablissement_id")}
"""

RATTACHEMENTS_MANQUANTS = f"""
INSERT INTO rattachement (id, encadreur_id, club_id, etat, demande_le, decide_le)
SELECT gen_random_uuid(), en.utilisateur_id, {CLUB_DE.format(etab="en.etablissement_id")}, 'actif', now(), now()
FROM encadreur en
WHERE en.etat = 'actif'
  AND NOT EXISTS (SELECT 1 FROM rattachement r WHERE r.encadreur_id = en.utilisateur_id AND r.etat = 'actif')
"""

ADHESIONS_AILLEURS = f"""
UPDATE adhesion a SET etat = 'retiree', retire_le = now(), motif_retrait = 'Changement d''établissement.'
FROM eleve el
WHERE a.etat IN ('en_attente_president', 'en_attente_validation', 'active') AND el.utilisateur_id = a.eleve_id
  AND a.club_id IS DISTINCT FROM {CLUB_DE.format(etab="el.etablissement_id")}
"""

ADHESIONS_MANQUANTES = f"""
INSERT INTO adhesion (id, eleve_id, club_id, etat, demande_le)
SELECT gen_random_uuid(), el.utilisateur_id, {CLUB_DE.format(etab="el.etablissement_id")}, 'en_attente_validation',
    now()
FROM eleve el
WHERE NOT EXISTS (
    SELECT 1 FROM adhesion a
    WHERE a.eleve_id = el.utilisateur_id AND a.etat IN ('en_attente_president', 'en_attente_validation', 'active')
)
"""

EFFECTIFS = f"""
SELECT c.id, c.etat, c.demandeur_id IS NULL AS nouveau,
    (SELECT count(DISTINCT r.encadreur_id) FROM rattachement r
        JOIN encadreur en ON en.utilisateur_id = r.encadreur_id
        JOIN utilisateur u ON u.id = r.encadreur_id
     WHERE r.club_id = c.id AND r.etat = 'actif' AND en.etat = 'actif' AND u.statut = 'actif') AS nb_encadreurs,
    (SELECT count(DISTINCT a.eleve_id) FROM adhesion a
        JOIN utilisateur u ON u.id = a.eleve_id
     WHERE a.club_id = c.id AND a.etat = 'active' AND u.statut = 'actif') AS nb_eleves
FROM club c WHERE c.etat IN {VIVANTS}
"""

RECALCUL = f"""
WITH eff AS ({EFFECTIFS}), calcul AS (
    SELECT id, etat AS ancien, nouveau, nb_encadreurs, nb_eleves,
        CASE WHEN nb_encadreurs >= {SEUIL_ENCADREURS} AND nb_eleves >= {SEUIL_ELEVES}
             THEN 'actif' ELSE 'en_constitution' END AS statut
    FROM eff
), journal AS (
    INSERT INTO club_statut (id, club_id, ancien, nouveau, cause, nb_encadreurs, nb_eleves)
    SELECT gen_random_uuid(), id, CASE WHEN nouveau THEN NULL ELSE ancien END, statut, 'migration', nb_encadreurs,
        nb_eleves
    FROM calcul
)
UPDATE club c SET etat = calcul.statut,
    actif_le = CASE WHEN calcul.statut = 'actif' THEN coalesce(c.actif_le, now()) ELSE c.actif_le END
FROM calcul WHERE c.id = calcul.id
"""


def _creer_clubs() -> None:
    connexion = op.get_bind()
    for etablissement_id, nom in connexion.execute(sa.text(ETABLISSEMENTS_SANS_CLUB)).all():
        nom_club = f"Club Santé — {nom}"[:150]
        connexion.execute(
            sa.text(
                "INSERT INTO club (id, etablissement_id, nom, nom_normalise, etat) "
                "VALUES (:id, :etablissement_id, :nom, :nom_normalise, 'en_constitution')"
            ),
            {
                "id": uuid.uuid7(),
                "etablissement_id": etablissement_id,
                "nom": nom_club,
                "nom_normalise": _normaliser(nom_club)[:150],
            },
        )


def upgrade() -> None:
    # Régions des DRE ; une DRE inconnue fait échouer la migration plutôt que d'être rangée au hasard.
    op.add_column("dre", sa.Column("region", sa.String(length=20), nullable=True))
    op.execute(REGION_DES_DRE)
    op.alter_column("dre", "region", nullable=False)
    op.create_check_constraint(op.f("ck_dre_region"), "dre", f"region IN ({_liste(REGIONS)})")

    # Club : statuts, échéance, déclaration sur le terrain.
    op.drop_constraint(op.f("ck_club_etat_club"), "club", type_="check")
    op.create_check_constraint(op.f("ck_club_etat_club"), "club", f"etat IN ({_liste(ETATS_CLUB)})")
    op.drop_index("uq_club_actif_par_etablissement", table_name="club")
    op.drop_constraint(op.f("uq_club_etablissement_id_nom_normalise"), "club", type_="unique")
    op.alter_column("club", "demandeur_id", nullable=True)
    op.alter_column("club", "etat", server_default="en_constitution")
    op.add_column("club", sa.Column("regularisation_jusquau", sa.DateTime(timezone=True), nullable=True))
    op.add_column("club", sa.Column("rappels_envoyes", sa.SmallInteger(), server_default=sa.text("0"), nullable=False))
    op.add_column("club", sa.Column("declare_terrain", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("club", sa.Column("declare_note", sa.String(length=300), nullable=True))
    op.add_column("club", sa.Column("declare_le", sa.DateTime(timezone=True), nullable=True))
    op.add_column("club", sa.Column("declare_par", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_club_declare_par_utilisateur"), "club", "utilisateur", ["declare_par"], ["id"], ondelete="SET NULL"
    )
    op.create_check_constraint(
        op.f("ck_club_echeance_si_regularisation"),
        "club",
        "(etat = 'en_regularisation') = (regularisation_jusquau IS NOT NULL)",
    )
    op.execute(DEMANDES_EN_TROP)
    op.execute("UPDATE club SET etat = 'en_constitution' WHERE etat = 'en_attente'")
    op.create_index(
        "uq_club_par_etablissement",
        "club",
        ["etablissement_id"],
        unique=True,
        postgresql_where=sa.text(f"etat IN {VIVANTS}"),
    )

    op.create_table(
        "club_statut",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("club_id", sa.Uuid(), nullable=False),
        sa.Column("ancien", sa.String(length=20), nullable=True),
        sa.Column("nouveau", sa.String(length=20), nullable=False),
        sa.Column("cause", sa.String(length=40), nullable=False),
        sa.Column("nb_encadreurs", sa.SmallInteger(), nullable=False),
        sa.Column("nb_eleves", sa.Integer(), nullable=False),
        sa.Column("par", sa.Uuid(), nullable=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(f"ancien IN ({_liste(ETATS_CLUB)})", name=op.f("ck_club_statut_etat_club_ancien")),
        sa.CheckConstraint(f"nouveau IN ({_liste(ETATS_CLUB)})", name=op.f("ck_club_statut_etat_club_nouveau")),
        sa.ForeignKeyConstraint(["club_id"], ["club.id"], name=op.f("fk_club_statut_club_id_club"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["par"], ["utilisateur.id"], name=op.f("fk_club_statut_par_utilisateur"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_club_statut")),
    )
    op.create_index("ix_club_statut_club_id_cree_le", "club_statut", ["club_id", "cree_le"])

    op.create_table(
        "signalement_desistement",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("club_id", sa.Uuid(), nullable=False),
        sa.Column("encadreur_id", sa.Uuid(), nullable=False),
        sa.Column("signale_par", sa.Uuid(), nullable=True),
        sa.Column("motif", sa.String(length=500), nullable=False),
        sa.Column("signale_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("etat", sa.String(length=20), server_default="en_attente", nullable=False),
        sa.Column("decide_par", sa.Uuid(), nullable=True),
        sa.Column("decide_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motif_decision", sa.String(length=500), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modifie_le", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "etat IN ('en_attente', 'confirme', 'rejete')", name=op.f("ck_signalement_desistement_etat_signalement")
        ),
        sa.CheckConstraint("signale_par <> encadreur_id", name=op.f("ck_signalement_desistement_pas_soi_meme")),
        sa.CheckConstraint(
            "(etat = 'en_attente') = (decide_le IS NULL)", name=op.f("ck_signalement_desistement_decision_datee")
        ),
        sa.CheckConstraint(
            "(etat = 'rejete') = (motif_decision IS NOT NULL)", name=op.f("ck_signalement_desistement_motif_si_rejete")
        ),
        sa.ForeignKeyConstraint(
            ["club_id"], ["club.id"], name=op.f("fk_signalement_desistement_club_id_club"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["encadreur_id"],
            ["utilisateur.id"],
            name=op.f("fk_signalement_desistement_encadreur_id_utilisateur"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["signale_par"],
            ["utilisateur.id"],
            name=op.f("fk_signalement_desistement_signale_par_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decide_par"],
            ["utilisateur.id"],
            name=op.f("fk_signalement_desistement_decide_par_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_signalement_desistement")),
    )
    op.create_index(op.f("ix_signalement_desistement_club_id"), "signalement_desistement", ["club_id"])
    op.create_index("ix_signalement_desistement_etat", "signalement_desistement", ["etat"])
    op.create_index(
        "uq_signalement_en_attente",
        "signalement_desistement",
        ["club_id", "encadreur_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'en_attente'"),
    )

    # Reprise des membres.
    _creer_clubs()
    op.drop_column("rattachement", "supplementaire")
    op.execute(RATTACHEMENTS_EN_ATTENTE)
    op.execute(RATTACHEMENTS_AILLEURS)
    op.execute(RATTACHEMENTS_MANQUANTS)
    op.create_index(
        "uq_rattachement_actif_par_encadreur",
        "rattachement",
        ["encadreur_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'actif'"),
    )
    op.execute("UPDATE adhesion SET etat = 'en_attente_validation' WHERE etat = 'en_attente_president'")
    op.execute(ADHESIONS_AILLEURS)
    op.execute(ADHESIONS_MANQUANTES)
    op.execute(RECALCUL)


def downgrade() -> None:
    # Descente volontairement incomplète : les rattachements et adhésions clos à la montée ne sont pas rouverts, et
    # les clubs créés par le système sont effacés avec leurs membres (échoue si un contenu les référence).
    op.drop_index("uq_rattachement_actif_par_encadreur", table_name="rattachement")
    op.add_column(
        "rattachement", sa.Column("supplementaire", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )
    op.drop_table("signalement_desistement")
    op.drop_table("club_statut")
    op.execute("DELETE FROM club WHERE demandeur_id IS NULL")
    op.execute("UPDATE club SET etat = 'actif' WHERE etat IN ('en_regularisation', 'suspendu')")
    op.execute("UPDATE club SET etat = 'en_attente' WHERE etat = 'en_constitution'")
    op.drop_index("uq_club_par_etablissement", table_name="club")
    op.create_index(
        "uq_club_actif_par_etablissement",
        "club",
        ["etablissement_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'actif'"),
    )
    op.create_unique_constraint(
        op.f("uq_club_etablissement_id_nom_normalise"), "club", ["etablissement_id", "nom_normalise"]
    )
    op.drop_constraint(op.f("ck_club_echeance_si_regularisation"), "club", type_="check")
    op.drop_constraint(op.f("fk_club_declare_par_utilisateur"), "club", type_="foreignkey")
    for colonne in ("declare_par", "declare_le", "declare_note", "declare_terrain", "rappels_envoyes"):
        op.drop_column("club", colonne)
    op.drop_column("club", "regularisation_jusquau")
    op.alter_column("club", "etat", server_default="en_attente")
    op.alter_column("club", "demandeur_id", nullable=False)
    op.drop_constraint(op.f("ck_club_etat_club"), "club", type_="check")
    op.create_check_constraint(op.f("ck_club_etat_club"), "club", "etat IN ('en_attente', 'actif', 'refuse')")
    op.drop_constraint(op.f("ck_dre_region"), "dre", type_="check")
    op.drop_column("dre", "region")
