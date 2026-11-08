"""Lecture publique et retrait des commentaires (spec 025) : seuls les commentaires publiés d'un article publié,
signature sans nom complet, ordre, pagination, « Mes commentaires » et retrait par l'auteur.

Écrits avant le code : un élève n'apparaît publiquement que par son pseudonyme et son club (docs/RULES.md)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.comptes.models import Utilisateur
from app.moderation.models import Contenu, EtatContenu
from tests.commentaires import (
    FILE,
    MIENS,
    connecter,
    contenu,
    decider,
    envoyer,
    moderateur,
    publics,
    publier_article,
)

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def scene(client: TestClient, creer_eleve: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any]) -> Any:
    creer_eleve()
    lecteur = creer_eleve("eleve2", affiche="Kofi des Plateaux")
    admin = moderateur(client, creer_collaborateur)
    adresse = publier_article(connecter(client, "eleve1"), admin)
    return {"adresse": adresse, "admin": admin, "lecteur": lecteur, "navigateur": connecter(client, "eleve2")}


def publie(scene: Any, texte: str = "Bravo au club !") -> dict[str, Any]:
    commentaire = envoyer(scene["navigateur"], scene["adresse"], texte)
    assert decider(scene["admin"], commentaire["id"], "approuver").status_code == 200
    return commentaire


def test_seuls_les_commentaires_publies_sont_lisibles(client: TestClient, scene: Any) -> None:
    approuve = publie(scene, "Approuvé")
    envoyer(scene["navigateur"], scene["adresse"], "En attente")
    refuse = envoyer(scene["navigateur"], scene["adresse"], "Refusé")
    decider(scene["admin"], refuse["id"], "refuser", "Non.")
    depublie = publie(scene, "Dépublié")
    decider(scene["admin"], depublie["id"], "depublier", "Retiré.")

    reponse = publics(client, scene["adresse"])

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert [c["texte"] for c in corps["commentaires"]] == ["Approuvé"]
    assert corps["commentaires"][0]["id"] == approuve["id"]
    assert (corps["total"], corps["page"], corps["pages"]) == (1, 1, 1)


def test_la_signature_dun_eleve_ne_montre_ni_nom_ni_identifiant(client: TestClient, scene: Any) -> None:
    publie(scene)

    brut = publics(client, scene["adresse"])
    commentaire = brut.json()["commentaires"][0]

    assert commentaire["signature"] == {"profil": "eleve", "nom": "Kofi des Plateaux", "club": None, "fonction": None}
    assert set(commentaire) == {"id", "texte", "signature", "publie_le"}
    for interdit in ("Kodjo", "eleve2", "auteur", "dre_code", "etablissement"):
        assert interdit not in brut.text


def test_la_signature_montre_le_club_de_leleve(client: TestClient, scene: Any, creer_club: Callable[..., Any]) -> None:
    creer_club(scene["lecteur"], nom="Club Santé du Lycée")
    publie(scene)

    assert publics(client, scene["adresse"]).json()["commentaires"][0]["signature"]["club"] == "Club Santé du Lycée"


def test_un_encadreur_signe_par_son_prenom_linitiale_et_sa_fonction(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any]
) -> None:
    creer_encadreur()
    commentaire = envoyer(connecter(client, "encadreur1"), scene["adresse"])
    decider(scene["admin"], commentaire["id"], "approuver")

    signature = publics(client, scene["adresse"]).json()["commentaires"][0]["signature"]

    assert signature["profil"] == "encadreur"
    assert signature["nom"] == "Jean K."
    assert signature["fonction"]


def test_les_commentaires_vont_du_plus_ancien_au_plus_recent_par_pages_de_50(
    client: TestClient, scene: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.commentaires import service

    monkeypatch.setattr(service, "ENVOIS_PAR_JOUR", 100)
    textes = [f"Commentaire {numero:02d}" for numero in range(52)]
    for texte in textes:
        publie(scene, texte)

    premiere = publics(client, scene["adresse"]).json()
    seconde = publics(client, scene["adresse"], page=2).json()

    assert (premiere["total"], premiere["pages"]) == (52, 2)
    assert [c["texte"] for c in premiere["commentaires"]] == textes[:50]
    assert [c["texte"] for c in seconde["commentaires"]] == textes[50:]


def test_un_article_depublie_cache_ses_commentaires(
    client: TestClient, scene: Any, en_base: Callable[..., Any]
) -> None:
    publie(scene)
    article_id = en_base(lambda db: db.scalar(select(Contenu.id).where(Contenu.adresse == scene["adresse"])))

    decider(scene["admin"], str(article_id), "depublier", "Vérification.")

    assert publics(client, scene["adresse"]).status_code == 404
    assert publics(client, "article-inexistant").status_code == 404


def test_mes_commentaires_montre_les_etats_et_le_motif(scene: Any) -> None:
    publie(scene, "Approuvé")
    refuse = envoyer(scene["navigateur"], scene["adresse"], "Refusé")
    decider(scene["admin"], refuse["id"], "refuser", "Propos hors sujet.")

    miens = scene["navigateur"].get(MIENS).json()["commentaires"]
    filtres = scene["navigateur"].get(MIENS, params={"article": scene["adresse"]}).json()["commentaires"]

    # Les plus récents d'abord.
    assert [(c["texte"], c["etat"]) for c in miens] == [("Refusé", "refuse"), ("Approuvé", "publie")]
    assert miens[0]["motif"] == "Propos hors sujet."
    assert miens[0]["article"]["adresse"] == scene["adresse"]
    assert len(filtres) == 2
    assert scene["navigateur"].get(MIENS, params={"article": "autre-article"}).json()["commentaires"] == []


def test_lauteur_retire_un_commentaire_publie(client: TestClient, scene: Any, en_base: Callable[..., Any]) -> None:
    commentaire = publie(scene)

    reponse = scene["navigateur"].delete(f"{MIENS}/{commentaire['id']}")

    assert reponse.status_code == 204, reponse.text
    assert publics(client, scene["adresse"]).json()["total"] == 0
    assert contenu(en_base, commentaire["id"]).etat is EtatContenu.retire
    assert scene["navigateur"].get(MIENS).json()["commentaires"][0]["etat"] == "retire"
    # Les points acquis restent.
    from tests.commentaires import lignes

    assert any(g.action == "eleve.commentaire" for g in lignes(en_base, scene["lecteur"].id))


def test_un_commentaire_retire_quitte_la_file(scene: Any) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])

    assert scene["navigateur"].delete(f"{MIENS}/{commentaire['id']}").status_code == 204
    assert commentaire["id"] not in [c["id"] for c in scene["admin"].get(FILE).json()["contenus"]]
    # Avec la version à jour : le commentaire n'est plus en attente, la décision est refusée quand même.
    version = scene["admin"].get(f"{FILE}/{commentaire['id']}").json()["version"]
    assert scene["admin"].post(f"{FILE}/{commentaire['id']}/approuver", json={"version": version}).status_code == 409


def test_un_autre_compte_ne_retire_pas_le_commentaire(client: TestClient, scene: Any) -> None:
    commentaire = publie(scene)
    autre = connecter(client, "eleve1")

    assert autre.delete(f"{MIENS}/{commentaire['id']}").status_code == 404
    assert publics(client, scene["adresse"]).json()["total"] == 1


def test_un_retrait_deja_fait_repond_409(scene: Any) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])
    scene["navigateur"].delete(f"{MIENS}/{commentaire['id']}")

    assert scene["navigateur"].delete(f"{MIENS}/{commentaire['id']}").status_code == 409


def test_une_decision_sur_une_version_perimee_apres_retrait_repond_409(scene: Any, en_base: Callable[..., Any]) -> None:
    """Le modérateur a lu le commentaire, l'auteur le retire, puis la décision arrive : 409, rien n'est publié."""
    commentaire = envoyer(scene["navigateur"], scene["adresse"])
    version = scene["admin"].get(f"{FILE}/{commentaire['id']}").json()["version"]

    scene["navigateur"].delete(f"{MIENS}/{commentaire['id']}")
    reponse = scene["admin"].post(f"{FILE}/{commentaire['id']}/approuver", json={"version": version})

    assert reponse.status_code == 409
    assert contenu(en_base, commentaire["id"]).etat is EtatContenu.retire


def test_un_eleve_peut_masquer_son_club(client: TestClient, scene: Any, creer_club: Callable[..., Any]) -> None:
    creer_club(scene["lecteur"], nom="Club Santé du Lycée")
    commentaire = (
        scene["navigateur"]
        .post(f"/api/articles/{scene['adresse']}/commentaires", json={"texte": "Sans mon club", "afficher_club": False})
        .json()
    )
    decider(scene["admin"], commentaire["id"], "approuver")

    assert publics(client, scene["adresse"]).json()["commentaires"][0]["signature"]["club"] is None


def test_le_titre_dun_brouillon_de_larticle_nest_jamais_montre_au_commentateur(
    client: TestClient, scene: Any, en_base: Callable[..., Any]
) -> None:
    publie(scene)
    article_id = str(en_base(lambda db: db.scalar(select(Contenu.id).where(Contenu.adresse == scene["adresse"]))))
    decider(scene["admin"], article_id, "depublier", "Vérification.")
    redacteur = connecter(client, "eleve1")
    actuel = redacteur.get(f"/api/mes-articles/{article_id}").json()
    modifie = redacteur.request(
        "PATCH",
        f"/api/mes-articles/{article_id}",
        json=actuel["champs"] | {"titre": "Titre jamais relu", "version": actuel["version"]},
    )
    assert modifie.status_code == 200, modifie.text

    article = scene["navigateur"].get(MIENS).json()["commentaires"][0]["article"]

    assert article == {"adresse": None, "titre": "Le lavage des mains au lycée"}


def test_un_encadreur_dont_la_verification_est_retiree_retire_encore_son_commentaire(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from sqlalchemy import update

    from app.encadreurs.models import Encadreur, EtatVerification

    encadreur = creer_encadreur()
    navigateur = connecter(client, "encadreur1")
    commentaire = envoyer(navigateur, scene["adresse"])
    en_base(
        lambda db: db.execute(
            update(Encadreur).where(Encadreur.utilisateur_id == encadreur.id).values(etat=EtatVerification.en_attente)
        )
    )

    assert navigateur.get(MIENS).status_code == 200
    assert navigateur.delete(f"{MIENS}/{commentaire['id']}").status_code == 204
