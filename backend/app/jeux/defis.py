"""Le défi du jour (spec 021, spec 022) : la même question pour tous, qui change à minuit (heure de Lomé, UTC+0).

La question part sans sa réponse ; la correction vient d'une seconde requête (ADR-0004). Un élève actif connecté
répond une fois par jour : sa première réponse est enregistrée, et rapporte les points du barème si elle est
juste. Les réponses suivantes du jour ne comptent pas : la correction lui révèle la bonne réponse.

Les visiteurs et les autres profils jouent la question publique, sans point. Chaque élève reçoit sa propre
question du jour, toujours différente de la publique : la correction vue sans être connecté ne lui sert à rien.
La correction n'est donnée que pour une question qu'on a pu recevoir (aujourd'hui ou hier, pour le passage de
minuit) : un compte ne peut pas lire la réponse de la question d'un autre élève.
"""

from dataclasses import dataclass
from datetime import date, timedelta
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


def rang(jour: date, nombre: int, eleve_id: UUID | None = None) -> int:
    """Le rang de la question dans la rotation. Public : le numéro du jour modulo le nombre de questions. Élève :
    décalé d'au moins 1 et d'au plus `nombre - 1` selon son identifiant, donc jamais la question publique."""
    public = jour.toordinal() % nombre
    if eleve_id is None or nombre < 2:
        return public
    return (public + 1 + eleve_id.int % (nombre - 1)) % nombre


async def du_jour(db: AsyncSession, jour: date | None = None, utilisateur: Utilisateur | None = None) -> DefiQuestion:
    """La question active du jour : la publique, ou celle de l'élève s'il peut gagner des points."""
    jour = jour or aujourd_hui()
    actives = select(DefiQuestion).where(DefiQuestion.actif.is_(True))
    nombre = await db.scalar(select(func.count()).select_from(actives.subquery()))
    if not nombre:
        raise AucunDefi
    eleve_id = utilisateur.id if peut_gagner(utilisateur) else None
    return await db.scalar(actives.order_by(DefiQuestion.ordre).offset(rang(jour, nombre, eleve_id)).limit(1))


async def _accessibles(db: AsyncSession, utilisateur: Utilisateur | None, jour: date) -> set[UUID]:
    """Les questions dont on peut demander la correction : la publique et, pour un élève, la sienne, du jour et de
    la veille (une bulle ouverte avant minuit)."""
    ids: set[UUID] = set()
    for j in (jour, jour - timedelta(days=1)):
        ids.add((await du_jour(db, j)).id)
        if peut_gagner(utilisateur):
            ids.add((await du_jour(db, j, utilisateur)).id)
    return ids


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
    jour = aujourd_hui()
    if defi.id not in await _accessibles(db, utilisateur, jour):
        # Une question qu'on n'a pas pu recevoir : on ne dit même pas qu'elle existe.
        raise AucunDefi
    correcte = choix == defi.bonne_reponse
    if not peut_gagner(utilisateur):
        return Correction(defi, choix, correcte, 0, deja_repondu=False)

    deja = await reponse_du_jour(db, utilisateur, jour)
    if deja is not None:
        if deja.defi.id == defi.id:
            return deja
        # L'élève a déjà répondu aujourd'hui, à une autre question (la banque a changé, ou il corrige la
        # publique) : cette correction-ci, sans point.
        return Correction(defi, choix, correcte, 0, deja_repondu=True)
    if (await du_jour(db, jour, utilisateur)).id != defi.id:
        # La question publique, ou la sienne d'hier : corrigée, mais ni comptée ni créditée.
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
