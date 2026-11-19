"""Routes des classements (spec 036, tâche 4) : charges publiques fermées, accès au classement d'un club,
rangs personnels et vue admin. Partie critique : la confidentialité des mineurs (docs/RULES.md)."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.clubs.models import EtatClub
from app.comptes.models import Role, Utilisateur
from app.points.models import Semestre
from tests.conftest import Navigateur, connecter_admin
from tests.espace_club import connecter
from tests.test_classements import affilier, etat_club, point, rattacher, renommer, semestre  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

PUBLIC = "/api/classements"
MOI = "/api/classements/moi"
MON_CLUB = "/api/classements/mon-club"
RANG_CLUB = "/api/classements/mon-club/rang"
ADMIN = "/api/admin/points/classements"
LECTEUR = {("tableau_de_bord", "consulter"), ("points", "consulter")}

CLES_PERSONNE = {"rang", "nom", "club", "dre", "points"}
CLES_CLUB = {"rang", "club_id", "nom", "etablissement", "dre", "points"}
CLES_INTERNE = {"rang", "nom", "points", "est_moi"}


@pytest.fixture
def reseau(
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> dict[str, Any]:
    """Un club actif à Grand Lomé : sa présidente Ama, un membre Kofi, un encadreur ; un élève de Kara sans club."""
    ama = creer_eleve("ama", "Ama Présidente", dre="grand-lome")
    club = creer_club(ama, nom="Club Santé Tokoin")
    kofi = creer_eleve("kofi", "Kofi Membre", dre="grand-lome")
    affilier(en_base, kofi.id, club.id)
    prof = creer_encadreur("prof", dre="grand-lome")
    renommer(en_base, prof.id, "Komla", "Adjo")
    rattacher(en_base, prof.id, club.id)
    yao = creer_eleve("yao", "Yao de Kara", dre="kara")
    point(en_base, ama.id, 300, "a1", semestre_id=semestre.id, club_id=club.id, demi_points=300)
    point(en_base, kofi.id, 100, "k1", semestre_id=semestre.id, club_id=club.id, demi_points=100)
    point(en_base, yao.id, 200, "y1", semestre_id=semestre.id)
    point(en_base, prof.id, 50, "p1", semestre_id=semestre.id, action="encadreur.bienvenue")
    return {"ama": ama, "kofi": kofi, "prof": prof, "yao": yao, "club": club}


# Classement public ---------------------------------------------------------------------------------------------


def test_le_classement_public_des_eleves_ne_montre_que_les_champs_publics(
    client: TestClient, reseau: dict[str, Any]
) -> None:
    corps = client.get(PUBLIC).json()

    assert [ligne["nom"] for ligne in corps["lignes"]] == ["Ama Présidente", "Yao de Kara", "Kofi Membre"]
    assert all(set(ligne) == CLES_PERSONNE for ligne in corps["lignes"])
    assert corps["lignes"][0]["club"] == "Club Santé Tokoin"
    assert corps["semestre"]["libelle"] == "Semestre en cours"
    texte = str(corps)
    for utilisateur in reseau.values():
        assert str(utilisateur.id) not in texte or utilisateur is reseau["club"]
    assert "Jean" not in texte and "Kodjo" not in texte  # le nom complet des comptes de test


def test_le_classement_public_des_encadreurs_montre_prenom_et_initiale(
    client: TestClient, reseau: dict[str, Any]
) -> None:
    corps = client.get(PUBLIC, params={"categorie": "encadreurs"}).json()

    assert corps["lignes"] == [
        {"rang": 1, "nom": "Komla A.", "club": "Club Santé Tokoin", "dre": corps["lignes"][0]["dre"], "points": 50}
    ]
    assert "Adjo" not in str(corps)


def test_le_classement_public_des_clubs_a_un_score_decimal(
    client: TestClient,
    reseau: dict[str, Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> None:
    point(en_base, reseau["kofi"].id, 5, "k2", semestre_id=semestre.id, club_id=reseau["club"].id, demi_points=5)

    corps = client.get(PUBLIC, params={"categorie": "clubs"}).json()

    assert len(corps["lignes"]) == 1
    assert set(corps["lignes"][0]) == CLES_CLUB
    assert corps["lignes"][0]["points"] == 202.5


def test_un_club_suspendu_quitte_le_classement_public(
    client: TestClient, reseau: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    etat_club(en_base, reseau["club"].id, EtatClub.suspendu)

    assert client.get(PUBLIC, params={"categorie": "clubs"}).json()["lignes"] == []


def test_le_classement_dune_dre(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = client.get(PUBLIC, params={"niveau": "dre", "dre": "kara"}).json()

    assert [ligne["nom"] for ligne in corps["lignes"]] == ["Yao de Kara"]
    assert corps["dre"]["code"] == "kara"


@pytest.mark.parametrize(
    ("params", "statut"),
    [
        ({"niveau": "dre"}, 422),
        ({"niveau": "dre", "dre": "atlantide"}, 404),
        ({"niveau": "club"}, 422),
        ({"categorie": "membres"}, 422),
        ({"par_page": 101}, 422),
        ({"page": 0}, 422),
    ],
)
def test_les_parametres_invalides_sont_refuses(
    client: TestClient, reseau: dict[str, Any], params: dict[str, Any], statut: int
) -> None:
    assert client.get(PUBLIC, params=params).status_code == statut


def test_une_page_hors_limites_est_vide_avec_le_total(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = client.get(PUBLIC, params={"page": 9}).json()

    assert corps["lignes"] == []
    assert corps["total"] == 3


# Classement interne du club ------------------------------------------------------------------------------------


def test_un_membre_voit_le_classement_de_son_club_avec_sa_ligne(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = connecter(client, "kofi").get(MON_CLUB).json()

    assert corps["club"]["nom"] == "Club Santé Tokoin"
    assert [(ligne["nom"], ligne["est_moi"]) for ligne in corps["lignes"]] == [
        ("Ama Présidente", False),
        ("Kofi Membre", True),
    ]
    assert all(set(ligne) == CLES_INTERNE for ligne in corps["lignes"])


def test_un_encadreur_rattache_voit_les_eleves_et_les_encadreurs(client: TestClient, reseau: dict[str, Any]) -> None:
    navigateur = connecter(client, "prof")

    assert [ligne["nom"] for ligne in navigateur.get(MON_CLUB).json()["lignes"]] == ["Ama Présidente", "Kofi Membre"]
    encadreurs = navigateur.get(MON_CLUB, params={"categorie": "encadreurs"}).json()
    assert [(ligne["nom"], ligne["est_moi"]) for ligne in encadreurs["lignes"]] == [("Komla A.", True)]


def test_la_presidente_voit_le_classement_de_son_club(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = connecter(client, "ama").get(MON_CLUB).json()

    assert corps["lignes"][0]["est_moi"] is True


def test_un_eleve_hors_du_club_ne_le_voit_pas(client: TestClient, reseau: dict[str, Any]) -> None:
    reponse = connecter(client, "yao").get(MON_CLUB)

    assert reponse.status_code == 404


def test_le_classement_dun_club_exige_une_connexion(client: TestClient, reseau: dict[str, Any]) -> None:
    assert client.get(MON_CLUB).status_code == 401
    assert client.get(MOI).status_code == 401


def test_un_classement_interne_de_clubs_est_refuse(client: TestClient, reseau: dict[str, Any]) -> None:
    assert connecter(client, "kofi").get(MON_CLUB, params={"categorie": "clubs"}).status_code == 422


# Rang du club (page « Mon club ») ------------------------------------------------------------------------------


def test_un_membre_voit_le_rang_de_son_club(client: TestClient, reseau: dict[str, Any]) -> None:
    for qui in ("kofi", "ama", "prof"):
        corps = connecter(client, qui).get(RANG_CLUB).json()

        assert corps["club"]["nom"] == "Club Santé Tokoin"
        assert corps["semestre"]["libelle"] == "Semestre en cours"
        assert (corps["points"], corps["rang_dre"], corps["rang_national"]) == (200.0, 1, 1)


def test_un_club_suspendu_na_plus_de_rang(
    client: TestClient, reseau: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    etat_club(en_base, reseau["club"].id, EtatClub.suspendu)

    corps = connecter(client, "kofi").get(RANG_CLUB).json()

    assert corps["points"] == 200.0
    assert (corps["rang_dre"], corps["rang_national"]) == (None, None)


def test_le_rang_du_club_exige_un_club_et_une_connexion(client: TestClient, reseau: dict[str, Any]) -> None:
    assert client.get(RANG_CLUB).status_code == 401
    assert connecter(client, "yao").get(RANG_CLUB).status_code == 404


# Rangs personnels ----------------------------------------------------------------------------------------------


def test_les_rangs_personnels_dun_eleve(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = connecter(client, "kofi").get(MOI).json()

    assert corps["club"]["nom"] == "Club Santé Tokoin"
    assert corps["semestre_en_cours"]["libelle"]
    assert corps["semestre"] == {"points": 100, "rang_club": 2, "rang_dre": 2, "rang_national": 3, "classe": True}
    assert corps["historique"]["rang_national"] == 3


def test_un_eleve_sans_club_garde_ses_rangs_dre_et_national(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = connecter(client, "yao").get(MOI).json()

    assert corps["club"] is None
    assert corps["semestre"]["rang_club"] is None
    assert corps["semestre"]["rang_dre"] == 1
    assert corps["semestre"]["rang_national"] == 2


def test_un_eleve_sans_point_nest_pas_classe(
    client: TestClient, reseau: dict[str, Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve("nouveau", "Nouveau Venu")

    corps = connecter(client, "nouveau").get(MOI).json()

    assert corps["semestre"] == {
        "points": 0,
        "rang_club": None,
        "rang_dre": None,
        "rang_national": None,
        "classe": False,
    }


def test_les_rangs_personnels_dun_encadreur(client: TestClient, reseau: dict[str, Any]) -> None:
    corps = connecter(client, "prof").get(MOI).json()

    assert corps["categorie"] == "encadreurs"
    assert corps["semestre"]["rang_club"] == 1
    assert corps["semestre"]["rang_national"] == 1


def test_un_visiteur_na_pas_de_classement_personnel(
    client: TestClient, reseau: dict[str, Any], creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg", email_confirme_le=datetime.now(UTC))
    navigateur = connecter(client, "passant")

    assert navigateur.get(MOI).status_code == 403
    assert navigateur.get(MON_CLUB).status_code == 403


# Vue admin -----------------------------------------------------------------------------------------------------


def _admin(client: TestClient, creer_collaborateur: Callable[..., Any], **options: Any) -> Navigateur:
    creer_collaborateur("equipe", droits=LECTEUR, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, "equipe")  # type: ignore[arg-type]
    return navigateur


def test_ladmin_voit_les_identifiants_pour_corriger(
    client: TestClient, reseau: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    admin = _admin(client, creer_collaborateur, double_auth=True)

    corps = admin.get(ADMIN).json()

    assert corps["lignes"][0]["utilisateur_id"] == str(reseau["ama"].id)


def test_ladmin_ouvre_le_classement_interne_dun_club_suspendu(
    client: TestClient, reseau: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    etat_club(en_base, reseau["club"].id, EtatClub.suspendu)
    admin = _admin(client, creer_collaborateur, double_auth=True)

    corps = admin.get(ADMIN, params={"club_id": str(reseau["club"].id)}).json()

    assert corps["statut"] == "suspendu"
    assert [ligne["nom"] for ligne in corps["lignes"]] == ["Ama Présidente", "Kofi Membre"]


def test_la_vue_admin_exige_la_double_authentification_et_le_perimetre_national(
    client: TestClient, reseau: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    sans_2fa = _admin(client, creer_collaborateur)
    assert sans_2fa.get(ADMIN).status_code == 403

    creer_collaborateur("kara", droits=LECTEUR, perimetre_dre="kara", double_auth=True)
    de_dre = Navigateur(client)
    connecter_admin(de_dre, "kara")  # type: ignore[arg-type]
    assert de_dre.get(ADMIN).status_code == 403
