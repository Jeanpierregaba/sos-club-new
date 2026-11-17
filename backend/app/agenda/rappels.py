"""Rappel de la veille (spec 041) : `python -m app.agenda.rappels`, chaque matin par le cron du VPS.

Pour chaque événement de club publié, non annulé, qui a lieu demain (heure de Lomé), les membres qui ont répondu « Je
participe » reçoivent une notification. `rappel_pour` retient la date rappelée : relancer la commande n'envoie rien de
plus, et un report à un autre jour rouvre un rappel.
"""

import asyncio
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda.models import Evenement, Reponse, ReponseEvenement
from app.agenda.schemas import LOME
from app.agenda.service import lien_public, membres_actifs
from app.db import SessionLocal
from app.notifications.service import notifier


async def envoyer(db: AsyncSession, maintenant: datetime | None = None) -> int:
    """Envoie les rappels de demain ; renvoie le nombre d'événements rappelés. Valide la transaction."""
    instant = (maintenant or datetime.now(UTC)).astimezone(LOME)
    demain = instant.date() + timedelta(days=1)
    debut = datetime.combine(demain, time(0), LOME)
    fin = debut + timedelta(days=1)
    evenements = (
        await db.scalars(
            select(Evenement)
            .where(
                Evenement.publie,
                Evenement.club_id.is_not(None),
                Evenement.annule_le.is_(None),
                Evenement.debut >= debut,
                Evenement.debut < fin,
                Evenement.rappel_pour.is_distinct_from(demain),
            )
            .order_by(Evenement.debut)
            # Deux lancements simultanés ne rappellent pas deux fois le même événement.
            .with_for_update(skip_locked=True)
        )
    ).all()
    for evenement in evenements:
        assert evenement.club_id is not None
        participants = await db.scalars(
            select(ReponseEvenement.eleve_id).where(
                ReponseEvenement.evenement_id == evenement.id,
                ReponseEvenement.reponse == Reponse.participe,
                ReponseEvenement.eleve_id.in_(membres_actifs(evenement.club_id)),
            )
        )
        heure = evenement.debut.astimezone(LOME).strftime("%H h %M")
        for eleve_id in participants.all():
            notifier(
                db, eleve_id, "evenement_rappel", f"Demain à {heure} : {evenement.titre}"[:200],
                evenement.lieu or "En ligne", lien_public(evenement.id),
            )  # fmt: skip
        evenement.rappel_pour = demain
    await db.commit()
    return len(evenements)


async def _main() -> None:
    async with SessionLocal() as db:
        nombre = await envoyer(db)
    print(f"Rappels de l'agenda : {nombre} événement(s).")


if __name__ == "__main__":
    asyncio.run(_main())
