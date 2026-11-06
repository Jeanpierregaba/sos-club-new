"""Le défi du jour (spec 021, tâche 2) : tirage stable dans la journée, correction séparée, aucun point."""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.jeux import banque_initiale, defis
from app.jeux.models import DefiQuestion
from app.points.models import MouvementPoints

DU_JOUR = "/api/jeux/defi-du-jour"


@pytest.fixture
def banque(en_base: Callable[..., Any]) -> None:
    en_base(banque_initiale.charger)


def tirer(en_base: Callable[..., Any], jour: date) -> DefiQuestion:
    return en_base(lambda db: defis.du_jour(db, jour))


def test_la_question_part_sans_sa_reponse(client: TestClient, banque: None) -> None:
    reponse = client.get(DU_JOUR)

    assert reponse.status_code == 200
    assert set(reponse.json()) == {"id", "categorie", "question", "options", "ma_reponse"}
    assert reponse.json()["ma_reponse"] is None


def test_la_meme_question_toute_la_journee_et_une_autre_le_lendemain(
    client: TestClient, banque: None, en_base: Callable[..., Any]
) -> None:
    assert client.get(DU_JOUR).json() == client.get(DU_JOUR).json()
    jour = date(2026, 11, 6)
    assert tirer(en_base, jour).id == tirer(en_base, jour).id
    assert tirer(en_base, jour).id != tirer(en_base, jour + timedelta(days=1)).id


def test_la_rotation_parcourt_toute_la_banque(banque: None, en_base: Callable[..., Any]) -> None:
    jour = date(2026, 11, 6)
    tirees = {tirer(en_base, jour + timedelta(days=i)).id for i in range(len(banque_initiale.QUESTIONS))}

    assert len(tirees) == len(banque_initiale.QUESTIONS)


def test_une_question_desactivee_nest_jamais_tiree(banque: None, en_base: Callable[..., Any]) -> None:
    async def desactiver(db: AsyncSession) -> None:
        await db.execute(update(DefiQuestion).where(DefiQuestion.ordre != 2).values(actif=False))

    en_base(desactiver)
    jour = date(2026, 11, 6)

    assert {tirer(en_base, jour + timedelta(days=i)).ordre for i in range(5)} == {2}


def test_sans_question_la_route_repond_404(client: TestClient) -> None:
    assert client.get(DU_JOUR).status_code == 404


def test_la_correction_donne_la_bonne_reponse_et_lexplication(
    client: TestClient, banque: None, en_base: Callable[..., Any]
) -> None:
    defi = client.get(DU_JOUR).json()
    question = en_base(lambda db: db.get(DefiQuestion, defi["id"]))
    avant = en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints)))
    url = f"/api/jeux/defis/{defi['id']}/reponse"

    juste = client.post(url, json={"choix": question.bonne_reponse}).json()
    fausse = client.post(url, json={"choix": (question.bonne_reponse + 1) % len(question.options)}).json()

    # Un visiteur : la correction, sans point ni réponse enregistrée.
    assert juste == {
        "choix": question.bonne_reponse,
        "correcte": True,
        "bonne_reponse": question.bonne_reponse,
        "explication": question.explication,
        "points": 0,
        "deja_repondu": False,
    }
    assert fausse["correcte"] is False
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints))) == avant


def test_la_correction_vaut_meme_apres_minuit(banque: None, client: TestClient, en_base: Callable[..., Any]) -> None:
    hier = tirer(en_base, date.today() - timedelta(days=1))

    reponse = client.post(f"/api/jeux/defis/{hier.id}/reponse", json={"choix": hier.bonne_reponse})

    assert reponse.json()["correcte"] is True


def test_un_choix_hors_des_options_est_refuse(client: TestClient, banque: None, en_base: Callable[..., Any]) -> None:
    # Les questions de la banque initiale ont trois options : 3 n'existe pas.
    defi = client.get(DU_JOUR).json()
    url = f"/api/jeux/defis/{defi['id']}/reponse"

    assert client.post(url, json={"choix": len(defi["options"])}).status_code == 422
    assert client.post(url, json={"choix": -1}).status_code == 422
    assert client.post(url, json={"choix": 9}).status_code == 422


def test_un_defi_inconnu_ou_desactive_est_introuvable(
    client: TestClient, banque: None, en_base: Callable[..., Any]
) -> None:
    defi = client.get(DU_JOUR).json()

    async def desactiver(db: AsyncSession) -> None:
        await db.execute(update(DefiQuestion).where(DefiQuestion.id == defi["id"]).values(actif=False))

    en_base(desactiver)

    assert client.post(f"/api/jeux/defis/{defi['id']}/reponse", json={"choix": 0}).status_code == 404
    inconnu = "00000000-0000-7000-8000-000000000000"
    assert client.post(f"/api/jeux/defis/{inconnu}/reponse", json={"choix": 0}).status_code == 404


def test_le_chargement_est_idempotent(banque: None, en_base: Callable[..., Any]) -> None:
    assert en_base(banque_initiale.charger) == 0
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(DefiQuestion))) == 30


def test_la_base_refuse_une_bonne_reponse_hors_des_options(en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(
            DefiQuestion(
                ordre=99, categorie="Test", question="?", options=["Oui", "Non"], bonne_reponse=2, explication="."
            )
        )
        await db.flush()

    with pytest.raises(IntegrityError):
        en_base(inserer)
