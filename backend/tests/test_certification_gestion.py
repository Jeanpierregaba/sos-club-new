"""Gestion de la certification par l'équipe (spec 029) : règles des badges versionnées, certificats révoqués ou
réémis avec la double authentification, et aucun accès pour les élèves, encadreurs et présidents."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.certification.models import Certificat, EtatCertificat
from app.comptes.models import Utilisateur
from app.notifications.models import Notification
from tests import test_quiz_banque as banque_027
from tests.certification import CERTIFICATION, acquerir, badges, certificats, creer_parcours, mettre_a_jour
from tests.conftest import Navigateur, connecter_admin
from tests.quiz import connecter, gains
from tests.test_quiz_banque import PUBLICATION

GESTION = "/api/admin/certification"
PUBLIC = "/api/certificats"
REGLES = {"noms": ["Cuivre", "Argent", "Or", "Platine", "Diamant Imhotep"], "paliers": [2, 5, 7, 9, 12]}

# Un collaborateur qui publie, avec la double authentification (spec 027).
publieur = banque_027.publieur


@pytest.fixture
def eleve(creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    return creer_eleve("ama")


def certifier(en_base: Callable[..., Any], joueur: Utilisateur) -> Certificat:
    acquerir(en_base, joueur, creer_parcours(en_base), range(1, 13))
    mettre_a_jour(en_base, joueur)
    return certificats(en_base, joueur.id)[0]


def journal(en_base: Callable[..., Any]) -> list[str]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(JournalAudit.action).where(JournalAudit.action.like("certif%")).order_by(JournalAudit.id)
            )
        ).all()
    )


def avis(en_base: Callable[..., Any], joueur: Utilisateur) -> list[str]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(Notification.type).where(Notification.utilisateur_id == joueur.id).order_by(Notification.id)
            )
        ).all()
    )


def total(en_base: Callable[..., Any], joueur: Utilisateur, action: str) -> int:
    return sum(g.montant for g in gains(en_base, joueur.id) if g.action == action)


# Règles des badges ------------------------------------------------------------------------------------------------


def test_changer_les_regles_ajoute_une_version(publieur: Navigateur, en_base: Callable[..., Any]) -> None:
    reponse = publieur.put(f"{GESTION}/regles", json=REGLES)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["version"] == 2
    historique = publieur.get(f"{GESTION}/regles").json()
    assert historique["en_cours"]["paliers"] == [2, 5, 7, 9, 12]
    assert [v["version"] for v in historique["versions"]] == [2, 1]
    assert journal(en_base) == ["certification_regles_modifiees"]


@pytest.mark.parametrize(
    "entree",
    [
        {"noms": REGLES["noms"], "paliers": [3, 3, 7, 9, 12]},
        {"noms": REGLES["noms"], "paliers": [3, 5, 9, 7, 12]},
        {"noms": REGLES["noms"], "paliers": [3, 5, 7, 9, 11]},
        {"noms": REGLES["noms"], "paliers": [0, 5, 7, 9, 12]},
        {"noms": REGLES["noms"], "paliers": [3, 5, 7, 12]},
        {"noms": ["Bronze", "", "Or", "Platine", "Diamant"], "paliers": [3, 5, 7, 9, 12]},
        {"noms": ["Bronze", "bronze", "Or", "Platine", "Diamant"], "paliers": [3, 5, 7, 9, 12]},
        {"noms": ["Bronze", "Argent", "Or", "Platine"], "paliers": [3, 5, 7, 9, 12]},
        {"noms": ["x" * 41, "Argent", "Or", "Platine", "Diamant"], "paliers": [3, 5, 7, 9, 12]},
    ],
)
def test_des_regles_incoherentes_sont_refusees(publieur: Navigateur, entree: dict[str, Any]) -> None:
    assert publieur.put(f"{GESTION}/regles", json=entree).status_code == 422


def test_changer_les_regles_exige_le_droit_dapprouver(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("pedago", droits={("quiz", "consulter"), ("quiz", "creer"), ("quiz", "modifier")})
    connecter_admin(client, "pedago")

    assert client.get(f"{GESTION}/regles").status_code == 200
    assert client.put(f"{GESTION}/regles", json=REGLES).status_code == 403


# Listes -----------------------------------------------------------------------------------------------------------


def test_lequipe_voit_les_certificats_et_les_badges(
    publieur: Navigateur, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    certificat = certifier(en_base, eleve)

    [ligne] = publieur.get(f"{GESTION}/certificats").json()["certificats"]
    delivres = publieur.get(f"{GESTION}/badges").json()["badges"]

    assert (ligne["numero"], ligne["titulaire"], ligne["etat"], ligne["role"]) == (
        certificat.numero,
        "Jean Kodjo",
        "valide",
        "eleve",
    )
    assert [b["nom"] for b in delivres] == ["Diamant Imhotep", "Platine", "Or", "Argent", "Bronze"]
    assert publieur.get(f"{GESTION}/certificats", params={"etat": "revoque"}).json()["certificats"] == []


# Révoquer ---------------------------------------------------------------------------------------------------------


def test_revoquer_retire_les_points_une_seule_fois_et_previent_le_titulaire(
    publieur: Navigateur, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    certificat = certifier(en_base, eleve)

    reponse = publieur.post(f"{GESTION}/certificats/{certificat.id}/revoquer", json={"motif": "Fraude avérée."})
    encore = publieur.post(f"{GESTION}/certificats/{certificat.id}/revoquer", json={"motif": "Fraude avérée."})

    assert reponse.status_code == 200, reponse.text
    assert (reponse.json()["etat"], reponse.json()["motif"]) == ("revoque", "Fraude avérée.")
    assert encore.status_code == 409
    assert total(en_base, eleve, "eleve.certification") == 0
    # Les badges et leurs points restent.
    assert len(badges(en_base, eleve.id)) == 5
    assert total(en_base, eleve, "eleve.badge") == 2500
    assert publieur.get(f"{PUBLIC}/{certificat.numero}").json()["etat"] == "revoque"
    assert "certification_revocation" in avis(en_base, eleve)
    assert journal(en_base)[-1] == "certificat_revoque"


def test_revoquer_sans_motif_est_refuse(publieur: Navigateur, eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    certificat = certifier(en_base, eleve)

    assert publieur.post(f"{GESTION}/certificats/{certificat.id}/revoquer", json={}).status_code == 422
    assert publieur.post(f"{GESTION}/certificats/{certificat.id}/revoquer", json={"motif": " "}).status_code == 422
    assert certificats(en_base, eleve.id)[0].etat is EtatCertificat.valide


def test_revoquer_exige_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any], eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    certificat = certifier(en_base, eleve)
    creer_collaborateur("sans2fa", droits=PUBLICATION)
    connecter_admin(client, "sans2fa")

    reponse = client.post(f"{GESTION}/certificats/{certificat.id}/revoquer", json={"motif": "Fraude avérée."})

    assert reponse.status_code == 403
    assert "double authentification" in reponse.json()["detail"]


def test_un_certificat_inconnu_repond_404(publieur: Navigateur) -> None:
    chemin = f"{GESTION}/certificats/00000000-0000-0000-0000-000000000000/revoquer"

    assert publieur.post(chemin, json={"motif": "Fraude avérée."}).status_code == 404


# Réémettre --------------------------------------------------------------------------------------------------------


def test_reemettre_donne_un_nouveau_numero_sans_nouveaux_points(
    publieur: Navigateur, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    ancien = certifier(en_base, eleve)
    en_base(lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == eleve.id).values(nom="Kodjo-Amegah")))
    avant = len(gains(en_base, eleve.id))

    reponse = publieur.post(f"{GESTION}/certificats/{ancien.id}/reemettre")

    assert reponse.status_code == 200, reponse.text
    nouveau = reponse.json()
    assert nouveau["numero"] != ancien.numero
    assert (nouveau["etat"], nouveau["titulaire"], nouveau["remplace_numero"]) == (
        "valide",
        "Jean Kodjo-Amegah",
        ancien.numero,
    )
    assert len(gains(en_base, eleve.id)) == avant
    ancien_public = publieur.get(f"{PUBLIC}/{ancien.numero}").json()
    assert (ancien_public["etat"], ancien_public["remplace_par"]) == ("remplace", nouveau["numero"])
    assert publieur.get(f"{PUBLIC}/{nouveau['numero']}").json()["etat"] == "valide"
    assert publieur.post(f"{GESTION}/certificats/{ancien.id}/reemettre").status_code == 409
    assert "certification_reemission" in avis(en_base, eleve)
    assert journal(en_base)[-1] == "certificat_reemis"


def test_un_certificat_revoque_puis_reemis_est_retabli_sans_ses_points(
    client: TestClient, publieur: Navigateur, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    ancien = certifier(en_base, eleve)
    publieur.post(f"{GESTION}/certificats/{ancien.id}/revoquer", json={"motif": "Erreur de saisie."})

    nouveau = publieur.post(f"{GESTION}/certificats/{ancien.id}/reemettre").json()

    assert nouveau["etat"] == "valide"
    assert total(en_base, eleve, "eleve.certification") == 0
    # Révoqué de nouveau : rien de plus à retirer.
    publieur.post(f"{GESTION}/certificats/{nouveau['id']}/revoquer", json={"motif": "Fraude avérée."})
    assert total(en_base, eleve, "eleve.certification") == 0
    connecter(client, "ama")
    assert client.get(f"{CERTIFICATION}/certificat.pdf").status_code == 404


# Droits -----------------------------------------------------------------------------------------------------------

ROUTES = [
    ("get", f"{GESTION}/regles", None),
    ("put", f"{GESTION}/regles", REGLES),
    ("get", f"{GESTION}/certificats", None),
    ("get", f"{GESTION}/badges", None),
    ("post", f"{GESTION}/certificats/{{id}}/revoquer", {"motif": "Pour voir."}),
    ("post", f"{GESTION}/certificats/{{id}}/reemettre", None),
]


@pytest.mark.parametrize("role", ["eleve", "president", "encadreur"])
@pytest.mark.parametrize(("methode", "chemin", "corps"), ROUTES)
def test_ni_eleve_ni_president_ni_encadreur_ne_gerent_la_certification(
    client: TestClient,
    eleve: Utilisateur,
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    role: str,
    methode: str,
    chemin: str,
    corps: Any,
) -> None:
    certificat = certifier(en_base, eleve)
    if role == "encadreur":
        creer_encadreur("kodjo")
        connecter(client, "kodjo")
    else:
        if role == "president":
            creer_club(eleve)
        connecter(client, "ama")

    reponse = getattr(client, methode)(chemin.format(id=certificat.id), **({"json": corps} if corps else {}))

    assert reponse.status_code == 403
    assert certificats(en_base, eleve.id)[0].etat is EtatCertificat.valide


def test_un_visiteur_ne_gere_rien(client: TestClient) -> None:
    assert client.get(f"{GESTION}/certificats").status_code == 401
