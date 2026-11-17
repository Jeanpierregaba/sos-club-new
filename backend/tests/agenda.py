"""Aides communes aux tests de l'agenda (spec 041)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.agenda.models import Evenement
from app.comptes.models import Utilisateur
from app.notifications.models import Notification
from tests.conftest import Navigateur, connecter_admin
from tests.espace_club import adherer, connecter
from tests.test_classements import rattacher

CLUB = "/api/clubs/moi/agenda"
FILE = "/api/admin/moderation"
MODERATION = {("tableau_de_bord", "consulter"), ("moderation", "consulter"), ("moderation", "approuver"),
              ("moderation", "depublier")}  # fmt: skip
AGENDA = {("agenda", "approuver"), ("agenda", "depublier")}


def plus_tard(jours: int = 7, heure: int = 9) -> datetime:
    """Une heure de Lomé, sans fuseau, comme le formulaire la saisit."""
    jour = (datetime.now(UTC) + timedelta(days=jours)).date()
    return datetime(jour.year, jour.month, jour.day, heure, 30)


def champs(**changements: Any) -> dict[str, Any]:
    debut = plus_tard()
    donnees = {
        "titre": "Causerie sur le paludisme",
        "type": "sensibilisation",
        "axe_code": "sante-environnement",
        "objectif": "Apprendre à installer une moustiquaire.",
        "description": "Une causerie dans la cour, avec démonstration et questions.",
        "lieu": "Cour du lycée",
        "en_ligne": False,
        "public_vise": "Élèves de 2nde",
        "debut": debut.isoformat(timespec="minutes"),
        "fin": (debut + timedelta(hours=2)).isoformat(timespec="minutes"),
        "places": None,
    }
    return {**donnees, **changements}


@pytest.fixture
def club(
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    """Un club en service : sa présidente (membre), deux encadreurs, deux membres et un élève non affilié ; un autre
    club avec son encadreur et sa présidente."""
    presidente = creer_eleve("presidente", "Ama")
    club = creer_club(presidente, nom="Club Santé Tokoin")
    prof = creer_encadreur("prof", etablissement_id=club.etablissement_id)
    collegue = creer_encadreur("collegue", etablissement_id=club.etablissement_id)
    for encadreur in (prof, collegue):
        rattacher(en_base, encadreur.id, club.id)
    membre = creer_eleve("membre", "Kossi")
    membre2 = creer_eleve("membre2", "Afi")
    for eleve in (membre, membre2):
        adherer(en_base, eleve, club)
    simple = creer_eleve("simple", "Yao")
    ailleurs = creer_encadreur("ailleurs", dre="maritime")
    autre_presidente = creer_eleve("autre-presidente", "Abla", dre="maritime")
    autre = creer_club(autre_presidente, nom="Club Santé Aného")
    rattacher(en_base, ailleurs.id, autre.id)
    return {
        "club": club, "presidente": presidente, "prof": prof, "collegue": collegue, "membre": membre,
        "membre2": membre2, "simple": simple, "ailleurs": ailleurs, "autre": autre,
        "autre_presidente": autre_presidente,
    }  # fmt: skip


def brouillon(navigateur: Navigateur, **changements: Any) -> dict[str, Any]:
    reponse = navigateur.post(CLUB, json=champs(**changements))
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def soumettre(navigateur: Navigateur, evenement: dict[str, Any]) -> Any:
    return navigateur.post(f"{CLUB}/{evenement['id']}/soumettre", json={"version": evenement["version"]})


def propose(navigateur: Navigateur, **changements: Any) -> dict[str, Any]:
    reponse = soumettre(navigateur, brouillon(navigateur, **changements))
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def moderateur(
    client: TestClient, creer_collaborateur: Callable[..., Any], identifiant: str = "agenda", droits: Any = None
) -> Navigateur:
    creer_collaborateur(identifiant, droits=MODERATION | AGENDA if droits is None else droits, double_auth=True)
    navigateur = Navigateur(client)
    assert connecter_admin(navigateur, identifiant).status_code == 200
    return navigateur


def decider(navigateur: Navigateur, contenu_id: str, decision: str, motif: str | None = None) -> Any:
    version = navigateur.get(f"{FILE}/{contenu_id}").json()["version"]
    corps: dict[str, Any] = {"version": version}
    if motif is not None:
        corps["motif"] = motif
    return navigateur.post(f"{FILE}/{contenu_id}/{decision}", json=corps)


def publie(
    client: TestClient, creer_collaborateur: Callable[..., Any], auteur: str = "prof", **changements: Any
) -> dict:
    """Un événement proposé par `auteur` et approuvé par l'équipe."""
    evenement = propose(connecter(client, auteur), **changements)
    equipe = moderateur(client, creer_collaborateur, f"equipe-{evenement['id'][-12:]}")
    reponse = decider(equipe, evenement["id"], "approuver")
    assert reponse.status_code == 200, reponse.text
    return evenement


def notifications(en_base: Callable[..., Any], qui: Utilisateur, type: str | None = None) -> list[Notification]:
    requete = select(Notification).where(Notification.utilisateur_id == qui.id).order_by(Notification.cree_le)
    if type is not None:
        requete = requete.where(Notification.type == type)
    return list(en_base(lambda db: db.scalars(requete)).all())


def ligne(en_base: Callable[..., Any], evenement_id: str | UUID) -> Evenement | None:
    return en_base(lambda db: db.get(Evenement, UUID(str(evenement_id))))


__all__ = ["club", "connecter"]
