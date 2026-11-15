"""Clôture de semestre et Top 3 (spec 037, R14) : partie critique, écrite avant le code (docs/TESTING.md).

Ce fichier couvre le calcul du classement à figer : qui est photographié, dans quel ordre, et comment les égalités
se départagent (le premier à atteindre son total passe devant, puis l'ordre alphabétique du pseudonyme).
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves.models import Classe, Eleve
from app.points import classements
from app.points.bareme import ACTION_CORRECTION
from app.points.models import MouvementPoints, Semestre
from app.points.service import aujourd_hui
from tests.test_classements import affilier, etablissements_de, point

pytestmark = pytest.mark.usefixtures("annuaire")

DEBUT = datetime(2026, 3, 1, 8, 0, tzinfo=UTC)


@pytest.fixture
def termine(en_base: Callable[..., Any]) -> Semestre:
    """Un semestre terminé hier : c'est celui qu'on clôture."""

    async def inserer(db: AsyncSession) -> Semestre:
        element = Semestre(
            libelle="Semestre 1 2026",
            debut=aujourd_hui() - timedelta(days=120),
            fin=aujourd_hui() - timedelta(days=1),
        )
        db.add(element)
        return element

    return en_base(inserer)


def dater(en_base: Callable[..., Any], ligne: MouvementPoints, quand: datetime) -> None:
    en_base(lambda db: db.execute(update(MouvementPoints).where(MouvementPoints.id == ligne.id).values(cree_le=quand)))


def gain(
    en_base: Callable[..., Any],
    eleve: Utilisateur,
    montant: int,
    cle: str,
    semestre: Semestre,
    quand: datetime = DEBUT,
    **options: Any,
) -> MouvementPoints:
    ligne = point(en_base, eleve.id, montant, cle, semestre_id=semestre.id, **options)
    dater(en_base, ligne, quand)
    return ligne


def figer(en_base: Callable[..., Any], semestre: Semestre, limite: int = 50) -> list[classements.LigneAFiger]:
    return en_base(lambda db: classements.classement_a_figer(db, semestre, limite=limite))


def test_la_photo_reprend_le_classement_national_du_semestre(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    aya = creer_eleve("eleve-a", "Aya", dre="grand-lome")
    ben = creer_eleve("eleve-b", "Ben", dre="maritime")
    club = creer_club(ben, nom="Club Santé Tokoin")
    gain(en_base, aya, 100, "aya", termine)
    gain(en_base, ben, 60, "ben", termine, club_id=club.id, demi_points=60)

    photo = figer(en_base, termine)

    assert [(l.rang, l.rang_brut, l.pseudonyme, l.club, l.dre, l.points) for l in photo] == [
        (1, 1, "Aya", None, "Grand Lomé", 100),
        (2, 2, "Ben", "Club Santé Tokoin", "Maritime", 60),
    ]
    assert photo[0].utilisateur_id == aya.id
    assert photo[0].atteint_le == DEBUT


def test_seules_les_lignes_du_semestre_clos_comptent(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], termine: Semestre
) -> None:
    aya = creer_eleve("eleve-a", "Aya")
    gain(en_base, aya, 40, "aya-clos", termine)
    point(en_base, aya.id, 500, "aya-hors-semestre")

    assert [(l.pseudonyme, l.points) for l in figer(en_base, termine)] == [("Aya", 40)]


def test_les_exclus_ne_sont_pas_photographies(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], termine: Semestre
) -> None:
    retenu = creer_eleve("eleve-retenu", "Retenu")
    suspendu = creer_eleve("eleve-suspendu", "Suspendu")
    ancien = creer_eleve("eleve-ancien", "Ancien")
    nul = creer_eleve("eleve-nul", "Nul")
    negatif = creer_eleve("eleve-negatif", "Négatif")
    for eleve in (retenu, suspendu, ancien, nul):
        gain(en_base, eleve, 30, f"gain-{eleve.identifiant}", termine)
    for eleve, montant in ((nul, -30), (negatif, -20)):
        gain(
            en_base,
            eleve,
            montant,
            f"correction-{eleve.identifiant}",
            termine,
            action=ACTION_CORRECTION,
            motif="Correction de test.",
        )
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == suspendu.id).values(statut=StatutCompte.suspendu)
        )
    )
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == ancien.id).values(ancien_eleve_le=datetime.now(UTC))
        )
    )

    assert [l.pseudonyme for l in figer(en_base, termine)] == ["Retenu"]


def test_a_egalite_le_premier_a_atteindre_son_total_passe_devant(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], termine: Semestre
) -> None:
    tardif = creer_eleve("eleve-a", "Aaron")
    precoce = creer_eleve("eleve-z", "Zoé")
    gain(en_base, tardif, 50, "aaron", termine, DEBUT + timedelta(days=3))
    gain(en_base, precoce, 30, "zoe-1", termine, DEBUT)
    gain(en_base, precoce, 20, "zoe-2", termine, DEBUT + timedelta(days=1))

    photo = figer(en_base, termine)

    assert [(l.rang, l.rang_brut, l.pseudonyme) for l in photo] == [(1, 1, "Zoé"), (2, 1, "Aaron")]
    assert photo[0].atteint_le == DEBUT + timedelta(days=1)


def test_la_derniere_ligne_fixe_la_date_datteinte(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], termine: Semestre
) -> None:
    """Une annulation tardive dans le semestre clos change le total : il est atteint à cette date-là."""
    ama = creer_eleve("eleve-a", "Ama")
    kofi = creer_eleve("eleve-k", "Kofi")
    gain(en_base, ama, 60, "ama-1", termine, DEBUT)
    erreur = gain(en_base, ama, 10, "ama-2", termine, DEBUT + timedelta(days=1))
    gain(
        en_base,
        ama,
        -10,
        "ama-annulation",
        termine,
        DEBUT + timedelta(days=9),
        annule_id=erreur.id,
        motif="Gain en double.",
    )
    gain(en_base, kofi, 60, "kofi", termine, DEBUT + timedelta(days=5))

    photo = figer(en_base, termine)

    assert [(l.pseudonyme, l.points, l.rang) for l in photo] == [("Kofi", 60, 1), ("Ama", 60, 2)]
    assert photo[1].atteint_le == DEBUT + timedelta(days=9)


def test_a_la_meme_seconde_lordre_alphabetique_tranche(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], termine: Semestre
) -> None:
    zoe = creer_eleve("eleve-z", "zoé")
    ama = creer_eleve("eleve-a", "Ama")
    gain(en_base, zoe, 50, "zoe", termine)
    gain(en_base, ama, 50, "ama", termine)

    assert [(l.rang, l.pseudonyme) for l in figer(en_base, termine)] == [(1, "Ama"), (2, "zoé")]


def test_une_egalite_qui_deborde_la_troisieme_place_garde_le_rang_brut(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], termine: Semestre
) -> None:
    premier = creer_eleve("eleve-p", "Premier")
    gain(en_base, premier, 90, "premier", termine)
    for numero in range(4):
        eleve = creer_eleve(f"eleve-{numero}", f"Égal {numero}")
        gain(en_base, eleve, 40, f"egal-{numero}", termine, DEBUT + timedelta(hours=numero))

    photo = figer(en_base, termine)

    assert [(l.rang, l.rang_brut, l.pseudonyme) for l in photo] == [
        (1, 1, "Premier"),
        (2, 2, "Égal 0"),
        (3, 2, "Égal 1"),
        (4, 2, "Égal 2"),
        (5, 2, "Égal 3"),
    ]


def test_la_photo_sarrete_aux_cinquante_premiers(en_base: Callable[..., Any], termine: Semestre) -> None:
    etablissement = etablissements_de(en_base, "grand-lome", 1)[0]

    async def creer(db: AsyncSession) -> None:
        for numero in range(55):
            compte = Utilisateur(
                identifiant=f"eleve-{numero:03d}",
                role=Role.eleve,
                prenom="Test",
                nom="Test",
                mot_de_passe_hash="inutilise",
            )
            db.add(compte)
            await db.flush()
            db.add(
                Eleve(
                    utilisateur_id=compte.id,
                    pseudonyme=f"Joueur {numero:03d}",
                    pseudonyme_normalise=f"joueur{numero:03d}",
                    classe=Classe.seconde,
                    etablissement_id=etablissement,
                    charte_version="test",
                )
            )
            db.add(
                MouvementPoints(
                    utilisateur_id=compte.id,
                    action="eleve.bienvenue",
                    montant=100 + numero,
                    semestre_id=termine.id,
                    cle=f"masse-{numero}",
                )
            )

    en_base(creer)

    photo = figer(en_base, termine)

    assert len(photo) == 50
    assert [l.rang for l in photo] == list(range(1, 51))
    assert photo[0].points == 154 and photo[-1].points == 105


def test_un_semestre_sans_eleve_classe_donne_une_photo_vide(en_base: Callable[..., Any], termine: Semestre) -> None:
    assert figer(en_base, termine) == []


def test_le_club_est_celui_de_ladhesion_active(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    president = creer_eleve("eleve-p", "Présidente")
    club = creer_club(president, nom="Club Santé Bè")
    membre = creer_eleve("eleve-m", "Membre")
    affilier(en_base, membre.id, club.id)
    gain(en_base, membre, 20, "membre", termine)

    (ligne,) = figer(en_base, termine)

    assert (ligne.pseudonyme, ligne.club) == ("Membre", "Club Santé Bè")
    assert isinstance(ligne.utilisateur_id, UUID)
