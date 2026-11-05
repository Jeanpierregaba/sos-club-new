"""Vérification des clubs par l'admin (spec 019, tâches 6 et 7) : file, périmètre DRE, double authentification,
activation atomique, doublure, version périmée, refus, compteurs. Écrits avant le code de la tâche 7."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces
from app.admin.models import Collaborateur, JournalAudit
from app.clubs import verification
from app.clubs.models import Club, ClubAxe, ClubPassation, EtatClub, EtatPassation
from app.comptes.inscription import Refus
from app.comptes.models import StatutCompte, Utilisateur
from app.referentiel.models import Etablissement, StatutEtablissement
from tests.conftest import (
    VERIFICATION_CLUBS,
    connecter_admin,
    etablissement_de,
    moteur_test,
)

FILE = "/api/admin/clubs"
PASSATIONS = "/api/admin/clubs/passations"
AXE = "sante-environnement"


def demande(
    en_base: Callable[..., Any],
    demandeur: Utilisateur,
    *,
    nom: str = "Club Santé de Tokoin",
    dre: str = "grand-lome",
    etat: EtatClub = EtatClub.en_attente,
    il_y_a: int = 0,
) -> Club:
    lieu = etablissement_de(en_base, dre)

    async def inserer(db: AsyncSession) -> Club:
        club = Club(
            etablissement_id=lieu,
            nom=nom,
            nom_normalise=nom.lower(),
            demandeur_id=demandeur.id,
            etat=etat,
            motif_refus="Motif du refus" if etat is EtatClub.refuse else None,
            demande_le=datetime.now(UTC) - timedelta(days=il_y_a),
        )
        db.add(club)
        await db.flush()
        db.add(ClubAxe(club_id=club.id, axe_code=AXE))
        return club

    return en_base(inserer)


def club_actif(
    en_base: Callable[..., Any], president: Utilisateur, *, nom: str = "Club déjà actif", dre: str = "grand-lome"
) -> Club:
    lieu = etablissement_de(en_base, dre)

    async def inserer(db: AsyncSession) -> Club:
        club = Club(
            etablissement_id=lieu,
            nom=nom,
            nom_normalise=nom.lower(),
            demandeur_id=president.id,
            president_id=president.id,
            etat=EtatClub.actif,
            actif_le=datetime.now(UTC),
        )
        db.add(club)
        await db.flush()
        return club

    return en_base(inserer)


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


# File ----------------------------------------------------------------------------------------------------------


def test_la_file_montre_les_demandes_en_attente_des_plus_anciennes_aux_plus_recentes(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    demande(en_base, creer_eleve("eleve.recent", affiche="Ama du Golfe"), nom="Club récent", il_y_a=1)
    demande(en_base, creer_eleve("eleve.ancien", affiche="Kofi Curieux"), nom="Club ancien", il_y_a=5)

    file = verificateur_clubs.get(FILE).json()

    assert file["total"] == 2
    assert [d["nom"] for d in file["demandes"]] == ["Club ancien", "Club récent"]
    premiere = file["demandes"][0]
    assert premiere["demandeur_pseudonyme"] == "Kofi Curieux"
    assert premiere["etablissement"]["dre_code"] == "grand-lome"
    assert premiere["axes"] == [AXE]
    assert premiere["etat"] == "en_attente"


def test_la_file_des_refuses_est_a_part(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    demande(
        en_base,
        creer_eleve("eleve1"),
        nom="Club refusé",
        etat=EtatClub.refuse,
    )
    demande(en_base, creer_eleve("eleve2", affiche="Kofi Curieux"), nom="Club en attente")

    refuses = verificateur_clubs.get(FILE, params={"etat": "refuse"}).json()["demandes"]

    assert [d["nom"] for d in refuses] == ["Club refusé"]
    assert refuses[0]["motif_refus"] == "Motif du refus"


def test_la_file_ne_liste_pas_les_clubs_actifs(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    club_actif(en_base, creer_eleve("eleve1"))

    assert verificateur_clubs.get(FILE, params={"etat": "actif"}).status_code == 422


# Activation ----------------------------------------------------------------------------------------------------


def test_activer_rend_le_club_actif_et_le_demandeur_president(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    club = demande(en_base, eleve)

    reponse = verificateur_clubs.post(f"{FILE}/{club.id}/activer")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "actif"
    apres = en_base(lambda db: db.get(Club, club.id))
    assert apres.etat is EtatClub.actif
    assert apres.president_id == eleve.id
    assert apres.actif_le is not None and apres.decide_le is not None and apres.decide_par is not None
    (entree,) = journal(en_base, "club_active")
    assert entree.cible_id == str(club.id)
    assert entree.details == {"president_pseudonyme": "Ama du Golfe"}
    assert entree.perimetre == "grand-lome"


def test_activer_deux_fois_repond_409(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer").status_code == 200

    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer").status_code == 409


def test_deux_activations_simultanees_une_seule_reussit(
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    chef = creer_collaborateur("verif.clubs", droits=VERIFICATION_CLUBS, double_auth=True)

    async def une_decision() -> bool:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
            auteur = await db.get(Utilisateur, chef.id)
            assert collaborateur is not None and auteur is not None
            acces = Acces(
                utilisateur=auteur,
                collaborateur=collaborateur,
                droits={("clubs", Action.consulter), ("clubs", Action.approuver)},
                double_auth_active=True,
            )
            try:
                await verification.activer(db, acces, club.id, "127.0.0.1")
            except Refus as refus:
                assert refus.statut == 409
                return False
            return True

    async def scenario() -> list[bool]:
        return await asyncio.gather(une_decision(), une_decision())

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert en_base(lambda db: db.get(Club, club.id)).etat is EtatClub.actif


def test_une_doublure_du_meme_etablissement_est_refusee_automatiquement(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    premier = demande(en_base, creer_eleve("eleve1"), nom="Club premier")
    doublure = demande(en_base, creer_eleve("eleve2", affiche="Kofi Curieux"), nom="Club doublure")

    assert verificateur_clubs.post(f"{FILE}/{premier.id}/activer").status_code == 200

    apres = en_base(lambda db: db.get(Club, doublure.id))
    assert apres.etat is EtatClub.refuse
    assert apres.motif_refus == "Un club a été activé pour cet établissement."
    refus = journal(en_base, "club_refuse")
    assert [(e.cible_id, e.details) for e in refus] == [
        (str(doublure.id), {"motif": "Un club a été activé pour cet établissement.", "automatique": True})
    ]


def test_activier_un_club_dun_etablissement_deja_dote_repond_409(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    # Un club actif est inséré directement : l'activation de la demande doit le voir.
    club_actif(en_base, creer_eleve("eleve1"))
    en_attente = demande(en_base, creer_eleve("eleve3", affiche="Afi Sage"), nom="Club en attente")

    reponse = verificateur_clubs.post(f"{FILE}/{en_attente.id}/activer")

    assert reponse.status_code == 409
    assert "club actif" in reponse.json()["detail"]


def test_activer_un_demandeur_suspendu_repond_409(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve1")
    club = demande(en_base, eleve)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=StatutCompte.suspendu)
        )
    )

    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer").status_code == 409
    assert en_base(lambda db: db.get(Club, club.id)).etat is EtatClub.en_attente


def test_activer_un_club_dun_etablissement_desactive_repond_409(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    en_base(
        lambda db: db.execute(
            update(Etablissement)
            .where(Etablissement.id == club.etablissement_id)
            .values(statut=StatutEtablissement.inactif)
        )
    )

    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer").status_code == 409


def test_une_version_perimee_repond_409_puis_la_bonne_version_passe(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    version = verificateur_clubs.get(FILE).json()["demandes"][0]["version"]
    en_base(lambda db: db.execute(update(Club).where(Club.id == club.id).values(version=Club.version + 1)))

    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer", json={"version": version}).status_code == 409
    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer", json={"version": version + 1}).status_code == 200


# Refus ---------------------------------------------------------------------------------------------------------


def test_refuser_garde_le_motif_et_ne_change_pas_le_president(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))

    reponse = verificateur_clubs.post(f"{FILE}/{club.id}/refuser", json={"motif": "  Encadreur non joignable  "})

    assert reponse.status_code == 200, reponse.text
    apres = en_base(lambda db: db.get(Club, club.id))
    assert (apres.etat, apres.motif_refus, apres.president_id) == (
        EtatClub.refuse,
        "Encadreur non joignable",
        None,
    )
    (entree,) = journal(en_base, "club_refuse")
    assert entree.details == {"motif": "Encadreur non joignable"}


@pytest.mark.parametrize("corps", [{}, {"motif": ""}, {"motif": "  "}, {"motif": "x" * 501}])
def test_un_refus_exige_un_motif(
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    corps: dict[str, str],
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))

    assert verificateur_clubs.post(f"{FILE}/{club.id}/refuser", json=corps).status_code == 422


def test_une_demande_deja_traitee_ne_se_decide_plus(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    verificateur_clubs.post(f"{FILE}/{club.id}/refuser", json={"motif": "Doublon"})

    assert verificateur_clubs.post(f"{FILE}/{club.id}/refuser", json={"motif": "Doublon"}).status_code == 409
    assert verificateur_clubs.post(f"{FILE}/{club.id}/activer").status_code == 409


# Périmètre et droits --------------------------------------------------------------------------------------------


def test_un_collaborateur_de_dre_ne_voit_et_ne_decide_que_sa_dre(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    demande(en_base, creer_eleve("eleve.kara", affiche="Ama Kara", dre="kara"), nom="Club Kara", dre="kara")
    lome = demande(
        en_base, creer_eleve("eleve.lome", affiche="Kofi Lome", dre="grand-lome"), nom="Club Lomé", dre="grand-lome"
    )
    creer_collaborateur("verif.kara", droits=VERIFICATION_CLUBS, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "verif.kara")

    file = client.get(FILE).json()

    assert (file["total"], [d["nom"] for d in file["demandes"]]) == (1, ["Club Kara"])
    assert client.post(f"{FILE}/{lome.id}/activer").status_code == 404
    assert client.post(f"{FILE}/{lome.id}/refuser", json={"motif": "Hors DRE"}).status_code == 404
    assert en_base(lambda db: db.get(Club, lome.id)).etat is EtatClub.en_attente


def test_un_collaborateur_national_voit_toutes_les_dre(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    demande(en_base, creer_eleve("eleve.kara", affiche="Ama Kara", dre="kara"), nom="Club Kara", dre="kara")
    demande(
        en_base, creer_eleve("eleve.lome", affiche="Kofi Lome", dre="grand-lome"), nom="Club Lomé", dre="grand-lome"
    )

    assert verificateur_clubs.get(FILE).json()["total"] == 2


def test_sans_le_droit_la_file_est_refusee(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})
    connecter_admin(client, "autre")

    assert client.get(FILE).status_code == 403
    assert client.post(f"{FILE}/{club.id}/activer").status_code == 403


def test_consulter_ne_permet_pas_de_decider(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    club = demande(en_base, creer_eleve("eleve1"))
    creer_collaborateur("lecteur", droits={("clubs", "consulter")}, double_auth=True)
    connecter_admin(client, "lecteur")

    assert client.get(FILE).status_code == 200
    assert client.post(f"{FILE}/{club.id}/activer").status_code == 403


def test_lire_la_file_exige_aussi_la_double_authentification(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    demande(en_base, creer_eleve("eleve1"))
    creer_collaborateur("lecteur", droits={("clubs", "consulter")})
    connecter_admin(client, "lecteur")

    assert client.get(FILE).status_code == 403
    assert client.get("/api/admin/moi").json()["clubs_a_valider"] is None


# Compteurs -------------------------------------------------------------------------------------------------------


def test_le_compteur_du_menu_additionne_les_demandes_et_les_passations(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    demande(en_base, creer_eleve("eleve1"), nom="Club en attente")
    president = creer_eleve("president", affiche="Kofi Curieux")
    successeur = creer_eleve("successeur", affiche="Afi Sage")
    club = club_actif(en_base, president)

    async def inserer(db: AsyncSession) -> None:
        db.add(
            ClubPassation(
                club_id=club.id,
                successeur_id=successeur.id,
                propose_par=president.id,
                etat=EtatPassation.en_attente,
            )
        )

    en_base(inserer)

    assert verificateur_clubs.get("/api/admin/moi").json()["clubs_a_valider"] == 2


def test_le_tableau_de_bord_compte_les_clubs_actifs_et_les_demandes(
    verificateur_clubs: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    demande(en_base, creer_eleve("eleve1"), nom="Club en attente")
    club_actif(en_base, creer_eleve("eleve2", affiche="Kofi Curieux"), nom="Club actif")

    tableau = verificateur_clubs.get("/api/admin/tableau-de-bord").json()

    assert tableau["clubs_a_valider"] == 1
    indicateur = {i["id"]: i["valeur"] for i in tableau["indicateurs"]}
    assert indicateur["clubs_actifs"] == 1
