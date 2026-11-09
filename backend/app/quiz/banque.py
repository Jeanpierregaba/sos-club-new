"""La banque de quiz (spec 027, CDC admin § 7) : le gestionnaire pédagogique prépare et soumet ; un autre
collaborateur publie en nommant le validateur médical (Q11). Seuls les droits `quiz` y donnent accès, vérifiés par
les routes ; les élèves, encadreurs et présidents n'y ont jamais accès.

Chaque transition verrouille le quiz et vérifie son état : de deux décisions simultanées, la seconde reçoit 409.
Chaque écriture entre au journal d'audit, dans la même transaction.
"""

from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.notifications.service import notifier
from app.quiz import horloge, parametres
from app.quiz.models import PARCOURS_JEUX, EtatQuiz, ParametresQuiz, QuestionQuiz, Quiz, ReponseQuiz, TentativeQuiz
from app.quiz.schemas_banque import (
    Approbation,
    HistoriqueParametres,
    ListeBanque,
    ParametresEntree,
    ParametresSortie,
    QuestionBanque,
    QuestionEntree,
    QuizBanque,
    QuizDetail,
    QuizEntree,
)
from app.referentiel.models import Axe


class Introuvable(Exception):
    pass


class EtatInvalide(Exception):
    """L'opération ne vaut pas dans l'état actuel du quiz (409)."""


class Refuse(Exception):
    """Publication à deux personnes : un contributeur ne publie pas son propre quiz (403)."""


