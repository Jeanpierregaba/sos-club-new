"""Registre des points pour l'équipe (spec 036, tâche 5) : filtres, pagination, champs, lecture seule, accès."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.comptes.models import Utilisateur
from app.points.bareme import ACTION_CORRECTION
from app.points.models import Semestre
from tests.conftest import Navigateur, connecter_admin
from tests.test_classements import affilier, point, semestre  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

REGISTRE = "/api/admin/points/registre"
BENEFICIAIRES = "/api/admin/points/beneficiaires"
LECTEUR = {("tableau_de_bord", "consulter"), ("points", "consulter")}
GESTIONNAIRE = LECTEUR | {("points", "modifier")}


def admin(client: TestClient, creer_collaborateur: Callable[..., Any], droits: set[Any], **options: Any) -> Navigateur:
    identifiant = options.pop("identifiant", "equipe")
    creer_collaborateur(identifiant, droits=droits, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


@pytest.fixture
def lignes(
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> dict[str, Any]:
    ama = creer_eleve("ama", "Ama Présidente")
    club = creer_club(ama, nom="Club Santé Tokoin")
    prof = creer_encadreur("prof")
    gain = point(en_base, ama.id, 100, "a1", semestre_id=semestre.id, club_id=club.id, demi_points=100)
    point(en_base, ama.id, 5, "a2")
    point(en_base, prof.id, 50, "p1", semestre_id=semestre.id, action="encadreur.bienvenue")
    correction = point(
        en_base, prof.id, -10, "c1", semestre_id=semestre.id, action=ACTION_CORRECTION, motif="Doublon de bienvenue."
    )
    return {"ama": ama, "prof": prof, "club": club, "gain": gain, "correction": correction}


@pytest.fixture
def equipe(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    return admin(client, creer_collaborateur, GESTIONNAIRE, double_auth=True)


def test_le_registre_liste_les_lignes_avec_leurs_champs(equipe: Navigateur, lignes: dict[str, Any]) -> None:
    corps = equipe.get(REGISTRE).json()

    assert corps["total"] == 4
    gain = next(ligne for ligne in corps["lignes"] if ligne["id"] == str(lignes["gain"].id))
    assert gain["pseudonyme"] == "Ama Présidente"
    assert gain["role"] == "eleve"
    assert gain["montant"] == 100
    assert gain["points_club"] == 50
    assert gain["club"]["nom"] == "Club Santé Tokoin"
    assert gain["semestre"] == "Semestre en cours"
    assert gain["cle"] == "a1"
    assert gain["est_correction"] is False and gain["annulee"] is False
    correction = next(ligne for ligne in corps["lignes"] if ligne["id"] == str(lignes["correction"].id))
    assert correction["motif"] == "Doublon de bienvenue."
    assert correction["est_correction"] is True


@pytest.mark.parametrize(
    ("filtres", "cles"),
    [
        ({"beneficiaire": "eleve"}, {"a1", "a2"}),
        ({"beneficiaire": "encadreur"}, {"p1", "c1"}),
        ({"correction": "true"}, {"c1"}),
        ({"correction": "false", "beneficiaire": "encadreur"}, {"p1"}),
        ({"action": "encadreur.bienvenue"}, {"p1"}),
        ({"recherche": "ama"}, {"a1", "a2"}),
        ({"recherche": "%"}, set()),
    ],
)
def test_les_filtres_se_combinent(
    equipe: Navigateur, lignes: dict[str, Any], filtres: dict[str, str], cles: set[str]
) -> None:
    corps = equipe.get(REGISTRE, params=filtres).json()

    assert {ligne["cle"] for ligne in corps["lignes"]} == cles
    assert corps["total"] == len(cles)


def test_les_filtres_par_club_et_par_semestre(
    equipe: Navigateur,
    lignes: dict[str, Any],
    semestre: Semestre,  # noqa: F811
) -> None:
    par_club = equipe.get(REGISTRE, params={"club_id": str(lignes["club"].id)}).json()
    par_semestre = equipe.get(REGISTRE, params={"semestre_id": str(semestre.id)}).json()

    assert {ligne["cle"] for ligne in par_club["lignes"]} == {"a1"}
    assert {ligne["cle"] for ligne in par_semestre["lignes"]} == {"a1", "p1", "c1"}


def test_le_filtre_par_dates(equipe: Navigateur, lignes: dict[str, Any]) -> None:
    assert equipe.get(REGISTRE, params={"du": "2000-01-01", "au": "2000-01-31"}).json()["total"] == 0
    assert equipe.get(REGISTRE, params={"du": "2026-02-01", "au": "2026-01-01"}).status_code == 422
    # Les deux bornes sont incluses : une ligne écrite aujourd'hui sort pour du = au = aujourd'hui (UTC).
    jour = datetime.now(UTC).date().isoformat()
    assert equipe.get(REGISTRE, params={"du": jour, "au": jour}).json()["total"] == lignes_total(equipe)


def lignes_total(navigateur: Navigateur) -> int:
    return int(navigateur.get(REGISTRE).json()["total"])


def test_le_registre_est_pagine(equipe: Navigateur, lignes: dict[str, Any]) -> None:
    premiere = equipe.get(REGISTRE, params={"par_page": 3}).json()
    seconde = equipe.get(REGISTRE, params={"par_page": 3, "page": 2}).json()

    assert (premiere["total"], len(premiere["lignes"]), len(seconde["lignes"])) == (4, 3, 1)


def test_aucune_route_ne_modifie_ni_ne_supprime_une_ligne(equipe: Navigateur, lignes: dict[str, Any]) -> None:
    chemin = f"{REGISTRE}/{lignes['gain'].id}"

    for methode in ("put", "patch", "delete"):
        assert getattr(equipe, methode)(chemin).status_code in (404, 405)


def test_le_registre_exige_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any], lignes: dict[str, Any]
) -> None:
    assert admin(client, creer_collaborateur, LECTEUR).get(REGISTRE).status_code == 403


def test_le_registre_exige_le_perimetre_national(
    client: TestClient, creer_collaborateur: Callable[..., Any], lignes: dict[str, Any]
) -> None:
    de_dre = admin(client, creer_collaborateur, LECTEUR, perimetre_dre="kara", double_auth=True)

    assert de_dre.get(REGISTRE).status_code == 403


def test_le_registre_exige_le_droit_points(
    client: TestClient, creer_collaborateur: Callable[..., Any], lignes: dict[str, Any]
) -> None:
    autre = admin(client, creer_collaborateur, {("tableau_de_bord", "consulter")}, double_auth=True)

    assert autre.get(REGISTRE).status_code == 403


# Recherche de bénéficiaires -------------------------------------------------------------------------------------


def test_la_recherche_trouve_un_eleve_par_pseudonyme_et_un_encadreur_par_identifiant(
    equipe: Navigateur, lignes: dict[str, Any]
) -> None:
    eleves = equipe.get(BENEFICIAIRES, params={"q": "présidente"}).json()
    encadreurs = equipe.get(BENEFICIAIRES, params={"q": "prof"}).json()

    assert eleves == [
        {
            "id": str(lignes["ama"].id),
            "role": "eleve",
            "nom_public": "Ama Présidente",
            "identifiant": "ama",
            "club": "Club Santé Tokoin",
            "points_total": 105,
        }
    ]
    assert [(element["identifiant"], element["points_total"]) for element in encadreurs] == [("prof", 40)]


def test_la_recherche_exclut_les_admins_et_borne_le_texte(
    equipe: Navigateur, lignes: dict[str, Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    assert equipe.get(BENEFICIAIRES, params={"q": "equipe"}).json() == []
    assert equipe.get(BENEFICIAIRES, params={"q": "a"}).status_code == 422
    assert equipe.get(BENEFICIAIRES, params={"q": "zzzz"}).json() == []


def test_la_recherche_est_reservee_aux_correcteurs(
    client: TestClient, creer_collaborateur: Callable[..., Any], lignes: dict[str, Any]
) -> None:
    lecteur = admin(client, creer_collaborateur, LECTEUR, double_auth=True)

    assert lecteur.get(BENEFICIAIRES, params={"q": "ama"}).status_code == 403


def test_une_ligne_du_compte_du_club_apparait_et_sannule(
    equipe: Navigateur, lignes: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    """Spec 038 : une ligne sans personne, au nom du club, se lit, se cherche par le club et s'annule."""
    from app.points import service

    club = lignes["club"]
    ligne = en_base(lambda db: service.crediter_club(db, "club.rapport_activite", club.id, "club.rapport_activite:r1"))

    corps = equipe.get(REGISTRE, params={"recherche": "tokoin"}).json()
    (du_club,) = [l for l in corps["lignes"] if l["id"] == str(ligne.id)]
    assert (du_club["role"], du_club["utilisateur_id"], du_club["identifiant"]) == ("club", None, None)
    assert (du_club["montant"], du_club["points_club"], du_club["club"]["nom"]) == (50, 50, "Club Santé Tokoin")
    assert str(ligne.id) in {l["id"] for l in equipe.get(REGISTRE, params={"club_id": str(club.id)}).json()["lignes"]}
    assert equipe.get(REGISTRE, params={"beneficiaire": "eleve"}).json()["total"] == 2

    reponse = equipe.post(f"/api/admin/points/lignes/{ligne.id}/annulation", json={"motif": "Rapport frauduleux."})

    assert reponse.status_code == 201
    assert reponse.json()["montant"] == -50 and reponse.json()["role"] == "club"
