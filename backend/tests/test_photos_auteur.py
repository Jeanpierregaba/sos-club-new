"""Photos d'un article par son auteur (spec 024) : envoi, attestation, limites, couverture, légende, ordre,
retrait, versions, aperçu de modération."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from app.comptes.models import Utilisateur
from app.moderation.models import Photo, VersionPhoto
from tests.conftest import Navigateur, connecter_admin
from tests.photos import (
    ARTICLES,
    FILE,
    MODERATION,
    ajouter,
    connecter,
    creer_article,
    decider,
    envoyer,
    image,
    soumettre,
)

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def auteur(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Navigateur:
    creer_eleve()
    navigateur = Navigateur(client)
    connecter(navigateur, "eleve1")
    return navigateur


@pytest.fixture
def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, "moderateur")  # type: ignore[arg-type]
    return navigateur


def fichiers(dossier: Path) -> list[str]:
    return sorted(p.name for p in (dossier / "photos").glob("*")) if (dossier / "photos").exists() else []


def test_une_photo_attestee_est_enregistree_avec_sa_vignette(
    auteur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)

    resultat = ajouter(auteur, article["id"], contenu=image(taille=(3000, 2000)))

    (photo,) = resultat["photos"]
    assert (photo["largeur"], photo["hauteur"], photo["couverture"]) == (1600, 1067, True)
    assert photo["legende"] == "Les élèves au point d'eau"
    assert len(fichiers(dossier_fichiers)) == 2
    enregistree = en_base(lambda db: db.scalar(select(Photo)))
    assert "accord des personnes reconnaissables" in enregistree.attestation
    assert enregistree.attestee_le is not None
    assert "photo_ajoutee" in en_base(lambda db: db.scalars(select(JournalAudit.action))).all()


@pytest.mark.parametrize(
    ("options", "attendu"),
    [
        ({"attestation": False}, "attestation"),
        ({"contenu": b"%PDF-1.4 pas une image"}, "photo lisible"),
        ({"legende": "Deux\nlignes"}, "légende"),
        ({"legende": "x" * 201}, "légende"),
    ],
)
def test_un_envoi_invalide_est_refuse_sans_rien_enregistrer(
    auteur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any], options: dict[str, Any], attendu: str
) -> None:
    article = creer_article(auteur)

    reponse = envoyer(auteur, article["id"], **options)

    assert reponse.status_code == 422
    assert attendu in reponse.json()["detail"]
    assert fichiers(dossier_fichiers) == []
    assert en_base(lambda db: db.scalar(select(Photo.id))) is None


def test_une_photo_trop_lourde_est_refusee(auteur: Navigateur, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "photo_octets_max", 1000)
    article = creer_article(auteur)

    reponse = envoyer(auteur, article["id"])

    assert reponse.status_code == 422
    assert "dépasse" in reponse.json()["detail"]


def test_cinq_photos_au_plus_et_une_seule_couverture(auteur: Navigateur) -> None:
    article = creer_article(auteur)
    for numero in range(5):
        resultat = ajouter(auteur, article["id"], legende=f"Photo {numero}", couverture=numero == 3)

    assert [p["couverture"] for p in resultat["photos"]].count(True) == 1
    assert resultat["photos"][0]["legende"] == "Photo 3"
    sixieme = envoyer(auteur, article["id"])
    assert sixieme.status_code == 409


def test_legende_couverture_et_ordre_se_modifient(auteur: Navigateur) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"], legende="Première")
    resultat = ajouter(auteur, article["id"], legende="Seconde")
    seconde = next(p for p in resultat["photos"] if p["legende"] == "Seconde")

    modifie = auteur.request(
        "PATCH",
        f"{ARTICLES}/{article['id']}/photos/{seconde['id']}",
        json={"version": resultat["version"], "legende": "Seconde, renommée", "couverture": True},
    )

    assert modifie.status_code == 200, modifie.text
    premiere = modifie.json()["photos"][0]
    assert (premiere["legende"], premiere["couverture"]) == ("Seconde, renommée", True)
    assert [p["couverture"] for p in modifie.json()["photos"]] == [True, False]


def test_retirer_une_photo_dun_brouillon_efface_ses_fichiers(
    auteur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"], legende="Première")
    resultat = ajouter(auteur, article["id"], legende="Seconde")
    couverture = next(p for p in resultat["photos"] if p["couverture"])

    retire = auteur.delete(
        f"{ARTICLES}/{article['id']}/photos/{couverture['id']}", params={"version": resultat["version"]}
    )

    assert retire.status_code == 200, retire.text
    # L'autre photo devient la couverture.
    assert [(p["legende"], p["couverture"]) for p in retire.json()["photos"]] == [("Seconde", True)]
    assert len(fichiers(dossier_fichiers)) == 2
    assert en_base(lambda db: db.scalar(select(Photo).where(Photo.id == couverture["id"]))) is None


def test_une_version_perimee_ou_un_article_en_attente_refuse_les_photos(auteur: Navigateur) -> None:
    article = creer_article(auteur)
    ajoutee = ajouter(auteur, article["id"])

    assert envoyer(auteur, article["id"], version=article["version"]).status_code == 409
    soumettre(auteur, article["id"])
    assert envoyer(auteur, article["id"]).status_code == 409
    photo = ajoutee["photos"][0]["id"]
    version = auteur.get(f"{ARTICLES}/{article['id']}").json()["version"]
    assert auteur.delete(f"{ARTICLES}/{article['id']}/photos/{photo}", params={"version": version}).status_code == 409


def test_un_autre_eleve_nenvoie_pas_de_photo_dans_mon_article(
    client: TestClient, auteur: Navigateur, creer_eleve: Callable[..., Utilisateur]
) -> None:
    article = creer_article(auteur)
    creer_eleve("eleve2", "Kofi de Kara", dre="kara")
    autre = Navigateur(client)
    connecter(autre, "eleve2")

    assert envoyer(autre, article["id"], version=article["version"]).status_code == 404


def test_une_nouvelle_version_reprend_les_photos_sans_toucher_a_la_version_en_ligne(
    auteur: Navigateur, moderateur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    photo = ajouter(auteur, article["id"], legende="En ligne")["photos"][0]["id"]
    soumettre(auteur, article["id"])
    decider(moderateur, article["id"], "approuver")

    actuel = auteur.get(f"{ARTICLES}/{article['id']}").json()
    modifie = auteur.request(
        "PATCH",
        f"{ARTICLES}/{article['id']}/photos/{photo}",
        json={"version": actuel["version"], "legende": "Légende révisée"},
    ).json()

    assert modifie["photos"][0]["legende"] == "Légende révisée"
    legendes = en_base(lambda db: db.scalars(select(VersionPhoto.legende).order_by(VersionPhoto.legende))).all()
    assert legendes == ["En ligne", "Légende révisée"]


def test_lapercu_admin_montre_les_photos_et_leur_attestation(auteur: Navigateur, moderateur: Navigateur) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"])
    soumettre(auteur, article["id"])

    apercu = moderateur.get(f"{FILE}/{article['id']}").json()

    (photo,) = apercu["photos_soumises"]
    assert "accord des personnes reconnaissables" in photo["attestation"]
    assert photo["attestee_le"] and photo["effacee"] is False
    assert apercu["photos_publiees"] == []


def test_supprimer_un_brouillon_efface_ses_photos(auteur: Navigateur, dossier_fichiers: Path) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"])

    assert auteur.delete(f"{ARTICLES}/{article['id']}").status_code == 204
    assert fichiers(dossier_fichiers) == []


def test_ajouter_une_photo_a_un_article_publie_ouvre_une_nouvelle_version(
    client: TestClient, auteur: Navigateur, moderateur: Navigateur
) -> None:
    article = creer_article(auteur)
    soumettre(auteur, article["id"])
    adresse = decider(moderateur, article["id"], "approuver")["adresse"]

    resultat = ajouter(auteur, article["id"])

    assert (resultat["etat"], resultat["en_ligne"]) == ("brouillon", True)
    assert client.get(f"/api/articles/{adresse}").json()["couverture"] is None


def test_disque_indisponible_rien_nest_enregistre(
    auteur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.fichiers.stockage import Disque, StockageIndisponible

    async def plein(self: Disque, cle: str, octets: bytes) -> None:
        raise StockageIndisponible

    monkeypatch.setattr(Disque, "enregistrer", plein)
    article = creer_article(auteur)

    reponse = envoyer(auteur, article["id"])

    assert reponse.status_code == 503
    assert en_base(lambda db: db.scalar(select(Photo.id))) is None
    assert fichiers(dossier_fichiers) == []


def test_retirer_la_couverture_la_donne_a_une_autre_et_la_remettre_la_garde(auteur: Navigateur) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"], legende="Première")
    resultat = ajouter(auteur, article["id"], legende="Seconde")
    premiere = next(p for p in resultat["photos"] if p["legende"] == "Première")

    deja = auteur.request(
        "PATCH",
        f"{ARTICLES}/{article['id']}/photos/{premiere['id']}",
        json={"version": resultat["version"], "couverture": True},
    ).json()
    assert [(p["legende"], p["couverture"]) for p in deja["photos"]] == [("Première", True), ("Seconde", False)]

    sans = auteur.request(
        "PATCH",
        f"{ARTICLES}/{article['id']}/photos/{premiere['id']}",
        json={"version": deja["version"], "couverture": False},
    ).json()
    assert [(p["legende"], p["couverture"]) for p in sans["photos"]] == [("Seconde", True), ("Première", False)]


def test_une_photo_deja_soumise_reste_dans_lhistorique_apres_un_retrait(
    auteur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    photo = ajouter(auteur, article["id"])["photos"][0]["id"]
    soumis = soumettre(auteur, article["id"])
    retire = auteur.post(f"{ARTICLES}/{article['id']}/retirer", json={"version": soumis["version"]}).json()

    reponse = auteur.delete(f"{ARTICLES}/{article['id']}/photos/{photo}", params={"version": retire["version"]})

    assert reponse.status_code == 200, reponse.text
    assert en_base(lambda db: db.scalar(select(Photo.id))) is not None
    assert len(fichiers(dossier_fichiers)) == 2