class Invalide(Exception):
    """Données refusées (422), avec un message pour l'équipe."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# Lecture ----------------------------------------------------------------------------------------------------------


async def _actives(db: AsyncSession, quiz_ids: list[UUID]) -> dict[UUID, int]:
    if not quiz_ids:
        return {}
    lignes = await db.execute(
        select(QuestionQuiz.quiz_id, func.count())
        .where(QuestionQuiz.quiz_id.in_(quiz_ids), QuestionQuiz.active)
        .group_by(QuestionQuiz.quiz_id)
    )
    return dict(lignes.all())


async def _titres_ressources(db: AsyncSession, quiz: list[Quiz]) -> dict[UUID, str]:
    ids = {q.ressource_id for q in quiz if q.ressource_id}
    if not ids:
        return {}
    return dict((await db.execute(select(Ressource.id, Ressource.titre).where(Ressource.id.in_(ids)))).all())


def _resume(quiz: Quiz, actives: int, acces: Acces, titres: dict[UUID, str]) -> dict[str, object]:
    return {
        "id": quiz.id,
        "titre": quiz.titre,
        "description": quiz.description,
        "axe_code": quiz.axe_code,
        "etat": quiz.etat,
        "parcours": quiz.parcours,
        "place": quiz.place,
        "ressource_id": quiz.ressource_id,
        "ressource_titre": titres.get(quiz.ressource_id) if quiz.ressource_id else None,
        "contenu_de_test": quiz.contenu_de_test,
        "questions_actives": actives,
        "soumis_le": quiz.soumis_le,
        "decide_le": quiz.decide_le,
        "motif": quiz.motif,
        "validateur_nom": quiz.validateur_nom,
        "validateur_qualite": quiz.validateur_qualite,
        "publie_le": quiz.publie_le,
        "modifie_le": quiz.modifie_le,
        "contributeur": acces.utilisateur.id in (quiz.contributeurs or []),
    }


async def lister(
    db: AsyncSession, acces: Acces, etat: EtatQuiz | None = None, parcours: str | None = None
) -> ListeBanque:
    requete = select(Quiz)
    if etat is not None:
        requete = requete.where(Quiz.etat == etat)
    if parcours is not None:
        requete = requete.where(Quiz.parcours == parcours)
    tous = list((await db.scalars(requete.order_by(Quiz.place.nulls_last(), Quiz.modifie_le.desc()))).all())
    actives = await _actives(db, [q.id for q in tous])
    titres = await _titres_ressources(db, tous)
    p = await parametres.en_cours(db, parcours or PARCOURS_JEUX)
    return ListeBanque(
        questions_requises=p.nb_questions,
        quiz=[QuizBanque.model_validate(_resume(q, actives.get(q.id, 0), acces, titres)) for q in tous],
    )


async def detail(db: AsyncSession, acces: Acces, quiz_id: UUID) -> QuizDetail:
    quiz = await db.get(Quiz, quiz_id)
    if quiz is None:
        raise Introuvable
    questions = (
        await db.scalars(
            select(QuestionQuiz)
            .where(QuestionQuiz.quiz_id == quiz.id)
            .order_by(QuestionQuiz.ordre, QuestionQuiz.active.desc(), QuestionQuiz.id)
        )
    ).all()
    p = await parametres.en_cours(db, quiz.parcours)
    return QuizDetail.model_validate(
        _resume(quiz, sum(1 for q in questions if q.active), acces, await _titres_ressources(db, [quiz]))
        | {
            "questions": [
                QuestionBanque(
                    id=q.id,
                    enonce=q.enonce,
                    choix=q.choix,
                    bonne_reponse=q.bonne_reponse,
                    explication=q.explication,
                    ordre=q.ordre,
                    active=q.active,
                )
                for q in questions
            ],
            "questions_requises": p.nb_questions,
        }
    )


# Préparer ---------------------------------------------------------------------------------------------------------


async def _verrouiller(db: AsyncSession, quiz_id: UUID) -> Quiz:
    quiz = await db.scalar(
        select(Quiz).where(Quiz.id == quiz_id).with_for_update().execution_options(populate_existing=True)
    )
    if quiz is None:
        raise Introuvable
    return quiz


def _brouillon(quiz: Quiz) -> None:
    if quiz.etat is not EtatQuiz.brouillon:
        raise EtatInvalide("Seul un quiz en brouillon se modifie : reprends-le d'abord en brouillon.")


def _contribue(quiz: Quiz, acces: Acces) -> None:
    if acces.utilisateur.id not in (quiz.contributeurs or []):
        quiz.contributeurs = [*(quiz.contributeurs or []), acces.utilisateur.id]


def _journal(db: AsyncSession, action: str, acces: Acces, quiz: Quiz, ip: str, **details: object) -> None:
    journaliser(
        db, f"quiz_{action}", acces.utilisateur, cible_type="quiz", cible_id=quiz.id, perimetre="national",
        details={"titre": quiz.titre, **details}, adresse_ip=ip,
    )  # fmt: skip


async def _axe_existe(db: AsyncSession, code: str) -> None:
    if await db.get(Axe, code) is None:
        raise Invalide("Cet axe n'existe pas.")


async def _fascicule_publie(db: AsyncSession, ressource_id: UUID | None) -> None:
    if ressource_id is None:
        return
    ressource = await db.get(Ressource, ressource_id)
    if (
        ressource is None
        or ressource.categorie is not CategorieRessource.fascicule
        or ressource.etat is not EtatRessource.publie
    ):
        raise Invalide("Choisis un fascicule publié dans la bibliothèque.")


def _parcours(entree: QuizEntree) -> dict[str, object]:
    """Ce que l'audit retient du parcours d'un quiz."""
    if entree.parcours == PARCOURS_JEUX:
        return {}
    return {"parcours": entree.parcours, "place": entree.place, "ressource_id": str(entree.ressource_id or "")}


async def creer(db: AsyncSession, acces: Acces, entree: QuizEntree, ip: str) -> Quiz:
    await _axe_existe(db, entree.axe_code)
    await _fascicule_publie(db, entree.ressource_id)
    quiz = Quiz(
        titre=entree.titre,
        description=entree.description,
        axe_code=entree.axe_code,
        parcours=entree.parcours,
        place=entree.place,
        ressource_id=entree.ressource_id,
        etat=EtatQuiz.brouillon,
        contributeurs=[acces.utilisateur.id],
    )
    db.add(quiz)
    await db.flush()
    _journal(db, "cree", acces, quiz, ip, **_parcours(entree))
    return quiz


async def modifier(db: AsyncSession, acces: Acces, quiz_id: UUID, entree: QuizEntree, ip: str) -> None:
    quiz = await _verrouiller(db, quiz_id)
    _brouillon(quiz)
    await _axe_existe(db, entree.axe_code)
    if entree.ressource_id != quiz.ressource_id:
        await _fascicule_publie(db, entree.ressource_id)
    if entree.parcours != quiz.parcours or entree.place != quiz.place:
        # Les réussites, les points et la progression d'un quiz joué dépendent de son parcours et de sa place.
        joue = await db.scalar(select(exists().where(TentativeQuiz.quiz_id == quiz.id, TentativeQuiz.essai.is_(False))))
        if joue:
            raise Invalide("Ce quiz a déjà été joué : son parcours et sa place ne changent plus.")
    quiz.titre, quiz.description, quiz.axe_code = entree.titre, entree.description, entree.axe_code
    quiz.parcours, quiz.place, quiz.ressource_id = entree.parcours, entree.place, entree.ressource_id
    _contribue(quiz, acces)
    _journal(db, "modifie", acces, quiz, ip, **_parcours(entree))


async def ajouter_question(db: AsyncSession, acces: Acces, quiz_id: UUID, entree: QuestionEntree, ip: str) -> UUID:
    quiz = await _verrouiller(db, quiz_id)
    _brouillon(quiz)
    dernier = await db.scalar(select(func.max(QuestionQuiz.ordre)).where(QuestionQuiz.quiz_id == quiz.id))
    question = QuestionQuiz(quiz_id=quiz.id, ordre=(dernier or 0) + 1, **entree.model_dump())
    db.add(question)
    _contribue(quiz, acces)
    quiz.modifie_le = horloge.maintenant()
    await db.flush()
    _journal(db, "question_ajoutee", acces, quiz, ip, question=str(question.id))
    return question.id


async def _question(db: AsyncSession, quiz: Quiz, question_id: UUID) -> QuestionQuiz:
    question = await db.get(QuestionQuiz, question_id)
    if question is None or question.quiz_id != quiz.id:
        raise Introuvable
    return question


async def modifier_question(
    db: AsyncSession, acces: Acces, quiz_id: UUID, question_id: UUID, entree: QuestionEntree, ip: str
) -> UUID:
    """Une question déjà tirée dans une partie n'est jamais réécrite : une partie en cours et l'historique gardent
    l'énoncé et les choix joués. Elle est désactivée et remplacée par une copie modifiée, à la même place."""
    quiz = await _verrouiller(db, quiz_id)
    _brouillon(quiz)
    question = await _question(db, quiz, question_id)
    tiree = await db.scalar(select(exists().where(ReponseQuiz.question_id == question.id)))
    if tiree and not question.active:
        # Déjà remplacée ou retirée : la modifier créerait une seconde copie active dans la réserve.
        raise EtatInvalide("Cette question a été remplacée ou retirée : modifie la question active.")
    if tiree:
        question.active = False
        question = QuestionQuiz(quiz_id=quiz.id, ordre=question.ordre, **entree.model_dump())
        db.add(question)
        await db.flush()
    else:
        for champ, valeur in entree.model_dump().items():
            setattr(question, champ, valeur)
        question.active = True
    _contribue(quiz, acces)
    quiz.modifie_le = horloge.maintenant()
    remplacement = {"remplace": str(question_id)} if tiree else {}
    _journal(db, "question_modifiee", acces, quiz, ip, question=str(question.id), **remplacement)
    return question.id


