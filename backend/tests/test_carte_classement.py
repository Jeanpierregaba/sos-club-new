"""Carte « Partager mon classement » (spec 044) : ce que l'image dit, et surtout ce qu'elle ne dit jamais.

Écrits avant le code : un élève est mineur, rien de sensible ne sort de la plateforme (docs/RULES.md)."""

import io
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import func, select, update

from app.comptes.models import Role, Utilisateur
from app.points.carte_classement import CarteClassement, Vue, textes
from app.points.models import MouvementPoints, Semestre
from tests.espace_club import connecter
from tests.test_classements import affilier, point, rattacher, renommer, semestre  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

CARTE = "/api/classements/moi/carte.png"


@pytest.fixture
def reseau(
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,  # noqa: F811
) -> dict[str, Any]:
    """Le réseau des tests des classements : Ama présidente et Kofi au club de Tokoin, un encadreur, Yao à Kara."""
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


def _carte(**champs: Any) -> CarteClassement:
    valeurs: dict[str, Any] = {
        "nom": "Kofi Membre",
        "niveau": "national",
        "dre": "Grand Lomé",
        "club": "Club Santé Tokoin",
        "periode": "semestre",
        "semestre": "Semestre en cours",
        "rang": 3,
        "classes": 3,
        "points": 100,
        "le": datetime(2026, 11, 19, tzinfo=UTC),
    }
    return CarteClassement(**(valeurs | champs))


# Les textes de la carte : une fonction pure ---------------------------------------------------------------------


def test_les_textes_de_la_carte_nationale_du_semestre() -> None:
    lignes = textes(_carte(), afficher_club=False)
    tout = " ".join(lignes)

    assert "Kofi Membre" in lignes
    assert "3ᵉ" in tout and "sur 3 classés" in tout
    assert "100 points" in tout
    assert "National" in tout and "Semestre en cours" in tout
    assert "Classement provisoire au 19 novembre 2026" in tout
    assert "Clubs Santé SOS Docteur TV" in tout
    assert "Club Santé Tokoin" not in tout


def test_le_club_napparait_que_si_on_le_choisit() -> None:
    assert "Club Santé Tokoin" in " ".join(textes(_carte(), afficher_club=True))
    assert "Club Santé Tokoin" not in " ".join(textes(_carte(club=None), afficher_club=True))


def test_les_vues_dre_club_et_historique() -> None:
    assert "DRE Grand Lomé" in " ".join(textes(_carte(niveau="dre"), afficher_club=False))
    assert "Club" in " ".join(textes(_carte(niveau="club"), afficher_club=False))
    historique = " ".join(textes(_carte(periode="historique", semestre=None), afficher_club=False))
    assert "Depuis le début" in historique
    assert "provisoire" not in historique


def test_le_premier_est_premier() -> None:
    assert "1ᵉʳ" in " ".join(textes(_carte(rang=1), afficher_club=False))


# La route -------------------------------------------------------------------------------------------------------


def _image(reponse: Any) -> Image.Image:
    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["content-type"] == "image/png"
    assert "no-store" in reponse.headers["cache-control"]
    return Image.open(io.BytesIO(reponse.content))


def test_un_eleve_obtient_sa_carte_png(client: TestClient, reseau: dict[str, Any]) -> None:
    image = _image(connecter(client, "kofi").get(CARTE)).convert("RGB")

    assert image.size == (1080, 1350)
    # Le logo est posé sur une pastille blanche au milieu du bandeau bleu.
    assert image.getpixel((540, 48)) == (255, 255, 255)
    assert image.getpixel((20, 20)) != (255, 255, 255)


@pytest.mark.parametrize("niveau", ["national", "dre", "club"])
@pytest.mark.parametrize("periode", ["semestre", "historique"])
def test_chaque_vue_produit_une_carte(client: TestClient, reseau: dict[str, Any], niveau: str, periode: str) -> None:
    reponse = connecter(client, "kofi").get(CARTE, params={"niveau": niveau, "periode": periode, "club": 1})

    _image(reponse)


