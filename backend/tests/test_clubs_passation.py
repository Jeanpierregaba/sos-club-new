"""Passation de présidence (spec 019, tâches 8 et 9) : proposition, périmètre, doublon, annulation, validation et
refus par l'admin, journalisation avant/après. Écrits avant le code de la tâche 9."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.clubs import service
from app.clubs.models import Adhesion, Club, ClubPassation, EtatAdhesion, EtatClub, EtatPassation
from app.comptes.models import StatutCompte, Utilisateur
from app.eleves.models import Eleve
from tests.conftest import (
    MOT_DE_PASSE,
    VERIFICATION_CLUBS,
    Navigateur,
    connecter_admin,
    etablissement_de,
)

PROPOSER = "/api/clubs/moi/passation"
ANNULER = "/api/clubs/moi/passation/annuler"
PASSATIONS = "/api/admin/clubs/passations"
MON_CLUB = "/api/clubs/moi"


def connecter(navigateur: Navigateur, identifiant: str) -> None:
    assert (
        navigateur.post(
            "/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE}
        ).status_code
        == 200
    )


def club_actif(en_base: Callable[..., Any], president: Utilisateur, *, dre: str = "grand-lome") -> Club:
    """Un club actif. Depuis la spec 020, un successeur doit être membre : les élèves déjà inscrits dans
    l'établissement (président compris) sont rendus membres du club."""
    lieu = etablissement_de(en_base, dre)

    async def inserer(db: AsyncSession) -> Club:
        club = Club(
            etablissement_id=lieu,
            nom="Club Santé de Tokoin",
            nom_normalise="club sante de tokoin",
            demandeur_id=president.id,
            president_id=president.id,
            etat=EtatClub.actif,
            actif_le=datetime.now(UTC),
        )
        db.add(club)
        await db.flush()
        for eleve_id in (await db.scalars(select(Eleve.utilisateur_id).where(Eleve.etablissement_id == lieu))).all():
            db.add(Adhesion(eleve_id=eleve_id, club_id=club.id, etat=EtatAdhesion.active))
        return club

    return en_base(inserer)


def demande_en_attente(en_base: Callable[..., Any], demandeur: Utilisateur, *, dre: str = "grand-lome") -> Club:
    lieu = etablissement_de(en_base, dre)

    async def inserer(db: AsyncSession) -> Club:
        club = Club(
            etablissement_id=lieu,
            nom="Club en attente",
            nom_normalise="club en attente",
            demandeur_id=demandeur.id,
            etat=EtatClub.en_attente,
        )
        db.add(club)
        await db.flush()
        return club

    return en_base(inserer)


def passation(en_base: Callable[..., Any], identifiant: UUID) -> ClubPassation:
    return en_base(lambda db: db.get(ClubPassation, identifiant))


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


def test_le_president_propose_un_successeur_du_meme_etablissement(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    reponse = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version})

    assert reponse.status_code == 201, reponse.text
    corps = reponse.json()
    assert (corps["etat"], corps["successeur_pseudonyme"]) == ("en_attente", "Kofi Curieux")
    (entree,) = journal(en_base, "club_passation_proposee")
    assert entree.cible_id == str(club.id)


def test_un_pseudonyme_hors_etablissement_ou_inexistant_est_refuse(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("ailleurs", affiche="Kofi Kara", dre="kara")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    assert navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Kara", "version": club.version}).status_code == 422
    assert navigateur.post(PROPOSER, json={"pseudonyme": "Personne", "version": club.version}).status_code == 422


def test_un_president_ne_se_propose_pas_lui_meme(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    assert navigateur.post(PROPOSER, json={"pseudonyme": "Ama du Golfe", "version": club.version}).status_code == 422


def test_un_successeur_suspendu_est_refuse(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    successeur = creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == successeur.id).values(statut=StatutCompte.suspendu)
        )
    )
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    assert navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).status_code == 409


def test_un_eleve_qui_ne_preside_pas_ne_propose_pas(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club_actif(en_base, creer_eleve("autre", affiche="Afi Sage"))
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    # Un club actif est présidé par un autre : seul son président peut proposer.
    reponse = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": 1})
    assert reponse.status_code == 403


def test_une_version_perimee_du_club_est_refusee(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    en_base(lambda db: db.execute(update(Club).where(Club.id == club.id).values(version=Club.version + 1)))
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    assert navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).status_code == 409


def test_une_seule_passation_en_attente_par_club(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    assert navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).status_code == 201

    assert navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).status_code == 409


def test_annuler_laisse_le_president_en_place_et_permet_de_reproposer(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()

    reponse = navigateur.post(ANNULER)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "refusee"
    assert en_base(lambda db: db.get(Club, club.id)).president_id == president.id
    assert navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).status_code == 201
    assert passation(en_base, UUID(proposition["id"])).etat is EtatPassation.refusee