async def retirer_question(db: AsyncSession, acces: Acces, quiz_id: UUID, question_id: UUID, ip: str) -> None:
    """Une question déjà tirée dans une partie est désactivée, pas effacée : l'historique des tentatives reste."""
    quiz = await _verrouiller(db, quiz_id)
    _brouillon(quiz)
    question = await _question(db, quiz, question_id)
    tiree = await db.scalar(select(exists().where(ReponseQuiz.question_id == question.id)))
    if tiree:
        question.active = False
    else:
        await db.delete(question)
    _contribue(quiz, acces)
    quiz.modifie_le = horloge.maintenant()
    _journal(db, "question_retiree", acces, quiz, ip, question=str(question_id), desactivee=bool(tiree))


async def _reserve_suffisante(db: AsyncSession, quiz: Quiz) -> None:
    requises = (await parametres.en_cours(db, quiz.parcours)).nb_questions
    actives = (await _actives(db, [quiz.id])).get(quiz.id, 0)
    if actives < requises:
        raise Invalide(f"Il faut au moins {requises} questions actives ; ce quiz en compte {actives}.")


async def soumettre(db: AsyncSession, acces: Acces, quiz_id: UUID, ip: str) -> None:
    quiz = await _verrouiller(db, quiz_id)
    _brouillon(quiz)
    await _reserve_suffisante(db, quiz)
    quiz.etat = EtatQuiz.soumis
    quiz.soumis_par = acces.utilisateur.id
    quiz.soumis_le = horloge.maintenant()
    _contribue(quiz, acces)
    _journal(db, "soumis", acces, quiz, ip)


