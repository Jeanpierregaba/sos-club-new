"""annuaire national du secondaire I

Spec 035 : les 2 396 établissements du Secondaire I de la liste nationale (2026). Chaque établissement porte sa
préfecture et son ordre d'enseignement. Un établissement déjà présent sous le même nom normalisé dans la même IESG
n'est pas recréé : il reçoit préfecture et ordre, garde son nom, son statut et ses membres. De même pour un
établissement seul de son nom dans la même DRE mais sous une autre IESG (le fichier range sous Mango ce que
l'annuaire place sous Grand Kpendjal). Les autres sont créés,
actifs, marqués `import_source` pour que le retour arrière ne retire qu'eux.

Revision ID: d6d0ef005da8
Revises: 56e0b6a25e70
Create Date: 2026-11-12

"""

import json
import unicodedata
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid7

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from alembic import op

revision: str = "d6d0ef005da8"
down_revision: str | Sequence[str] | None = "56e0b6a25e70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FICHIER = Path(__file__).resolve().parents[1] / "donnees" / "etablissements_secondaire_1.json"
SOURCE = "secondaire-1-2026"
ORDRES = ("public", "prive_laic", "prive_catholique", "prive_protestant", "prive_islamique", "communautaire")
LOT = 500

_meta = sa.MetaData()
_etablissement = sa.Table(
    "etablissement", _meta, sa.Column("id", sa.Uuid), sa.Column("iesg_id", sa.Uuid), sa.Column("nom", sa.String),
    sa.Column("nom_normalise", sa.String), sa.Column("type", sa.String), sa.Column("statut", sa.String),
    sa.Column("version", sa.Integer), sa.Column("prefecture", sa.String), sa.Column("ordre", sa.String),
    sa.Column("import_source", sa.String),
)  # fmt: skip


def normaliser(texte: str) -> str:
    """Copie figée de `app.referentiel.normalisation.normaliser` : une évolution du code ne change pas un rejeu."""
    decompose = unicodedata.normalize("NFKD", texte.replace("’", "'").replace("‐", "-"))
    sans_accents = "".join(c for c in decompose if not unicodedata.combining(c))
    return " ".join(sans_accents.casefold().split())


def upgrade() -> None:
    op.add_column("etablissement", sa.Column("prefecture", sa.String(length=100), nullable=True))
    op.add_column(
        "etablissement",
        sa.Column(
            "ordre",
            sa.Enum(*ORDRES, name="ordre_enseignement", native_enum=False, create_constraint=True, length=20),
            nullable=True,
        ),
    )
    op.add_column("etablissement", sa.Column("import_source", sa.String(length=40), nullable=True))
    op.create_index(op.f("ix_etablissement_prefecture"), "etablissement", ["prefecture"], unique=False)
    op.create_index(op.f("ix_etablissement_import_source"), "etablissement", ["import_source"], unique=False)

    connexion = op.get_bind()
    iesg = {
        nom: (id_, dre) for id_, nom, dre in connexion.execute(sa.text("SELECT id, nom_normalise, dre_code FROM iesg"))
    }
    if not iesg:
        raise RuntimeError("Aucune IESG en base : le référentiel doit être chargé avant la liste du Secondaire I.")
    dans_l_iesg: set[tuple[object, str]] = set()
    dans_la_dre: defaultdict[tuple[str, str], list[object]] = defaultdict(list)
    for id_, iesg_id, nom, dre in connexion.execute(
        sa.text(
            "SELECT e.id, e.iesg_id, e.nom_normalise, i.dre_code FROM etablissement e JOIN iesg i ON i.id = e.iesg_id"
        )
    ):
        dans_l_iesg.add((iesg_id, nom))
        dans_la_dre[(dre, nom)].append(id_)

    lignes, ailleurs = [], []
    for e in json.loads(FICHIER.read_text(encoding="utf-8")):
        cible = iesg.get(normaliser(e["iesg"]))
        if cible is None:
            raise RuntimeError(f"IESG inconnue dans la liste du Secondaire I : {e['iesg']}")
        iesg_id, dre = cible
        nom = normaliser(e["nom"])
        homonymes = dans_la_dre.get((dre, nom), [])
        if (iesg_id, nom) not in dans_l_iesg and len(homonymes) == 1:
            # Déjà là sous une autre IESG de la même DRE : on le complète, on ne le duplique pas.
            ailleurs.append({"cible": homonymes[0], "prefecture": e["prefecture"], "ordre": e["ordre"]})
            continue
        lignes.append(
            {
                "id": uuid7(), "iesg_id": iesg_id, "nom": e["nom"], "nom_normalise": nom, "type": e["type"],
                "statut": "actif", "version": 1, "prefecture": e["prefecture"], "ordre": e["ordre"],
                "import_source": SOURCE,
            }
        )  # fmt: skip
    for debut in range(0, len(lignes), LOT):
        requete = insert(_etablissement).values(lignes[debut : debut + LOT])
        connexion.execute(
            requete.on_conflict_do_update(
                index_elements=["iesg_id", "nom_normalise"],
                # Déjà présent : préfecture et ordre seulement ; ni le nom, ni le statut, ni l'origine.
                set_={"prefecture": requete.excluded.prefecture, "ordre": requete.excluded.ordre},
            )
        )
    if ailleurs:
        connexion.execute(
            sa.text("UPDATE etablissement SET prefecture = :prefecture, ordre = :ordre WHERE id = :cible"), ailleurs
        )


def downgrade() -> None:
    connexion = op.get_bind()
    utilises = connexion.execute(
        sa.text(
            "SELECT count(*) FROM etablissement e WHERE e.import_source = :source AND ("
            " EXISTS (SELECT 1 FROM club c WHERE c.etablissement_id = e.id)"
            " OR EXISTS (SELECT 1 FROM eleve l WHERE l.etablissement_id = e.id)"
            " OR EXISTS (SELECT 1 FROM encadreur n WHERE n.etablissement_id = e.id))"
        ).bindparams(source=SOURCE)
    ).scalar()
    if utilises:
        raise RuntimeError(
            f"Retour impossible : {utilises} établissement(s) importé(s) ont déjà un club, un élève ou un encadreur."
        )
    connexion.execute(sa.text("DELETE FROM etablissement WHERE import_source = :source").bindparams(source=SOURCE))
    op.drop_index(op.f("ix_etablissement_import_source"), table_name="etablissement")
    op.drop_index(op.f("ix_etablissement_prefecture"), table_name="etablissement")
    op.drop_column("etablissement", "import_source")
    op.drop_column("etablissement", "ordre")
    op.drop_column("etablissement", "prefecture")
