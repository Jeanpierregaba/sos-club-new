"""Les 100 quiz Jeux sur 4 niveaux, les étoiles et la carte Gold (spec 034, lot 2) : partie critique, écrite avant
le code (docs/TESTING.md)."""

import itertools
from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.jeux.models import EtoileObtenue
from app.points.models import MouvementPoints
from app.quiz import parametres
from app.quiz.models import EtatQuiz, EtatTentative, Quiz, TentativeQuiz
from tests.quiz import DEBUT, Horloge, connecter, figer_horloge, jouer
from tests.quiz import creer_quiz as creer_quiz_brut

pytestmark = pytest.mark.usefixtures("annuaire")
CATALOGUE = "/api/jeux/quiz"
_numeros = itertools.count(1)


@pytest.fixture(autouse=True)
def numerotation() -> None:
    global _numeros
    _numeros = itertools.count(1)


def creer_quiz(en_base: Callable[..., Any], **champs: Any) -> Quiz:
    """Un quiz du parcours officiel : numéroté, comme les 100 défis (seuls ceux-là comptent pour les étoiles)."""
    champs.setdefault("numero", next(_numeros))
    return creer_quiz_brut(en_base, **champs)


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


def affilier(en_base: Callable[..., Any], eleve: Utilisateur) -> UUID:
    """L'élève confirmé dans le club actif de son établissement."""

    async def faire(db: AsyncSession) -> UUID:
        profil = await db.get(Eleve, eleve.id)
        assert profil is not None
        club = await activation.club_de(db, profil.etablissement_id)
        await db.execute(update(Club).where(Club.id == club.id).values(etat=EtatClub.actif))
        db.add(Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.active))
        return club.id

    return en_base(faire)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama")
    connecter(client, "ama")
    return utilisateur


def deja_reussi(en_base: Callable[..., Any], joueur_id: UUID, quiz: Quiz) -> None:
    """Une réussite ancienne, écrite directement : les parcours complets se testent sans jouer chaque partie."""

    async def inserer(db: AsyncSession) -> None:
        p = await parametres.en_cours(db)
        db.add(
            TentativeQuiz(
                quiz_id=quiz.id, joueur_id=joueur_id, parametres_id=p.id, etat=EtatTentative.terminee,
                jour=DEBUT.date(), commencee_le=DEBUT, derniere_activite=DEBUT, terminee_le=DEBUT,
                score=p.nb_questions, reussie=True,
            )
        )  # fmt: skip

    en_base(inserer)


def gains(en_base: Callable[..., Any], joueur_id: UUID) -> dict[str, MouvementPoints]:
    lignes = en_base(lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == joueur_id)))
    return {ligne.action: ligne for ligne in lignes}


def etoiles(en_base: Callable[..., Any], joueur_id: UUID) -> list[str]:
    return sorted(
        en_base(lambda db: db.scalars(select(EtoileObtenue.niveau).where(EtoileObtenue.utilisateur_id == joueur_id)))
    )


# Le gain d'un quiz dépend de son niveau ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("niveau", "montant"), [("debutant", 50), ("intermediaire", 100), ("avance", 150), ("expert", 200)]
)
def test_un_quiz_reussi_une_premiere_fois_rapporte_le_montant_de_son_niveau(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge, niveau: str, montant: int
) -> None:
    club_id = affilier(en_base, eleve)
    quiz = creer_quiz(en_base, niveau=niveau)
    creer_quiz(en_base, niveau=niveau, titre="Un autre quiz du niveau")

    fin = jouer(client, quiz, justes=15)

    assert fin["resultat"]["points"] == montant
    gain = gains(en_base, eleve.id)[f"eleve.quiz_{niveau}"]
    assert (gain.montant, gain.club_id, gain.demi_points_club) == (montant, club_id, montant)


def test_un_quiz_deja_recompense_rejoue_ne_rapporte_rien(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base, niveau="expert")
    creer_quiz(en_base, niveau="expert", titre="Un autre")
    jouer(client, quiz, justes=15)

    fin = jouer(client, quiz, justes=15)

    assert fin["resultat"]["points"] == 0
    assert len(gains(en_base, eleve.id)) == 1


def test_un_eleve_non_affilie_gagne_ses_points_sans_club(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base, niveau="debutant")
    creer_quiz(en_base, niveau="debutant", titre="Un autre")

    jouer(client, quiz, justes=15)

    gain = gains(en_base, eleve.id)["eleve.quiz_debutant"]
    assert gain.montant == 50 and gain.club_id is None


