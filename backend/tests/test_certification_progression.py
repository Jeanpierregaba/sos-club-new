"""La progression dans le parcours Génie Imhotep (spec 029) : places dans l'ordre, badges et certificat délivrés
une seule fois, avec leurs points. Partie critique (points, quiz arbitrés), écrite avant le code."""

import asyncio
import re
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification import progression
from app.certification.models import Certificat, EtatCertificat
from app.comptes.models import StatutCompte, Utilisateur
from app.notifications.models import Notification
from app.quiz.models import EtatQuiz, Quiz
from tests.certification import (
    NUMERO,
    acquerir,
    badges,
    certificats,
    creer_parcours,
    mettre_a_jour,
    places,
    regles,
)
from tests.conftest import moteur_test
from tests.quiz import QUIZ, Horloge, connecter, creer_quiz, figer_horloge, gains, jouer, regler


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama")
    connecter(client, "ama")
    return utilisateur


@pytest.fixture
def encadreur(client: TestClient, creer_encadreur: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_encadreur("kofi")
    connecter(client, "kofi")
    return utilisateur


def actions(en_base: Callable[..., Any], joueur: Utilisateur) -> list[tuple[str, int]]:
    return sorted((g.action, g.montant) for g in gains(en_base, joueur.id))


def avis(en_base: Callable[..., Any], joueur: Utilisateur) -> list[str]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(Notification.type).where(Notification.utilisateur_id == joueur.id).order_by(Notification.id)
            )
        ).all()
    )


# L'ordre des places -----------------------------------------------------------------------------------------------


def test_une_place_souvre_quand_la_precedente_est_reussie(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=range(1, 5))
    acquerir(en_base, eleve, quiz, [1, 2])

    refus = client.post(f"{QUIZ}/{quiz[4].id}/tentatives")

    assert refus.status_code == 403
    assert "précédente" in refus.json()["detail"]
    assert jouer(client, quiz[3], justes=15)["resultat"]["reussie"] is True
    assert client.post(f"{QUIZ}/{quiz[4].id}/tentatives").status_code == 201


def test_la_place_1_est_ouverte_demblee(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1, 2])

    assert client.post(f"{QUIZ}/{quiz[2].id}/tentatives").status_code == 403
    assert client.post(f"{QUIZ}/{quiz[1].id}/tentatives").status_code == 201


def test_une_place_sans_quiz_publie_bloque_les_suivantes(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1, 3])
    acquerir(en_base, eleve, quiz, [1])

    assert client.post(f"{QUIZ}/{quiz[3].id}/tentatives").status_code == 403


def test_une_place_reussie_reste_acquise_quand_son_quiz_est_remplace(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1, 2])
    acquerir(en_base, eleve, quiz, [1])
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == quiz[1].id).values(etat=EtatQuiz.depublie)))
    creer_quiz(en_base, titre="Place 1, version revue", place=1)

    assert client.post(f"{QUIZ}/{quiz[2].id}/tentatives").status_code == 201


def test_un_echec_ne_reussit_pas_la_place(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1])

    jouer(client, quiz[1], justes=11)

    assert places(en_base, eleve.id) == []


def test_un_quiz_de_certification_reussi_ne_rapporte_pas_les_50_points_dun_quiz(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=[1])

    resultat = jouer(client, quiz[1], justes=15)["resultat"]

    assert resultat["reussie"] is True
    assert resultat["points"] == 0
    assert places(en_base, eleve.id) == [1]
    assert actions(en_base, eleve) == []


