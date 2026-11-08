"""La partie de quiz, arbitrée par le serveur (spec 027, ADR-0004).

Le serveur tire les questions au lancement, puis envoie une question à la fois : une question n'est « envoyée »
(heure enregistrée) qu'au moment où elle part vers le joueur, et son délai court à partir de là. Une réponse
compte si elle arrive dans le temps affiché plus la tolérance ; sinon la question est ratée. Rien dans ce module
n'envoie la bonne réponse : il ne la lit que pour trancher une réponse reçue.

Chaque opération verrouille la tentative : deux réponses simultanées, ou deux fins, ne comptent qu'une fois.
"""

import random
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, StatutCompte, Utilisateur
from app.points import service as points
from app.points.bareme import QUIZ_ELEVE
from app.points.models import MouvementPoints
from app.quiz import horloge, parametres
from app.quiz.models import (
    EtatQuiz,
    EtatTentative,
    ParametresQuiz,
    QuestionQuiz,
    Quiz,
    ReponseQuiz,
    TentativeQuiz,
)
from app.quiz.schemas import EtatPartie, ListeQuiz, QuestionJoueur, QuizJoueur, ResultatPartie

# Une tentative sans activité pendant ce temps est close avec le score acquis.
INACTIVITE = timedelta(minutes=10)
_hasard = random.SystemRandom()


class Introuvable(Exception):
    """Quiz non publié, tentative d'un autre joueur, ou question qui n'est pas la question en cours."""


class PlafondAtteint(Exception):
    pass


class ChoixInvalide(Exception):
    pass


class QuizIncomplet(Exception):
    """La réserve active compte moins de questions que le paramètre en cours."""


def _ms(duree: timedelta) -> int:
    return round(duree.total_seconds() * 1000)


def _delai(p: ParametresQuiz) -> timedelta:
    return timedelta(milliseconds=p.temps_ms + p.tolerance_ms)


def cle_points(quiz_id: UUID, joueur_id: UUID) -> str:
    return f"quiz:{quiz_id}:{joueur_id}"


# Lancer -------------------------------------------------------------------------------------------------------


async def lancer(db: AsyncSession, joueur: Utilisateur, quiz_id: UUID, *, essai: bool = False) -> EtatPartie:
    """Tire les questions et envoie la première. Un essai (mode test d'un collaborateur) accepte un quiz non
    publié, n'entre pas dans le plafond et remplace l'essai précédent du collaborateur."""
    quiz = await db.get(Quiz, quiz_id)
    if quiz is None or (not essai and quiz.etat is not EtatQuiz.publie):
        raise Introuvable
    # Sérialise les lancements d'un même joueur : le plafond et la tentative en cours restent exacts.
    await db.execute(select(Utilisateur.id).where(Utilisateur.id == joueur.id).with_for_update())
    maintenant = horloge.maintenant()
    p = await parametres.en_cours(db)

    if essai:
        await db.execute(delete(TentativeQuiz).where(TentativeQuiz.joueur_id == joueur.id, TentativeQuiz.essai))
    else:
        precedente = await db.scalar(
            select(TentativeQuiz)
            .where(
                TentativeQuiz.quiz_id == quiz.id,
                TentativeQuiz.joueur_id == joueur.id,
                TentativeQuiz.etat == EtatTentative.en_cours,
                TentativeQuiz.essai.is_(False),
            )
            .with_for_update()
        )
        if precedente is not None:
            await _terminer(db, precedente, joueur, quiz, await _parametres_de(db, precedente), maintenant)
        du_jour = await db.scalar(
            select(func.count())
            .select_from(TentativeQuiz)
            .where(
                TentativeQuiz.quiz_id == quiz.id,
                TentativeQuiz.joueur_id == joueur.id,
                TentativeQuiz.jour == maintenant.date(),
                TentativeQuiz.essai.is_(False),
            )
        )
        if (du_jour or 0) >= p.tentatives_par_jour:
            raise PlafondAtteint

    reserve = list(
        (
            await db.scalars(
                select(QuestionQuiz)
                .where(QuestionQuiz.quiz_id == quiz.id, QuestionQuiz.active)
                .order_by(QuestionQuiz.ordre)
            )
        ).all()
    )
    if len(reserve) < p.nb_questions:
        raise QuizIncomplet

    tentative = TentativeQuiz(
        quiz_id=quiz.id,
        joueur_id=joueur.id,
        parametres_id=p.id,
        essai=essai,
        etat=EtatTentative.en_cours,
        jour=maintenant.date(),
        commencee_le=maintenant,
        derniere_activite=maintenant,
    )
    db.add(tentative)
    await db.flush()
    for rang, question in enumerate(_hasard.sample(reserve, p.nb_questions), start=1):
        ordre = list(range(len(question.choix)))
        _hasard.shuffle(ordre)
        db.add(
            ReponseQuiz(
                tentative_id=tentative.id,
                rang=rang,
                question_id=question.id,
                ordre_choix=ordre,
                envoyee_le=maintenant if rang == 1 else None,
            )
        )
    await db.flush()
    return await _etat(db, tentative, quiz, p, maintenant)


