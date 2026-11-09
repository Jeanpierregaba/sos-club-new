"""La banque de quiz (spec 027) : préparée par le gestionnaire pédagogique, publiée par un autre collaborateur qui
nomme le validateur médical ; aucun accès pour les élèves, encadreurs et présidents, même par l'API."""

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.models import JournalAudit
from app.comptes.models import Utilisateur
from app.notifications.models import Notification
from app.quiz import banque
from app.quiz.models import EtatQuiz, ParametresQuiz, QuestionQuiz, Quiz
from app.quiz.schemas_banque import Approbation
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin, moteur_test
from tests.quiz import Horloge, bon_choix, connecter, creer_quiz, figer_horloge, gains, regler, tentatives

BANQUE = "/api/admin/quiz"
PREPARATION = {("quiz", "consulter"), ("quiz", "creer"), ("quiz", "modifier"), ("quiz", "soumettre")}
PUBLICATION = {("quiz", "consulter"), ("quiz", "approuver"), ("quiz", "depublier")}
APPROBATION = {"validateur_nom": "Dr Afi Mensah", "validateur_qualite": "Médecin de santé publique"}


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_collaborateur("pedago", droits=PREPARATION)
    connecter_admin(client, "pedago")
    return utilisateur


@pytest.fixture
def publieur(client: TestClient, creer_collaborateur: Callable[..., Utilisateur]) -> Navigateur:
    creer_collaborateur("publieur", droits=PUBLICATION, double_auth=True)
    navigateur = Navigateur(client)
    from tests.conftest import code_totp

    corps = navigateur.post(
        "/api/comptes/connexion", json={"identifiant": "publieur", "mot_de_passe": MOT_DE_PASSE}
    ).json()
    navigateur.post("/api/comptes/connexion/code", json={"jeton": corps["jeton"], "code": code_totp()})
    return navigateur


def axe(en_base: Callable[..., Any]) -> str:
    from app.referentiel.models import Axe

    return en_base(lambda db: db.scalar(select(Axe.code).order_by(Axe.code).limit(1)))


def question(i: int = 1) -> dict[str, Any]:
    return {"enonce": f"Question {i} ?", "choix": [f"Juste {i}", f"Faux {i}"], "bonne_reponse": 0}


def quiz_pret(client: Any, en_base: Callable[..., Any], questions: int = 15) -> dict[str, Any]:
    corps = client.post(BANQUE, json={"titre": "Hygiène des mains", "axe_code": axe(en_base)}).json()
    for i in range(questions):
        corps = client.post(f"{BANQUE}/{corps['id']}/questions", json=question(i + 1)).json()
    return corps


def soumis(client: Any, en_base: Callable[..., Any]) -> dict[str, Any]:
    corps = quiz_pret(client, en_base)
    reponse = client.post(f"{BANQUE}/{corps['id']}/soumettre")
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def journal(en_base: Callable[..., Any]) -> list[str]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(JournalAudit.action).where(JournalAudit.action.like("quiz_%")).order_by(JournalAudit.id)
            )
        ).all()
    )


# Préparer ---------------------------------------------------------------------------------------------------------


