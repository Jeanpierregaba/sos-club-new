"""Déclaration des partages d'articles (spec 044, R17) : la nature selon l'auteur de l'article, l'article publié,
le lien vérifiable, une fois par réseau ou par article, 3 déclarations par jour, et les droits.

Écrits avant le code : aucun point sans vérification, rien de public (docs/RULES.md, docs/TESTING.md)."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from alembic import command
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from app.moderation.models import Contenu
from tests.commentaires import ARTICLES, connecter, decider, publier_article
from tests.partages import LIENS, PARTAGES_MOI, declare, declarer, etat_article, moderateur_partages

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def scene(client: TestClient, creer_eleve: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any]) -> Any:
    creer_eleve()  # la rédactrice, Ama
    creer_eleve("eleve2", affiche="Kofi des Plateaux")
    redactrice = connecter(client, "eleve1")
    admin = moderateur_partages(client, creer_collaborateur)
    return {
        "adresse": publier_article(redactrice, admin),
        "redactrice": redactrice,
        "lecteur": connecter(client, "eleve2"),
        "admin": admin,
    }


def _partages(en_base: Callable[..., Any]) -> int:
    return int(
        en_base(lambda db: db.scalar(select(func.count()).select_from(Contenu).where(Contenu.type == "partage")))
    )


# Nature et état -------------------------------------------------------------------------------------------------


def test_un_lecteur_declare_une_republication_en_attente(scene: Any) -> None:
    partage = declare(scene["lecteur"], scene["adresse"], "facebook")

    assert partage["nature"] == "republication"
    assert partage["reseau"] == "facebook"
    assert partage["etat"] == "en_attente"
    assert partage["points"] is None


def test_lautrice_declare_le_partage_de_son_article(scene: Any) -> None:
    partage = declare(scene["redactrice"], scene["adresse"], "instagram")

    assert partage["nature"] == "partage"


def test_letat_de_larticle_pour_la_personne(scene: Any) -> None:
    declare(scene["redactrice"], scene["adresse"], "facebook")

    etat = etat_article(scene["redactrice"], scene["adresse"]).json()

    assert etat["nature"] == "partage"
    assert etat["reseaux_declares"] == ["facebook"]
    assert etat["restantes_aujourdhui"] == 2
    assert etat_article(scene["lecteur"], scene["adresse"]).json() == {
        "nature": "republication",
        "reseaux_declares": [],
        "restantes_aujourdhui": 3,
    }


# Article --------------------------------------------------------------------------------------------------------


def test_seul_un_article_publie_se_declare(scene: Any, en_base: Callable[..., Any]) -> None:
    brouillon = scene["redactrice"].post(
        ARTICLES,
        json={"titre": "Un brouillon", "chapo": "Chapo du brouillon.", "texte": "Texte.",
              "axe_code": "sante-environnement", "afficher_club": True},
    ).json()  # fmt: skip

    assert declarer(scene["lecteur"], "article-inexistant").status_code == 404
    assert declarer(scene["lecteur"], str(brouillon["id"])).status_code == 404
    assert _partages(en_base) == 0


def test_un_article_depublie_ne_se_declare_plus(scene: Any) -> None:
    article = scene["admin"].get("/api/admin/moderation", params={"etat": "publie"}).json()["contenus"][0]
    assert decider(scene["admin"], article["id"], "depublier", "Retiré pour le test.").status_code == 200

    assert declarer(scene["lecteur"], scene["adresse"]).status_code == 404


# Liens ----------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("reseau", "lien"),
    [
        ("facebook", "http://www.facebook.com/ama/posts/1"),
        ("facebook", "https://www.tiktok.com/@ama/video/1"),
        ("facebook", "https://facebook.com.exemple.tg/posts/1"),
        ("facebook", "https://faux-facebook.com/posts/1"),
        ("instagram", "javascript:alert(1)"),
        ("instagram", "data:text/html,bonjour"),
        ("linkedin", "https://www.linkedin.com/" + "a" * 500),
        ("tiktok", "https://"),
        ("tiktok", "pas un lien"),
        ("whatsapp", "https://wa.me/22890000000"),
    ],
)
def test_les_liens_invalides_sont_refuses(scene: Any, en_base: Callable[..., Any], reseau: str, lien: str) -> None:
    assert declarer(scene["lecteur"], scene["adresse"], reseau, lien).status_code == 422
    assert _partages(en_base) == 0


@pytest.mark.parametrize(
    ("reseau", "lien"),
    [
        ("facebook", "https://m.facebook.com/story.php?story_fbid=1"),
        ("facebook", "https://fb.watch/abc123/"),
        ("tiktok", "https://vm.tiktok.com/ZMabc123/"),
        ("linkedin", "https://lnkd.in/abc123"),
        ("instagram", "  https://instagram.com/p/abc/  "),
    ],
)
def test_les_liens_des_reseaux_sont_acceptes(scene: Any, reseau: str, lien: str) -> None:
    partage = declare(scene["lecteur"], scene["adresse"], reseau, lien)

    assert partage["lien"] == lien.strip()


def test_un_lien_deja_declare_est_refuse_meme_par_une_autre_personne(scene: Any) -> None:
    declare(scene["lecteur"], scene["adresse"], "facebook")

    reponse = declarer(scene["redactrice"], scene["adresse"], "facebook", LIENS["facebook"])

    assert reponse.status_code == 409


# Une fois par réseau, une fois par article ----------------------------------------------------------------------


def test_un_reseau_ne_se_declare_quune_fois_par_article(scene: Any) -> None:
    declare(scene["redactrice"], scene["adresse"], "facebook")

    second = declarer(scene["redactrice"], scene["adresse"], "facebook", "https://facebook.com/ama/posts/autre")

    assert second.status_code == 409
    assert declare(scene["redactrice"], scene["adresse"], "tiktok")["nature"] == "partage"


def test_une_republication_ne_se_declare_quune_fois_par_article(scene: Any) -> None:
    declare(scene["lecteur"], scene["adresse"], "facebook")

    assert declarer(scene["lecteur"], scene["adresse"], "instagram").status_code == 409


def test_un_refus_libere_le_reseau_et_le_lien(scene: Any) -> None:
    partage = declare(scene["redactrice"], scene["adresse"], "facebook")
    assert decider(scene["admin"], partage["id"], "refuser", "Le lien ne s'ouvre pas.").status_code == 200

    again = declare(scene["redactrice"], scene["adresse"], "facebook")

    assert again["etat"] == "en_attente"


# Plafond du jour ------------------------------------------------------------------------------------------------


def test_trois_declarations_par_jour_refus_compris(scene: Any) -> None:
    premiere = declare(scene["redactrice"], scene["adresse"], "facebook")
    assert decider(scene["admin"], premiere["id"], "refuser", "Lien privé.").status_code == 200
    declare(scene["redactrice"], scene["adresse"], "instagram")
    declare(scene["redactrice"], scene["adresse"], "tiktok")

    quatrieme = declarer(scene["redactrice"], scene["adresse"], "linkedin")

    assert quatrieme.status_code == 429
    assert etat_article(scene["redactrice"], scene["adresse"]).json()["restantes_aujourdhui"] == 0


# Droits ---------------------------------------------------------------------------------------------------------


def test_une_personne_non_connectee_ne_declare_pas(client: TestClient, scene: Any, en_base: Callable[..., Any]) -> None:
    client.cookies.clear()

    assert declarer(client, scene["adresse"]).status_code == 401
    assert client.get(PARTAGES_MOI).status_code == 401
    assert _partages(en_base) == 0


def test_un_compte_suspendu_ne_declare_pas(scene: Any, en_base: Callable[..., Any]) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.identifiant == "eleve2").values(statut=StatutCompte.suspendu)
        )
    )

    assert declarer(scene["lecteur"], scene["adresse"]).status_code in {401, 403}
    assert _partages(en_base) == 0


def test_un_visiteur_ne_declare_pas(
    client: TestClient, scene: Any, creer_utilisateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_utilisateur("visiteur1", Role.visiteur, email="visiteur1@exemple.tg", email_confirme_le=datetime.now(UTC))

    assert declarer(connecter(client, "visiteur1"), scene["adresse"]).status_code == 403
    assert _partages(en_base) == 0


def test_un_encadreur_non_verifie_ne_declare_pas(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_encadreur("encadreur2", etat=EtatVerification.en_attente)

    assert declarer(connecter(client, "encadreur2"), scene["adresse"]).status_code == 403
    assert _partages(en_base) == 0


def test_un_encadreur_verifie_declare_une_republication(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any]
) -> None:
    creer_encadreur()

    assert declare(connecter(client, "encadreur1"), scene["adresse"])["nature"] == "republication"


# Migration ------------------------------------------------------------------------------------------------------


def test_le_retour_arriere_est_refuse_avec_des_partages(scene: Any) -> None:
    from pathlib import Path

    declare(scene["lecteur"], scene["adresse"])
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")

    with pytest.raises(RuntimeError, match="partages sont enregistrés"):
        command.downgrade(configuration, "4dc45a4fff16")
    command.upgrade(configuration, "head")
