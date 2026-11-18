"""Événements de club (spec 041) : droits, brouillons, soumission, approbation, invitations, annulation.

Partie critique (droits, points, rien de public avant l'approbation), écrite avant le code (docs/TESTING.md)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.clubs.models import Club, EtatClub
from app.points.models import MouvementPoints
from tests.agenda import (
    CLUB,
    brouillon,
    champs,
    club,
    connecter,
    decider,
    ligne,
    moderateur,
    notifications,
    plus_tard,
    propose,
    publie,
    soumettre,
)
from tests.conftest import Navigateur

__all__ = ["club"]

pytestmark = pytest.mark.usefixtures("annuaire")


def points(en_base: Callable[..., Any], qui: Any) -> list[MouvementPoints]:
    return list(
        en_base(lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == qui.id))).all()
    )


# Droits et brouillons --------------------------------------------------------------------------------------


@pytest.mark.parametrize("qui", ["prof", "presidente"])
def test_un_encadreur_ou_la_presidente_propose_un_evenement(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any], qui: str
) -> None:
    navigateur = connecter(client, qui)
    evenement = brouillon(navigateur)
    assert evenement["etat"] == "brouillon"
    assert evenement["de_moi"] is True

    reponse = soumettre(navigateur, evenement)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "en_attente"
    # Rien de public avant l'approbation.
    assert ligne(en_base, evenement["id"]) is None
    autres = {"prof": ("collegue", "presidente"), "presidente": ("prof", "collegue")}[qui]
    for nom in autres:
        (avis,) = notifications(en_base, club[nom], "evenement_soumis")
        assert avis.lien == f"/mon-club/agenda/{evenement['id']}"


# Un encadreur d'un autre club tient l'agenda du sien, sans voir celui-ci (test suivant).
@pytest.mark.parametrize("qui", ["membre", "simple"])
def test_les_autres_ne_tiennent_pas_lagenda_du_club(client: TestClient, club: dict[str, Any], qui: str) -> None:
    navigateur = connecter(client, qui)
    prof = connecter(client, "prof")
    evenement = brouillon(prof)

    assert navigateur.post(CLUB, json=champs()).status_code == 403
    assert navigateur.get(CLUB).status_code == 403
    assert navigateur.get(f"{CLUB}/{evenement['id']}").status_code in (403, 404)


def test_un_encadreur_dun_autre_club_ne_voit_pas_levenement(client: TestClient, club: dict[str, Any]) -> None:
    evenement = brouillon(connecter(client, "prof"))
    soumettre(connecter(client, "prof"), evenement)
    ailleurs = connecter(client, "ailleurs")

    assert ailleurs.get(f"{CLUB}/{evenement['id']}").status_code == 404
    assert [e["id"] for e in ailleurs.get(CLUB).json()["evenements"]] == []


def test_un_brouillon_reste_prive_a_son_auteur(client: TestClient, club: dict[str, Any]) -> None:
    evenement = brouillon(connecter(client, "prof"))
    collegue = connecter(client, "collegue")

    assert collegue.get(CLUB).json()["evenements"] == []
    assert collegue.get(f"{CLUB}/{evenement['id']}").status_code == 404


def test_seul_lauteur_modifie_son_evenement(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    evenement = propose(prof)
    collegue = connecter(client, "collegue")
    corps = {"version": evenement["version"], "champs": champs(titre="Autre titre")}

    assert collegue.get(f"{CLUB}/{evenement['id']}").json()["peut_modifier"] is False
    assert collegue.put(f"{CLUB}/{evenement['id']}", json=corps).status_code == 404


@pytest.mark.parametrize(
    "changements",
    [
        {"fin": plus_tard(heure=8).isoformat(timespec="minutes")},
        {"en_ligne": True, "lien": None},
        {"en_ligne": True, "lien": "http://exemple.tg/salle"},
        {"lieu": None},
        {"titre": "a"},
        {"axe_code": "axe-inconnu"},
        {"places": 0},
    ],
)
def test_une_saisie_incoherente_est_refusee(
    client: TestClient, club: dict[str, Any], changements: dict[str, Any]
) -> None:
    reponse = connecter(client, "prof").post(CLUB, json=champs(**changements))

    assert reponse.status_code == 422, reponse.text


def test_un_evenement_qui_commence_dans_le_passe_ne_se_soumet_pas(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    hier = (datetime.now(UTC) - timedelta(days=1)).replace(tzinfo=None, second=0, microsecond=0)
    evenement = brouillon(
        prof,
        debut=hier.isoformat(timespec="minutes"),
        fin=(hier + timedelta(hours=2)).isoformat(timespec="minutes"),
    )

    reponse = soumettre(prof, evenement)

    assert reponse.status_code == 422
    assert "passé" in reponse.json()["detail"]


def test_un_club_suspendu_ne_propose_plus(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    en_base(lambda db: db.execute(update(Club).where(Club.id == club["club"].id).values(etat=EtatClub.suspendu)))

    assert connecter(client, "prof").post(CLUB, json=champs()).status_code == 403


def test_un_brouillon_jamais_soumis_se_supprime(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    evenement = brouillon(prof)

    reponse = prof.delete(f"{CLUB}/{evenement['id']}", params={"version": evenement["version"]})

    assert reponse.status_code == 204
    assert prof.get(CLUB).json()["evenements"] == []


# Approbation ---------------------------------------------------------------------------------------------------


def test_lapprobation_publie_credite_lencadreur_et_invite_les_membres(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur, "prof", titre="Journée de salubrité")

    copie = ligne(en_base, evenement["id"])
    assert copie is not None and copie.publie and copie.titre == "Journée de salubrité"
    assert copie.club_id == club["club"].id and copie.niveau.value == "club"
    assert [(m.action, m.montant) for m in points(en_base, club["prof"])][-1:] == [("encadreur.evenement", 30)]
    for membre in ("presidente", "membre", "membre2"):
        (invitation,) = notifications(en_base, club[membre], "evenement_invitation")
        assert invitation.lien == f"/agenda/{evenement['id']}"
    assert notifications(en_base, club["simple"], "evenement_invitation") == []


def test_la_presidente_ne_recoit_pas_de_points(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    avant = len(points(en_base, club["presidente"]))

    publie(client, creer_collaborateur, "presidente")

    assert len(points(en_base, club["presidente"])) == avant


def test_les_heures_saisies_a_lome_restent_les_memes(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    debut = plus_tard(jours=10, heure=14)
    evenement = publie(
        client,
        creer_collaborateur,
        debut=debut.isoformat(timespec="minutes"),
        fin=(debut + timedelta(hours=1)).isoformat(timespec="minutes"),
    )

    copie = ligne(en_base, evenement["id"])
    assert copie is not None
    assert copie.debut == debut.replace(tzinfo=UTC)
    assert copie.debut.tzinfo is not None


def test_une_modification_approuvee_est_recopiee_sans_points_ni_invitation(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)
    prof = connecter(client, "prof")
    membre = connecter(client, "membre2")
    membre.put(f"/api/agenda/{evenement['id']}/reponse", json={"reponse": "non"})
    actuel = prof.get(f"{CLUB}/{evenement['id']}").json()
    nouveau_debut = plus_tard(jours=8)
    modifie = prof.put(
        f"{CLUB}/{evenement['id']}",
        json={
            "version": actuel["version"],
            "champs": champs(
                titre="Causerie déplacée",
                debut=nouveau_debut.isoformat(timespec="minutes"),
                fin=(nouveau_debut + timedelta(hours=2)).isoformat(timespec="minutes"),
            ),
        },
    ).json()
    # La version en ligne reste jusqu'à la décision.
    assert ligne(en_base, evenement["id"]).titre == "Causerie sur le paludisme"
    assert soumettre(prof, modifie).status_code == 200
    equipe = moderateur(client, creer_collaborateur, "equipe2")

    assert decider(equipe, evenement["id"], "approuver").status_code == 200

    assert ligne(en_base, evenement["id"]).titre == "Causerie déplacée"
    assert [m.action for m in points(en_base, club["prof"])].count("encadreur.evenement") == 1
    assert len(notifications(en_base, club["membre"], "evenement_invitation")) == 1
    assert len(notifications(en_base, club["membre"], "evenement_modifie")) == 1
    assert notifications(en_base, club["membre2"], "evenement_modifie") == []


def test_sans_le_droit_de_lagenda_on_ne_decide_pas(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    from tests.agenda import MODERATION

    evenement = propose(connecter(client, "prof"))
    equipe = moderateur(client, creer_collaborateur, "moderateur", MODERATION)

    assert decider(equipe, evenement["id"], "approuver").status_code == 403


def test_refus_et_correction_exigent_un_motif_de_dix_caracteres(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = propose(connecter(client, "prof"))
    equipe = moderateur(client, creer_collaborateur)

    assert decider(equipe, evenement["id"], "refuser", "Non").status_code == 422
    assert decider(equipe, evenement["id"], "corriger").status_code == 422
    assert decider(equipe, evenement["id"], "corriger", "Précise le lieu exact.").status_code == 200
    vue = connecter(client, "prof").get(f"{CLUB}/{evenement['id']}").json()
    assert vue["etat"] == "a_corriger" and vue["motif_decision"] == "Précise le lieu exact."


def test_retirer_du_site_depublie_lagenda(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)
    equipe = moderateur(client, creer_collaborateur, "retrait")

    assert decider(equipe, evenement["id"], "depublier", "Signalé par l'établissement").status_code == 200

    assert ligne(en_base, evenement["id"]).publie is False


# Annulation ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("qui", ["prof", "collegue", "presidente"])
def test_un_gestionnaire_annule_avec_un_motif_et_les_invites_sont_prevenus(
    client: TestClient,
    club: dict[str, Any],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
    qui: str,
) -> None:
    evenement = publie(client, creer_collaborateur)
    navigateur = connecter(client, qui)

    assert navigateur.post(f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Court"}).status_code == 422
    reponse = navigateur.post(f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Examens avancés d'une semaine"})

    assert reponse.status_code == 200, reponse.text
    copie = ligne(en_base, evenement["id"])
    assert copie.publie and copie.annule_le is not None
    (avis,) = notifications(en_base, club["membre"], "evenement_annule")
    assert avis.message == "Examens avancés d'une semaine"
    journal = en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "evenement_annule")))
    assert [j.cible_id for j in journal.all()] == [evenement["id"]]
    assert navigateur.post(f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Une seconde fois"}).status_code == 409


def test_un_evenement_annule_ne_se_modifie_plus(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)
    prof: Navigateur = connecter(client, "prof")
    prof.post(f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Examens avancés d'une semaine"})
    actuel = prof.get(f"{CLUB}/{evenement['id']}").json()

    reponse = prof.put(f"{CLUB}/{evenement['id']}", json={"version": actuel["version"], "champs": champs()})

    assert reponse.status_code == 409
    assert actuel["peut_modifier"] is False


# Suites de la relecture -------------------------------------------------------------------------------------


def test_un_evenement_devenu_passe_ne_sapprouve_pas(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.moderation.models import VersionContenu

    evenement = propose(connecter(client, "prof"))
    hier = (datetime.now(UTC) - timedelta(days=1)).replace(tzinfo=None)

    async def vieillir(db: Any) -> None:
        version = await db.scalar(select(VersionContenu).where(VersionContenu.contenu_id == UUID(evenement["id"])))
        version.donnees = {
            **version.donnees,
            "debut": hier.isoformat(timespec="minutes"),
            "fin": (hier + timedelta(hours=1)).isoformat(timespec="minutes"),
        }

    en_base(vieillir)
    equipe = moderateur(client, creer_collaborateur)

    reponse = decider(equipe, evenement["id"], "approuver")

    assert reponse.status_code == 409
    assert ligne(en_base, evenement["id"]) is None
    assert [m.action for m in points(en_base, club["prof"])].count("encadreur.evenement") == 0


def test_une_revision_en_attente_dun_evenement_annule_ne_se_publie_pas(
    client: TestClient, club: dict[str, Any], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    evenement = publie(client, creer_collaborateur)
    prof = connecter(client, "prof")
    actuel = prof.get(f"{CLUB}/{evenement['id']}").json()
    modifie = prof.put(
        f"{CLUB}/{evenement['id']}", json={"version": actuel["version"], "champs": champs(titre="Nouveau titre")}
    ).json()
    assert soumettre(prof, modifie).status_code == 200
    connecter(client, "collegue").post(
        f"{CLUB}/{evenement['id']}/annuler", json={"motif": "Salle indisponible ce jour"}
    )
    equipe = moderateur(client, creer_collaborateur, "equipe-revision")

    assert decider(equipe, evenement["id"], "approuver").status_code == 409

    assert ligne(en_base, evenement["id"]).titre == "Causerie sur le paludisme"
    assert notifications(en_base, club["membre"], "evenement_modifie") == []


def test_un_evenement_de_club_se_soumet_avec_son_axe(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")

    reponse = soumettre(prof, brouillon(prof, axe_code=None))

    assert reponse.status_code == 422
    assert "axe" in reponse.json()["detail"]
