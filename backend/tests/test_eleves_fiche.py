"""Fiche d'adhésion de l'élève (spec 030) : saisie à l'inscription, lecture et correction par l'élève."""

import inspect
from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin import exports
from app.admin.models import JournalAudit
from app.comptes.models import Utilisateur
from app.config import settings
from app.eleves import fiche as service_fiche
from app.eleves.models import FicheEleve, FicheEleveAxe, FicheEleveParcours
from app.referentiel.models import Axe
from tests.conftest import connecter_admin
from tests.fiche import fiche
from tests.quiz import connecter
from tests.test_eleves_inscription import INSCRIPTION, formulaire

FICHE = "/api/eleves/moi/fiche"

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


def fiche_en_base(en_base: Callable[..., Any]) -> FicheEleve | None:
    return en_base(lambda db: db.scalar(select(FicheEleve)))


# Inscription -------------------------------------------------------------------------------------------------


def test_linscription_enregistre_la_fiche_complete(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base))

    assert reponse.status_code == 201
    enregistree = fiche_en_base(en_base)
    assert enregistree is not None
    assert enregistree.annee_scolaire == service_fiche.annee_scolaire(date.today())
    assert enregistree.responsable_telephone == "90112233"
    assert enregistree.pere_telephone == "+22890112233"
    assert enregistree.reseaux == ["facebook", "autre"]
    assert enregistree.complete_le is not None and enregistree.engagement_le is not None
    axes = en_base(lambda db: db.scalars(select(FicheEleveAxe.axe_code)))
    assert sorted(axes) == ["genie-imhotep", "sante-environnement"]
    parcours = en_base(lambda db: db.scalars(select(FicheEleveParcours)))
    assert [(p.rang, p.etablissement) for p in parcours] == [(1, "CEG Bè")]


def test_lannee_scolaire_bascule_en_septembre() -> None:
    assert service_fiche.annee_scolaire(date(2026, 8, 31)) == "2025-2026"
    assert service_fiche.annee_scolaire(date(2026, 9, 1)) == "2026-2027"


def test_sans_fiche_linscription_est_refusee_et_rien_nest_ecrit(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    corps = formulaire(en_base)
    del corps["fiche"]

    assert client.post(INSCRIPTION, json=corps).status_code == 422
    assert en_base(lambda db: db.scalar(select(Utilisateur.id))) is None


@pytest.mark.parametrize(
    "champs",
    [
        {"sexe": None},
        {"date_naissance": None},
        {"lieu_naissance": "   "},
        {"responsable": None},
        {"responsable": {"nom": "Koffi Mensah", "telephone": ""}},
        {"responsable": {"nom": " ", "telephone": "90112233"}},
        {"axes": []},
        {"engagement": False},
        {"reseaux": ["facebook", "autre"], "reseau_autre": None},
        {"reseaux": ["snapchat"]},
        {"telephone": "12"},
        {"pere": {"nom": "Koffi", "profession": None, "telephone": "abc"}},
        {"parcours": [{"annee": "2025", "etablissement": "CEG Bè", "iesg": None}]},
    ],
)
def test_une_fiche_incomplete_ou_invalide_est_refusee(
    client: TestClient, en_base: Callable[..., Any], champs: dict[str, Any]
) -> None:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base, fiche=fiche(**champs)))

    assert reponse.status_code == 422
    assert fiche_en_base(en_base) is None


@pytest.mark.parametrize("age", [7, 31])
def test_une_date_de_naissance_hors_des_bornes_est_refusee(
    client: TestClient, en_base: Callable[..., Any], age: int
) -> None:
    naissance = date.today().replace(year=date.today().year - age, day=1)

    reponse = client.post(INSCRIPTION, json=formulaire(en_base, fiche=fiche(date_naissance=naissance.isoformat())))

    assert reponse.status_code == 422


