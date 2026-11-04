"""Chargement initial du référentiel depuis l'annuaire du site (spec 016)."""

import asyncio
from collections import Counter

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.referentiel.chargement import charger, lire_annuaire
from app.referentiel.models import Axe, Dre, Etablissement, Iesg, StatutEtablissement
from tests.conftest import moteur_test

DOUBLONS = {"IESG Aného": 5, "IESG Dapaong": 1}


async def _compter() -> list[int | None]:
    async with moteur_test.connect() as connexion:
        return [await connexion.scalar(select(func.count()).select_from(t)) for t in (Dre, Iesg, Etablissement, Axe)]


def test_le_chargement_donne_7_dre_19_iesg_838_etablissements_et_7_axes(annuaire: None) -> None:
    assert asyncio.run(_compter()) == [7, 19, 838, 7]


def test_relancer_le_chargement_ne_cree_aucun_doublon(annuaire: None) -> None:
    async def relancer() -> None:
        async with moteur_test.begin() as connexion:
            await connexion.run_sync(charger)

    asyncio.run(relancer())
    assert asyncio.run(_compter()) == [7, 19, 838, 7]


def test_chaque_iesg_garde_ses_etablissements_moins_les_doublons(annuaire: None) -> None:
    attendus = Counter(e["iesg"] for e in lire_annuaire()["etablissements"])
    for nom, retires in DOUBLONS.items():
        attendus[nom] -= retires

    async def compter_par_iesg() -> dict[str, int]:
        async with moteur_test.connect() as connexion:
            lignes = await connexion.execute(
                select(Iesg.nom, func.count(Etablissement.id)).join(Etablissement).group_by(Iesg.nom)
            )
            return dict(lignes.all())

    assert asyncio.run(compter_par_iesg()) == dict(attendus)


def test_les_etablissements_importes_sont_actifs_dans_la_bonne_dre(annuaire: None) -> None:
    async def verifier() -> tuple[int, str | None]:
        async with moteur_test.connect() as connexion:
            inactifs = await connexion.scalar(
                select(func.count()).select_from(Etablissement).where(Etablissement.statut != StatutEtablissement.actif)
            )
            dre = await connexion.scalar(
                select(Iesg.dre_code).join(Etablissement).where(Etablissement.nom == "Lycée de Tokoin I")
            )
            return inactifs or 0, dre

    assert asyncio.run(verifier()) == (0, "grand-lome")


def test_le_perimetre_d_un_collaborateur_doit_etre_une_dre_du_referentiel() -> None:
    async def inserer(code: str) -> None:
        async with moteur_test.begin() as connexion:
            await connexion.execute(
                text(
                    "INSERT INTO collaborateur (id, email, prenom, nom, perimetre_dre, super_admin) "
                    "VALUES (gen_random_uuid(), :email, 'A', 'B', :code, false)"
                ),
                {"email": f"{code}@exemple.tg", "code": code},
            )

    asyncio.run(inserer("kara"))
    with pytest.raises(IntegrityError, match="fk_collaborateur_perimetre_dre_dre"):
        asyncio.run(inserer("inconnue"))
