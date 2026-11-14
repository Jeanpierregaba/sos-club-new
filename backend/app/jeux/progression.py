"""Progression d'un élève dans les 100 quiz Jeux (spec 034, lot 2) : gain selon le niveau du quiz, étoile de chaque
niveau validé, carte Gold aux quatre étoiles, et décompte « points des quiz » / « points des étoiles ».

Le serveur seul décide (ADR-0004) : une étoile s'écrit par une insertion unique (élève, niveau), puis son bonus par
la clé `etoile:<niveau>:<élève>` du registre ; deux réussites simultanées ne la donnent qu'une fois.
"""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import distinct, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, StatutCompte, Utilisateur
from app.jeux.models import EtoileObtenue
from app.points import service as points
from app.points.bareme import ETOILE_NIVEAU, QUIZ_ELEVE, QUIZ_NIVEAU
from app.points.models import LigneBareme, MouvementPoints, SousCompte
from app.quiz.models import NIVEAUX, PARCOURS_JEUX, EtatQuiz, NiveauQuiz, Quiz, TentativeQuiz


class NiveauProgression(BaseModel):
    niveau: NiveauQuiz
    reussis: int
    total: int
    etoile: bool


class ProgressionJeux(BaseModel):
    quiz_reussis: int
    niveaux: list[NiveauProgression]
    # Le niveau en cours : le premier sans étoile (le dernier, quand tous en ont une).
    niveau_courant: NiveauQuiz
    points_quiz: int
    points_etoiles: int
    total: int
    gold: bool
    # Les quiz publiés déjà réussis, pour cocher les défis sur la page Jeux.
    reussis: list[UUID]


def recompense(joueur: Utilisateur) -> bool:
    """Seul un élève actif gagne les récompenses des Jeux ; un encadreur, un visiteur, un invité ou un ancien élève
    (spec 034) joue sans."""
    return joueur.role is Role.eleve and joueur.statut is StatutCompte.actif and joueur.ancien_eleve_le is None


def _reussie(joueur_id: UUID):
    return (
        TentativeQuiz.joueur_id == joueur_id,
        TentativeQuiz.essai.is_(False),
        TentativeQuiz.reussie.is_(True),
    )


def _publie_jeux():
    return Quiz.parcours == PARCOURS_JEUX, Quiz.etat == EtatQuiz.publie


def _du_parcours():
    """Les quiz qui comptent pour les étoiles : publiés et numérotés dans le parcours officiel des 100 défis, ceux
    que la page Jeux montre. Un quiz sans numéro rapporte ses points sans compter pour une étoile."""
    return *_publie_jeux(), Quiz.numero.is_not(None)


async def apres_reussite(db: AsyncSession, joueur: Utilisateur, quiz: Quiz, cle: str) -> MouvementPoints | None:
    """Une partie Jeux réussie par un élève actif sur un quiz publié : le gain du niveau du quiz (une seule fois par
    quiz, clé `cle`), puis l'étoile du niveau si tous ses quiz du parcours sont réussis. Un quiz sans niveau rapporte
    le montant Débutant et ne compte pour aucune étoile. Renvoie le gain du quiz."""
    await db.flush()
    niveau = quiz.niveau or NiveauQuiz.debutant
    gain = await points.crediter(db, QUIZ_NIVEAU[niveau.value], joueur.id, cle)
    if quiz.niveau is not None:
        await verifier_etoile(db, joueur.id, quiz.niveau)
    return gain


async def verifier_etoile(db: AsyncSession, joueur_id: UUID, niveau: NiveauQuiz) -> bool:
    """Donne l'étoile du niveau si chacun de ses quiz du parcours est réussi. Renvoie vrai si elle vient d'être
    donnée. Un verrou par élève sérialise deux réussites simultanées de quiz différents du même niveau : la seconde
    compte après la validation de la première, et voit donc toutes les réussites."""
    await db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"etoiles:{joueur_id}"))))
    total = await db.scalar(select(func.count()).select_from(Quiz).where(*_du_parcours(), Quiz.niveau == niveau))
    if not total:
        return False
    reussis = await db.scalar(
        select(func.count(distinct(TentativeQuiz.quiz_id)))
        .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
        .where(*_reussie(joueur_id), *_du_parcours(), Quiz.niveau == niveau)
    )
    if reussis != total:
        return False
    etoile_id = await db.scalar(
        insert(EtoileObtenue)
        .values(utilisateur_id=joueur_id, niveau=niveau.value)
        .on_conflict_do_nothing(index_elements=["utilisateur_id", "niveau"])
        .returning(EtoileObtenue.id)
    )
    if etoile_id is None:
        return False
    bonus = await points.crediter(db, ETOILE_NIVEAU[niveau.value], joueur_id, f"etoile:{niveau.value}:{joueur_id}")
    etoile = await db.get(EtoileObtenue, etoile_id)
    if etoile is not None and bonus is not None:
        etoile.mouvement_id = bonus.id
    return True


