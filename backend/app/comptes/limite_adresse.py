"""Plafond d'appels par adresse IP pour les routes publiques coûteuses ou sensibles (cartes, codes des visiteurs).

Même mécanisme que les demandes de lien (spec 039) : une ligne d'essai « en cours », qui ne compte jamais parmi les
échecs de connexion. La clé est en majuscules : aucune saisie d'identifiant, toujours mise en minuscules, ne peut la
produire pour bloquer une adresse à distance.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import TentativeConnexion
from app.comptes.service import empreinte
from app.config import settings


class PlafondAtteint(Exception):
    pass


async def limiter(db: AsyncSession, prefixe: str, adresse_ip: str, plafond: int) -> None:
    """Compte un appel de cette adresse sur la fenêtre des essais ; lève `PlafondAtteint` au-delà du plafond.
    Valide la transaction."""
    cle = empreinte(f"{prefixe.upper()}:{adresse_ip}")
    maintenant = datetime.now(UTC)
    # Les lignes de cette clé plus vieilles que la fenêtre ne servent plus : la route fait son ménage.
    await db.execute(
        delete(TentativeConnexion).where(
            TentativeConnexion.cle_hash == cle,
            TentativeConnexion.cree_le <= maintenant - timedelta(minutes=settings.fenetre_essais_minutes),
        )
    )
    nombre = await db.scalar(
        select(func.count()).select_from(TentativeConnexion).where(TentativeConnexion.cle_hash == cle)
    )
    # Une adresse au plafond n'écrit plus rien : elle ne peut pas remplir la table.
    if (nombre or 0) >= plafond:
        await db.commit()
        raise PlafondAtteint
    db.add(TentativeConnexion(cle_hash=cle, adresse_ip=f"{prefixe.lower()}:{adresse_ip}"[:45]))
    await db.commit()
