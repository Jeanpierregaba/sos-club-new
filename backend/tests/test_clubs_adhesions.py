"""Affiliations des élèves (spec 020, tâche 2) : demande de l'élève, confirmation ou refus du président,
annulation et retraits, président membre de droit. La validation par un collaborateur est en tâche 4."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.clubs.models import Adhesion, EtatAdhesion, EtatClub
from app.comptes.models import Utilisateur
from tests.conftest import MOT_DE_PASSE

pytestmark = pytest.mark.usefixtures("annuaire")


def connecter(client: TestClient, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


@pytest.fixture
def president(creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    return creer_eleve("president", "Le Président")


@pytest.fixture
def club(president: Utilisateur, creer_club: Callable[..., Any]) -> Any:
    return creer_club(president)


@pytest.fixture
def eleve(creer_eleve: Callable[..., Utilisateur], club: Any) -> Utilisateur:
    """Un élève du même établissement que le club."""
    return creer_eleve("kofi", "Kofi du Golfe", etablissement_id=club.etablissement_id)


def adhesion_de(en_base: Callable[..., Any], eleve: Utilisateur) -> Adhesion:
    return en_base(
        lambda db: db.scalar(
            select(Adhesion).where(Adhesion.eleve_id == eleve.id).order_by(Adhesion.demande_le.desc()).limit(1)
        )
    )


def membre(en_base: Callable[..., Any], eleve: Utilisateur, club: Any) -> Adhesion:
    async def inserer(db: AsyncSession) -> Adhesion:
        adhesion = Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.active)
        db.add(adhesion)
        return adhesion

    return en_base(inserer)


def demander(client: TestClient, club: Any) -> Any:
    return client.post(f"/api/clubs/{club.id}/adhesions")


def demande_en_attente(client: TestClient, club: Any, eleve: Utilisateur) -> dict[str, Any]:
    connecter(client, eleve.identifiant)
    reponse = demander(client, club)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


# Demande de l'élève -----------------------------------------------------------------------------------------


def test_un_eleve_demande_a_rejoindre_le_club_de_son_etablissement(
    client: TestClient, club: Any, eleve: Utilisateur
) -> None:
    connecter(client, "kofi")

    reponse = demander(client, club)

    assert reponse.status_code == 201
    assert reponse.json()["etat"] == "en_attente_president"
    assert reponse.json()["club_nom"] == club.nom


def test_un_eleve_dun_autre_etablissement_ne_peut_pas_demander(
    client: TestClient, club: Any, creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve("lointain", "Élève de Kara", dre="kara")
    connecter(client, "lointain")

    assert demander(client, club).status_code == 403


def test_un_club_qui_nest_pas_actif_ne_recoit_pas_de_demande(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]
) -> None:
    demandeur = creer_eleve("demandeur", "Le Demandeur")
    en_attente = creer_club(demandeur, etat=EtatClub.en_attente)
    creer_eleve("kofi", "Kofi", etablissement_id=en_attente.etablissement_id)
    connecter(client, "kofi")

    assert demander(client, en_attente).status_code == 404


def test_une_seconde_demande_est_refusee(client: TestClient, club: Any, eleve: Utilisateur) -> None:
    demande_en_attente(client, club, eleve)

    reponse = demander(client, club)

    assert reponse.status_code == 409
    assert "déjà" in reponse.json()["detail"]


def test_le_president_est_deja_membre(client: TestClient, club: Any, president: Utilisateur) -> None:
    connecter(client, "president")

    reponse = demander(client, club)

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Tu es déjà membre de ce club."


def test_un_encadreur_ne_demande_pas_une_affiliation(
    client: TestClient, club: Any, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    creer_encadreur("prof")
    connecter(client, "prof")

    assert demander(client, club).status_code == 403


# Confirmation par le président (écrite avant le code, spec 020) ---------------------------------------------


def test_le_president_voit_les_demandes_a_confirmer(client: TestClient, club: Any, eleve: Utilisateur) -> None:
    demande_en_attente(client, club, eleve)
    connecter(client, "president")

    reponse = client.get(f"/api/clubs/{club.id}/adhesions/demandes")

    assert reponse.status_code == 200
    assert [d["pseudonyme"] for d in reponse.json()] == ["Kofi du Golfe"]


def test_le_president_confirme_et_la_demande_attend_le_collaborateur(
    client: TestClient, club: Any, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    demande = demande_en_attente(client, club, eleve)
    connecter(client, "president")

    reponse = client.post(
        f"/api/clubs/{club.id}/adhesions/{demande['id']}/confirmer", json={"version": demande["version"]}
    )

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "en_attente_validation"
    adhesion = adhesion_de(en_base, eleve)
    assert adhesion.confirme_par == club.president_id
    assert adhesion.confirme_le is not None
    journal = en_base(lambda db: db.scalar(select(JournalAudit).where(JournalAudit.action == "adhesion_confirmee")))
    assert journal is not None


def test_une_confirmation_sur_une_version_perimee_est_refusee(
    client: TestClient, club: Any, eleve: Utilisateur
) -> None:
    demande = demande_en_attente(client, club, eleve)
    connecter(client, "president")
    url = f"/api/clubs/{club.id}/adhesions/{demande['id']}/confirmer"
    assert client.post(url, json={"version": demande["version"]}).status_code == 200

    # Le second onglet du président a encore l'ancienne version : la demande a déjà été traitée.
    assert client.post(url, json={"version": demande["version"]}).status_code == 409


def test_seul_le_president_confirme(
    client: TestClient,
    club: Any,
    eleve: Utilisateur,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    demande = demande_en_attente(client, club, eleve)
    autre = creer_eleve("ama", "Ama", etablissement_id=club.etablissement_id)
    membre(en_base, autre, club)
    connecter(client, "ama")

    reponse = client.post(
        f"/api/clubs/{club.id}/adhesions/{demande['id']}/confirmer", json={"version": demande["version"]}
    )

    assert reponse.status_code == 403
    assert client.get(f"/api/clubs/{club.id}/adhesions/demandes").status_code == 403


def test_une_demande_dun_autre_club_est_introuvable_pour_ce_president(
    client: TestClient,
    club: Any,
    eleve: Utilisateur,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
) -> None:
    demande = demande_en_attente(client, club, eleve)
    autre_president = creer_eleve("autre.president", "Autre Président", dre="kara")
    autre_club = creer_club(autre_president, nom="Club de Kara")
    connecter(client, "autre.president")

    reponse = client.post(
        f"/api/clubs/{autre_club.id}/adhesions/{demande['id']}/confirmer", json={"version": demande["version"]}
    )

    assert reponse.status_code == 404


# Refus par le président -------------------------------------------------------------------------------------


def test_un_refus_sans_motif_est_rejete(client: TestClient, club: Any, eleve: Utilisateur) -> None:
    demande = demande_en_attente(client, club, eleve)
    connecter(client, "president")

    reponse = client.post(
        f"/api/clubs/{club.id}/adhesions/{demande['id']}/refuser", json={"motif": "", "version": demande["version"]}
    )

    assert reponse.status_code == 422


def test_un_refus_avec_motif_est_lu_par_leleve_qui_peut_redemander(
    client: TestClient, club: Any, eleve: Utilisateur
) -> None:
    demande = demande_en_attente(client, club, eleve)
    connecter(client, "president")
    reponse = client.post(
        f"/api/clubs/{club.id}/adhesions/{demande['id']}/refuser",
        json={"motif": "Tu n'es pas inscrit dans notre lycée.", "version": demande["version"]},
    )
    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "refusee"

    connecter(client, "kofi")
    espace = client.get("/api/eleves/moi").json()
    assert espace["adhesion"]["etat"] == "refusee"
    assert espace["adhesion"]["motif_refus"] == "Tu n'es pas inscrit dans notre lycée."
    assert demander(client, club).status_code == 201


# Annulation et retraits -------------------------------------------------------------------------------------


def test_leleve_annule_sa_demande(client: TestClient, club: Any, eleve: Utilisateur) -> None:
    demande_en_attente(client, club, eleve)

    reponse = client.delete(f"/api/clubs/{club.id}/adhesions/moi")

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "retiree"


def test_un_membre_se_retire_lui_meme(
    client: TestClient, club: Any, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    membre(en_base, eleve, club)
    connecter(client, "kofi")

    reponse = client.delete(f"/api/clubs/{club.id}/adhesions/moi")

    assert reponse.status_code == 200
    adhesion = adhesion_de(en_base, eleve)
    assert adhesion.etat is EtatAdhesion.retiree
    assert adhesion.retire_par == eleve.id


def test_sans_adhesion_il_ny_a_rien_a_retirer(client: TestClient, club: Any, eleve: Utilisateur) -> None:
    connecter(client, "kofi")

    assert client.delete(f"/api/clubs/{club.id}/adhesions/moi").status_code == 404


def test_le_president_ne_peut_pas_se_retirer(client: TestClient, club: Any, president: Utilisateur) -> None:
    connecter(client, "president")

    reponse = client.delete(f"/api/clubs/{club.id}/adhesions/moi")

    assert reponse.status_code == 409
    assert "passation" in reponse.json()["detail"]


def test_le_president_retire_un_membre_avec_un_motif(
    client: TestClient, club: Any, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    adhesion = membre(en_base, eleve, club)
    connecter(client, "president")

    reponse = client.post(
        f"/api/clubs/{club.id}/adhesions/{adhesion.id}/retirer",
        json={"motif": "A quitté l'établissement.", "version": adhesion.version},
    )

    assert reponse.status_code == 200
    retiree = adhesion_de(en_base, eleve)
    assert retiree.etat is EtatAdhesion.retiree
    assert retiree.motif_retrait == "A quitté l'établissement."
    assert retiree.retire_par == club.president_id


def test_le_president_ne_peut_pas_etre_retire(
    client: TestClient, club: Any, president: Utilisateur, en_base: Callable[..., Any]
) -> None:
    adhesion = adhesion_de(en_base, president)
    connecter(client, "president")

    reponse = client.post(f"/api/clubs/{club.id}/adhesions/{adhesion.id}/retirer", json={"version": adhesion.version})

    assert reponse.status_code == 409


# Président membre de droit ---------------------------------------------------------------------------------


def test_lactivation_dun_club_rend_son_president_membre(
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    demandeur = creer_eleve("demandeur", "La Demandeuse")
    demande = creer_club(demandeur, etat=EtatClub.en_attente)

    reponse = verificateur_clubs.post(f"/api/admin/clubs/{demande.id}/activer", json={"version": demande.version})

    assert reponse.status_code == 200, reponse.text
    adhesion = adhesion_de(en_base, demandeur)
    assert adhesion.etat is EtatAdhesion.active
    assert adhesion.club_id == demande.id
