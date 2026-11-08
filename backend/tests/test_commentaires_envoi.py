"""Envoi d'un commentaire (spec 025) : qui peut commenter, quel article, quel texte, et les plafonds contre le spam.

Écrits avant le code : rien de public sans modération, et les droits se vérifient dans l'API (docs/TESTING.md)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.comptes.models import StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from app.moderation.models import Contenu, EtatContenu
from tests.commentaires import (
    ARTICLES,
    FILE,
    MIENS,
    commenter,
    connecter,
    decider,
    envoyer,
    moderateur,
    publics,
    publier_article,
)

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def scene(client: TestClient, creer_eleve: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any]) -> Any:
    """Un article publié par eleve1, un lecteur eleve2 connecté, un modérateur."""
    creer_eleve()
    creer_eleve("eleve2", affiche="Kofi des Plateaux")
    redacteur = connecter(client, "eleve1")
    admin = moderateur(client, creer_collaborateur)
    adresse = publier_article(redacteur, admin)
    lecteur = connecter(client, "eleve2")
    return {"adresse": adresse, "lecteur": lecteur, "redacteur": redacteur, "admin": admin}


def test_un_eleve_envoie_un_commentaire_en_attente_invisible_du_public(client: TestClient, scene: Any) -> None:
    commentaire = envoyer(scene["lecteur"], scene["adresse"], "Super idée, merci !")

    assert commentaire["etat"] == "en_attente"
    assert commentaire["texte"] == "Super idée, merci !"
    assert commentaire["article"] == {"adresse": scene["adresse"], "titre": "Le lavage des mains au lycée"}
    assert publics(client, scene["adresse"]).json()["total"] == 0
    miens = scene["lecteur"].get(MIENS).json()["commentaires"]
    assert [c["id"] for c in miens] == [commentaire["id"]]
    file = scene["admin"].get(FILE).json()["contenus"]
    assert [(c["id"], c["type"]) for c in file] == [(commentaire["id"], "commentaire")]


def test_un_encadreur_actif_commente(client: TestClient, scene: Any, creer_encadreur: Callable[..., Any]) -> None:
    creer_encadreur()
    encadreur = connecter(client, "encadreur1")

    assert commenter(encadreur, scene["adresse"]).status_code == 201


def test_un_encadreur_non_verifie_ne_commente_pas(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_encadreur(etat=EtatVerification.en_attente)
    encadreur = connecter(client, "encadreur1")

    assert commenter(encadreur, scene["adresse"]).status_code == 403
    assert _commentaires(en_base) == 0


def test_un_visiteur_ne_commente_pas(client: TestClient, scene: Any, en_base: Callable[..., Any]) -> None:
    client.cookies.clear()

    assert commenter(client, scene["adresse"]).status_code == 401
    assert _commentaires(en_base) == 0


def test_un_compte_suspendu_ne_commente_pas(client: TestClient, scene: Any, en_base: Callable[..., Any]) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.identifiant == "eleve2").values(statut=StatutCompte.suspendu)
        )
    )

    assert commenter(scene["lecteur"], scene["adresse"]).status_code in {401, 403}
    assert _commentaires(en_base) == 0


def test_seul_un_article_publie_se_commente(client: TestClient, scene: Any, en_base: Callable[..., Any]) -> None:
    redacteur = scene["redacteur"]
    brouillon = redacteur.post(
        ARTICLES,
        json={"titre": "Un brouillon", "chapo": "Chapo du brouillon.", "texte": "Texte.",
              "axe_code": "sante-environnement", "afficher_club": True},
    ).json()  # fmt: skip

    assert commenter(scene["lecteur"], "article-inexistant").status_code == 404
    assert commenter(scene["lecteur"], str(brouillon["id"])).status_code == 404
    decider(scene["admin"], _article_id(en_base, scene["adresse"]), "depublier", "Retiré pour vérification.")
    assert commenter(scene["lecteur"], scene["adresse"]).status_code == 404
    assert _commentaires(en_base) == 0


@pytest.mark.parametrize("texte", ["", "   ", "\n\n\t", "a" * 1001])
def test_un_texte_vide_ou_trop_long_est_refuse(scene: Any, texte: str, en_base: Callable[..., Any]) -> None:
    assert commenter(scene["lecteur"], scene["adresse"], texte).status_code == 422
    assert _commentaires(en_base) == 0


def test_le_texte_est_normalise(scene: Any) -> None:
    commentaire = envoyer(scene["lecteur"], scene["adresse"], "  Bravo\u0007 !\n\n\n\n\nOn essaie aussi 💪  ")

    assert commentaire["texte"] == "Bravo !\n\nOn essaie aussi 💪"


def test_mille_caracteres_passent(scene: Any) -> None:
    assert commenter(scene["lecteur"], scene["adresse"], "é" * 1000).status_code == 201


def test_le_html_est_garde_tel_quel(scene: Any) -> None:
    texte = '<script>alert(1)</script> <a href="https://exemple.tg">lien</a>'

    assert envoyer(scene["lecteur"], scene["adresse"], texte)["texte"] == texte


def test_un_double_envoi_ne_fait_quun_commentaire(scene: Any, en_base: Callable[..., Any]) -> None:
    premier = envoyer(scene["lecteur"], scene["adresse"], "Même texte")
    second = commenter(scene["lecteur"], scene["adresse"], "Même texte")

    assert second.status_code == 200, second.text
    assert second.json()["id"] == premier["id"]
    assert _commentaires(en_base) == 1


def test_le_meme_texte_une_minute_plus_tard_fait_un_second_commentaire(scene: Any, en_base: Callable[..., Any]) -> None:
    premier = envoyer(scene["lecteur"], scene["adresse"], "Même texte")
    _vieillir(en_base, premier["id"], timedelta(minutes=2))

    assert commenter(scene["lecteur"], scene["adresse"], "Même texte").status_code == 201
    assert _commentaires(en_base) == 2


def test_au_dela_de_vingt_envois_par_jour_lapi_repond_429(scene: Any, en_base: Callable[..., Any]) -> None:
    hier = envoyer(scene["lecteur"], scene["adresse"], "Envoyé hier")
    _vieillir(en_base, hier["id"], timedelta(days=1))
    for numero in range(20):
        commentaire = envoyer(scene["lecteur"], scene["adresse"], f"Commentaire {numero}")
        # Les décisions libèrent la limite d'attente : seul le plafond du jour reste.
        assert decider(scene["admin"], commentaire["id"], "refuser", "Hors sujet.").status_code == 200

    trop = commenter(scene["lecteur"], scene["adresse"], "Le vingt et unième")

    assert trop.status_code == 429
    assert "20 commentaires" in trop.json()["detail"]


def test_trois_commentaires_en_attente_au_plus_sans_bloquer_les_articles(scene: Any) -> None:
    for numero in range(3):
        envoyer(scene["lecteur"], scene["adresse"], f"Commentaire {numero}")

    assert commenter(scene["lecteur"], scene["adresse"], "Un quatrième").status_code == 409
    # La limite se compte par type : l'élève peut encore soumettre un article.
    article = scene["lecteur"].post(
        ARTICLES,
        json={"titre": "Mon article", "chapo": "Un chapo assez long.", "texte": "Texte.",
              "axe_code": "sante-environnement", "afficher_club": True},
    ).json()  # fmt: skip
    soumis = scene["lecteur"].post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"]})
    assert soumis.status_code == 200, soumis.text


def test_le_commentaire_garde_la_dre_de_son_auteur(scene: Any, en_base: Callable[..., Any]) -> None:
    commentaire = envoyer(scene["lecteur"], scene["adresse"])

    enregistre = en_base(lambda db: db.get(Contenu, _uuid(commentaire["id"])))
    assert enregistre.dre_code == "grand-lome"
    assert enregistre.etat is EtatContenu.en_attente
    assert enregistre.parent_id is not None


# Aides ----------------------------------------------------------------------------------------------------------


def _uuid(valeur: str) -> Any:
    from uuid import UUID

    return UUID(valeur)


def _commentaires(en_base: Callable[..., Any]) -> int:
    return len(list(en_base(lambda db: db.scalars(select(Contenu.id).where(Contenu.type == "commentaire")))))


def _article_id(en_base: Callable[..., Any], adresse: str) -> str:
    return str(en_base(lambda db: db.scalar(select(Contenu.id).where(Contenu.adresse == adresse))))


def _vieillir(en_base: Callable[..., Any], contenu_id: str, duree: timedelta) -> None:
    en_base(
        lambda db: db.execute(
            update(Contenu).where(Contenu.id == _uuid(contenu_id)).values(cree_le=datetime.now(UTC) - duree)
        )
    )
