"""Événements nationaux et régionaux de l'équipe (spec 041) : droits, périmètre DRE, publication immédiate, journal."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from tests.agenda import champs, club, plus_tard, publie
from tests.conftest import Navigateur, connecter_admin

__all__ = ["club"]

pytestmark = pytest.mark.usefixtures("annuaire")

ADMIN = "/api/admin/agenda"
GESTION = {("agenda", "consulter"), ("agenda", "creer"), ("agenda", "modifier")}


def equipe(
    client: TestClient, creer_collaborateur: Callable[..., Any], identifiant: str, droits: Any, dre: str | None = None
) -> Navigateur:
    creer_collaborateur(identifiant, droits=droits, double_auth=True, perimetre_dre=dre)
    navigateur = Navigateur(client)
    assert connecter_admin(navigateur, identifiant).status_code == 200
    return navigateur


def corps(niveau: str = "national", dre_code: str | None = None, **changements: Any) -> dict[str, Any]:
    return {"niveau": niveau, "dre_code": dre_code, "champs": champs(axe_code=None, **changements)}


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return list(en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all())


def test_lequipe_publie_un_evenement_national(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    chef = equipe(client, creer_collaborateur, "chef", GESTION)

    reponse = chef.post(ADMIN, json=corps(titre="Finale nationale Génie Imhotep", type="concours"))

    assert reponse.status_code == 201, reponse.text
    evenement = reponse.json()
    assert (evenement["niveau"], evenement["club"]) == ("national", None)
    client.cookies.clear()
    assert client.get(f"/api/agenda/{evenement['id']}").status_code == 200
    assert [j.cible_id for j in journal(en_base, "evenement_cree")] == [evenement["id"]]


def test_sans_le_droit_de_creer_cest_refuse(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    lecteur = equipe(client, creer_collaborateur, "lecteur", {("agenda", "consulter")})

    assert lecteur.post(ADMIN, json=corps()).status_code == 403


def test_un_collaborateur_de_dre_ne_gere_que_sa_dre(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    regional = equipe(client, creer_collaborateur, "regional", GESTION, dre="grand-lome")

    assert regional.post(ADMIN, json=corps()).status_code == 403
    assert regional.post(ADMIN, json=corps("regional", "maritime")).status_code == 403
    cree = regional.post(ADMIN, json=corps("regional", "grand-lome", titre="Séminaire des encadreurs"))
    assert cree.status_code == 201, cree.text
    chef = equipe(client, creer_collaborateur, "chef", GESTION)
    autre = chef.post(ADMIN, json=corps("regional", "maritime")).json()

    assert regional.put(f"{ADMIN}/{autre['id']}", json=corps("regional", "maritime")).status_code == 404
    assert [e["id"] for e in regional.get(ADMIN).json()] == [cree.json()["id"]]


def test_un_evenement_regional_a_sa_dre_et_un_national_nen_a_pas(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    chef = equipe(client, creer_collaborateur, "chef", GESTION)

    assert chef.post(ADMIN, json=corps("regional", None)).status_code == 422
    assert chef.post(ADMIN, json=corps("national", "maritime")).status_code == 422
    assert chef.post(ADMIN, json=corps("club", None)).status_code == 422


def test_lequipe_reporte_puis_annule_et_cest_journalise(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    chef = equipe(client, creer_collaborateur, "chef", GESTION)
    evenement = chef.post(ADMIN, json=corps()).json()
    debut = plus_tard(jours=20)
    report = corps(
        debut=debut.isoformat(timespec="minutes"), fin=(debut + timedelta(hours=3)).isoformat(timespec="minutes")
    )

    assert chef.put(f"{ADMIN}/{evenement['id']}", json=report).status_code == 200
    annule = chef.post(f"{ADMIN}/{evenement['id']}/annuler", json={"motif": "Salle indisponible ce jour-là"})

    assert annule.status_code == 200, annule.text
    assert annule.json()["annule"] is True
    assert len(journal(en_base, "evenement_modifie")) == 1
    assert len(journal(en_base, "evenement_annule")) == 1


def test_annuler_un_evenement_de_club_exige_le_droit_de_depublier(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)
    chef = equipe(client, creer_collaborateur, "chef", GESTION)
    motif = {"motif": "Annulé à la demande de la DRE"}

    assert chef.post(f"{ADMIN}/{evenement['id']}/annuler", json=motif).status_code == 403
    assert chef.put(f"{ADMIN}/{evenement['id']}", json=corps()).status_code == 409
    gardien = equipe(client, creer_collaborateur, "gardien", GESTION | {("agenda", "depublier")})
    assert gardien.post(f"{ADMIN}/{evenement['id']}/annuler", json=motif).status_code == 200
