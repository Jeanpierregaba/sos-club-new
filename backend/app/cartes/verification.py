"""Vérification publique d'une carte par le code de son QR (spec 040, Q30).

Seul le code secret de 192 bits ouvre une carte : jamais le numéro imprimé, qui se devine. La limite par adresse IP
n'est qu'une défense en profondeur contre les essais en masse.
"""

import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartes.models import FORMAT_CODE, Carte
from app.cartes.schemas import VerificationCarte
from app.cartes.service import etat_de
from app.comptes import limite_adresse
from app.config import settings

FORME = re.compile(FORMAT_CODE)


async def limiter(db: AsyncSession, adresse_ip: str) -> None:
    await limite_adresse.limiter(db, "CARTE", adresse_ip, settings.verifications_carte_max_adresse)


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
