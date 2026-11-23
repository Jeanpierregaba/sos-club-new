"""Les vies quotidiennes (spec 048, spec 049) : 3 par jour, communes aux quiz des jeux et à la certification.

Les vies ne sont pas stockées : elles se comptent à partir des parties du joueur. Une partie terminée sans réussite,
lancée aujourd'hui (jour de Lomé), coûte une vie ; une partie réussie ne coûte rien ; une partie en cours réserve une
vie jusqu'à sa fin, pour qu'un joueur à une vie ne lance pas plusieurs quiz à la fois. Les essais de l'équipe ne
comptent pas, et les invités sans compte gardent leur propre limite (spec 031).
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, Utilisateur
from app.quiz.models import EtatTentative, TentativeQuiz
from app.quiz.schemas import Vies as VuesVies

VIES_PAR_JOUR = 3


@dataclass(frozen=True)
class Vies:
    total: int
    perdues: int
    en_cours: int

    @property
    def restantes(self) -> int:
        return max(0, self.total - self.perdues - self.en_cours)


def concerne(joueur: Utilisateur) -> bool:
    """Les invités sans compte ont leur limite de 3 quiz au total, pas de vies."""
    return joueur.role is not Role.invite


async def du_jour(db: AsyncSession, joueur_id: UUID, jour: date) -> Vies:
    siennes = (TentativeQuiz.joueur_id == joueur_id, TentativeQuiz.essai.is_(False))
    perdues = await db.scalar(
        select(func.count())
        .select_from(TentativeQuiz)
        .where(
            *siennes,
            TentativeQuiz.jour == jour,
            TentativeQuiz.etat == EtatTentative.terminee,
            TentativeQuiz.reussie.is_not(True),
        )
    )
    # Une partie en cours réserve une vie, quel que soit son jour de lancement.
    en_cours = await db.scalar(
        select(func.count()).select_from(TentativeQuiz).where(*siennes, TentativeQuiz.etat == EtatTentative.en_cours)
    )
    return Vies(total=VIES_PAR_JOUR, perdues=perdues or 0, en_cours=en_cours or 0)


async def resume(db: AsyncSession, joueur: Utilisateur, jour: date) -> VuesVies | None:
    """Les vies du jour telles que l'API les envoie ; None pour un invité."""
    if not concerne(joueur):
        return None
    v = await du_jour(db, joueur.id, jour)
    return VuesVies(total=v.total, restantes=v.restantes, perdues=v.perdues, en_cours=v.en_cours)
