"""Effacement des photos refusées depuis plus de 90 jours (spec 024)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.comptes.models import Utilisateur
from app.moderation import photos
from app.moderation.models import DecisionModeration, Photo
from tests.conftest import Navigateur, connecter_admin
from tests.photos import FILE, MODERATION, ajouter, connecter, creer_article, decider, soumettre

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def auteur(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Navigateur:
    creer_eleve()
    navigateur = Navigateur(client)
    connecter(navigateur, "eleve1")
    return navigateur


@pytest.fixture
def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, "moderateur")  # type: ignore[arg-type]
    return navigateur


def vieillir(en_base: Callable[..., Any], jours: int) -> None:
    quand = datetime.now(UTC) - timedelta(days=jours)
    en_base(lambda db: db.execute(update(DecisionModeration).values(decide_le=quand)))


def purger(en_base: Callable[..., Any]) -> int:
    return int(en_base(photos.purger))


def fichiers(dossier: Path) -> int:
    return len(list((dossier / "photos").glob("*.webp")))


def test_les_photos_dun_article_refuse_depuis_plus_de_90_jours_sont_effacees(
    auteur: Navigateur, moderateur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"])
    soumettre(auteur, article["id"])
    decider(moderateur, article["id"], "refuser", "Hors sujet.")
    vieillir(en_base, 91)

    assert purger(en_base) == 1

    assert fichiers(dossier_fichiers) == 0
    assert en_base(lambda db: db.scalar(select(Photo.efface_le))) is not None
    (photo,) = moderateur.get(f"{FILE}/{article['id']}").json()["photos_soumises"]
    assert photo["effacee"] is True and photo["attestation"]
    # Une seconde purge ne refait rien.
    assert purger(en_base) == 0


def test_avant_90_jours_rien_nest_efface(
    auteur: Navigateur, moderateur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"])
    soumettre(auteur, article["id"])
    decider(moderateur, article["id"], "refuser", "Hors sujet.")
    vieillir(en_base, 89)

    assert purger(en_base) == 0
    assert fichiers(dossier_fichiers) == 2


def test_une_photo_encore_en_ligne_nest_pas_effacee_apres_le_refus_dune_revision(
    client: TestClient,
    auteur: Navigateur,
    moderateur: Navigateur,
    dossier_fichiers: Path,
    en_base: Callable[..., Any],
) -> None:
    article = creer_article(auteur)
    en_ligne = ajouter(auteur, article["id"])["photos"][0]["id"]
    soumettre(auteur, article["id"])
    adresse = decider(moderateur, article["id"], "approuver")["adresse"]
    refusee = next(p["id"] for p in ajouter(auteur, article["id"])["photos"] if p["id"] != en_ligne)
    soumettre(auteur, article["id"])
    decider(moderateur, article["id"], "refuser", "Photo floue.")
    vieillir(en_base, 91)

    assert purger(en_base) == 1

    effacees = en_base(lambda db: db.scalars(select(Photo.id).where(Photo.efface_le.is_not(None)))).all()
    assert [str(i) for i in effacees] == [refusee]
    assert client.get(f"/api/articles/{adresse}/photos/{en_ligne}/grande").status_code == 200
    assert fichiers(dossier_fichiers) == 2


def test_les_photos_dun_article_publie_ne_sont_jamais_effacees(
    auteur: Navigateur, moderateur: Navigateur, dossier_fichiers: Path, en_base: Callable[..., Any]
) -> None:
    article = creer_article(auteur)
    ajouter(auteur, article["id"])
    soumettre(auteur, article["id"])
    decider(moderateur, article["id"], "approuver")
    vieillir(en_base, 400)

    assert purger(en_base) == 0
    assert fichiers(dossier_fichiers) == 2