def test_ladmin_valide_la_passation_et_les_droits_changent(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    successeur = creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()

    reponse = verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/valider")

    assert reponse.status_code == 200, reponse.text
    assert en_base(lambda db: db.get(Club, club.id)).president_id == successeur.id

    async def preside(db: AsyncSession, utilisateur: Utilisateur) -> Club | None:
        return await service.club_preside(db, utilisateur)

    assert en_base(lambda db: preside(db, president)) is None
    assert en_base(lambda db: preside(db, successeur)) is not None
    (entree,) = journal(en_base, "club_passation")
    assert entree.details["avant"] == str(president.id)
    assert entree.details["apres"] == str(successeur.id)
    assert entree.details["avant_pseudonyme"] == "Ama du Golfe"
    assert entree.details["apres_pseudonyme"] == "Kofi Curieux"


def test_le_nouveau_president_voit_le_club_dans_son_espace(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()
    verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/valider")

    nouveau = Navigateur(client)
    connecter(nouveau, "successeur")
    corps = nouveau.get(MON_CLUB).json()

    assert corps["club"]["president"] is True
    assert corps["club"]["id"] == str(club.id)
    assert (
        nouveau.post(PROPOSER, json={"pseudonyme": "Ama du Golfe", "version": corps["club"]["version"]}).status_code
        == 201
    )


def test_une_passation_ne_se_valide_pas_deux_fois(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()
    assert verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/valider").status_code == 200

    assert verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/valider").status_code == 409


def test_refuser_une_passation_laisse_le_president_et_affiche_le_motif(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()

    reponse = verificateur_clubs.post(
        f"{PASSATIONS}/{proposition['id']}/refuser", json={"motif": "  Successeur non confirmé  "}
    )

    assert reponse.status_code == 200, reponse.text
    assert en_base(lambda db: db.get(Club, club.id)).president_id == president.id
    corps = navigateur.get(MON_CLUB).json()
    assert corps["passation"]["etat"] == "refusee"
    assert corps["passation"]["motif_refus"] == "Successeur non confirmé"


def test_un_refus_de_passation_exige_un_motif(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()

    assert verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/refuser", json={}).status_code == 422
    assert verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/refuser", json={"motif": "x"}).status_code == 422


def test_un_successeur_suspendu_apres_la_proposition_ne_devient_pas_president(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    successeur = creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == successeur.id).values(statut=StatutCompte.suspendu)
        )
    )

    assert verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/valider").status_code == 409
    assert en_base(lambda db: db.get(Club, club.id)).president_id == president.id


def test_un_successeur_qui_change_detablissement_est_refuse(
    client: TestClient,
    verificateur_clubs: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", affiche="Ama du Golfe")
    successeur = creer_eleve("successeur", affiche="Kofi Curieux")
    club = club_actif(en_base, president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    proposition = navigateur.post(PROPOSER, json={"pseudonyme": "Kofi Curieux", "version": club.version}).json()
    ailleurs = etablissement_de(en_base, "kara")
    en_base(
        lambda db: db.execute(
            update(Eleve).where(Eleve.utilisateur_id == successeur.id).values(etablissement_id=ailleurs)
        )
    )

    assert verificateur_clubs.post(f"{PASSATIONS}/{proposition['id']}/valider").status_code == 409
    assert en_base(lambda db: db.get(Club, club.id)).president_id == president.id


def test_la_file_des_passations_respecte_le_perimetre_dre(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    president_kara = creer_eleve("president.kara", affiche="Ama Kara", dre="kara")
    creer_eleve("successeur.kara", affiche="Kofi Kara", dre="kara")
    president_lome = creer_eleve("president.lome", affiche="Afi Lome")
    creer_eleve("successeur.lome", affiche="Yao Lome")
    club_kara = club_actif(en_base, president_kara, dre="kara")
    club_lome = club_actif(en_base, president_lome, dre="grand-lome")

    async def inserer(db: AsyncSession) -> None:
        for club, successeur_pseudo in ((club_kara, "Kofi Kara"), (club_lome, "Yao Lome")):
            successeur = await db.scalar(select(Eleve).where(Eleve.pseudonyme == successeur_pseudo))
            assert successeur is not None
            db.add(
                ClubPassation(
                    club_id=club.id,
                    successeur_id=successeur.utilisateur_id,
                    propose_par=club.president_id,
                )
            )

    en_base(inserer)
    creer_collaborateur("verif.kara", droits=VERIFICATION_CLUBS, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "verif.kara")

    file = client.get(PASSATIONS).json()

    assert (file["total"], [p["club_id"] for p in file["passations"]]) == (1, [str(club_kara.id)])
    assert client.post(f"{PASSATIONS}/00000000-0000-7000-8000-000000000000/valider").status_code == 404
