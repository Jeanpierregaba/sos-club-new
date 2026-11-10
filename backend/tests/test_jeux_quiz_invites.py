"""Quiz ouverts depuis la page des jeux (spec 031) : un joueur sans compte joue trois quiz au plus, sans points
(limite portée de 2 à 3 le 2026-11-10)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.comptes.models import Role, Utilisateur
from app.jeux import invites
from app.points.models import MouvementPoints
from app.quiz.models import TentativeQuiz
from tests.certification import creer_parcours
from tests.quiz import Horloge, bon_choix, connecter, creer_quiz, figer_horloge

QUIZ = "/api/jeux/quiz"


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


def lancer(client: TestClient, quiz: Any) -> Any:
    return client.post(f"{QUIZ}/{quiz.id}/tentatives")


def jouer_tout(client: TestClient, etat: dict[str, Any]) -> dict[str, Any]:
    while etat["question"] is not None:
        q = etat["question"]
        reponse = client.post(
            f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses", json={"rang": q["rang"], "choix": bon_choix(q)}
        )
        assert reponse.status_code == 200, reponse.text
        etat = reponse.json()
    return etat


def invites_en_base(en_base: Callable[..., Any]) -> list[Utilisateur]:
    return en_base(lambda db: db.scalars(select(Utilisateur).where(Utilisateur.role == Role.invite))).all()


def test_le_catalogue_est_public(client: TestClient, en_base: Callable[..., Any]) -> None:
    creer_quiz(en_base, titre="Hygiène")
    creer_quiz(en_base, titre="Trop court", questions=5)

    corps = client.get(QUIZ).json()

    assert [q["titre"] for q in corps["quiz"]] == ["Hygiène"]
    assert (corps["limite"], corps["restants"], corps["connecte"]) == (3, 3, False)


def test_un_joueur_sans_compte_joue_sans_points(
    client: TestClient, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_quiz(en_base)

    reponse = lancer(client, quiz)

    assert reponse.status_code == 201
    assert invites.COOKIE in reponse.cookies
    final = jouer_tout(client, reponse.json())
    assert final["resultat"]["reussie"] is True
    (invite,) = invites_en_base(en_base)
    assert (invite.email, invite.mot_de_passe_hash) == (None, "")
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints))) == 0
    assert client.get(QUIZ).json()["restants"] == 2


def test_au_quatrieme_quiz_il_faut_un_compte(client: TestClient, en_base: Callable[..., Any], heure: Horloge) -> None:
    quiz = [creer_quiz(en_base, titre=f"Quiz {i}") for i in range(4)]
    for un in quiz[:3]:
        assert lancer(client, un).status_code == 201

    refus = lancer(client, quiz[3])

    assert refus.status_code == 403
    assert "3 quiz gratuits" in refus.json()["detail"]
    # Le site reconnaît la fin de l'essai à ce marqueur, pas au seul code 403.
    assert refus.headers["x-raison"] == "fin-essai"
    assert client.get(QUIZ).json()["restants"] == 0
    # Rejouer un des quiz déjà commencés reste possible.
    assert lancer(client, quiz[0]).status_code == 201
    assert len(invites_en_base(en_base)) == 1


def test_le_jeton_dinvite_ne_vaut_pas_une_session(
    client: TestClient, en_base: Callable[..., Any], heure: Horloge
) -> None:
    from app.config import settings

    quiz = [creer_quiz(en_base, titre=f"Quiz {i}") for i in range(3)]
    jeton = lancer(client, quiz[0]).cookies[invites.COOKIE]
    client.cookies.set(settings.cookie_session, jeton)

    assert client.get("/api/comptes/moi").status_code == 401
    assert client.post(f"/api/quiz/{quiz[2].id}/tentatives").status_code == 401


def test_la_certification_reste_fermee(client: TestClient, en_base: Callable[..., Any]) -> None:
    parcours = creer_parcours(en_base, places=[1])
    creer_quiz(en_base, titre="Jeu")

    # Un quiz de certification n'est ni listé ni jouable ici.
    assert all(q["id"] != str(parcours[1].id) for q in client.get(QUIZ).json()["quiz"])
    assert lancer(client, parcours[1]).status_code == 404


def test_un_compte_connecte_joue_depuis_ses_quiz(
    client: TestClient, en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    quiz = creer_quiz(en_base)
    creer_eleve("ama")
    connecter(client, "ama")

    assert client.get(QUIZ).json()["connecte"] is True
    assert lancer(client, quiz).status_code == 409
    assert invites_en_base(en_base) == []


def test_une_partie_dun_autre_invite_est_introuvable(
    client: TestClient, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_quiz(en_base)
    etat = lancer(client, quiz).json()
    client.cookies.clear()

    assert client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").status_code == 404
    lancer(client, quiz)
    assert client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").status_code == 404


def test_les_invites_napparaissent_pas_dans_les_inscrits(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], heure: Horloge
) -> None:
    from tests.conftest import connecter_admin

    lancer(client, creer_quiz(en_base))
    client.cookies.clear()
    creer_collaborateur("chef", droits={("inscrits", "consulter"), ("tableau_de_bord", "consulter")})
    connecter_admin(client, "chef")

    assert client.get("/api/admin/inscrits").json()["total"] == 1  # le collaborateur seulement
    assert "invite" not in client.get("/api/admin/tableau-de-bord").json()["comptes_par_profil"]


def test_la_purge_efface_les_invites_de_plus_de_7_jours(
    client: TestClient, en_base: Callable[..., Any], heure: Horloge
) -> None:
    lancer(client, creer_quiz(en_base))
    en_base(lambda db: db.execute(update(Utilisateur).values(cree_le=datetime.now(UTC) - timedelta(days=8))))

    assert en_base(invites.purger) == 1

    assert invites_en_base(en_base) == []
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(TentativeQuiz))) == 0


def test_les_quiz_des_jeux_laissent_20_secondes_et_la_certification_5(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    """Le chrono des jeux passe à 20 s (2026-11-10) ; la certification garde ses propres paramètres."""
    from app.quiz import parametres

    assert client.get(QUIZ).json()["temps_ms"] == 20000

    async def certification(db: Any) -> int:
        return (await parametres.en_cours(db, "certification")).temps_ms

    assert en_base(certification) == 5000


def test_un_refus_d_origine_n_est_pas_une_fin_d_essai(client: TestClient, en_base: Callable[..., Any]) -> None:
    """Le bug du 2026-11-10 : un 403 sans rapport (ici le contrôle d'origine) passait pour la fin de l'essai."""
    quiz = creer_quiz(en_base)

    refus = client.post(f"{QUIZ}/{quiz.id}/tentatives", headers={"Origin": "https://autre-site.example"})

    assert refus.status_code == 403
    assert "x-raison" not in refus.headers
    assert client.get(QUIZ).json()["restants"] == 3
