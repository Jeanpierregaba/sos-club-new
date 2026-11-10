"""« Quel axe est fait pour toi ? » (specs 021 et 032) : table de correspondance, départages, parties gardées par
l'API (3 par élève, reprise, concurrence), accès élève."""

import asyncio
from collections import Counter
from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import StatutCompte, Utilisateur
from app.jeux import parties_quel_axe
from app.jeux.models import PartieQuelAxe
from app.jeux.quel_axe import ORDRE_AXES, QUESTIONS, calculer
from app.points.models import MouvementPoints
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin, moteur_test

ETAT = "/api/jeux/quel-axe"
PARTIES = "/api/jeux/quel-axe/parties"

# La table du document fonctionnel, recopiée à la main : (question, réponse) → (axe +3, axe +1).
TABLE = {
    (1, "A"): ("TV", "LM"),
    (1, "B"): ("SS", "SE"),
    (1, "C"): ("LM", "EVSS"),
    (1, "D"): ("GI", "GB"),
    (2, "A"): ("EVSS", "TV"),
    (2, "B"): ("SE", "EVSS"),
    (2, "C"): ("GB", "GI"),
    (2, "D"): ("SS", "LM"),
    (3, "A"): ("TV", "GB"),
    (3, "B"): ("LM", "SS"),
    (3, "C"): ("GI", "GB"),
    (3, "D"): ("EVSS", "SE"),
    (4, "A"): ("GI", "SE"),
    (4, "B"): ("SE", "EVSS"),
    (4, "C"): ("GB", "SS"),
    (4, "D"): ("EVSS", "TV"),
    (5, "A"): ("SS", "SE"),
    (5, "B"): ("TV", "LM"),
    (5, "C"): ("LM", "EVSS"),
    (5, "D"): ("GB", "GI"),
    (6, "A"): ("SE", "GI"),
    (6, "B"): ("GB", "TV"),
    (6, "C"): ("EVSS", "LM"),
    (6, "D"): ("SS", "SE"),
    (7, "A"): ("GI", "GB"),
    (7, "B"): ("TV", "EVSS"),
    (7, "C"): ("LM", "SS"),
    (7, "D"): ("SE", "TV"),
}


def test_les_28_reponses_suivent_la_table_du_document() -> None:
    code = {
        (numero, r.lettre): (r.principal, r.secondaire)
        for numero, question in enumerate(QUESTIONS, start=1)
        for r in question.reponses
    }
    assert code == TABLE


def test_chaque_axe_est_axe_principal_4_fois() -> None:
    assert Counter(principal for principal, _ in TABLE.values()) == dict.fromkeys(ORDRE_AXES, 4)


def test_sans_egalite() -> None:
    resultat = calculer(list("AAAAAAB"))

    assert (resultat.principal, resultat.autres) == ("TV", ("SE", "GI"))
    assert (resultat.scores["TV"], resultat.scores["SE"]) == (10, 5)


def test_a_egalite_laxe_le_plus_souvent_principal_passe_devant() -> None:
    # EVSS et TV ont 9 points ; EVSS a été trois fois axe principal, TV deux fois.
    resultat = calculer(list("AAADACD"))

    assert resultat.scores["EVSS"] == resultat.scores["TV"] == 9
    assert resultat.principal == "EVSS"


def test_puis_laxe_principal_de_la_question_1_sil_est_ex_aequo() -> None:
    # TV et GI : 7 points et deux fois principal chacun ; la question 1 désignait TV.
    resultat = calculer(list("AAAAAAA"))

    assert resultat.scores["TV"] == resultat.scores["GI"] == 7
    assert (resultat.principal, resultat.autres) == ("TV", ("GI", "SE"))


def test_enfin_lordre_officiel_des_axes() -> None:
    # EVSS et LM : 8 points, deux fois principal ; la question 1 désignait TV, qui n'est pas ex æquo.
    resultat = calculer(list("AAABCCC"))

    assert resultat.scores["EVSS"] == resultat.scores["LM"] == 8
    assert (resultat.principal, resultat.autres) == ("EVSS", ("LM", "TV"))


def test_il_faut_sept_reponses() -> None:
    with pytest.raises(ValueError):
        calculer(list("AAAAA"))


