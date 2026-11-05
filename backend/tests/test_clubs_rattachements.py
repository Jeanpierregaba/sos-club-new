"""Rattachements des encadreurs (spec 020, tâche 3) : demande, décision du président, retraits, club
supplémentaire. La validation par un collaborateur est en tâche 4."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import EtatRattachement, Rattachement
from app.comptes.models import Utilisateur
from app.encadreurs.models import EtatVerification
from tests.conftest import MOT_DE_PASSE

pytestmark = pytest.mark.usefixtures("annuaire")


def connecter(client: TestClient, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


@pytest.fixture
def club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    return creer_club(creer_eleve("president", "Le Président"))


@pytest.fixture
def autre_club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    return creer_club(creer_eleve("president.kara", "Présidente de Kara", dre="kara"), nom="Club de Kara")


@pytest.fixture
def encadreur(creer_encadreur: Callable[..., Utilisateur], club: Any) -> Utilisateur:
    return creer_encadreur("prof", etablissement_id=club.etablissement_id)


def rattacher(en_base: Callable[..., Any], encadreur: Utilisateur, club: Any) -> Rattachement:
    async def inserer(db: AsyncSession) -> Rattachement:
        rattachement = Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=EtatRattachement.actif)
        db.add(rattachement)
        return rattachement

    return en_base(inserer)


def demande(client: TestClient, club: Any) -> dict[str, Any]:
    connecter(client, "prof")
    reponse = client.post(f"/api/clubs/{club.id}/rattachements")
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def test_un_encadreur_demande_son_premier_rattachement(client: TestClient, club: Any, encadreur: Utilisateur) -> None:
    corps = demande(client, club)

    assert corps["etat"] == "en_attente_president"
    assert corps["supplementaire"] is False


def test_un_second_club_est_marque_supplementaire(
    client: TestClient, club: Any, autre_club: Any, encadreur: Utilisateur, en_base: Callable[..., Any]
) -> None:
    rattacher(en_base, encadreur, club)

    corps = demande(client, autre_club)

    assert corps["supplementaire"] is True


def test_un_encadreur_non_actif_ne_demande_pas(
    client: TestClient, club: Any, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    creer_encadreur("prof", etablissement_id=club.etablissement_id, etat=EtatVerification.en_attente)
    connecter(client, "prof")

    assert client.post(f"/api/clubs/{club.id}/rattachements").status_code == 403


def test_un_eleve_ne_demande_pas_de_rattachement(
    client: TestClient, club: Any, creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id)
    connecter(client, "kofi")

    assert client.post(f"/api/clubs/{club.id}/rattachements").status_code == 403


def test_une_seconde_demande_ou_un_club_deja_encadre_est_refuse(
    client: TestClient, club: Any, autre_club: Any, encadreur: Utilisateur, en_base: Callable[..., Any]
) -> None:
    demande(client, club)
    assert client.post(f"/api/clubs/{club.id}/rattachements").status_code == 409

    rattacher(en_base, encadreur, autre_club)
    reponse = client.post(f"/api/clubs/{autre_club.id}/rattachements")
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Tu es déjà rattaché à ce club."


def test_le_president_voit_lencadreur_et_confirme(client: TestClient, club: Any, encadreur: Utilisateur) -> None:
    corps = demande(client, club)
    connecter(client, "president")

    demandes = client.get(f"/api/clubs/{club.id}/rattachements/demandes").json()
    reponse = client.post(
        f"/api/clubs/{club.id}/rattachements/{corps['id']}/confirmer", json={"version": corps["version"]}
    )

    assert [(d["prenom"], d["fonction"]) for d in demandes] == [("Jean", "enseignant")]
    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "en_attente_validation"


def test_le_president_refuse_avec_un_motif(client: TestClient, club: Any, encadreur: Utilisateur) -> None:
    corps = demande(client, club)
    connecter(client, "president")
    url = f"/api/clubs/{club.id}/rattachements/{corps['id']}/refuser"

    assert client.post(url, json={"motif": "", "version": corps["version"]}).status_code == 422
    reponse = client.post(url, json={"motif": "Nous ne vous connaissons pas.", "version": corps["version"]})

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "refuse"
    assert reponse.json()["motif_refus"] == "Nous ne vous connaissons pas."


def test_seul_le_president_decide(
    client: TestClient, club: Any, encadreur: Utilisateur, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    corps = demande(client, club)
    # Un autre encadreur, même rattaché, ne décide pas à la place du président.
    connecter(client, "prof")

    reponse = client.post(
        f"/api/clubs/{club.id}/rattachements/{corps['id']}/confirmer", json={"version": corps["version"]}
    )

    assert reponse.status_code == 403


def test_lencadreur_quitte_un_club(
    client: TestClient, club: Any, encadreur: Utilisateur, en_base: Callable[..., Any]
) -> None:
    rattacher(en_base, encadreur, club)
    connecter(client, "prof")

    reponse = client.delete(f"/api/clubs/{club.id}/rattachements/moi")

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "retire"


def test_le_president_retire_un_encadreur_qui_peut_redemander(
    client: TestClient, club: Any, encadreur: Utilisateur, en_base: Callable[..., Any]
) -> None:
    rattachement = rattacher(en_base, encadreur, club)
    connecter(client, "president")

    reponse = client.post(
        f"/api/clubs/{club.id}/rattachements/{rattachement.id}/retirer",
        json={"motif": "Muté dans un autre lycée.", "version": rattachement.version},
    )

    assert reponse.status_code == 200
    retire = en_base(lambda db: db.get(Rattachement, rattachement.id))
    assert retire.etat is EtatRattachement.retire
    assert retire.motif_retrait == "Muté dans un autre lycée."
    assert demande(client, club)["etat"] == "en_attente_president"


def test_mes_clubs_liste_les_rattachements_en_cours_puis_termines(
    client: TestClient, club: Any, autre_club: Any, encadreur: Utilisateur, en_base: Callable[..., Any]
) -> None:
    rattacher(en_base, encadreur, club)

    async def ancien(db: AsyncSession) -> None:
        db.add(
            Rattachement(
                encadreur_id=encadreur.id,
                club_id=autre_club.id,
                etat=EtatRattachement.refuse,
                motif_refus="Hors périmètre.",
            )
        )

    en_base(ancien)
    connecter(client, "prof")

    reponse = client.get("/api/encadreurs/moi/clubs")

    assert reponse.status_code == 200
    assert [(r["club_nom"], r["etat"]) for r in reponse.json()["rattachements"]] == [
        (club.nom, "actif"),
        ("Club de Kara", "refuse"),
    ]


def test_mes_clubs_est_reserve_aux_encadreurs(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> None:
    creer_eleve("kofi", "Kofi")
    connecter(client, "kofi")

    assert client.get("/api/encadreurs/moi/clubs").status_code == 403


def test_les_rattachements_sont_journalises(
    client: TestClient, club: Any, encadreur: Utilisateur, en_base: Callable[..., Any]
) -> None:
    from app.admin.models import JournalAudit

    demande(client, club)

    actions = en_base(
        lambda db: db.scalars(select(JournalAudit.action).where(JournalAudit.action.like("rattachement_%")))
    ).all()
    assert actions == ["rattachement_demande"]
