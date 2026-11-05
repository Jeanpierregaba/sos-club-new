"""Contraintes des tables de la spec 020 : la base garantit les règles même si le code se trompe."""

from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import (
    Adhesion,
    ClubPassation,
    EtatAdhesion,
    EtatPassation,
    EtatRattachement,
    Rattachement,
)
from app.comptes.models import Utilisateur

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def club(creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any]) -> Any:
    return creer_club(creer_eleve("president", "Le Président"))


def ajouter(en_base: Callable[..., Any], *lignes: Any) -> None:
    async def inserer(db: AsyncSession) -> None:
        for ligne in lignes:
            db.add(ligne)
            await db.flush()

    en_base(inserer)


def test_le_president_du_club_de_test_est_membre(club: Any, en_base: Callable[..., Any]) -> None:
    from sqlalchemy import select

    adhesion = en_base(lambda db: db.scalar(select(Adhesion).where(Adhesion.club_id == club.id)))
    assert adhesion.eleve_id == club.president_id
    assert adhesion.etat is EtatAdhesion.active


def test_un_eleve_na_quune_adhesion_en_cours(
    club: Any, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve2", "Kofi")
    ajouter(en_base, Adhesion(eleve_id=eleve.id, club_id=club.id))

    with pytest.raises(IntegrityError):
        ajouter(en_base, Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.en_attente_validation))


def test_apres_un_refus_ou_un_retrait_une_nouvelle_demande_est_possible(
    club: Any, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve2", "Kofi")
    ajouter(
        en_base,
        Adhesion(
            eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.refusee, motif_refus="Pas de cet établissement."
        ),
        Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.retiree),
        Adhesion(eleve_id=eleve.id, club_id=club.id),
    )


def test_un_refus_porte_toujours_un_motif(
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    eleve = creer_eleve("eleve2", "Kofi")
    encadreur = creer_encadreur()

    with pytest.raises(IntegrityError):
        ajouter(en_base, Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.refusee))
    with pytest.raises(IntegrityError):
        ajouter(en_base, Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=EtatRattachement.refuse))
    # Un motif sur une demande qui n'est pas refusée est refusé aussi.
    with pytest.raises(IntegrityError):
        ajouter(en_base, Adhesion(eleve_id=eleve.id, club_id=club.id, motif_refus="Sans objet."))


def test_un_encadreur_peut_avoir_plusieurs_clubs_mais_une_seule_demande_par_club(
    club: Any,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    autre = creer_club(creer_eleve("president2", "Autre Président", dre="kara"), nom="Club de Kara")
    encadreur = creer_encadreur()
    ajouter(
        en_base,
        Rattachement(encadreur_id=encadreur.id, club_id=club.id, etat=EtatRattachement.actif),
        Rattachement(encadreur_id=encadreur.id, club_id=autre.id, supplementaire=True),
    )

    with pytest.raises(IntegrityError):
        ajouter(en_base, Rattachement(encadreur_id=encadreur.id, club_id=club.id))


def test_une_seule_passation_en_attente_par_club_meme_chez_lencadreur(
    club: Any, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    successeur = creer_eleve("eleve2", "Kofi")
    ajouter(
        en_base,
        ClubPassation(
            club_id=club.id,
            successeur_id=successeur.id,
            propose_par=club.president_id,
            etat=EtatPassation.en_attente_encadreur,
        ),
    )

    with pytest.raises(IntegrityError):
        ajouter(
            en_base,
            ClubPassation(club_id=club.id, successeur_id=successeur.id, propose_par=club.president_id),
        )


def test_la_migration_rend_membre_le_president_dun_club_deja_actif(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    """La reprise de données de la migration : un club actif avant la spec 020 n'a pas d'adhésion."""
    from pathlib import Path

    from alembic.config import Config
    from sqlalchemy import text

    from alembic import command

    president = creer_eleve("president", "Le Président")
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
    command.downgrade(configuration, "c1a2b3d4e5f6")
    try:

        async def club_davant(db: AsyncSession) -> None:
            await db.execute(
                text(
                    "INSERT INTO club (id, etablissement_id, nom, nom_normalise, demandeur_id, president_id, etat, actif_le)"
                    " SELECT gen_random_uuid(), etablissement_id, 'Club ancien', 'club ancien', :p, :p, 'actif', now()"
                    " FROM eleve WHERE utilisateur_id = :p"
                ),
                {"p": president.id},
            )

        en_base(club_davant)
    finally:
        command.upgrade(configuration, "head")

    async def adhesions(db: AsyncSession) -> list[tuple[Any, str]]:
        return [tuple(r) for r in await db.execute(text("SELECT eleve_id, etat FROM adhesion"))]

    assert en_base(adhesions) == [(president.id, "active")]
