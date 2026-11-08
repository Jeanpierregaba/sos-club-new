"""Rédaction d'un article par son auteur (spec 023) : brouillon, modification, soumission, retrait, suppression,
limites et droits."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.comptes.models import StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from app.moderation.models import Contenu, VersionContenu
from app.referentiel.models import Axe
from tests.conftest import MOT_DE_PASSE, Navigateur

ARTICLES = "/api/mes-articles"

pytestmark = pytest.mark.usefixtures("annuaire")


def connecter(client: Any, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


def champs(**autres: Any) -> dict[str, Any]:
    return {
        "titre": "Le lavage des mains au lycée",
        "chapo": "Notre club a installé trois points d'eau dans la cour.",
        "texte": "## Pourquoi\n\nParce que **les mains** transportent les microbes.\n\n- savon\n- eau",
        "axe_code": "sante-environnement",
        "afficher_club": True,
    } | autres


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> TestClient:
    creer_eleve()
    connecter(client, "eleve1")
    return client


def creer(client: Any, **autres: Any) -> dict[str, Any]:
    reponse = client.post(ARTICLES, json=champs(**autres))
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def test_un_eleve_cree_un_brouillon_le_modifie_puis_le_soumet(eleve: TestClient, en_base: Callable[..., Any]) -> None:
    article = creer(eleve)
    assert (article["etat"], article["en_ligne"], article["soumettable"]) == ("brouillon", False, True)

    modifie = eleve.patch(
        f"{ARTICLES}/{article['id']}", json=champs(titre="Le lavage des mains", version=article["version"])
    )
    assert modifie.status_code == 200, modifie.text
    assert modifie.json()["champs"]["titre"] == "Le lavage des mains"

    soumis = eleve.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": modifie.json()["version"]})

    assert soumis.status_code == 200, soumis.text
    assert (soumis.json()["etat"], soumis.json()["modifiable"]) == ("en_attente", False)
    # Une seule version : le brouillon se modifie en place tant qu'il n'est pas soumis.
    versions = en_base(lambda db: db.scalars(select(VersionContenu))).all()
    assert [(v.numero, v.etat) for v in versions] == [(1, "soumise")]
    assert en_base(lambda db: db.scalar(select(Contenu.dre_code))) == "grand-lome"
    actions = en_base(lambda db: db.scalars(select(JournalAudit.action))).all()
    assert "article_soumis" in actions
    assert eleve.get(ARTICLES).json()["articles"][0]["titre"] == "Le lavage des mains"


def test_un_article_en_attente_ne_se_modifie_pas_mais_se_retire(eleve: TestClient) -> None:
    article = creer(eleve)
    soumis = eleve.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"]}).json()

    bloque = eleve.patch(f"{ARTICLES}/{article['id']}", json=champs(version=soumis["version"]))
    assert bloque.status_code == 409

    retire = eleve.post(f"{ARTICLES}/{article['id']}/retirer", json={"version": soumis["version"]})
    assert retire.status_code == 200, retire.text
    assert (retire.json()["etat"], retire.json()["modifiable"]) == ("brouillon", True)


def test_une_version_perimee_est_refusee(eleve: TestClient) -> None:
    article = creer(eleve)
    eleve.patch(f"{ARTICLES}/{article['id']}", json=champs(titre="Première modification", version=article["version"]))

    perimee = eleve.patch(f"{ARTICLES}/{article['id']}", json=champs(version=article["version"]))
    sans_version = eleve.patch(f"{ARTICLES}/{article['id']}", json=champs())

    assert perimee.status_code == 409
    assert sans_version.status_code == 409


def test_seul_un_brouillon_jamais_soumis_se_supprime(eleve: TestClient, en_base: Callable[..., Any]) -> None:
    brouillon = creer(eleve)
    soumis = creer(eleve, titre="Un second article")
    soumis = eleve.post(f"{ARTICLES}/{soumis['id']}/soumettre", json={"version": soumis["version"]}).json()
    retire = eleve.post(f"{ARTICLES}/{soumis['id']}/retirer", json={"version": soumis["version"]}).json()

    assert retire["supprimable"] is False
    assert eleve.delete(f"{ARTICLES}/{retire['id']}").status_code == 409
    assert eleve.delete(f"{ARTICLES}/{brouillon['id']}").status_code == 204
    assert en_base(lambda db: db.scalar(select(Contenu.id).where(Contenu.id == brouillon["id"]))) is None


def test_trois_articles_en_attente_au_plus(eleve: TestClient) -> None:
    for numero in range(4):
        article = creer(eleve, titre=f"Article numéro {numero}")
        reponse = eleve.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"]})

    assert reponse.status_code == 409
    assert "3 articles en attente" in reponse.json()["detail"]


def test_vingt_brouillons_au_plus(eleve: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.moderation import service

    monkeypatch.setattr(service, "MAX_BROUILLONS", 2)
    creer(eleve)
    creer(eleve)

    assert eleve.post(ARTICLES, json=champs()).status_code == 409


@pytest.mark.parametrize(
    ("champ", "valeur"),
    [
        ("titre", "ab"),
        ("titre", "x" * 121),
        ("titre", "Deux\nlignes"),
        ("chapo", "court"),
        ("texte", ""),
        ("texte", "x" * 20_001),
        ("texte", "Un caractère \x00 interdit"),
        ("axe_code", "INCONNU"),
    ],
)
def test_les_champs_invalides_sont_refuses(eleve: TestClient, champ: str, valeur: str) -> None:
    assert eleve.post(ARTICLES, json=champs(**{champ: valeur})).status_code == 422


def test_un_axe_desactive_reste_accepte_sil_etait_deja_celui_de_larticle(
    eleve: TestClient, en_base: Callable[..., Any]
) -> None:
    article = creer(eleve)
    en_base(lambda db: db.execute(update(Axe).where(Axe.code == "sante-environnement").values(actif=False)))

    garde = eleve.patch(f"{ARTICLES}/{article['id']}", json=champs(titre="Titre modifié", version=article["version"]))
    nouveau = eleve.post(ARTICLES, json=champs())

    assert garde.status_code == 200, garde.text
    assert nouveau.status_code == 422


def test_un_auteur_ne_voit_ni_ne_touche_larticle_dun_autre(
    client: TestClient, creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve()
    creer_eleve("eleve2", "Kofi de Kara", dre="kara")
    connecter(client, "eleve1")
    article = creer(client)

    autre = Navigateur(client)
    connecter(autre, "eleve2")

    assert autre.get(f"{ARTICLES}/{article['id']}").status_code == 404
    assert autre.request("PATCH", f"{ARTICLES}/{article['id']}", json=champs(version=1)).status_code == 404
    assert autre.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": 1}).status_code == 404
    assert autre.delete(f"{ARTICLES}/{article['id']}").status_code == 404
    assert autre.get(ARTICLES).json() == {"articles": []}


def test_un_encadreur_actif_redige_mais_pas_un_encadreur_en_attente(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    creer_encadreur()
    creer_encadreur("encadreur2", etat=EtatVerification.en_attente)
    connecter(client, "encadreur1")
    assert client.post(ARTICLES, json=champs()).status_code == 201

    attente = Navigateur(client)
    connecter(attente, "encadreur2")
    assert attente.post(ARTICLES, json=champs()).status_code == 403
    assert attente.get(ARTICLES).status_code == 403


def test_un_compte_suspendu_ou_un_admin_ne_redige_pas(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    eleve = creer_eleve()
    connecter(client, "eleve1")
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=StatutCompte.suspendu)
        )
    )
    assert client.post(ARTICLES, json=champs()).status_code in {401, 403}

    creer_collaborateur("chef")
    admin = Navigateur(client)
    connecter(admin, "chef")
    assert admin.post(ARTICLES, json=champs()).status_code == 403


def test_il_faut_etre_connecte(client: TestClient) -> None:
    assert client.get(ARTICLES).status_code == 401
    assert client.post(ARTICLES, json=champs()).status_code == 401
