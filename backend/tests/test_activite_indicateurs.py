"""Page « Activité » (spec 051) : droits, indicateurs sur des données construites, période vide, export."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite import service
from app.activite.models import (
    EvenementActivite,
    TotalActiviteJour,
    TypeEvenement,
    VisiteursGroupeJour,
    VisiteursJour,
)
from app.admin.models import JournalAudit
from app.quiz import parametres
from app.quiz.models import EtatTentative, Quiz, TentativeQuiz
from tests.certification import acquerir, creer_parcours
from tests.conftest import connecter_admin
from tests.quiz import creer_quiz

AUJOURDHUI = date(2026, 11, 23)
BLOCS = ("audience", "inscription", "jeux", "certification", "contenus", "regions", "retention", "erreurs")
URL = "/api/admin/activite"
PERIODE = {"du": "2026-11-01", "au": "2026-11-23"}


@pytest.fixture(autouse=True)
def jour_fixe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "aujourdhui", lambda: AUJOURDHUI)


@pytest.fixture
def super_admin(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("chef", super_admin=True, double_auth=True)
    assert connecter_admin(client).status_code == 200
    return client


def lire(client: TestClient, bloc: str, **periode: str) -> dict[str, Any]:
    reponse = client.get(f"{URL}/{bloc}", params=periode or PERIODE)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def chiffre(bloc: dict[str, Any], cle: str) -> tuple[Any, Any]:
    trouve = next(c for c in bloc["chiffres"] if c["cle"] == cle)
    return trouve["valeur"], trouve["precedent"]


def tableau(bloc: dict[str, Any], cle: str) -> list[dict[str, Any]]:
    return next(t for t in bloc["tableaux"] if t["cle"] == cle)["lignes"]


def ajouter(en_base: Callable[..., Any], *lignes: Any) -> None:
    async def _ajouter(db: AsyncSession) -> None:
        db.add_all(lignes)

    en_base(_ajouter)


def vue(jour: date, visiteur: str, chemin: str = "/", **champs: Any) -> EvenementActivite:
    return EvenementActivite(
        jour=jour, cree_le=datetime.combine(jour, datetime.min.time(), UTC) + timedelta(hours=10),
        type=champs.pop("type_", TypeEvenement.page_vue), visiteur=visiteur, chemin=chemin, **champs,
    )  # fmt: skip


# Droits ----------------------------------------------------------------------------------------------------------


def test_reserve_au_super_administrateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> None:
    creer_collaborateur("analyste", droits={("tableau_de_bord", "consulter")}, double_auth=True)
    connecter_admin(client, "analyste")
    assert client.get(f"{URL}/audience").status_code == 403
    assert client.get(f"{URL}/audience/export.csv").status_code == 403


def test_un_visiteur_n_y_a_pas_acces(client: TestClient) -> None:
    assert client.get(f"{URL}/audience").status_code == 401


@pytest.mark.parametrize("bloc", BLOCS)
def test_une_periode_vide_ne_casse_aucun_bloc(super_admin: TestClient, bloc: str) -> None:
    resultat = lire(super_admin, bloc)
    assert resultat["bloc"] == bloc
    assert (resultat["precedent_du"], resultat["precedent_au"]) == ("2026-10-09", "2026-10-31")


@pytest.mark.parametrize(
    ("periode", "code"),
    [({"du": "2026-11-10", "au": "2026-11-01"}, 422), ({"du": "2025-01-01", "au": "2026-11-23"}, 422)],
)
def test_une_periode_invalide_est_refusee(super_admin: TestClient, periode: dict[str, str], code: int) -> None:
    assert super_admin.get(f"{URL}/audience", params=periode).status_code == code


def test_par_defaut_les_30_derniers_jours(super_admin: TestClient) -> None:
    resultat = super_admin.get(f"{URL}/audience").json()
    assert (resultat["du"], resultat["au"]) == ("2026-10-25", "2026-11-23")


# Audience --------------------------------------------------------------------------------------------------------


def test_audience_reunit_evenements_bruts_et_totaux(super_admin: TestClient, en_base: Callable[..., Any]) -> None:
    j1, j2 = date(2026, 11, 20), date(2026, 11, 21)
    ajouter(
        en_base,
        vue(j1, "a", "/jeux", provenance="facebook", appareil="telephone"),
        vue(j1, "a", "/quiz/$id", connecte=True),
        vue(j2, "a", "/jeux"),  # le lendemain, la même personne compte de nouveau
        vue(j2, "b", "/", provenance="direct", appareil="ordinateur"),
        vue(date(2026, 10, 20), "z", "/"),  # période précédente
        # Un jour sorti des 90 jours dans la période : seulement ses totaux.
        TotalActiviteJour(
            jour=date(2026, 11, 2), type=TypeEvenement.page_vue, chemin="/jeux", detail="", provenance="",
            appareil="", navigateur="", connecte=False, evenements=5,
        ),
        *[
            VisiteursGroupeJour(jour=date(2026, 11, 2), type=TypeEvenement.page_vue, dimensions=d, valeurs=v, visiteurs=2)
            for d, v in (("", ""), ("chemin", "/jeux"), ("connecte", "false"), ("provenance", ""), ("appareil", ""),
                         ("navigateur", ""))
        ],
        VisiteursJour(jour=date(2026, 11, 2), visiteurs=2),
    )  # fmt: skip
    resultat = lire(super_admin, "audience")
    assert chiffre(resultat, "visiteurs") == (5, 1)
    assert chiffre(resultat, "pages_vues") == (9, 1)
    assert chiffre(resultat, "part_connectes")[0] == round(100 / 9, 1)
    assert tableau(resultat, "pages")[0] == {"chemin": "/jeux", "vues": 7, "visiteurs": 4}
    assert {ligne["libelle"]: ligne["visiteurs"] for ligne in tableau(resultat, "provenance")} == {
        "facebook": 1,
        "direct": 1,
    }
    serie = next(s for s in resultat["series"] if s["cle"] == "visiteurs")["points"]
    assert {p["jour"]: p["valeur"] for p in serie if p["valeur"]} == {"2026-11-02": 2, "2026-11-20": 1, "2026-11-21": 2}


# Inscription -----------------------------------------------------------------------------------------------------


def test_entonnoir_et_abandons(super_admin: TestClient, en_base: Callable[..., Any]) -> None:
    jour = date(2026, 11, 20)
    etape = TypeEvenement.etape_inscription
    ajouter(
        en_base,
        *[vue(jour, v, "/inscription", type_=etape, detail="eleve:ouvert") for v in "abcd"],
        *[vue(jour, v, "/inscription", type_=etape, detail="eleve:commence") for v in "ab"],
        vue(jour, "a", "/inscription", type_=etape, detail="eleve:envoye"),
        vue(jour, "a", "/inscription", type_=etape, detail="eleve:envoye"),
        vue(jour, "a", "/inscription", type_=etape, detail="eleve:refuse-doublon"),
        vue(jour, "a", "/inscription", type_=etape, detail="eleve:cree"),
        vue(jour, "c", "/", type_=TypeEvenement.clic_inscription, detail="accueil"),
    )
    resultat = lire(super_admin, "inscription")
    entonnoir = tableau(resultat, "entonnoir_eleve")
    assert [(e["visiteurs"], e["passage"], e["abandon"]) for e in entonnoir] == [
        (4, None, None),
        (2, 50.0, 50.0),
        (1, 50.0, 50.0),
        (1, 100.0, 0.0),
    ]
    assert tableau(resultat, "refus") == [{"profil": "Élèves", "motif": "refuse-doublon", "nombre": 1}]
    assert tableau(resultat, "clics") == [{"endroit": "accueil", "clics": 1, "visiteurs": 1}]
    assert chiffre(resultat, "conversion_eleves")[0] == 25.0


# Jeux et certification : les chiffres égalent ceux de la base ----------------------------------------------------


def partie(en_base: Callable[..., Any], quiz: Quiz, joueur: Any, quand: datetime, reussie: bool | None) -> None:
    async def inserer(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, quiz.parcours)
        db.add(
            TentativeQuiz(
                quiz_id=quiz.id, joueur_id=joueur.id, parametres_id=p.id,
                etat=EtatTentative.en_cours if reussie is None else EtatTentative.terminee,
                jour=quand.date(), commencee_le=quand, derniere_activite=quand,
                terminee_le=None if reussie is None else quand + timedelta(seconds=90), reussie=reussie,
            )
        )  # fmt: skip

    en_base(inserer)


@pytest.mark.usefixtures("annuaire")
def test_jeux_comptes_sur_les_parties(
    super_admin: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    quiz = creer_quiz(en_base, niveau="debutant", numero=1)
    eleve, autre = creer_utilisateur("aya"), creer_utilisateur("kofi")
    quand = datetime(2026, 11, 20, 15, tzinfo=UTC)
    partie(en_base, quiz, eleve, quand, True)
    partie(en_base, quiz, eleve, quand, False)
    partie(en_base, quiz, autre, quand, None)
    partie(en_base, quiz, autre, datetime(2026, 10, 20, tzinfo=UTC), True)  # période précédente
    resultat = lire(super_admin, "jeux")
    assert chiffre(resultat, "lancees") == (3, 1)
    assert chiffre(resultat, "reussies") == (1, 1)
    assert chiffre(resultat, "taux_reussite")[0] == 50.0
    assert chiffre(resultat, "abandons")[0] == round(100 / 3, 1)
    assert chiffre(resultat, "joueurs") == (2, 1)
    attendu = en_base(
        lambda db: db.scalar(
            select(func.count())
            .select_from(TentativeQuiz)
            .where(TentativeQuiz.commencee_le >= datetime(2026, 11, 1, tzinfo=UTC))
        )
    )
    assert attendu == 3
    assert tableau(resultat, "quiz")[0]["lancees"] == 3


@pytest.mark.usefixtures("annuaire")
def test_certification_entonnoir_des_places(
    super_admin: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    parcours = creer_parcours(en_base, places=range(1, 4))
    acquerir(en_base, creer_utilisateur("aya"), parcours, [1, 2, 3])
    acquerir(en_base, creer_utilisateur("kofi"), parcours, [1])
    partie(en_base, parcours[2], creer_utilisateur("ama"), datetime(2026, 11, 20, tzinfo=UTC), False)
    places = tableau(lire(super_admin, "certification"), "places")
    assert [p["candidats"] for p in places[:4]] == [2, 1, 1, 0]
    # Place 2 : la réussite d'Aya (le 9 novembre, en 0 s) et l'échec d'Ama (90 s).
    assert (places[1]["tentatives"], places[1]["echec"], places[1]["temps"]) == (2, 50.0, 45)


# Erreurs et recherches -------------------------------------------------------------------------------------------


def test_une_recherche_ne_s_affiche_qu_a_partir_de_3_visiteurs(
    super_admin: TestClient, en_base: Callable[..., Any]
) -> None:
    jour = date(2026, 11, 20)
    recherche = TypeEvenement.recherche
    ajouter(
        en_base,
        *[vue(jour, v, "/inscription", type_=recherche, detail="lycée de tsévié") for v in "abc"],
        *[vue(jour, v, "/inscription", type_=recherche, detail="kodjo") for v in "aa"],
        vue(jour, "a", "/ancienne-page", type_=TypeEvenement.erreur, detail="404"),
    )
    resultat = lire(super_admin, "erreurs")
    assert tableau(resultat, "recherches") == [{"recherche": "lycée de tsévié", "page": "/inscription", "visiteurs": 3}]
    assert tableau(resultat, "introuvables") == [{"chemin": "/ancienne-page", "vues": 1, "visiteurs": 1}]


# Export ----------------------------------------------------------------------------------------------------------


def test_l_export_ne_contient_que_des_totaux_et_est_journalise(
    super_admin: TestClient, en_base: Callable[..., Any]
) -> None:
    ajouter(en_base, vue(date(2026, 11, 20), "emprt0123456789a", "/jeux"))
    reponse = super_admin.get(f"{URL}/audience/export.csv", params=PERIODE)
    assert reponse.status_code == 200
    assert reponse.headers["content-type"].startswith("text/csv")
    assert "activite-audience-2026-11-01-2026-11-23.csv" in reponse.headers["content-disposition"]
    texte = reponse.content.decode("utf-8-sig")
    assert "Pages les plus vues" in texte and "/jeux;1;1" in texte
    assert "emprt0123456789a" not in texte
    actions = en_base(lambda db: db.scalars(select(JournalAudit.action)))
    assert "activite_exportee" in list(actions)


# Rétention, régions, contenus, erreurs du serveur ----------------------------------------------------------------


def test_retention_par_cohorte_sans_part_pour_une_semaine_pas_finie(
    super_admin: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    from app.activite.models import PresenceSemaine

    lundi = date(2026, 11, 2)
    inscription = datetime(2026, 11, 3, 9, tzinfo=UTC)
    aya = creer_utilisateur("aya", cree_le=inscription)
    creer_utilisateur("kofi", cree_le=inscription)
    ajouter(en_base, PresenceSemaine(utilisateur_id=aya.id, semaine=lundi + timedelta(weeks=1)))
    [cohorte] = tableau(lire(super_admin, "retention"), "cohortes")
    # La semaine + 4 (le 30 novembre) n'est pas encore finie le 23 : pas de part.
    assert cohorte == {"semaine": "2026-11-02", "inscrits": 2, "s1": 50.0, "s4": None}


def test_regions_par_dre(super_admin: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]) -> None:
    from app.comptes.models import Utilisateur

    ama = creer_eleve("ama", dre="grand-lome")

    async def inscrite_dans_la_periode(db: AsyncSession) -> None:
        (await db.get(Utilisateur, ama.id)).cree_le = datetime(2026, 11, 10, 9, tzinfo=UTC)

    en_base(inscrite_dans_la_periode)
    lignes = {ligne["dre"]: ligne for ligne in tableau(lire(super_admin, "regions"), "dre")}
    assert sum(int(ligne["inscrits"]) for ligne in lignes.values()) == 1
    assert len(lignes) > 1  # toutes les DRE actives, même sans activité


def test_contenus_par_document(super_admin: TestClient, en_base: Callable[..., Any]) -> None:
    from tests.bibliotheque import creer_ressource

    ressource = creer_ressource(en_base, titre="Guide du lavage des mains")
    jour = date(2026, 11, 20)
    fichier = TypeEvenement.telechargement
    ajouter(
        en_base,
        vue(jour, "a", "/bibliotheque", type_=fichier, detail=f"lire:{ressource.id}"),
        vue(jour, "b", "/bibliotheque", type_=fichier, detail=f"telecharger:{ressource.id}"),
    )
    resultat = lire(super_admin, "contenus")
    assert tableau(resultat, "bibliotheque") == [
        {"document": "Guide du lavage des mains", "lectures": 1, "telechargements": 1}
    ]
    assert chiffre(resultat, "documents") == (2, 0)


def test_erreurs_du_serveur_par_route(super_admin: TestClient, en_base: Callable[..., Any]) -> None:
    jour = date(2026, 11, 20)
    erreur = TypeEvenement.erreur
    ajouter(
        en_base,
        vue(jour, "a", "/api/jeux/quiz/{quiz_id}", type_=erreur, detail="500"),
        vue(jour, "b", "/api/jeux/quiz/{quiz_id}", type_=erreur, detail="500"),
    )
    resultat = lire(super_admin, "erreurs")
    assert tableau(resultat, "routes") == [{"route": "/api/jeux/quiz/{quiz_id}", "nombre": 2}]
    assert chiffre(resultat, "serveur")[0] == 2


def test_l_export_neutralise_les_formules(super_admin: TestClient, en_base: Callable[..., Any]) -> None:
    jour = date(2026, 11, 20)
    ajouter(
        en_base,
        *[vue(jour, v, "/inscription", type_=TypeEvenement.recherche, detail="=lien(x)") for v in "abc"],
    )
    texte = super_admin.get(f"{URL}/erreurs/export.csv", params=PERIODE).content.decode("utf-8-sig")
    assert "'=lien(x)" in texte
