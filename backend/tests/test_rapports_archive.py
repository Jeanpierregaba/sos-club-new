# ruff: noqa: F811
"""Archive et exports des rapports (spec 038) : droits, périmètre DRE, CSV sans nom d'élève et journalisé, PDF d'un
rapport approuvé seulement."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from tests.conftest import Navigateur, connecter_admin
from tests.espace_club import connecter
from tests.test_rapports import RAPPORTS, brouillon, club, complet, soumettre  # noqa: F401
from tests.test_rapports_examen import decider, depose, equipe  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

ARCHIVE = "/api/admin/rapports"
LECTURE = {("tableau_de_bord", "consulter"), ("rapports", "consulter")}
EXPORT = LECTURE | {("rapports", "exporter")}


def archiviste(
    client: TestClient, creer_collaborateur: Callable[..., Any], droits: set[Any], **options: Any
) -> Navigateur:
    identifiant = options.pop("identifiant", "archives")
    creer_collaborateur(identifiant, droits=droits, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


@pytest.fixture
def rapports(client: TestClient, club: dict[str, Any], equipe: Navigateur) -> dict[str, dict]:
    approuve = depose(client, "prof")
    decider(equipe, approuve["id"], "approuver")
    soumis = depose(client, "presidente", donnees=complet(type_activite="sensibilisation", titre="<b>Gras</b>"))
    prof = connecter(client, "prof")
    brouillon(prof, donnees=complet(titre="Brouillon privé"))
    ailleurs = depose(client, "ailleurs")
    return {"approuve": approuve, "soumis": soumis, "ailleurs": ailleurs}


def test_larchive_liste_les_rapports_soumis_sans_les_brouillons(
    client: TestClient, creer_collaborateur: Callable[..., Any], rapports: dict[str, dict]
) -> None:
    national = archiviste(client, creer_collaborateur, LECTURE, double_auth=True)

    corps = national.get(ARCHIVE).json()

    assert corps["total"] == 3
    assert "Brouillon privé" not in {r["titre"] for r in corps["rapports"]}
    approuve = next(r for r in corps["rapports"] if r["id"] == rapports["approuve"]["id"])
    assert (approuve["etat"], approuve["points_auteur"], approuve["points_club"]) == ("approuve", 100, 50)
    soumis = next(r for r in corps["rapports"] if r["id"] == rapports["soumis"]["id"])
    assert soumis["auteur"] == "Président du club"
    assert national.get(ARCHIVE, params={"etat": "approuve"}).json()["total"] == 1
    assert national.get(ARCHIVE, params={"recherche": "tokoin"}).json()["total"] == 2


def test_un_collaborateur_de_dre_ne_voit_que_sa_region(
    client: TestClient, creer_collaborateur: Callable[..., Any], rapports: dict[str, dict]
) -> None:
    maritime = archiviste(
        client, creer_collaborateur, LECTURE, identifiant="maritime", perimetre_dre="maritime", double_auth=True
    )

    corps = maritime.get(ARCHIVE).json()

    assert [r["id"] for r in corps["rapports"]] == [rapports["ailleurs"]["id"]]
    assert maritime.get(f"{ARCHIVE}/{rapports['approuve']['id']}/export.pdf").status_code == 404


def test_larchive_exige_le_droit_et_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any], rapports: dict[str, dict]
) -> None:
    sans_2fa = archiviste(client, creer_collaborateur, EXPORT, identifiant="sans2fa")
    lecteur = archiviste(client, creer_collaborateur, LECTURE, identifiant="lecteur", double_auth=True)

    assert sans_2fa.get(ARCHIVE).status_code == 403
    assert lecteur.get(f"{ARCHIVE}/export.csv").status_code == 403
    assert connecter(client, "prof").get(ARCHIVE).status_code in (401, 403)


def test_lexport_csv_ne_contient_aucun_nom_deleve_et_est_journalise(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    rapports: dict[str, dict],
    en_base: Callable[..., Any],
) -> None:
    national = archiviste(client, creer_collaborateur, EXPORT, double_auth=True)

    reponse = national.get(f"{ARCHIVE}/export.csv")

    assert reponse.status_code == 200
    texte = reponse.content.decode("utf-8-sig")
    assert texte.splitlines()[0].startswith("Référence;Modèle;État")
    assert len(texte.strip().splitlines()) == 4
    for interdit in ("presidente", "Ama", "Brouillon privé"):
        assert interdit not in texte
    assert "Président du club" in texte
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "rapports_exportes"))
    ).all()
    assert entree.details["lignes"] == 3


def test_le_pdf_dun_rapport_approuve_seulement(
    client: TestClient, creer_collaborateur: Callable[..., Any], rapports: dict[str, dict]
) -> None:
    prof = connecter(client, "prof")
    collegue = connecter(client, "collegue")

    reponse = prof.get(f"{RAPPORTS}/{rapports['approuve']['id']}/export.pdf")

    assert reponse.status_code == 200
    assert reponse.content.startswith(b"%PDF")
    assert reponse.headers["content-disposition"].startswith("attachment")
    assert collegue.get(f"{RAPPORTS}/{rapports['approuve']['id']}/export.pdf").status_code == 200
    assert collegue.get(f"{RAPPORTS}/{rapports['soumis']['id']}/export.pdf").status_code == 409
    assert connecter(client, "ailleurs").get(f"{RAPPORTS}/{rapports['approuve']['id']}/export.pdf").status_code == 404

    national = archiviste(client, creer_collaborateur, LECTURE, double_auth=True)
    assert national.get(f"{ARCHIVE}/{rapports['approuve']['id']}/export.pdf").content.startswith(b"%PDF")
    assert national.get(f"{ARCHIVE}/{rapports['soumis']['id']}/export.pdf").status_code == 409


def test_un_titre_avec_des_balises_reste_du_texte_dans_le_pdf(
    client: TestClient, club: dict[str, Any], equipe: Navigateur
) -> None:
    rapport = depose(client, "prof", donnees=complet(titre="<b>Gras</b> & <font>"))
    decider(equipe, rapport["id"], "approuver")

    reponse = connecter(client, "prof").get(f"{RAPPORTS}/{rapport['id']}/export.pdf")

    assert reponse.status_code == 200 and reponse.content.startswith(b"%PDF")