async def reprendre(db: AsyncSession, acces: Acces, quiz_id: UUID, ip: str) -> None:
    """Un quiz soumis (retiré de la file) ou dépublié revient en brouillon pour être modifié."""
    quiz = await _verrouiller(db, quiz_id)
    if quiz.etat not in (EtatQuiz.soumis, EtatQuiz.depublie):
        raise EtatInvalide("Seul un quiz soumis ou dépublié se reprend en brouillon.")
    quiz.etat = EtatQuiz.brouillon
    _journal(db, "repris", acces, quiz, ip)


# Décider ----------------------------------------------------------------------------------------------------------


def _prevenir(db: AsyncSession, quiz: Quiz, titre: str, message: str | None) -> None:
    if quiz.soumis_par is not None:
        notifier(db, quiz.soumis_par, "quiz_decision", titre, message, f"/admin/quiz/{quiz.id}")


async def approuver(db: AsyncSession, acces: Acces, quiz_id: UUID, entree: Approbation, ip: str) -> None:
    quiz = await _verrouiller(db, quiz_id)
    if acces.utilisateur.id in (quiz.contributeurs or []):
        raise Refuse
    if quiz.etat is not EtatQuiz.soumis:
        raise EtatInvalide("Ce quiz n'est plus en attente de publication.")
    await _reserve_suffisante(db, quiz)
    occupee = f"La place {quiz.place} a déjà un quiz publié : dépublie-le d'abord."
    if quiz.place is not None and await db.scalar(
        select(exists().where(Quiz.place == quiz.place, Quiz.etat == EtatQuiz.publie, Quiz.id != quiz.id))
    ):
        raise EtatInvalide(occupee)
    maintenant = horloge.maintenant()
    quiz.etat = EtatQuiz.publie
    quiz.decide_par, quiz.decide_le = acces.utilisateur.id, maintenant
    quiz.validateur_nom, quiz.validateur_qualite = entree.validateur_nom, entree.validateur_qualite
    quiz.publie_le = maintenant
    quiz.motif = None
    if quiz.place is not None:
        # Deux approbations simultanées sur une même place : l'index unique de la base tranche.
        try:
            async with db.begin_nested():
                await db.flush()
        except IntegrityError:
            raise EtatInvalide(occupee) from None
    _prevenir(db, quiz, f"Ton quiz « {quiz.titre} » est publié", None)
    _journal(
        db, "approuve", acces, quiz, ip,
        validateur_nom=entree.validateur_nom, validateur_qualite=entree.validateur_qualite,
    )  # fmt: skip


async def refuser(db: AsyncSession, acces: Acces, quiz_id: UUID, motif: str, ip: str) -> None:
    quiz = await _verrouiller(db, quiz_id)
    if quiz.etat is not EtatQuiz.soumis:
        raise EtatInvalide("Ce quiz n'est plus en attente de publication.")
    quiz.etat = EtatQuiz.brouillon
    quiz.decide_par, quiz.decide_le, quiz.motif = acces.utilisateur.id, horloge.maintenant(), motif
    _prevenir(db, quiz, f"Ton quiz « {quiz.titre} » n'est pas publié", motif)
    _journal(db, "refuse", acces, quiz, ip, motif=motif)


