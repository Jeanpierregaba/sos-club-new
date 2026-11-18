"""Détection des doublons probables (spec 042), sans base : les vraies paires de l'analyse du 2026-11-18 sont
trouvées, les établissements distincts (numéros, groupes, annexes, points cardinaux) ne le sont pas."""

from uuid import uuid7

import pytest

from app.referentiel.doublons import Fiche, Raison, paires

GOLFE, AGOE, DAPAONG, MANGO, KPENDJAL, TSEVIE, KARA, NIAMTOUGOU, BASSAR, ANIE = (
    "golfe", "agoe", "dapaong", "mango", "kpendjal", "tsevie", "kara", "niamtougou", "bassar", "anie",
)  # fmt: skip
DRE = {
    GOLFE: "grand-lome", AGOE: "grand-lome", DAPAONG: "savanes", MANGO: "savanes", KPENDJAL: "savanes",
    TSEVIE: "maritime", KARA: "kara", NIAMTOUGOU: "kara", BASSAR: "kara", ANIE: "plateaux-est",
}  # fmt: skip


def fiche(nom: str, iesg: str, dre: str | None = None) -> Fiche:
    return Fiche(id=uuid7(), nom=nom, iesg_id=iesg, dre_code=dre or DRE[iesg])


@pytest.mark.parametrize(
    ("premier", "second", "raison"),
    [
        (("Lycée de Tokoin I", GOLFE), ("Lycée Tokoin I", GOLFE), Raison.meme_nom),
        (("CEG Bogou 2", DAPAONG), ("CEG Bogou II", DAPAONG), Raison.meme_nom),
        (("Lycée Kara 1", KARA), ("Lycée Kara I", KARA), Raison.meme_nom),
        (("CEG Solidarité", "aneho", "maritime"), ("CEG La Solidarité", "aneho", "maritime"), Raison.meme_nom),
        (("CEG Sirka Ndjei", KARA), ("CEG Sirka N'Djei", KARA), Raison.meme_nom),
        (("CEG Amégapé Nyamégbé", "adeta", "plateaux-ouest"), ("CEG D'Amegape Nyamegbe", "adeta", "plateaux-ouest"),
         Raison.meme_nom),
        (("CPL Alfred Nobel", GOLFE), ("CPL Alfred Nobel", AGOE), Raison.meme_nom),
        (("CPL CITAPA", "kpalime", "plateaux-ouest"), ("CPI Citapa", "kpalime", "plateaux-ouest"), Raison.meme_nom),
        (("CEG Warkanbou", DAPAONG), ("CEG Warkambou", DAPAONG), Raison.nom_proche),
        (("CEG Dassouté Nank", DAPAONG), ("CEG Dassoute-Nanik", DAPAONG), Raison.nom_proche),
        (("Lycée Koudjoaré", KPENDJAL), ("Lycée Koundjoare", MANGO), Raison.nom_proche),
        (("CEG Malgbangou", KPENDJAL), ("CEG Malgbongou", MANGO), Raison.nom_proche),
        (("Lycée Agbélouvé", TSEVIE), ("Lycée Agbelouve(PC)", TSEVIE), Raison.nom_proche),
        (("CEG Ossakré", NIAMTOUGOU), ("CEG Ossacre", NIAMTOUGOU), Raison.meme_prononciation),
        (("Lycée Sola", KARA), ("Lycée Solla", KARA), Raison.meme_prononciation),
        (("CEG Baka Copé", TSEVIE), ("CEG Baka-Kope", TSEVIE), Raison.meme_prononciation),
    ],
)  # fmt: skip
def test_les_doublons_de_lanalyse_sont_trouves(
    premier: tuple[str, ...], second: tuple[str, ...], raison: Raison
) -> None:
    (paire,) = paires([fiche(*premier), fiche(*second)])

    assert {paire.a.nom, paire.b.nom} == {premier[0], second[0]}
    assert paire.raison is raison


def test_trois_fiches_du_meme_etablissement_donnent_trois_paires() -> None:
    kondokope = [fiche("CEG Kondokopé", TSEVIE), fiche("CEG Kondo Copé", TSEVIE), fiche("CEG Kondocope", TSEVIE)]

    assert len(paires(kondokope)) == 3


@pytest.mark.parametrize(
    "groupe",
    [
        [("CPL La Fabienne I", AGOE), ("CPL La Fabienne III", AGOE), ("CPL La Fabienne M", AGOE),
         ("CPL La Fabienne A", GOLFE)],
        [("CPL Le Souverain G/A", TSEVIE), ("CPL Le Souverain G/B", TSEVIE)],
        [("CEG Bassar Est", BASSAR), ("CEG Bassar Ouest", BASSAR)],
        [("CPI Daroul Hikmah I", AGOE), ("CPI Daroul Hikmah IV", GOLFE), ("CPI Daroul Hikmah 5", AGOE)],
        [("CPL Le Jardin de la Connaissance et de l'Excellence", AGOE),
         ("CPL Le Jardin de la Connaissance et de l'Excellence (Annexe)", AGOE)],
        [("CPL Saint Charbel N°1", AGOE), ("CPL Saint Charbel II", AGOE)],
        [("CPL Bernard B. Dadie", AGOE), ("CPL Bernard B. Dadier II", AGOE)],
        [("Lycée de Tokoin I", GOLFE), ("Lycée de Tokoin II", GOLFE)],
        [("Lycée Tokoin", GOLFE), ("CEG Tokoin", GOLFE)],
    ],
)  # fmt: skip
def test_les_etablissements_distincts_ne_sont_pas_proposes(groupe: list[tuple[str, str]]) -> None:
    assert paires([fiche(*f) for f in groupe]) == []


def test_deux_dre_differentes_ne_forment_jamais_une_paire() -> None:
    assert paires([fiche("CEG Kpodji", "zio", "maritime"), fiche("CEG Kpodji", "kara", "kara")]) == []


def test_une_paire_secrit_dans_un_seul_sens() -> None:
    liste = [fiche("Lycée Tokoin I", GOLFE), fiche("Lycée de Tokoin I", GOLFE)]

    (paire,) = paires(liste)

    assert paire.a.id < paire.b.id
