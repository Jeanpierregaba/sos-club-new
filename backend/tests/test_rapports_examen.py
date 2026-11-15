# ruff: noqa: F811
"""Examen des rapports et points (spec 038) : approbation, doublon, mensuel et bilan, correction, refus, périmètre,
concurrence. Partie critique (points, ADR-0004), écrite avant le code."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces
from app.admin.models import Collaborateur
from app.clubs.models import EtatClub
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.encadreurs.models import Encadreur, EtatVerification
from app.moderation import decisions
from app.moderation.models import Contenu
from app.notifications.models import Notification
from app.points.models import MouvementPoints, Semestre
from app.points.service import aujourd_hui
from tests.bibliotheque import pdf
from tests.conftest import Navigateur, connecter_admin, moteur_test
from tests.espace_club import connecter
from tests.test_classements import etat_club
from tests.test_clotures import termine  # noqa: F401
from tests.test_rapports import RAPPORTS, brouillon, club, complet, soumettre  # noqa: F401
from tests.test_rapports_pieces import envoyer

pytestmark = pytest.mark.usefixtures("annuaire")

FILE = "/api/admin/moderation"
MODERATION = {("tableau_de_bord", "consulter"), ("moderation", "consulter"), ("moderation", "approuver")}
MOTIF = "Il manque la liste des intervenants."


def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any], **options: Any) -> Navigateur:
    identifiant = options.pop("identifiant", "moderateur")
    creer_collaborateur(identifiant, droits=MODERATION, double_auth=True, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


@pytest.fixture
def equipe(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    return moderateur(client, creer_collaborateur)


def decider(equipe: Navigateur, rapport_id: str, decision: str, **corps: Any) -> Any:
    version = equipe.get(f"{FILE}/{rapport_id}").json()["version"]
    return equipe.post(f"{FILE}/{rapport_id}/{decision}", json={"version": version, **corps})


def depose(client: TestClient, qui: str, modele: str = "activite", donnees: dict | None = None) -> dict:
    navigateur = connecter(client, qui)
    reponse = soumettre(navigateur, brouillon(navigateur, modele, donnees if donnees is not None else complet()))
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def lignes(en_base: Callable[..., Any]) -> list[tuple[str | None, str, int, int | None]]:
    """(identifiant ou None pour le club, action, montant, demi-points du club), dans l'ordre d'écriture."""
    return [
        tuple(l)
        for l in en_base(
            lambda db: db.execute(
                select(
                    Utilisateur.identifiant,
                    MouvementPoints.action,
                    MouvementPoints.montant,
                    MouvementPoints.demi_points_club,
                )
                .outerjoin(Utilisateur, Utilisateur.id == MouvementPoints.utilisateur_id)
                .where(MouvementPoints.action.like("%rapport%") | MouvementPoints.action.like("%bilan%"))
                .order_by(MouvementPoints.cree_le, MouvementPoints.id)
            )
        ).all()
    ]


def mois_precedent() -> str:
    return (aujourd_hui().replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()


# Approbation et points -----------------------------------------------------------------------------------------


def test_un_rapport_dencadreur_approuve_credite_lencadreur_et_le_club_une_fois(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    rapport = depose(client, "prof")

    reponse = decider(equipe, rapport["id"], "approuver")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["rapport"]["points_auteur"] == 100
    assert lignes(en_base) == [
        ("prof", "encadreur.rapport_activite", 100, None),
        (None, "club.rapport_activite", 50, 100),
    ]
    assert decider(equipe, rapport["id"], "approuver").status_code == 409
    assert len(lignes(en_base)) == 2
    vu = connecter(client, "prof").get(f"{RAPPORTS}/{rapport['id']}").json()
    assert (vu["etat"], vu["points"]) == ("approuve", 100)
    titres = [
        n.titre
        for n in en_base(
            lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == club["collegue"].id))
        ).all()
    ]
    assert any("est approuvé" in t for t in titres)


def test_le_rapport_de_la_presidente_ne_credite_que_le_club(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    rapport = depose(client, "presidente")

    assert decider(equipe, rapport["id"], "approuver").status_code == 200
    assert lignes(en_base) == [(None, "club.rapport_activite", 50, 100)]


def test_un_doublon_approuve_ne_credite_rien_et_reste_lie(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    premier = depose(client, "prof")
    second = depose(client, "presidente", donnees=complet(titre="La même causerie"))
    apercu = equipe.get(f"{FILE}/{second['id']}").json()["rapport"]
    assert [v["reference"] for v in apercu["doublons_probables"]] == [premier["reference"]]

    assert decider(equipe, second["id"], "approuver", doublon_de=premier["id"]).status_code == 422
    decider(equipe, premier["id"], "approuver")
    reponse = decider(equipe, second["id"], "approuver", doublon_de=premier["id"])

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["rapport"]["doublon_de"]["reference"] == premier["reference"]
    assert len(lignes(en_base)) == 2
    vu = connecter(client, "presidente").get(f"{RAPPORTS}/{second['id']}").json()
    assert vu["doublon_de"] == premier["reference"]


def test_un_doublon_se_lie_seulement_au_meme_club(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, creer_eleve: Callable[..., Utilisateur]
) -> None:
    from tests.test_classements import rattacher

    ailleurs = depose(client, "ailleurs")
    decider(equipe, ailleurs["id"], "approuver")
    rapport = depose(client, "prof")
    assert rattacher is not None

    assert decider(equipe, rapport["id"], "approuver", doublon_de=ailleurs["id"]).status_code == 422
    assert decider(equipe, rapport["id"], "approuver", doublon_de=rapport["id"]).status_code == 422


def test_un_second_mensuel_du_meme_mois_ne_credite_rien(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    donnees = {"mois": mois_precedent(), "synthese": "Trois causeries."}
    premier = depose(client, "prof", "mensuel", donnees)
    second = depose(client, "prof", "mensuel", {**donnees, "titre": "Encore"})
    assert second["doublons_probables"] == [premier["reference"]]

    for rapport in (premier, second):
        assert decider(equipe, rapport["id"], "approuver").status_code == 200

    assert lignes(en_base) == [("prof", "encadreur.rapport_mensuel", 75, None)]
    assert connecter(client, "prof").get(f"{RAPPORTS}/{second['id']}").json()["points"] is None


def test_deux_bilans_du_semestre_creditent_chaque_encadreur_et_le_club_une_fois(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any], termine: Semestre
) -> None:
    donnees = {"semestre_id": str(termine.id), "synthese": "Un semestre riche.", "resultats": "12 activités."}
    for qui in ("prof", "collegue"):
        rapport = depose(client, qui, "bilan", donnees)
        assert decider(equipe, rapport["id"], "approuver").status_code == 200

    assert lignes(en_base) == [
        ("prof", "encadreur.bilan_semestriel", 200, None),
        (None, "club.bilan_semestriel", 100, 200),
        ("collegue", "encadreur.bilan_semestriel", 200, None),
    ]


def test_un_bilan_se_soumet_apres_la_fin_du_semestre(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    async def inserer(db: AsyncSession) -> Semestre:
        element = Semestre(
            libelle="En cours", debut=aujourd_hui() - timedelta(days=5), fin=aujourd_hui() + timedelta(days=5)
        )
        db.add(element)
        return element

    en_cours = en_base(inserer)
    prof = connecter(client, "prof")
    rapport = brouillon(prof, "bilan", {"semestre_id": str(en_cours.id), "synthese": "Trop tôt.", "resultats": "-"})

    assert soumettre(prof, rapport).status_code == 422


def test_une_correction_garde_lhistorique_et_les_documents(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    prof = connecter(client, "prof")
    rapport = envoyer(prof, brouillon(prof, donnees=complet()), pdf()).json()
    rapport = soumettre(prof, rapport).json()
    (document,) = equipe.get(f"{FILE}/{rapport['id']}").json()["rapport"]["documents"]
    assert equipe.get(f"/api/admin/rapports/{rapport['id']}/documents/{document['id']}").status_code == 200

    assert decider(equipe, rapport["id"], "corriger", motif="Court").status_code == 422
    assert decider(equipe, rapport["id"], "corriger", motif=MOTIF).status_code == 200
    assert lignes(en_base) == []

    a_corriger = prof.get(f"{RAPPORTS}/{rapport['id']}").json()
    assert a_corriger["etat"] == "a_corriger" and a_corriger["modifiable"] is True
    corrige = prof.put(
        f"{RAPPORTS}/{rapport['id']}",
        json={"version": a_corriger["version"], "donnees": complet(deroulement="Exposé par M. Agbeko et Mme Sena.")},
    ).json()
    assert len(corrige["documents"]) == 1
    renvoye = soumettre(prof, corrige).json()
    assert (renvoye["etat"], renvoye["reference"]) == ("soumis", rapport["reference"])
    assert [(d["decision"], d["motif"]) for d in renvoye["historique"]] == [("corriger", MOTIF)]
    assert decider(equipe, rapport["id"], "approuver").status_code == 200
    assert len(lignes(en_base)) == 2


def test_un_rapport_refuse_ne_credite_rien(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    rapport = depose(client, "prof")

    assert decider(equipe, rapport["id"], "refuser", motif="Activité non réalisée.").status_code == 200

    assert lignes(en_base) == []
    assert connecter(client, "prof").get(f"{RAPPORTS}/{rapport['id']}").json()["etat"] == "refuse"


def test_un_rapport_ne_se_depublie_pas(client: TestClient, club: dict[str, Any], equipe: Navigateur) -> None:
    rapport = depose(client, "prof")
    decider(equipe, rapport["id"], "approuver")

    assert decider(equipe, rapport["id"], "depublier", motif="Retrait demandé.").status_code in (403, 409)


def test_un_encadreur_qui_nest_plus_verifie_nest_pas_approuve(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    rapport = depose(client, "prof")
    en_base(
        lambda db: db.execute(
            update(Encadreur)
            .where(Encadreur.utilisateur_id == club["prof"].id)
            .values(etat=EtatVerification.en_attente)
        )
    )

    assert decider(equipe, rapport["id"], "approuver").status_code == 409
    assert lignes(en_base) == []


def test_un_club_suspendu_ne_recoit_pas_sa_part(
    client: TestClient, club: dict[str, Any], equipe: Navigateur, en_base: Callable[..., Any]
) -> None:
    rapport = depose(client, "prof")
    etat_club(en_base, club["club"].id, EtatClub.suspendu)

    assert decider(equipe, rapport["id"], "approuver").status_code == 200
    assert lignes(en_base) == [("prof", "encadreur.rapport_activite", 100, None)]


def test_un_moderateur_dune_autre_dre_ne_voit_pas_le_rapport(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    prof = connecter(client, "prof")
    rapport = soumettre(prof, envoyer(prof, brouillon(prof, donnees=complet()), pdf()).json()).json()
    kara = moderateur(client, creer_collaborateur, identifiant="kara", perimetre_dre="kara")

    assert kara.get(f"{FILE}/{rapport['id']}").status_code == 404
    piece = rapport["documents"][0]["id"]
    assert kara.get(f"/api/admin/rapports/{rapport['id']}/documents/{piece}").status_code == 404
    assert prof.get(f"/api/admin/rapports/{rapport['id']}/documents/{piece}").status_code in (401, 403)


def test_deux_approbations_simultanees_ne_creditent_quune_fois(
    client: TestClient,
    club: dict[str, Any],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    rapport = depose(client, "prof")
    chefs = [creer_collaborateur(nom, droits=MODERATION, double_auth=True) for nom in ("chef1", "chef2")]

    async def une(chef: Utilisateur) -> bool:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
            acces = Acces(
                utilisateur=await db.get(Utilisateur, chef.id),  # type: ignore[arg-type]
                collaborateur=collaborateur,  # type: ignore[arg-type]
                droits={("moderation", Action.consulter), ("moderation", Action.approuver)},
                double_auth_active=True,
            )
            version = (await db.get(Contenu, UUID(rapport["id"]))).version  # type: ignore[union-attr]
            try:
                await decisions.approuver(db, acces, UUID(rapport["id"]), version, "127.0.0.1")
            except Refus as refus:
                assert refus.statut == 409
                return False
            return True

    async def scenario() -> list[bool]:
        return await asyncio.gather(*(une(chef) for chef in chefs))

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert len(lignes(en_base)) == 2