def test_une_date_de_naissance_future_est_refusee(client: TestClient, en_base: Callable[..., Any]) -> None:
    demain = date.today().replace(year=date.today().year + 1).isoformat()

    assert client.post(INSCRIPTION, json=formulaire(en_base, fiche=fiche(date_naissance=demain))).status_code == 422


@pytest.mark.parametrize(
    "axes",
    [
        ["genie-imhotep", "sante-sexuelle-evss", "sport-secourisme", "bourses-excellence"],
        ["axe-inconnu"],
        ["genie-imhotep", "genie-imhotep"],
    ],
)
def test_les_axes_sont_verifies(client: TestClient, en_base: Callable[..., Any], axes: list[str]) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, fiche=fiche(axes=axes))).status_code == 422


def test_un_axe_desactive_est_refuse(client: TestClient, en_base: Callable[..., Any]) -> None:
    def activer(actif: bool) -> Callable[[Any], Any]:
        return lambda db: db.execute(update(Axe).where(Axe.code == "sport-secourisme").values(actif=actif))

    en_base(activer(False))
    try:
        reponse = client.post(INSCRIPTION, json=formulaire(en_base, fiche=fiche(axes=["sport-secourisme"])))
    finally:
        en_base(activer(True))

    assert reponse.status_code == 422
    assert "axe" in reponse.json()["detail"].lower()


def test_les_noms_ewe_et_kabiye_sont_acceptes(client: TestClient, en_base: Callable[..., Any]) -> None:
    corps = formulaire(
        en_base,
        fiche=fiche(lieu_naissance="Kpalimé  Agɔmɛ", responsable={"nom": "Ɖoʋi Ŋutsu", "telephone": "90112233"}),
    )
    assert client.post(INSCRIPTION, json=corps).status_code == 201

    enregistree = fiche_en_base(en_base)
    assert enregistree is not None
    assert (enregistree.lieu_naissance, enregistree.responsable_nom) == ("Kpalimé Agɔmɛ", "Ɖoʋi Ŋutsu")


# Lecture et correction par l'élève ---------------------------------------------------------------------------


def test_leleve_lit_sa_fiche(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base))

    corps = client.get(FICHE).json()

    assert corps["responsable"] == {"nom": "Koffi Mensah", "telephone": "90112233"}
    assert corps["axes"] == ["genie-imhotep", "sante-environnement"]
    assert corps["annee_scolaire"] == service_fiche.annee_scolaire(date.today())
    assert client.get("/api/eleves/moi").json()["fiche_complete"] is True


def test_leleve_corrige_sa_fiche(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base))
    version = client.get(FICHE).json()["version"]

    reponse = client.put(
        FICHE,
        json=fiche(axes=["leadership-mentorat"], parcours=[], reseaux=[], reseau_autre=None) | {"version": version},
    )

    assert reponse.status_code == 200
    assert reponse.json()["axes"] == ["leadership-mentorat"]
    assert reponse.json()["parcours"] == []
    assert reponse.json()["version"] == version + 1
    assert client.put(FICHE, json=fiche() | {"version": version}).status_code == 409


def test_un_ancien_eleve_sans_fiche_la_complete(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_eleve("ama")
    connecter(client, "ama")
    assert client.get("/api/eleves/moi").json()["fiche_complete"] is False
    assert client.get(FICHE).json() is None

    reponse = client.put(FICHE, json=fiche() | {"version": None})

    assert reponse.status_code == 200
    assert client.get("/api/eleves/moi").json()["fiche_complete"] is True
    assert fiche_en_base(en_base) is not None


def test_la_fiche_est_reservee_aux_eleves(client: TestClient, creer_encadreur: Callable[..., Utilisateur]) -> None:
    assert client.get(FICHE).status_code == 401
    creer_encadreur("kofi")
    connecter(client, "kofi")

    assert client.get(FICHE).status_code == 403
    assert client.put(FICHE, json=fiche() | {"version": None}).status_code == 403


# Lecture par l'équipe -----------------------------------------------------------------------------------------


def inscrire_aya(client: TestClient, en_base: Callable[..., Any]) -> str:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base))
    client.cookies.clear()
    return reponse.json()["id"]


