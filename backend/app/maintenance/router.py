"""Routes du mode maintenance (spec 047)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces, adresse_ip, exiger_super_admin_pour
from app.admin.journal import journaliser
from app.db import get_session
from app.maintenance import service
from app.maintenance.schemas import EtatMaintenance, EtatSitePublic, MiseAJourMaintenance

Base = Annotated[AsyncSession, Depends(get_session)]
SuperAdminMaintenance = Annotated[Acces, Depends(exiger_super_admin_pour("maintenance:gerer"))]

router = APIRouter(tags=["maintenance"])
router_admin = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/etat-site", response_model=EtatSitePublic)
async def etat_site(db: Base) -> EtatSitePublic:
    """Indique au client si la maintenance est active. Exempté de la garde de maintenance."""
    return EtatSitePublic(maintenance=await service.maintenance_active(db))


@router_admin.get("/maintenance", response_model=EtatMaintenance)
async def lire_maintenance(_: SuperAdminMaintenance, db: Base) -> EtatMaintenance:
    etat = await service.etat_actuel(db)
    return EtatMaintenance.model_validate(etat)


@router_admin.put("/maintenance", response_model=EtatMaintenance)
async def changer_maintenance(
    entree: MiseAJourMaintenance, acces: SuperAdminMaintenance, db: Base, request: Request
) -> EtatMaintenance:
    actuel = await service.etat_actuel(db)
    if actuel.maintenance_active != entree.maintenance_active:
        etat = await service.definir_maintenance(db, entree.maintenance_active, acces.utilisateur.id)
        journaliser(
            db,
            "maintenance_activee" if entree.maintenance_active else "maintenance_desactivee",
            acces.utilisateur,
            cible_type="etat_site",
            cible_id="1",
            adresse_ip=adresse_ip(request),
        )
        await db.commit()
        service._ecrire_cache(etat.maintenance_active)
    else:
        etat = actuel
        service._ecrire_cache(etat.maintenance_active)
    return EtatMaintenance.model_validate(etat)