def test_un_quiz_jeux_sans_niveau_rapporte_le_montant_debutant(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base)

    jouer(client, quiz, justes=15)

    assert gains(en_base, eleve.id)["eleve.quiz_debutant"].montant == 50
    assert etoiles(en_base, eleve.id) == []


# Les étoiles ------------------------------------------------------------------------------------------------------

BONUS = {"debutant": 500, "intermediaire": 1000, "avance": 1500, "expert": 3000}


@pytest.mark.parametrize("niveau", list(BONUS))
def test_le_dernier_quiz_d_un_niveau_debloque_son_etoile(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge, niveau: str
) -> None:
    club_id = affilier(en_base, eleve)
    anciens = [creer_quiz(en_base, niveau=niveau, titre=f"Quiz {i}") for i in range(2)]
    for quiz in anciens:
        deja_reussi(en_base, eleve.id, quiz)
    dernier = creer_quiz(en_base, niveau=niveau, titre="Le dernier")

    jouer(client, dernier, justes=15)

    assert etoiles(en_base, eleve.id) == [niveau]
    bonus = gains(en_base, eleve.id)[f"eleve.etoile_{niveau}"]
    assert (bonus.montant, bonus.club_id, bonus.demi_points_club) == (BONUS[niveau], club_id, BONUS[niveau])


def test_pas_d_etoile_tant_qu_un_quiz_du_niveau_n_est_pas_reussi(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base, niveau="debutant")
    creer_quiz(en_base, niveau="debutant", titre="Pas encore réussi")

    jouer(client, quiz, justes=15)

    assert etoiles(en_base, eleve.id) == []


def test_un_quiz_rate_ne_debloque_pas_l_etoile(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base, niveau="debutant")

    jouer(client, quiz, justes=3)

    assert etoiles(en_base, eleve.id) == []


def test_un_quiz_depublie_ne_compte_plus_pour_l_etoile(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    creer_quiz(en_base, niveau="avance", etat=EtatQuiz.depublie, titre="Retiré")
    quiz = creer_quiz(en_base, niveau="avance")

    jouer(client, quiz, justes=15)

    assert etoiles(en_base, eleve.id) == ["avance"]


def test_une_etoile_n_est_donnee_qu_une_fois(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base, niveau="expert")
    jouer(client, quiz, justes=15)
    jouer(client, quiz, justes=15)

    assert etoiles(en_base, eleve.id) == ["expert"]
    assert [a for a in gains(en_base, eleve.id) if a.startswith("eleve.etoile")] == ["eleve.etoile_expert"]


def test_un_encadreur_ne_gagne_ni_etoile_ni_points_d_eleve(
    client: TestClient, en_base: Callable[..., Any], creer_encadreur: Callable[..., Utilisateur], heure: Horloge
) -> None:
    encadreur = creer_encadreur()
    connecter(client, encadreur.identifiant)
    quiz = creer_quiz(en_base, niveau="debutant")

    jouer(client, quiz, justes=15)

    assert etoiles(en_base, encadreur.id) == []
    assert not [a for a in gains(en_base, encadreur.id) if a.startswith("eleve.")]


def ancien(en_base: Callable[..., Any], eleve: Utilisateur) -> None:
    from app.points.service import maintenant

    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(ancien_eleve_le=maintenant())
        )
    )