def fiche_admin(identifiant: str) -> str:
    return f"/api/admin/inscrits/{identifiant}/fiche"


def consultations(en_base: Callable[..., Any]) -> list[JournalAudit]:
    return en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "fiche_eleve_consultee"))
    ).all()


def test_un_collaborateur_habilite_lit_la_fiche_et_cest_journalise(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    eleve_id = inscrire_aya(client, en_base)
    creer_collaborateur("chef", droits={("fiches_eleves", "consulter")}, double_auth=True)
    connecter_admin(client, "chef")

    reponse = client.get(fiche_admin(eleve_id))

    assert reponse.status_code == 200
    assert reponse.json()["responsable"]["nom"] == "Koffi Mensah"
    journal = consultations(en_base)
    assert [(j.cible_id, j.perimetre) for j in journal] == [(eleve_id, "grand-lome")]
    # Le journal ne garde jamais le contenu de la fiche.
    assert "Koffi" not in str(journal[0].details)


def test_un_collaborateur_de_la_dre_lit_les_fiches_de_sa_dre_seulement(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    eleve_id = inscrire_aya(client, en_base)
    creer_collaborateur("lome", droits={("fiches_eleves", "consulter")}, perimetre_dre="grand-lome", double_auth=True)
    creer_collaborateur("kara", droits={("fiches_eleves", "consulter")}, perimetre_dre="kara", double_auth=True)

    connecter_admin(client, "lome")
    assert client.get(fiche_admin(eleve_id)).status_code == 200
    client.cookies.clear()
    connecter_admin(client, "kara")
    assert client.get(fiche_admin(eleve_id)).status_code == 404
    assert len(consultations(en_base)) == 1


def test_sans_le_droit_ou_sans_double_authentification_la_fiche_est_refusee(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    eleve_id = inscrire_aya(client, en_base)
    creer_collaborateur("lecteur", droits={("inscrits", "consulter")}, double_auth=True)
    connecter_admin(client, "lecteur")
    assert client.get(fiche_admin(eleve_id)).status_code == 403
    client.cookies.clear()

    creer_collaborateur("sans2fa", droits={("fiches_eleves", "consulter")})
    connecter_admin(client, "sans2fa")
    assert client.get(fiche_admin(eleve_id)).status_code == 403
    assert consultations(en_base) == []


def test_ni_un_eleve_ni_un_encadreur_ne_lit_la_fiche_dun_autre(
    client: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
) -> None:
    eleve_id = inscrire_aya(client, en_base)
    creer_eleve("kossi", affiche="Kossi du Plateau")
    connecter(client, "kossi")
    assert client.get(fiche_admin(eleve_id)).status_code in (401, 403)
    assert client.get(FICHE).json() is None
    client.cookies.clear()

    creer_encadreur("kofi")
    connecter(client, "kofi")
    assert client.get(fiche_admin(eleve_id)).status_code in (401, 403)


def test_aucun_champ_de_la_fiche_nest_exportable_ni_public(client: TestClient, en_base: Callable[..., Any]) -> None:
    # Les exports lisent le seul compte (`utilisateur`) : son « telephone » n'est pas celui de la fiche.
    champs = set(FicheEleve.__table__.columns.keys()) - {"utilisateur_id", "version", "cree_le", "modifie_le"}
    assert champs.isdisjoint(set(exports.COLONNES) - {"telephone"})
    assert "fiche_eleve" not in inspect.getsource(exports).lower().replace("ficheeleve", "fiche_eleve")

    inscrire_aya(client, en_base)
    # Les pages publiques qui citent des élèves ne montrent que le pseudonyme.
    for adresse in ("/api/articles", "/api/clubs"):
        reponse = client.get(adresse)
        assert reponse.status_code == 200
        assert "Koffi Mensah" not in reponse.text and "CS-042" not in reponse.text