# API des parties (spec 032) ---------------------------------------------------------------------------------


def connecter(client: TestClient | Navigateur, identifiant: str = "ama") -> None:
    client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})


@pytest.fixture
def ama(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    eleve = creer_eleve("ama", "Ama")
    connecter(client)
    return eleve


def jouer(client: TestClient, lettres: str = "AAAAAAB") -> dict[str, Any]:
    """Une partie entière : démarrage, 7 réponses, fin."""
    partie = client.post(PARTIES).json()
    for numero, lettre in enumerate(lettres, start=1):
        client.put(f"{PARTIES}/{partie['id']}/reponses/{numero}", json={"lettre": lettre})
    return client.post(f"{PARTIES}/{partie['id']}/fin").json()


def test_un_eleve_actif_recoit_les_7_questions_sans_les_axes(client: TestClient, ama: Utilisateur) -> None:
    corps = client.get(ETAT).json()

    assert [q["numero"] for q in corps["questions"]] == [1, 2, 3, 4, 5, 6, 7]
    premiere = corps["questions"][0]["reponses"][0]
    assert premiere == {"id": "A", "libelle": "Réaliser une vidéo ou interviewer des élèves."}
    assert (corps["limite"], corps["utilisees"], corps["restantes"]) == (3, 0, 3)
    assert corps["en_cours"] is None
    assert corps["historique"] == []


def test_consulter_le_jeu_ne_coute_rien(client: TestClient, ama: Utilisateur, en_base: Callable[..., Any]) -> None:
    client.get(ETAT)
    client.get(ETAT)

    assert en_base(lambda db: db.scalar(select(func.count()).select_from(PartieQuelAxe))) == 0


def test_commencer_cree_la_partie_1(client: TestClient, ama: Utilisateur) -> None:
    reponse = client.post(PARTIES)

    assert reponse.status_code == 201
    assert reponse.json()["numero"] == 1
    assert reponse.json()["reponses"] == [None] * 7
    etat = client.get(ETAT).json()
    assert (etat["utilisees"], etat["restantes"]) == (1, 2)
    assert etat["en_cours"]["id"] == reponse.json()["id"]


def test_commencer_avec_une_partie_en_cours_la_reprend(client: TestClient, ama: Utilisateur) -> None:
    premiere = client.post(PARTIES).json()

    reprise = client.post(PARTIES)

    assert reprise.status_code == 200
    assert reprise.json()["id"] == premiere["id"]
    assert client.get(ETAT).json()["utilisees"] == 1


def test_une_partie_interrompue_se_reprend_sur_un_autre_appareil(client: TestClient, ama: Utilisateur) -> None:
    partie = client.post(PARTIES).json()
    for numero, lettre in enumerate("ABC", start=1):
        client.put(f"{PARTIES}/{partie['id']}/reponses/{numero}", json={"lettre": lettre})

    autre = Navigateur(client)
    connecter(autre)
    etat = autre.get(ETAT).json()

    assert etat["en_cours"]["id"] == partie["id"]
    assert etat["en_cours"]["reponses"] == ["A", "B", "C", None, None, None, None]
    assert etat["utilisees"] == 1


def test_changer_une_reponse_avant_la_fin_change_le_resultat(client: TestClient, ama: Utilisateur) -> None:
    partie = client.post(PARTIES).json()
    for numero, lettre in enumerate("AAAAAAB", start=1):
        client.put(f"{PARTIES}/{partie['id']}/reponses/{numero}", json={"lettre": lettre})
    # Sans changement, TV ; en remplaçant les réponses 1, 3 et 5, l'élève penche vers le sport.
    for numero in (1, 3, 5):
        client.put(f"{PARTIES}/{partie['id']}/reponses/{numero}", json={"lettre": "B" if numero != 5 else "A"})
    client.put(f"{PARTIES}/{partie['id']}/reponses/2", json={"lettre": "D"})

    fin = client.post(f"{PARTIES}/{partie['id']}/fin").json()

    attendu = calculer(list("BDBAAAB"))
    assert fin["resultat"] == {"principal": attendu.principal, "autres": list(attendu.autres)}
    assert fin["resultat"]["principal"] != "TV"


def test_une_partie_ne_se_termine_quavec_7_reponses(client: TestClient, ama: Utilisateur) -> None:
    partie = client.post(PARTIES).json()
    for numero in range(1, 7):
        client.put(f"{PARTIES}/{partie['id']}/reponses/{numero}", json={"lettre": "A"})

    reponse = client.post(f"{PARTIES}/{partie['id']}/fin")

    assert reponse.status_code == 400
    assert reponse.json()["detail"] == "Réponds aux 7 questions pour voir ton résultat."


def test_une_partie_terminee_est_figee(client: TestClient, ama: Utilisateur) -> None:
    fin = jouer(client)

    assert client.put(f"{PARTIES}/{fin['id']}/reponses/1", json={"lettre": "D"}).status_code == 409
    # Terminer à nouveau renvoie le même résultat.
    assert client.post(f"{PARTIES}/{fin['id']}/fin").json()["resultat"] == fin["resultat"]


def test_une_partie_terminee_ne_rapporte_rien(
    client: TestClient, ama: Utilisateur, en_base: Callable[..., Any]
) -> None:
    avant = en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints)))

    fin = jouer(client)

    assert fin["resultat"] == {"principal": "TV", "autres": ["SE", "GI"]}
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints))) == avant


