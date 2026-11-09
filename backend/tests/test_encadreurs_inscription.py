"""Inscription d'un encadreur (spec 018) : compte en attente, profil, établissement proposé, sans aucun point."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.models import JournalAudit
from app.comptes.champs import normaliser_telephone
from app.comptes.models import Role, Utilisateur
from app.config import settings
from app.encadreurs.models import Encadreur, EtatVerification, Fonction
from app.points.models import MouvementPoints
from app.referentiel.models import Etablissement, Iesg, StatutEtablissement
from tests.fiche import fiche

INSCRIPTION = "/api/encadreurs/inscription"

pytestmark = pytest.mark.usefixtures("annuaire")


def etablissement_id(en_base: Callable[..., Any], nom: str = "Lycée de Tokoin I") -> str:
    return str(en_base(lambda db: db.scalar(select(Etablissement.id).where(Etablissement.nom == nom))))


def formulaire(en_base: Callable[..., Any], **champs: Any) -> dict[str, Any]:
    valeurs: dict[str, Any] = {
        "prenom": "Kossi",
        "nom": "Agbeko",
        "email": "kossi.agbeko@ecole.tg",
        "telephone": "+228 90 12 34 56",
        "identifiant": "kossi.agbeko",
        "mot_de_passe": "un-mot-de-passe",
        "fonction": "enseignant",
        "charte": True,
        "consentement": True,
        "etablissement_id": etablissement_id(en_base),
    }
    return valeurs | champs


def compter(en_base: Callable[..., Any], modele: Any) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(modele)))


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


# Parcours ----------------------------------------------------------------------------------------------------


def test_une_inscription_cree_un_compte_en_attente_sans_points(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base, email="Kossi.Agbeko@Ecole.tg"))

    assert reponse.status_code == 201, reponse.text
    corps = reponse.json()
    assert (corps["identifiant"], corps["role"]) == ("kossi.agbeko", "encadreur")
    assert client.get("/api/comptes/moi").status_code == 200

    utilisateur = en_base(lambda db: db.get(Utilisateur, UUID(corps["id"])))
    encadreur = en_base(lambda db: db.get(Encadreur, utilisateur.id))
    assert (utilisateur.email, utilisateur.telephone) == ("kossi.agbeko@ecole.tg", "+22890123456")
    assert utilisateur.consentement_le is not None
    assert (encadreur.etat, encadreur.fonction, encadreur.charte_version) == (
        EtatVerification.en_attente,
        Fonction.enseignant,
        settings.version_charte,
    )
    assert compter(en_base, MouvementPoints) == 0
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "inscription_encadreur"))
    ).all()
    assert entree.perimetre == "grand-lome"
    assert entree.details["etablissement_propose"] is False


def test_les_inscriptions_fermees_refusent_aussi_les_encadreurs(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", False)

    assert client.post(INSCRIPTION, json=formulaire(en_base)).status_code == 403
    assert compter(en_base, Utilisateur) == 0


def test_un_utilisateur_connecte_ne_cree_pas_un_second_compte(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base))

    reponse = client.post(INSCRIPTION, json=formulaire(en_base, identifiant="autre", email="autre@ecole.tg"))

    assert reponse.status_code == 409
    assert compter(en_base, Utilisateur) == 1


@pytest.mark.parametrize("case", ["charte", "consentement"])
def test_les_cases_sont_verifiees_par_lapi(client: TestClient, en_base: Callable[..., Any], case: str) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, **{case: False})).status_code == 422
    corps = formulaire(en_base)
    del corps[case]
    assert client.post(INSCRIPTION, json=corps).status_code == 422


@pytest.mark.parametrize("email", [None, "", "pas-un-email"])
def test_lemail_est_obligatoire_et_valide(client: TestClient, en_base: Callable[..., Any], email: str | None) -> None:
    corps = formulaire(en_base, email=email)

    assert client.post(INSCRIPTION, json=corps).status_code == 422
    assert compter(en_base, Utilisateur) == 0


@pytest.mark.parametrize(
    ("champs", "message"),
    [
        ({"identifiant": "pris"}, "Cet identifiant est déjà pris."),
        ({"email": "pris@ecole.tg"}, "Cet email est déjà pris."),
    ],
)
def test_un_champ_deja_pris_est_nomme(
    client: TestClient,
    en_base: Callable[..., Any],
    creer_utilisateur: Callable[..., Utilisateur],
    champs: dict[str, str],
    message: str,
) -> None:
    creer_utilisateur("pris", Role.encadreur, email="pris@ecole.tg")

    reponse = client.post(INSCRIPTION, json=formulaire(en_base, **champs))

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == message
    assert compter(en_base, Encadreur) == 0


def test_le_role_et_letat_ne_se_choisissent_pas(client: TestClient, en_base: Callable[..., Any]) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, role="admin")).status_code == 422
    assert client.post(INSCRIPTION, json=formulaire(en_base, etat="actif")).status_code == 422
    assert compter(en_base, Utilisateur) == 0


# Fonction --------------------------------------------------------------------------------------------------------


def test_la_fonction_autre_exige_une_precision(client: TestClient, en_base: Callable[..., Any]) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, fonction="autre")).status_code == 422
    assert (
        client.post(INSCRIPTION, json=formulaire(en_base, fonction="autre", fonction_precision="  ")).status_code == 422
    )

    reponse = client.post(
        INSCRIPTION, json=formulaire(en_base, fonction="autre", fonction_precision=" Bibliothécaire ")
    )

    assert reponse.status_code == 201, reponse.text
    encadreur = en_base(lambda db: db.scalar(select(Encadreur)))
    assert (encadreur.fonction, encadreur.fonction_precision) == (Fonction.autre, "Bibliothécaire")


def test_une_precision_sans_fonction_autre_est_ignoree(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base, fonction="sante", fonction_precision="Infirmier"))

    encadreur = en_base(lambda db: db.scalar(select(Encadreur)))
    assert (encadreur.fonction, encadreur.fonction_precision) == (Fonction.sante, None)


def test_une_fonction_inconnue_est_refusee(client: TestClient, en_base: Callable[..., Any]) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, fonction="directeur")).status_code == 422


# Téléphone -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("saisi", "enregistre"),
    [
        ("+228 90 12 34 56", "+22890123456"),
        ("90-12-34-56", "90123456"),
        ("(228) 90.12.34.56", "22890123456"),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_le_telephone_est_normalise(saisi: str | None, enregistre: str | None) -> None:
    assert normaliser_telephone(saisi) == enregistre


@pytest.mark.parametrize("telephone", ["1234567", "+228 90 12 34 56 78 90 12", "90 12 AB 56", "++22890123456"])
def test_un_telephone_invalide_est_refuse(client: TestClient, en_base: Callable[..., Any], telephone: str) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, telephone=telephone)).status_code == 422


@pytest.mark.parametrize("telephone", [None, "", "  "])
def test_le_telephone_est_obligatoire(client: TestClient, en_base: Callable[..., Any], telephone: str | None) -> None:
    corps = formulaire(en_base)
    del corps["telephone"]
    assert client.post(INSCRIPTION, json=corps).status_code == 422

    assert client.post(INSCRIPTION, json=formulaire(en_base, telephone=telephone)).status_code == 422
    assert compter(en_base, Encadreur) == 0


def test_la_discipline_est_enregistree(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = client.post(
        INSCRIPTION, json=formulaire(en_base, discipline="  SVT (Sciences de la Vie  et de la Terre) ")
    )

    assert reponse.status_code == 201
    encadreur = en_base(lambda db: db.scalar(select(Encadreur)))
    assert encadreur.discipline == "SVT (Sciences de la Vie et de la Terre)"
    assert client.get("/api/encadreurs/moi").json()["discipline"] == "SVT (Sciences de la Vie et de la Terre)"


def test_lespace_montre_la_region_et_la_ville_de_letablissement(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base))

    etablissement = client.get("/api/encadreurs/moi").json()["etablissement"]

    lieu = en_base(lambda db: db.scalar(select(Etablissement.localite).where(Etablissement.nom == "Lycée de Tokoin I")))
    assert (etablissement["dre"], etablissement["localite"]) == ("Grand Lomé", lieu)


# Établissement ---------------------------------------------------------------------------------------------------


def test_un_encadreur_peut_proposer_son_etablissement(client: TestClient, en_base: Callable[..., Any]) -> None:
    iesg = str(en_base(lambda db: db.scalar(select(Iesg.id).where(Iesg.nom == "IESG Golfe"))))
    corps = formulaire(en_base, proposition={"iesg_id": iesg, "nom": "CEG Nouveau Quartier"})
    del corps["etablissement_id"]

    assert client.post(INSCRIPTION, json=corps).status_code == 201

    etablissement = en_base(
        lambda db: db.scalar(select(Etablissement).where(Etablissement.nom == "CEG Nouveau Quartier"))
    )
    assert etablissement.statut is StatutEtablissement.propose
    encadreur = en_base(lambda db: db.scalar(select(Encadreur)))
    assert encadreur.etablissement_id == etablissement.id


def test_un_etablissement_inactif_est_refuse(client: TestClient, en_base: Callable[..., Any]) -> None:
    identifiant = etablissement_id(en_base)
    en_base(
        lambda db: db.execute(
            Etablissement.__table__.update()
            .where(Etablissement.id == UUID(identifiant))
            .values(statut=StatutEtablissement.inactif)
        )
    )

    assert client.post(INSCRIPTION, json=formulaire(en_base)).status_code == 422


# Limite ----------------------------------------------------------------------------------------------------------


def test_la_limite_par_adresse_est_partagee_avec_les_eleves(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "inscriptions_max_adresse", 1)
    eleve = {
        "prenom": "Aya", "nom": "Mensah", "pseudonyme": "Aya la Curieuse", "identifiant": "aya.mensah",
        "mot_de_passe": "un-mot-de-passe", "classe": "2nde", "charte": True, "consentement_parent": True,
        "etablissement_id": etablissement_id(en_base), "fiche": fiche(),
    }  # fmt: skip
    assert client.post("/api/eleves/inscription", json=eleve).status_code == 201
    client.cookies.clear()

    assert client.post(INSCRIPTION, json=formulaire(en_base)).status_code == 429
    assert compter(en_base, Encadreur) == 0
