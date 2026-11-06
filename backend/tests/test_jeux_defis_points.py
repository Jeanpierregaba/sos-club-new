"""Points de la question du jour (spec 022, tâche 2) : +20 à la première réponse juste du jour d'un élève actif,
une seule réponse comptée par jour, rien pour un visiteur ou un autre profil."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Utilisateur
from app.jeux import banque_initiale, defis
from app.jeux.models import DefiQuestion, DefiReponse
from app.points.models import LigneBareme, MouvementPoints
from app.points.service import aujourd_hui
from tests.conftest import MOT_DE_PASSE, connecter_admin

DU_JOUR = "/api/jeux/defi-du-jour"


@pytest.fixture(autouse=True)
def banque(en_base: Callable[..., Any]) -> None:
    en_base(banque_initiale.charger)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama", "Ama")
    connecter(client, "ama")
    return utilisateur


def connecter(client: TestClient, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


def question_du_jour(en_base: Callable[..., Any]) -> DefiQuestion:
    return en_base(defis.du_jour)


def repondre(client: TestClient, defi: DefiQuestion, choix: int) -> dict[str, Any]:
    reponse = client.post(f"/api/jeux/defis/{defi.id}/reponse", json={"choix": choix})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def fausse(defi: DefiQuestion) -> int:
    return (defi.bonne_reponse + 1) % len(defi.options)


def gains(en_base: Callable[..., Any], utilisateur: Utilisateur | None = None) -> list[tuple[str, int]]:
    async def lire(db: AsyncSession) -> list[tuple[str, int]]:
        requete = select(MouvementPoints.action, MouvementPoints.montant).where(
            MouvementPoints.action == "eleve.question_jour"
        )
        if utilisateur is not None:
            requete = requete.where(MouvementPoints.utilisateur_id == utilisateur.id)
        return [(a, m) for a, m in await db.execute(requete)]

    return en_base(lire)


def reponses_enregistrees(en_base: Callable[..., Any]) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(DefiReponse)))


def test_une_bonne_reponse_rapporte_20_points_une_seule_fois(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    defi = question_du_jour(en_base)

    corps = repondre(client, defi, defi.bonne_reponse)

    assert (corps["correcte"], corps["points"], corps["deja_repondu"]) == (True, 20, False)
    assert gains(en_base, eleve) == [("eleve.question_jour", 20)]


def test_une_deuxieme_reponse_du_jour_ne_compte_pas(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    defi = question_du_jour(en_base)
    repondre(client, defi, defi.bonne_reponse)

    encore = repondre(client, defi, fausse(defi))

    # C'est la première réponse qui est renvoyée, sans nouveau crédit.
    assert (encore["choix"], encore["correcte"], encore["deja_repondu"]) == (defi.bonne_reponse, True, True)
    assert encore["points"] == 20
    assert gains(en_base, eleve) == [("eleve.question_jour", 20)]
    assert reponses_enregistrees(en_base) == 1


def test_une_reponse_fausse_ne_rapporte_rien_et_bloque_la_journee(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    defi = question_du_jour(en_base)

    premiere = repondre(client, defi, fausse(defi))
    seconde = repondre(client, defi, defi.bonne_reponse)

    assert (premiere["correcte"], premiere["points"]) == (False, 0)
    assert (seconde["correcte"], seconde["points"], seconde["deja_repondu"]) == (False, 0, True)
    assert gains(en_base) == []


def test_apres_reconnexion_la_question_montre_la_reponse_deja_donnee(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    defi = question_du_jour(en_base)
    repondre(client, defi, defi.bonne_reponse)
    client.post("/api/comptes/deconnexion")

    assert client.get(DU_JOUR).json()["ma_reponse"] is None
    connecter(client, "ama")
    ma_reponse = client.get(DU_JOUR).json()["ma_reponse"]

    assert ma_reponse["deja_repondu"] is True
    assert (ma_reponse["choix"], ma_reponse["points"]) == (defi.bonne_reponse, 20)
    assert repondre(client, defi, defi.bonne_reponse)["deja_repondu"] is True
    assert len(gains(en_base, eleve)) == 1


def test_un_visiteur_et_un_encadreur_ne_gagnent_rien(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    defi = question_du_jour(en_base)
    assert repondre(client, defi, defi.bonne_reponse)["points"] == 0

    creer_encadreur("prof")
    connecter(client, "prof")
    assert repondre(client, defi, defi.bonne_reponse)["points"] == 0
    assert repondre(client, defi, defi.bonne_reponse)["deja_repondu"] is False

    assert gains(en_base) == []
    assert reponses_enregistrees(en_base) == 0


def test_un_collaborateur_ne_gagne_rien(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur("chef", super_admin=True, double_auth=True)
    connecter_admin(client, "chef")
    defi = question_du_jour(en_base)

    assert repondre(client, defi, defi.bonne_reponse)["points"] == 0
    assert gains(en_base) == []


def test_la_question_dun_autre_jour_ne_rapporte_rien(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    hier = en_base(lambda db: defis.du_jour(db, aujourd_hui() - timedelta(days=1)))

    corps = repondre(client, hier, hier.bonne_reponse)

    assert (corps["correcte"], corps["points"], corps["deja_repondu"]) == (True, 0, False)
    assert reponses_enregistrees(en_base) == 0
    # La question du jour reste à jouer.
    assert client.get(DU_JOUR).json()["ma_reponse"] is None


def test_un_bareme_a_zero_enregistre_la_reponse_sans_point(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    async def couper(db: AsyncSession) -> None:
        await db.execute(update(LigneBareme).where(LigneBareme.code == "eleve.question_jour").values(montant=0))

    en_base(couper)
    defi = question_du_jour(en_base)

    assert repondre(client, defi, defi.bonne_reponse)["points"] == 0
    assert reponses_enregistrees(en_base) == 1
    assert gains(en_base) == []


def test_deux_reponses_simultanees_ne_creditent_quune_fois(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """La seconde requête n'a pas encore vu la première : la contrainte unique tranche."""
    defi = question_du_jour(en_base)
    repondre(client, defi, defi.bonne_reponse)
    vraie = defis.reponse_du_jour
    appels = {"n": 0}

    async def aveugle(db: AsyncSession, utilisateur: Utilisateur | None, jour: Any) -> Any:
        appels["n"] += 1
        return None if appels["n"] == 1 else await vraie(db, utilisateur, jour)

    monkeypatch.setattr(defis, "reponse_du_jour", aveugle)

    corps = repondre(client, defi, defi.bonne_reponse)

    assert corps["deja_repondu"] is True
    assert len(gains(en_base, eleve)) == 1
    assert reponses_enregistrees(en_base) == 1