# Reprendre et répondre ------------------------------------------------------------------------------------------


async def etat(db: AsyncSession, joueur: Utilisateur, tentative_id: UUID | str, *, essai: bool = False) -> EtatPartie:
    """L'état courant (reprise après une coupure ou un rechargement) : la question en cours garde son heure
    d'envoi d'origine ; expirée, elle est ratée et la suivante part."""
    tentative = await _charger(db, joueur, tentative_id, essai)
    quiz, p, maintenant = await _contexte(db, tentative)
    await _avancer(db, tentative, joueur, quiz, p, maintenant)
    return await _finir_reponse(db, tentative, quiz, p, maintenant)


async def repondre(
    db: AsyncSession, joueur: Utilisateur, tentative_id: UUID | str, rang: int, choix: int, *, essai: bool = False
) -> EtatPartie:
    tentative = await _charger(db, joueur, tentative_id, essai)
    quiz, p, maintenant = await _contexte(db, tentative)
    if tentative.etat is EtatTentative.en_cours and maintenant - tentative.derniere_activite > INACTIVITE:
        await _terminer(db, tentative, joueur, quiz, p, maintenant)

    ligne = await db.scalar(
        select(ReponseQuiz).where(ReponseQuiz.tentative_id == tentative.id, ReponseQuiz.rang == rang)
    )
    if ligne is None or ligne.envoyee_le is None:
        raise Introuvable
    if ligne.correcte is not None or tentative.etat is EtatTentative.terminee:
        # Double envoi, ou réponse arrivée après la fin : rien ne change, le joueur reçoit l'état courant.
        await _avancer(db, tentative, joueur, quiz, p, maintenant)
        return await _finir_reponse(db, tentative, quiz, p, maintenant)
    if choix >= len(ligne.ordre_choix):
        raise ChoixInvalide

    ligne.repondue_le = maintenant
    if maintenant <= ligne.envoyee_le + _delai(p):
        question = await db.get(QuestionQuiz, ligne.question_id)
        assert question is not None
        ligne.choix = ligne.ordre_choix[choix]
        ligne.correcte = ligne.choix == question.bonne_reponse
    else:
        ligne.correcte = False
    tentative.derniere_activite = maintenant
    await _envoyer_suivante(db, tentative, joueur, quiz, p, maintenant)
    return await _finir_reponse(db, tentative, quiz, p, maintenant)


# Liste des quiz ---------------------------------------------------------------------------------------------------


async def liste(db: AsyncSession, joueur: Utilisateur, axe: str | None = None) -> ListeQuiz:
    p = await parametres.en_cours(db)
    requete = select(Quiz).where(Quiz.etat == EtatQuiz.publie)
    if axe:
        requete = requete.where(Quiz.axe_code == axe)
    tous = (await db.scalars(requete.order_by(Quiz.publie_le.desc(), Quiz.titre))).all()

    les_siennes = (TentativeQuiz.joueur_id == joueur.id, TentativeQuiz.essai.is_(False))
    resultats = {
        quiz_id: (bool(reussi), meilleur)
        for quiz_id, reussi, meilleur in await db.execute(
            select(TentativeQuiz.quiz_id, func.bool_or(TentativeQuiz.reussie), func.max(TentativeQuiz.score))
            .where(*les_siennes, TentativeQuiz.etat == EtatTentative.terminee)
            .group_by(TentativeQuiz.quiz_id)
        )
    }
    du_jour = dict(
        (
            await db.execute(
                select(TentativeQuiz.quiz_id, func.count())
                .where(*les_siennes, TentativeQuiz.jour == horloge.maintenant().date())
                .group_by(TentativeQuiz.quiz_id)
            )
        ).all()
    )
    return ListeQuiz(
        nb_questions=p.nb_questions,
        seuil=p.seuil,
        quiz=[
            QuizJoueur(
                id=q.id,
                titre=q.titre,
                description=q.description,
                axe_code=q.axe_code,
                contenu_de_test=q.contenu_de_test,
                publie_le=q.publie_le,
                reussi=resultats.get(q.id, (False, None))[0],
                meilleur_score=resultats.get(q.id, (False, None))[1],
                tentatives_restantes=max(0, p.tentatives_par_jour - du_jour.get(q.id, 0)),
            )
            for q in tous
        ],
    )


# Interne ----------------------------------------------------------------------------------------------------------


async def _charger(db: AsyncSession, joueur: Utilisateur, tentative_id: UUID | str, essai: bool) -> TentativeQuiz:
    try:
        identifiant = UUID(str(tentative_id))
    except ValueError:
        raise Introuvable from None
    tentative = await db.scalar(
        select(TentativeQuiz)
        .where(TentativeQuiz.id == identifiant, TentativeQuiz.joueur_id == joueur.id, TentativeQuiz.essai.is_(essai))
        .with_for_update()
    )
    if tentative is None:
        raise Introuvable
    return tentative


async def _parametres_de(db: AsyncSession, tentative: TentativeQuiz) -> ParametresQuiz:
    p = await db.get(ParametresQuiz, tentative.parametres_id)
    assert p is not None
    return p


