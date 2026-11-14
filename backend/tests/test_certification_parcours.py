"""« Ma certification » et le PDF du certificat (spec 029) : réservés au joueur, et le PDF à son seul titulaire."""

import io
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import update

from app.bibliotheque.models import CategorieRessource, EtatRessource
from app.certification.models import Certificat, EtatCertificat
from app.comptes.models import StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from app.quiz.models import EtatQuiz, Quiz
from tests.bibliotheque import creer_ressource
from tests.certification import CERTIFICATION, acquerir, certificats, creer_parcours, mettre_a_jour
from tests.conftest import connecter_admin
from tests.quiz import Horloge, connecter, creer_quiz, figer_horloge, lancer

PDF = f"{CERTIFICATION}/certificat.pdf"


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama")
    connecter(client, "ama")
    return utilisateur


def etats(corps: dict[str, Any]) -> list[str]:
    return [p["etat"] for p in corps["places"]]


def test_ma_certification_montre_les_20_places_dans_lordre(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1, 2, 3, 5])
    acquerir(en_base, eleve, quiz, [1])

    corps = client.get(CERTIFICATION).json()

    assert [p["place"] for p in corps["places"]] == list(range(1, 21))
    assert etats(corps)[:6] == ["reussie", "ouverte", "verrouillee", "bientot", "verrouillee", "bientot"]
    assert corps["reussies"] == 1
    assert corps["places"][1]["titre"] == "Place 2"
    # Spec 034 : aucun plafond quotidien, 10 questions et 10/10 pour valider.
    assert corps["places"][1]["tentatives_restantes"] is None
    assert (corps["nb_questions"], corps["seuil"]) == (10, 10)
    assert [(p["thematique"], p["thematique_nom"]) for p in corps["places"][3:5]] == [
        (1, "Ambassadeur Santé Junior"),
        (2, "Pair Éducateur Santé et Citoyenneté"),
    ]


def test_ma_certification_montre_les_badges_et_leurs_paliers(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    quiz = creer_parcours(en_base, places=[1, 2, 3, 4])
    acquerir(en_base, eleve, quiz, [1, 2, 3, 4])

    # L'ouverture de la page délivre ce qui est dû (rattrapage).
    corps = client.get(CERTIFICATION).json()

    assert [(b["nom"], b["palier"]) for b in corps["badges"]] == [
        ("Ambassadeur Santé Junior", 4),
        ("Pair Éducateur Santé et Citoyenneté", 8),
        ("Sentinelle de la Prévention", 12),
        ("Champion de la Santé et EVSS", 16),
        ("Maître Génie Imhotep", 20),
    ]
    assert [b["obtenu_le"] is not None for b in corps["badges"]] == [True, False, False, False, False]
    assert corps["certificat"] is None


def test_le_fascicule_relie_est_propose_sil_est_publie(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    publie = creer_ressource(en_base, categorie=CategorieRessource.fascicule, titre="Fascicule 1")
    retire = creer_ressource(
        en_base, categorie=CategorieRessource.fascicule, titre="Fascicule 2", etat=EtatRessource.depublie
    )
    creer_quiz(en_base, titre="Place 1", place=1, ressource_id=publie.id)
    creer_quiz(en_base, titre="Place 2", place=2, ressource_id=retire.id)

    places = client.get(CERTIFICATION).json()["places"]

    assert places[0]["fascicule"] == {"id": str(publie.id), "titre": "Fascicule 1"}
    assert places[1]["fascicule"] is None


def test_une_partie_en_cours_est_signalee(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1])
    etat = lancer(client, quiz[1])

    assert client.get(CERTIFICATION).json()["places"][0]["tentative_en_cours"] == etat["tentative_id"]


def test_une_place_reussie_sur_un_quiz_retire_reste_reussie(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    quiz = creer_parcours(en_base, places=[1, 2])
    acquerir(en_base, eleve, quiz, [1])
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == quiz[1].id).values(etat=EtatQuiz.depublie)))

    places = client.get(CERTIFICATION).json()["places"]

    assert (places[0]["etat"], places[0]["quiz_id"]) == ("reussie", None)
    assert places[1]["etat"] == "ouverte"


