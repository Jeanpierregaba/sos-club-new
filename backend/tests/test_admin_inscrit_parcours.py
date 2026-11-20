"""Fiche complète d'un inscrit (spec 045) : registre des points, quiz, certification et contenus, en lecture."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid7

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification.models import BadgeObtenu, Certificat, EtatCertificat
from app.moderation.models import Contenu, EtatContenu, EtatVersion, VersionContenu
from app.points.bareme import ACTION_CORRECTION
from app.points.models import MouvementPoints, Semestre
from app.points.service import aujourd_hui
from app.quiz import parametres
from app.quiz.models import EtatTentative, Quiz, TentativeQuiz
from tests.certification import acquerir, creer_parcours
from tests.conftest import MOT_DE_PASSE, connecter_admin
from tests.quiz import DEBUT, creer_quiz
from tests.test_classements import point

INSCRITS = "/api/admin/inscrits"
LECTURE = {("tableau_de_bord", "consulter"), ("inscrits", "consulter")}

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def lecteur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("lecteur", droits=LECTURE, double_auth=True)
    connecter_admin(client, "lecteur")
    return client


# Points -------------------------------------------------------------------------------------------------------


def test_le_registre_complet_est_pagine(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    autre = creer_eleve("eleve2", affiche="Autre Pseudo")
    for numero in range(60):
        point(en_base, eleve.id, 1, f"ligne-{numero}")
    point(en_base, autre.id, 5, "autre")

    page1 = lecteur.get(f"{INSCRITS}/{eleve.id}/points").json()
    page2 = lecteur.get(f"{INSCRITS}/{eleve.id}/points", params={"page": 2}).json()

    assert page1["registre"]["total"] == 60
    assert len(page1["registre"]["lignes"]) == 50
    assert len(page2["registre"]["lignes"]) == 10
    assert page1["totaux"]["total"] == 60
    lignes = page1["registre"]["lignes"] + page2["registre"]["lignes"]
    assert {ligne["utilisateur_id"] for ligne in lignes} == {str(eleve.id)}
    dates = [ligne["cree_le"] for ligne in lignes]
    assert dates == sorted(dates, reverse=True)


def test_le_filtre_semestre_et_les_corrections(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()

    async def creer_semestre(db: AsyncSession) -> Semestre:
        element = Semestre(libelle="S1", debut=aujourd_hui() - timedelta(days=5), fin=aujourd_hui() + timedelta(days=5))
        db.add(element)
        return element

    semestre = en_base(creer_semestre)
    ligne = point(en_base, eleve.id, 10, "dans", semestre_id=semestre.id)
    point(en_base, eleve.id, 3, "hors")
    point(en_base, eleve.id, -10, "annulation", semestre_id=semestre.id, annule_id=ligne.id, motif="Doublon constaté")
    point(en_base, eleve.id, 4, "corr", action=ACTION_CORRECTION, motif="Oubli de crédit")

    filtre = lecteur.get(f"{INSCRITS}/{eleve.id}/points", params={"semestre_id": str(semestre.id)}).json()
    tout = lecteur.get(f"{INSCRITS}/{eleve.id}/points").json()

    assert {ligne["cle"] for ligne in filtre["registre"]["lignes"]} == {"dans", "annulation"}
    assert tout["semestres"] == [{"id": str(semestre.id), "libelle": "S1"}]
    par_cle = {ligne["cle"]: ligne for ligne in tout["registre"]["lignes"]}
    assert par_cle["dans"]["annulee"] is True
    assert par_cle["annulation"]["motif"] == "Doublon constaté"
    assert par_cle["corr"]["est_correction"] is True


# Quiz ---------------------------------------------------------------------------------------------------------


def tentative(
    en_base: Callable[..., Any], joueur_id: UUID, quiz: Quiz, *, reussie: bool | None, score: int | None = 10,
    essai: bool = False, decalage: int = 0, points: int | None = None,
    etat: EtatTentative = EtatTentative.terminee,
) -> None:  # fmt: skip
    async def inserer(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, quiz.parcours)
        mouvement_id = None
        if points is not None:
            mouvement = MouvementPoints(
                utilisateur_id=joueur_id, action="eleve.quiz", montant=points, cle=f"quiz-{uuid7()}"
            )
            db.add(mouvement)
            await db.flush()
            mouvement_id = mouvement.id
        debut = DEBUT + timedelta(minutes=decalage)
        db.add(
            TentativeQuiz(
                quiz_id=quiz.id, joueur_id=joueur_id, parametres_id=p.id, essai=essai, etat=etat,
                jour=debut.date(), commencee_le=debut, derniere_activite=debut,
                terminee_le=debut + timedelta(seconds=90) if etat is EtatTentative.terminee else None,
                score=score if etat is EtatTentative.terminee else None,
                reussie=reussie if etat is EtatTentative.terminee else None, mouvement_id=mouvement_id,
            )
        )  # fmt: skip

    en_base(inserer)


def test_les_quiz_valides_et_toutes_les_tentatives(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz_a = creer_quiz(en_base, titre="Hygiène", niveau="debutant", numero=1)
    quiz_b = creer_quiz(en_base, titre="Nutrition", niveau="debutant", numero=2)
    tentative(en_base, eleve.id, quiz_a, reussie=False, score=5, decalage=0)
    tentative(en_base, eleve.id, quiz_a, reussie=True, score=12, decalage=10, points=20)
    tentative(en_base, eleve.id, quiz_a, reussie=True, score=14, decalage=20)
    tentative(en_base, eleve.id, quiz_b, reussie=True, score=15, decalage=30, points=20)
    tentative(en_base, eleve.id, quiz_b, reussie=True, score=15, decalage=40, essai=True)
    tentative(en_base, eleve.id, quiz_b, reussie=None, decalage=50, etat=EtatTentative.en_cours)

    reponse = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz")

    assert reponse.status_code == 200, reponse.text
    donnees = reponse.json()
    assert donnees["resume"] == {"quiz_valides": 2, "tentatives": 4, "echecs": 1, "points": 40}
    valides = {v["titre"]: v for v in donnees["valides"]}
    assert set(valides) == {"Hygiène", "Nutrition"}
    assert valides["Hygiène"]["meilleur_score"] == 14
    assert valides["Hygiène"]["premiere_reussite"] == "2026-11-09T10:11:30Z"
    assert valides["Hygiène"]["reussites"] == 2
    page = donnees["tentatives"]
    assert page["total"] == 6
    assert page["tentatives"][0]["etat"] == "en_cours"
    assert any(t["essai"] for t in page["tentatives"])
    assert page["tentatives"][-1]["duree_s"] == 90
    for t in page["tentatives"]:
        assert set(t) >= {"quiz_titre", "score", "nb_questions", "reussie"}
        assert "questions" not in t and "reponses" not in t


def test_les_filtres_des_tentatives(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    jeu = creer_quiz(en_base, titre="Jeu", niveau="debutant", numero=1)
    (place,) = creer_parcours(en_base, places=[1]).values()
    tentative(en_base, eleve.id, jeu, reussie=False)
    tentative(en_base, eleve.id, jeu, reussie=True, decalage=1)
    tentative(en_base, eleve.id, place, reussie=True, decalage=2)

    def titres(**params: str) -> list[str]:
        page = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz", params=params).json()["tentatives"]
        return [t["quiz_titre"] for t in page["tentatives"]]

    assert titres(parcours="certification") == ["Place 1"]
    assert titres(parcours="jeux", resultat="echouees") == ["Jeu"]
    assert titres(resultat="reussies") == ["Place 1", "Jeu"]
    assert lecteur.get(f"{INSCRITS}/{eleve.id}/quiz", params={"parcours": "autre"}).status_code == 422


def test_un_inscrit_sans_quiz(lecteur: TestClient, creer_encadreur: Callable[..., Any]) -> None:
    encadreur = creer_encadreur()

    donnees = lecteur.get(f"{INSCRITS}/{encadreur.id}/quiz").json()

    assert donnees["resume"] == {"quiz_valides": 0, "tentatives": 0, "echecs": 0, "points": 0}
    assert donnees["valides"] == []
    assert donnees["tentatives"]["tentatives"] == []


# Certification ------------------------------------------------------------------------------------------------


def test_la_progression_les_badges_et_les_certificats(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    parcours = creer_parcours(en_base, places=[1, 2, 3])
    acquerir(en_base, eleve, parcours, [1, 2, 3])

    async def inserer(db: AsyncSession) -> None:
        db.add(
            BadgeObtenu(utilisateur_id=eleve.id, rang=1, nom="Éclaireur", palier=3, regles_version=1, obtenu_le=DEBUT)
        )
        db.add(
            Certificat(
                numero="GI-AAAA-BBBB-CCCC", utilisateur_id=eleve.id, role="eleve", titulaire_prenom="Jean",
                titulaire_nom="Kodjo", etat=EtatCertificat.revoque, delivre_le=DEBUT, motif="Fraude constatée",
                decide_le=DEBUT,
            )
        )  # fmt: skip

    en_base(inserer)

    donnees = lecteur.get(f"{INSCRITS}/{eleve.id}/certification").json()

    assert len(donnees["places"]) == 20
    reussies = [p for p in donnees["places"] if p["reussie_le"]]
    assert [p["place"] for p in reussies] == [1, 2, 3]
    assert reussies[0]["quiz_titre"] == "Place 1"
    assert donnees["badges"] == [{"rang": 1, "nom": "Éclaireur", "palier": 3, "obtenu_le": "2026-11-09T10:00:00Z"}]
    (certificat,) = donnees["certificats"]
    assert (certificat["etat"], certificat["motif"], certificat["titulaire"]) == (
        "revoque", "Fraude constatée", "Jean Kodjo",
    )  # fmt: skip


def test_sans_parcours_de_certification(lecteur: TestClient, creer_eleve: Callable[..., Any]) -> None:
    eleve = creer_eleve()

    donnees = lecteur.get(f"{INSCRITS}/{eleve.id}/certification").json()

    assert len(donnees["places"]) == 20
    assert all(p["reussie_le"] is None for p in donnees["places"])
    assert donnees["badges"] == [] and donnees["certificats"] == []


# Contenus -----------------------------------------------------------------------------------------------------


def contenu(
    en_base: Callable[..., Any], auteur_id: UUID, etat: EtatContenu, titre: str, type_: str = "article"
) -> None:
    contenu_id = uuid7()

    async def inserer(db: AsyncSession) -> None:
        db.add(Contenu(id=contenu_id, type=type_, auteur_id=auteur_id, etat=etat))
        await db.flush()
        version = VersionContenu(
            id=uuid7(), contenu_id=contenu_id, numero=1, donnees={"titre": titre, "texte": "Un texte."},
            etat=EtatVersion.travail,
        )  # fmt: skip
        db.add(version)
        await db.flush()
        await db.execute(update(Contenu).where(Contenu.id == contenu_id).values(version_travail_id=version.id))

    en_base(inserer)


def test_les_contenus_de_linscrit_et_leurs_filtres(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    autre = creer_eleve("eleve2", affiche="Autre Pseudo")
    contenu(en_base, eleve.id, EtatContenu.brouillon, "Mon brouillon")
    contenu(en_base, eleve.id, EtatContenu.refuse, "Mon refusé")
    contenu(en_base, autre.id, EtatContenu.brouillon, "Pas le mien")

    tout = lecteur.get(f"{INSCRITS}/{eleve.id}/contenus").json()
    refuses = lecteur.get(f"{INSCRITS}/{eleve.id}/contenus", params={"etat": "refuse"}).json()
    autres_types = lecteur.get(f"{INSCRITS}/{eleve.id}/contenus", params={"type": "commentaire"}).json()

    assert tout["total"] == 2
    assert {c["titre"] for c in tout["contenus"]} == {"Mon brouillon", "Mon refusé"}
    assert tout["contenus"][0]["type_libelle"] == "Article"
    assert [c["titre"] for c in refuses["contenus"]] == ["Mon refusé"]
    assert autres_types["total"] == 0


# Droits -------------------------------------------------------------------------------------------------------

ROUTES = ("points", "quiz", "certification", "contenus")


@pytest.mark.parametrize("route", ROUTES)
def test_les_routes_ne_sont_pas_mises_en_cache(
    lecteur: TestClient, creer_eleve: Callable[..., Any], route: str
) -> None:
    eleve = creer_eleve()

    reponse = lecteur.get(f"{INSCRITS}/{eleve.id}/{route}")

    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("route", ROUTES)
def test_un_compte_introuvable_ou_collaborateur(
    lecteur: TestClient, creer_collaborateur: Callable[..., Any], route: str
) -> None:
    autre = creer_collaborateur("autre")

    assert lecteur.get(f"{INSCRITS}/{autre.id}/{route}").status_code == 404
    assert lecteur.get(f"{INSCRITS}/{uuid7()}/{route}").status_code == 404


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(("droits", "dre"), [({("tableau_de_bord", "consulter")}, None), (LECTURE, "grand-lome")])
def test_la_lecture_exige_le_droit_national(
    client: TestClient, creer_collaborateur: Callable[..., Any], creer_eleve: Callable[..., Any], route: str,
    droits: set[tuple[str, str]], dre: str | None,
) -> None:  # fmt: skip
    eleve = creer_eleve()
    creer_collaborateur("sans", droits=droits, perimetre_dre=dre, double_auth=True)
    connecter_admin(client, "sans")

    assert client.get(f"{INSCRITS}/{eleve.id}/{route}").status_code == 403


@pytest.mark.parametrize("route", ROUTES)
def test_un_eleve_ou_un_visiteur_sont_refuses(client: TestClient, creer_eleve: Callable[..., Any], route: str) -> None:
    eleve = creer_eleve()
    autre = creer_eleve("eleve2", affiche="Autre Pseudo")

    assert client.get(f"{INSCRITS}/{autre.id}/{route}").status_code in (401, 403)
    client.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": MOT_DE_PASSE})
    assert client.get(f"{INSCRITS}/{eleve.id}/{route}").status_code in (401, 403)


# Après relecture ----------------------------------------------------------------------------------------------


def test_un_visiteur_na_pas_de_fiche_dinscrit(lecteur: TestClient, creer_utilisateur: Callable[..., Any]) -> None:
    from app.comptes.models import Role

    visiteur = creer_utilisateur("curieux", Role.visiteur, email="curieux@exemple.tg")

    for route in ROUTES:
        assert lecteur.get(f"{INSCRITS}/{visiteur.id}/{route}").status_code == 404


def test_les_lignes_du_compte_collectif_dun_club_sont_exclues(
    lecteur: TestClient, creer_eleve: Callable[..., Any], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    point(en_base, eleve.id, 7, "a-moi")

    async def ligne_du_club(db: AsyncSession) -> None:
        from sqlalchemy import select

        from app.clubs.models import Club

        club_id = await db.scalar(select(Club.id).limit(1))
        db.add(
            MouvementPoints(
                utilisateur_id=None, club_id=club_id, action="club.bienvenue_eleve", montant=5, demi_points_club=10,
                cle="club-seul",
            )
        )  # fmt: skip

    creer_club(creer_eleve("eleve3", affiche="Pseudo Président"))
    en_base(ligne_du_club)

    lignes = lecteur.get(f"{INSCRITS}/{eleve.id}/points").json()["registre"]["lignes"]

    assert [ligne["cle"] for ligne in lignes] == ["a-moi"]


def test_les_tentatives_sont_paginees_par_25(
    lecteur: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    quiz = creer_quiz(en_base, titre="Hygiène", niveau="debutant", numero=1)
    for minute in range(27):
        tentative(en_base, eleve.id, quiz, reussie=False, decalage=minute)

    page2 = lecteur.get(f"{INSCRITS}/{eleve.id}/quiz", params={"page": 2}).json()["tentatives"]

    assert (page2["total"], len(page2["tentatives"])) == (27, 2)


def test_un_encadreur_connecte_est_refuse(
    client: TestClient, creer_eleve: Callable[..., Any], creer_encadreur: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    creer_encadreur()
    client.post("/api/comptes/connexion", json={"identifiant": "encadreur1", "mot_de_passe": MOT_DE_PASSE})

    for route in ROUTES:
        assert client.get(f"{INSCRITS}/{eleve.id}/{route}").status_code in (401, 403)
