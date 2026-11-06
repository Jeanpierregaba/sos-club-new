"""Le défi du jour (spec 021, spec 022) : la même question pour tous, qui change à minuit (heure de Lomé, UTC+0).

La question part sans sa réponse ; la correction vient d'une seconde requête (ADR-0004). Un élève actif connecté
répond une fois par jour : sa première réponse est enregistrée, et rapporte les points du barème si elle est
juste. Les réponses suivantes du jour ne comptent pas : la correction lui révèle la bonne réponse. Un visiteur
ou un autre profil reçoit la correction, sans point.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, StatutCompte, Utilisateur
from app.jeux.models import DefiQuestion, DefiReponse
from app.points import service as points
from app.points.bareme import QUESTION_JOUR_ELEVE
from app.points.models import MouvementPoints
from app.points.service import aujourd_hui

VIOLATION_UNICITE = "23505"


class AucunDefi(Exception):
    pass


@dataclass(frozen=True)
class Correction:
    defi: DefiQuestion
    choix: int
    correcte: bool
    # Points gagnés par cette réponse-ci : 0 pour une réponse fausse, déjà comptée ou d'un visiteur.
    points: int
    # Vrai si l'élève avait déjà répondu aujourd'hui : c'est sa première réponse qui est renvoyée.
    deja_repondu: bool


def peut_gagner(utilisateur: Utilisateur | None) -> bool:
    """Seul un élève au compte actif gagne des points au défi du jour (référentiel du 2026-11-05)."""
    return utilisateur is not None and utilisateur.role is Role.eleve and utilisateur.statut is StatutCompte.actif


async def du_jour(db: AsyncSession, jour: date | None = None) -> DefiQuestion:
    """La question active de rang (numéro du jour modulo leur nombre), dans l'ordre de la rotation."""
    jour = jour or aujourd_hui()
    actives = select(DefiQuestion).where(DefiQuestion.actif.is_(True))
    nombre = await db.scalar(select(func.count()).select_from(actives.subquery()))
    if not nombre:
        raise AucunDefi
    return await db.scalar(actives.order_by(DefiQuestion.ordre).offset(jour.toordinal() % nombre).limit(1))


async def reponse_du_jour(db: AsyncSession, utilisateur: Utilisateur | None, jour: date) -> Correction | None:
    """La réponse déjà comptée de cet élève pour ce jour, ou None."""
    if not peut_gagner(utilisateur):
        return None
    ligne = (
        await db.execute(
            select(DefiReponse, DefiQuestion, MouvementPoints.montant)
            .join(DefiQuestion, DefiQuestion.id == DefiReponse.defi_id)
            .outerjoin(MouvementPoints, MouvementPoints.id == DefiReponse.mouvement_id)
            .where(DefiReponse.eleve_id == utilisateur.id, DefiReponse.jour == jour)
        )
    ).first()
    if ligne is None:
        return None
    reponse, defi, montant = ligne
    return Correction(defi, reponse.choix, reponse.correcte, montant or 0, deja_repondu=True)


async def corriger(db: AsyncSession, defi_id: UUID, choix: int, utilisateur: Utilisateur | None = None) -> Correction:
    """La correction d'une question active, même si minuit est passé depuis son affichage. Pour un élève actif
    qui répond à la question du jour, la première réponse du jour est enregistrée et créditée si elle est juste."""
    defi = await db.get(DefiQuestion, defi_id)
    if defi is None or not defi.actif:
        raise AucunDefi
    if choix >= len(defi.options):
        raise ValueError("Cette réponse n'existe pas.")
    correcte = choix == defi.bonne_reponse
    if not peut_gagner(utilisateur):
        return Correction(defi, choix, correcte, 0, deja_repondu=False)

    jour = aujourd_hui()
    deja = await reponse_du_jour(db, utilisateur, jour)
    if deja is not None:
        return deja
    if (await du_jour(db, jour)).id != defi.id:
        # Une question d'un autre jour : corrigée, mais ni comptée ni créditée.
        return Correction(defi, choix, correcte, 0, deja_repondu=False)

    reponse = DefiReponse(eleve_id=utilisateur.id, defi_id=defi.id, jour=jour, choix=choix, correcte=correcte)
    try:
        # Un point de sauvegarde : si une réponse simultanée est passée avant, seule cette insertion est annulée.
        async with db.begin_nested():
            db.add(reponse)
    except IntegrityError as erreur:
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        deja = await reponse_du_jour(db, utilisateur, jour)
        assert deja is not None
        return deja

    gagnes = 0
    if correcte:
        mouvement = await points.crediter(
            db, QUESTION_JOUR_ELEVE, utilisateur.id, f"question_jour:{utilisateur.id}:{jour}"
        )
        if mouvement is not None:
            reponse.mouvement_id = mouvement.id
            gagnes = mouvement.montant
    await db.commit()
    return Correction(defi, choix, correcte, gagnes, deja_repondu=False)
