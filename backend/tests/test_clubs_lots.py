"""Files et décisions en lot des collaborateurs (spec 020, tâche 4) : périmètre DRE, résultat par élément,
rattachement supplémentaire réservé à l'équipe nationale, compteur du tableau de bord."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Adhesion, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from tests.conftest import VERIFICATION_CLUBS, Navigateur, connecter_admin, etablissement_de

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    """Un club de la DRE Grand Lomé."""
    return creer_club(creer_eleve("president", "Le Président"))


@pytest.fixture
def autre_club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    return creer_club(creer_eleve("president.kara", "Présidente de Kara", dre="kara"), nom="Club de Kara")


def confirmee(en_base: Callable[..., Any], eleve: Utilisateur, club: Any) -> Adhesion:
    """Une affiliation déjà confirmée par le président : elle attend le collaborateur."""

    async def inserer(db: AsyncSession) -> Adhesion:
        adhesion = Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.en_attente_validation)
        db.add(adhesion)
        return adhesion

    return en_base(inserer)


def rattachement(
    en_base: Callable[..., Any],
    encadreur: Utilisateur,
    club: Any,
    etat: EtatRattachement = EtatRattachement.en_attente_validation,
    supplementaire: bool = False,
) -> Rattachement:
    async def inserer(db: AsyncSession) -> Rattachement:
        ligne = Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=etat, supplementaire=supplementaire)
        db.add(ligne)
        return ligne

    return en_base(inserer)


@pytest.fixture
def collaborateur_dre(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Callable[[str], TestClient]:
    """Connecte un collaborateur de la DRE demandée, avec les droits du module clubs."""

    def connecter(dre: str) -> TestClient:
        creer_collaborateur(f"dre.{dre}", droits=VERIFICATION_CLUBS, perimetre_dre=dre, double_auth=True)
        connecter_admin(client, f"dre.{dre}")
        return client

    return connecter


def lot(*lignes: Any) -> dict[str, Any]:
    return {"elements": [{"id": str(ligne.id), "version": ligne.version} for ligne in lignes]}


# Affiliations -----------------------------------------------------------------------------------------------


def test_la_file_ne_montre_que_les_affiliations_du_perimetre(
    collaborateur_dre: Callable[[str], TestClient],
    club: Any,
    autre_club: Any,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    confirmee(en_base, creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id), club)
    confirmee(en_base, creer_eleve("ama", "Ama de Kara", etablissement_id=autre_club.etablissement_id), autre_club)
    client = collaborateur_dre("grand-lome")

    reponse = client.get("/api/admin/clubs/affiliations")

    assert reponse.status_code == 200
    assert reponse.json()["total"] == 1
    assert [d["pseudonyme"] for d in reponse.json()["demandes"]] == ["Kofi"]


def test_un_lot_valide_les_demandes_et_signale_celle_qui_echoue(
    verificateur_clubs: TestClient,
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    kofi = confirmee(en_base, creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id), club)
    ama = confirmee(en_base, creer_eleve("ama", "Ama", etablissement_id=club.etablissement_id), club)
    corps = lot(kofi, ama)
    corps["elements"][1]["version"] = ama.version + 1  # un autre collaborateur est passé par là

    reponse = verificateur_clubs.post("/api/admin/clubs/affiliations/valider", json=corps)

    assert reponse.status_code == 200
    assert reponse.json()["reussies"] == [str(kofi.id)]
    assert [(e["id"], e["message"]) for e in reponse.json()["echecs"]] == [
        (str(ama.id), "Cette demande a déjà été traitée : recharge la page.")
    ]
    assert en_base(lambda db: db.get(Adhesion, kofi.id)).etat is EtatAdhesion.active
    assert en_base(lambda db: db.get(Adhesion, ama.id)).etat is EtatAdhesion.en_attente_validation


def test_une_demande_hors_du_perimetre_est_introuvable(
    collaborateur_dre: Callable[[str], TestClient],
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    kofi = confirmee(en_base, creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id), club)
    client = collaborateur_dre("kara")

    reponse = client.post("/api/admin/clubs/affiliations/valider", json=lot(kofi))

    assert reponse.json() == {
        "reussies": [],
        "echecs": [{"id": str(kofi.id), "message": "Cette demande est introuvable."}],
    }
    assert en_base(lambda db: db.get(Adhesion, kofi.id)).etat is EtatAdhesion.en_attente_validation


def test_un_refus_en_lot_exige_un_motif(
    verificateur_clubs: TestClient,
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    kofi = confirmee(en_base, creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id), club)
    url = "/api/admin/clubs/affiliations/refuser"

    assert verificateur_clubs.post(url, json=lot(kofi)).status_code == 422
    reponse = verificateur_clubs.post(url, json={**lot(kofi), "motif": "Élève inconnu de l'établissement."})

    assert reponse.json()["reussies"] == [str(kofi.id)]
    refusee = en_base(lambda db: db.get(Adhesion, kofi.id))
    assert refusee.etat is EtatAdhesion.refusee
    assert refusee.motif_refus == "Élève inconnu de l'établissement."


def test_un_eleve_qui_a_change_detablissement_nest_pas_valide(
    verificateur_clubs: TestClient,
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    eleve = creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id)
    kofi = confirmee(en_base, eleve, club)
    ailleurs = etablissement_de(en_base, "savanes")

    async def demenager(db: AsyncSession) -> None:
        (await db.get(Eleve, eleve.id)).etablissement_id = ailleurs

    en_base(demenager)

    reponse = verificateur_clubs.post("/api/admin/clubs/affiliations/valider", json=lot(kofi))

    assert reponse.json()["echecs"][0]["message"] == "Cet élève a changé d'établissement depuis sa demande."


def test_il_faut_le_droit_dapprouver_les_clubs(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    kofi = confirmee(en_base, creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id), club)
    creer_collaborateur("lecteur", droits={("tableau_de_bord", "consulter"), ("clubs", "consulter")})
    connecter_admin(client, "lecteur")

    assert client.post("/api/admin/clubs/affiliations/valider", json=lot(kofi)).status_code == 403


# Rattachements ----------------------------------------------------------------------------------------------


def test_un_premier_rattachement_est_valide_par_la_dre(
    collaborateur_dre: Callable[[str], TestClient],
    club: Any,
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    demande = rattachement(en_base, creer_encadreur("prof"), club)
    client = collaborateur_dre("grand-lome")

    file = client.get("/api/admin/clubs/rattachements").json()
    reponse = client.post("/api/admin/clubs/rattachements/valider", json=lot(demande))

    assert file["demandes"][0]["decidable"] is True
    assert reponse.json()["reussies"] == [str(demande.id)]
    assert en_base(lambda db: db.get(Rattachement, demande.id)).etat is EtatRattachement.actif


def test_un_club_supplementaire_exige_lequipe_nationale(
    verificateur_clubs: TestClient,
    creer_collaborateur: Callable[..., Any],
    club: Any,
    autre_club: Any,
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    prof = creer_encadreur("prof")
    rattachement(en_base, prof, autre_club, etat=EtatRattachement.actif)
    demande = rattachement(en_base, prof, club, supplementaire=True)
    # Deux sessions : un collaborateur de la DRE (second navigateur) et l'équipe nationale.
    creer_collaborateur("dre.grand-lome", droits=VERIFICATION_CLUBS, perimetre_dre="grand-lome", double_auth=True)
    dre = Navigateur(verificateur_clubs)
    connecter_admin(dre, "dre.grand-lome")

    file = dre.get("/api/admin/clubs/rattachements").json()
    refus_dre = dre.post("/api/admin/clubs/rattachements/valider", json=lot(demande)).json()
    reponse = verificateur_clubs.post("/api/admin/clubs/rattachements/valider", json=lot(demande))

    assert file["demandes"][0]["decidable"] is False
    assert refus_dre["echecs"][0]["message"].startswith("Autorisation nationale requise")
    assert reponse.json()["reussies"] == [str(demande.id)]


def test_le_caractere_supplementaire_est_recalcule_a_la_decision(
    collaborateur_dre: Callable[[str], TestClient],
    club: Any,
    autre_club: Any,
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    prof = creer_encadreur("prof")
    # Demandé comme premier club, mais un autre rattachement a été validé entre-temps.
    demande = rattachement(en_base, prof, club, supplementaire=False)
    rattachement(en_base, prof, autre_club, etat=EtatRattachement.actif)
    client = collaborateur_dre("grand-lome")

    reponse = client.post("/api/admin/clubs/rattachements/valider", json=lot(demande))

    assert reponse.json()["echecs"][0]["message"].startswith("Autorisation nationale requise")
    assert en_base(lambda db: db.get(Rattachement, demande.id)).etat is EtatRattachement.en_attente_validation


def test_un_refus_de_rattachement_porte_le_motif(
    verificateur_clubs: TestClient, club: Any, creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    demande = rattachement(en_base, creer_encadreur("prof"), club)

    reponse = verificateur_clubs.post(
        "/api/admin/clubs/rattachements/refuser", json={**lot(demande), "motif": "Encadreur inconnu."}
    )

    assert reponse.json()["reussies"] == [str(demande.id)]
    refuse = en_base(lambda db: db.get(Rattachement, demande.id))
    assert refuse.etat is EtatRattachement.refuse
    assert refuse.motif_refus == "Encadreur inconnu."


# Compteur ---------------------------------------------------------------------------------------------------


def test_le_compteur_compte_les_demandes_decidables(
    collaborateur_dre: Callable[[str], TestClient],
    club: Any,
    autre_club: Any,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    confirmee(en_base, creer_eleve("kofi", "Kofi", etablissement_id=club.etablissement_id), club)
    rattachement(en_base, creer_encadreur("prof"), club)
    # Un club supplémentaire ne compte pas pour une DRE : elle ne peut pas le décider.
    rattachement(en_base, creer_encadreur("prof2"), club, supplementaire=True)
    client = collaborateur_dre("grand-lome")

    assert client.get("/api/admin/moi").json()["clubs_a_valider"] == 2