def test_le_certificat_obtenu_apparait(client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    quiz = creer_parcours(en_base)
    acquerir(en_base, eleve, quiz, range(1, 21))

    corps = client.get(CERTIFICATION).json()

    assert corps["reussies"] == 20
    assert corps["certificat"]["etat"] == "valide"
    assert corps["certificat"]["numero"] == certificats(en_base, eleve.id)[0].numero


# Droits -----------------------------------------------------------------------------------------------------------


def test_un_visiteur_est_refuse(client: TestClient) -> None:
    assert client.get(CERTIFICATION).status_code == 401
    assert client.get(PDF).status_code == 401


def test_un_eleve_suspendu_est_refuse(client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=StatutCompte.suspendu)
        )
    )

    assert client.get(CERTIFICATION).status_code in (401, 403)


def test_un_encadreur_non_verifie_est_refuse(client: TestClient, creer_encadreur: Callable[..., Utilisateur]) -> None:
    creer_encadreur("kofi", etat=EtatVerification.en_attente)
    connecter(client, "kofi")

    assert client.get(CERTIFICATION).status_code == 403


def test_un_collaborateur_ne_suit_pas_le_parcours(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur("chef", droits={("quiz", "consulter")})
    connecter_admin(client, "chef")

    assert client.get(CERTIFICATION).status_code == 403


# Le PDF -----------------------------------------------------------------------------------------------------------


def certifier(en_base: Callable[..., Any], joueur: Utilisateur) -> Certificat:
    acquerir(en_base, joueur, creer_parcours(en_base), range(1, 21))
    mettre_a_jour(en_base, joueur)
    return certificats(en_base, joueur.id)[0]


def test_le_titulaire_telecharge_son_certificat(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    certificat = certifier(en_base, eleve)

    reponse = client.get(PDF)

    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "application/pdf"
    assert reponse.headers["cache-control"] == "no-store"
    assert certificat.numero in reponse.headers["content-disposition"]
    texte = PdfReader(io.BytesIO(reponse.content)).pages[0].extract_text()
    assert "Jean Kodjo" in texte
    assert "Certificat Génie Imhotep" in texte
    assert certificat.numero in texte
    assert f"/certificats/{certificat.numero}" in texte


def test_le_pdf_ecrit_les_lettres_ewe_et_kabiye(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(prenom="Kɔfi", nom="Agbɛnyo Ŋutsu-Ɖoʋi")
        )
    )
    certifier(en_base, eleve)

    texte = PdfReader(io.BytesIO(client.get(PDF).content)).pages[0].extract_text()

    assert "Kɔfi Agbɛnyo Ŋutsu-Ɖoʋi" in texte


def test_le_titulaire_choisit_de_montrer_son_club(
    client: TestClient, eleve: Utilisateur, creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_club(eleve, nom="Club Santé de Tokoin")
    certificat = certifier(en_base, eleve)
    assert client.get(CERTIFICATION).json()["certificat"] | {"delivre_le": None} == {
        "numero": certificat.numero,
        "etat": "valide",
        "delivre_le": None,
        "club": "Club Santé de Tokoin",
        "afficher_club": False,
    }

    reponse = client.put(f"{CERTIFICATION}/club", json={"afficher": True})

    assert reponse.status_code == 200
    assert reponse.json()["afficher_club"] is True
    assert client.get(f"/api/certificats/{certificat.numero}").json()["titulaire"]["club"] == "Club Santé de Tokoin"
    client.put(f"{CERTIFICATION}/club", json={"afficher": False})
    assert client.get(f"/api/certificats/{certificat.numero}").json()["titulaire"]["club"] is None


def test_choisir_son_club_sans_certificat_repond_404(client: TestClient, eleve: Utilisateur) -> None:
    assert client.put(f"{CERTIFICATION}/club", json={"afficher": True}).status_code == 404


def test_sans_certificat_le_pdf_repond_404(client: TestClient, eleve: Utilisateur) -> None:
    assert client.get(PDF).status_code == 404


def test_un_certificat_revoque_ne_se_telecharge_plus(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    certifier(en_base, eleve)
    en_base(
        lambda db: db.execute(
            update(Certificat).values(etat=EtatCertificat.revoque, motif="Erreur.", decide_le=Certificat.delivre_le)
        )
    )

    assert client.get(PDF).status_code == 404


def test_un_autre_compte_ne_recoit_jamais_le_certificat_dun_autre(
    client: TestClient,
    eleve: Utilisateur,
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    certifier(en_base, eleve)
    creer_eleve("kossi", affiche="Kossi du Plateau")
    connecter(client, "kossi")
    assert client.get(PDF).status_code == 404

    creer_collaborateur("chef", droits={("quiz", "consulter"), ("quiz", "depublier")})
    connecter_admin(client, "chef")
    assert client.get(PDF).status_code == 404
