"""Actualités du club (spec 026) : le président rédige au nom du club, rien n'est public avant l'approbation,
la signature est celle du club, aucun point n'est crédité, et la passation transmet la main.

Écrits avant le code : rien de public sans modération, droits dans l'API (docs/RULES.md, docs/TESTING.md)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.points.models import MouvementPoints
from tests.espace_club import ACTUALITES, champs_actualite, connecter, decider, espace, passer_la_main, scene
from tests.photos import image

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def club(
    client: TestClient,
    creer_eleve: Callable[..., Any],
    creer_club: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    return scene(client, creer_eleve, creer_club, creer_encadreur, creer_collaborateur, en_base)


def soumettre(club: dict[str, Any], **autres: Any) -> dict[str, Any]:
    actualite = club["nav_president"].post(ACTUALITES, json=champs_actualite(**autres))
    assert actualite.status_code == 201, actualite.text
    corps = actualite.json()
    soumise = club["nav_president"].post(f"{ACTUALITES}/{corps['id']}/soumettre", json={"version": corps["version"]})
    assert soumise.status_code == 200, soumise.text
    return dict(soumise.json())


def publier(club: dict[str, Any], **autres: Any) -> str:
    actualite = soumettre(club, **autres)
    approuvee = decider(club["admin"], actualite["id"], "approuver")
    assert approuvee.status_code == 200, approuvee.text
    return str(approuvee.json()["adresse"])


def test_le_president_redige_un_brouillon_au_nom_du_club(club: dict[str, Any]) -> None:
    reponse = club["nav_president"].post(ACTUALITES, json=champs_actualite())

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["etat"] == "brouillon"
    assert [a["id"] for a in club["nav_president"].get(ACTUALITES).json()["articles"]] == [reponse.json()["id"]]
    # Une actualité n'est pas un article personnel.
    assert club["nav_president"].get("/api/mes-articles").json()["articles"] == []


def test_rien_nest_public_avant_lapprobation(client: TestClient, club: dict[str, Any]) -> None:
    actualite = soumettre(club)

    assert client.get("/api/articles").json()["total"] == 0
    assert client.get(f"/api/clubs/{club['club'].id}").json()["actualites"] == []
    assert actualite["adresse"] is None


def test_une_actualite_approuvee_est_signee_du_club_sans_point(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    adresse = publier(club)

    article = client.get(f"/api/articles/{adresse}").json()
    liste = client.get("/api/articles").json()["articles"]
    fiche = client.get(f"/api/clubs/{club['club'].id}").json()

    assert article["nature"] == "actualite"
    assert article["signature"] == {"profil": "club", "nom": "Club Santé du Lycée", "club": None, "fonction": None}
    assert [a["nature"] for a in liste] == ["actualite"]
    assert [a["adresse"] for a in fiche["actualites"]] == [adresse]
    brut = client.get(f"/api/articles/{adresse}").text
    for interdit in ("Zoé", "president", "Kodjo"):
        assert interdit not in brut
    gains = en_base(lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.cle.like("actualite:%"))))
    assert list(gains) == []
    vue = club["nav_membre"].get(espace(club["club"].id)).json()
    assert vue["indicateurs"]["actualites"] == 1
    assert [a["adresse"] for a in vue["actualites"]] == [adresse]


def test_un_article_personnel_garde_sa_nature(client: TestClient, club: dict[str, Any]) -> None:
    article = club["nav_membre"].post("/api/mes-articles", json=champs_actualite(titre="Mon article")).json()
    club["nav_membre"].post(f"/api/mes-articles/{article['id']}/soumettre", json={"version": article["version"]})
    decider(club["admin"], article["id"], "approuver")

    assert [a["nature"] for a in client.get("/api/articles").json()["articles"]] == ["article"]


def test_le_president_ajoute_une_photo(club: dict[str, Any]) -> None:
    actualite = club["nav_president"].post(ACTUALITES, json=champs_actualite()).json()

    reponse = club["nav_president"].post(
        f"{ACTUALITES}/{actualite['id']}/photos",
        data={"version": str(actualite["version"]), "attestation": "true"},
        files={"fichier": ("photo.jpg", image(), "image/jpeg")},
    )

    assert reponse.status_code == 200, reponse.text
    assert len(reponse.json()["photos"]) == 1


def test_le_suivi_du_president_montre_ses_actualites(club: dict[str, Any]) -> None:
    actualite = soumettre(club)

    suivi = club["nav_president"].get(espace(club["club"].id)).json()["suivi"]

    assert [(a["id"], a["etat"]) for a in suivi["actualites"]] == [(actualite["id"], "en_attente")]


def test_apres_une_passation_le_nouveau_president_gere_les_actualites(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    brouillon = club["nav_president"].post(ACTUALITES, json=champs_actualite()).json()
    adresse = publier(club, titre="Déjà publiée")

    passer_la_main(en_base, club["admin"], club["club"], club["membre"])

    ancien = club["nav_president"]
    assert ancien.get(f"{ACTUALITES}/{brouillon['id']}").status_code in {403, 404}
    assert ancien.post(ACTUALITES, json=champs_actualite()).status_code in {403, 404}
    nouveau = connecter(client, "membre")
    assert nouveau.get(f"{ACTUALITES}/{brouillon['id']}").status_code == 200
    assert len(nouveau.get(ACTUALITES).json()["articles"]) == 2
    # La signature reste celle du club.
    assert client.get(f"/api/articles/{adresse}").json()["signature"]["nom"] == "Club Santé du Lycée"


def test_lapprobation_previent_le_president_en_place(club: dict[str, Any], en_base: Callable[..., Any]) -> None:
    from app.notifications.models import Notification

    actualite = soumettre(club)
    decider(club["admin"], actualite["id"], "approuver")

    avis = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == club["president"].id))
    )
    assert [(a.type, a.lien) for a in avis] == [("actualite_approuve", "/mon-club")]


def test_une_actualite_refusee_ou_depubliee_nest_pas_publique(client: TestClient, club: dict[str, Any]) -> None:
    refusee = soumettre(club, titre="Refusée")
    decider(club["admin"], refusee["id"], "refuser", "Hors sujet.")
    adresse = publier(club, titre="Dépubliée")
    article_id = next(
        a["id"] for a in club["nav_president"].get(ACTUALITES).json()["articles"] if a["titre"] == "Dépubliée"
    )
    decider(club["admin"], article_id, "depublier", "Retirée.")

    assert client.get("/api/articles").json()["total"] == 0
    assert client.get(f"/api/articles/{adresse}").status_code == 404
    assert client.get(f"/api/clubs/{club['club'].id}").json()["actualites"] == []


def test_un_article_personnel_du_president_nest_pas_une_actualite(club: dict[str, Any]) -> None:
    article = club["nav_president"].post("/api/mes-articles", json=champs_actualite(titre="Perso")).json()

    assert club["nav_president"].get(ACTUALITES).json()["articles"] == []
    assert club["nav_president"].get(f"{ACTUALITES}/{article['id']}").status_code == 404


def test_lancien_president_ne_soumet_ni_ne_touche_aux_photos(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    brouillon = club["nav_president"].post(ACTUALITES, json=champs_actualite()).json()
    photo = (
        club["nav_president"]
        .post(
            f"{ACTUALITES}/{brouillon['id']}/photos",
            data={"version": str(brouillon["version"]), "attestation": "true"},
            files={"fichier": ("photo.jpg", image(), "image/jpeg")},
        )
        .json()
    )
    photo_id = photo["photos"][0]["id"]
    passer_la_main(en_base, club["admin"], club["club"], club["membre"])

    ancien = club["nav_president"]
    assert ancien.post(f"{ACTUALITES}/{brouillon['id']}/soumettre", json={"version": photo["version"]}).status_code in {
        403,
        404,
    }
    assert ancien.get(f"{ACTUALITES}/{brouillon['id']}/photos/{photo_id}/vignette").status_code == 404
    nouveau = connecter(client, "membre")
    assert nouveau.get(f"{ACTUALITES}/{brouillon['id']}/photos/{photo_id}/vignette").status_code == 200


def test_une_decision_apres_la_passation_previent_le_nouveau_president(
    club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    from app.notifications.models import Notification

    actualite = soumettre(club)
    passer_la_main(en_base, club["admin"], club["club"], club["membre"])

    assert decider(club["admin"], actualite["id"], "approuver").status_code == 200

    avis = en_base(lambda db: db.scalars(select(Notification).where(Notification.type == "actualite_approuve")))
    assert [a.utilisateur_id for a in avis] == [club["membre"].id]


def test_une_photo_dactualite_nest_pas_publique_avant_lapprobation(client: TestClient, club: dict[str, Any]) -> None:
    brouillon = club["nav_president"].post(ACTUALITES, json=champs_actualite()).json()
    photo = (
        club["nav_president"]
        .post(
            f"{ACTUALITES}/{brouillon['id']}/photos",
            data={"version": str(brouillon["version"]), "attestation": "true"},
            files={"fichier": ("photo.jpg", image(), "image/jpeg")},
        )
        .json()
    )
    photo_id = photo["photos"][0]["id"]
    club["nav_president"].post(f"{ACTUALITES}/{brouillon['id']}/soumettre", json={"version": photo["version"]})

    adresse = decider_et_adresse(club, brouillon["id"])
    assert client.get(f"/api/articles/{adresse}/photos/{photo_id}/vignette").status_code == 200


def decider_et_adresse(club: dict[str, Any], contenu_id: str) -> str:
    # Avant l'approbation, aucune adresse n'existe : rien à lire publiquement.
    assert club["admin"].get(f"/api/admin/moderation/{contenu_id}").json()["adresse"] is None
    return str(decider(club["admin"], contenu_id, "approuver").json()["adresse"])