def test_les_donnees_de_la_carte(client: TestClient, reseau: dict[str, Any], en_base: Callable[..., Any]) -> None:
    from app.points.classements import Periode, carte_personnelle

    kofi = reseau["kofi"]

    async def lire(db: Any, niveau: Vue) -> CarteClassement:
        utilisateur = await db.get(Utilisateur, kofi.id)
        return await carte_personnelle(db, utilisateur, niveau, Periode.semestre)

    national = en_base(lambda db: lire(db, Vue.national))
    dre = en_base(lambda db: lire(db, Vue.dre))
    club = en_base(lambda db: lire(db, Vue.club))

    assert (national.nom, national.rang, national.classes, national.points) == ("Kofi Membre", 3, 3, 100)
    assert (dre.rang, dre.classes, dre.dre) == (2, 2, "Grand Lomé")
    assert (club.rang, club.classes, club.club) == (2, 2, "Club Santé Tokoin")


def test_un_encadreur_est_nomme_par_son_prenom_et_son_initiale(
    reseau: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    from app.points.classements import Periode, carte_personnelle

    async def lire(db: Any) -> CarteClassement:
        return await carte_personnelle(db, await db.get(Utilisateur, reseau["prof"].id), Vue.national, Periode.semestre)

    carte = en_base(lire)
    tout = " ".join(textes(carte, afficher_club=True))

    assert carte.nom == "Komla A."
    assert "Adjo" not in tout


def test_aucune_donnee_sensible_dans_les_textes(reseau: dict[str, Any], en_base: Callable[..., Any]) -> None:
    from app.points.classements import Periode, carte_personnelle

    async def lire(db: Any) -> tuple[CarteClassement, Utilisateur]:
        utilisateur = await db.get(Utilisateur, reseau["kofi"].id)
        return await carte_personnelle(db, utilisateur, Vue.national, Periode.semestre), utilisateur

    carte, utilisateur = en_base(lire)
    tout = " ".join(textes(carte, afficher_club=True))

    for sensible in (utilisateur.prenom, utilisateur.nom, utilisateur.identifiant, str(utilisateur.id), "Lycée"):
        assert sensible not in tout


# Refus ----------------------------------------------------------------------------------------------------------


def test_une_personne_sans_point_nest_pas_classee(
    client: TestClient, reseau: dict[str, Any], creer_eleve: Callable[..., Any]
) -> None:
    creer_eleve("nouveau", "Nouveau Venu")

    assert connecter(client, "nouveau").get(CARTE).status_code == 404


def test_la_vue_club_exige_un_club(client: TestClient, reseau: dict[str, Any]) -> None:
    assert connecter(client, "yao").get(CARTE, params={"niveau": "club"}).status_code == 422


def test_sans_semestre_en_cours_seul_lhistorique(
    client: TestClient, reseau: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    en_base(lambda db: db.execute(update(Semestre).values(debut=date(2019, 9, 1), fin=date(2020, 1, 31))))
    navigateur = connecter(client, "kofi")

    assert navigateur.get(CARTE).status_code == 409
    _image(navigateur.get(CARTE, params={"periode": "historique"}))


def test_les_parametres_invalides_sont_refuses(client: TestClient, reseau: dict[str, Any]) -> None:
    navigateur = connecter(client, "kofi")

    assert navigateur.get(CARTE, params={"niveau": "monde"}).status_code == 422
    assert navigateur.get(CARTE, params={"periode": "annee"}).status_code == 422


def test_visiteur_admin_et_anonyme_sont_refuses(
    client: TestClient,
    reseau: dict[str, Any],
    creer_utilisateur: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
) -> None:
    assert client.get(CARTE).status_code == 401
    creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg", email_confirme_le=datetime.now(UTC))
    assert connecter(client, "passant").get(CARTE).status_code == 403


def test_la_carte_ne_rapporte_aucun_point(
    client: TestClient, reseau: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    def compter() -> int:
        return int(en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints))))

    avant = compter()
    _image(connecter(client, "kofi").get(CARTE))

    assert compter() == avant


def test_le_nombre_de_cartes_est_limite(
    client: TestClient, reseau: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "cartes_classement_max", 2)
    navigateur = connecter(client, "kofi")

    assert [navigateur.get(CARTE).status_code for _ in range(3)] == [200, 200, 429]
