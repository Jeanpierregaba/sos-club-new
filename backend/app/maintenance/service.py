"""Lecture et écriture du mode maintenance (spec 047), avec cache mémoire court par processus."""

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.maintenance.models import EtatSite

TTL_CACHE = 5.0


@dataclass
class EtatCache:
    maintenance_active: bool
    expire_a: float


_cache: EtatCache | None = None


def _lire_cache() -> bool | None:
    if _cache is None or _cache.expire_a <= time.monotonic():
        return None
    return _cache.maintenance_active


def _ecrire_cache(maintenance_active: bool) -> None:
    global _cache
    _cache = EtatCache(maintenance_active=maintenance_active, expire_a=time.monotonic() + TTL_CACHE)


def invalider_cache() -> None:
    global _cache
    _cache = None


async def etat_actuel(db: AsyncSession) -> EtatSite:
    etat = await db.scalar(select(EtatSite).where(EtatSite.id == 1))
    if etat is None:
        # Filet de sécurité si la ligne singleton manque (migration incomplète) : on considère le site ouvert.
        return EtatSite(id=1, maintenance_active=False, active_le=None, active_par_id=None)
    return etat


async def maintenance_active(db: AsyncSession) -> bool:
    en_cache = _lire_cache()
    if en_cache is not None:
        return en_cache
    etat = await etat_actuel(db)
    _ecrire_cache(etat.maintenance_active)
    return etat.maintenance_active


async def definir_maintenance(db: AsyncSession, active: bool, utilisateur_id: UUID | None) -> EtatSite:
    # La ligne singleton peut manquer (base de test vidée, restauration partielle) : on la recrée.
    etat = await db.get(EtatSite, 1)
    if etat is None:
        etat = EtatSite(id=1, maintenance_active=False)
        db.add(etat)
    etat.maintenance_active = active
    etat.active_le = datetime.now(UTC) if active else None
    etat.active_par_id = utilisateur_id if active else None
    await db.flush()
    _ecrire_cache(etat.maintenance_active)
    return etat