def test_le_gestionnaire_prepare_et_soumet_un_quiz(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = quiz_pret(client, en_base)

    assert corps["etat"] == "brouillon"
    assert corps["questions_actives"] == 15
    assert corps["questions"][0]["bonne_reponse"] == 0
    assert corps["contributeur"] is True

    reponse = client.post(f"{BANQUE}/{corps['id']}/soumettre")

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "soumis"
    assert journal(en_base)[0] == "quiz_cree"
    assert journal(en_base)[-1] == "quiz_soumis"


def test_un_quiz_sous_le_nombre_requis_ne_se_soumet_pas(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = quiz_pret(client, en_base, questions=14)

    reponse = client.post(f"{BANQUE}/{corps['id']}/soumettre")

    assert reponse.status_code == 422
    assert "15" in reponse.json()["detail"]


@pytest.mark.parametrize(
    "entree",
    [
        {"enonce": "Un seul choix ?", "choix": ["Seul"], "bonne_reponse": 0},
        {"enonce": "Cinq choix ?", "choix": ["a", "b", "c", "d", "e"], "bonne_reponse": 0},
        {"enonce": "Hors limites ?", "choix": ["a", "b"], "bonne_reponse": 2},
        {"enonce": "Doublon ?", "choix": ["Oui", "oui"], "bonne_reponse": 0},
        {"enonce": "Deux bonnes ?", "choix": ["a", "b"], "bonne_reponse": [0, 1]},
        {"enonce": "", "choix": ["a", "b"], "bonne_reponse": 0},
        {"enonce": "x" * 301, "choix": ["a", "b"], "bonne_reponse": 0},
    ],
)
def test_une_question_invalide_est_refusee(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], entree: dict[str, Any]
) -> None:
    corps = client.post(BANQUE, json={"titre": "Quiz", "axe_code": axe(en_base)}).json()

    assert client.post(f"{BANQUE}/{corps['id']}/questions", json=entree).status_code == 422


def test_un_quiz_soumis_ne_se_modifie_plus(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = soumis(client, en_base)
    premiere = corps["questions"][0]["id"]

    assert client.put(f"{BANQUE}/{corps['id']}/questions/{premiere}", json=question(99)).status_code == 409
    assert client.post(f"{BANQUE}/{corps['id']}/questions", json=question(99)).status_code == 409
    assert client.delete(f"{BANQUE}/{corps['id']}/questions/{premiere}").status_code == 409
    assert client.put(f"{BANQUE}/{corps['id']}", json={"titre": "Autre", "axe_code": axe(en_base)}).status_code == 409


def test_le_gestionnaire_reprend_un_quiz_soumis_en_brouillon(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = soumis(client, en_base)

    reponse = client.post(f"{BANQUE}/{corps['id']}/reprendre")

    assert reponse.json()["etat"] == "brouillon"
    assert client.post(f"{BANQUE}/{corps['id']}/questions", json=question(16)).status_code == 201


def test_retirer_une_question_deja_jouee_la_desactive(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    corps = quiz_pret(client, en_base)
    client.post(f"{BANQUE}/{corps['id']}/essais")
    jouee = corps["questions"][0]["id"]
    # L'essai en cours a tiré toutes les questions ; la première est donc référencée.
    reponse = client.delete(f"{BANQUE}/{corps['id']}/questions/{jouee}")

    assert reponse.status_code == 200
    [ligne] = [q for q in reponse.json()["questions"] if q["id"] == jouee]
    assert ligne["active"] is False
    assert reponse.json()["questions_actives"] == 14


def test_modifier_une_question_deja_jouee_la_remplace_sans_toucher_la_partie(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    corps = quiz_pret(client, en_base)
    essai = client.post(f"{BANQUE}/{corps['id']}/essais").json()
    # La question envoyée en premier à l'essai : c'est elle qu'on modifie.
    [jouee] = [q for q in corps["questions"] if q["enonce"] == essai["question"]["enonce"]]

    reponse = client.put(f"{BANQUE}/{corps['id']}/questions/{jouee['id']}", json=question(99))

    assert reponse.status_code == 200
    questions = reponse.json()["questions"]
    [ancienne] = [q for q in questions if q["id"] == jouee["id"]]
    [nouvelle] = [q for q in questions if q["enonce"] == question(99)["enonce"]]
    assert ancienne["active"] is False and ancienne["enonce"] == jouee["enonce"]
    assert nouvelle["active"] is True and nouvelle["id"] != jouee["id"]
    assert reponse.json()["questions_actives"] == 15
    # La partie en cours garde la question telle qu'elle a été envoyée, jugée sur sa bonne réponse d'origine.
    etat = client.get(f"{BANQUE}/essais/{essai['tentative_id']}").json()
    assert etat["question"] == essai["question"] | {"restant_ms": etat["question"]["restant_ms"]}
    while etat["question"] is not None:
        etat = client.post(
            f"{BANQUE}/essais/{essai['tentative_id']}/reponses",
            json={"rang": etat["question"]["rang"], "choix": bon_choix(etat["question"])},
        ).json()
    assert etat["resultat"]["score"] == 15


def test_une_question_deja_remplacee_ne_se_modifie_plus(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    corps = quiz_pret(client, en_base)
    client.post(f"{BANQUE}/{corps['id']}/essais")
    ancienne = corps["questions"][0]["id"]
    client.put(f"{BANQUE}/{corps['id']}/questions/{ancienne}", json=question(98))

    reponse = client.put(f"{BANQUE}/{corps['id']}/questions/{ancienne}", json=question(99))

    assert reponse.status_code == 409
    detail = client.get(f"{BANQUE}/{corps['id']}").json()
    assert detail["questions_actives"] == 15
    # À la même place, la remplaçante active vient avant l'ancienne désactivée.
    premiere, deuxieme = detail["questions"][:2]
    assert premiere["active"] is True and premiere["enonce"] == question(98)["enonce"]
    assert deuxieme["id"] == ancienne and deuxieme["active"] is False


def test_modifier_une_question_jamais_jouee_la_reecrit(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = quiz_pret(client, en_base, questions=2)
    premiere = corps["questions"][0]["id"]

    reponse = client.put(f"{BANQUE}/{corps['id']}/questions/{premiere}", json=question(99))

    [ligne] = [q for q in reponse.json()["questions"] if q["id"] == premiere]
    assert ligne["enonce"] == question(99)["enonce"]
    assert len(reponse.json()["questions"]) == 2


def test_retirer_une_question_jamais_jouee_lefface(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = quiz_pret(client, en_base, questions=2)

    reponse = client.delete(f"{BANQUE}/{corps['id']}/questions/{corps['questions'][0]['id']}")

    assert len(reponse.json()["questions"]) == 1


# Publier ----------------------------------------------------------------------------------------------------------


def test_un_autre_collaborateur_publie_en_nommant_le_validateur(
    client: TestClient,
    gestionnaire: Utilisateur,
    publieur: Navigateur,
    en_base: Callable[..., Any],
) -> None:
    corps = soumis(client, en_base)

    reponse = publieur.post(f"{BANQUE}/{corps['id']}/approuver", json=APPROBATION)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "publie"
    assert reponse.json()["validateur_nom"] == "Dr Afi Mensah"
    [avis] = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == gestionnaire.id))
    ).all()
    assert "publié" in avis.titre
    assert journal(en_base)[-1] == "quiz_approuve"


def test_un_contributeur_ne_publie_pas_son_propre_quiz(
    client: TestClient, creer_collaborateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur("chef", super_admin=True, double_auth=True)
    connecter_admin(client, "chef")
    corps = soumis(client, en_base)

    reponse = client.post(f"{BANQUE}/{corps['id']}/approuver", json=APPROBATION)

    assert reponse.status_code == 403
    assert en_base(lambda db: db.get(Quiz, corps["id"])).etat is EtatQuiz.soumis


def test_celui_qui_a_seulement_modifie_une_question_ne_publie_pas_non_plus(
    client: TestClient,
    gestionnaire: Utilisateur,
    creer_collaborateur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    corps = quiz_pret(client, en_base)
    creer_collaborateur("relecteur", droits=PREPARATION | PUBLICATION, double_auth=True)
    relecteur = Navigateur(client)
    from tests.conftest import code_totp

    jeton = relecteur.post(
        "/api/comptes/connexion", json={"identifiant": "relecteur", "mot_de_passe": MOT_DE_PASSE}
    ).json()["jeton"]
    relecteur.post("/api/comptes/connexion/code", json={"jeton": jeton, "code": code_totp()})
    relecteur.put(f"{BANQUE}/{corps['id']}/questions/{corps['questions'][0]['id']}", json=question(42))
    client.post(f"{BANQUE}/{corps['id']}/soumettre")

    assert relecteur.post(f"{BANQUE}/{corps['id']}/approuver", json=APPROBATION).status_code == 403


@pytest.mark.parametrize(
    "entree",
    [
        {"validateur_nom": "", "validateur_qualite": "Médecin"},
        {"validateur_nom": "Dr Mensah", "validateur_qualite": " "},
        {"validateur_nom": "Dr Mensah"},
        {},
    ],
)
def test_une_approbation_sans_validateur_medical_est_refusee(
    client: TestClient,
    gestionnaire: Utilisateur,
    publieur: Navigateur,
    en_base: Callable[..., Any],
    entree: dict[str, Any],
) -> None:
    corps = soumis(client, en_base)

    assert publieur.post(f"{BANQUE}/{corps['id']}/approuver", json=entree).status_code == 422


def test_un_refus_renvoie_le_quiz_en_brouillon_avec_son_motif(
    client: TestClient, gestionnaire: Utilisateur, publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    corps = soumis(client, en_base)

    reponse = publieur.post(f"{BANQUE}/{corps['id']}/refuser", json={"motif": "La question 3 est ambiguë."})

    assert reponse.json()["etat"] == "brouillon"
    assert reponse.json()["motif"] == "La question 3 est ambiguë."
    [avis] = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.utilisateur_id == gestionnaire.id))
    ).all()
    assert avis.message == "La question 3 est ambiguë."


def test_un_quiz_depublie_disparait_mais_garde_ses_tentatives_et_ses_points(
    client: TestClient,
    gestionnaire: Utilisateur,
    publieur: Navigateur,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    heure: Horloge,
) -> None:
    corps = soumis(client, en_base)
    publieur.post(f"{BANQUE}/{corps['id']}/approuver", json=APPROBATION)
    eleve = creer_eleve("ama")
    joueur = Navigateur(client)
    joueur.post("/api/comptes/connexion", json={"identifiant": "ama", "mot_de_passe": MOT_DE_PASSE})
    etat = joueur.post(f"/api/quiz/{corps['id']}/tentatives").json()
    while etat["question"] is not None:
        etat = joueur.post(
            f"/api/quiz/tentatives/{etat['tentative_id']}/reponses",
            json={"rang": etat["question"]["rang"], "choix": bon_choix(etat["question"])},
        ).json()

    reponse = publieur.post(f"{BANQUE}/{corps['id']}/depublier", json={"motif": "Recommandation à mettre à jour."})

    assert reponse.json()["etat"] == "depublie"
    assert joueur.get("/api/quiz").json()["quiz"] == []
    assert joueur.post(f"/api/quiz/{corps['id']}/tentatives").status_code == 404
    assert len(gains(en_base, eleve.id)) == 1
    assert len(tentatives(en_base)) == 1


def test_deux_approbations_simultanees_une_seule_passe(
    client: TestClient,
    gestionnaire: Utilisateur,
    creer_collaborateur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    corps = soumis(client, en_base)
    premier = creer_collaborateur("pub1", droits=PUBLICATION, double_auth=True)
    second = creer_collaborateur("pub2", droits=PUBLICATION, double_auth=True)

    async def decider(qui: Utilisateur) -> str:
        from app.admin.models import Collaborateur

        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == qui.id))
            acces = Acces(utilisateur=qui, collaborateur=collaborateur)  # type: ignore[arg-type]
            try:
                await banque.approuver(db, acces, corps["id"], Approbation(**APPROBATION), "test")
                await asyncio.sleep(0.2)
                await db.commit()
                return "ok"
            except banque.EtatInvalide:
                return "conflit"

    async def scenario() -> list[str]:
        return await asyncio.gather(decider(premier), decider(second))

    assert sorted(asyncio.run(scenario())) == ["conflit", "ok"]


# Droits -------------------------------------------------------------------------------------------------------------


ROUTES = [
    ("get", BANQUE, None),
    ("post", BANQUE, {"titre": "Quiz", "axe_code": "x"}),
    ("put", f"{BANQUE}/{{id}}", {"titre": "Quiz", "axe_code": "x"}),
    ("post", f"{BANQUE}/{{id}}/questions", question()),
    ("post", f"{BANQUE}/{{id}}/soumettre", None),
    ("post", f"{BANQUE}/{{id}}/approuver", APPROBATION),
    ("post", f"{BANQUE}/{{id}}/depublier", {"motif": "Pour voir."}),
    (
        "put",
        f"{BANQUE}/parametres",
        {"nb_questions": 5, "temps_ms": 5000, "tolerance_ms": 0, "seuil": 3, "tentatives_par_jour": 3},
    ),
    ("post", f"{BANQUE}/{{id}}/essais", None),
]


@pytest.mark.parametrize("role", ["eleve", "president", "encadreur"])
@pytest.mark.parametrize(("methode", "chemin", "corps"), ROUTES)
def test_ni_eleve_ni_president_ni_encadreur_ne_touchent_a_la_banque(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    role: str,
    methode: str,
    chemin: str,
    corps: Any,
) -> None:
    quiz = creer_quiz(en_base, etat=EtatQuiz.soumis)
    if role == "encadreur":
        creer_encadreur("kodjo")
        connecter(client, "kodjo")
    else:
        eleve = creer_eleve("ama")
        if role == "president":
            creer_club(eleve)
        connecter(client, "ama")
    avant = en_base(lambda db: db.get(Quiz, quiz.id))

    reponse = getattr(client, methode)(chemin.format(id=quiz.id), **({"json": corps} if corps else {}))

    assert reponse.status_code == 403
    apres = en_base(lambda db: db.get(Quiz, quiz.id))
    assert (apres.etat, apres.version) == (avant.etat, avant.version)
    assert len(en_base(lambda db: db.scalars(select(ParametresQuiz))).all()) <= 1


@pytest.mark.parametrize(
    ("droits", "methode", "chemin", "corps"),
    [
        ({("quiz", "consulter")}, "post", BANQUE, {"titre": "Quiz", "axe_code": "x"}),
        ({("quiz", "consulter"), ("quiz", "creer")}, "post", f"{BANQUE}/{{id}}/soumettre", None),
        (PREPARATION, "post", f"{BANQUE}/{{id}}/approuver", APPROBATION),
        (PREPARATION, "post", f"{BANQUE}/{{id}}/depublier", {"motif": "Pour voir."}),
        ({("moderation", "consulter")}, "get", BANQUE, None),
    ],
)
def test_un_collaborateur_sans_le_droit_est_refuse(
    client: TestClient,
    creer_collaborateur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    droits: set[tuple[str, str]],
    methode: str,
    chemin: str,
    corps: Any,
) -> None:
    quiz = creer_quiz(en_base, etat=EtatQuiz.soumis)
    creer_collaborateur("limite", droits=droits, double_auth=True)
    connecter_admin(client, "limite")

    reponse = getattr(client, methode)(chemin.format(id=quiz.id), **({"json": corps} if corps else {}))

    assert reponse.status_code == 403
    assert "acces_refuse" in [a for a in en_base(lambda db: db.scalars(select(JournalAudit.action))).all()]


def test_publier_exige_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    quiz = creer_quiz(en_base, etat=EtatQuiz.soumis)
    creer_collaborateur("sans2fa", droits=PUBLICATION)
    connecter_admin(client, "sans2fa")

    reponse = client.post(f"{BANQUE}/{quiz.id}/approuver", json=APPROBATION)

    assert reponse.status_code == 403
    assert "double authentification" in reponse.json()["detail"]


# Paramètres ---------------------------------------------------------------------------------------------------------


def test_changer_les_parametres_ajoute_une_version(publieur: Navigateur, en_base: Callable[..., Any]) -> None:
    entree = {"nb_questions": 10, "temps_ms": 8000, "tolerance_ms": 2000, "seuil": 8, "tentatives_par_jour": 5}

    reponse = publieur.put(f"{BANQUE}/parametres", json=entree)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["version"] == 2
    historique = publieur.get(f"{BANQUE}/parametres").json()
    assert historique["en_cours"]["nb_questions"] == 10
    assert [v["version"] for v in historique["versions"]] == [2, 1]
    assert journal(en_base)[-1] == "quiz_parametres_modifies"


@pytest.mark.parametrize(
    "entree",
    [
        {"nb_questions": 10, "temps_ms": 5000, "tolerance_ms": 2000, "seuil": 11, "tentatives_par_jour": 5},
        {"nb_questions": 10, "temps_ms": 0, "tolerance_ms": 2000, "seuil": 8, "tentatives_par_jour": 5},
        {"nb_questions": 10, "temps_ms": 5000, "tolerance_ms": 2000, "seuil": 8, "tentatives_par_jour": 0},
        {"nb_questions": 0, "temps_ms": 5000, "tolerance_ms": 2000, "seuil": 0, "tentatives_par_jour": 5},
    ],
)
def test_des_parametres_incoherents_sont_refuses(publieur: Navigateur, entree: dict[str, int]) -> None:
    assert publieur.put(f"{BANQUE}/parametres", json=entree).status_code == 422


def test_relever_le_nombre_de_questions_au_dessus_dune_reserve_publiee_est_refuse(
    publieur: Navigateur, en_base: Callable[..., Any]
) -> None:
    creer_quiz(en_base, questions=15, titre="Court")
    creer_quiz(en_base, questions=20, titre="Long")
    entree = {"nb_questions": 18, "temps_ms": 5000, "tolerance_ms": 2000, "seuil": 14, "tentatives_par_jour": 5}

    reponse = publieur.put(f"{BANQUE}/parametres", json=entree)

    assert reponse.status_code == 422
    assert "Court" in reponse.json()["detail"]
    assert "Long" not in reponse.json()["detail"]


def test_preparer_des_quiz_ne_suffit_pas_pour_changer_les_parametres(
    client: TestClient, gestionnaire: Utilisateur
) -> None:
    entree = {"nb_questions": 10, "temps_ms": 8000, "tolerance_ms": 2000, "seuil": 8, "tentatives_par_jour": 5}

    assert client.put(f"{BANQUE}/parametres", json=entree).status_code == 403
    assert client.get(f"{BANQUE}/parametres").status_code == 200


# Mode test ----------------------------------------------------------------------------------------------------------


def test_un_essai_abandonne_depuis_un_jour_est_efface_au_prochain_essai(
    client: TestClient,
    gestionnaire: Utilisateur,
    publieur: Navigateur,
    en_base: Callable[..., Any],
    heure: Horloge,
) -> None:
    corps = quiz_pret(client, en_base)
    oublie = client.post(f"{BANQUE}/{corps['id']}/essais").json()
    heure.avancer(23 * 3600)
    recent = publieur.post(f"{BANQUE}/{corps['id']}/essais").json()
    assert {str(t.id) for t in tentatives(en_base)} == {oublie["tentative_id"], recent["tentative_id"]}
    heure.avancer(2 * 3600)

    dernier = publieur.post(f"{BANQUE}/{corps['id']}/essais").json()

    # L'essai oublié du gestionnaire est effacé ; celui du publieur est remplacé par le nouveau.
    assert {str(t.id) for t in tentatives(en_base)} == {dernier["tentative_id"]}


def test_un_essai_ne_laisse_ni_tentative_ni_plafond_ni_points(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    corps = quiz_pret(client, en_base)
    regler(en_base, tentatives_par_jour=1)

    for _ in range(2):
        etat = client.post(f"{BANQUE}/{corps['id']}/essais").json()
        while etat["question"] is not None:
            etat = client.post(
                f"{BANQUE}/essais/{etat['tentative_id']}/reponses",
                json={"rang": etat["question"]["rang"], "choix": bon_choix(etat["question"])},
            ).json()
        assert etat["resultat"] == {"score": 15, "total": 15, "seuil": 12, "reussie": True, "points": 0}

    assert tentatives(en_base) == []
    assert gains(en_base, gestionnaire.id) == []
    assert client.get(f"{BANQUE}/essais/{etat['tentative_id']}").status_code == 404


def test_un_essai_ne_se_rejoue_pas_par_les_routes_du_joueur(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    corps = quiz_pret(client, en_base)
    etat = client.post(f"{BANQUE}/{corps['id']}/essais").json()

    assert client.get(f"/api/quiz/tentatives/{etat['tentative_id']}").status_code == 403


def test_un_essai_respecte_le_chrono(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    corps = quiz_pret(client, en_base)
    etat = client.post(f"{BANQUE}/{corps['id']}/essais").json()
    heure.avancer(8)

    suite = client.get(f"{BANQUE}/essais/{etat['tentative_id']}").json()

    assert suite["question"]["rang"] == 2


def test_un_essai_sur_une_reserve_incomplete_est_refuse(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    corps = quiz_pret(client, en_base, questions=3)

    assert client.post(f"{BANQUE}/{corps['id']}/essais").status_code == 409


def test_les_questions_dun_quiz_supprime_restent_introuvables(
    client: TestClient, gestionnaire: Utilisateur, en_base: Callable[..., Any]
) -> None:
    autre = creer_quiz(en_base, etat=EtatQuiz.brouillon)
    corps = quiz_pret(client, en_base, questions=1)
    etrangere = en_base(lambda db: db.scalar(select(QuestionQuiz.id).where(QuestionQuiz.quiz_id == autre.id)))

    assert client.delete(f"{BANQUE}/{corps['id']}/questions/{etrangere}").status_code == 404