async def _contexte(db: AsyncSession, tentative: TentativeQuiz) -> tuple[Quiz, ParametresQuiz, datetime]:
    quiz = await db.get(Quiz, tentative.quiz_id)
    assert quiz is not None
    return quiz, await _parametres_de(db, tentative), horloge.maintenant()


async def _lignes(db: AsyncSession, tentative: TentativeQuiz) -> list[ReponseQuiz]:
    return list(
        (
            await db.scalars(
                select(ReponseQuiz).where(ReponseQuiz.tentative_id == tentative.id).order_by(ReponseQuiz.rang)
            )
        ).all()
    )


async def _courante(db: AsyncSession, tentative: TentativeQuiz) -> ReponseQuiz | None:
    return next((ligne for ligne in await _lignes(db, tentative) if ligne.correcte is None), None)


async def _avancer(
    db: AsyncSession, tentative: TentativeQuiz, joueur: Utilisateur, quiz: Quiz, p: ParametresQuiz, maintenant: datetime
) -> None:
    """Applique le temps écoulé : clôture après une longue inactivité, question expirée comptée ratée."""
    if tentative.etat is EtatTentative.terminee:
        return
    if maintenant - tentative.derniere_activite > INACTIVITE:
        await _terminer(db, tentative, joueur, quiz, p, maintenant)
        return
    courante = await _courante(db, tentative)
    if courante is not None and courante.envoyee_le is not None and maintenant > courante.envoyee_le + _delai(p):
        courante.correcte = False
        tentative.derniere_activite = maintenant
        await _envoyer_suivante(db, tentative, joueur, quiz, p, maintenant)


async def _envoyer_suivante(
    db: AsyncSession, tentative: TentativeQuiz, joueur: Utilisateur, quiz: Quiz, p: ParametresQuiz, maintenant: datetime
) -> None:
    suivante = await _courante(db, tentative)
    if suivante is None:
        await _terminer(db, tentative, joueur, quiz, p, maintenant)
    elif suivante.envoyee_le is None:
        suivante.envoyee_le = maintenant


async def _terminer(
    db: AsyncSession, tentative: TentativeQuiz, joueur: Utilisateur, quiz: Quiz, p: ParametresQuiz, maintenant: datetime
) -> None:
    """Les questions non tranchées sont ratées ; la réussite se calcule sur le seuil de la version de la tentative.
    Seule la première réussite d'un élève actif, sur un quiz toujours publié, rapporte des points."""
    lignes = await _lignes(db, tentative)
    for ligne in lignes:
        if ligne.correcte is None:
            ligne.correcte = False
    tentative.score = sum(1 for ligne in lignes if ligne.correcte)
    tentative.reussie = tentative.score >= p.seuil
    tentative.etat = EtatTentative.terminee
    tentative.terminee_le = maintenant
    if (
        not tentative.essai
        and tentative.reussie
        and quiz.etat is EtatQuiz.publie
        and joueur.role is Role.eleve
        and joueur.statut is StatutCompte.actif
    ):
        # La clé unique du registre garantit un seul crédit par élève et par quiz, quelle que soit la tentative.
        mouvement = await points.crediter(db, QUIZ_ELEVE, joueur.id, cle_points(quiz.id, joueur.id))
        if mouvement is not None:
            tentative.mouvement_id = mouvement.id
    await db.flush()


async def _etat(
    db: AsyncSession, tentative: TentativeQuiz, quiz: Quiz, p: ParametresQuiz, maintenant: datetime
) -> EtatPartie:
    question = None
    resultat = None
    if tentative.etat is EtatTentative.terminee:
        gain = await db.get(MouvementPoints, tentative.mouvement_id) if tentative.mouvement_id else None
        resultat = ResultatPartie(
            score=tentative.score or 0,
            total=p.nb_questions,
            seuil=p.seuil,
            reussie=bool(tentative.reussie),
            points=gain.montant if gain else 0,
        )
    else:
        courante = await _courante(db, tentative)
        assert courante is not None and courante.envoyee_le is not None
        source = await db.get(QuestionQuiz, courante.question_id)
        assert source is not None
        restant = courante.envoyee_le + timedelta(milliseconds=p.temps_ms) - maintenant
        question = QuestionJoueur(
            rang=courante.rang,
            enonce=source.enonce,
            choix=[source.choix[i] for i in courante.ordre_choix],
            temps_ms=p.temps_ms,
            restant_ms=max(0, _ms(restant)),
        )
    return EtatPartie(
        tentative_id=tentative.id,
        quiz_id=quiz.id,
        titre=quiz.titre,
        total=p.nb_questions,
        question=question,
        resultat=resultat,
    )


async def _finir_reponse(
    db: AsyncSession, tentative: TentativeQuiz, quiz: Quiz, p: ParametresQuiz, maintenant: datetime
) -> EtatPartie:
    """Construit l'état renvoyé ; un essai terminé est effacé aussitôt (il ne laisse aucune trace)."""
    resultat = await _etat(db, tentative, quiz, p, maintenant)
    if tentative.essai and tentative.etat is EtatTentative.terminee:
        await db.execute(delete(TentativeQuiz).where(TentativeQuiz.id == tentative.id))
    return resultat
