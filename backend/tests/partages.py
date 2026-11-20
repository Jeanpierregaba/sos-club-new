"""Aides communes aux tests des partages (spec 044) : un article publié, une déclaration de partage."""

from collections.abc import Callable
from typing import Any

from tests.commentaires import MODERATION
from tests.conftest import Navigateur, connecter_admin

PARTAGES_MOI = "/api/partages/moi"
DECIDER_PARTAGES = {("partages", "approuver")}
LIENS = {
    "facebook": "https://www.facebook.com/ama.golfe/posts/123456789",
    "instagram": "https://www.instagram.com/p/C0deP4rt4ge/",
    "tiktok": "https://www.tiktok.com/@ama.golfe/video/7300000000000000000",
    "linkedin": "https://www.linkedin.com/posts/ama-golfe_activity-7300000000000000000",
}


def declarer(navigateur: Any, adresse: str, reseau: str = "facebook", lien: str | None = None) -> Any:
    return navigateur.post(f"/api/articles/{adresse}/partages", json={"reseau": reseau, "lien": lien or LIENS[reseau]})


def declare(navigateur: Any, adresse: str, reseau: str = "facebook", lien: str | None = None) -> dict[str, Any]:
    reponse = declarer(navigateur, adresse, reseau, lien)
    assert reponse.status_code == 201, reponse.text
    return dict(reponse.json())


def etat_article(navigateur: Any, adresse: str) -> Any:
    return navigateur.get(f"/api/articles/{adresse}/partages/moi")


def moderateur_partages(
    client: Any, creer_collaborateur: Callable[..., Any], identifiant: str = "moderateur", **options: Any
) -> Navigateur:
    """Un collaborateur qui modère, avec le droit de décider des partages."""
    droits = options.pop("droits", MODERATION | DECIDER_PARTAGES)
    creer_collaborateur(identifiant, droits=droits, double_auth=True, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur
