"""Moteur d'activation des clubs (spec 033, ADR-0011) : seuils, unicité, régularisation, échéance, concurrence."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Adhesion, Club, ClubStatut, EtatAdhesion, EtatClub
from app.comptes.models import StatutCompte, Utilisateur
from app.encadreurs.models import EtatVerification
from app.notifications.models import Notification
from tests.activation import (
    DEBUT,
    Horloge,
    ajouter_eleves,
    ajouter_encadreur,
    figer,
    peupler,
    recalculer,
)
from tests.conftest import etablissement_de, moteur_test

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer(monkeypatch)


@pytest.fixture
def etab(en_base: Callable[..., Any]) -> UUID:
    return etablissement_de(en_base, "grand-lome")


def club(en_base: Callable[..., Any], club_id: UUID) -> Club:
    return en_base(lambda db: db.get(Club, club_id))


def journal(en_base: Callable[..., Any], club_id: UUID) -> list[ClubStatut]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(ClubStatut).where(ClubStatut.club_id == club_id).order_by(ClubStatut.cree_le, ClubStatut.id)
            )
        )
    )


def notifies(en_base: Callable[..., Any], type_: str) -> set[UUID]:
    return set(en_base(lambda db: db.scalars(select(Notification.utilisateur_id).where(Notification.type == type_))))


def retirer_un_eleve(en_base: Callable[..., Any], eleve_id: UUID) -> None:
    en_base(
        lambda db: db.execute(update(Adhesion).where(Adhesion.eleve_id == eleve_id).values(etat=EtatAdhesion.retiree))
    )


# Création ----------------------------------------------------------------------------------------------------


def test_le_club_d_un_etablissement_est_cree_une_seule_fois(en_base: Callable[..., Any], etab: UUID) -> None:
    premier = en_base(lambda db: activation.club_de(db, etab))
    second = en_base(lambda db: activation.club_de(db, etab))

    assert premier.id == second.id
    assert premier.etat is EtatClub.en_constitution
    assert premier.nom.startswith("Club Santé — ")
    assert premier.demandeur_id is None
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(Club))) == 1


# Seuils ------------------------------------------------------------------------------------------------------


def test_deux_encadreurs_et_21_eleves_ne_suffisent_pas(en_base: Callable[..., Any], etab: UUID, heure: Horloge) -> None:
    effectif = peupler(en_base, etab, 2, 21)

    assert recalculer(en_base, effectif.club_id) is EtatClub.en_constitution
    assert club(en_base, effectif.club_id).actif_le is None


def test_trois_encadreurs_et_20_eleves_ne_suffisent_pas(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = peupler(en_base, etab, 3, 20)

    assert recalculer(en_base, effectif.club_id) is EtatClub.en_constitution


def test_le_21e_eleve_active_le_club_trace_et_previent(en_base: Callable[..., Any], etab: UUID, heure: Horloge) -> None:
    effectif = peupler(en_base, etab, 3, 20)
    recalculer(en_base, effectif.club_id)
    ajouter_eleves(en_base, etab, 1)

    assert recalculer(en_base, effectif.club_id, "affiliation_confirmee") is EtatClub.actif

    lu = club(en_base, effectif.club_id)
    assert lu.etat is EtatClub.actif
    assert lu.actif_le == DEBUT
    activation_ = journal(en_base, effectif.club_id)[-1]
    assert (activation_.ancien, activation_.nouveau) == (EtatClub.en_constitution, EtatClub.actif)
    assert (activation_.nb_encadreurs, activation_.nb_eleves, activation_.cause) == (3, 21, "affiliation_confirmee")
    assert notifies(en_base, "club_active") == set(effectif.encadreurs)


def test_un_recalcul_sans_changement_n_ecrit_rien(en_base: Callable[..., Any], etab: UUID, heure: Horloge) -> None:
    effectif = peupler(en_base, etab, 3, 21)
    recalculer(en_base, effectif.club_id)
    avant = len(journal(en_base, effectif.club_id))

    recalculer(en_base, effectif.club_id)

    assert len(journal(en_base, effectif.club_id)) == avant


@pytest.mark.parametrize(
    "ecart",
    ["affiliation_a_confirmer", "eleve_suspendu", "encadreur_non_verifie", "encadreur_suspendu"],
)
def test_seuls_les_membres_confirmes_et_actifs_comptent(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge, ecart: str
) -> None:
    effectif = peupler(en_base, etab, 2, 20)
    if ecart == "affiliation_a_confirmer":
        ajouter_encadreur(en_base, etab)
        ajouter_eleves(en_base, etab, 1, etat=EtatAdhesion.en_attente_validation)
    elif ecart == "eleve_suspendu":
        ajouter_encadreur(en_base, etab)
        ajouter_eleves(en_base, etab, 1, statut=StatutCompte.suspendu)
    elif ecart == "encadreur_non_verifie":
        ajouter_encadreur(en_base, etab, etat=EtatVerification.en_attente)
        ajouter_eleves(en_base, etab, 1)
    else:
        ajouter_encadreur(en_base, etab, statut=StatutCompte.suspendu)
        ajouter_eleves(en_base, etab, 1)

    assert recalculer(en_base, effectif.club_id) is EtatClub.en_constitution
    assert en_base(lambda db: activation.effectifs(db, effectif.club_id)) in {(2, 21), (3, 20)}


def test_un_eleve_ne_compte_qu_une_fois(en_base: Callable[..., Any], etab: UUID, heure: Horloge) -> None:
    effectif = peupler(en_base, etab, 3, 20)
    # Une ancienne affiliation retirée puis une nouvelle active : un seul élève.
    eleve = effectif.eleves[0]
    en_base(lambda db: _ajouter_affiliation(db, eleve, effectif.club_id, EtatAdhesion.retiree))

    assert en_base(lambda db: activation.effectifs(db, effectif.club_id)) == (3, 20)
    assert recalculer(en_base, effectif.club_id) is EtatClub.en_constitution


async def _ajouter_affiliation(db: AsyncSession, eleve: UUID, club_id: UUID, etat: EtatAdhesion) -> None:
    db.add(Adhesion(eleve_id=eleve, club_id=club_id, etat=etat))


# Régularisation et échéance ----------------------------------------------------------------------------------


def _club_actif(en_base: Callable[..., Any], etab: UUID) -> Any:
    effectif = peupler(en_base, etab, 3, 21)
    assert recalculer(en_base, effectif.club_id) is EtatClub.actif
    return effectif


def test_sous_21_eleves_le_club_entre_en_regularisation_pour_15_jours(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = _club_actif(en_base, etab)
    heure.avancer(3)
    retirer_un_eleve(en_base, effectif.eleves[0])

    assert recalculer(en_base, effectif.club_id, "affiliation_retiree") is EtatClub.en_regularisation

    lu = club(en_base, effectif.club_id)
    assert lu.regularisation_jusquau == DEBUT + timedelta(days=3 + 15)
    assert lu.rappels_envoyes == 0
    assert notifies(en_base, "club_en_regularisation") == set(effectif.encadreurs)


def test_le_seuil_revenu_avant_l_echeance_rend_le_club_actif(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = _club_actif(en_base, etab)
    retirer_un_eleve(en_base, effectif.eleves[0])
    recalculer(en_base, effectif.club_id)
    heure.avancer(14)
    ajouter_eleves(en_base, etab, 1)

    assert recalculer(en_base, effectif.club_id) is EtatClub.actif
    lu = club(en_base, effectif.club_id)
    assert lu.regularisation_jusquau is None
    assert lu.actif_le == DEBUT


def test_a_l_echeance_le_club_est_suspendu(en_base: Callable[..., Any], etab: UUID, heure: Horloge) -> None:
    effectif = _club_actif(en_base, etab)
    retirer_un_eleve(en_base, effectif.eleves[0])
    recalculer(en_base, effectif.club_id)
    heure.avancer(15)

    # Avant toute écriture, la lecture le dit déjà suspendu.
    assert activation.statut_effectif(club(en_base, effectif.club_id), heure.maintenant) is EtatClub.suspendu
    assert recalculer(en_base, effectif.club_id, "echeance") is EtatClub.suspendu

    lu = club(en_base, effectif.club_id)
    assert (lu.etat, lu.regularisation_jusquau) == (EtatClub.suspendu, None)
    assert journal(en_base, effectif.club_id)[-1].cause == "echeance"
    assert notifies(en_base, "club_suspendu") == set(effectif.encadreurs)


def test_la_veille_de_l_echeance_le_club_est_encore_en_regularisation(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = _club_actif(en_base, etab)
    retirer_un_eleve(en_base, effectif.eleves[0])
    recalculer(en_base, effectif.club_id)
    heure.avancer(14.9)

    assert recalculer(en_base, effectif.club_id) is EtatClub.en_regularisation


def test_un_club_suspendu_revient_seul_quand_le_seuil_revient(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = _club_actif(en_base, etab)
    retirer_un_eleve(en_base, effectif.eleves[0])
    recalculer(en_base, effectif.club_id)
    heure.avancer(20)
    recalculer(en_base, effectif.club_id)
    ajouter_eleves(en_base, etab, 1)

    assert recalculer(en_base, effectif.club_id) is EtatClub.actif
    assert club(en_base, effectif.club_id).actif_le == DEBUT


def test_un_club_suspendu_toujours_sous_le_seuil_reste_suspendu(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = _club_actif(en_base, etab)
    retirer_un_eleve(en_base, effectif.eleves[0])
    recalculer(en_base, effectif.club_id)
    heure.avancer(16)
    recalculer(en_base, effectif.club_id)
    heure.avancer(1)

    assert recalculer(en_base, effectif.club_id) is EtatClub.suspendu


def test_un_compte_suspendu_fait_passer_le_club_en_regularisation(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = _club_actif(en_base, etab)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == effectif.encadreurs[0]).values(statut=StatutCompte.suspendu)
        )
    )

    assert recalculer(en_base, effectif.club_id) is EtatClub.en_regularisation


# Concurrence -------------------------------------------------------------------------------------------------


def test_deux_recalculs_simultanes_n_activent_qu_une_fois(
    en_base: Callable[..., Any], etab: UUID, heure: Horloge
) -> None:
    effectif = peupler(en_base, etab, 3, 21)

    async def un_recalcul() -> EtatClub:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            statut = await activation.recalculer(db, effectif.club_id, "concurrent")
            await db.commit()
            return statut

    async def deux() -> list[EtatClub]:
        return list(await asyncio.gather(un_recalcul(), un_recalcul()))

    assert asyncio.run(deux()) == [EtatClub.actif, EtatClub.actif]
    activations = [ligne for ligne in journal(en_base, effectif.club_id) if ligne.nouveau is EtatClub.actif]
    assert len(activations) == 1
    assert len(notifies(en_base, "club_active")) == 3
    assert (
        en_base(
            lambda db: db.scalar(
                select(func.count()).select_from(Notification).where(Notification.type == "club_active")
            )
        )
        == 3
    )