def test_un_ancien_eleve_ne_gagne_ni_etoile_ni_points(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    ancien(en_base, eleve)
    quiz = creer_quiz(en_base, niveau="debutant")

    jouer(client, quiz, justes=15)

    assert etoiles(en_base, eleve.id) == []
    assert gains(en_base, eleve.id) == {}


def test_depublier_un_quiz_ne_donne_pas_l_etoile_a_un_ancien_eleve(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur
) -> None:
    from app.jeux import progression
    from app.quiz.models import NiveauQuiz

    reussi = creer_quiz(en_base, niveau="debutant")
    creer_quiz(en_base, niveau="debutant", titre="Retiré", etat=EtatQuiz.brouillon)
    deja_reussi(en_base, eleve.id, reussi)
    ancien(en_base, eleve)

    assert en_base(lambda db: progression.reverifier_niveau(db, NiveauQuiz.debutant)) == 0
    assert etoiles(en_base, eleve.id) == []


# Progression, sous-totaux et carte Gold ------------------------------------------------------------------------


def test_la_progression_separe_points_des_quiz_et_points_des_etoiles(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base, niveau="intermediaire")
    autre = creer_quiz(en_base, niveau="debutant", titre="Débutant")
    jouer(client, quiz, justes=15)

    progression = client.get(CATALOGUE).json()["progression"]

    assert progression["quiz_reussis"] == 1
    assert progression["points_quiz"] == 100
    assert progression["points_etoiles"] == 1000
    assert progression["total"] == 1100
    assert progression["gold"] is False
    niveaux = {n["niveau"]: n for n in progression["niveaux"]}
    assert niveaux["intermediaire"] == {"niveau": "intermediaire", "reussis": 1, "total": 1, "etoile": True}
    assert niveaux["debutant"] == {"niveau": "debutant", "reussis": 0, "total": 1, "etoile": False}
    assert str(quiz.id) in progression["reussis"] and str(autre.id) not in progression["reussis"]


def test_les_quatre_etoiles_donnent_la_carte_gold(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    for niveau in ("debutant", "intermediaire", "avance"):
        jouer(client, creer_quiz(en_base, niveau=niveau, titre=niveau), justes=15)
    assert client.get(CATALOGUE).json()["progression"]["gold"] is False

    jouer(client, creer_quiz(en_base, niveau="expert", titre="expert"), justes=15)

    progression = client.get(CATALOGUE).json()["progression"]
    assert progression["gold"] is True
    assert progression["points_quiz"] == 50 + 100 + 150 + 200
    assert progression["points_etoiles"] == 6000


def test_le_catalogue_donne_le_numero_et_le_niveau_de_chaque_quiz(
    client: TestClient, en_base: Callable[..., Any], heure: Horloge
) -> None:
    async def numeroter(db: AsyncSession) -> None:
        quiz = await db.scalar(select(Quiz))
        assert quiz is not None
        quiz.numero = 7

    creer_quiz(en_base, niveau="avance")
    en_base(numeroter)

    corps = client.get(CATALOGUE).json()

    assert [(q["numero"], q["niveau"]) for q in corps["quiz"]] == [(7, "avance")]
    assert corps["progression"] is None


def test_l_equipe_voit_les_eleves_gold(
    client: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
    heure: Horloge,
) -> None:
    from tests.conftest import connecter_admin

    eleve = creer_eleve("kofi", affiche="Kofi des Plateaux")

    async def quatre(db: AsyncSession) -> None:
        for niveau in ("debutant", "intermediaire", "avance", "expert"):
            db.add(EtoileObtenue(utilisateur_id=eleve.id, niveau=niveau))

    en_base(quatre)
    creer_collaborateur("gold", droits={("tableau_de_bord", "consulter"), ("points", "consulter")})
    connecter_admin(client, "gold")

    corps = client.get("/api/admin/jeux/gold").json()

    assert [e["pseudonyme"] for e in corps] == ["Kofi des Plateaux"]
    assert "nom" not in corps[0] and "prenom" not in corps[0]


def test_l_equipe_regle_le_niveau_d_un_quiz_jeux_dans_la_banque(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    from app.referentiel.models import Axe
    from tests.conftest import connecter_admin

    creer_collaborateur("pedago", droits={("quiz", "consulter"), ("quiz", "creer"), ("quiz", "modifier")})
    connecter_admin(client, "pedago")
    axe = en_base(lambda db: db.scalar(select(Axe.code).order_by(Axe.code).limit(1)))

    cree = client.post("/api/admin/quiz", json={"titre": "Quiz expert", "axe_code": axe, "niveau": "expert"})
    assert cree.status_code == 201, cree.text
    quiz_id = cree.json()["id"]
    modifie = client.put(
        f"/api/admin/quiz/{quiz_id}", json={"titre": "Quiz expert", "axe_code": axe, "niveau": "avance"}
    )

    assert modifie.status_code in (200, 204), modifie.text
    detail = client.get(f"/api/admin/quiz/{quiz_id}").json()
    assert (detail["niveau"], detail["numero"]) == ("avance", None)


def test_l_eleve_lit_sa_progression_pour_sa_carte_de_membre(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    jouer(client, creer_quiz(en_base, niveau="expert"), justes=15)

    progression = client.get(f"{CATALOGUE}/progression").json()

    assert (progression["quiz_reussis"], progression["points_etoiles"]) == (1, 3000)


def test_la_progression_est_reservee_aux_eleves(client: TestClient) -> None:
    assert client.get(f"{CATALOGUE}/progression").status_code == 401


# Corrections de la relecture du lot 2 -------------------------------------------------------------------------------


def test_un_quiz_sans_numero_ne_compte_pas_pour_l_etoile(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, heure: Horloge
) -> None:
    creer_quiz(en_base, niveau="avance", numero=None, titre="Hors parcours")
    quiz = creer_quiz(en_base, niveau="avance")

    jouer(client, quiz, justes=15)

    assert etoiles(en_base, eleve.id) == ["avance"]


def test_depublier_un_quiz_donne_l_etoile_a_qui_a_reussi_tous_les_autres(
    client: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
) -> None:
    from tests.conftest import MOT_DE_PASSE, Navigateur, code_totp

    eleve = creer_eleve("kofi")
    reussi = creer_quiz(en_base, niveau="expert")
    manque = creer_quiz(en_base, niveau="expert", titre="Pas encore joué")
    deja_reussi(en_base, eleve.id, reussi)
    creer_collaborateur("publieur", droits={("quiz", "consulter"), ("quiz", "depublier")}, double_auth=True)
    navigateur = Navigateur(client)
    jeton = navigateur.post(
        "/api/comptes/connexion", json={"identifiant": "publieur", "mot_de_passe": MOT_DE_PASSE}
    ).json()["jeton"]
    navigateur.post("/api/comptes/connexion/code", json={"jeton": jeton, "code": code_totp()})

    reponse = navigateur.post(f"/api/admin/quiz/{manque.id}/depublier", json={"motif": "Question à revoir."})

    assert reponse.status_code in (200, 204), reponse.text
    assert etoiles(en_base, eleve.id) == ["expert"]
    assert "eleve.etoile_expert" in gains(en_base, eleve.id)


def test_deux_reussites_simultanees_des_deux_derniers_quiz_donnent_l_etoile(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    import asyncio

    from app.jeux import progression
    from app.quiz.models import NiveauQuiz
    from tests.conftest import moteur_test

    eleve = creer_eleve("kofi")
    a, b = creer_quiz(en_base, niveau="debutant"), creer_quiz(en_base, niveau="debutant", titre="B")

    async def reussir(quiz: Quiz) -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            p = await parametres.en_cours(db)
            db.add(
                TentativeQuiz(
                    quiz_id=quiz.id, joueur_id=eleve.id, parametres_id=p.id, etat=EtatTentative.terminee,
                    jour=DEBUT.date(), commencee_le=DEBUT, derniere_activite=DEBUT, terminee_le=DEBUT,
                    score=15, reussie=True,
                )
            )  # fmt: skip
            await db.flush()
            await progression.verifier_etoile(db, eleve.id, NiveauQuiz.debutant)
            await asyncio.sleep(0.2)
            await db.commit()

    async def scenario() -> None:
        await asyncio.gather(reussir(a), reussir(b))

    asyncio.run(scenario())

    assert etoiles(en_base, eleve.id) == ["debutant"]


def test_les_gains_d_avant_les_niveaux_ne_comptent_pas_dans_les_points_des_quiz(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur
) -> None:
    from app.points import service

    en_base(lambda db: service.crediter(db, "eleve.quiz", eleve.id, "quiz:ancien"))

    assert client.get(f"{CATALOGUE}/progression").json()["points_quiz"] == 0


def test_un_responsable_de_dre_ne_voit_que_les_eleves_gold_de_sa_dre(
    client: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
) -> None:
    from tests.conftest import connecter_admin

    du_golfe = creer_eleve("ama", affiche="Ama du Golfe", dre="grand-lome")
    de_kara = creer_eleve("kossi", affiche="Kossi de Kara", dre="kara")

    async def quatre(db: AsyncSession) -> None:
        for eleve in (du_golfe, de_kara):
            for niveau in ("debutant", "intermediaire", "avance", "expert"):
                db.add(EtoileObtenue(utilisateur_id=eleve.id, niveau=niveau))

    en_base(quatre)
    creer_collaborateur("dre", droits={("tableau_de_bord", "consulter"), ("points", "consulter")}, perimetre_dre="kara")
    connecter_admin(client, "dre")

    assert [e["pseudonyme"] for e in client.get("/api/admin/jeux/gold").json()] == ["Kossi de Kara"]


def test_corriger_le_titre_d_un_quiz_ne_change_pas_son_niveau(
    client: TestClient, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any]
) -> None:
    from app.referentiel.models import Axe
    from tests.conftest import connecter_admin

    creer_collaborateur("pedago", droits={("quiz", "consulter"), ("quiz", "creer"), ("quiz", "modifier")})
    connecter_admin(client, "pedago")
    axe = en_base(lambda db: db.scalar(select(Axe.code).order_by(Axe.code).limit(1)))
    quiz_id = client.post("/api/admin/quiz", json={"titre": "Quiz", "axe_code": axe, "niveau": "expert"}).json()["id"]

    client.put(f"/api/admin/quiz/{quiz_id}", json={"titre": "Quiz corrigé", "axe_code": axe})

    assert client.get(f"/api/admin/quiz/{quiz_id}").json()["niveau"] == "expert"
