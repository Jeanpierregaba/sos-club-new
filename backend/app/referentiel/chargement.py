"""Chargement initial du référentiel depuis l'annuaire du site (spec 016, Q28).

Appelé par la migration `referentiel` et par les tests. Il peut être relancé sans créer de doublon. Il travaille
sur des tables SQLAlchemy Core qui ne listent que les colonnes de la migration : une évolution future des modèles
ne casse pas une migration déjà passée.
"""

import json
from pathlib import Path
from typing import Any
from uuid import uuid7

from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, Uuid, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from app.referentiel.normalisation import normaliser
from app.referentiel.regions import REGION_PAR_DRE

FICHIER = Path(__file__).resolve().parents[2] / "alembic" / "donnees" / "annuaire.json"

_meta = MetaData()
_dre = Table(
    "dre", _meta, Column("code", String), Column("nom", String), Column("nom_normalise", String),
    Column("nom_complet", String), Column("region", String), Column("ordre", Integer), Column("actif", Boolean),
    Column("version", Integer),
)  # fmt: skip
_iesg = Table(
    "iesg", _meta, Column("id", Uuid), Column("dre_code", String), Column("nom", String),
    Column("nom_normalise", String), Column("zone", String), Column("actif", Boolean), Column("version", Integer),
)  # fmt: skip
_etablissement = Table(
    "etablissement", _meta, Column("id", Uuid), Column("iesg_id", Uuid), Column("nom", String),
    Column("nom_normalise", String), Column("type", String), Column("statut", String), Column("version", Integer),
)  # fmt: skip
_axe = Table(
    "axe", _meta, Column("code", String), Column("libelle", String), Column("libelle_normalise", String),
    Column("description", String), Column("ordre", Integer), Column("actif", Boolean), Column("version", Integer),
)  # fmt: skip


def lire_annuaire() -> dict[str, list[dict[str, Any]]]:
    return json.loads(FICHIER.read_text(encoding="utf-8"))


def charger(connexion: Connection, *, etablissements: bool = True) -> None:
    """DRE, IESG et axes, puis les établissements si demandé. Les doublons de l'annuaire, même nom dans la même
    IESG, ne sont chargés qu'une fois."""
    annuaire = lire_annuaire()

    connexion.execute(
        insert(_dre)
        .values(
            [
                d
                | {
                    "nom_normalise": normaliser(d["nom"]),
                    "region": REGION_PAR_DRE[d["code"]].value,
                    "actif": True,
                    "version": 1,
                }
                for d in annuaire["dre"]
            ]
        )
        .on_conflict_do_nothing()
    )
    connexion.execute(
        insert(_iesg)
        .values(
            [
                {
                    "id": uuid7(),
                    "dre_code": i["dre"],
                    "nom": i["nom"],
                    "nom_normalise": normaliser(i["nom"]),
                    "zone": i["zone"],
                    "actif": True,
                    "version": 1,
                }
                for i in annuaire["iesg"]
            ]
        )
        .on_conflict_do_nothing()
    )
    connexion.execute(
        insert(_axe)
        .values(
            [a | {"libelle_normalise": normaliser(a["libelle"]), "actif": True, "version": 1} for a in annuaire["axes"]]
        )
        .on_conflict_do_nothing()
    )
    if not etablissements:
        return

    # Les IESG ont un nom unique dans tout l'annuaire : il suffit à retrouver leur identifiant.
    ids = {nom: id_ for id_, nom in connexion.execute(select(_iesg.c.id, _iesg.c.nom))}
    lignes: dict[tuple[Any, str], dict[str, Any]] = {}
    for e in annuaire["etablissements"]:
        cle = (ids[e["iesg"]], normaliser(e["nom"]))
        lignes.setdefault(
            cle,
            {
                "id": uuid7(),
                "iesg_id": cle[0],
                "nom": e["nom"],
                "nom_normalise": cle[1],
                "type": e["type"],
                "statut": "actif",
                "version": 1,
            },
        )
    connexion.execute(insert(_etablissement).values(list(lignes.values())).on_conflict_do_nothing())
