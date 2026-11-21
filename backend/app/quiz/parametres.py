"""Paramètres versionnés d'un parcours de quiz (spec 027, CDC admin § 7). Les paramètres en cours sont la version
la plus haute ; une tentative garde la version avec laquelle elle a commencé."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.quiz.models import PARCOURS_CERTIFICATION, PARCOURS_JEUX, ParametresQuiz

# Q12 : 15 questions, 2 secondes de tolérance, réussite à 12 ; plafond de 10 tentatives par jour.
PAR_DEFAUT = {"nb_questions": 15, "temps_ms": 5000, "tolerance_ms": 2000, "seuil": 12, "tentatives_par_jour": 10}
# Spec 048 : 15 secondes par question dans les jeux et la certification (20 s depuis le 2026-11-10).
TEMPS_MS = 15000
PAR_DEFAUT_PARCOURS = {
    PARCOURS_JEUX: PAR_DEFAUT | {"temps_ms": TEMPS_MS},
    # Spec 034 : 10 questions, 10/10, arrêt à la première erreur, sans plafond par quiz (les vies de la spec 048
    # s'appliquent à tous les parcours).
    PARCOURS_CERTIFICATION: PAR_DEFAUT
    | {
        "nb_questions": 10,
        "temps_ms": TEMPS_MS,
        "seuil": 10,
        "tentatives_par_jour": None,
        "arret_premiere_erreur": True,
    },
}


async def en_cours(db: AsyncSession, parcours: str = PARCOURS_JEUX) -> ParametresQuiz:
    """La dernière version ; la première est créée avec les valeurs par défaut si le parcours n'en a aucune."""
    requete = select(ParametresQuiz).where(ParametresQuiz.parcours == parcours).order_by(ParametresQuiz.version.desc())
    parametres = await db.scalar(requete.limit(1))
    if parametres is None:
        await db.execute(
            insert(ParametresQuiz)
            .values(parcours=parcours, version=1, **PAR_DEFAUT_PARCOURS.get(parcours, PAR_DEFAUT))
            .on_conflict_do_nothing(index_elements=["parcours", "version"])
        )
        parametres = await db.scalar(requete.limit(1))
        assert parametres is not None
    return parametres
