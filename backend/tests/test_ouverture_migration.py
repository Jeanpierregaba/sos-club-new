"""Migration de la spec 049 : banque officielle, remise à zéro des Jeux et de la certification avant l'ouverture."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from alembic.config import Config
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.certification.models import (
    BadgeObtenu,
    BadgeObtenuArchive,
    EtatCertificat,
    PlaceReussie,
    PlaceReussieArchive,
)
from app.comptes.models import Utilisateur
from app.jeux import progression as jeux
from app.jeux.models import EtoileObtenue, EtoileObtenueArchive
from app.points import service as points
from app.points.bareme import ETOILE_NIVEAU, QUESTION_JOUR_ELEVE, QUIZ_NIVEAU, SAISON
from app.points.models import MouvementPoints
from app.quiz import parametres
from app.quiz.models import EtatQuiz, EtatTentative, NiveauQuiz, ParametresQuiz, QuestionQuiz, Quiz, TentativeQuiz
from tests.certification import acquerir, badges, certificats, creer_parcours, mettre_a_jour, places
from tests.quiz import DEBUT, creer_quiz, gains

AVANT = "9aa1a0ded79b"
AIMES = "AIMES-AFRIQUE — Clubs Santé SOS Docteur TV"
DONNEES = json.loads(
    (Path(__file__).resolve().parents[1] / "alembic" / "donnees" / "banque_officielle.json").read_text(encoding="utf-8")
)
JEUX_100 = json.loads(
    (Path(__file__).resolve().parents[1] / "alembic" / "donnees" / "jeux_100.json").read_text(encoding="utf-8")
)
JEUX_CERTIFICATION = {*QUIZ_NIVEAU.values(), *ETOILE_NIVEAU.values()} | {
    "eleve.quiz_certification",
    "eleve.badge",
    "eleve.certification",
}


def configuration() -> Config:
    return Config(Path(__file__).resolve().parents[1] / "alembic.ini")


def _recharger() -> None:
    command.downgrade(configuration(), AVANT)
    command.upgrade(configuration(), "head")


def _tentative_reussie(db: AsyncSession, joueur_id: UUID, quiz_id: UUID, p: ParametresQuiz) -> TentativeQuiz:
    return TentativeQuiz(
        quiz_id=quiz_id, joueur_id=joueur_id, parametres_id=p.id, etat=EtatTentative.terminee, jour=DEBUT.date(),
        commencee_le=DEBUT, derniere_activite=DEBUT, terminee_le=DEBUT, score=p.nb_questions, reussie=True,
    )  # fmt: skip


@pytest.fixture
def eleve(creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    return creer_eleve("ama")


@pytest.fixture
def avant_l_ouverture(en_base: Callable[..., Any], eleve: Utilisateur) -> dict[str, Any]:
    """Un défi Jeux d'AIMES-AFRIQUE (la banque est là) et un élève qui a tout gagné pendant les tests : un quiz
    Jeux, une étoile, les 20 places, les 5 badges, le certificat ; plus un point de la vie du club et une partie en
    cours."""
    defi = creer_quiz(en_base, titre="Défi 1", niveau="debutant", numero=1)
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == defi.id).values(validateur_nom=AIMES)))
    parcours = creer_parcours(en_base)
    acquerir(en_base, eleve, parcours, range(1, 21))
    mettre_a_jour(en_base, eleve)

    async def jouer_les_jeux(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, "jeux")
        db.add(_tentative_reussie(db, eleve.id, defi.id, p))
        await db.flush()
        compte = await db.get(Utilisateur, eleve.id)
        assert compte is not None
        quiz = await db.get(Quiz, defi.id)
        assert quiz is not None
        await jeux.apres_reussite(db, compte, quiz, f"quiz:{defi.id}:{eleve.id}")
        await points.crediter(db, QUESTION_JOUR_ELEVE, eleve.id, "question:1")
        db.add(
            TentativeQuiz(
                quiz_id=defi.id, joueur_id=eleve.id, parametres_id=p.id, etat=EtatTentative.en_cours,
                jour=DEBUT.date(), commencee_le=DEBUT, derniere_activite=DEBUT,
            )
        )  # fmt: skip

    en_base(jouer_les_jeux)
    return {"defi": defi, "parcours": parcours}


def _total(en_base: Callable[..., Any], eleve_id: UUID, actions: set[str]) -> tuple[int, int]:
    lignes = [g for g in gains(en_base, eleve_id) if g.action in actions]
    return sum(g.montant for g in lignes), sum(g.demi_points_club or 0 for g in lignes)


def _compter(en_base: Callable[..., Any], modele: Any) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(modele)))


def test_les_gains_de_test_existent_avant(
    en_base: Callable[..., Any], eleve: Utilisateur, avant_l_ouverture: Any
) -> None:
    montant, _ = _total(en_base, eleve.id, JEUX_CERTIFICATION)
    # 50 (quiz Débutant) + 500 (étoile, seul quiz du niveau) + 20 × 50 + 5 × 500 + 1 000.
    assert montant == 50 + 500 + 20 * 50 + 5 * 500 + 1000
    assert (len(places(en_base, eleve.id)), len(badges(en_base, eleve.id)), len(certificats(en_base, eleve.id))) == (
        20,
        5,
        1,
    )


def test_remet_a_zero_sans_rien_effacer(
    en_base: Callable[..., Any], eleve: Utilisateur, avant_l_ouverture: Any
) -> None:
    avant = len(gains(en_base, eleve.id))

    _recharger()

    # Les gains des Jeux et de la certification, et la part du club : annulés au registre, avec un motif.
    assert _total(en_base, eleve.id, JEUX_CERTIFICATION) == (0, 0)
    annulations = [g for g in gains(en_base, eleve.id) if g.annule_id is not None]
    assert len(annulations) == avant - 1
    assert {g.motif for g in annulations} == {"Remise à zéro avant l'ouverture au public (spec 049)."}
    # La vie du club ne bouge pas.
    assert _total(en_base, eleve.id, {QUESTION_JOUR_ELEVE})[0] == 20
    # Étoiles, places et badges archivés ; certificat révoqué et archivé.
    assert (_compter(en_base, EtoileObtenue), _compter(en_base, PlaceReussie), _compter(en_base, BadgeObtenu)) == (
        0,
        0,
        0,
    )
    assert _compter(en_base, EtoileObtenueArchive) == 1
    assert _compter(en_base, PlaceReussieArchive) == 20
    assert _compter(en_base, BadgeObtenuArchive) == 5
    (certificat,) = certificats(en_base, eleve.id)
    assert certificat.etat is EtatCertificat.revoque
    assert certificat.archive_le is not None
    assert certificat.motif == "Remise à zéro avant l'ouverture au public (spec 049)."
    # La partie en cours est close sans réussite.
    en_cours = en_base(lambda db: db.scalar(select(func.count()).where(TentativeQuiz.etat == EtatTentative.en_cours)))
    assert en_cours == 0


def test_remplace_les_quiz(en_base: Callable[..., Any], avant_l_ouverture: dict[str, Any]) -> None:
    _recharger()

    async def lire(db: AsyncSession) -> dict[str, Any]:
        publies = (await db.scalars(select(Quiz).where(Quiz.etat == EtatQuiz.publie))).all()
        nombres = dict(
            (await db.execute(select(QuestionQuiz.quiz_id, func.count()).group_by(QuestionQuiz.quiz_id))).all()
        )
        anciens = (await db.scalars(select(Quiz.etat).where(Quiz.titre.in_(["Défi 1", "Place 1", "Place 20"])))).all()
        p = await parametres.en_cours(db, "jeux")
        return {
            "jeux": sorted((q.numero, q.niveau) for q in publies if q.parcours == "jeux"),
            "places": sorted(q.place for q in publies if q.parcours == "certification"),
            "questions": {nombres[q.id] for q in publies},
            "anciens": set(anciens),
            "parametres": (p.nb_questions, p.seuil),
        }

    etat = en_base(lire)

    # Puis la spec 050 recompose les 80 quiz Jeux en 100.
    assert [n for n, _ in etat["jeux"]] == list(range(1, 101))
    assert [niveau for _, niveau in etat["jeux"]] == [q["niveau"] for q in JEUX_100]
    assert etat["places"] == list(range(1, 21))
    assert etat["questions"] == {10}
    assert etat["anciens"] == {EtatQuiz.depublie}
    assert etat["parametres"] == (10, 8)


def test_regagner_apres_la_remise_a_zero(
    en_base: Callable[..., Any], eleve: Utilisateur, avant_l_ouverture: Any
) -> None:
    _recharger()
    nouveaux = {
        q.place: q
        for q in en_base(
            lambda db: db.scalars(select(Quiz).where(Quiz.parcours == "certification", Quiz.etat == EtatQuiz.publie))
        ).all()
    }

    acquerir(en_base, eleve, nouveaux, range(1, 21))
    mettre_a_jour(en_base, eleve)

    async def jouer_le_niveau_debutant(db: AsyncSession) -> bool:
        p = await parametres.en_cours(db, "jeux")
        quiz = (
            await db.scalars(select(Quiz).where(Quiz.etat == EtatQuiz.publie, Quiz.niveau == NiveauQuiz.debutant))
        ).all()
        for q in quiz:
            db.add(_tentative_reussie(db, eleve.id, q.id, p))
        await db.flush()
        return await jeux.verifier_etoile(db, eleve.id, NiveauQuiz.debutant)

    assert en_base(jouer_le_niveau_debutant) is True
    assert places(en_base, eleve.id) == list(range(1, 21))
    assert len(badges(en_base, eleve.id)) == 5
    valides = [c for c in certificats(en_base, eleve.id) if c.etat is EtatCertificat.valide]
    assert len(valides) == 1
    nouveaux_gains = [g for g in gains(en_base, eleve.id) if g.cle.endswith(f":{SAISON}")]
    assert sum(g.montant for g in nouveaux_gains) == 20 * 50 + 5 * 500 + 1000 + 500


def test_le_retour_arriere_est_refuse_apres_la_remise_a_zero(avant_l_ouverture: Any) -> None:
    _recharger()
    with pytest.raises(RuntimeError, match="ne se défait pas"):
        command.downgrade(configuration(), AVANT)


def test_rien_sans_la_banque(en_base: Callable[..., Any], eleve: Utilisateur) -> None:
    parcours = creer_parcours(en_base, places=[1])
    acquerir(en_base, eleve, parcours, [1])

    _recharger()

    assert places(en_base, eleve.id) == [1]
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(Quiz))) == 1
    assert en_base(lambda db: db.scalar(select(func.count()).where(MouvementPoints.annule_id.is_not(None)))) == 0


def test_part_du_club_gain_deja_annule_et_correction_de_l_equipe(
    en_base: Callable[..., Any], eleve: Utilisateur, creer_club: Callable[..., Any], avant_l_ouverture: Any
) -> None:
    """La part du club est retirée avec le gain ; un gain déjà annulé ne l'est pas deux fois ; une correction de
    l'équipe (spec 036) reste ; l'annulation tombe dans le semestre du gain."""
    club = creer_club(eleve)

    async def inserer(db: AsyncSession) -> None:
        avec_club = MouvementPoints(
            utilisateur_id=eleve.id, action=QUIZ_NIVEAU["avance"], montant=150, cle="club:1", club_id=club.id,
            demi_points_club=150,
        )  # fmt: skip
        deja = MouvementPoints(utilisateur_id=eleve.id, action=QUIZ_NIVEAU["expert"], montant=200, cle="deja:1")
        db.add_all([avec_club, deja])
        await db.flush()
        await points.annuler(db, deja)
        db.add(
            MouvementPoints(
                utilisateur_id=eleve.id, action="admin.correction", montant=-30, cle="correction:1",
                motif="Erreur de saisie.",
            )
        )  # fmt: skip

    en_base(inserer)

    _recharger()

    lignes = gains(en_base, eleve.id)
    assert _total(en_base, eleve.id, JEUX_CERTIFICATION) == (0, 0)
    assert sum(g.demi_points_club or 0 for g in lignes if g.club_id == club.id) == 0
    deja = next(g for g in lignes if g.cle == "deja:1")
    assert len([g for g in lignes if g.annule_id == deja.id]) == 1
    assert [g.montant for g in lignes if g.action == "admin.correction"] == [-30]
    origine = {g.id: g.semestre_id for g in lignes}
    assert all(g.semestre_id == origine[g.annule_id] for g in lignes if g.annule_id is not None)


def test_un_certificat_de_la_phase_de_test_ne_se_reemet_pas(
    en_base: Callable[..., Any], eleve: Utilisateur, avant_l_ouverture: Any
) -> None:
    from app.certification import gestion

    _recharger()
    (certificat,) = certificats(en_base, eleve.id)

    async def reemettre(db: AsyncSession) -> None:
        with pytest.raises(gestion.EtatInvalide, match="phase de test"):
            await gestion.reemettre(db, None, certificat.id, "127.0.0.1")  # type: ignore[arg-type]

    en_base(reemettre)
    liste = en_base(lambda db: gestion.lister_certificats(db, certificat_id=certificat.id))
    assert liste.certificats[0].archive is True
