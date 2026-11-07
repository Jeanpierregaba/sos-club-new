"""Lecture publique des articles (spec 023) : rien avant l'approbation, signature sans nom complet, club choisi,
filtre par axe, adresse stable et pagination."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.comptes.models import Utilisateur
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin

PUBLICS = "/api/articles"
ARTICLES = "/api/mes-articles"
FILE = "/api/admin/moderation"
MODERATION = {("moderation", "consulter"), ("moderation", "approuver"), ("moderation", "depublier")}

pytestmark = pytest.mark.usefixtures("annuaire")


def connecter(client: Any, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


def champs(**autres: Any) -> dict[str, Any]:
    return {
        "titre": "Le lavage des mains au lycée",
        "chapo": "Notre club a installé trois points d'eau dans la cour.",
        "texte": "Parce que **les mains** transportent les microbes.",
        "axe_code": "sante-environnement",
        "afficher_club": True,
    } | autres


@pytest.fixture
def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, "moderateur")  # type: ignore[arg-type]
    return navigateur


@pytest.fixture
def auteur(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Navigateur:
    creer_eleve()
    navigateur = Navigateur(client)
    connecter(navigateur, "eleve1")
    return navigateur


def soumettre(auteur: Any, **autres: Any) -> dict[str, Any]:
    article = auteur.post(ARTICLES, json=champs(**autres)).json()
    return auteur.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"]}).json()


def decider(moderateur: Any, contenu_id: str, decision: str, motif: str | None = None) -> Any:
    version = moderateur.get(f"{FILE}/{contenu_id}").json()["version"]
    reponse = moderateur.post(f"{FILE}/{contenu_id}/{decision}", json={"version": version, "motif": motif})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def publier(auteur: Any, moderateur: Any, **autres: Any) -> str:
    article = soumettre(auteur, **autres)
    return str(decider(moderateur, article["id"], "approuver")["adresse"])


def test_rien_nest_public_avant_lapprobation(client: TestClient, auteur: Navigateur, moderateur: Navigateur) -> None:
    auteur.post(ARTICLES, json=champs(titre="Un brouillon"))
    en_attente = soumettre(auteur, titre="En attente")
    a_corriger = soumettre(auteur, titre="À corriger")
    decider(moderateur, a_corriger["id"], "corriger", "Précise.")
    refuse = soumettre(auteur, titre="Refusé")
    decider(moderateur, refuse["id"], "refuser", "Non.")

    assert client.get(PUBLICS).json() == {"articles": [], "page": 1, "pages": 1, "total": 0}
    for titre in ("un-brouillon", "en-attente", "a-corriger", "refuse"):
        assert client.get(f"{PUBLICS}/{titre}").status_code == 404
    assert en_attente["adresse"] is None


def test_un_article_approuve_se_lit_avec_la_signature_de_leleve(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    adresse = publier(auteur, moderateur)

    liste = client.get(PUBLICS).json()
    article = client.get(f"{PUBLICS}/{adresse}").json()

    assert [a["adresse"] for a in liste["articles"]] == [adresse]
    assert article["titre"] == "Le lavage des mains au lycée"
    assert article["texte"] == "Parce que **les mains** transportent les microbes."
    assert article["axe"] == {"code": "sante-environnement", "libelle": article["axe"]["libelle"]}
    assert article["signature"] == {"profil": "eleve", "nom": "Ama du Golfe", "club": None, "fonction": None}
    # Ni nom, ni prénom, ni identifiant, ni établissement de l'élève dans la réponse publique.
    brut = client.get(f"{PUBLICS}/{adresse}").text
    for interdit in ("Kodjo", "eleve1", "auteur", "dre_code", "etablissement"):
        assert interdit not in brut
    assert set(article) == {"adresse", "titre", "chapo", "texte", "axe", "signature", "publie_le"}


def test_le_club_napparait_que_si_leleve_la_choisi(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    moderateur: Navigateur,
) -> None:
    president = creer_eleve("president", "La Présidente")
    creer_club(president, nom="Club Santé du Lycée")
    navigateur = Navigateur(client)
    connecter(navigateur, "president")

    avec = publier(navigateur, moderateur, titre="Avec mon club")
    sans = publier(navigateur, moderateur, titre="Sans mon club", afficher_club=False)

    assert client.get(f"{PUBLICS}/{avec}").json()["signature"]["club"] == "Club Santé du Lycée"
    assert client.get(f"{PUBLICS}/{sans}").json()["signature"]["club"] is None


def test_un_encadreur_signe_par_son_prenom_linitiale_et_sa_fonction(
    client: TestClient, creer_encadreur: Callable[..., Any], moderateur: Navigateur
) -> None:
    creer_encadreur()
    navigateur = Navigateur(client)
    connecter(navigateur, "encadreur1")

    adresse = publier(navigateur, moderateur)

    article = client.get(f"{PUBLICS}/{adresse}")
    assert article.json()["signature"] == {
        "profil": "encadreur",
        "nom": "Jean K.",
        "club": None,
        "fonction": "enseignant",
    }
    assert "Kodjo" not in article.text


def test_une_revision_en_attente_ne_change_pas_la_version_publique(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    adresse = publier(auteur, moderateur)
    article_id = auteur.get(ARTICLES).json()["articles"][0]["id"]
    actuel = auteur.get(f"{ARTICLES}/{article_id}").json()
    modifie = auteur.request(
        "PATCH",
        f"{ARTICLES}/{article_id}",
        json=champs(titre="Titre révisé", texte="<script>alert(1)</script>") | {"version": actuel["version"]},
    ).json()
    auteur.post(f"{ARTICLES}/{article_id}/soumettre", json={"version": modifie["version"]})

    pendant = client.get(f"{PUBLICS}/{adresse}").json()
    assert (pendant["titre"], pendant["texte"]) == (
        "Le lavage des mains au lycée",
        "Parce que **les mains** transportent les microbes.",
    )

    decider(moderateur, article_id, "approuver")
    apres = client.get(f"{PUBLICS}/{adresse}").json()
    # L'adresse reste ; le texte est rendu tel quel, et le site ne l'interprète jamais comme du HTML.
    assert (apres["titre"], apres["texte"]) == ("Titre révisé", "<script>alert(1)</script>")


def test_un_article_depublie_disparait(client: TestClient, auteur: Navigateur, moderateur: Navigateur) -> None:
    adresse = publier(auteur, moderateur)
    article_id = auteur.get(ARTICLES).json()["articles"][0]["id"]

    decider(moderateur, article_id, "depublier", "Signalé.")

    assert client.get(f"{PUBLICS}/{adresse}").status_code == 404
    assert client.get(PUBLICS).json()["total"] == 0


def test_la_liste_se_filtre_par_axe_et_se_pagine(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.articles import public

    monkeypatch.setattr(public, "PAR_PAGE", 2)
    publier(auteur, moderateur, titre="Premier", axe_code="genie-imhotep")
    publier(auteur, moderateur, titre="Deuxième")
    publier(auteur, moderateur, titre="Troisième")

    page1 = client.get(PUBLICS).json()
    page2 = client.get(PUBLICS, params={"page": 2}).json()
    imhotep = client.get(PUBLICS, params={"axe": "genie-imhotep"}).json()

    assert ([a["titre"] for a in page1["articles"]], page1["pages"], page1["total"]) == (
        ["Troisième", "Deuxième"],
        2,
        3,
    )
    assert [a["titre"] for a in page2["articles"]] == ["Premier"]
    assert [a["titre"] for a in imhotep["articles"]] == ["Premier"]
    assert client.get(PUBLICS, params={"page": 0}).status_code == 422
