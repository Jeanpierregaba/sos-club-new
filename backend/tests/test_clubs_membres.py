"""Liste des membres et changements d'établissement (spec 020, tâche 5)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from tests.conftest import MOT_DE_PASSE, VERIFICATION_CLUBS, connecter_admin, etablissement_de

pytestmark = pytest.mark.usefixtures("annuaire")


def connecter(client: TestClient, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


@pytest.fixture
def club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    return creer_club(creer_eleve("president", "Zoé la Présidente"))


def adhesion(en_base: Callable[..., Any], eleve: Utilisateur, club: Any, etat: EtatAdhesion) -> Adhesion:
    async def inserer(db: AsyncSession) -> Adhesion:
        ligne = Adhesion(eleve_id=eleve.id, club_id=club.id, etat=etat)
        db.add(ligne)
        return ligne

    return en_base(inserer)


def rattacher(en_base: Callable[..., Any], encadreur: Utilisateur, club: Any) -> Rattachement:
    async def inserer(db: AsyncSession) -> Rattachement:
        ligne = Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=EtatRattachement.actif)
        db.add(ligne)
        return ligne

    return en_base(inserer)


@pytest.fixture
def avec_membres(club: Any, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]) -> Any:
    """Le club, avec un membre actif (Ama) et une demande en attente (Kofi)."""
    adhesion(en_base, creer_eleve("ama", "Ama", etablissement_id=club.etablissement_id), club, EtatAdhesion.active)
    adhesion(
        en_base,
        creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id),
        club,
        EtatAdhesion.en_attente_validation,
    )
    return club


# Liste des membres ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("identifiant", ["president", "ama"])
def test_le_president_et_les_membres_voient_la_liste(client: TestClient, avec_membres: Any, identifiant: str) -> None:
    connecter(client, identifiant)

    reponse = client.get(f"/api/clubs/{avec_membres.id}/membres")

    assert reponse.status_code == 200
    membres = reponse.json()["membres"]
    assert [(m["pseudonyme"], m["president"]) for m in membres] == [("Zoé la Présidente", True), ("Ama", False)]
    # Le pseudonyme seulement : ni nom, ni classe.
    assert set(membres[0]) == {"id", "pseudonyme", "depuis", "president", "version"}


def test_un_encadreur_rattache_voit_la_liste(
    client: TestClient, avec_membres: Any, creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    rattacher(en_base, creer_encadreur("prof"), avec_membres)
    connecter(client, "prof")

    reponse = client.get(f"/api/clubs/{avec_membres.id}/membres")

    assert reponse.status_code == 200
    assert [(e["prenom"], e["fonction"]) for e in reponse.json()["encadreurs"]] == [("Jean", "enseignant")]


@pytest.mark.parametrize("identifiant", ["kofi", "voisin", "prof.libre"])
def test_les_autres_ne_voient_pas_la_liste(
    client: TestClient,
    avec_membres: Any,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    identifiant: str,
) -> None:
    # Kofi n'est pas encore validé ; le voisin est du même établissement sans être membre ; le professeur
    # n'est pas rattaché.
    creer_eleve("voisin", "Voisin", etablissement_id=avec_membres.etablissement_id)
    creer_encadreur("prof.libre")
    connecter(client, identifiant)

    assert client.get(f"/api/clubs/{avec_membres.id}/membres").status_code == 404


def test_sans_connexion_la_liste_est_refusee(client: TestClient, avec_membres: Any) -> None:
    assert client.get(f"/api/clubs/{avec_membres.id}/membres").status_code == 401


def test_un_collaborateur_voit_la_liste_dans_son_perimetre_seulement(
    client: TestClient, avec_membres: Any, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("dre.kara", droits=VERIFICATION_CLUBS, perimetre_dre="kara", double_auth=True)
    creer_collaborateur("dre.lome", droits=VERIFICATION_CLUBS, perimetre_dre="grand-lome", double_auth=True)
    url = f"/api/admin/clubs/{avec_membres.id}/membres"

    connecter_admin(client, "dre.kara")
    assert client.get(url).status_code == 404
    connecter_admin(client, "dre.lome")
    assert [m["pseudonyme"] for m in client.get(url).json()["membres"]] == ["Zoé la Présidente", "Ama"]


# Changements d'établissement --------------------------------------------------------------------------------


def changer_detablissement(client: TestClient, chemin: str, etablissement_id: Any) -> Any:
    version = client.get(chemin).json()["version"]
    return client.patch(chemin, json={"version": version, "etablissement_id": str(etablissement_id)})


def test_un_membre_qui_change_detablissement_quitte_le_club(
    client: TestClient, avec_membres: Any, en_base: Callable[..., Any]
) -> None:
    """Spec 033 : l'ancienne affiliation prend fin, une nouvelle s'ouvre « à confirmer » dans le club du nouvel
    établissement."""
    connecter(client, "ama")
    savanes = etablissement_de(en_base, "savanes")

    reponse = changer_detablissement(client, "/api/eleves/moi", savanes)

    assert reponse.status_code == 200, reponse.text
    lignes = en_base(
        lambda db: db.execute(
            select(Adhesion.club_id, Adhesion.etat, Adhesion.motif_retrait)
            .join(Utilisateur, Utilisateur.id == Adhesion.eleve_id)
            .where(Utilisateur.identifiant == "ama")
        )
    ).all()
    anciennes = [ligne for ligne in lignes if ligne.club_id == avec_membres.id]
    nouvelles = [ligne for ligne in lignes if ligne.club_id != avec_membres.id]
    assert [(a.etat, a.motif_retrait) for a in anciennes] == [(EtatAdhesion.retiree, "Changement d'établissement.")]
    assert [a.etat for a in nouvelles] == [EtatAdhesion.en_attente_validation]
    nouveau_club = en_base(lambda db: db.get(Club, nouvelles[0].club_id))
    assert nouveau_club.etablissement_id == savanes


def test_un_president_ne_change_pas_detablissement_avant_une_passation(
    client: TestClient, club: Any, en_base: Callable[..., Any]
) -> None:
    connecter(client, "president")

    reponse = changer_detablissement(client, "/api/eleves/moi", etablissement_de(en_base, "savanes"))

    assert reponse.status_code == 409
    assert "passation" in reponse.json()["detail"]
    president = en_base(lambda db: db.get(Eleve, club.president_id))
    assert president.etablissement_id == club.etablissement_id


def test_un_encadreur_qui_change_detablissement_suit_son_etablissement(
    client: TestClient,
    club: Any,
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    """Spec 033 : un seul club par encadreur ; son rattachement suit l'établissement de son profil."""
    prof = creer_encadreur("prof", etablissement_id=club.etablissement_id)
    local = rattacher(en_base, prof, club)
    savanes = etablissement_de(en_base, "savanes")
    connecter(client, "prof")

    reponse = changer_detablissement(client, "/api/encadreurs/moi", savanes)

    assert reponse.status_code == 200, reponse.text
    lignes = en_base(
        lambda db: db.execute(
            select(Rattachement.id, Rattachement.etat, Club.etablissement_id)
            .join(Club, Club.id == Rattachement.club_id)
            .where(Rattachement.encadreur_id == prof.id)
        )
    ).all()
    assert {(ligne.id == local.id, ligne.etat, ligne.etablissement_id) for ligne in lignes} == {
        (True, EtatRattachement.retire, club.etablissement_id),
        (False, EtatRattachement.actif, savanes),
    }
