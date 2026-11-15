"""Rapports d'activité (spec 038) : dépôt, soumission, lecture et confidentialité. Partie critique (droits,
données de mineurs), écrite avant le code (docs/TESTING.md)."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.comptes.models import Utilisateur
from app.notifications.models import Notification
from app.points.service import aujourd_hui
from tests.conftest import Navigateur
from tests.espace_club import connecter
from tests.test_classements import rattacher

pytestmark = pytest.mark.usefixtures("annuaire")

RAPPORTS = "/api/rapports"
HIER = aujourd_hui() - timedelta(days=1)


def complet(**changements: Any) -> dict[str, Any]:
    donnees = {
        "titre": "Causerie sur le paludisme",
        "axe_code": "sante-environnement",
        "type_activite": "causerie",
        "date_activite": HIER.isoformat(),
        "lieu": "Cour du lycée",
        "responsable": "M. Agbeko",
        "objectifs": "Expliquer la prévention du paludisme.",
        "deroulement": "Exposé, questions, démonstration de la moustiquaire.",
        "resultats": "Les élèves savent installer une moustiquaire.",
        "participants": {"total": 40, "filles": 22, "garcons": 18},
    }
    return {**donnees, **changements}


@pytest.fixture
def club(
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> dict[str, Any]:
    """Un club en service avec sa présidente, deux encadreurs vérifiés, et un encadreur d'un autre club."""
    presidente = creer_eleve("presidente", "Ama")
    club = creer_club(presidente, nom="Club Santé Tokoin")
    prof = creer_encadreur("prof", etablissement_id=club.etablissement_id)
    collegue = creer_encadreur("collegue", etablissement_id=club.etablissement_id)
    for encadreur in (prof, collegue):
        rattacher(en_base, encadreur.id, club.id)
    ailleurs = creer_encadreur("ailleurs", dre="maritime")
    autre_president = creer_eleve("autre-president", "Kofi", dre="maritime")
    autre = creer_club(autre_president, nom="Club Santé Aného")
    rattacher(en_base, ailleurs.id, autre.id)
    return {"club": club, "presidente": presidente, "prof": prof, "collegue": collegue, "ailleurs": ailleurs}


def brouillon(navigateur: Navigateur, modele: str = "activite", donnees: dict[str, Any] | None = None) -> dict:
    reponse = navigateur.post(RAPPORTS, json={"modele": modele})
    assert reponse.status_code == 201, reponse.text
    rapport = reponse.json()
    if donnees is not None:
        reponse = navigateur.put(
            f"{RAPPORTS}/{rapport['id']}", json={"version": rapport["version"], "donnees": donnees}
        )
        assert reponse.status_code == 200, reponse.text
        rapport = reponse.json()
    return rapport


def soumettre(navigateur: Navigateur, rapport: dict) -> Any:
    return navigateur.post(f"{RAPPORTS}/{rapport['id']}/soumission", json={"version": rapport["version"]})


def notifications(en_base: Callable[..., Any], qui: Utilisateur) -> list[Notification]:
    return list(en_base(lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == qui.id))).all())


# Dépôt ---------------------------------------------------------------------------------------------------------


def test_un_encadreur_soumet_un_rapport_et_le_club_est_prevenu(
    client: TestClient, club: dict[str, Any], en_base: Callable[..., Any]
) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof, donnees=complet())

    reponse = soumettre(prof, rapport)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["etat"] == "soumis"
    assert corps["reference"].startswith(f"RA-{aujourd_hui().year}-")
    assert corps["club"]["nom"] == "Club Santé Tokoin"
    for qui in (club["collegue"], club["presidente"]):
        (avis,) = notifications(en_base, qui)
        assert corps["reference"] in avis.titre and avis.lien == f"/rapports/{corps['id']}"
    assert notifications(en_base, club["prof"]) == []


