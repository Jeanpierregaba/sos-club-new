"""La partie de quiz (spec 027, ADR-0004) : le serveur envoie une question à la fois, sans sa réponse, mesure le
temps et calcule seul le résultat. Écrits avant le code (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from app.quiz import partie
from app.quiz.models import EtatQuiz, EtatTentative, Quiz, ReponseQuiz
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin, moteur_test
from tests.quiz import (
    QUIZ,
    Horloge,
    bon_choix,
    connecter,
    creer_quiz,
    figer_horloge,
    gains,
    jouer,
    lancer,
    mauvais_choix,
    regler,
    repondre,
    tentatives,
)

CLES_INTERDITES = {"bonne_reponse", "explication", "correcte", "ordre_choix", "question_id"}


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama")
    connecter(client, "ama")
    return utilisateur


@pytest.fixture
def quiz(en_base: Callable[..., Any]) -> Quiz:
    return creer_quiz(en_base)


def cles(valeur: Any) -> set[str]:
    if isinstance(valeur, dict):
        return set(valeur) | {c for v in valeur.values() for c in cles(v)}
    if isinstance(valeur, list):
        return {c for v in valeur for c in cles(v)}
    return set()


def textes(valeur: Any) -> list[str]:
    if isinstance(valeur, dict):
        return [t for v in valeur.values() for t in textes(v)]
    if isinstance(valeur, list):
        return [t for v in valeur for t in textes(v)]
    return [valeur] if isinstance(valeur, str) else []


# Réponses jamais exposées -------------------------------------------------------------------------------------


def test_aucune_reponse_au_joueur_ne_contient_la_bonne_reponse(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    corps = [client.get(QUIZ).json()]
    etat = lancer(client, quiz)
    corps.append(etat)
    while etat["question"] is not None:
        corps.append(client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").json())
        etat = repondre(client, etat, bon_choix(etat["question"]))
        corps.append(etat)
    corps.append(client.get(QUIZ).json())

    for c in corps:
        assert not cles(c) & CLES_INTERDITES
        assert not any("Explication secrète" in t for t in textes(c))


def test_une_question_arrive_seule_avec_ses_choix_melanges(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    etat = lancer(client, quiz)

    assert etat["total"] == 15
    assert etat["question"]["rang"] == 1
    assert etat["question"]["temps_ms"] == 5000
    assert etat["resultat"] is None
    assert sorted(t.split(" ")[0] for t in etat["question"]["choix"]) == ["Faux", "Faux", "Juste"]


def test_la_reponse_suivante_ne_dit_pas_si_la_precedente_etait_juste(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    etat = lancer(client, quiz)
    juste = repondre(client, etat, bon_choix(etat["question"]))
    faux = repondre(client, juste, mauvais_choix(juste["question"]))

    assert set(juste) == set(faux)
    assert juste["resultat"] is None and faux["resultat"] is None


# Le temps ----------------------------------------------------------------------------------------------------


def _premiere_a(client: TestClient, quiz: Quiz, heure: Horloge, secondes: float) -> dict[str, Any]:
    etat = lancer(client, quiz)
    heure.avancer(secondes)
    etat = repondre(client, etat, bon_choix(etat["question"]))
    while etat["question"] is not None:
        etat = repondre(client, etat, bon_choix(etat["question"]))
    return etat["resultat"]


def test_une_reponse_a_6_9_secondes_compte(client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge) -> None:
    assert _premiere_a(client, quiz, heure, 6.9)["score"] == 15


def test_une_reponse_a_7_1_secondes_est_ratee(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    assert _premiere_a(client, quiz, heure, 7.1)["score"] == 14


def test_le_delai_court_a_partir_de_lenvoi_de_chaque_question(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    etat = lancer(client, quiz)
    for _ in range(15):
        heure.avancer(6.5)
        etat = repondre(client, etat, bon_choix(etat["question"]))

    assert etat["resultat"]["score"] == 15


def test_recharger_ne_rend_pas_de_temps(client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge) -> None:
    etat = lancer(client, quiz)
    heure.avancer(4)
    reprise = client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").json()

    assert reprise["question"]["rang"] == 1
    assert reprise["question"]["restant_ms"] == 1000
    heure.avancer(3.5)
    suite = repondre(client, reprise, bon_choix(reprise["question"]))
    assert suite["question"]["rang"] == 2
    # La première est ratée : il ne reste que 14 bonnes réponses possibles.
    while suite["question"] is not None:
        suite = repondre(client, suite, bon_choix(suite["question"]))
    assert suite["resultat"]["score"] == 14


def test_apres_une_coupure_le_joueur_reprend_a_la_question_suivante(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    etat = lancer(client, quiz)
    heure.avancer(60)

    reprise = client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").json()

    assert reprise["question"]["rang"] == 2
    assert reprise["question"]["restant_ms"] == 5000


def test_une_tentative_inactive_10_minutes_est_close_avec_le_score_acquis(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = lancer(client, quiz)
    for _ in range(12):
        etat = repondre(client, etat, bon_choix(etat["question"]))
    heure.avancer(11 * 60)

    fin = client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").json()

    assert fin["question"] is None
    assert fin["resultat"] == {"score": 12, "total": 15, "seuil": 12, "reussie": True, "points": 50}
    assert len(gains(en_base, eleve.id)) == 1


def test_la_liste_propose_de_reprendre_la_partie_en_cours(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    assert client.get(QUIZ).json()["quiz"][0]["tentative_en_cours"] is None
    etat = lancer(client, quiz)
    heure.avancer(5 * 60)

    [ligne] = client.get(QUIZ).json()["quiz"]

    assert ligne["tentative_en_cours"] == etat["tentative_id"]


def test_une_reussite_abandonnee_est_creditee_quand_le_joueur_revoit_la_liste(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = lancer(client, quiz)
    for _ in range(12):
        etat = repondre(client, etat, bon_choix(etat["question"]))
    heure.avancer(11 * 60)

    [ligne] = client.get(QUIZ).json()["quiz"]

    assert ligne["tentative_en_cours"] is None
    assert ligne["reussi"] is True
    assert ligne["meilleur_score"] == 12
    assert len(gains(en_base, eleve.id)) == 1
    [tentative] = tentatives(en_base)
    assert tentative.etat is EtatTentative.terminee


# Le résultat ------------------------------------------------------------------------------------------------


def test_onze_bonnes_reponses_sur_quinze_ne_suffisent_pas(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    resultat = jouer(client, quiz, 11)["resultat"]

    assert resultat == {"score": 11, "total": 15, "seuil": 12, "reussie": False, "points": 0}
    assert gains(en_base, eleve.id) == []


def test_douze_bonnes_reponses_reussissent_et_rapportent_50_points(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    resultat = jouer(client, quiz, 12)["resultat"]

    assert resultat == {"score": 12, "total": 15, "seuil": 12, "reussie": True, "points": 50}
    [ligne] = gains(en_base, eleve.id)
    assert (ligne.action, ligne.montant, ligne.cle) == ("eleve.quiz", 50, f"quiz:{quiz.id}:{eleve.id}")


def test_une_seconde_reussite_ne_rapporte_rien(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    jouer(client, quiz, 15)
    resultat = jouer(client, quiz, 15)["resultat"]

    assert resultat["reussie"] is True
    assert resultat["points"] == 0
    assert len(gains(en_base, eleve.id)) == 1


def test_un_encadreur_joue_sans_points(
    client: TestClient,
    creer_encadreur: Callable[..., Utilisateur],
    quiz: Quiz,
    heure: Horloge,
    en_base: Callable[..., Any],
) -> None:
    encadreur = creer_encadreur("kodjo")
    connecter(client, "kodjo")

    resultat = jouer(client, quiz, 15)["resultat"]

    assert resultat["reussie"] is True
    assert resultat["points"] == 0
    assert gains(en_base, encadreur.id) == []


def test_un_quiz_depublie_pendant_la_partie_se_termine_sans_points(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = lancer(client, quiz)
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == quiz.id).values(etat=EtatQuiz.depublie)))
    while etat["question"] is not None:
        etat = repondre(client, etat, bon_choix(etat["question"]))

    assert etat["resultat"]["reussie"] is True
    assert etat["resultat"]["points"] == 0
    assert gains(en_base, eleve.id) == []


def test_les_points_dun_quiz_depublie_restent_acquis(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    jouer(client, quiz, 15)
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == quiz.id).values(etat=EtatQuiz.depublie)))

    assert len(gains(en_base, eleve.id)) == 1
    assert len(tentatives(en_base)) == 1


# Doubles envois et concurrence --------------------------------------------------------------------------------


def test_la_meme_reponse_envoyee_deux_fois_ne_compte_quune_fois(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    etat = lancer(client, quiz)
    premiere = repondre(client, etat, mauvais_choix(etat["question"]))
    # Le même rang renvoyé, cette fois juste : déjà tranché, rien ne change.
    seconde = repondre(client, etat, bon_choix(etat["question"]))

    assert seconde["question"]["rang"] == premiere["question"]["rang"] == 2
    while seconde["question"] is not None:
        seconde = repondre(client, seconde, bon_choix(seconde["question"]))
    assert seconde["resultat"]["score"] == 14


def _tentative_avec_derniere_question(client: TestClient, quiz: Quiz) -> dict[str, Any]:
    etat = lancer(client, quiz)
    for _ in range(14):
        etat = repondre(client, etat, bon_choix(etat["question"]))
    return etat


def test_deux_fins_simultanees_ne_creditent_quune_fois(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = _tentative_avec_derniere_question(client, quiz)
    joueur = en_base(lambda db: db.get(Utilisateur, eleve.id))

    async def une_requete() -> dict[str, Any]:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            resultat = await partie.repondre(db, joueur, etat["tentative_id"], 15, bon_choix(etat["question"]))
            await asyncio.sleep(0.2)
            await db.commit()
            return resultat.model_dump()

    async def scenario() -> list[dict[str, Any]]:
        return await asyncio.gather(une_requete(), une_requete())

    fins = asyncio.run(scenario())

    assert [f["resultat"]["score"] for f in fins] == [15, 15]
    # Les deux voient la même tentative terminée, et le même crédit.
    assert [f["resultat"]["points"] for f in fins] == [50, 50]
    assert len(gains(en_base, eleve.id)) == 1


def test_relancer_pendant_la_derniere_reponse_ne_bloque_pas_et_credite_une_fois(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    # La dernière réponse clôt et crédite (verrou de la tentative, puis écriture au registre) pendant qu'un
    # lancement tient le joueur et attend la même tentative : aucun interblocage, un seul crédit.
    etat = _tentative_avec_derniere_question(client, quiz)
    joueur = en_base(lambda db: db.get(Utilisateur, eleve.id))

    async def repondre_a_la_derniere() -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            await partie.repondre(db, joueur, etat["tentative_id"], 15, bon_choix(etat["question"]))
            await asyncio.sleep(0.2)
            await db.commit()

    async def relancer() -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            await asyncio.sleep(0.05)
            await partie.lancer(db, joueur, quiz.id)
            await db.commit()

    async def scenario() -> None:
        await asyncio.wait_for(asyncio.gather(repondre_a_la_derniere(), relancer()), timeout=10)

    asyncio.run(scenario())

    assert len(gains(en_base, eleve.id)) == 1
    assert sorted(t.etat.value for t in tentatives(en_base)) == ["en_cours", "terminee"]


def test_deux_reponses_simultanees_a_la_meme_question_ne_comptent_quune_fois(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = lancer(client, quiz)
    joueur = en_base(lambda db: db.get(Utilisateur, eleve.id))

    async def une_requete(choix: int) -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            await partie.repondre(db, joueur, etat["tentative_id"], 1, choix)
            await asyncio.sleep(0.2)
            await db.commit()

    async def scenario() -> None:
        await asyncio.gather(une_requete(bon_choix(etat["question"])), une_requete(mauvais_choix(etat["question"])))

    asyncio.run(scenario())

    reponses = en_base(lambda db: db.scalars(select(ReponseQuiz).where(ReponseQuiz.repondue_le.is_not(None)))).all()
    assert len(reponses) == 1
    assert client.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").json()["question"]["rang"] == 2


# Plafond, paramètres, nouvelle tentative -------------------------------------------------------------------------


def test_au_plafond_du_jour_une_nouvelle_tentative_est_refusee(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    regler(en_base, tentatives_par_jour=2)
    jouer(client, quiz, 0)
    jouer(client, quiz, 0)

    reponse = client.post(f"{QUIZ}/{quiz.id}/tentatives")

    assert reponse.status_code == 429
    assert len(tentatives(en_base)) == 2
    heure.avancer(24 * 3600)
    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 201


def test_le_plafond_compte_par_quiz(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    regler(en_base, tentatives_par_jour=1)
    autre = creer_quiz(en_base, titre="Autre quiz")
    jouer(client, quiz, 0)

    assert client.post(f"{QUIZ}/{autre.id}/tentatives").status_code == 201


def test_une_tentative_garde_la_version_des_parametres_de_son_debut(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = lancer(client, quiz)
    regler(en_base, seuil=15, temps_ms=1000, tolerance_ms=0)
    heure.avancer(6)
    n = 0
    while etat["question"] is not None:
        etat = repondre(client, etat, bon_choix(etat["question"]) if n < 12 else mauvais_choix(etat["question"]))
        n += 1

    assert etat["resultat"]["seuil"] == 12
    assert etat["resultat"]["score"] == 12
    assert etat["resultat"]["reussie"] is True


def test_un_tirage_prend_le_nombre_de_questions_du_parametre_dans_la_reserve(
    client: TestClient, eleve: Utilisateur, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    grand = creer_quiz(en_base, questions=20)
    regler(en_base, nb_questions=10, seuil=8)

    etat = lancer(client, grand)

    assert etat["total"] == 10


def test_lancer_une_tentative_clot_celle_en_cours(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    premiere = lancer(client, quiz)
    for _ in range(3):
        premiere = repondre(client, premiere, bon_choix(premiere["question"]))
    seconde = lancer(client, quiz)

    ancienne = client.get(f"{QUIZ}/tentatives/{premiere['tentative_id']}").json()
    assert ancienne["question"] is None
    assert ancienne["resultat"]["score"] == 3
    assert seconde["question"]["rang"] == 1


# La liste des quiz --------------------------------------------------------------------------------------------


def test_la_liste_montre_les_quiz_publies_et_letat_du_joueur(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    for etat in (EtatQuiz.brouillon, EtatQuiz.soumis, EtatQuiz.depublie):
        creer_quiz(en_base, etat=etat, titre=f"Quiz {etat}")
    jouer(client, quiz, 9)
    jouer(client, quiz, 13)
    jouer(client, quiz, 10)

    [ligne] = client.get(QUIZ).json()["quiz"]

    assert ligne["id"] == str(quiz.id)
    assert ligne["reussi"] is True
    assert ligne["meilleur_score"] == 13
    assert ligne["tentatives_restantes"] == 7
    assert ligne["contenu_de_test"] is True


def test_la_liste_se_filtre_par_axe(
    client: TestClient, eleve: Utilisateur, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    from app.referentiel.models import Axe

    premier, second = en_base(lambda db: db.scalars(select(Axe.code).order_by(Axe.code).limit(2))).all()
    creer_quiz(en_base, titre="Premier", axe=premier)
    creer_quiz(en_base, titre="Second", axe=second)

    titres = [q["titre"] for q in client.get(QUIZ, params={"axe": second}).json()["quiz"]]

    assert titres == ["Second"]


# Accès --------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("statut", [StatutCompte.suspendu, StatutCompte.revoque])
def test_un_eleve_inactif_ne_joue_pas(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    quiz: Quiz,
    en_base: Callable[..., Any],
    statut: StatutCompte,
) -> None:
    eleve = creer_eleve("kofi")
    connecter(client, "kofi")
    en_base(lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=statut)))

    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code in (401, 403)
    assert client.get(QUIZ).status_code in (401, 403)


def test_un_encadreur_non_verifie_ne_joue_pas(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur], quiz: Quiz
) -> None:
    creer_encadreur("kodjo", etat=EtatVerification.en_attente)
    connecter(client, "kodjo")

    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 403


def test_un_visiteur_ne_joue_pas(client: TestClient, quiz: Quiz) -> None:
    assert client.get(QUIZ).status_code == 401
    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 401


def test_un_collaborateur_ne_joue_pas_hors_du_mode_test(
    client: TestClient, creer_collaborateur: Callable[..., Utilisateur], quiz: Quiz
) -> None:
    creer_collaborateur("chef", super_admin=True, double_auth=True)
    connecter_admin(client, "chef")

    assert client.post(f"{QUIZ}/{quiz.id}/tentatives").status_code == 403


@pytest.mark.parametrize("etat", [EtatQuiz.brouillon, EtatQuiz.soumis, EtatQuiz.depublie])
def test_un_quiz_non_publie_ne_se_lance_pas(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], etat: EtatQuiz
) -> None:
    autre = creer_quiz(en_base, etat=etat)

    assert client.post(f"{QUIZ}/{autre.id}/tentatives").status_code == 404


def test_la_tentative_dun_autre_joueur_est_introuvable(
    client: TestClient,
    eleve: Utilisateur,
    creer_eleve: Callable[..., Utilisateur],
    quiz: Quiz,
    heure: Horloge,
) -> None:
    etat = lancer(client, quiz)
    creer_eleve("kofi", affiche="Kofi des Plateaux")
    autre = Navigateur(client)
    autre.post("/api/comptes/connexion", json={"identifiant": "kofi", "mot_de_passe": MOT_DE_PASSE})

    assert autre.get(f"{QUIZ}/tentatives/{etat['tentative_id']}").status_code == 404
    assert (
        autre.post(f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses", json={"rang": 1, "choix": 0}).status_code
        == 404
    )


def test_une_reponse_a_une_question_future_est_introuvable(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge
) -> None:
    etat = lancer(client, quiz)

    reponse = client.post(f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses", json={"rang": 3, "choix": 0})

    assert reponse.status_code == 404


@pytest.mark.parametrize("choix", [-1, 3, 10])
def test_un_choix_hors_limites_est_refuse(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, choix: int
) -> None:
    etat = lancer(client, quiz)

    reponse = client.post(f"{QUIZ}/tentatives/{etat['tentative_id']}/reponses", json={"rang": 1, "choix": choix})

    assert reponse.status_code == 422


def test_un_eleve_suspendu_pendant_la_partie_ne_gagne_pas_de_points(
    client: TestClient, eleve: Utilisateur, quiz: Quiz, heure: Horloge, en_base: Callable[..., Any]
) -> None:
    etat = _tentative_avec_derniere_question(client, quiz)
    joueur = en_base(lambda db: db.get(Utilisateur, eleve.id))
    joueur.statut = StatutCompte.suspendu

    async def finir() -> dict[str, Any]:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            resultat = await partie.repondre(db, joueur, etat["tentative_id"], 15, bon_choix(etat["question"]))
            await db.commit()
            return resultat.model_dump()

    assert asyncio.run(finir())["resultat"]["points"] == 0
    assert gains(en_base, eleve.id) == []
    assert Role.eleve is joueur.role
