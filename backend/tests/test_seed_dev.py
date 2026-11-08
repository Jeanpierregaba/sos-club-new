"""Seed des comptes de développement : base locale seulement, accès utilisables tels quels."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.comptes.models import Utilisateur
from app.config import settings
from app.seed_dev import COMPTES, ProductionRefusee, ecrire_fichier, semer

pytestmark = pytest.mark.usefixtures("annuaire")


def acces_de(acces: list[dict[str, str]], identifiant: str) -> dict[str, str]:
    return next(a for a in acces if a["identifiant"] == identifiant)


def test_le_seed_cree_un_compte_par_profil(client: TestClient, en_base: Callable[..., Any]) -> None:
    acces = en_base(semer)

    assert len(acces) == len(COMPTES)
    comptes = select(func.count()).select_from(Utilisateur).where(Utilisateur.identifiant.like("dev.%"))
    assert en_base(lambda db: db.scalar(comptes)) == len(COMPTES)


def test_un_super_admin_se_connecte_avec_le_secret_ecrit(client: TestClient, en_base: Callable[..., Any]) -> None:
    super_admin = acces_de(en_base(semer), "dev.superadmin")

    etape = client.post(
        "/api/comptes/connexion", json={"identifiant": "dev.superadmin", "mot_de_passe": super_admin["mot_de_passe"]}
    ).json()
    code = pyotp.TOTP(super_admin["secret_totp"]).now()
    reponse = client.post("/api/comptes/connexion/code", json={"jeton": etape["jeton"], "code": code})

    assert reponse.status_code == 200
    assert client.get("/api/admin/collaborateurs").status_code == 200


def test_un_analyste_se_connecte_sans_code(client: TestClient, en_base: Callable[..., Any]) -> None:
    analyste = acces_de(en_base(semer), "dev.analyste")

    assert "secret_totp" not in analyste
    client.post(
        "/api/comptes/connexion", json={"identifiant": "dev.analyste", "mot_de_passe": analyste["mot_de_passe"]}
    )
    assert client.get("/api/admin/tableau-de-bord").status_code == 200
    assert client.get("/api/admin/inscrits").status_code == 403


def test_relancer_change_les_mots_de_passe(client: TestClient, en_base: Callable[..., Any]) -> None:
    ancien = acces_de(en_base(semer), "dev.eleve1")["mot_de_passe"]
    nouveau = acces_de(en_base(semer), "dev.eleve1")["mot_de_passe"]

    assert ancien != nouveau
    assert (
        client.post("/api/comptes/connexion", json={"identifiant": "dev.eleve1", "mot_de_passe": ancien}).status_code
        == 401
    )
    assert (
        client.post("/api/comptes/connexion", json={"identifiant": "dev.eleve1", "mot_de_passe": nouveau}).status_code
        == 200
    )


def test_refuse_en_production(en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "site_origine", "https://clubs-sante.tg")

    with pytest.raises(ProductionRefusee):
        en_base(semer)


def test_le_fichier_d_acces_est_prive(en_base: Callable[..., Any], tmp_path: Path) -> None:
    chemin = tmp_path / "acces.local"

    ecrire_fichier(en_base(semer), chemin)

    assert oct(chemin.stat().st_mode & 0o777) == "0o600"
    texte = chemin.read_text()
    assert "[dev.superadmin] Super-administrateur" in texte
    assert "identifiant    : dev.superadmin" in texte
    assert "e-mail         : dev.superadmin@exemple.tg" in texte


def test_un_super_admin_se_connecte_aussi_par_e_mail(client: TestClient, en_base: Callable[..., Any]) -> None:
    super_admin = acces_de(en_base(semer), "dev.superadmin")

    reponse = client.post(
        "/api/comptes/connexion",
        json={"identifiant": super_admin["email"], "mot_de_passe": super_admin["mot_de_passe"]},
    )

    assert reponse.json()["etape"] == "code"


def test_les_encadreurs_ont_un_profil_et_le_premier_est_actif(client: TestClient, en_base: Callable[..., Any]) -> None:
    en_base(semer)
    encadreur = acces_de(en_base(semer), "dev.encadreur")
    client.post(
        "/api/comptes/connexion", json={"identifiant": "dev.encadreur", "mot_de_passe": encadreur["mot_de_passe"]}
    )

    espace = client.get("/api/encadreurs/moi").json()

    assert (espace["etat"], espace["fonction"]) == ("actif", "enseignant")
    assert espace["points"]["total"] == 100
    assert acces_de(en_base(semer), "dev.encadreur.attente")["profil"] == "Encadreur (en attente)"


def test_les_eleves_ont_un_profil_et_leur_bienvenue(client: TestClient, en_base: Callable[..., Any]) -> None:
    en_base(semer)
    # Relancé : ni second profil, ni seconde ligne de bienvenue, ni second semestre.
    eleve = acces_de(en_base(semer), "dev.eleve1")
    client.post("/api/comptes/connexion", json={"identifiant": "dev.eleve1", "mot_de_passe": eleve["mot_de_passe"]})

    espace = client.get("/api/eleves/moi").json()

    assert espace["pseudonyme"] == "Ama du Golfe"
    assert espace["etablissement"]["nom"] == "Lycée de Tokoin I"
    assert espace["points"]["semestre"] is not None
    # La bienvenue (+100) et l'article de test publié (+50, spec 023).
    assert (espace["points"]["points_semestre"], espace["points"]["total"]) == (150, 150)


def test_le_seed_prepare_trois_articles_de_test_une_seule_fois(client: TestClient, en_base: Callable[..., Any]) -> None:
    from app.moderation.models import Contenu

    en_base(semer)
    en_base(semer)

    etats = sorted(en_base(lambda db: db.scalars(select(Contenu.etat).where(Contenu.type == "article"))).all())
    assert etats == ["a_corriger", "en_attente", "publie"]
    publics = [a for a in client.get("/api/articles").json()["articles"] if a["nature"] == "article"]
    assert [a["titre"] for a in publics] == ["Article de test — Un point d'eau dans la cour"]
    assert publics[0]["signature"]["club"] == "Club Santé Tokoin"


def test_le_seed_prepare_deux_commentaires_de_test_une_seule_fois(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    from app.moderation.models import Contenu

    en_base(semer)
    en_base(semer)

    etats = sorted(en_base(lambda db: db.scalars(select(Contenu.etat).where(Contenu.type == "commentaire"))).all())
    assert etats == ["en_attente", "publie"]
    publics = client.get("/api/articles/article-de-test-un-point-d-eau-dans-la-cour/commentaires").json()
    assert [c["texte"][:22] for c in publics["commentaires"]] == ["[Commentaire de test] "]


def test_le_seed_prepare_une_actualite_et_une_proposition_de_fiche(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    from app.moderation.models import Contenu

    en_base(semer)
    en_base(semer)

    lignes = en_base(lambda db: db.execute(select(Contenu.type, Contenu.etat).where(Contenu.club_id.is_not(None))))
    assert sorted((t, e.value) for t, e in lignes) == [("actualite", "publie"), ("fiche_club", "en_attente")]
    natures = [a["nature"] for a in client.get("/api/articles").json()["articles"]]
    assert sorted(natures) == ["actualite", "article"]


def test_le_seed_prepare_trois_quiz_de_test_une_seule_fois(en_base: Callable[..., Any]) -> None:
    from app.quiz.models import Quiz

    en_base(semer)
    en_base(semer)

    lignes = en_base(lambda db: db.execute(select(Quiz.etat, Quiz.contenu_de_test, Quiz.titre)))
    assert sorted(e.value for e, _, _ in lignes) == ["brouillon", "publie", "soumis"]
    assert all(test and titre.startswith("[Test]") for _, test, titre in lignes)
