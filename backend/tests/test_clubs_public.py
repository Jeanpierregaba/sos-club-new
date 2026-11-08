"""Lecture publique des clubs (spec 019, tâche 5) : clubs actifs seulement, fiche minimale, aucun nominatif."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Club, ClubAxe, EtatClub
from app.comptes.models import Utilisateur
from tests.conftest import etablissement_de


def club(
    en_base: Callable[..., Any],
    utilisateur: Utilisateur,
    *,
    nom: str = "Club Santé de Tokoin",
    etat: EtatClub = EtatClub.actif,
    dre: str = "grand-lome",
) -> Club:
    lieu = etablissement_de(en_base, dre)

    async def inserer(db: AsyncSession) -> Club:
        element = Club(
            etablissement_id=lieu,
            nom=nom,
            nom_normalise=nom.lower(),
            demandeur_id=utilisateur.id,
            president_id=utilisateur.id if etat is EtatClub.actif else None,
            etat=etat,
            motif_refus="Motif" if etat is EtatClub.refuse else None,
        )
        db.add(element)
        await db.flush()
        db.add(ClubAxe(club_id=element.id, axe_code="sante-environnement"))
        return element

    return en_base(inserer)


def test_la_liste_ne_montre_que_les_clubs_actifs(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    actif = club(en_base, eleve)
    club(en_base, eleve, nom="Club en attente", etat=EtatClub.en_attente)
    club(en_base, eleve, nom="Club refusé", etat=EtatClub.refuse)

    liste = client.get("/api/clubs").json()

    assert [c["id"] for c in liste] == [str(actif.id)]
    assert liste[0]["etablissement"]["dre_code"] == "grand-lome"


def test_la_fiche_publique_est_minimale_et_sans_nominatif(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    actif = club(en_base, eleve)

    reponse = client.get(f"/api/clubs/{actif.id}")

    assert reponse.status_code == 200
    fiche = reponse.json()
    assert set(fiche) == {"id", "nom", "description", "etablissement", "axes", "actif_le", "actualites"}
    assert fiche["nom"] == "Club Santé de Tokoin"
    assert fiche["axes"] == ["sante-environnement"]
    texte = reponse.text
    assert "Kodjo" not in texte
    assert "Ama du Golfe" not in texte
    assert "eleve1" not in texte


def test_un_club_en_attente_ou_refuse_est_introuvable_en_public(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    attente = club(en_base, eleve, nom="Club en attente", etat=EtatClub.en_attente)
    refuse = club(en_base, eleve, nom="Club refusé", etat=EtatClub.refuse)

    assert client.get(f"/api/clubs/{attente.id}").status_code == 404
    assert client.get(f"/api/clubs/{refuse.id}").status_code == 404
    assert client.get("/api/clubs/00000000-0000-7000-8000-000000000000").status_code == 404


def test_le_club_dun_etablissement_se_lit_par_son_identifiant(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    actif = club(en_base, eleve)
    vide = UUID("00000000-0000-7000-8000-000000000000")

    trouve = client.get("/api/clubs/par-etablissement", params={"etablissement_id": actif.etablissement_id})
    absent = client.get("/api/clubs/par-etablissement", params={"etablissement_id": vide})

    assert trouve.status_code == 200
    assert trouve.json()["id"] == str(actif.id)
    assert absent.status_code == 204
    assert absent.content == b""


def test_la_carte_sans_club_rend_une_liste_vide(client: TestClient) -> None:
    assert client.get("/api/clubs").json() == []
