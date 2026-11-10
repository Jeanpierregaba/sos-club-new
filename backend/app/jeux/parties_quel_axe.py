"""Les parties de « Quel axe est fait pour toi ? » (spec 032).

Trois parties au plus par élève, sur toute la vie du compte, jamais remises à zéro. Une partie compte dès que
l'API la crée ; elle se reprend toujours, et une seule peut être en cours. La limite est tenue par un verrou du
compte au démarrage, et garantie par la base (numéro 1 à 3 unique par élève, une seule partie en cours). Aucun
point, badge ni certificat : ce domaine n'appelle jamais `points`.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Utilisateur
from app.jeux import quel_axe
from app.jeux.models import PartieQuelAxe

LIMITE = 3


class PlusDeParticipation(Exception):
    pass


class PartieIntrouvable(Exception):
    pass


class PartieTerminee(Exception):
    pass


class PartieIncomplete(Exception):
    pass


async def parties(db: AsyncSession, eleve_id: UUID) -> list[PartieQuelAxe]:
    requete = select(PartieQuelAxe).where(PartieQuelAxe.eleve_id == eleve_id).order_by(PartieQuelAxe.numero)
    return list((await db.scalars(requete)).all())


def _en_cours(liste: list[PartieQuelAxe]) -> PartieQuelAxe | None:
    return next((p for p in liste if p.terminee_le is None), None)


@dataclass(frozen=True)
class Etat:
    utilisees: int
    restantes: int
    en_cours: PartieQuelAxe | None
    # Les parties terminées, de la plus récente à la plus ancienne.
    historique: list[PartieQuelAxe]


async def etat(db: AsyncSession, eleve: Utilisateur) -> Etat:
    """Le compteur et les parties de l'élève : l'API est la seule source de vérité."""
    liste = await parties(db, eleve.id)
    return Etat(
        utilisees=len(liste),
        restantes=max(LIMITE - len(liste), 0),
        en_cours=_en_cours(liste),
        historique=sorted((p for p in liste if p.terminee_le is not None), key=lambda p: p.numero, reverse=True),
    )


async def commencer(db: AsyncSession, eleve: Utilisateur) -> tuple[PartieQuelAxe, bool]:
    """Reprend la partie en cours s'il y en a une ; sinon en crée une, s'il reste une participation.
    Renvoie la partie et vrai si elle vient d'être créée."""
    # Lu avant tout commit ou rollback, qui périment les objets de la session (dont l'élève).
    eleve_id = eleve.id
    # Le verrou du compte sérialise deux démarrages simultanés (double clic, deux appareils).
    await db.execute(select(Utilisateur.id).where(Utilisateur.id == eleve_id).with_for_update())
    liste = await parties(db, eleve_id)
    if (en_cours := _en_cours(liste)) is not None:
        return en_cours, False
    if len(liste) >= LIMITE:
        raise PlusDeParticipation
    nombre = len(quel_axe.QUESTIONNAIRES[quel_axe.VERSION])
    partie = PartieQuelAxe(
        eleve_id=eleve_id,
        numero=len(liste) + 1,
        version_questionnaire=quel_axe.VERSION,
        reponses=[None] * nombre,
        commencee_le=datetime.now(UTC),
    )
    db.add(partie)
    try:
        await db.commit()
    except IntegrityError:
        # Filet de la base : en principe inatteignable (le verrou sérialise les démarrages), mais si un autre
        # chemin créait une partie, on reprend ce qui existe plutôt que d'échouer.
        await db.rollback()
        liste = await parties(db, eleve_id)
        if (en_cours := _en_cours(liste)) is not None:
            return en_cours, False
        raise PlusDeParticipation from None
    return partie, True


async def _partie_a_modifier(db: AsyncSession, eleve: Utilisateur, partie_id: UUID) -> PartieQuelAxe:
    partie = await db.scalar(
        select(PartieQuelAxe).where(PartieQuelAxe.id == partie_id, PartieQuelAxe.eleve_id == eleve.id).with_for_update()
    )
    if partie is None:
        raise PartieIntrouvable
    return partie


async def lire(db: AsyncSession, eleve: Utilisateur, partie_id: UUID) -> PartieQuelAxe:
    partie = await db.scalar(
        select(PartieQuelAxe).where(PartieQuelAxe.id == partie_id, PartieQuelAxe.eleve_id == eleve.id)
    )
    if partie is None:
        raise PartieIntrouvable
    return partie


async def repondre(db: AsyncSession, eleve: Utilisateur, partie_id: UUID, numero: int, lettre: str) -> PartieQuelAxe:
    """Enregistre (ou remplace) la réponse à la question `numero` (à partir de 1) d'une partie en cours."""
    partie = await _partie_a_modifier(db, eleve, partie_id)
    if partie.terminee_le is not None:
        raise PartieTerminee
    if not 1 <= numero <= len(partie.reponses):
        raise PartieIntrouvable
    reponses = list(partie.reponses)
    reponses[numero - 1] = lettre
    partie.reponses = reponses
    await db.commit()
    return partie


async def terminer(db: AsyncSession, eleve: Utilisateur, partie_id: UUID) -> PartieQuelAxe:
    """Calcule et fige le résultat. Une partie déjà terminée est renvoyée telle quelle."""
    partie = await _partie_a_modifier(db, eleve, partie_id)
    if partie.terminee_le is not None:
        return partie
    if any(r is None for r in partie.reponses):
        raise PartieIncomplete
    resultat = quel_axe.calculer(cast(list[quel_axe.Lettre], partie.reponses), partie.version_questionnaire)
    partie.principal = resultat.principal
    partie.autres = list(resultat.autres)
    partie.terminee_le = datetime.now(UTC)
    await db.commit()
    return partie
