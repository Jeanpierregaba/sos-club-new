"""Les quiz du parcours de certification dans la banque (spec 029) : une place de 1 à 12, un fascicule publié
éventuel, une seule publication par place, et des paramètres propres au parcours."""

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.bibliotheque.models import CategorieRessource, EtatRessource
from app.comptes.models import Utilisateur
from app.quiz import banque
from app.quiz.models import EtatQuiz, Quiz
from app.quiz.schemas_banque import Approbation
from tests import test_quiz_banque as banque_027
from tests.bibliotheque import creer_ressource
from tests.conftest import Navigateur, moteur_test
from tests.quiz import creer_quiz, regler
from tests.test_quiz_banque import APPROBATION, BANQUE, PUBLICATION, axe, question

# Les collaborateurs de la spec 027 : l'un prépare, l'autre publie avec la double authentification.
gestionnaire = banque_027.gestionnaire
publieur = banque_027.publieur


def preparer(client: Any, en_base: Callable[..., Any], questions: int = 15, **champs: Any) -> dict[str, Any]:
    entree = {"titre": "Les gestes barrières", "axe_code": axe(en_base), "parcours": "certification", "place": 1}
    reponse = client.post(BANQUE, json=entree | champs)
    assert reponse.status_code == 201, reponse.text
    corps = reponse.json()
    for i in range(questions):
        corps = client.post(f"{BANQUE}/{corps['id']}/questions", json=question(i + 1)).json()
    return corps


def soumettre(client: Any, corps: dict[str, Any]) -> dict[str, Any]:
    reponse = client.post(f"{BANQUE}/{corps['id']}/soumettre")
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def fascicule(en_base: Callable[..., Any], **champs: Any) -> Any:
    return creer_ressource(en_base, categorie=CategorieRessource.fascicule, titre="Fascicule 1", **champs)


# Préparer ---------------------------------------------------------------------------------------------------------


def test_un_quiz_de_certification_a_une_place_et_un_fascicule(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    ressource = fascicule(en_base)

    corps = preparer(client, en_base, place=4, ressource_id=str(ressource.id))

    assert (corps["parcours"], corps["place"], corps["ressource_id"]) == ("certification", 4, str(ressource.id))
    assert corps["ressource_titre"] == "Fascicule 1"


def test_un_quiz_de_jeux_na_ni_place_ni_fascicule(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = client.post(BANQUE, json={"titre": "Quiz", "axe_code": axe(en_base), "place": 3}).json()

    assert (corps["parcours"], corps["place"], corps["ressource_id"]) == ("jeux", None, None)


@pytest.mark.parametrize("place", [None, 0, 13])
def test_une_place_absente_ou_hors_limites_est_refusee(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], place: int | None
) -> None:
    entree = {"titre": "Quiz", "axe_code": axe(en_base), "parcours": "certification", "place": place}

    assert client.post(BANQUE, json=entree).status_code == 422


@pytest.mark.parametrize(
    "ressource",
    [
        {"categorie": CategorieRessource.guide},
        {"categorie": CategorieRessource.fascicule, "etat": EtatRessource.brouillon},
    ],
)
def test_le_fascicule_doit_etre_un_fascicule_publie(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], ressource: dict[str, Any]
) -> None:
    autre = creer_ressource(en_base, **ressource)
    entree = {
        "titre": "Quiz",
        "axe_code": axe(en_base),
        "parcours": "certification",
        "place": 1,
        "ressource_id": str(autre.id),
    }

    reponse = client.post(BANQUE, json=entree)

    assert reponse.status_code == 422
    assert "fascicule" in reponse.json()["detail"]


