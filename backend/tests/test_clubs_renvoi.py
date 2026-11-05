"""Renvoi d'une demande refusée (spec 019, tâche 4) : seule une demande refusée repasse en attente ; le motif
précédent reste au journal."""

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.clubs.models import Club, ClubAxe, EtatClub
from app.comptes.models import Utilisateur
from tests.conftest import MOT_DE_PASSE, etablissement_de

RENVOYER = "/api/clubs/demande/renvoyer"


def connecter(client: TestClient, identifiant: str) -> None:
    assert (
        client.post(
            "/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE}
        ).status_code
        == 200
    )


def club_refuse(
    en_base: Callable[..., Any], utilisateur: Utilisateur, *, motif: str = "Encadreur non joignable"
) -> Club:
    lieu = etablissement_de(en_base, "grand-lome")

    async def inserer(db: AsyncSession) -> Club:
        club = Club(
            etablissement_id=lieu,
            nom="Club Santé de Tokoin",
            nom_normalise="club sante de tokoin",
            demandeur_id=utilisateur.id,
            etat=EtatClub.refuse,
            motif_refus=motif,
            decide_le=None,
        )
        db.add(club)
        await db.flush()
        db.add(ClubAxe(club_id=club.id, axe_code="sante-environnement"))
        return club

    return en_base(inserer)


def test_une_demande_refusee_repasse_en_attente_et_le_motif_reste_au_journal(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    club = club_refuse(en_base, eleve)
    connecter(client, "eleve1")

    reponse = client.post(RENVOYER)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "en_attente"
    assert reponse.json()["motif_refus"] is None
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "club_redemande"))
    ).all()
    assert entree.cible_id == str(club.id)
    assert entree.details == {"motif_precedent": "Encadreur non joignable"}


def test_une_demande_en_attente_ne_se_renvoie_pas(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    lieu = etablissement_de(en_base, "grand-lome")

    async def inserer(db: AsyncSession) -> None:
        db.add(
            Club(
                etablissement_id=lieu,
                nom="Club en attente",
                nom_normalise="club en attente",
                demandeur_id=eleve.id,
                etat=EtatClub.en_attente,
            )
        )

    en_base(inserer)
    connecter(client, "eleve1")

    assert client.post(RENVOYER).status_code == 409


def test_un_autre_eleve_ne_renvoie_pas_la_demande(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    titulaire = creer_eleve("eleve1", affiche="Ama du Golfe")
    club_refuse(en_base, titulaire)
    creer_eleve("eleve2", affiche="Kofi Curieux")
    connecter(client, "eleve2")

    assert client.post(RENVOYER).status_code == 409


def test_le_renvoi_est_refuse_si_letablissement_a_maintenant_un_club_actif(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    club_refuse(en_base, eleve)
    autre = creer_eleve("eleve2", affiche="Kofi Curieux")
    lieu = etablissement_de(en_base, "grand-lome")

    async def activer(db: AsyncSession) -> None:
        club = Club(
            etablissement_id=lieu,
            nom="Club actif",
            nom_normalise="club actif",
            demandeur_id=autre.id,
            president_id=autre.id,
            etat=EtatClub.actif,
        )
        db.add(club)

    en_base(activer)
    connecter(client, "eleve1")

    assert client.post(RENVOYER).status_code == 409
