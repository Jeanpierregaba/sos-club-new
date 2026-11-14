"""Échéances des régularisations (spec 033) : `python -m app.clubs.echeances`, lancée chaque jour par le cron du VPS.

Un club en régularisation dont l'échéance est passée est recalculé (il passe « suspendu » s'il n'a pas retrouvé son
seuil) ; sinon ses encadreurs reçoivent un rappel à J+7 puis à J+14. La commande est idempotente : chaque club est
traité sous son verrou, et un rappel déjà parti n'est jamais renvoyé. Sans elle, l'affichage reste juste (statut
effectif) ; seuls les rappels manquent.
"""

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Club, EtatClub
from app.db import SessionLocal
from app.notifications.service import notifier

logger = logging.getLogger(__name__)

RAPPELS = (timedelta(days=7), timedelta(days=14))


@dataclass
class Bilan:
    suspendus: int = 0
    rappels: int = 0


async def _rappel(db: AsyncSession, club: Club, instant: datetime) -> bool:
    assert club.regularisation_jusquau is not None
    ouverture = club.regularisation_jusquau - activation.DELAI_REGULARISATION
    dus = sum(1 for delai in RAPPELS if instant >= ouverture + delai)
    if dus <= club.rappels_envoyes:
        return False
    club.rappels_envoyes = dus
    # Arrondi au jour supérieur : à moins de 24 h de l'échéance, il reste encore « 1 jour », jamais « 0 ».
    restant = max(math.ceil((club.regularisation_jusquau - instant).total_seconds() / 86400), 1)
    message = (
        f"Il reste {restant} jour{'s' if restant > 1 else ''} au club pour retrouver 3 encadreurs et 21 élèves, "
        f"avant le {club.regularisation_jusquau.strftime('%d/%m/%Y')}. Sinon il sera suspendu."
    )
    for utilisateur_id in await activation.destinataires(db, club):
        notifier(db, utilisateur_id, "club_rappel_regularisation", f"{club.nom} : rappel", message, activation.LIEN)
    return True


async def traiter(db: AsyncSession) -> Bilan:
    bilan = Bilan()
    ids = list(await db.scalars(select(Club.id).where(Club.etat == EtatClub.en_regularisation)))
    for club_id in ids:
        instant = activation.maintenant()
        club = await db.scalar(
            select(Club).where(Club.id == club_id).with_for_update().execution_options(populate_existing=True)
        )
        if club is None or club.etat is not EtatClub.en_regularisation or club.regularisation_jusquau is None:
            await db.rollback()
            continue
        if club.regularisation_jusquau <= instant:
            if await activation.recalculer(db, club.id, "echeance") is EtatClub.suspendu:
                bilan.suspendus += 1
        elif await _rappel(db, club, instant):
            bilan.rappels += 1
        await db.commit()
    return bilan


async def _main() -> None:
    async with SessionLocal() as db:
        bilan = await traiter(db)
    logger.info("Échéances des clubs : %s suspendu(s), %s rappel(s).", bilan.suspendus, bilan.rappels)
    print(f"Échéances des clubs : {bilan.suspendus} suspendu(s), {bilan.rappels} rappel(s).")


if __name__ == "__main__":
    asyncio.run(_main())
