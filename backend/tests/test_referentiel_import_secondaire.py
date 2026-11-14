"""Conversion de la liste nationale du Secondaire I (spec 035) : casse des noms, type, ordre et IESG."""

import json
from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.referentiel.import_secondaire import FICHIER, casse, convertir, type_de


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("CPL LES BÂTISSEURS", "CPL Les Bâtisseurs"),
        ("CPL LA VOIE DE L'UNIVERSITE", "CPL La Voie de l'Universite"),
        ("CEG DASSOUTE-NANIK", "CEG Dassoute-Nanik"),
        ("LYCEE HANYIGBA", "Lycée Hanyigba"),
        ("CPL NOUVELLE ELITE II", "CPL Nouvelle Élite II"),
        ("CEG N'KPE", "CEG N'Kpe"),
        ("INSTITUT SACRE-COEUR D'AVEPOZO (ISCA)", "Institut Sacre-Coeur d'Avepozo (ISCA)"),
        ("LYCEE AGBELOUVE(PC)", "Lycée Agbelouve(PC)"),
        ("ECOLE INTERNATIONALE Dr BAH-SALAMI", "École Internationale Dr Bah-Salami"),
        ("CPL WINNER'S HOUSE", "CPL Winner's House"),
        ("  CEG   TOULE ", "CEG Toule"),
    ],
)
def test_la_casse_des_noms(brut: str, attendu: str) -> None:
    assert casse(brut) == attendu


@pytest.mark.parametrize(
    ("nom", "type_"),
    [("Lycée Pana", "lycee"), ("LPL La Lumière", "lycee"), ("CS Le Savoir", "complexe"), ("CEG Toule", "college"),
     ("CPL Esperance", "college"), ("Institut Secondaire X", "autre")],
)  # fmt: skip
def test_le_type_se_deduit_du_premier_mot(nom: str, type_: str) -> None:
    assert type_de(nom) == type_


def test_la_conversion_rattache_l_iesg_garde_un_seul_doublon_et_traduit_l_ordre() -> None:
    lignes = [
        ("CEG TOULE", "CENTRALE", "IESG SOTOUBOUA", "BLITTA", "Public"),
        ("CEG TOULÉ", "CENTRALE", "IESG SOTOUBOUA", "BLITTA", "Public"),
        ("CPL ESPOIR", "LOME", "IESG AGOE NYIVE", "AGOE NYIVE", "Privé Laïc"),
    ]

    resultat = convertir(lignes)

    assert resultat == [
        {"iesg": "IESG Sotouboua", "nom": "CEG Toule", "type": "college", "prefecture": "Blitta", "ordre": "public"},
        {"iesg": "IESG Agoényivé", "nom": "CPL Espoir", "type": "college", "prefecture": "Agoè-Nyivé",
         "ordre": "prive_laic"},
    ]  # fmt: skip


def test_une_iesg_ou_un_ordre_inconnus_arretent_la_conversion() -> None:
    with pytest.raises(ValueError, match="IESG inconnue"):
        convertir([("CEG X", "KARA", "IESG INCONNUE", "KOZAH", "Public")])
    with pytest.raises(ValueError, match="Ordre inconnu"):
        convertir([("CEG X", "KARA", "IESG KARA", "KOZAH", "Privé bouddhiste")])
    with pytest.raises(ValueError, match="Préfecture inconnue"):
        convertir([("CEG X", "KARA", "IESG KARA", "ATLANTIS", "Public")])


def test_les_prefectures_prennent_leur_graphie_officielle() -> None:
    lignes = [("CEG A", "SAVANES", "IESG DAPAONG", "TONE", "Public"), ("CEG B", "LOME", "IESG GOLFE", "GOLFE", None)]

    assert [e["prefecture"] for e in convertir(lignes)] == ["Tône", "Golfe"]


# La migration (spec 035) ------------------------------------------------------------------------------------------


def _configuration() -> Any:
    from pathlib import Path

    from alembic.config import Config

    return Config(Path(__file__).resolve().parents[1] / "alembic.ini")


AVANT = "56e0b6a25e70"


def _attendus_crees(liste: list[dict[str, Any]], deja: set[tuple[str, str]]) -> int:
    """Le nombre de lignes que l'import doit créer : ni présentes dans leur IESG, ni seules de leur nom dans la DRE.
    `deja` : les établissements présents avant l'import (IESG normalisée, nom normalisé)."""
    from collections import Counter

    from app.referentiel.chargement import lire_annuaire
    from app.referentiel.normalisation import normaliser

    dre_de = {normaliser(i["nom"]): i["dre"] for i in lire_annuaire()["iesg"]}
    par_dre = Counter((dre_de[i], n) for i, n in deja)
    crees = 0
    for e in liste:
        iesg, nom = normaliser(e["iesg"]), normaliser(e["nom"])
        if (iesg, nom) not in deja and par_dre[(dre_de[iesg], nom)] != 1:
            crees += 1
    return crees


