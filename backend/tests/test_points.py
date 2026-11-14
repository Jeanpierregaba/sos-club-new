"""Registre des points (spec 017, ADR-0004) : partie critique, écrite avant le code (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Utilisateur
from app.points import service
from app.points.bareme import (
    ACTION_CORRECTION,
    ARTICLE_ELEVE,
    ARTICLE_ENCADREUR,
    BIENVENUE_ELEVE,
    BIENVENUE_ENCADREUR,
    QUESTION_JOUR_ELEVE,
)
from app.points.models import LigneBareme, MouvementPoints, Semestre
from tests.conftest import moteur_test

AUJOURD_HUI = service.aujourd_hui()


@pytest.fixture
def eleve(creer_utilisateur: Callable[..., Utilisateur]) -> Utilisateur:
    return creer_utilisateur("aya")


@pytest.fixture
def creer_semestre(en_base: Callable[..., Any]) -> Callable[..., Semestre]:
    def creer(libelle: str, debut: date, fin: date) -> Semestre:
        async def inserer(db: AsyncSession) -> Semestre:
            semestre = Semestre(libelle=libelle, debut=debut, fin=fin)
            db.add(semestre)
            return semestre

        return en_base(inserer)

    return creer


@pytest.fixture
def semestre(creer_semestre: Callable[..., Semestre]) -> Semestre:
    return creer_semestre("En cours", AUJOURD_HUI - timedelta(days=10), AUJOURD_HUI + timedelta(days=10))


def crediter(en_base: Callable[..., Any], eleve_id: UUID, cle: str, action: str = BIENVENUE_ELEVE) -> Any:
    return en_base(lambda db: service.crediter(db, action, eleve_id, cle))


def lignes(en_base: Callable[..., Any], eleve_id: UUID) -> list[MouvementPoints]:
    async def lire(db: AsyncSession) -> list[MouvementPoints]:
        return list(await db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == eleve_id)))

    return en_base(lire)


def regler(en_base: Callable[..., Any], action: str, **valeurs: Any) -> None:
    en_base(lambda db: db.execute(update(LigneBareme).where(LigneBareme.code == action).values(**valeurs)))


def test_un_gain_copie_le_montant_du_bareme_et_prend_le_semestre_en_cours(
    eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    ligne = crediter(en_base, eleve.id, f"bienvenue:{eleve.id}")

    assert ligne is not None
    assert (ligne.montant, ligne.action, ligne.semestre_id) == (100, BIENVENUE_ELEVE, semestre.id)
    assert ligne.annule_id is None


def test_hors_semestre_la_ligne_na_pas_de_semestre(
    eleve: Utilisateur, creer_semestre: Callable[..., Semestre], en_base: Callable[..., Any]
) -> None:
    creer_semestre("Passé", AUJOURD_HUI - timedelta(days=60), AUJOURD_HUI - timedelta(days=1))
    creer_semestre("À venir", AUJOURD_HUI + timedelta(days=1), AUJOURD_HUI + timedelta(days=60))

    ligne = crediter(en_base, eleve.id, f"bienvenue:{eleve.id}")

    assert ligne is not None
    assert ligne.semestre_id is None
    totaux = en_base(lambda db: service.totaux(db, eleve.id))
    assert (totaux.semestre, totaux.points_semestre, totaux.total) == (None, 0, 100)


@pytest.mark.parametrize("reglage", [{"actif": False}, {"montant": 0}])
def test_une_action_desactivee_ou_a_zero_necrit_rien(
    reglage: dict[str, Any], eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    regler(en_base, BIENVENUE_ELEVE, **reglage)

    assert crediter(en_base, eleve.id, f"bienvenue:{eleve.id}") is None
    assert lignes(en_base, eleve.id) == []


def test_une_action_inconnue_est_une_erreur(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    with pytest.raises(service.ActionInconnue):
        crediter(en_base, eleve.id, "x", action="eleve.inexistante")


def test_la_meme_cle_ne_credite_quune_fois(eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]) -> None:
    cle = f"bienvenue:{eleve.id}"

    assert crediter(en_base, eleve.id, cle) is not None
    assert crediter(en_base, eleve.id, cle) is None
    assert len(lignes(en_base, eleve.id)) == 1


def test_la_meme_cle_en_deux_requetes_simultanees_ne_credite_quune_fois(
    eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    cle = f"bienvenue:{eleve.id}"

    async def une_requete() -> bool:
        async with AsyncSession(moteur_test) as db:
            ligne = await service.crediter(db, BIENVENUE_ELEVE, eleve.id, cle)
            # Laisse l'autre requête écrire avant de valider : la seconde attend alors la première.
            await asyncio.sleep(0.2)
            await db.commit()
            return ligne is not None

    async def scenario() -> list[bool]:
        return await asyncio.gather(une_requete(), une_requete())

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert len(lignes(en_base, eleve.id)) == 1


def test_changer_le_bareme_ne_touche_pas_aux_lignes_deja_ecrites(
    creer_utilisateur: Callable[..., Utilisateur], semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    premier, second = creer_utilisateur("aya"), creer_utilisateur("kofi")
    crediter(en_base, premier.id, f"bienvenue:{premier.id}")

    regler(en_base, BIENVENUE_ELEVE, montant=150)
    crediter(en_base, second.id, f"bienvenue:{second.id}")

    assert [ligne.montant for ligne in lignes(en_base, premier.id)] == [100]
    assert [ligne.montant for ligne in lignes(en_base, second.id)] == [150]


def test_les_totaux_separent_le_semestre_et_lhistorique(
    eleve: Utilisateur, creer_semestre: Callable[..., Semestre], semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    passe = creer_semestre("Passé", AUJOURD_HUI - timedelta(days=60), AUJOURD_HUI - timedelta(days=11))

    async def anciennes_lignes(db: AsyncSession) -> None:
        db.add(MouvementPoints(utilisateur_id=eleve.id, action="eleve.quiz", montant=25, semestre_id=passe.id, cle="a"))
        db.add(MouvementPoints(utilisateur_id=eleve.id, action="eleve.quiz", montant=25, semestre_id=None, cle="b"))

    en_base(anciennes_lignes)
    crediter(en_base, eleve.id, f"bienvenue:{eleve.id}")
    crediter(en_base, eleve.id, "quiz:1", action="eleve.quiz")

    totaux = en_base(lambda db: service.totaux(db, eleve.id))

    assert totaux.semestre is not None and totaux.semestre.id == semestre.id
    assert (totaux.points_semestre, totaux.total) == (150, 200)
    dernieres = en_base(lambda db: service.dernieres_lignes(db, eleve.id, 2))
    assert [(ligne.montant, ligne.semestre) for ligne in dernieres] == [(50, "En cours"), (100, "En cours")]


def test_un_eleve_sans_ligne_a_zero(eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]) -> None:
    totaux = en_base(lambda db: service.totaux(db, eleve.id))

    assert (totaux.points_semestre, totaux.total) == (0, 0)


def test_la_base_refuse_un_montant_negatif_sans_annulation(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(MouvementPoints(utilisateur_id=eleve.id, action="eleve.quiz", montant=-25, cle="negatif"))

    with pytest.raises(IntegrityError):
        en_base(inserer)


def test_une_correction_exige_un_motif(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(MouvementPoints(utilisateur_id=eleve.id, action=ACTION_CORRECTION, montant=-25, cle="correction"))

    with pytest.raises(IntegrityError):
        en_base(inserer)


def test_un_gain_ordinaire_ne_porte_pas_de_motif(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(
            MouvementPoints(
                utilisateur_id=eleve.id, action="eleve.quiz", montant=25, cle="gain-motive", motif="interdit"
            )
        )

    with pytest.raises(IntegrityError):
        en_base(inserer)


def test_une_correction_negative_est_acceptee_avec_son_motif(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> MouvementPoints:
        ligne = MouvementPoints(
            utilisateur_id=eleve.id,
            action=ACTION_CORRECTION,
            montant=-25,
            cle="correction",
            motif="Doublon signalé par le club.",
        )
        db.add(ligne)
        return ligne

    ligne = en_base(inserer)

    assert (ligne.montant, ligne.motif, ligne.club_id, ligne.demi_points_club) == (
        -25,
        "Doublon signalé par le club.",
        None,
        None,
    )


def test_une_correction_negative_peut_etre_annulee_par_un_montant_positif(
    eleve: Utilisateur, en_base: Callable[..., Any]
) -> None:
    async def corriger(db: AsyncSession) -> MouvementPoints:
        ligne = MouvementPoints(
            utilisateur_id=eleve.id,
            action=ACTION_CORRECTION,
            montant=-25,
            cle="correction",
            motif="Erreur de saisie.",
        )
        db.add(ligne)
        return ligne

    correction = en_base(corriger)

    async def annuler(db: AsyncSession) -> MouvementPoints:
        ligne = MouvementPoints(
            utilisateur_id=eleve.id,
            action=ACTION_CORRECTION,
            montant=25,
            cle="annulation:correction",
            annule_id=correction.id,
            motif="Correction annulée.",
        )
        db.add(ligne)
        return ligne

    annulation = en_base(annuler)

    assert (annulation.montant, annulation.annule_id) == (25, correction.id)
    assert en_base(lambda db: service.totaux(db, eleve.id)).total == 0


def test_une_annulation_est_une_ligne_negative_unique(
    eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    gain = crediter(en_base, eleve.id, "quiz:1", action="eleve.quiz")

    def annuler(cle: str) -> None:
        async def inserer(db: AsyncSession) -> None:
            db.add(
                MouvementPoints(
                    utilisateur_id=eleve.id, action="eleve.quiz", montant=-gain.montant, cle=cle, annule_id=gain.id
                )
            )

        en_base(inserer)

    annuler("annulation:quiz:1")
    assert en_base(lambda db: service.totaux(db, eleve.id)).total == 0
    with pytest.raises(IntegrityError):
        annuler("annulation:quiz:1:bis")


def test_annuler_retire_un_gain_une_seule_fois(
    eleve: Utilisateur, semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    gain = crediter(en_base, eleve.id, "quiz:1", action="eleve.quiz")

    annulation = en_base(lambda db: service.annuler(db, gain))
    deuxieme = en_base(lambda db: service.annuler(db, gain))

    assert (annulation.montant, annulation.annule_id, annulation.action) == (-gain.montant, gain.id, "eleve.quiz")
    assert annulation.semestre_id == semestre.id
    assert deuxieme is None
    assert en_base(lambda db: service.totaux(db, eleve.id)).total == 0


def test_deux_annulations_simultanees_ne_retirent_quune_fois(eleve: Utilisateur, en_base: Callable[..., Any]) -> None:
    gain = crediter(en_base, eleve.id, "quiz:1", action="eleve.quiz")

    async def une_requete() -> bool:
        async with AsyncSession(moteur_test) as db:
            ligne = await service.annuler(db, gain)
            await asyncio.sleep(0.2)
            await db.commit()
            return ligne is not None

    async def scenario() -> list[bool]:
        return await asyncio.gather(une_requete(), une_requete())

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert en_base(lambda db: service.totaux(db, eleve.id)).total == 0


def test_la_base_refuse_deux_semestres_qui_se_chevauchent(creer_semestre: Callable[..., Semestre]) -> None:
    creer_semestre("Premier", date(2027, 1, 1), date(2027, 6, 30))

    with pytest.raises(IntegrityError):
        creer_semestre("Second", date(2027, 6, 30), date(2027, 12, 31))


def test_le_bareme_initial_contient_toute_la_grille(en_base: Callable[..., Any]) -> None:
    async def lire(db: AsyncSession) -> tuple[int, list[str]]:
        nombre = await db.scalar(select(func.count()).select_from(LigneBareme))
        en_service = list(
            await db.scalars(select(LigneBareme.code).where(LigneBareme.en_service).order_by(LigneBareme.code))
        )
        return nombre, en_service

    # Les actions écrites par une spec livrée : la bienvenue élève (017), encadreur (018), la question du jour (022),
    # les articles (023), les commentaires (025), la certification (029), la spec 034 : quiz par niveau, étoiles et
    # quiz de certification, puis la correction manuelle (036) ; les anciennes parts fixes du club restent,
    # désactivées.
    assert en_base(lire) == (
        47,
        [
            ACTION_CORRECTION,
            ARTICLE_ELEVE,
            "eleve.badge",
            BIENVENUE_ELEVE,
            "eleve.certification",
            "eleve.commentaire",
            "eleve.etoile_avance",
            "eleve.etoile_debutant",
            "eleve.etoile_expert",
            "eleve.etoile_intermediaire",
            QUESTION_JOUR_ELEVE,
            "eleve.quiz_avance",
            "eleve.quiz_certification",
            "eleve.quiz_debutant",
            "eleve.quiz_expert",
            "eleve.quiz_intermediaire",
            ARTICLE_ENCADREUR,
            BIENVENUE_ENCADREUR,
            "encadreur.certification",
            "encadreur.commentaire",
        ],
    )