def test_trois_parties_puis_plus_aucune(client: TestClient, ama: Utilisateur) -> None:
    for numero, lettres in enumerate(("AAAAAAB", "AAADACD", "AAABCCC"), start=1):
        assert jouer(client, lettres)["numero"] == numero

    refus = client.post(PARTIES)

    assert refus.status_code == 403
    assert refus.json()["detail"].startswith("Tu as utilisé tes 3 participations !")
    etat = client.get(ETAT).json()
    assert (etat["utilisees"], etat["restantes"]) == (3, 0)
    assert [p["numero"] for p in etat["historique"]] == [3, 2, 1]
    assert [p["resultat"]["principal"] for p in etat["historique"]] == ["EVSS", "EVSS", "TV"]
    for partie in etat["historique"]:
        assert client.get(f"{PARTIES}/{partie['id']}").status_code == 200


def test_la_troisieme_partie_en_cours_peut_toujours_se_terminer(client: TestClient, ama: Utilisateur) -> None:
    jouer(client)
    jouer(client)
    troisieme = client.post(PARTIES).json()

    assert client.post(PARTIES).json()["id"] == troisieme["id"]
    for numero in range(1, 8):
        client.put(f"{PARTIES}/{troisieme['id']}/reponses/{numero}", json={"lettre": "A"})
    assert client.post(f"{PARTIES}/{troisieme['id']}/fin").json()["resultat"]["principal"] == "TV"


def test_deux_demarrages_simultanes_ne_creent_quune_partie(ama: Utilisateur, en_base: Callable[..., Any]) -> None:
    eleve = en_base(lambda db: db.get(Utilisateur, ama.id))

    async def demarrer() -> int:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            partie, _ = await parties_quel_axe.commencer(db, eleve)
            return partie.numero

    async def scenario() -> list[int]:
        return await asyncio.gather(*(demarrer() for _ in range(4)))

    assert asyncio.run(scenario()) == [1, 1, 1, 1]
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(PartieQuelAxe))) == 1


def test_des_demarrages_simultanes_apres_deux_parties_ne_depassent_pas_3(
    client: TestClient, ama: Utilisateur, en_base: Callable[..., Any]
) -> None:
    jouer(client)
    jouer(client)
    eleve = en_base(lambda db: db.get(Utilisateur, ama.id))

    async def demarrer() -> int:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            partie, _ = await parties_quel_axe.commencer(db, eleve)
            return partie.numero

    async def scenario() -> list[int]:
        return await asyncio.gather(*(demarrer() for _ in range(4)))

    assert asyncio.run(scenario()) == [3, 3, 3, 3]
    numeros = en_base(lambda db: db.scalars(select(PartieQuelAxe.numero).order_by(PartieQuelAxe.numero)))
    assert list(numeros) == [1, 2, 3]