def _etat(en_base: Callable[..., Any], *, importe: bool = True) -> dict[str, Any]:
    """L'annuaire en base ; `importe=False` avant la migration, quand la colonne `import_source` n'existe pas."""
    origine = "e.import_source IS NOT NULL" if importe else "false"

    async def lire(db: AsyncSession) -> dict[str, Any]:
        lignes = (
            await db.execute(
                text(
                    f"SELECT i.nom_normalise, e.nom_normalise, {origine} FROM etablissement e "
                    "JOIN iesg i ON i.id = e.iesg_id"
                )
            )
        ).all()
        return {
            "total": len(lignes),
            "importes": sum(1 for *_, importe in lignes if importe),
            "existants": {(i, n) for i, n, importe in lignes if not importe},
            "doublons": await db.scalar(
                text(
                    "SELECT count(*) FROM (SELECT 1 FROM etablissement GROUP BY iesg_id, nom_normalise "
                    "HAVING count(*) > 1) d"
                )
            ),
        }

    return en_base(lire)


def _ajouter_existant(en_base: Callable[..., Any], statut: str) -> Any:
    async def inserer(db: AsyncSession) -> Any:
        iesg_id = await db.scalar(text("SELECT id FROM iesg WHERE nom_normalise = 'iesg dapaong'"))
        # Déjà là, écrit autrement : même nom normalisé que « CPL Les Bâtisseurs » de la liste.
        return await db.scalar(
            text(
                "INSERT INTO etablissement (id, iesg_id, nom, nom_normalise, type, statut) "
                "VALUES (gen_random_uuid(), :iesg, 'CPL les batisseurs', 'cpl les batisseurs', 'college', :statut) "
                "RETURNING id"
            ).bindparams(iesg=iesg_id, statut=statut)
        )

    return en_base(inserer)


@pytest.mark.parametrize("statut", ["inactif", "propose"])
def test_la_migration_importe_la_liste_sans_dupliquer_ni_renommer_l_existant(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Any], statut: str
) -> None:
    from alembic import command

    liste = json.loads(FICHIER.read_text(encoding="utf-8"))
    command.downgrade(_configuration(), AVANT)
    try:
        ancien_id = _ajouter_existant(en_base, statut)
        avant = _etat(en_base, importe=False)
    finally:
        command.upgrade(_configuration(), "head")

    apres = _etat(en_base)
    assert apres["doublons"] == 0
    assert apres["importes"] == _attendus_crees(liste, avant["existants"])
    assert apres["total"] == avant["total"] + apres["importes"]

    async def lire(db: AsyncSession) -> Any:
        return (
            await db.execute(
                text(
                    "SELECT nom, statut, prefecture, ordre, import_source FROM etablissement WHERE id = :id"
                ).bindparams(id=ancien_id)
            )
        ).one()

    assert tuple(en_base(lire)) == ("CPL les batisseurs", statut, "Tône", "prive_laic", None)


def test_un_etablissement_range_sous_une_autre_iesg_de_la_dre_n_est_pas_duplique(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Any]
) -> None:
    """L'annuaire range « CEG Bagré » sous l'IESG Grand Kpendjal, le fichier sous Mango : il est complété, pas recréé."""
    from alembic import command

    command.downgrade(_configuration(), AVANT)
    command.upgrade(_configuration(), "head")

    async def lire(db: AsyncSession) -> list[Any]:
        return list(
            (
                await db.execute(
                    text(
                        "SELECT i.nom, e.prefecture, e.import_source FROM etablissement e JOIN iesg i ON i.id = e.iesg_id "
                        "WHERE e.nom_normalise = 'ceg bagre'"
                    )
                )
            ).all()
        )

    assert [tuple(ligne) for ligne in en_base(lire)] == [("IESG Grand Kpendjal", "Kpendjal", None)]


def test_le_retour_arriere_ne_retire_que_les_etablissements_importes(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Any]
) -> None:
    from alembic import command

    command.downgrade(_configuration(), AVANT)
    try:
        avant = _etat(en_base, importe=False)
        command.upgrade(_configuration(), "head")
        command.downgrade(_configuration(), AVANT)
        assert _etat(en_base, importe=False) == avant
    finally:
        command.upgrade(_configuration(), "head")


def test_le_retour_arriere_refuse_si_un_etablissement_importe_a_un_membre(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Any]
) -> None:
    from alembic import command

    async def un_importe(db: AsyncSession) -> Any:
        return await db.scalar(
            text("SELECT id FROM etablissement WHERE import_source = 'secondaire-1-2026' ORDER BY nom LIMIT 1")
        )

    # Les tables sont vidées entre les tests : la liste est réimportée par un aller-retour.
    command.downgrade(_configuration(), AVANT)
    command.upgrade(_configuration(), "head")
    creer_eleve("kofi", etablissement_id=en_base(un_importe))

    with pytest.raises(RuntimeError, match="déjà un club, un élève ou un encadreur"):
        command.downgrade(_configuration(), AVANT)
    command.upgrade(_configuration(), "head")


ADMIN = "/api/admin/referentiel/etablissements"


