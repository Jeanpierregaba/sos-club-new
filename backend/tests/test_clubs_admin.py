"""Admin existant (spec 019, tâche 10) : le club d'un élève apparaît dans sa fiche, avec son état et s'il le
préside ; le seed de démonstration prépare un club actif et une demande en attente."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Club, ClubAxe, EtatClub
from app.comptes.models import Utilisateur
from app.seed_dev import semer
from tests.conftest import VERIFICATION_CLUBS, connecter_admin, etablissement_de

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def admin_inscrits(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("verif.inscrits", droits=VERIFICATION_CLUBS | {("inscrits", "consulter")}, double_auth=True)
    connecter_admin(client, "verif.inscrits")
    return client


def club(
    en_base: Callable[..., Any],
    utilisateur: Utilisateur,
    *,
    etat: EtatClub = EtatClub.en_attente,
    nom: str = "Club Santé de Tokoin",
) -> Club:
    lieu = etablissement_de(en_base, "grand-lome")

    async def inserer(db: AsyncSession) -> Club:
        element = Club(
            etablissement_id=lieu,
            nom=nom,
            nom_normalise=nom.lower(),
            demandeur_id=utilisateur.id,
            president_id=utilisateur.id if etat is EtatClub.actif else None,
            etat=etat,
            motif_refus="Motif" if etat is EtatClub.refuse else None,
            actif_le=datetime.now(UTC) if etat is EtatClub.actif else None,
        )
        db.add(element)
        await db.flush()
        db.add(ClubAxe(club_id=element.id, axe_code="sante-environnement"))
        return element

    return en_base(inserer)


def test_la_fiche_dun_eleve_montre_sa_demande_et_son_etat(
    admin_inscrits: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    club(en_base, eleve)

    fiche = admin_inscrits.get(f"/api/admin/inscrits/{eleve.id}").json()

    assert fiche["eleve"]["club"] == {
        "id": fiche["eleve"]["club"]["id"],
        "nom": "Club Santé de Tokoin",
        "etat": "en_attente",
        "president": False,
        "motif_refus": None,
    }


def test_la_fiche_dun_president_indique_quil_preside(
    admin_inscrits: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    club(en_base, eleve, etat=EtatClub.actif)

    fiche = admin_inscrits.get(f"/api/admin/inscrits/{eleve.id}").json()

    assert fiche["eleve"]["club"]["etat"] == "actif"
    assert fiche["eleve"]["club"]["president"] is True


def test_un_eleve_sans_club_na_pas_de_bloc_club(
    admin_inscrits: TestClient, creer_eleve: Callable[..., Utilisateur]
) -> None:
    eleve = creer_eleve("eleve1")

    assert admin_inscrits.get(f"/api/admin/inscrits/{eleve.id}").json()["eleve"]["club"] is None


def test_le_seed_cree_un_club_actif_et_une_demande_en_attente(client: TestClient, en_base: Callable[..., Any]) -> None:
    en_base(semer)
    en_base(semer)

    async def compter(db: AsyncSession) -> tuple[int, int]:
        actifs = await db.scalar(select(func.count()).select_from(Club).where(Club.etat == EtatClub.actif))
        attente = await db.scalar(select(func.count()).select_from(Club).where(Club.etat == EtatClub.en_attente))
        return (actifs or 0, attente or 0)

    assert en_base(compter) == (1, 1)
    (actif,) = client.get("/api/clubs").json()
    assert actif["nom"] == "Club Santé Tokoin"
    assert actif["axes"] == ["sante-environnement", "sport-secourisme"]