async def progression(db: AsyncSession, joueur_id: UUID) -> ProgressionJeux:
    totaux = dict(
        (
            await db.execute(
                select(Quiz.niveau, func.count()).where(*_du_parcours(), Quiz.niveau.is_not(None)).group_by(Quiz.niveau)
            )
        ).all()
    )
    reussites = (
        await db.execute(
            select(Quiz.id, Quiz.niveau)
            .distinct()
            .join(TentativeQuiz, TentativeQuiz.quiz_id == Quiz.id)
            .where(*_reussie(joueur_id), *_du_parcours())
        )
    ).all()
    reussis = [quiz_id for quiz_id, _ in reussites]
    par_niveau: dict[NiveauQuiz, int] = {}
    for _, niveau in reussites:
        if niveau is not None:
            par_niveau[niveau] = par_niveau.get(niveau, 0) + 1
    avec_etoile = set(
        (await db.scalars(select(EtoileObtenue.niveau).where(EtoileObtenue.utilisateur_id == joueur_id))).all()
    )
    sommes = dict(
        (
            await db.execute(
                select(LigneBareme.sous_compte, func.coalesce(func.sum(MouvementPoints.montant), 0))
                .join(LigneBareme, LigneBareme.code == MouvementPoints.action)
                .where(
                    MouvementPoints.utilisateur_id == joueur_id,
                    LigneBareme.sous_compte.is_not(None),
                    # Les gains d'avant les niveaux (spec 027) ne comptent pas dans les 10 000 points des 100 quiz.
                    MouvementPoints.action != QUIZ_ELEVE,
                )
                .group_by(LigneBareme.sous_compte)
            )
        ).all()
    )
    niveaux = [
        NiveauProgression(niveau=n, reussis=par_niveau.get(n, 0), total=totaux.get(n, 0), etoile=n.value in avec_etoile)
        for n in NIVEAUX
    ]
    points_quiz = int(sommes.get(SousCompte.quiz, 0))
    points_etoiles = int(sommes.get(SousCompte.etoiles, 0))
    return ProgressionJeux(
        quiz_reussis=len(reussis),
        niveaux=niveaux,
        niveau_courant=next((n.niveau for n in niveaux if not n.etoile), NIVEAUX[-1]),
        points_quiz=points_quiz,
        points_etoiles=points_etoiles,
        total=points_quiz + points_etoiles,
        gold=all(n.value in avec_etoile for n in NIVEAUX),
        reussis=reussis,
    )


async def reverifier_niveau(db: AsyncSession, niveau: NiveauQuiz) -> int:
    """Après la dépublication d'un quiz du niveau (le dénominateur baisse) : donne l'étoile aux élèves actifs qui ont
    désormais réussi tous les quiz du niveau (jamais à un ancien élève). Renvoie le nombre d'étoiles données."""
    candidats = (
        await db.scalars(
            select(TentativeQuiz.joueur_id)
            .distinct()
            .join(Quiz, Quiz.id == TentativeQuiz.quiz_id)
            .join(Utilisateur, Utilisateur.id == TentativeQuiz.joueur_id)
            .where(
                TentativeQuiz.essai.is_(False),
                TentativeQuiz.reussie.is_(True),
                Quiz.niveau == niveau,
                Utilisateur.role == Role.eleve,
                Utilisateur.statut == StatutCompte.actif,
                Utilisateur.ancien_eleve_le.is_(None),
                ~select(EtoileObtenue.id)
                .where(EtoileObtenue.utilisateur_id == TentativeQuiz.joueur_id, EtoileObtenue.niveau == niveau.value)
                .exists(),
            )
        )
    ).all()
    donnees = 0
    for joueur_id in candidats:
        donnees += await verifier_etoile(db, joueur_id, niveau)
    return donnees
