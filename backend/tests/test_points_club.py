# ruff: noqa: F811
"""Lignes du compte collectif d'un club (spec 038, note de l'ADR-0012) : partie critique, écrite avant le code.

Une ligne de club n'a pas de personne : elle crédite le club seul, compte dans son score et ne change aucun total,
rang ni date d'atteinte personnels.
"""

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import EtatClub
from app.comptes.models import Utilisateur
from app.points import classements, service
from app.points.models import MouvementPoints, Semestre
from tests.test_classements import classement, etat_club, point, semestre  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

RAPPORT_CLUB = "club.rapport_activite"


def crediter_club(en_base: Callable[..., Any], club_id: Any, cle: str, action: str = RAPPORT_CLUB) -> Any:
    return en_base(lambda db: service.crediter_club(db, action, club_id, cle))


def lignes_de_club(en_base: Callable[..., Any]) -> list[MouvementPoints]:
    return list(
        en_base(lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id.is_(None)))).all()
    )


def test_une_ligne_de_club_credite_le_club_seul(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    club = creer_club(creer_eleve("pres", "Présidente"), nom="Club Santé Bè")

    ligne = crediter_club(en_base, club.id, "club.rapport_activite:r1")

    assert ligne is not None
    assert (ligne.utilisateur_id, ligne.club_id, ligne.montant, ligne.demi_points_club) == (None, club.id, 50, 100)
    assert ligne.semestre_id == semestre.id
    resultat = classement(en_base, categorie=classements.Categorie.clubs)
    assert [(l.nom, l.points) for l in resultat.lignes] == [("Club Santé Bè", 50)]


def test_la_meme_cle_ne_credite_le_club_quune_fois(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    club = creer_club(creer_eleve("pres", "Présidente"))

    assert crediter_club(en_base, club.id, "club.rapport_activite:r1") is not None
    assert crediter_club(en_base, club.id, "club.rapport_activite:r1") is None
    assert len(lignes_de_club(en_base)) == 1


@pytest.mark.parametrize("etat", [EtatClub.suspendu, EtatClub.en_constitution])
def test_un_club_hors_service_nest_pas_credite(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
    etat: EtatClub,
) -> None:
    club = creer_club(creer_eleve("pres", "Présidente"))
    etat_club(en_base, club.id, etat)

    assert crediter_club(en_base, club.id, "club.rapport_activite:r1") is None
    assert lignes_de_club(en_base) == []


def test_une_action_qui_nest_pas_du_club_est_refusee(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    club = creer_club(creer_eleve("pres", "Présidente"))

    with pytest.raises(ValueError, match="club"):
        crediter_club(en_base, club.id, "cle", action="encadreur.rapport_activite")

    async def inserer(db: AsyncSession) -> None:
        db.add(
            MouvementPoints(
                utilisateur_id=None, action="encadreur.rapport_activite", montant=50, cle="sans-compte",
                club_id=club.id, demi_points_club=100,
            )
        )  # fmt: skip

    with pytest.raises(IntegrityError):
        en_base(inserer)


def test_une_ligne_de_club_garde_le_double_en_demi_points(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    club = creer_club(creer_eleve("pres", "Présidente"))

    async def inserer(db: AsyncSession) -> None:
        db.add(
            MouvementPoints(
                utilisateur_id=None, action=RAPPORT_CLUB, montant=50, cle="moitie", club_id=club.id,
                demi_points_club=50,
            )
        )  # fmt: skip

    with pytest.raises(IntegrityError):
        en_base(inserer)


def test_une_ligne_de_club_ne_change_rien_aux_personnes(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    president = creer_eleve("pres", "Présidente")
    club = creer_club(president, nom="Club Santé Bè")
    point(en_base, president.id, 30, "gain", semestre_id=semestre.id, club_id=club.id, demi_points=30)
    avant_totaux = en_base(lambda db: service.totaux(db, president.id))
    avant_totaux = (avant_totaux.points_semestre, avant_totaux.total)
    avant_eleves = classement(en_base).lignes
    avant_photo = en_base(lambda db: classements.classement_a_figer(db, semestre))
    avant_club = en_base(lambda db: classements.classement_du_club(db, club)).lignes

    crediter_club(en_base, club.id, "club.rapport_activite:r1")

    apres = en_base(lambda db: service.totaux(db, president.id))
    assert (apres.points_semestre, apres.total) == avant_totaux
    assert classement(en_base).lignes == avant_eleves
    assert en_base(lambda db: classements.classement_a_figer(db, semestre)) == avant_photo
    assert en_base(lambda db: classements.classement_du_club(db, club)).lignes == avant_club
    assert en_base(lambda db: service.scores_des_clubs(db, [club.id])) == {club.id: 65}


def test_annuler_une_ligne_de_club_la_retire(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    club = creer_club(creer_eleve("pres", "Présidente"))
    ligne = crediter_club(en_base, club.id, "club.rapport_activite:r1")

    retrait = en_base(lambda db: service.annuler(db, ligne))

    assert (retrait.utilisateur_id, retrait.montant, retrait.demi_points_club) == (None, -50, -100)
    assert en_base(lambda db: service.scores_des_clubs(db, [club.id])) == {club.id: 0}