def importe(en_base: Callable[..., Any], nom: str, *, ordre: str = "public", prefecture: str = "Kozah") -> Any:
    """Un établissement comme la migration le crée : dans l'IESG Kara, avec préfecture, ordre et origine."""
    from app.referentiel.models import Etablissement, Iesg, OrdreEnseignement, TypeEtablissement
    from app.referentiel.normalisation import normaliser

    async def inserer(db: AsyncSession) -> Any:
        from sqlalchemy import select

        iesg_id = await db.scalar(select(Iesg.id).where(Iesg.nom_normalise == "iesg kara"))
        etablissement = Etablissement(
            iesg_id=iesg_id, nom=nom, nom_normalise=normaliser(nom), type=TypeEtablissement.college,
            prefecture=prefecture, ordre=OrdreEnseignement(ordre), import_source="secondaire-1-2026",
        )  # fmt: skip
        db.add(etablissement)
        await db.flush()
        return etablissement.id

    return en_base(inserer)


@pytest.fixture
def gestion(client: Any, creer_collaborateur: Callable[..., Any]) -> Any:
    from tests.conftest import connecter_admin

    creer_collaborateur(super_admin=True, double_auth=True)
    connecter_admin(client)
    return client


@pytest.mark.usefixtures("annuaire")
def test_le_back_office_filtre_par_ordre_prefecture_et_origine(gestion: Any, en_base: Callable[..., Any]) -> None:
    importe(en_base, "CPI Al-Houda", ordre="prive_islamique", prefecture="Kozah")
    importe(en_base, "CEG Tchitchao", ordre="public", prefecture="Kozah")
    importe(en_base, "CEG Pya", ordre="public", prefecture="Binah")

    def noms(**filtres: Any) -> list[str]:
        page = gestion.get(ADMIN, params=filtres | {"par_page": 100})
        assert page.status_code == 200, page.text
        return sorted(e["nom"] for e in page.json()["etablissements"])

    assert noms(ordre="prive_islamique") == ["CPI Al-Houda"]
    assert noms(prefecture="Kozah", ordre="public") == ["CEG Tchitchao"]
    assert noms(importes=True) == ["CEG Pya", "CEG Tchitchao", "CPI Al-Houda"]
    assert "CEG Pya" not in noms(importes=False, dre="kara")
    fiche = gestion.get(ADMIN, params={"recherche": "Al-Houda"}).json()["etablissements"][0]
    assert (fiche["ordre"], fiche["prefecture"], fiche["import_source"]) == (
        "prive_islamique",
        "Kozah",
        "secondaire-1-2026",
    )


@pytest.mark.usefixtures("annuaire")
def test_l_equipe_corrige_la_prefecture_et_l_ordre(gestion: Any, en_base: Callable[..., Any]) -> None:
    importe(en_base, "CEG Tchitchao")
    fiche = gestion.get(ADMIN, params={"recherche": "Tchitchao"}).json()["etablissements"][0]

    reponse = gestion.patch(
        f"{ADMIN}/{fiche['id']}", json={"version": fiche["version"], "prefecture": "Assoli", "ordre": "communautaire"}
    )
    assert reponse.status_code == 200, reponse.text
    assert (reponse.json()["prefecture"], reponse.json()["ordre"]) == ("Assoli", "communautaire")

    from sqlalchemy import select

    from app.admin.models import JournalAudit

    entree = en_base(
        lambda db: db.scalar(
            select(JournalAudit).where(JournalAudit.action == "referentiel_modifie").order_by(JournalAudit.quand.desc())
        )
    )
    assert entree is not None and str(entree.cible_id) == fiche["id"]
    assert {"prefecture", "ordre"} <= set(entree.details["apres"])

    effacee = gestion.patch(f"{ADMIN}/{fiche['id']}", json={"version": reponse.json()["version"], "ordre": None})
    assert effacee.json()["ordre"] is None
    assert gestion.patch(f"{ADMIN}/{fiche['id']}", json={"version": 9, "ordre": "inconnu"}).status_code == 422


@pytest.mark.usefixtures("annuaire")
def test_la_recherche_a_l_inscription_trouve_un_college_importe_avec_sa_prefecture(
    client: Any, en_base: Callable[..., Any]
) -> None:
    importe(en_base, "CEG Tchitchao", prefecture="Kozah")

    trouves = client.get("/api/referentiel/etablissements", params={"recherche": "tchitchao"}).json()

    assert ("CEG Tchitchao", "Kozah") in [(e["nom"], e["prefecture"]) for e in trouves]


@pytest.mark.usefixtures("annuaire")
def test_le_club_d_un_college_importe_s_active_au_seuil(en_base: Callable[..., Any]) -> None:
    from app.clubs.models import Club, EtatClub
    from tests.activation import peupler, recalculer

    etablissement_id = importe(en_base, "CEG Tchitchao")
    effectif = peupler(en_base, etablissement_id, 3, 20)
    assert recalculer(en_base, effectif.club_id) is EtatClub.en_constitution
    from tests.activation import ajouter_eleves

    ajouter_eleves(en_base, etablissement_id, 1)

    assert recalculer(en_base, effectif.club_id, "affiliation_confirmee") is EtatClub.actif
    assert en_base(lambda db: db.get(Club, effectif.club_id)).etablissement_id == etablissement_id