async def depublier(db: AsyncSession, acces: Acces, quiz_id: UUID, motif: str, ip: str) -> None:
    """Le quiz disparaît pour les joueurs ; les tentatives et les points acquis restent."""
    quiz = await _verrouiller(db, quiz_id)
    if quiz.etat is not EtatQuiz.publie:
        raise EtatInvalide("Ce quiz n'est pas en ligne.")
    quiz.etat = EtatQuiz.depublie
    quiz.decide_par, quiz.decide_le, quiz.motif = acces.utilisateur.id, horloge.maintenant(), motif
    _prevenir(db, quiz, f"Ton quiz « {quiz.titre} » est dépublié", motif)
    _journal(db, "depublie", acces, quiz, ip, motif=motif)


# Paramètres -------------------------------------------------------------------------------------------------------


def _sortie(p: ParametresQuiz) -> ParametresSortie:
    return ParametresSortie(
        version=p.version,
        nb_questions=p.nb_questions,
        temps_ms=p.temps_ms,
        tolerance_ms=p.tolerance_ms,
        seuil=p.seuil,
        tentatives_par_jour=p.tentatives_par_jour,
        cree_le=p.cree_le,
    )


async def historique(db: AsyncSession, parcours: str = PARCOURS_JEUX) -> HistoriqueParametres:
    en_cours = await parametres.en_cours(db, parcours)
    versions = (
        await db.scalars(
            select(ParametresQuiz).where(ParametresQuiz.parcours == parcours).order_by(ParametresQuiz.version.desc())
        )
    ).all()
    return HistoriqueParametres(en_cours=_sortie(en_cours), versions=[_sortie(p) for p in versions])


async def changer_parametres(
    db: AsyncSession, acces: Acces, entree: ParametresEntree, ip: str, parcours: str = PARCOURS_JEUX
) -> ParametresSortie:
    """Ajoute une version. Refusé si un quiz publié n'a pas assez de questions actives pour le nouveau nombre."""
    # Verrouille les quiz soumis ou publiés : une publication simultanée attend ce changement, puis vérifie sa
    # réserve contre le nouveau nombre de questions ; une publication déjà faite est vue ici.
    candidats = (
        await db.scalars(
            select(Quiz)
            .where(Quiz.parcours == parcours, Quiz.etat.in_((EtatQuiz.soumis, EtatQuiz.publie)))
            .order_by(Quiz.id)
            # FOR NO KEY UPDATE : les parties continuent de se lancer pendant le changement.
            .with_for_update(key_share=True)
            .execution_options(populate_existing=True)
        )
    ).all()
    actuels = await parametres.en_cours(db, parcours)
    publies = [q for q in candidats if q.etat is EtatQuiz.publie]
    actives = await _actives(db, [q.id for q in publies])
    trop_courts = sorted(q.titre for q in publies if actives.get(q.id, 0) < entree.nb_questions)
    if trop_courts:
        raise Invalide(
            f"Ces quiz publiés ont moins de {entree.nb_questions} questions actives : " + ", ".join(trop_courts) + "."
        )
    nouvelle = ParametresQuiz(
        parcours=parcours, version=actuels.version + 1, cree_par=acces.utilisateur.id, **entree.model_dump()
    )
    db.add(nouvelle)
    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError:
        raise EtatInvalide("Les paramètres viennent d'être changés par quelqu'un d'autre : recharge la page.") from None
    journaliser(
        db, "quiz_parametres_modifies", acces.utilisateur, cible_type="parametres_quiz", cible_id=nouvelle.id,
        perimetre="national", details={"parcours": parcours, "version": nouvelle.version, **entree.model_dump()}, adresse_ip=ip,
    )  # fmt: skip
    await db.refresh(nouvelle)
    return _sortie(nouvelle)
