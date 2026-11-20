"""Les chiffres de l'accueil (section « Jeux & classement ») : des totaux nationaux, calculés à la demande,
sans aucune donnée personnelle."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.activation import en_service
from app.clubs.models import Club
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.points.models import MouvementPoints
from app.points.schemas import ChiffresPublics
from app.quiz.models import EtatTentative, TentativeQuiz


async def chiffres(db: AsyncSession) -> ChiffresPublics:
    eleves = await db.scalar(
        select(func.count())
        .select_from(Utilisateur)
        .where(Utilisateur.role == Role.eleve, Utilisateur.statut == StatutCompte.actif)
    )
    clubs = await db.scalar(select(func.count()).select_from(Club).where(en_service()))
    # Comme le tableau de bord : les parties de test des collaborateurs ne comptent pas.
    quiz = await db.scalar(
        select(func.count())
        .select_from(TentativeQuiz)
        .where(TentativeQuiz.etat == EtatTentative.terminee, TentativeQuiz.essai.is_(False))
    )
    # Les points des personnes, annulations et corrections comprises ; la part des clubs n'est pas recomptée.
    points = await db.scalar(
        select(func.coalesce(func.sum(MouvementPoints.montant), 0)).where(MouvementPoints.utilisateur_id.is_not(None))
    )
    return ChiffresPublics(eleves=eleves or 0, clubs=clubs or 0, quiz=quiz or 0, points=max(int(points or 0), 0))
