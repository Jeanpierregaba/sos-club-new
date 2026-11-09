"""La gestion de la bibliothèque (spec 028) : préparée par un collaborateur, publiée par un autre qui nomme le
validateur ; aucun accès pour les élèves, encadreurs, présidents et visiteurs."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.models import JournalAudit
from app.bibliotheque import gestion
from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.bibliotheque.schemas import Approbation
from app.comptes.models import Utilisateur
from app.config import settings
from app.fichiers.stockage import Disque, StockageIndisponible
from app.notifications.models import Notification
from tests.bibliotheque import (
    APPROBATION,
    GESTION,
    PREPARATION,
    PUBLICATION,
    creer_ressource,
    envoi_image,
    envoi_pdf,
    image,
    pdf,
)
from tests.conftest import MOT_DE_PASSE, Navigateur, code_totp, connecter_admin, moteur_test
from tests.quiz import connecter

INFOS = {"titre": "Guide du lavage des mains", "description": "Les bons gestes.", "categorie": "guide"}


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_collaborateur("pedago", droits=PREPARATION)
    connecter_admin(client, "pedago")
    return utilisateur


@pytest.fixture
def publieur(client: TestClient, creer_collaborateur: Callable[..., Utilisateur]) -> Navigateur:
    creer_collaborateur("publieur", droits=PUBLICATION, double_auth=True)
    navigateur = Navigateur(client)
    corps = navigateur.post(
        "/api/comptes/connexion", json={"identifiant": "publieur", "mot_de_passe": MOT_DE_PASSE}
    ).json()
    navigateur.post("/api/comptes/connexion/code", json={"jeton": corps["jeton"], "code": code_totp()})
    return navigateur


def fichiers(dossier: Path) -> set[str]:
    racine = dossier / "ressources"
    return {p.name for p in racine.iterdir() if not p.name.startswith(".")} if racine.exists() else set()


def journal(en_base: Callable[..., Any]) -> list[str]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(JournalAudit.action).where(JournalAudit.action.like("bibliotheque_%")).order_by(JournalAudit.id)
            )
        ).all()
    )


def brouillon(client: Any, infos: dict[str, Any] | None = None) -> dict[str, Any]:
    reponse = client.post(GESTION, json=infos or INFOS)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def pret(client: Any, infos: dict[str, Any] | None = None, *, couverture: bool = False) -> dict[str, Any]:
    corps = brouillon(client, infos)
    corps = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf()).json()
    if couverture:
        corps = client.put(f"{GESTION}/{corps['id']}/couverture", **envoi_image()).json()
    return corps


def soumise(client: Any, infos: dict[str, Any] | None = None, *, couverture: bool = False) -> dict[str, Any]:
    corps = pret(client, infos, couverture=couverture)
    reponse = client.post(f"{GESTION}/{corps['id']}/soumettre")
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


# Préparer ---------------------------------------------------------------------------------------------------------


def test_le_gestionnaire_cree_depose_et_soumet_une_ressource(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], dossier_fichiers: Path
) -> None:
    corps = brouillon(client)
    assert corps["etat"] == "brouillon"
    assert corps["contributeur"] is True
    assert corps["fichier_octets"] is None

    corps = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf(pdf(3))).json()

    assert corps["pages"] == 3
    assert corps["fichier_octets"] == len(pdf(3))
    assert len(fichiers(dossier_fichiers)) == 1

    reponse = client.post(f"{GESTION}/{corps['id']}/soumettre")

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "soumis"
    assert journal(en_base) == ["bibliotheque_creee", "bibliotheque_fichier_depose", "bibliotheque_soumise"]


@pytest.mark.parametrize(
    "infos",
    [
        {**INFOS, "titre": ""},
        {**INFOS, "titre": "x" * 151},
        {**INFOS, "description": "x" * 501},
        {**INFOS, "categorie": "video"},
        {**INFOS, "axe_code": "inconnu"},
        {**INFOS, "parution": "x" * 61},
    ],
)
def test_des_informations_invalides_sont_refusees(
    client: TestClient, gestionnaire: Utilisateur, infos: dict[str, Any]
) -> None:
    assert client.post(GESTION, json=infos).status_code == 422


def test_la_parution_ne_vaut_que_pour_un_magazine(client: TestClient, gestionnaire: Utilisateur) -> None:
    guide = brouillon(client, {**INFOS, "parution": "N° 12"})
    magazine = brouillon(client, {**INFOS, "categorie": "magazine", "parution": "N° 12 — octobre 2026"})

    assert guide["parution"] is None
    assert magazine["parution"] == "N° 12 — octobre 2026"


@pytest.mark.parametrize(
    "octets",
    [b"Bonjour", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, pdf(javascript=True)],
    ids=["texte", "image-renommee", "javascript"],
)
def test_un_fichier_refuse_ne_laisse_rien(
    client: TestClient, gestionnaire: Utilisateur, dossier_fichiers: Path, octets: bytes
) -> None:
    corps = brouillon(client)

    reponse = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf(octets))

    assert reponse.status_code == 422
    assert fichiers(dossier_fichiers) == set()


def test_le_message_dit_pourquoi_un_pdf_est_refuse(client: TestClient, gestionnaire: Utilisateur) -> None:
    corps = brouillon(client)

    reponse = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf(pdf(javascript=True)))

    assert "JavaScript" in reponse.json()["detail"]


def test_un_pdf_trop_lourd_est_refuse(
    client: TestClient, gestionnaire: Utilisateur, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "ressource_octets_max", 500)
    corps = brouillon(client)

    reponse = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf(pdf(3)))

    assert reponse.status_code == 413
    assert "Mo" in reponse.json()["detail"]


def test_remplacer_le_pdf_efface_lancien(client: TestClient, gestionnaire: Utilisateur, dossier_fichiers: Path) -> None:
    corps = pret(client)
    avant = fichiers(dossier_fichiers)

    corps = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf(pdf(5))).json()

    apres = fichiers(dossier_fichiers)
    assert corps["pages"] == 5
    assert len(apres) == 1
    assert apres != avant


def test_la_couverture_se_depose_et_se_retire(
    client: TestClient, gestionnaire: Utilisateur, dossier_fichiers: Path
) -> None:
    corps = pret(client)

    corps = client.put(f"{GESTION}/{corps['id']}/couverture", **envoi_image()).json()

    assert corps["a_couverture"] is True
    assert len(fichiers(dossier_fichiers)) == 3
    lue = client.get(f"{GESTION}/{corps['id']}/couverture/vignette")
    assert lue.status_code == 200
    assert lue.headers["content-type"] == "image/webp"

    corps = client.delete(f"{GESTION}/{corps['id']}/couverture").json()

    assert corps["a_couverture"] is False
    assert len(fichiers(dossier_fichiers)) == 1


def test_une_couverture_illisible_est_refusee(client: TestClient, gestionnaire: Utilisateur) -> None:
    corps = pret(client)

    assert client.put(f"{GESTION}/{corps['id']}/couverture", **envoi_image(b"pas une image")).status_code == 422


def test_une_ressource_sans_fichier_ne_se_soumet_pas(client: TestClient, gestionnaire: Utilisateur) -> None:
    corps = brouillon(client)

    reponse = client.post(f"{GESTION}/{corps['id']}/soumettre")

    assert reponse.status_code == 422
    assert "PDF" in reponse.json()["detail"]


def test_un_magazine_sans_couverture_ne_se_soumet_pas(client: TestClient, gestionnaire: Utilisateur) -> None:
    corps = pret(client, {**INFOS, "categorie": "magazine"})

    reponse = client.post(f"{GESTION}/{corps['id']}/soumettre")

    assert reponse.status_code == 422
    assert "couverture" in reponse.json()["detail"]
    corps = client.put(f"{GESTION}/{corps['id']}/couverture", **envoi_image()).json()
    assert client.post(f"{GESTION}/{corps['id']}/soumettre").status_code == 200


def test_une_ressource_soumise_ne_se_modifie_plus(client: TestClient, gestionnaire: Utilisateur) -> None:
    corps = soumise(client, couverture=True)
    rid = corps["id"]

    assert client.put(f"{GESTION}/{rid}", json={**INFOS, "titre": "Autre"}).status_code == 409
    assert client.put(f"{GESTION}/{rid}/fichier", **envoi_pdf()).status_code == 409
    assert client.put(f"{GESTION}/{rid}/couverture", **envoi_image()).status_code == 409
    assert client.delete(f"{GESTION}/{rid}/couverture").status_code == 409


def test_le_gestionnaire_reprend_une_ressource_soumise(client: TestClient, gestionnaire: Utilisateur) -> None:
    corps = soumise(client)

    reponse = client.post(f"{GESTION}/{corps['id']}/reprendre")

    assert reponse.json()["etat"] == "brouillon"
    assert client.put(f"{GESTION}/{corps['id']}", json={**INFOS, "titre": "Autre"}).status_code == 200


def test_le_stockage_indisponible_repond_503_sans_rien_changer(
    client: TestClient, gestionnaire: Utilisateur, monkeypatch: pytest.MonkeyPatch, en_base: Callable[..., Any]
) -> None:
    corps = brouillon(client)

    async def panne(self: Disque, cle: str, octets: bytes) -> None:
        raise StockageIndisponible

    monkeypatch.setattr(Disque, "enregistrer", panne)

    reponse = client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf())

    assert reponse.status_code == 503
    ressource = en_base(lambda db: db.get(Ressource, corps["id"]))
    assert ressource.fichier_cle is None


# Publier ----------------------------------------------------------------------------------------------------------


def test_un_autre_collaborateur_publie_en_nommant_le_validateur(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    corps = soumise(client)

    reponse = publieur.post(f"{GESTION}/{corps['id']}/approuver", json=APPROBATION)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "publie"
    assert reponse.json()["validateur_nom"] == "Dr Afi Mensah"
    assert reponse.json()["deja_publiee"] is True
    [avis] = en_base(lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == gestionnaire.id)))
    assert avis.type == "bibliotheque_decision"
    assert avis.lien == f"/admin/bibliotheque/{corps['id']}"
    assert journal(en_base)[-1] == "bibliotheque_approuvee"


def test_qui_a_prepare_la_ressource_ne_la_publie_pas(
    client: TestClient, creer_collaborateur: Callable[..., Utilisateur]
) -> None:
    creer_collaborateur("tout", droits=PREPARATION | PUBLICATION, double_auth=True)
    connecter_admin(client, "tout")
    corps = soumise(client)

    reponse = client.post(f"{GESTION}/{corps['id']}/approuver", json=APPROBATION)

    assert reponse.status_code == 403
    assert client.get(f"{GESTION}/{corps['id']}").json()["etat"] == "soumis"


@pytest.mark.parametrize(
    "approbation",
    [
        {},
        {"validateur_nom": "Dr Afi Mensah"},
        {"validateur_qualite": "Médecin"},
        {**APPROBATION, "validateur_nom": " "},
    ],
)
def test_lapprobation_exige_le_validateur(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, approbation: dict[str, str]
) -> None:
    corps = soumise(client)

    assert publieur.post(f"{GESTION}/{corps['id']}/approuver", json=approbation).status_code == 422


def test_un_refus_renvoie_la_ressource_en_brouillon_avec_son_motif(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    corps = soumise(client)

    reponse = publieur.post(f"{GESTION}/{corps['id']}/refuser", json={"motif": "La source n'est pas citée."})

    assert reponse.json()["etat"] == "brouillon"
    assert reponse.json()["motif"] == "La source n'est pas citée."
    [avis] = en_base(lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == gestionnaire.id)))
    assert avis.message == "La source n'est pas citée."


def test_depublier_puis_reprendre_et_republier(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    corps = soumise(client)
    publieur.post(f"{GESTION}/{corps['id']}/approuver", json=APPROBATION)

    reponse = publieur.post(f"{GESTION}/{corps['id']}/depublier", json={"motif": "Chiffres à mettre à jour."})

    assert reponse.json()["etat"] == "depublie"
    assert client.post(f"{GESTION}/{corps['id']}/reprendre").json()["etat"] == "brouillon"
    assert client.put(f"{GESTION}/{corps['id']}/fichier", **envoi_pdf(pdf(4))).status_code == 200
    assert client.post(f"{GESTION}/{corps['id']}/soumettre").status_code == 200
    # Le gestionnaire a de nouveau contribué ; le publieur, qui n'a rien préparé, peut republier.
    assert publieur.post(f"{GESTION}/{corps['id']}/approuver", json=APPROBATION).json()["pages"] == 4


def test_deux_approbations_simultanees_une_seule_passe(
    client: TestClient,
    gestionnaire: Utilisateur,
    creer_collaborateur: Callable[..., Utilisateur],
) -> None:
    corps = soumise(client)
    premier = creer_collaborateur("pub1", droits=PUBLICATION, double_auth=True)
    second = creer_collaborateur("pub2", droits=PUBLICATION, double_auth=True)

    async def decider(qui: Utilisateur) -> str:
        from app.admin.models import Collaborateur

        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == qui.id))
            acces = Acces(utilisateur=qui, collaborateur=collaborateur)  # type: ignore[arg-type]
            try:
                await gestion.approuver(db, acces, corps["id"], Approbation(**APPROBATION), "test")
                await asyncio.sleep(0.2)
                await db.commit()
                return "ok"
            except gestion.EtatInvalide:
                return "conflit"

    async def scenario() -> list[str]:
        return await asyncio.gather(decider(premier), decider(second))

    assert sorted(asyncio.run(scenario())) == ["conflit", "ok"]


# Relire et supprimer ------------------------------------------------------------------------------------------------


def test_le_publieur_relit_le_pdf_soumis_sans_le_compter(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    corps = soumise(client)

    reponse = publieur.get(f"{GESTION}/{corps['id']}/fichier")

    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "application/pdf"
    assert reponse.content.startswith(b"%PDF-")
    assert en_base(lambda db: db.get(Ressource, corps["id"])).telechargements == 0


def test_supprimer_un_brouillon_jamais_publie_efface_ses_fichiers(
    client: TestClient, gestionnaire: Utilisateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    corps = pret(client, couverture=True)

    reponse = client.delete(f"{GESTION}/{corps['id']}")

    assert reponse.status_code == 204
    assert fichiers(dossier_fichiers) == set()
    assert en_base(lambda db: db.get(Ressource, corps["id"])) is None
    assert client.get(f"{GESTION}/{corps['id']}").status_code == 404
    assert journal(en_base)[-1] == "bibliotheque_supprimee"


def test_une_ressource_deja_publiee_ne_se_supprime_pas(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], dossier_fichiers: Path
) -> None:
    ressource = creer_ressource(en_base, etat=EtatRessource.depublie)
    client.post(f"{GESTION}/{ressource.id}/reprendre")

    reponse = client.delete(f"{GESTION}/{ressource.id}")

    assert reponse.status_code == 409
    assert len(fichiers(dossier_fichiers)) == 1


def test_la_liste_se_filtre_par_etat(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    creer_ressource(en_base, etat=EtatRessource.soumis, titre="En attente")
    creer_ressource(en_base, etat=EtatRessource.publie, titre="En ligne", categorie=CategorieRessource.fiche)

    tout = client.get(GESTION).json()["ressources"]
    file = client.get(GESTION, params={"etat": "soumis"}).json()["ressources"]

    assert {r["titre"] for r in tout} == {"En attente", "En ligne"}
    assert [r["titre"] for r in file] == ["En attente"]


# Droits -----------------------------------------------------------------------------------------------------------

ROUTES = [
    ("get", GESTION, None),
    ("post", GESTION, {"json": INFOS}),
    ("get", f"{GESTION}/{{id}}", None),
    ("put", f"{GESTION}/{{id}}", {"json": INFOS}),
    ("delete", f"{GESTION}/{{id}}", None),
    ("put", f"{GESTION}/{{id}}/fichier", envoi_pdf()),
    ("put", f"{GESTION}/{{id}}/couverture", envoi_image(image())),
    ("delete", f"{GESTION}/{{id}}/couverture", None),
    ("get", f"{GESTION}/{{id}}/fichier", None),
    ("get", f"{GESTION}/{{id}}/couverture/grande", None),
    ("post", f"{GESTION}/{{id}}/soumettre", None),
    ("post", f"{GESTION}/{{id}}/reprendre", None),
    ("post", f"{GESTION}/{{id}}/approuver", {"json": APPROBATION}),
    ("post", f"{GESTION}/{{id}}/refuser", {"json": {"motif": "Pour voir."}}),
    ("post", f"{GESTION}/{{id}}/depublier", {"json": {"motif": "Pour voir."}}),
]


@pytest.mark.parametrize("role", ["visiteur", "eleve", "president", "encadreur"])
@pytest.mark.parametrize(("methode", "chemin", "options"), ROUTES)
def test_les_comptes_hors_equipe_ny_ont_pas_acces(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    role: str,
    methode: str,
    chemin: str,
    options: dict[str, Any] | None,
) -> None:
    ressource = creer_ressource(en_base, etat=EtatRessource.soumis, couverture=True)
    if role == "encadreur":
        creer_encadreur("kodjo")
        connecter(client, "kodjo")
    elif role != "visiteur":
        eleve = creer_eleve("ama")
        if role == "president":
            creer_club(eleve)
        connecter(client, "ama")

    reponse = getattr(client, methode)(chemin.format(id=ressource.id), **(options or {}))

    assert reponse.status_code == (401 if role == "visiteur" else 403)
    apres = en_base(lambda db: db.get(Ressource, ressource.id))
    assert (apres.etat, apres.version) == (EtatRessource.soumis, ressource.version)


@pytest.mark.parametrize(
    ("droits", "methode", "chemin", "options"),
    [
        ({("bibliotheque", "consulter")}, "post", GESTION, {"json": INFOS}),
        ({("bibliotheque", "consulter")}, "put", f"{GESTION}/{{id}}/fichier", envoi_pdf()),
        ({("bibliotheque", "consulter"), ("bibliotheque", "creer")}, "post", f"{GESTION}/{{id}}/soumettre", None),
        (PREPARATION, "post", f"{GESTION}/{{id}}/approuver", {"json": APPROBATION}),
        (PREPARATION, "post", f"{GESTION}/{{id}}/depublier", {"json": {"motif": "Pour voir."}}),
        ({("quiz", "consulter")}, "get", GESTION, None),
    ],
)
def test_un_collaborateur_sans_le_droit_est_refuse(
    client: TestClient,
    creer_collaborateur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    droits: set[tuple[str, str]],
    methode: str,
    chemin: str,
    options: dict[str, Any] | None,
) -> None:
    ressource = creer_ressource(en_base, etat=EtatRessource.brouillon)
    creer_collaborateur("partiel", droits=droits)
    connecter_admin(client, "partiel")

    reponse = getattr(client, methode)(chemin.format(id=ressource.id), **(options or {}))

    assert reponse.status_code == 403


def test_publier_exige_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    ressource = creer_ressource(en_base, etat=EtatRessource.soumis)
    creer_collaborateur("sans2fa", droits=PUBLICATION)
    connecter_admin(client, "sans2fa")

    reponse = client.post(f"{GESTION}/{ressource.id}/approuver", json=APPROBATION)

    assert reponse.status_code == 403
    assert "double authentification" in reponse.json()["detail"]