def test_la_partie_suit_les_parametres_du_parcours_de_certification(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    regler(en_base, parcours="certification", nb_questions=5, seuil=4)
    quiz = creer_parcours(en_base, places=[1])

    etat = jouer(client, quiz[1], justes=4)

    assert etat["total"] == 5
    assert etat["resultat"]["reussie"] is True


def test_la_liste_des_jeux_ne_montre_pas_les_quiz_de_certification(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    creer_quiz(en_base, titre="Jeu")
    creer_parcours(en_base, places=[1])

    assert [q["titre"] for q in client.get(QUIZ).json()["quiz"]] == ["Jeu"]


# Badges -----------------------------------------------------------------------------------------------------------


def test_le_badge_bronze_a_la_3e_place_rapporte_500_une_seule_fois(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=range(1, 4))
    acquerir(en_base, eleve, quiz, [1, 2])

    jouer(client, quiz[3], justes=15)
    jouer(client, quiz[3], justes=15)

    [bronze] = badges(en_base, eleve.id)
    assert (bronze.rang, bronze.nom, bronze.palier, bronze.regles_version) == (1, "Bronze", 3, 1)
    assert actions(en_base, eleve) == [("eleve.badge", 500)]
    assert [g.cle for g in gains(en_base, eleve.id)] == [f"badge:1:{eleve.id}"]
    assert avis(en_base, eleve) == ["certification_badge"]


def test_un_encadreur_obtient_le_badge_sans_points(
    client: TestClient, encadreur: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base, places=range(1, 4))
    acquerir(en_base, encadreur, quiz, [1, 2])

    jouer(client, quiz[3], justes=15)

    assert [b.nom for b in badges(en_base, encadreur.id)] == ["Bronze"]
    assert gains(en_base, encadreur.id) == []


def test_un_palier_abaisse_delivre_le_badge_au_rattrapage(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    quiz = creer_parcours(en_base, places=[1, 2])
    acquerir(en_base, eleve, quiz, [1, 2])
    mettre_a_jour(en_base, eleve)
    assert badges(en_base, eleve.id) == []

    regles(en_base, ["Cuivre", "Argent", "Or", "Platine", "Diamant Imhotep"], [2, 5, 7, 9, 12])
    mettre_a_jour(en_base, eleve)

    [cuivre] = badges(en_base, eleve.id)
    assert (cuivre.nom, cuivre.palier, cuivre.regles_version) == ("Cuivre", 2, 2)
    assert actions(en_base, eleve) == [("eleve.badge", 500)]


def test_une_nouvelle_version_des_regles_garde_les_badges_deja_obtenus(
    eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    quiz = creer_parcours(en_base, places=range(1, 6))
    acquerir(en_base, eleve, quiz, [1, 2, 3])
    mettre_a_jour(en_base, eleve)

    regles(en_base, ["Cuivre", "Fer", "Or", "Platine", "Diamant Imhotep"], [3, 4, 7, 9, 12])
    acquerir(en_base, eleve, quiz, [4])
    mettre_a_jour(en_base, eleve)

    assert [(b.nom, b.palier, b.regles_version) for b in badges(en_base, eleve.id)] == [
        ("Bronze", 3, 1),
        ("Fer", 4, 2),
    ]


def test_un_compte_suspendu_recoit_ses_badges_a_la_reactivation(
    eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    quiz = creer_parcours(en_base, places=range(1, 4))
    acquerir(en_base, eleve, quiz, [1, 2, 3])

    def statut(valeur: StatutCompte) -> None:
        en_base(lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=valeur)))

    statut(StatutCompte.suspendu)
    mettre_a_jour(en_base, eleve)
    assert badges(en_base, eleve.id) == []

    statut(StatutCompte.actif)
    mettre_a_jour(en_base, eleve)
    assert [b.nom for b in badges(en_base, eleve.id)] == ["Bronze"]
    assert actions(en_base, eleve) == [("eleve.badge", 500)]


# Certificat -------------------------------------------------------------------------------------------------------


def test_la_12e_place_delivre_le_certificat_et_1000_points(
    client: TestClient, eleve: Utilisateur, en_base: Callable[..., Any], heure: Horloge
) -> None:
    quiz = creer_parcours(en_base)
    acquerir(en_base, eleve, quiz, range(1, 12))

    jouer(client, quiz[12], justes=15)

    [certificat] = certificats(en_base, eleve.id)
    assert re.match(NUMERO, certificat.numero)
    assert certificat.etat is EtatCertificat.valide
    assert (certificat.role, certificat.titulaire_prenom, certificat.titulaire_nom) == ("eleve", "Jean", "Kodjo")
    assert certificat.club_id is None
    assert len(badges(en_base, eleve.id)) == 5
    assert actions(en_base, eleve) == [("eleve.badge", 500)] * 5 + [("eleve.certification", 1000)]
    assert avis(en_base, eleve).count("certification_certificat") == 1


def test_le_club_de_leleve_affilie_est_enregistre_pour_ses_points(
    eleve: Utilisateur, en_base: Callable[..., Any], creer_club: Callable[..., Any]
) -> None:
    club = creer_club(eleve)
    quiz = creer_parcours(en_base)
    acquerir(en_base, eleve, quiz, range(1, 13))

    mettre_a_jour(en_base, eleve)

    assert {b.club_id for b in badges(en_base, eleve.id)} == {club.id}
    assert certificats(en_base, eleve.id)[0].club_id == club.id


def test_un_encadreur_certifie_gagne_1000_points(encadreur: Utilisateur, en_base: Callable[..., Any]) -> None:
    quiz = creer_parcours(en_base)
    acquerir(en_base, encadreur, quiz, range(1, 13))

    mettre_a_jour(en_base, encadreur)

    [certificat] = certificats(en_base, encadreur.id)
    assert certificat.role == "encadreur"
    assert actions(en_base, encadreur) == [("encadreur.certification", 1000)]


def test_onze_places_ne_suffisent_pas(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    quiz = creer_parcours(en_base)
    acquerir(en_base, eleve, quiz, range(1, 12))

    mettre_a_jour(en_base, eleve)

    assert certificats(en_base, eleve.id) == []
    assert len(badges(en_base, eleve.id)) == 4


def test_deux_fins_simultanees_ne_delivrent_quun_certificat(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    quiz = creer_parcours(en_base)
    acquerir(en_base, eleve, quiz, range(1, 13))

    async def une_fin() -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            compte = await db.get(Utilisateur, eleve.id)
            assert compte is not None
            await progression.mettre_a_jour(db, compte)
            await asyncio.sleep(0.2)
            await db.commit()

    async def scenario() -> None:
        await asyncio.gather(une_fin(), une_fin())

    asyncio.run(scenario())

    assert len(certificats(en_base, eleve.id)) == 1
    assert len(badges(en_base, eleve.id)) == 5
    assert actions(en_base, eleve) == [("eleve.badge", 500)] * 5 + [("eleve.certification", 1000)]


def test_un_certificat_revoque_nest_pas_redelivre(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    quiz = creer_parcours(en_base)
    acquerir(en_base, eleve, quiz, range(1, 13))
    mettre_a_jour(en_base, eleve)
    en_base(
        lambda db: db.execute(
            update(Certificat)
            .where(Certificat.utilisateur_id == eleve.id)
            .values(etat=EtatCertificat.revoque, motif="Fraude avérée.", decide_le=Certificat.delivre_le)
        )
    )

    mettre_a_jour(en_base, eleve)

    assert [c.etat for c in certificats(en_base, eleve.id)] == [EtatCertificat.revoque]
