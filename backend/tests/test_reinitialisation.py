"""Réinitialisation du mot de passe d'un élève par un encadreur de son club (spec 039, Q4). Partie critique (droits,
comptes), écrite avant le code."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.clubs.models import Adhesion, EtatAdhesion, EtatClub
from app.comptes.inscription import Refus
from app.comptes.models import StatutCompte, Utilisateur
from app.encadreurs.models import Encadreur, EtatVerification
from app.notifications.models import Notification
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin, moteur_test
from tests.espace_club import adherer, connecter
from tests.test_classements import etat_club, rattacher

pytestmark = pytest.mark.usefixtures("annuaire")

MON_CLUB = "/api/clubs/mon-club-sante"
MOTIF = "Mot de passe oublié, demandé en classe."


@pytest.fixture
def club(
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    presidente = creer_eleve("presidente", "Ama")
    club = creer_club(presidente, nom="Club Santé Tokoin")
    prof = creer_encadreur("prof", etablissement_id=club.etablissement_id)
    rattacher(en_base, prof.id, club.id)
    membre = creer_eleve("membre", "Yao")
    adhesion = adherer(en_base, membre, club)
    attente = creer_eleve("attente", "Esi")
    en_attente = adherer(en_base, attente, club, EtatAdhesion.en_attente_validation)
    autre_president = creer_eleve("autre-president", "Kofi", dre="maritime")
    autre = creer_club(autre_president, nom="Club Santé Aného")
    ailleurs = creer_encadreur("ailleurs", dre="maritime")
    rattacher(en_base, ailleurs.id, autre.id)
    return {
        "club": club, "prof": prof, "membre": membre, "adhesion": adhesion, "en_attente": en_attente,
        "presidente": presidente, "ailleurs": ailleurs,
    }  # fmt: skip


def reinitialiser(navigateur: Navigateur, adhesion_id: Any, motif: str = MOTIF) -> Any:
    return navigateur.post(f"{MON_CLUB}/affiliations/{adhesion_id}/mot-de-passe", json={"motif": motif})


def connexion(client: TestClient, identifiant: str, mot_de_passe: str) -> Any:
    return Navigateur(client).post(
        "/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": mot_de_passe}
    )


def journal(en_base: Callable[..., Any]) -> list[JournalAudit]:
    return list(
        en_base(
            lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "mot_de_passe_reinitialise"))
        ).all()
    )


def test_lencadreur_reinitialise_un_membre_confirme(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    eleve = connecter(client, "membre")
    prof = connecter(client, "prof")

    reponse = reinitialiser(prof, club["adhesion"].id)

    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["cache-control"] == "no-store"
    provisoire = reponse.json()["mot_de_passe"]
    assert len(provisoire) == 12
    assert eleve.get("/api/comptes/moi").status_code == 401
    assert connexion(client, "membre", MOT_DE_PASSE).status_code == 401
    nouvelle = connexion(client, "membre", provisoire)
    assert nouvelle.status_code == 200
    assert nouvelle.json()["mot_de_passe_provisoire"] is True

    (entree,) = journal(en_base)
    assert entree.auteur_id == club["prof"].id and entree.cible_id == str(club["membre"].id)
    assert entree.details["motif"] == MOTIF and entree.details["club"] == str(club["club"].id)
    assert provisoire not in str(entree.details)
    (avis,) = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == club["membre"].id))
    ).all()
    prof = club["prof"]
    assert avis.titre == f"Ton mot de passe a été réinitialisé par {prof.prenom} {prof.nom}"
    assert provisoire not in f"{avis.titre}{avis.message}"


def test_changer_son_mot_de_passe_efface_le_marqueur(client: TestClient, club: dict[str, Any]) -> None:
    provisoire = reinitialiser(connecter(client, "prof"), club["adhesion"].id).json()["mot_de_passe"]
    eleve = Navigateur(client)
    eleve.post("/api/comptes/connexion", json={"identifiant": "membre", "mot_de_passe": provisoire})

    reponse = eleve.post("/api/comptes/mot-de-passe", json={"actuel": provisoire, "nouveau": "mon-nouveau-secret"})

    assert reponse.status_code == 204, reponse.text
    assert eleve.get("/api/comptes/moi").json()["mot_de_passe_provisoire"] is False


def test_hors_des_membres_confirmes_le_membre_nexiste_pas(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    prof = connecter(client, "prof")
    assert reinitialiser(prof, club["en_attente"].id).status_code == 404
    assert reinitialiser(connecter(client, "ailleurs"), club["adhesion"].id).status_code == 404

    en_base(
        lambda db: db.execute(
            update(Adhesion).where(Adhesion.id == club["adhesion"].id).values(etat=EtatAdhesion.retiree)
        )
    )
    assert reinitialiser(prof, club["adhesion"].id).status_code == 404
    assert journal(en_base) == []


def test_un_eleve_suspendu_nest_pas_reinitialise(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == club["membre"].id).values(statut=StatutCompte.suspendu)
        )
    )

    assert reinitialiser(connecter(client, "prof"), club["adhesion"].id).status_code == 409


def test_seul_un_encadreur_verifie_dun_club_en_service_reinitialise(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    for qui in ("presidente", "membre"):
        assert reinitialiser(connecter(client, qui), club["adhesion"].id).status_code == 403
    prof = connecter(client, "prof")
    etat_club(en_base, club["club"].id, EtatClub.suspendu)
    assert reinitialiser(prof, club["adhesion"].id).status_code == 403
    etat_club(en_base, club["club"].id, EtatClub.actif)
    en_base(
        lambda db: db.execute(
            update(Encadreur)
            .where(Encadreur.utilisateur_id == club["prof"].id)
            .values(etat=EtatVerification.en_attente)
        )
    )
    assert reinitialiser(prof, club["adhesion"].id).status_code == 403
    assert journal(en_base) == []


@pytest.mark.parametrize("motif", ["", "Oublié", "x" * 201])
def test_le_motif_compte_10_a_200_caracteres(client: TestClient, club: dict[str, Any], motif: str) -> None:
    assert reinitialiser(connecter(client, "prof"), club["adhesion"].id, motif).status_code == 422


def test_la_onzieme_reinitialisation_du_jour_est_refusee(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    prof = connecter(client, "prof")
    for _ in range(10):
        assert reinitialiser(prof, club["adhesion"].id).status_code == 200

    reponse = reinitialiser(prof, club["adhesion"].id)

    assert reponse.status_code == 429
    assert len(journal(en_base)) == 10


def test_le_plafond_tient_sous_des_requetes_simultanees(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    from app.clubs import mon_club_sante

    prof = connecter(client, "prof")
    for _ in range(8):
        reinitialiser(prof, club["adhesion"].id)

    async def une() -> bool:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            auteur = await db.get(Utilisateur, club["prof"].id)
            try:
                await mon_club_sante.reinitialiser_membre(db, auteur, UUID(str(club["adhesion"].id)), MOTIF, "1.2.3.4")
            except Refus as refus:
                assert refus.statut == 429
                return False
            return True

    async def scenario() -> list[bool]:
        return await asyncio.gather(*(une() for _ in range(4)))

    assert sorted(asyncio.run(scenario())) == [False, False, True, True]
    assert (
        en_base(
            lambda db: db.scalar(
                select(func.count()).select_from(JournalAudit).where(JournalAudit.action == "mot_de_passe_reinitialise")
            )
        )
        == 10
    )


def test_la_reinitialisation_par_lequipe_marque_et_previent_sans_nommer(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur(
        "equipe", droits={("tableau_de_bord", "consulter"), ("inscrits", "consulter"), ("inscrits", "modifier")},
        double_auth=True,
    )  # fmt: skip
    admin = Navigateur(client)
    connecter_admin(admin, "equipe")  # type: ignore[arg-type]

    reponse = admin.post(f"/api/admin/inscrits/{club['membre'].id}/mot-de-passe", json={"motif": MOTIF})

    assert reponse.status_code == 200, reponse.text
    assert connexion(client, "membre", reponse.json()["mot_de_passe"]).json()["mot_de_passe_provisoire"] is True
    (avis,) = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == club["membre"].id))
    ).all()
    assert avis.titre == "Ton mot de passe a été réinitialisé par l'équipe des Clubs Santé"
    collaborateur = en_base(lambda db: db.scalar(select(Utilisateur).where(Utilisateur.identifiant == "equipe")))
    assert collaborateur.nom not in f"{avis.titre}{avis.message}"


def test_un_encadreur_sans_club_ou_un_visiteur_ne_reinitialise_rien(
    client: TestClient,
    club: dict[str, Any],
    en_base: Callable[..., Any],
    creer_utilisateur: Callable[..., Utilisateur],
) -> None:
    from app.clubs.models import EtatRattachement, Rattachement
    from app.comptes.models import Role

    creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg", email_confirme_le=datetime.now(UTC))
    assert reinitialiser(connecter(client, "passant"), club["adhesion"].id).status_code == 403
    en_base(
        lambda db: db.execute(
            update(Rattachement)
            .where(Rattachement.encadreur_id == club["prof"].id)
            .values(etat=EtatRattachement.retire)
        )
    )

    assert reinitialiser(connecter(client, "prof"), club["adhesion"].id).status_code == 404
    assert journal(en_base) == []