def test_la_place_se_change_en_brouillon(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = preparer(client, en_base, questions=0, place=2)
    entree = {"titre": corps["titre"], "axe_code": corps["axe_code"], "parcours": "certification", "place": 5}

    reponse = client.put(f"{BANQUE}/{corps['id']}", json=entree)

    assert reponse.status_code == 200
    assert reponse.json()["place"] == 5


def test_le_parcours_dun_quiz_deja_joue_ne_change_plus(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = client.post(BANQUE, json={"titre": "Quiz", "axe_code": axe(en_base)}).json()

    async def jouee(db: AsyncSession) -> None:
        from datetime import UTC, datetime

        from app.quiz.models import TentativeQuiz
        from app.quiz.parametres import en_cours

        p = await en_cours(db)
        maintenant = datetime.now(UTC)
        db.add(
            TentativeQuiz(
                quiz_id=corps["id"],
                joueur_id=gestionnaire.id,
                parametres_id=p.id,
                jour=maintenant.date(),
                commencee_le=maintenant,
                derniere_activite=maintenant,
            )
        )

    en_base(jouee)
    entree = {"titre": "Quiz", "axe_code": corps["axe_code"], "parcours": "certification", "place": 1}

    reponse = client.put(f"{BANQUE}/{corps['id']}", json=entree)

    assert reponse.status_code == 422
    assert "parcours" in reponse.json()["detail"]


def test_la_liste_se_filtre_par_parcours(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    creer_quiz(en_base, titre="Jeu")
    creer_quiz(en_base, titre="Place 1", place=1)

    certification = client.get(BANQUE, params={"parcours": "certification"}).json()["quiz"]
    jeux = client.get(BANQUE, params={"parcours": "jeux"}).json()["quiz"]

    assert [q["titre"] for q in certification] == ["Place 1"]
    assert [q["titre"] for q in jeux] == ["Jeu"]
    assert len(client.get(BANQUE).json()["quiz"]) == 2


# Publier ----------------------------------------------------------------------------------------------------------


def test_une_place_deja_occupee_refuse_une_seconde_publication(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    creer_quiz(en_base, titre="Déjà en ligne", place=4)
    corps = soumettre(client, preparer(client, en_base, place=4))

    reponse = publieur.post(f"{BANQUE}/{corps['id']}/approuver", json=APPROBATION)

    assert reponse.status_code == 409
    assert "place 4" in reponse.json()["detail"]


def test_une_place_liberee_par_une_depublication_accepte_un_remplacant(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    ancien = creer_quiz(en_base, titre="Ancien", place=4)
    corps = soumettre(client, preparer(client, en_base, place=4))

    publieur.post(f"{BANQUE}/{ancien.id}/depublier", json={"motif": "Remplacé par une version revue."})
    reponse = publieur.post(f"{BANQUE}/{corps['id']}/approuver", json=APPROBATION)

    assert reponse.status_code == 200, reponse.text


def test_deux_approbations_simultanees_sur_une_place_une_seule_passe(
    client: TestClient,
    gestionnaire: Utilisateur,
    creer_collaborateur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    premier = soumettre(client, preparer(client, en_base, place=7))
    second = soumettre(client, preparer(client, en_base, place=7))
    pub1 = creer_collaborateur("pub1", droits=PUBLICATION, double_auth=True)
    pub2 = creer_collaborateur("pub2", droits=PUBLICATION, double_auth=True)

    async def decider(qui: Utilisateur, quiz_id: str) -> str:
        from app.admin.models import Collaborateur

        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == qui.id))
            acces = Acces(utilisateur=qui, collaborateur=collaborateur)  # type: ignore[arg-type]
            try:
                await banque.approuver(db, acces, quiz_id, Approbation(**APPROBATION), "test")
                await asyncio.sleep(0.2)
                await db.commit()
                return "ok"
            except banque.EtatInvalide:
                return "conflit"

    async def scenario() -> list[str]:
        return await asyncio.gather(decider(pub1, premier["id"]), decider(pub2, second["id"]))

    assert sorted(asyncio.run(scenario())) == ["conflit", "ok"]
    publies = en_base(lambda db: db.scalars(select(Quiz).where(Quiz.etat == EtatQuiz.publie))).all()
    assert len(publies) == 1


# Paramètres -------------------------------------------------------------------------------------------------------


def test_le_parcours_de_certification_a_ses_propres_parametres(publieur: Navigateur) -> None:
    entree = {"nb_questions": 10, "temps_ms": 8000, "tolerance_ms": 2000, "seuil": 9, "tentatives_par_jour": 3}

    reponse = publieur.put(f"{BANQUE}/parametres", params={"parcours": "certification"}, json=entree)

    assert reponse.status_code == 200, reponse.text
    certification = publieur.get(f"{BANQUE}/parametres", params={"parcours": "certification"}).json()
    jeux = publieur.get(f"{BANQUE}/parametres").json()
    assert certification["en_cours"]["seuil"] == 9
    assert jeux["en_cours"]["seuil"] == 12


def test_la_reserve_dun_quiz_de_certification_suit_les_parametres_de_son_parcours(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    regler(en_base, parcours="certification", nb_questions=10, seuil=8)
    corps = preparer(client, en_base, questions=10)

    assert corps["questions_requises"] == 10
    assert client.post(f"{BANQUE}/{corps['id']}/soumettre").status_code == 200


def test_un_parcours_inconnu_est_refuse(publieur: Navigateur) -> None:
    assert publieur.get(f"{BANQUE}/parametres", params={"parcours": "autre"}).status_code == 422
