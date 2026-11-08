"""Modération des commentaires (spec 025) : file et aperçu avec l'article commenté, décisions permises, périmètre,
points (+5 une fois, 5 rémunérés par jour), club bénéficiaire et notifications.

Écrits avant le code : la modération décide de ce qui devient public et crédite des points (docs/TESTING.md)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.comptes.models import Utilisateur
from app.moderation.models import Contenu, EtatContenu
from tests.commentaires import (
    FILE,
    contenu,
    decider,
    envoyer,
    lignes,
    moderateur,
    notifications,
    publier_article,
)

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def scene(client: TestClient, creer_eleve: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any]) -> Any:
    from tests.commentaires import connecter

    redactrice = creer_eleve()
    lecteur = creer_eleve("eleve2", affiche="Kofi des Plateaux")
    navigateur_redactrice = connecter(client, "eleve1")
    admin = moderateur(client, creer_collaborateur)
    adresse = publier_article(navigateur_redactrice, admin)
    return {
        "adresse": adresse,
        "redactrice": redactrice,
        "navigateur_redactrice": navigateur_redactrice,
        "lecteur": lecteur,
        "navigateur": connecter(client, "eleve2"),
        "admin": admin,
    }


def test_la_file_et_lapercu_montrent_larticle_commente(scene: Any) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"], "Bravo à tout le club !")

    element = next(c for c in scene["admin"].get(FILE).json()["contenus"] if c["id"] == commentaire["id"])
    apercu = scene["admin"].get(f"{FILE}/{commentaire['id']}").json()

    assert element["type"] == "commentaire"
    assert element["parent"] == {"adresse": scene["adresse"], "titre": "Le lavage des mains au lycée"}
    assert "Bravo à tout le club" in element["titre"]
    assert apercu["soumise"] == {"texte": "Bravo à tout le club !"}
    assert apercu["parent"] == element["parent"]
    assert apercu["correction_possible"] is False
    assert apercu["adresse"] is None


def test_un_article_peut_etre_corrige_pas_un_commentaire(scene: Any) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])

    reponse = decider(scene["admin"], commentaire["id"], "corriger", "Reformule.")

    assert reponse.status_code == 409
    assert scene["admin"].get(f"{FILE}/{commentaire['id']}").json()["etat"] == "en_attente"


def test_lapprobation_publie_sans_adresse_et_credite_cinq_points_une_fois(
    scene: Any, en_base: Callable[..., Any]
) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])

    assert decider(scene["admin"], commentaire["id"], "approuver").status_code == 200
    publie = contenu(en_base, commentaire["id"])
    assert publie.etat is EtatContenu.publie
    assert publie.adresse is None
    gains = lignes(en_base, scene["lecteur"].id)
    assert [(g.action, g.montant, g.cle) for g in gains if g.action.endswith("commentaire")] == [
        ("eleve.commentaire", 5, f"commentaire:{commentaire['id']}")
    ]

    # Dépublié puis republié : jamais une seconde ligne.
    assert decider(scene["admin"], commentaire["id"], "depublier", "Hors sujet.").status_code == 200
    assert len([g for g in lignes(en_base, scene["lecteur"].id) if g.action.endswith("commentaire")]) == 1


def test_un_encadreur_recoit_les_points_du_bareme_encadreur(
    client: TestClient, scene: Any, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from tests.commentaires import connecter

    encadreur = creer_encadreur()
    commentaire = envoyer(connecter(client, "encadreur1"), scene["adresse"])

    decider(scene["admin"], commentaire["id"], "approuver")

    assert [g.action for g in lignes(en_base, encadreur.id) if g.action.endswith("commentaire")] == [
        "encadreur.commentaire"
    ]


def test_au_dela_de_cinq_commentaires_du_jour_le_suivant_est_publie_sans_points(
    scene: Any, en_base: Callable[..., Any]
) -> None:
    for numero in range(6):
        commentaire = envoyer(scene["navigateur"], scene["adresse"], f"Commentaire {numero}")
        assert decider(scene["admin"], commentaire["id"], "approuver").status_code == 200

    gains = [g for g in lignes(en_base, scene["lecteur"].id) if g.action == "eleve.commentaire"]
    assert len(gains) == 5
    assert contenu(en_base, commentaire["id"]).etat is EtatContenu.publie


def test_le_plafond_se_compte_au_jour_de_lenvoi(scene: Any, en_base: Callable[..., Any]) -> None:
    hier = envoyer(scene["navigateur"], scene["adresse"], "Envoyé hier")
    en_base(
        lambda db: db.execute(
            update(Contenu).where(Contenu.id == UUID(hier["id"])).values(cree_le=datetime.now(UTC) - timedelta(days=1))
        )
    )
    for numero in range(5):
        commentaire = envoyer(scene["navigateur"], scene["adresse"], f"Aujourd'hui {numero}")
        decider(scene["admin"], commentaire["id"], "approuver")

    # Approuvé aujourd'hui, mais envoyé hier : il compte pour hier, où rien n'a encore été rémunéré.
    decider(scene["admin"], hier["id"], "approuver")

    assert len([g for g in lignes(en_base, scene["lecteur"].id) if g.action == "eleve.commentaire"]) == 6


def test_les_commentaires_refuses_ne_comptent_pas_dans_le_plafond(scene: Any, en_base: Callable[..., Any]) -> None:
    for numero in range(2):
        refuse = envoyer(scene["navigateur"], scene["adresse"], f"Refusé {numero}")
        decider(scene["admin"], refuse["id"], "refuser", "Hors sujet.")
    for numero in range(5):
        commentaire = envoyer(scene["navigateur"], scene["adresse"], f"Approuvé {numero}")
        decider(scene["admin"], commentaire["id"], "approuver")

    assert len([g for g in lignes(en_base, scene["lecteur"].id) if g.action == "eleve.commentaire"]) == 5


def test_le_club_de_leleve_affilie_est_enregistre(
    scene: Any, creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    club = creer_club(scene["lecteur"], nom="Club Santé du Lycée")
    commentaire = envoyer(scene["navigateur"], scene["adresse"])

    decider(scene["admin"], commentaire["id"], "approuver")

    assert contenu(en_base, commentaire["id"]).club_beneficiaire_id == club.id


def test_le_refus_exige_un_motif_et_previent_lauteur(scene: Any, en_base: Callable[..., Any]) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])

    assert decider(scene["admin"], commentaire["id"], "refuser").status_code == 422
    assert decider(scene["admin"], commentaire["id"], "refuser", "Propos blessant.").status_code == 200

    avis = notifications(en_base, scene["lecteur"].id)
    assert [(a.type, a.message, a.lien) for a in avis] == [
        ("commentaire_refuse", "Propos blessant.", "/mes-commentaires")
    ]
    assert all(g.action != "eleve.commentaire" for g in lignes(en_base, scene["lecteur"].id))


def test_la_publication_previent_lauteur_du_commentaire_et_celle_de_larticle_une_fois(
    scene: Any, en_base: Callable[..., Any]
) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])
    avant = len(notifications(en_base, scene["redactrice"].id))

    decider(scene["admin"], commentaire["id"], "approuver")
    decider(scene["admin"], commentaire["id"], "depublier", "Vérification.")

    assert [a.type for a in notifications(en_base, scene["lecteur"].id)] == [
        "commentaire_approuve",
        "commentaire_depublie",
    ]
    nouvelles = notifications(en_base, scene["redactrice"].id)[avant:]
    assert [a.type for a in nouvelles] == ["article_commentaire"]
    assert "Le lavage des mains au lycée" in nouvelles[0].titre
    assert nouvelles[0].lien == f"/articles/{scene['adresse']}"


def test_lauteure_de_larticle_nest_pas_prevenue_de_son_propre_commentaire(
    scene: Any, en_base: Callable[..., Any]
) -> None:
    commentaire = envoyer(scene["navigateur_redactrice"], scene["adresse"], "Merci pour vos retours !")
    avant = len(notifications(en_base, scene["redactrice"].id))

    decider(scene["admin"], commentaire["id"], "approuver")

    assert [a.type for a in notifications(en_base, scene["redactrice"].id)[avant:]] == ["commentaire_approuve"]


def test_un_moderateur_de_dre_ne_voit_pas_les_commentaires_dune_autre_dre(
    client: TestClient, scene: Any, creer_collaborateur: Callable[..., Any]
) -> None:
    commentaire = envoyer(scene["navigateur"], scene["adresse"])
    regional = moderateur(client, creer_collaborateur, "regional", perimetre_dre="kara")

    assert regional.get(f"{FILE}/{commentaire['id']}").status_code == 404
    assert decider_brut(regional, commentaire["id"]).status_code == 404


def test_un_collaborateur_ne_commente_pas(client: TestClient, scene: Any, en_base: Callable[..., Any]) -> None:
    """Un collaborateur n'a pas de profil d'élève ni d'encadreur : il ne peut donc pas commenter."""
    reponse = scene["admin"].post(f"/api/articles/{scene['adresse']}/commentaires", json={"texte": "Bravo"})

    assert reponse.status_code == 403
    assert en_base(lambda db: db.scalar(select(Contenu.id).where(Contenu.type == "commentaire"))) is None


def decider_brut(navigateur: Any, contenu_id: str) -> Any:
    return navigateur.post(f"{FILE}/{contenu_id}/approuver", json={"version": 1})
