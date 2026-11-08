"""Aides communes aux tests de l'espace du président (spec 026) : un club actif avec son président, un membre, un
encadreur rattaché, un élève extérieur, et un modérateur qui valide aussi les passations."""

from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Adhesion, ClubPassation, EtatAdhesion, EtatPassation, EtatRattachement, Rattachement
from tests.conftest import MOT_DE_PASSE, VERIFICATION_CLUBS, Navigateur, connecter_admin

FILE = "/api/admin/moderation"
FICHE = "/api/clubs/moi/fiche"
ACTUALITES = "/api/clubs/moi/actualites"
MODERATION = {("tableau_de_bord", "consulter"), ("moderation", "consulter"), ("moderation", "approuver"),
              ("moderation", "depublier")}  # fmt: skip


def espace(club_id: Any) -> str:
    return f"/api/clubs/{club_id}/espace"


def connecter(client: Any, identifiant: str) -> Navigateur:
    navigateur = Navigateur(client)
    reponse = navigateur.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text
    return navigateur


def adherer(en_base: Callable[..., Any], eleve: Any, club: Any, etat: EtatAdhesion = EtatAdhesion.active) -> Adhesion:
    async def inserer(db: AsyncSession) -> Adhesion:
        ligne = Adhesion(eleve_id=eleve.id, club_id=club.id, etat=etat)
        db.add(ligne)
        return ligne

    return en_base(inserer)


def rattacher(en_base: Callable[..., Any], encadreur: Any, club: Any) -> Rattachement:
    async def inserer(db: AsyncSession) -> Rattachement:
        ligne = Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=EtatRattachement.actif)
        db.add(ligne)
        return ligne

    return en_base(inserer)


def moderateur(
    client: Any, creer_collaborateur: Callable[..., Any], identifiant: str = "moderateur", **options: Any
) -> Navigateur:
    """Un collaborateur qui modère les contenus et valide les passations."""
    creer_collaborateur(identifiant, droits=MODERATION | VERIFICATION_CLUBS, double_auth=True, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


def decider(navigateur: Any, contenu_id: str, decision: str, motif: str | None = None) -> Any:
    lu = navigateur.get(f"{FILE}/{contenu_id}")
    assert lu.status_code == 200, lu.text
    corps: dict[str, Any] = {"version": lu.json()["version"]}
    if motif is not None:
        corps["motif"] = motif
    return navigateur.post(f"{FILE}/{contenu_id}/{decision}", json=corps)


def passer_la_main(en_base: Callable[..., Any], admin: Any, club: Any, successeur: Any) -> None:
    """Une passation en attente de l'admin, validée par lui (spec 019)."""

    async def inserer(db: AsyncSession) -> ClubPassation:
        ligne = ClubPassation(
            club_id=club.id, successeur_id=successeur.id, propose_par=club.president_id, etat=EtatPassation.en_attente
        )
        db.add(ligne)
        return ligne

    passation = en_base(inserer)
    reponse = admin.post(f"/api/admin/clubs/passations/{passation.id}/valider", json={})
    assert reponse.status_code == 200, reponse.text


def champs_actualite(**autres: Any) -> dict[str, Any]:
    return {
        "titre": "Journée de dépistage au lycée",
        "chapo": "Notre club a accueilli l'infirmière du district pour une matinée de sensibilisation.",
        "texte": "Plus de **cent élèves** sont passés par nos ateliers.",
        "axe_code": "sante-environnement",
        "afficher_club": True,
    } | autres


def scene(
    client: Any,
    creer_eleve: Callable[..., Any],
    creer_club: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    president = creer_eleve("president", "Zoé la Présidente")
    club = creer_club(president, nom="Club Santé du Lycée")
    membre = creer_eleve("membre", "Ama du Golfe", etablissement_id=club.etablissement_id)
    adherer(en_base, membre, club)
    exterieur = creer_eleve("exterieur", "Kofi des Plateaux", dre="kara")
    encadreur = creer_encadreur(etablissement_id=club.etablissement_id)
    rattacher(en_base, encadreur, club)
    return {
        "club": club,
        "president": president,
        "membre": membre,
        "exterieur": exterieur,
        "encadreur": encadreur,
        "admin": moderateur(client, creer_collaborateur),
        "nav_president": connecter(client, "president"),
        "nav_membre": connecter(client, "membre"),
        "nav_exterieur": connecter(client, "exterieur"),
        "nav_encadreur": connecter(client, "encadreur1"),
    }
