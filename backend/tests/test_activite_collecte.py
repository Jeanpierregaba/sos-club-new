"""Collecte anonyme des événements d'activité (spec 051, ADR-0014) : écrite avant le code."""

from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect as inspecter
from sqlalchemy import select

from app.activite import service
from app.activite.models import EvenementActivite, SelActivite
from tests.conftest import connecter_admin
from tests.test_connexion import se_connecter

EVENEMENTS = "/api/activite/evenements"
CHROME_ANDROID = "Mozilla/5.0 (Linux; Android 13; SM-A135F) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36"
SAFARI_IPAD = "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Safari/604.1"
FIREFOX_PC = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
ROBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


def envoyer(client: TestClient, corps: dict[str, Any], agent: str = CHROME_ANDROID, **entetes: str) -> Any:
    return client.post(EVENEMENTS, json=corps, headers={"User-Agent": agent, **entetes})


def lister(en_base: Callable[..., Any]) -> list[EvenementActivite]:
    async def _lister(db: Any) -> list[EvenementActivite]:
        return list(await db.scalars(select(EvenementActivite).order_by(EvenementActivite.cree_le)))

    return en_base(_lister)


@pytest.fixture
def jour(monkeypatch: pytest.MonkeyPatch) -> Callable[[date], None]:
    def fixer(valeur: date) -> None:
        monkeypatch.setattr(service, "aujourdhui", lambda: valeur)

    return fixer


# Enregistrement et anonymat ------------------------------------------------------------------------------------


def test_une_page_vue_est_enregistree_sans_donnee_personnelle(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = envoyer(
        client,
        {"type": "page_vue", "chemin": "/quiz/$id", "referent": "https://l.facebook.com/l.php?u=x", "entree": True},
    )
    assert reponse.status_code == 204
    [evenement] = lister(en_base)
    assert evenement.type == "page_vue"
    assert evenement.chemin == "/quiz/$id"
    assert evenement.provenance == "facebook"
    assert evenement.appareil == "telephone"
    assert evenement.navigateur == "chrome"
    assert evenement.connecte is False
    assert len(evenement.visiteur) == 16
    assert "testclient" not in evenement.visiteur


def test_aucune_colonne_ne_peut_porter_ip_compte_ou_saisie() -> None:
    colonnes = {c.key for c in inspecter(EvenementActivite).columns}
    assert colonnes == {
        "id", "cree_le", "jour", "type", "visiteur", "chemin", "detail", "provenance", "appareil", "navigateur",
        "connecte",
    }  # fmt: skip
    assert not [c for c in inspecter(EvenementActivite).columns if c.foreign_keys]


def test_meme_visiteur_le_meme_jour_un_autre_le_lendemain(
    client: TestClient, en_base: Callable[..., Any], jour: Callable[[date], None]
) -> None:
    jour(date(2026, 11, 20))
    envoyer(client, {"type": "page_vue", "chemin": "/"})
    envoyer(client, {"type": "page_vue", "chemin": "/jeux"})
    envoyer(client, {"type": "page_vue", "chemin": "/"}, agent=FIREFOX_PC)
    jour(date(2026, 11, 21))
    envoyer(client, {"type": "page_vue", "chemin": "/"})
    premier, deuxieme, autre_navigateur, lendemain = lister(en_base)
    assert premier.visiteur == deuxieme.visiteur
    assert autre_navigateur.visiteur != premier.visiteur
    assert lendemain.visiteur != premier.visiteur
    assert lendemain.jour == date(2026, 11, 21)


def test_le_sel_d_un_jour_passe_est_efface(
    client: TestClient, en_base: Callable[..., Any], jour: Callable[[date], None]
) -> None:
    jour(date(2026, 11, 20))
    envoyer(client, {"type": "page_vue", "chemin": "/"})
    jour(date(2026, 11, 21))
    envoyer(client, {"type": "page_vue", "chemin": "/"})
    jours = en_base(lambda db: db.scalars(select(SelActivite.jour)))
    assert list(jours) == [date(2026, 11, 21)]


@pytest.mark.parametrize(
    ("agent", "appareil", "navigateur"),
    [
        (SAFARI_IPAD, "tablette", "safari"),
        (FIREFOX_PC, "ordinateur", "firefox"),
        (CHROME_ANDROID, "telephone", "chrome"),
    ],
)
def test_appareil_et_navigateur_sans_version(agent: str, appareil: str, navigateur: str) -> None:
    assert service.appareil(agent) == appareil
    assert service.navigateur(agent) == navigateur


@pytest.mark.parametrize(
    ("referent", "utm", "provenance"),
    [
        (None, None, "direct"),
        ("https://www.google.com/", None, "recherche"),
        ("https://wa.me/228", None, "whatsapp"),
        ("https://www.tiktok.com/@sosdocteurtv", None, "tiktok"),
        ("https://youtu.be/abc", None, "youtube"),
        ("https://un-blog.tg/article", None, "autre"),
        ("https://www.google.com/", "Affiche-Lome", "affiche-lome"),
        (None, "<script>", "direct"),
        ("pas une adresse", None, "autre"),
    ],
)
def test_provenance_ramenee_a_une_categorie(referent: str | None, utm: str | None, provenance: str) -> None:
    assert service.provenance(referent, utm) == provenance


# Exclusions ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("entetes", [{"Sec-GPC": "1"}, {"DNT": "1"}])
def test_ne_pas_me_suivre_est_respecte(
    client: TestClient, en_base: Callable[..., Any], entetes: dict[str, str]
) -> None:
    assert envoyer(client, {"type": "page_vue", "chemin": "/"}, **entetes).status_code == 204
    assert lister(en_base) == []


def test_un_robot_n_est_pas_compte(client: TestClient, en_base: Callable[..., Any]) -> None:
    assert envoyer(client, {"type": "page_vue", "chemin": "/"}, agent=ROBOT).status_code == 204
    assert lister(en_base) == []


def test_un_compte_admin_n_est_pas_compte(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("chef", super_admin=True)
    assert connecter_admin(client).status_code == 200
    assert envoyer(client, {"type": "page_vue", "chemin": "/"}).status_code == 204
    assert lister(en_base) == []


def test_un_compte_connecte_est_signale_sans_etre_identifie(
    client: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    creer_utilisateur()
    assert se_connecter(client).status_code == 200
    envoyer(client, {"type": "page_vue", "chemin": "/mon-espace"})
    [evenement] = lister(en_base)
    assert evenement.connecte is True


# Schéma fermé ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "corps",
    [
        {"type": "inconnu", "chemin": "/"},
        {"type": "telechargement", "chemin": "/bibliotheque"},  # seulement côté serveur
        {"type": "page_vue", "chemin": "/" + "a" * 200},
        {"type": "page_vue", "chemin": "/", "detail": "x"},
        {"type": "clic_inscription", "chemin": "/", "detail": "n-importe-ou"},
        {"type": "etape_inscription", "chemin": "/inscription", "detail": "eleve:cree"},  # étape serveur
        {"type": "erreur", "chemin": "/x", "detail": "500"},
        {"type": "page_vue", "chemin": "/", "champ_en_trop": 1},
    ],
)
def test_un_evenement_hors_schema_est_refuse(
    client: TestClient, en_base: Callable[..., Any], corps: dict[str, Any]
) -> None:
    assert envoyer(client, corps).status_code == 422
    assert lister(en_base) == []


@pytest.mark.parametrize(
    ("chemin", "garde"),
    [
        ("/quiz/$id", "/quiz/$id"),
        ("/quiz/", "/quiz"),
        ("/carte/AbCdEf123456", "autre"),  # un code de carte n'est jamais gardé
        ("/mot-de-passe/nouveau?jeton=secret", "/mot-de-passe/nouveau"),  # sans le jeton
        ("/admin/inscrits/$id", "autre"),
        ("/jean-kodjo", "autre"),
    ],
)
def test_seuls_les_chemins_du_site_sont_gardes(
    client: TestClient, en_base: Callable[..., Any], chemin: str, garde: str
) -> None:
    assert envoyer(client, {"type": "page_vue", "chemin": chemin}).status_code == 204
    [evenement] = lister(en_base)
    assert evenement.chemin == garde


def test_clics_et_etapes_d_inscription(client: TestClient, en_base: Callable[..., Any]) -> None:
    envoyer(client, {"type": "clic_inscription", "chemin": "/", "detail": "accueil"})
    envoyer(client, {"type": "etape_inscription", "chemin": "/inscription", "detail": "eleve:ouvert"})
    envoyer(client, {"type": "etape_inscription", "chemin": "/inscription", "detail": "encadreur:commence"})
    assert [(e.type, e.detail) for e in lister(en_base)] == [
        ("clic_inscription", "accueil"),
        ("etape_inscription", "eleve:ouvert"),
        ("etape_inscription", "encadreur:commence"),
    ]


@pytest.mark.parametrize(
    ("saisie", "garde"),
    [("  Lycée  de   Tsévié ", "lycée de tsévié"), ("90 12 34 56", None), ("jean@exemple.tg", None)],
)
def test_une_recherche_ne_garde_ni_numero_ni_adresse(
    client: TestClient, en_base: Callable[..., Any], saisie: str, garde: str | None
) -> None:
    reponse = envoyer(client, {"type": "recherche", "chemin": "/inscription", "detail": saisie})
    assert reponse.status_code == 204
    assert [e.detail for e in lister(en_base)] == ([garde] if garde else [])


@pytest.mark.parametrize(("chemin", "garde"), [("/ancienne-page", "/ancienne-page"), ("/x/123456789", "autre")])
def test_une_page_introuvable_garde_seulement_un_premier_segment_lisible(
    client: TestClient, en_base: Callable[..., Any], chemin: str, garde: str
) -> None:
    envoyer(client, {"type": "erreur", "chemin": chemin, "detail": "404"})
    [evenement] = lister(en_base)
    assert (evenement.chemin, evenement.detail) == (garde, "404")


# Débit -----------------------------------------------------------------------------------------------------------


def test_le_debit_est_limite_par_adresse(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service, "PLAFOND", 3)
    codes = [envoyer(client, {"type": "page_vue", "chemin": "/"}).status_code for _ in range(5)]
    assert codes == [204, 204, 204, 429, 429]
    assert len(lister(en_base)) == 3


def test_seule_la_page_d_entree_porte_la_provenance(client: TestClient, en_base: Callable[..., Any]) -> None:
    envoyer(client, {"type": "page_vue", "chemin": "/", "referent": "https://www.google.com/", "entree": True})
    envoyer(client, {"type": "page_vue", "chemin": "/jeux", "referent": "https://www.google.com/"})
    assert [e.provenance for e in lister(en_base)] == ["recherche", None]


def test_un_article_ou_un_quiz_se_compte_un_par_un(client: TestClient, en_base: Callable[..., Any]) -> None:
    adresse = "se-laver-les-mains-" + "x" * 80
    assert envoyer(client, {"type": "page_vue", "chemin": "/articles/$adresse", "detail": adresse}).status_code == 204
    assert envoyer(client, {"type": "page_vue", "chemin": "/jeux", "detail": "jeux"}).status_code == 422
    assert envoyer(client, {"type": "page_vue", "chemin": "/quiz/$id", "detail": "Pas Une Adresse"}).status_code == 422
    assert [e.detail for e in lister(en_base)] == [adresse[:60]]
