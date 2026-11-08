"""Aides communes aux tests des commentaires (spec 025) : un article publié, des navigateurs connectés, l'envoi
d'un commentaire et les décisions du modérateur."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.moderation.models import Contenu
from app.notifications.models import Notification
from app.points.models import MouvementPoints
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin

PUBLICS = "/api/articles"
ARTICLES = "/api/mes-articles"
MIENS = "/api/mes-commentaires"
FILE = "/api/admin/moderation"
MODERATION = {("tableau_de_bord", "consulter"), ("moderation", "consulter"), ("moderation", "approuver"),
              ("moderation", "depublier")}  # fmt: skip


def connecter(client: Any, identifiant: str) -> Navigateur:
    navigateur = Navigateur(client)
    reponse = navigateur.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text
    return navigateur


def moderateur(
    client: Any, creer_collaborateur: Callable[..., Any], identifiant: str = "moderateur", **options: Any
) -> Navigateur:
    creer_collaborateur(identifiant, droits=MODERATION, double_auth=True, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


def decider(moderateur: Any, contenu_id: str, decision: str, motif: str | None = None) -> Any:
    lu = moderateur.get(f"{FILE}/{contenu_id}")
    assert lu.status_code == 200, lu.text
    corps: dict[str, Any] = {"version": lu.json()["version"]}
    if motif is not None:
        corps["motif"] = motif
    return moderateur.post(f"{FILE}/{contenu_id}/{decision}", json=corps)


def publier_article(auteur: Any, moderateur: Any, titre: str = "Le lavage des mains au lycée") -> str:
    """Un article publié ; renvoie son adresse publique."""
    article = auteur.post(
        ARTICLES,
        json={
            "titre": titre,
            "chapo": "Notre club a installé trois points d'eau dans la cour.",
            "texte": "Parce que les mains transportent les microbes.",
            "axe_code": "sante-environnement",
            "afficher_club": True,
        },
    ).json()
    soumis = auteur.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"]})
    assert soumis.status_code == 200, soumis.text
    approuve = decider(moderateur, article["id"], "approuver")
    assert approuve.status_code == 200, approuve.text
    return str(approuve.json()["adresse"])


def commenter(navigateur: Any, adresse: str, texte: str = "Bravo au club, on fait pareil chez nous !") -> Any:
    return navigateur.post(f"{PUBLICS}/{adresse}/commentaires", json={"texte": texte})


def envoyer(navigateur: Any, adresse: str, texte: str = "Bravo au club, on fait pareil chez nous !") -> dict[str, Any]:
    reponse = commenter(navigateur, adresse, texte)
    assert reponse.status_code == 201, reponse.text
    return dict(reponse.json())


def publics(client: Any, adresse: str, page: int = 1) -> Any:
    return client.get(f"{PUBLICS}/{adresse}/commentaires", params={"page": page})


def lignes(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[MouvementPoints]:
    return list(
        en_base(lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == utilisateur_id)))
    )


def notifications(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[Notification]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(Notification).where(Notification.utilisateur_id == utilisateur_id).order_by(Notification.cree_le)
            )
        )
    )


def contenu(en_base: Callable[..., Any], contenu_id: str) -> Contenu:
    return en_base(lambda db: db.get(Contenu, UUID(contenu_id)))
