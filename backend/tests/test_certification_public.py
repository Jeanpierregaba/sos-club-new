"""Vérification publique d'un certificat (spec 029) : l'état et le titulaire, jamais son nom complet, son
identifiant ni son établissement (RULES)."""

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.certification.models import Certificat, EtatCertificat
from app.comptes.models import Utilisateur
from tests.certification import acquerir, certificats, creer_parcours, mettre_a_jour

PUBLIC = "/api/certificats"


def certifier(en_base: Callable[..., Any], joueur: Utilisateur) -> Certificat:
    acquerir(en_base, joueur, creer_parcours(en_base), range(1, 13))
    mettre_a_jour(en_base, joueur)
    return certificats(en_base, joueur.id)[0]


def test_un_certificat_deleve_montre_son_pseudonyme_et_son_club(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    eleve = creer_eleve("ama", affiche="Ama du Golfe")
    creer_club(eleve, nom="Club Santé du Lycée de Tokoin")
    certificat = certifier(en_base, eleve)

    reponse = client.get(f"{PUBLIC}/{certificat.numero}")

    assert reponse.status_code == 200
    assert reponse.headers["cache-control"] == "no-store"
    corps = reponse.json()
    assert corps["etat"] == "valide"
    assert corps["titulaire"] == {
        "type": "eleve",
        "pseudonyme": "Ama du Golfe",
        "club": "Club Santé du Lycée de Tokoin",
    }
    assert corps["remplace_par"] is None
    # Ni nom réel, ni identifiant, ni établissement.
    contenu = reponse.text
    assert "Kodjo" not in contenu and "Jean" not in contenu
    assert str(eleve.id) not in contenu
    assert not {"utilisateur_id", "etablissement", "etablissement_id", "id"} & corps.keys()


def test_un_eleve_sans_club_napparait_que_par_son_pseudonyme(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("ama", affiche="Ama du Golfe")
    certificat = certifier(en_base, eleve)

    corps = client.get(f"{PUBLIC}/{certificat.numero}").json()

    assert corps["titulaire"] == {"type": "eleve", "pseudonyme": "Ama du Golfe", "club": None}


def test_un_certificat_dencadreur_montre_son_prenom_son_initiale_et_sa_fonction(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = creer_encadreur("kofi")
    certificat = certifier(en_base, encadreur)

    corps = client.get(f"{PUBLIC}/{certificat.numero}").json()

    assert corps["titulaire"] == {"type": "encadreur", "prenom": "Jean", "initiale": "K.", "fonction": "enseignant"}
    assert "Kodjo" not in client.get(f"{PUBLIC}/{certificat.numero}").text


def test_un_numero_recopie_en_minuscules_est_reconnu(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    certificat = certifier(en_base, creer_eleve("ama"))

    assert client.get(f"{PUBLIC}/{certificat.numero.lower()}").status_code == 200


def test_un_numero_inconnu_ou_mal_forme_repond_404(client: TestClient) -> None:
    assert client.get(f"{PUBLIC}/GI-0000-0000-0000").status_code == 404
    assert client.get(f"{PUBLIC}/pas-un-numero").status_code == 404
    assert client.get(f"{PUBLIC}/GI-IIII-OOOO-UUUU").status_code == 404


def test_un_certificat_revoque_est_annonce_revoque(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    certificat = certifier(en_base, creer_eleve("ama"))
    en_base(
        lambda db: db.execute(
            update(Certificat).values(
                etat=EtatCertificat.revoque, motif="Fraude avérée.", decide_le=Certificat.delivre_le
            )
        )
    )

    corps = client.get(f"{PUBLIC}/{certificat.numero}").json()

    assert corps["etat"] == "revoque"
    # Le motif reste interne.
    assert "motif" not in corps
    assert "Fraude" not in client.get(f"{PUBLIC}/{certificat.numero}").text
