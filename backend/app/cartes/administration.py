"""Les cartes vues et suspendues par l'équipe, depuis la fiche d'un inscrit (spec 040, CDC admin § 10).

Une suspension par l'équipe s'ajoute aux causes automatiques et ne se lève que par l'équipe. Chaque action est
journalisée avec son motif et notifie le titulaire, sans nommer le collaborateur. Le code du QR n'apparaît ni au
journal, ni dans la fiche.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.admin.models import JournalAudit
from app.cartes.models import Carte
from app.cartes.schemas import CarteAdmin, EvenementCarte
from app.cartes.service import etat_de
from app.notifications.service import notifier

ACTIONS = ("carte_suspendue", "carte_reactivee")


class Introuvable(Exception):
    pass


class Refus(Exception):
    pass


async def carte_admin(db: AsyncSession, utilisateur_id: UUID) -> CarteAdmin | None:
    carte = await db.scalar(select(Carte).where(Carte.utilisateur_id == utilisateur_id))
    if carte is None:
        return None
    etat = await etat_de(db, carte)
    entrees = await db.scalars(
        select(JournalAudit)
        .where(
            JournalAudit.cible_type == "carte", JournalAudit.cible_id == str(carte.id), JournalAudit.action.in_(ACTIONS)
        )
        .order_by(JournalAudit.quand.desc())
    )
    historique = [EvenementCarte(action=e.action, le=e.quand, motif=e.details.get("motif")) for e in entrees]  # type: ignore[arg-type]
    historique.append(EvenementCarte(action="carte_delivree", le=carte.delivree_le))
    return CarteAdmin(
        type=etat.type,
        numero=etat.numero,
        valide=etat.valide,
        cause=etat.cause,
        club=etat.club,
        delivree_le=etat.delivree_le,
        suspendue_le=etat.suspendue_le,
        motif_suspension=etat.motif_suspension,
        historique=historique,
    )


async def _verrouiller(db: AsyncSession, utilisateur_id: UUID) -> Carte:
    carte = await db.scalar(select(Carte).where(Carte.utilisateur_id == utilisateur_id).with_for_update())
    if carte is None:
        raise Introuvable
    return carte


async def suspendre(db: AsyncSession, acces: Acces, utilisateur_id: UUID, motif: str, ip: str) -> CarteAdmin:
    carte = await _verrouiller(db, utilisateur_id)
    if carte.suspendue_le is not None:
        raise Refus("Cette carte est déjà suspendue par l'équipe.")
    carte.suspendue_le = datetime.now(UTC)
    carte.suspendue_par = acces.utilisateur.id
    carte.motif_suspension = motif
    journaliser(
        db, "carte_suspendue", acces.utilisateur, cible_type="carte", cible_id=carte.id,
        details={"motif": motif, "numero": carte.numero, "titulaire": str(utilisateur_id)}, adresse_ip=ip,
    )  # fmt: skip
    notifier(
        db, utilisateur_id, "carte_suspendue", "Ta carte a été suspendue par l'équipe des Clubs Santé",
        "Contacte l'équipe nationale des Clubs Santé pour en savoir plus.", lien="/ma-carte",
    )  # fmt: skip
    await db.commit()
    resultat = await carte_admin(db, utilisateur_id)
    assert resultat is not None
    return resultat


async def reactiver(db: AsyncSession, acces: Acces, utilisateur_id: UUID, motif: str, ip: str) -> CarteAdmin:
    carte = await _verrouiller(db, utilisateur_id)
    if carte.suspendue_le is None:
        raise Refus("Cette carte n'est pas suspendue par l'équipe.")
    carte.suspendue_le = None
    carte.suspendue_par = None
    carte.motif_suspension = None
    journaliser(
        db, "carte_reactivee", acces.utilisateur, cible_type="carte", cible_id=carte.id,
        details={"motif": motif, "numero": carte.numero, "titulaire": str(utilisateur_id)}, adresse_ip=ip,
    )  # fmt: skip
    notifier(db, utilisateur_id, "carte_reactivee", "Ta carte est de nouveau valide", lien="/ma-carte")
    await db.commit()
    resultat = await carte_admin(db, utilisateur_id)
    assert resultat is not None
    return resultat
