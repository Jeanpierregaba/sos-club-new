"""Listes publiques du référentiel (spec 016) : sans compte, actives seulement, sans champ d'administration."""

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.referentiel.models import Axe, Dre, Etablissement, Iesg, StatutEtablissement

EnBase = Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any]

pytestmark = pytest.mark.usefixtures("annuaire")


def executer(en_base: EnBase, requete: Any) -> None:
    async def lancer(db: AsyncSession) -> None:
        await db.execute(requete)

    en_base(lancer)


def chercher(client: TestClient, **params: str) -> Any:
    return client.get("/api/referentiel/etablissements", params=params)


def test_les_dre_sont_publiques_dans_l_ordre_de_la_carte(client: TestClient) -> None:
    reponse = client.get("/api/referentiel/dre")
    assert reponse.status_code == 200
    dre = reponse.json()
    assert [d["code"] for d in dre] == [
        "savanes", "kara", "centrale", "plateaux-est", "plateaux-ouest", "maritime", "grand-lome"
    ]  # fmt: skip
    grand_lome = dre[-1]
    assert grand_lome["nb_etablissements"] == 47
    assert {i["nom"]: i["nb_etablissements"] for i in grand_lome["iesg"]} == {"IESG Golfe": 29, "IESG Agoényivé": 18}
    assert sum(d["nb_etablissements"] for d in dre) == 838


def test_une_dre_desactivee_n_apparait_pas(client: TestClient, en_base: EnBase) -> None:
    executer(en_base, update(Dre).where(Dre.code == "kara").values(actif=False))
    codes = [d["code"] for d in client.get("/api/referentiel/dre").json()]
    assert "kara" not in codes
    assert "kara" not in [d["code"] for d in client.get("/api/referentiel/annuaire").json()]


def test_aucun_champ_d_administration_dans_les_listes(client: TestClient) -> None:
    dre = client.get("/api/referentiel/dre").json()[0]
    assert set(dre) == {"code", "nom", "nom_complet", "nb_etablissements", "iesg"}
    assert set(dre["iesg"][0]) == {"id", "nom", "zone", "nb_etablissements"}
    trouve = chercher(client, recherche="tokoin").json()[0]
    assert set(trouve) == {"id", "nom", "type", "iesg_id", "iesg", "dre_code", "dre", "localite"}
    axe = client.get("/api/referentiel/axes").json()[0]
    assert set(axe) == {"code", "libelle", "description"}


def test_l_annuaire_contient_les_etablissements_de_chaque_iesg(client: TestClient) -> None:
    annuaire = client.get("/api/referentiel/annuaire").json()
    golfe = next(i for i in annuaire[-1]["iesg"] if i["nom"] == "IESG Golfe")
    assert len(golfe["etablissements"]) == golfe["nb_etablissements"] == 29
    assert {"nom": "Lycée de Tokoin I", "type": "lycee"}.items() <= next(
        e for e in golfe["etablissements"] if e["nom"] == "Lycée de Tokoin I"
    ).items()


def test_la_recherche_ignore_accents_et_majuscules(client: TestClient) -> None:
    reponse = chercher(client, recherche="LYCEE tokoin")
    assert reponse.status_code == 200
    noms = [e["nom"] for e in reponse.json()]
    assert "Lycée de Tokoin I" in noms
    assert all("tokoin" in n.lower() and "lyc" in n.lower() for n in noms)
    assert reponse.json()[0]["dre_code"] == "grand-lome"


def test_la_recherche_renvoie_20_resultats_au_plus(client: TestClient) -> None:
    assert len(chercher(client, recherche="lycee").json()) == 20


def test_la_recherche_se_limite_a_une_dre(client: TestClient) -> None:
    resultats = chercher(client, recherche="lycee", dre="kara").json()
    assert resultats
    assert {e["dre_code"] for e in resultats} == {"kara"}


@pytest.mark.parametrize("params", [{"recherche": "a"}, {"recherche": "  a "}, {"recherche": "\u0301\u0301"}, {}])
def test_une_recherche_trop_courte_ou_absente_est_refusee(client: TestClient, params: dict[str, str]) -> None:
    reponse = chercher(client, **params)
    assert reponse.status_code == 422


def test_les_caracteres_speciaux_ne_servent_pas_de_joker(client: TestClient) -> None:
    assert chercher(client, recherche="%%").json() == []
    assert chercher(client, recherche="__").json() == []


def test_un_etablissement_inactif_n_apparait_nulle_part(client: TestClient, en_base: EnBase) -> None:
    executer(
        en_base,
        update(Etablissement)
        .where(Etablissement.nom == "Lycée de Tokoin I")
        .values(statut=StatutEtablissement.inactif),
    )
    golfe = next(i for i in client.get("/api/referentiel/dre").json()[-1]["iesg"] if i["nom"] == "IESG Golfe")
    assert golfe["nb_etablissements"] == 28
    noms = [e["nom"] for e in chercher(client, iesg=golfe["id"]).json()]
    assert len(noms) == 28
    assert "Lycée de Tokoin I" not in noms
    assert "Lycée de Tokoin I" not in [e["nom"] for e in chercher(client, recherche="tokoin").json()]


def test_un_etablissement_propose_n_apparait_pas(client: TestClient, en_base: EnBase) -> None:
    executer(
        en_base,
        update(Etablissement)
        .where(Etablissement.nom == "Lycée de Tokoin I")
        .values(statut=StatutEtablissement.propose),
    )
    assert "Lycée de Tokoin I" not in [e["nom"] for e in chercher(client, recherche="tokoin").json()]


def test_les_etablissements_d_une_iesg_desactivee_n_apparaissent_pas(client: TestClient, en_base: EnBase) -> None:
    executer(en_base, update(Iesg).where(Iesg.nom == "IESG Golfe").values(actif=False))
    assert chercher(client, recherche="tokoin").json() == []
    grand_lome = client.get("/api/referentiel/dre").json()[-1]
    assert [i["nom"] for i in grand_lome["iesg"]] == ["IESG Agoényivé"]


def test_les_axes_sont_publics_dans_l_ordre(client: TestClient, en_base: EnBase) -> None:
    axes = client.get("/api/referentiel/axes").json()
    assert [a["code"] for a in axes][:2] == ["genie-imhotep", "sante-sexuelle-evss"]
    assert len(axes) == 7
    executer(en_base, update(Axe).where(Axe.code == "bourses-excellence").values(actif=False))
    assert len(client.get("/api/referentiel/axes").json()) == 6
