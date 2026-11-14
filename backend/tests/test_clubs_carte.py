"""Carte nationale publique (spec 033) : trois chiffres réels sans double compte, arbre par région, aucune donnée
personnelle."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import func, select, update

from app.clubs.models import Club, EtatClub
from app.referentiel.models import Etablissement, StatutEtablissement
from tests.activation import ajouter_eleves, club_id_de, peupler, recalculer
from tests.conftest import etablissement_de

CARTE = "/api/clubs/carte"

pytestmark = pytest.mark.usefixtures("annuaire")


def etablissements(en_base: Callable[..., Any]) -> int:
    return en_base(
        lambda db: db.scalar(
            select(func.count()).select_from(Etablissement).where(Etablissement.statut == StatutEtablissement.actif)
        )
    )


def statut_de(carte: dict[str, Any], etablissement_id: UUID) -> str:
    for region in carte["regions"]:
        for dre in region["dres"]:
            for iesg in dre["iesg"]:
                for etablissement in iesg["etablissements"]:
                    if etablissement["id"] == str(etablissement_id):
                        return etablissement["statut"]
    raise AssertionError("établissement absent")


def test_sans_club_la_carte_montre_des_zeros_et_tous_les_etablissements(
    client: Any, en_base: Callable[..., Any]
) -> None:
    carte = client.get(CARTE).json()

    assert carte["chiffres"] == {"etablissements": etablissements(en_base), "clubs": 0, "clubs_actifs": 0}
    assert [r["code"] for r in carte["regions"]] == ["maritime", "plateaux", "centrale", "kara", "savanes"]
    maritime = carte["regions"][0]
    assert {d["code"] for d in maritime["dres"]} == {"grand-lome", "maritime"}


def test_trois_chiffres_distincts_sans_double_compte(client: Any, en_base: Callable[..., Any]) -> None:
    actif = etablissement_de(en_base, "grand-lome")
    effectif = peupler(en_base, actif, 3, 21)
    recalculer(en_base, effectif.club_id)
    # Un second recalcul, une seconde affiliation : toujours un seul club.
    ajouter_eleves(en_base, actif, 1)
    recalculer(en_base, effectif.club_id)
    en_constitution = etablissement_de(en_base, "kara")
    peupler(en_base, en_constitution, 1, 2)
    declare = etablissement_de(en_base, "savanes")
    club_declare = club_id_de(en_base, declare)
    en_base(lambda db: db.execute(update(Club).where(Club.id == club_declare).values(declare_terrain=True)))
    suspendu = etablissement_de(en_base, "centrale")
    club_suspendu = club_id_de(en_base, suspendu)
    en_base(lambda db: db.execute(update(Club).where(Club.id == club_suspendu).values(etat=EtatClub.suspendu)))

    carte = client.get(CARTE).json()

    assert carte["chiffres"] == {"etablissements": etablissements(en_base), "clubs": 3, "clubs_actifs": 1}
    assert statut_de(carte, actif) == "actif"
    assert statut_de(carte, en_constitution) == "en_constitution"
    assert statut_de(carte, declare) == "en_constitution"
    assert statut_de(carte, suspendu) == "suspendu"
    maritime = carte["regions"][0]
    assert (maritime["nb_clubs"], maritime["nb_actifs"]) == (1, 1)


def test_la_carte_ne_contient_aucune_donnee_personnelle(client: Any, en_base: Callable[..., Any]) -> None:
    etab = etablissement_de(en_base, "grand-lome")
    effectif = peupler(en_base, etab, 3, 21)
    recalculer(en_base, effectif.club_id)

    texte = client.get(CARTE).text

    for interdit in ("pseudonyme", "prenom", "email", "telephone", "Test", "nb_eleves", "president"):
        assert interdit not in texte