def test_la_reference_reste_et_chaque_rapport_a_la_sienne(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    premier = soumettre(prof, brouillon(prof, donnees=complet())).json()
    second = soumettre(prof, brouillon(prof, donnees=complet(type_activite="sensibilisation"))).json()

    assert premier["reference"] != second["reference"]


def test_la_presidente_depose_un_rapport_dactivite_seulement(client: TestClient, club: dict[str, Any]) -> None:
    presidente = connecter(client, "presidente")

    assert soumettre(presidente, brouillon(presidente, donnees=complet())).status_code == 200
    assert presidente.post(RAPPORTS, json={"modele": "mensuel"}).status_code == 403
    assert presidente.post(RAPPORTS, json={"modele": "bilan"}).status_code == 403


def test_un_eleve_qui_nest_pas_president_ne_depose_rien(
    client: TestClient, club: dict[str, Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    creer_eleve("membre", "Yao")

    assert connecter(client, "membre").post(RAPPORTS, json={"modele": "activite"}).status_code == 403


def test_un_encadreur_non_verifie_ne_depose_rien(
    client: TestClient, club: dict[str, Any], creer_encadreur: Callable[..., Utilisateur]
) -> None:
    from app.encadreurs.models import EtatVerification

    creer_encadreur("nouveau", etat=EtatVerification.en_attente)

    assert connecter(client, "nouveau").post(RAPPORTS, json={"modele": "activite"}).status_code == 403


def test_un_champ_manquant_bloque_la_soumission_et_garde_le_brouillon(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof, donnees=complet(lieu="", participants={"total": None}))

    reponse = soumettre(prof, rapport)

    assert reponse.status_code == 422
    assert "le lieu" in reponse.json()["detail"] and "le nombre de participants" in reponse.json()["detail"]
    assert prof.get(f"{RAPPORTS}/{rapport['id']}").json()["etat"] == "brouillon"


@pytest.mark.parametrize(
    "donnees",
    [
        complet(participants={"total": -1}),
        complet(participants={"total": 10, "filles": 8, "garcons": 5}),
        complet(videos=["https://vimeo.com/123456"]),
        complet(champ_inconnu="x"),
    ],
)
def test_des_champs_invalides_sont_refuses(client: TestClient, club: dict[str, Any], donnees: dict) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)

    reponse = prof.put(f"{RAPPORTS}/{rapport['id']}", json={"version": rapport["version"], "donnees": donnees})

    assert reponse.status_code == 422


def test_un_lien_youtube_est_garde_par_son_identifiant(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")

    rapport = brouillon(prof, donnees=complet(videos=["https://youtu.be/dQw4w9WgXcQ"]))

    assert rapport["donnees"]["videos"] == ["dQw4w9WgXcQ"]


@pytest.mark.parametrize("decalage", [-1, 400])
def test_une_date_future_ou_trop_ancienne_est_refusee(client: TestClient, club: dict[str, Any], decalage: int) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof, donnees=complet(date_activite=(aujourd_hui() - timedelta(days=decalage)).isoformat()))

    assert soumettre(prof, rapport).status_code == 422


def test_un_type_dactivite_inconnu_est_refuse(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof)

    reponse = prof.put(
        f"{RAPPORTS}/{rapport['id']}", json={"version": rapport["version"], "donnees": complet(type_activite="fete")}
    )

    assert reponse.status_code == 422


def test_une_version_soumise_ne_se_modifie_plus(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = soumettre(prof, brouillon(prof, donnees=complet())).json()

    reponse = prof.put(f"{RAPPORTS}/{rapport['id']}", json={"version": rapport["version"], "donnees": complet()})

    assert reponse.status_code == 409


def test_un_brouillon_se_supprime_pas_un_rapport_soumis(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    a_jeter = brouillon(prof)
    soumis = soumettre(prof, brouillon(prof, donnees=complet())).json()

    assert prof.delete(f"{RAPPORTS}/{a_jeter['id']}").status_code == 204
    assert prof.get(f"{RAPPORTS}/{a_jeter['id']}").status_code == 404
    assert prof.delete(f"{RAPPORTS}/{soumis['id']}").status_code == 409


def test_un_doublon_probable_est_signale_sans_bloquer(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    presidente = connecter(client, "presidente")
    premier = soumettre(prof, brouillon(prof, donnees=complet())).json()

    second = soumettre(presidente, brouillon(presidente, donnees=complet(titre="Même causerie"))).json()

    assert second["etat"] == "soumis"
    assert second["doublons_probables"] == [premier["reference"]]


# Lecture et confidentialité -------------------------------------------------------------------------------------


def test_un_brouillon_nest_vu_que_de_son_auteur(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = brouillon(prof, donnees=complet())

    for autre in ("collegue", "presidente", "ailleurs"):
        assert connecter(client, autre).get(f"{RAPPORTS}/{rapport['id']}").status_code == 404


def test_les_encadreurs_du_club_lisent_et_consultent(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = soumettre(prof, brouillon(prof, donnees=complet())).json()
    lectures = prof.get(RAPPORTS).json()["rapports"][0]["lectures"]
    assert lectures == [{"nom": lectures[0]["nom"], "consulte_le": None}]

    collegue = connecter(client, "collegue")
    lu = collegue.get(f"{RAPPORTS}/{rapport['id']}")

    assert lu.status_code == 200 and lu.json()["donnees"]["titre"] == "Causerie sur le paludisme"
    assert lu.json()["mien"] is False and lu.json()["modifiable"] is False
    assert prof.get(RAPPORTS).json()["rapports"][0]["lectures"][0]["consulte_le"] is not None
    assert [r["id"] for r in collegue.get(RAPPORTS).json()["rapports"]] == [rapport["id"]]
    assert connecter(client, "ailleurs").get(f"{RAPPORTS}/{rapport['id']}").status_code == 404


def test_la_presidente_ne_voit_pas_les_mensuels(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    debut = aujourd_hui().replace(day=1)
    mois = (debut - timedelta(days=1)).replace(day=1)
    mensuel = soumettre(prof, brouillon(prof, "mensuel", {"mois": mois.isoformat(), "synthese": "Un mois actif."}))
    assert mensuel.status_code == 200, mensuel.text

    presidente = connecter(client, "presidente")

    assert presidente.get(f"{RAPPORTS}/{mensuel.json()['id']}").status_code == 404
    assert presidente.get(RAPPORTS).json()["rapports"] == []


def test_un_mensuel_se_soumet_apres_la_fin_du_mois(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    suivant = (aujourd_hui().replace(day=28) + timedelta(days=4)).replace(day=1)
    rapport = brouillon(prof, "mensuel", {"mois": suivant.isoformat(), "synthese": "Trop tôt."})

    assert soumettre(prof, rapport).status_code == 422


def test_un_anonyme_ne_lit_rien(client: TestClient, club: dict[str, Any]) -> None:
    prof = connecter(client, "prof")
    rapport = soumettre(prof, brouillon(prof, donnees=complet())).json()

    assert client.get(f"{RAPPORTS}/{rapport['id']}").status_code == 401
    assert client.get(RAPPORTS).status_code == 401


def test_les_types_dactivite_actifs(client: TestClient, club: dict[str, Any]) -> None:
    types = connecter(client, "prof").get(f"{RAPPORTS}/types-activite").json()

    assert types[0] == {"code": "causerie", "libelle": "Causerie éducative"}
