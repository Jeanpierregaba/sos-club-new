"""Part du club à 50 % (spec 034, lot 1, ADR-0012) : partie critique, écrite avant le code (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub
from app.comptes.models import StatutCompte, Utilisateur
from app.points import service
from app.points.bareme import (
    ARTICLE_ENCADREUR,
    BADGE_ELEVE,
    BIENVENUE_ELEVE,
    CERTIFICATION_ELEVE,
    COMMENTAIRE_ELEVE,
    ETOILE_NIVEAU,
    QUESTION_JOUR_ELEVE,
    QUIZ_CERTIFICATION_ELEVE,
    QUIZ_NIVEAU,
)
from app.points.models import LigneBareme, MouvementPoints
from tests.activation import ajouter_eleves, club_id_de
from tests.conftest import etablissement_de, moteur_test

pytestmark = pytest.mark.usefixtures("annuaire")


def mettre_club(en_base: Callable[..., Any], club_id: UUID, etat: EtatClub) -> None:
    # Une régularisation a toujours son échéance (spec 033) : ici, dans 15 jours.
    echeance = datetime.now(UTC) + timedelta(days=15) if etat is EtatClub.en_regularisation else None
    en_base(
        lambda db: db.execute(update(Club).where(Club.id == club_id).values(etat=etat, regularisation_jusquau=echeance))
    )


@pytest.fixture
def etab(en_base: Callable[..., Any]) -> UUID:
    return etablissement_de(en_base, "grand-lome")


@pytest.fixture
def club_actif(en_base: Callable[..., Any], etab: UUID) -> UUID:
    club_id = club_id_de(en_base, etab)
    mettre_club(en_base, club_id, EtatClub.actif)
    return club_id


def crediter(en_base: Callable[..., Any], action: str, utilisateur_id: UUID, cle: str) -> MouvementPoints | None:
    return en_base(lambda db: service.crediter(db, action, utilisateur_id, cle))


def lignes(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[MouvementPoints]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(MouvementPoints)
                .where(MouvementPoints.utilisateur_id == utilisateur_id)
                .order_by(MouvementPoints.cree_le, MouvementPoints.id)
            )
        )
    )


def score(en_base: Callable[..., Any], club_id: UUID) -> float:
    return en_base(lambda db: service.scores_des_clubs(db, [club_id])).get(club_id, 0)


# Le club reçoit la moitié ------------------------------------------------------------------------------------


def test_un_eleve_affilie_a_un_club_actif_lui_rapporte_la_moitie(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)

    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve, "commentaire:1")

    assert gain is not None
    assert (gain.montant, gain.club_id, gain.demi_points_club) == (5, club_actif, 5)
    assert score(en_base, club_actif) == 2.5


def test_un_club_en_regularisation_recoit_encore_sa_part(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)
    mettre_club(en_base, club_actif, EtatClub.en_regularisation)

    crediter(en_base, BIENVENUE_ELEVE, eleve, "bienvenue:1")

    assert score(en_base, club_actif) == 50


@pytest.mark.parametrize("etat", [EtatClub.en_constitution, EtatClub.suspendu])
def test_un_club_hors_service_ne_recoit_rien(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID, etat: EtatClub
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)
    mettre_club(en_base, club_actif, etat)

    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve, "commentaire:1")

    assert gain is not None and gain.montant == 5
    assert gain.club_id is None and gain.demi_points_club is None
    assert score(en_base, club_actif) == 0


def test_une_regularisation_echue_vaut_une_suspension(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)
    hier = datetime.now(UTC) - timedelta(days=1)
    en_base(
        lambda db: db.execute(
            update(Club)
            .where(Club.id == club_actif)
            .values(etat=EtatClub.en_regularisation, regularisation_jusquau=hier)
        )
    )

    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve, "commentaire:1")

    assert gain is not None and gain.club_id is None


def test_un_eleve_suspendu_n_alimente_plus_son_club(en_base: Callable[..., Any], etab: UUID, club_actif: UUID) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1, statut=StatutCompte.suspendu)

    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve, "commentaire:1")

    assert gain is not None and gain.club_id is None


@pytest.mark.parametrize("etat", [EtatAdhesion.en_attente_validation, EtatAdhesion.retiree])
def test_sans_affiliation_active_l_eleve_garde_ses_points_seul(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID, etat: EtatAdhesion
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1, etat=etat)

    gain = crediter(en_base, QUESTION_JOUR_ELEVE, eleve, "question:1")

    assert gain is not None and gain.montant == 20 and gain.club_id is None
    assert score(en_base, club_actif) == 0


def test_un_gain_d_encadreur_ne_credite_aucun_club(
    en_base: Callable[..., Any], creer_encadreur: Callable[..., Utilisateur], club_actif: UUID
) -> None:
    encadreur = creer_encadreur()

    gain = crediter(en_base, ARTICLE_ENCADREUR, encadreur.id, "article:1")

    assert gain is not None and gain.club_id is None


def test_une_annulation_retire_aussi_la_part_du_club(en_base: Callable[..., Any], etab: UUID, club_actif: UUID) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)
    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve, "commentaire:1")
    assert gain is not None

    annulation = en_base(lambda db: service.annuler(db, gain))

    assert (annulation.montant, annulation.club_id, annulation.demi_points_club) == (-5, club_actif, -5)
    assert score(en_base, club_actif) == 0


def test_un_changement_d_etablissement_laisse_les_points_a_l_ancien_club(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)
    crediter(en_base, BIENVENUE_ELEVE, eleve, "bienvenue:1")
    autre_etab = etablissement_de(en_base, "plateaux-ouest")
    autre_club = club_id_de(en_base, autre_etab)
    mettre_club(en_base, autre_club, EtatClub.actif)

    async def changer(db: AsyncSession) -> None:
        await db.execute(update(Adhesion).where(Adhesion.eleve_id == eleve).values(etat=EtatAdhesion.retiree))
        await db.flush()
        db.add(Adhesion(eleve_id=eleve, club_id=autre_club, etat=EtatAdhesion.active))

    en_base(changer)
    crediter(en_base, COMMENTAIRE_ELEVE, eleve, "commentaire:1")

    assert score(en_base, club_actif) == 50
    assert score(en_base, autre_club) == 2.5


def test_un_meme_gain_n_est_credite_qu_une_fois_au_club(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID
) -> None:
    (eleve,) = ajouter_eleves(en_base, etab, 1)

    async def deux_fois() -> None:
        async def une(db_session: Any) -> None:
            async with db_session() as db:
                await service.crediter(db, COMMENTAIRE_ELEVE, eleve, "commentaire:1")
                await db.commit()

        from sqlalchemy.ext.asyncio import async_sessionmaker

        fabrique = async_sessionmaker(moteur_test, expire_on_commit=False)
        await asyncio.gather(une(fabrique), une(fabrique))

    asyncio.run(deux_fois())

    assert len(lignes(en_base, eleve)) == 1
    assert score(en_base, club_actif) == 2.5


def test_le_score_d_un_club_additionne_les_demi_points(
    en_base: Callable[..., Any], etab: UUID, club_actif: UUID
) -> None:
    eleves = ajouter_eleves(en_base, etab, 3)
    for i, eleve in enumerate(eleves):
        crediter(en_base, COMMENTAIRE_ELEVE, eleve, f"commentaire:{i}")

    assert score(en_base, club_actif) == 7.5


# Le barème de la spec 034 ---------------------------------------------------------------------------------------

ATTENDU = {
    BIENVENUE_ELEVE: (100, "vie", None),
    COMMENTAIRE_ELEVE: (5, "vie", None),
    "eleve.republication": (10, "vie", None),
    "eleve.article": (50, "vie", None),
    "eleve.partage": (50, "vie", None),
    QUESTION_JOUR_ELEVE: (20, "vie", None),
    QUIZ_NIVEAU["debutant"]: (50, "jeux", "quiz"),
    QUIZ_NIVEAU["intermediaire"]: (100, "jeux", "quiz"),
    QUIZ_NIVEAU["avance"]: (150, "jeux", "quiz"),
    QUIZ_NIVEAU["expert"]: (200, "jeux", "quiz"),
    ETOILE_NIVEAU["debutant"]: (500, "jeux", "etoiles"),
    ETOILE_NIVEAU["intermediaire"]: (1000, "jeux", "etoiles"),
    ETOILE_NIVEAU["avance"]: (1500, "jeux", "etoiles"),
    ETOILE_NIVEAU["expert"]: (3000, "jeux", "etoiles"),
    QUIZ_CERTIFICATION_ELEVE: (50, "certification", None),
    BADGE_ELEVE: (500, "certification", None),
    CERTIFICATION_ELEVE: (1000, "certification", None),
}


def test_le_bareme_de_l_eleve_suit_le_cahier_des_charges(en_base: Callable[..., Any]) -> None:
    bareme = {
        ligne.code: (ligne.montant, ligne.parcours, ligne.sous_compte)
        for ligne in en_base(lambda db: db.scalars(select(LigneBareme)))
    }

    for code, attendu in ATTENDU.items():
        assert bareme[code] == attendu, code
    # Les parts fixes de la spec 022 restent, désactivées : la règle des 50 % les remplace.
    actives = {ligne.code for ligne in en_base(lambda db: db.scalars(select(LigneBareme).where(LigneBareme.actif)))}
    assert not [code for code in actives if code.startswith("club.") and code.endswith("_eleve")]