def test_la_partie_dun_autre_eleve_est_introuvable(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> None:
    creer_eleve("ama", "Ama")
    creer_eleve("kofi", "Kofi")
    connecter(client, "kofi")
    partie_de_kofi = client.post(PARTIES).json()

    autre = Navigateur(client)
    connecter(autre, "ama")

    assert autre.get(f"{PARTIES}/{partie_de_kofi['id']}").status_code == 404
    assert autre.put(f"{PARTIES}/{partie_de_kofi['id']}/reponses/1", json={"lettre": "A"}).status_code == 404
    assert autre.post(f"{PARTIES}/{partie_de_kofi['id']}/fin").status_code == 404


@pytest.mark.parametrize(
    ("numero", "corps"),
    [(0, {"lettre": "A"}), (8, {"lettre": "A"}), (1, {"lettre": "E"}), (1, {"lettre": "A", "eleve_id": "x"})],
)
def test_une_reponse_invalide_est_refusee(
    client: TestClient, ama: Utilisateur, numero: int, corps: dict[str, str]
) -> None:
    partie = client.post(PARTIES).json()

    assert client.put(f"{PARTIES}/{partie['id']}/reponses/{numero}", json=corps).status_code == 422


def test_un_visiteur_doit_se_connecter(client: TestClient) -> None:
    partie = "01a1c198-1a6a-71ca-a1f9-c617be84bea4"
    assert client.get(ETAT).status_code == 401
    assert client.post(PARTIES).status_code == 401
    assert client.get(f"{PARTIES}/{partie}").status_code == 401
    assert client.put(f"{PARTIES}/{partie}/reponses/1", json={"lettre": "A"}).status_code == 401
    assert client.post(f"{PARTIES}/{partie}/fin").status_code == 401


def test_une_partie_inexistante_est_introuvable(client: TestClient, ama: Utilisateur) -> None:
    partie = "01a1c198-1a6a-71ca-a1f9-c617be84bea4"
    assert client.get(f"{PARTIES}/{partie}").status_code == 404
    assert client.put(f"{PARTIES}/{partie}/reponses/1", json={"lettre": "A"}).status_code == 404
    assert client.post(f"{PARTIES}/{partie}/fin").status_code == 404


def test_un_encadreur_na_pas_acces(client: TestClient, creer_encadreur: Callable[..., Utilisateur]) -> None:
    creer_encadreur("prof")
    connecter(client, "prof")

    reponse = client.get(ETAT)

    assert reponse.status_code == 403
    assert reponse.json()["detail"] == "Ce jeu est réservé aux élèves inscrits."
    assert client.post(PARTIES).status_code == 403


def test_un_collaborateur_na_pas_acces(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur("chef", super_admin=True, double_auth=True)
    connecter_admin(client, "chef")

    assert client.get(ETAT).status_code == 403
    assert client.post(PARTIES).status_code == 403


def test_un_eleve_suspendu_na_plus_acces_et_sa_partie_reste_en_letat(
    client: TestClient, ama: Utilisateur, en_base: Callable[..., Any]
) -> None:
    partie = client.post(PARTIES).json()
    client.put(f"{PARTIES}/{partie['id']}/reponses/1", json={"lettre": "B"})
    en_base(
        lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == ama.id).values(statut=StatutCompte.suspendu))
    )

    # Une session d'un compte non actif ne vaut plus rien : l'API répond 401, comme pour une session révoquée.
    assert client.get(ETAT).status_code == 401
    assert client.post(PARTIES).status_code == 401
    assert client.get(f"{PARTIES}/{partie['id']}").status_code == 401
    assert client.put(f"{PARTIES}/{partie['id']}/reponses/2", json={"lettre": "A"}).status_code == 401
    assert client.post(f"{PARTIES}/{partie['id']}/fin").status_code == 401
    enregistree = en_base(lambda db: db.get(PartieQuelAxe, UUID(partie["id"])))
    assert enregistree.reponses == ["B", None, None, None, None, None, None]
    assert enregistree.terminee_le is None


def test_les_parties_sont_effacees_avec_le_compte(
    client: TestClient, ama: Utilisateur, en_base: Callable[..., Any]
) -> None:
    jouer(client)

    en_base(lambda db: db.execute(delete(Utilisateur).where(Utilisateur.id == ama.id)))

    assert en_base(lambda db: db.scalar(select(func.count()).select_from(PartieQuelAxe))) == 0
