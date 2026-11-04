"""Espace de l'élève (spec 017) : ses points, son profil, son mot de passe. Il ne voit que ses propres données."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from app.comptes.models import Role, Utilisateur
from app.config import settings
from app.points.models import Semestre
from app.points.service import aujourd_hui
from app.referentiel.models import Etablissement, StatutEtablissement
from tests.conftest import MOT_DE_PASSE, Navigateur

MOI = "/api/eleves/moi"
MOT_DE_PASSE_URL = "/api/comptes/mot-de-passe"

pytestmark = pytest.mark.usefixtures("annuaire")


def id_etablissement(en_base: Callable[..., Any], nom: str) -> str:
    return str(en_base(lambda db: db.scalar(select(Etablissement.id).where(Etablissement.nom == nom))))


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


def inscrire(client: TestClient, en_base: Callable[..., Any], identifiant: str = "aya", pseudo: str = "Aya K") -> Any:
    reponse = client.post(
        "/api/eleves/inscription",
        json={
            "prenom": "Aya", "nom": "Mensah", "pseudonyme": pseudo, "identifiant": identifiant,
            "mot_de_passe": MOT_DE_PASSE, "classe": "3e", "charte": True, "consentement_parent": True,
            "etablissement_id": id_etablissement(en_base, "Lycée de Tokoin I"),
        },
    )  # fmt: skip
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


def test_lespace_montre_le_profil_et_les_points(client: TestClient, en_base: Callable[..., Any]) -> None:
    async def semestre(db: Any) -> None:
        db.add(Semestre(libelle="S1", debut=aujourd_hui() - timedelta(days=1), fin=aujourd_hui() + timedelta(days=9)))

    en_base(semestre)
    inscrire(client, en_base)

    espace = client.get(MOI).json()

    assert (espace["pseudonyme"], espace["classe"], espace["email"]) == ("Aya K", "3e", None)
    assert espace["etablissement"]["nom"] == "Lycée de Tokoin I"
    assert espace["etablissement"]["dre_code"] == "grand-lome"
    assert espace["points"]["semestre"]["libelle"] == "S1"
    assert (espace["points"]["points_semestre"], espace["points"]["total"]) == (100, 100)
    assert [(ligne["libelle"], ligne["montant"]) for ligne in espace["points"]["lignes"]] == [("Compte créé", 100)]
    # Rien qui permette d'identifier l'élève au-delà de ce qu'il a saisi lui-même.
    assert "nom" not in espace and "prenom" not in espace


def test_sans_semestre_les_points_comptent_dans_le_total(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)

    points = client.get(MOI).json()["points"]

    assert (points["semestre"], points["points_semestre"], points["total"]) == (None, 0, 100)


def test_lespace_exige_une_session_et_un_compte_eleve(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    assert client.get(MOI).status_code == 401
    creer_utilisateur("prof", Role.encadreur, email="prof@ecole.tg")
    client.post("/api/comptes/connexion", json={"identifiant": "prof", "mot_de_passe": MOT_DE_PASSE})

    assert client.get(MOI).status_code == 403


def test_un_eleve_sans_profil_est_refuse(client: TestClient, creer_utilisateur: Callable[..., Utilisateur]) -> None:
    creer_utilisateur("ancien")
    client.post("/api/comptes/connexion", json={"identifiant": "ancien", "mot_de_passe": MOT_DE_PASSE})

    assert client.get(MOI).status_code == 403


def test_chaque_eleve_ne_voit_que_ses_donnees(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base, "aya", "Aya K")
    autre = Navigateur(client)
    client_autre = autre
    reponse = client_autre.post(
        "/api/eleves/inscription",
        json={
            "prenom": "Kofi", "nom": "Agbo", "pseudonyme": "Kofi A", "identifiant": "kofi",
            "mot_de_passe": MOT_DE_PASSE, "classe": "tle", "charte": True, "consentement_parent": True,
            "etablissement_id": id_etablissement(en_base, "Lycée de Tokoin I"),
        },
    )  # fmt: skip
    assert reponse.status_code == 201

    assert client.get(MOI).json()["pseudonyme"] == "Aya K"
    assert autre.get(MOI).json()["pseudonyme"] == "Kofi A"


def test_modifier_sa_classe_son_etablissement_et_son_email(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)
    espace = client.get(MOI).json()
    autre = id_etablissement(en_base, "Lycée Tokoin Est")

    reponse = client.patch(
        MOI,
        json={"version": espace["version"], "classe": "2nde", "etablissement_id": autre, "email": "Aya@Exemple.tg"},
    )

    assert reponse.status_code == 200, reponse.text
    nouvel = reponse.json()
    assert (nouvel["classe"], nouvel["etablissement"]["id"], nouvel["email"]) == ("2nde", autre, "aya@exemple.tg")
    assert nouvel["points"]["total"] == 100
    (entree,) = journal(en_base, "profil_eleve_modifie")
    assert entree.details["avant"]["classe"] == "3e"
    assert "aya@exemple.tg" not in str(entree.details)

    efface = client.patch(MOI, json={"version": nouvel["version"], "email": ""})
    assert efface.status_code == 200, efface.text
    assert efface.json()["email"] is None


def test_le_pseudonyme_ne_se_change_pas_soi_meme(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)
    espace = client.get(MOI).json()

    assert client.patch(MOI, json={"version": espace["version"], "pseudonyme": "Autre"}).status_code == 422


def test_un_etablissement_inactif_ou_propose_est_refuse(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)
    espace = client.get(MOI).json()
    autre = id_etablissement(en_base, "Lycée Tokoin Est")

    async def proposer(db: Any) -> None:
        etablissement = await db.get(Etablissement, UUID(autre))
        etablissement.statut = StatutEtablissement.propose

    en_base(proposer)

    reponse = client.patch(MOI, json={"version": espace["version"], "etablissement_id": autre})

    assert reponse.status_code == 422


def test_une_version_perimee_est_refusee(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)
    version = client.get(MOI).json()["version"]
    client.patch(MOI, json={"version": version, "classe": "2nde"})

    reponse = client.patch(MOI, json={"version": version, "classe": "1re"})

    assert reponse.status_code == 409


def test_un_email_deja_pris_est_refuse(
    client: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("prof", Role.encadreur, email="prof@ecole.tg")
    inscrire(client, en_base)
    version = client.get(MOI).json()["version"]

    assert client.patch(MOI, json={"version": version, "email": "prof@ecole.tg"}).status_code == 409


# Mot de passe ------------------------------------------------------------------------------------------------


def test_changer_son_mot_de_passe_coupe_les_autres_sessions(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)
    ailleurs = Navigateur(client)
    connexion = ailleurs.post("/api/comptes/connexion", json={"identifiant": "aya", "mot_de_passe": MOT_DE_PASSE})
    assert connexion.status_code == 200

    reponse = client.post(MOT_DE_PASSE_URL, json={"actuel": MOT_DE_PASSE, "nouveau": "nouveau-secret"})

    assert reponse.status_code == 204
    assert client.get(MOI).status_code == 200
    assert ailleurs.get(MOI).status_code == 401
    client.cookies.clear()
    connexion = client.post("/api/comptes/connexion", json={"identifiant": "aya", "mot_de_passe": "nouveau-secret"})
    assert connexion.status_code == 200
    assert len(journal(en_base, "mot_de_passe_change")) == 1


def test_un_mot_de_passe_actuel_faux_ou_un_nouveau_trop_court(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)

    faux = client.post(MOT_DE_PASSE_URL, json={"actuel": "pas-le-bon", "nouveau": "nouveau-secret"})
    court = client.post(MOT_DE_PASSE_URL, json={"actuel": MOT_DE_PASSE, "nouveau": "court"})

    assert (faux.status_code, court.status_code) == (400, 422)
    assert client.post(MOT_DE_PASSE_URL, json={"actuel": "x", "nouveau": "y"}).status_code == 422


def test_changer_son_mot_de_passe_exige_une_session(client: TestClient) -> None:
    assert client.post(MOT_DE_PASSE_URL, json={"actuel": "a", "nouveau": "bbbbbbbb"}).status_code == 401


def test_les_essais_de_mot_de_passe_sont_limites(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)

    statuts = [
        client.post(MOT_DE_PASSE_URL, json={"actuel": "pas-le-bon", "nouveau": "nouveau-secret"}).status_code
        for _ in range(7)
    ]

    assert statuts[:5] == [400] * 5
    assert statuts[-1] == 429


def test_les_changements_demail_sont_limites(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire(client, en_base)
    statuts = []
    for numero in range(7):
        version = client.get(MOI).json()["version"]
        statuts.append(client.patch(MOI, json={"version": version, "email": f"essai{numero}@exemple.tg"}).status_code)

    assert statuts[:5] == [200] * 5
    assert statuts[-1] == 429
    # Changer de classe reste possible.
    version = client.get(MOI).json()["version"]
    assert client.patch(MOI, json={"version": version, "classe": "2nde"}).status_code == 200
