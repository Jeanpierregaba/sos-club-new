"""Vérification publique d'une carte par le code de son QR (spec 040, Q30).

Seul le code secret de 192 bits ouvre une carte : jamais le numéro imprimé, qui se devine. La limite par adresse IP
n'est qu'une défense en profondeur contre les essais en masse.
"""

import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartes.models import FORMAT_CODE, Carte
from app.cartes.schemas import VerificationCarte
from app.cartes.service import etat_de
from app.comptes.models import TentativeConnexion
from app.comptes.service import empreinte
from app.config import settings

FORME = re.compile(FORMAT_CODE)


class TropDeVerifications(Exception):
    pass


async def limiter(db: AsyncSession, adresse_ip: str) -> None:
    """Même mécanisme que les demandes de lien (spec 039) : une ligne d'essai « en cours », qui ne compte jamais
    parmi les échecs de connexion. La clé est en majuscules : aucune saisie d'identifiant, toujours mise en
    minuscules, ne peut la produire pour bloquer une adresse à distance."""
    cle = empreinte(f"CARTE:{adresse_ip}")
    maintenant = datetime.now(UTC)
    # Les lignes de cette clé plus vieilles que la fenêtre ne servent plus : la route publique fait son ménage.
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
    if (nombre or 0) >= settings.verifications_carte_max_adresse:
        await db.commit()
        raise TropDeVerifications
    db.add(TentativeConnexion(cle_hash=cle, adresse_ip=f"carte:{adresse_ip}"[:45]))
    await db.commit()


async def verifier(db: AsyncSession, code: str) -> VerificationCarte | None:
    if not FORME.fullmatch(code):
        return None
    carte = await db.scalar(select(Carte).where(Carte.code == code))
    if carte is None:
        return None
    etat = await etat_de(db, carte)
    return VerificationCarte(
        type=etat.type,
        numero=etat.numero,
        club=etat.club,
        valide=etat.valide,
        verifiee_le=datetime.now(UTC),
    )
