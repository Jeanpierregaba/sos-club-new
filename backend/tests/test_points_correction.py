"""Correction motivée et annulation d'une ligne du registre (spec 036, tâche 6). Partie critique : écrite pour
fixer le comportement avant l'écran (docs/TESTING.md)."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.models import JournalAudit
from app.comptes.models import Role, Utilisateur
from app.points.bareme import ACTION_CORRECTION, CERTIFICATION_ELEVE
from app.points.models import MouvementPoints, Semestre
from app.points.service import aujourd_hui
from tests.conftest import Navigateur, connecter_admin
from tests.test_classements import point, semestre  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

CORRECTIONS = "/api/admin/points/corrections"
GESTIONNAIRE = {("tableau_de_bord", "consulter"), ("points", "consulter"), ("points", "modifier")}
MOTIF = "Erreur de saisie lors du quiz."


def annulation(ligne_id: Any) -> str:
    return f"/api/admin/points/lignes/{ligne_id}/annulation"


def admin(client: TestClient, creer_collaborateur: Callable[..., Any], droits: set[Any], **options: Any) -> Navigateur:
    identifiant = options.pop("identifiant", "equipe")
    creer_collaborateur(identifiant, droits=droits, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


@pytest.fixture
def equipe(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    return admin(client, creer_collaborateur, GESTIONNAIRE, double_auth=True)


@pytest.fixture
def eleve_du_club(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> tuple[Utilisateur, Any]:
    ama = creer_eleve("ama", "Ama Présidente")
    return ama, creer_club(ama, nom="Club Santé Tokoin")


def total(en_base: Callable[..., Any], utilisateur_id: Any) -> int:
    return int(
        en_base(
            lambda db: db.scalar(
                select(func.coalesce(func.sum(MouvementPoints.montant), 0)).where(
                    MouvementPoints.utilisateur_id == utilisateur_id
                )
            )
        )
    )


def part_du_club(en_base: Callable[..., Any], club_id: Any) -> float:
    demi = en_base(
        lambda db: db.scalar(
            select(func.coalesce(func.sum(MouvementPoints.demi_points_club), 0)).where(
                MouvementPoints.club_id == club_id
            )
        )
    )
    return int(demi) / 2


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return list(en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all())


def corriger(navigateur: Navigateur, utilisateur_id: Any, montant: int, **champs: Any) -> Any:
    corps = {"utilisateur_id": str(utilisateur_id), "montant": montant, "motif": MOTIF, "cle": str(uuid4())}
    return navigateur.post(CORRECTIONS, json=corps | champs)


# Correction ----------------------------------------------------------------------------------------------------


def test_une_correction_positive_secrit_sans_part_de_club(
    equipe: Navigateur,
    eleve_du_club: tuple[Utilisateur, Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> None:
    ama, club = eleve_du_club

    reponse = corriger(equipe, ama.id, 25)

    assert reponse.status_code == 201, reponse.text
    corps = reponse.json()
    assert (corps["action"], corps["montant"], corps["motif"]) == (ACTION_CORRECTION, 25, MOTIF)
    assert corps["club"] is None and corps["points_club"] is None
    assert corps["semestre"] == "Semestre en cours"
    assert corps["valide_par"]["identifiant"] == "equipe"
    assert total(en_base, ama.id) == 25
    assert part_du_club(en_base, club.id) == 0


def test_une_correction_negative_baisse_leleve_et_pas_le_club(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, club = eleve_du_club
    point(en_base, ama.id, 100, "a1", club_id=club.id, demi_points=100)

    assert corriger(equipe, ama.id, -10).status_code == 201

    assert total(en_base, ama.id) == 90
    assert part_du_club(en_base, club.id) == 50


def test_un_total_peut_devenir_negatif(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any], client: TestClient
) -> None:
    ama, _ = eleve_du_club

    assert corriger(equipe, ama.id, -40).status_code == 201

    assert total(en_base, ama.id) == -40
    # Un total négatif reste privé : il n'est jamais publié dans un classement.
    reponse = client.get("/api/classements", params={"periode": "historique"})
    assert reponse.status_code == 200
    assert reponse.json()["lignes"] == []


def test_une_correction_change_le_classement_interne_du_club(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, club = eleve_du_club
    point(en_base, ama.id, 100, "a1", club_id=club.id, demi_points=100)
    interne = {"club_id": str(club.id), "categorie": "eleves", "periode": "historique"}

    assert corriger(equipe, ama.id, -40).status_code == 201

    (ligne,) = equipe.get("/api/admin/points/classements", params=interne).json()["lignes"]
    assert ligne["points"] == 60


def test_une_correction_hors_semestre_ne_compte_que_dans_lhistorique(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any]
) -> None:
    ama, _ = eleve_du_club

    corps = corriger(equipe, ama.id, 15).json()

    assert corps["semestre"] is None


@pytest.mark.parametrize(
    "champs",
    [
        {"montant": 0},
        {"montant": 10_001},
        {"montant": -10_001},
        {"motif": "Trop court"[:9]},
        {"motif": "x" * 501},
        {"motif": "          espaces  "},
    ],
)
def test_les_entrees_invalides_sont_refusees(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any], champs: dict[str, Any]
) -> None:
    ama, _ = eleve_du_club

    reponse = corriger(equipe, ama.id, champs.pop("montant", 10), **champs)

    assert reponse.status_code == 422
    assert total(en_base, ama.id) == 0


def test_une_correction_ne_vise_ni_admin_ni_visiteur_ni_invite(
    equipe: Navigateur, creer_utilisateur: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any]
) -> None:
    visiteur = creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg")
    invite = creer_utilisateur("invite1", Role.invite)
    collegue = creer_collaborateur("collegue")

    for cible in (visiteur, invite, collegue):
        assert corriger(equipe, cible.id, 10).status_code == 422
    assert corriger(equipe, uuid4(), 10).status_code == 404


def test_un_encadreur_se_corrige_aussi(equipe: Navigateur, creer_encadreur: Callable[..., Utilisateur]) -> None:
    prof = creer_encadreur("prof")

    assert corriger(equipe, prof.id, 30).status_code == 201


def test_la_meme_cle_necrit_quune_ligne(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, _ = eleve_du_club
    cle = str(uuid4())

    premiere = corriger(equipe, ama.id, 20, cle=cle)
    seconde = corriger(equipe, ama.id, 20, cle=cle)
    autre = corriger(equipe, ama.id, 99, cle=cle)

    autre_motif = corriger(equipe, ama.id, 20, cle=cle, motif="Un tout autre motif de correction.")

    assert (premiere.status_code, seconde.status_code, autre.status_code) == (201, 200, 409)
    assert autre_motif.status_code == 409
    assert premiere.json()["id"] == seconde.json()["id"]
    assert total(en_base, ama.id) == 20


def test_la_correction_est_journalisee(
    equipe: Navigateur,
    eleve_du_club: tuple[Utilisateur, Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> None:
    ama, _ = eleve_du_club

    corriger(equipe, ama.id, -5)

    (entree,) = journal(en_base, "points_corriges")
    assert entree.details["beneficiaire"] == str(ama.id)
    assert entree.details["montant"] == -5
    assert entree.details["motif"] == MOTIF
    assert entree.details["semestre"] == "Semestre en cours"
    assert entree.details["club"] is None
    assert entree.perimetre == "national"


@pytest.mark.parametrize(
    ("droits", "options"),
    [
        ({("tableau_de_bord", "consulter"), ("points", "consulter")}, {"double_auth": True}),
        (GESTIONNAIRE, {}),
        (GESTIONNAIRE, {"double_auth": True, "perimetre_dre": "kara"}),
    ],
)
def test_corriger_exige_le_droit_la_2fa_et_le_national(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    eleve_du_club: tuple[Utilisateur, Any],
    en_base: Callable[..., Any],
    droits: set[Any],
    options: dict[str, Any],
) -> None:
    ama, _ = eleve_du_club
    navigateur = admin(client, creer_collaborateur, droits, **options)

    assert corriger(navigateur, ama.id, 10).status_code == 403
    assert total(en_base, ama.id) == 0


# Annulation ----------------------------------------------------------------------------------------------------


def test_annuler_un_gain_retire_la_part_du_club_dans_le_semestre_dorigine(
    equipe: Navigateur,
    eleve_du_club: tuple[Utilisateur, Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> None:
    ama, club = eleve_du_club

    async def passe(db: Any) -> Semestre:
        element = Semestre(
            libelle="Semestre passé",
            debut=aujourd_hui() - timedelta(days=200),
            fin=aujourd_hui() - timedelta(days=20),
        )
        db.add(element)
        return element

    ancien = en_base(passe)
    gain = point(en_base, ama.id, 100, "a1", semestre_id=ancien.id, club_id=club.id, demi_points=100)

    reponse = equipe.post(annulation(gain.id), json={"motif": MOTIF})

    assert reponse.status_code == 201, reponse.text
    corps = reponse.json()
    # L'annulation va dans le semestre du gain, pas dans le semestre en cours.
    assert (corps["montant"], corps["annule_id"], corps["semestre"]) == (-100, str(gain.id), "Semestre passé")
    assert corps["points_club"] == -50
    assert total(en_base, ama.id) == 0
    assert part_du_club(en_base, club.id) == 0
    origine = en_base(lambda db: db.get(MouvementPoints, gain.id))
    assert (origine.montant, origine.motif) == (100, None)
    (entree,) = journal(en_base, "points_annules")
    assert entree.details["club"]["nom"] == "Club Santé Tokoin"
    assert entree.details["ligne_annulee"] == str(gain.id)


def test_une_ligne_ne_sannule_quune_fois(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, _ = eleve_du_club
    gain = point(en_base, ama.id, 100, "a1")

    assert equipe.post(annulation(gain.id), json={"motif": MOTIF}).status_code == 201
    assert equipe.post(annulation(gain.id), json={"motif": MOTIF}).status_code == 409
    assert total(en_base, ama.id) == 0


def test_annuler_une_correction_la_retire_exactement(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, _ = eleve_du_club
    correction = corriger(equipe, ama.id, -30).json()

    reponse = equipe.post(annulation(correction["id"]), json={"motif": "La correction visait le mauvais élève."})

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["montant"] == 30
    assert total(en_base, ama.id) == 0
    registre = equipe.get("/api/admin/points/registre").json()
    assert next(ligne for ligne in registre["lignes"] if ligne["id"] == correction["id"])["annulee"] is True


def test_les_points_dun_certificat_se_retirent_par_la_revocation(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, _ = eleve_du_club
    gain = point(en_base, ama.id, 100, "cert1", action=CERTIFICATION_ELEVE)

    reponse = equipe.post(annulation(gain.id), json={"motif": MOTIF})

    assert reponse.status_code == 422
    assert "certificat" in reponse.json()["detail"]
    assert total(en_base, ama.id) == 100


def test_une_annulation_ne_sannule_pas(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, _ = eleve_du_club
    gain = point(en_base, ama.id, 100, "a1")
    contre = equipe.post(annulation(gain.id), json={"motif": MOTIF}).json()

    assert equipe.post(annulation(contre["id"]), json={"motif": MOTIF}).status_code == 422


def test_annuler_exige_un_motif_et_une_ligne_connue(
    equipe: Navigateur, eleve_du_club: tuple[Utilisateur, Any], en_base: Callable[..., Any]
) -> None:
    ama, _ = eleve_du_club
    gain = point(en_base, ama.id, 100, "a1")

    assert equipe.post(annulation(gain.id), json={"motif": "court"}).status_code == 422
    assert equipe.post(annulation(gain.id), json={}).status_code == 422
    assert equipe.post(annulation(uuid4()), json={"motif": MOTIF}).status_code == 404


def test_annuler_est_reserve_au_national_avec_2fa(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    eleve_du_club: tuple[Utilisateur, Any],
    en_base: Callable[..., Any],
) -> None:
    ama, _ = eleve_du_club
    gain = point(en_base, ama.id, 100, "a1")
    de_dre = admin(client, creer_collaborateur, GESTIONNAIRE, double_auth=True, perimetre_dre="kara")

    assert de_dre.post(annulation(gain.id), json={"motif": MOTIF}).status_code == 403
    assert total(en_base, ama.id) == 100
