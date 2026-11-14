"""Routes du référentiel (spec 016) : listes publiques, sans compte, et administration sous /admin/referentiel."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission, exiger_super_admin_pour, refuser
from app.db import get_session
from app.referentiel import administration, service
from app.referentiel.models import OrdreEnseignement, StatutEtablissement, TypeEtablissement
from app.referentiel.normalisation import normaliser
from app.referentiel.schemas import (
    AxeAdmin,
    AxeCreation,
    AxeModification,
    AxePublic,
    DreAdmin,
    DreAnnuaire,
    DreCreation,
    DreModification,
    DrePublique,
    EtablissementAdmin,
    EtablissementCreation,
    EtablissementModification,
    EtablissementTrouve,
    IesgAdmin,
    IesgCreation,
    IesgModification,
    PageEtablissements,
    Remplacement,
)

Base = Annotated[AsyncSession, Depends(get_session)]

router_public = APIRouter(prefix="/referentiel", tags=["referentiel"])


@router_public.get("/dre")
async def lister_dre(db: Base) -> list[DrePublique]:
    return await service.lister_dre(db)


@router_public.get("/annuaire")
async def annuaire(db: Base) -> list[DreAnnuaire]:
    return await service.annuaire(db)


@router_public.get("/etablissements")
async def chercher_etablissements(
    db: Base,
    iesg: UUID | None = None,
    recherche: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    dre: Annotated[str | None, Query(max_length=30)] = None,
) -> list[EtablissementTrouve]:
    """`iesg` : tous les établissements de l'inspection ; `recherche` : 20 résultats au plus. L'un des deux est requis."""
    # Compté après normalisation : deux accents seuls ne font pas une recherche.
    if iesg is None and (recherche is None or len(normaliser(recherche).replace(" ", "")) < 2):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Tape au moins 2 lettres ou choisis une inspection.")
    return await service.chercher_etablissements(db, iesg_id=iesg, recherche=recherche, dre_code=dre)


@router_public.get("/axes")
async def lister_axes(db: Base) -> list[AxePublic]:
    return await service.lister_axes(db)


# Administration ----------------------------------------------------------------------------------------------

router_admin = APIRouter(prefix="/admin/referentiel", tags=["admin"])

Lecteur = Annotated[Acces, Depends(exiger_permission("clubs", Action.consulter))]
Createur = Annotated[Acces, Depends(exiger_permission("clubs", Action.creer))]
Modificateur = Annotated[Acces, Depends(exiger_permission("clubs", Action.modifier))]
# Les DRE, IESG et axes sont des paramètres nationaux (CDC admin, 3) : réservés au super-administrateur.
SuperAdmin = Annotated[Acces, Depends(exiger_super_admin_pour("referentiel:administrer"))]


@asynccontextmanager
async def _traduire_refus(db: AsyncSession, request: Request, acces: Acces, droit: str) -> AsyncIterator[None]:
    try:
        yield
    except administration.HorsPerimetre:
        # Levé avant toute modification : le refus est seul dans la transaction qu'il valide.
        await refuser(db, request, acces, droit)
    except administration.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Élément introuvable.") from None
    except administration.Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_admin.get("/dre")
async def admin_lister_dre(acces: Lecteur, db: Base) -> list[DreAdmin]:
    return await administration.lister_dre(db, acces)


@router_admin.post("/dre", status_code=status.HTTP_201_CREATED)
async def admin_creer_dre(entree: DreCreation, request: Request, acces: SuperAdmin, db: Base) -> DreAdmin:
    async with _traduire_refus(db, request, acces, "referentiel:administrer"):
        return await administration.creer_dre(db, acces, entree, adresse_ip(request))


@router_admin.patch("/dre/{code}")
async def admin_modifier_dre(
    code: str, entree: DreModification, request: Request, acces: SuperAdmin, db: Base
) -> DreAdmin:
    async with _traduire_refus(db, request, acces, "referentiel:administrer"):
        return await administration.modifier_dre(db, acces, code, entree, adresse_ip(request))


@router_admin.post("/iesg", status_code=status.HTTP_201_CREATED)
async def admin_creer_iesg(entree: IesgCreation, request: Request, acces: SuperAdmin, db: Base) -> IesgAdmin:
    async with _traduire_refus(db, request, acces, "referentiel:administrer"):
        return await administration.creer_iesg(db, acces, entree, adresse_ip(request))


@router_admin.patch("/iesg/{iesg_id}")
async def admin_modifier_iesg(
    iesg_id: UUID, entree: IesgModification, request: Request, acces: SuperAdmin, db: Base
) -> IesgAdmin:
    async with _traduire_refus(db, request, acces, "referentiel:administrer"):
        return await administration.modifier_iesg(db, acces, iesg_id, entree, adresse_ip(request))


@router_admin.get("/etablissements")
async def admin_lister_etablissements(
    acces: Lecteur,
    db: Base,
    recherche: Annotated[str | None, Query(max_length=100)] = None,
    dre: Annotated[str | None, Query(max_length=30)] = None,
    iesg: UUID | None = None,
    type: TypeEtablissement | None = None,
    statut: StatutEtablissement | None = None,
    ordre: OrdreEnseignement | None = None,
    prefecture: Annotated[str | None, Query(max_length=100)] = None,
    importes: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    par_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PageEtablissements:
    return await administration.lister_etablissements(
        db,
        acces,
        recherche=recherche,
        dre_code=dre,
        iesg_id=iesg,
        type_=type,
        statut=statut,
        page=page,
        par_page=par_page,
        ordre=ordre,
        prefecture=prefecture,
        importes=importes,
    )


@router_admin.post("/etablissements", status_code=status.HTTP_201_CREATED)
async def admin_creer_etablissement(
    entree: EtablissementCreation, request: Request, acces: Createur, db: Base
) -> EtablissementAdmin:
    async with _traduire_refus(db, request, acces, "clubs:creer"):
        return await administration.creer_etablissement(db, acces, entree, adresse_ip(request))


@router_admin.patch("/etablissements/{etablissement_id}")
async def admin_modifier_etablissement(
    etablissement_id: UUID, entree: EtablissementModification, request: Request, acces: Modificateur, db: Base
) -> EtablissementAdmin:
    async with _traduire_refus(db, request, acces, "clubs:modifier"):
        return await administration.modifier_etablissement(db, acces, etablissement_id, entree, adresse_ip(request))


@router_admin.post("/etablissements/{etablissement_id}/remplacer")
async def admin_remplacer_proposition(
    etablissement_id: UUID, entree: Remplacement, request: Request, acces: Modificateur, db: Base
) -> EtablissementAdmin:
    async with _traduire_refus(db, request, acces, "clubs:modifier"):
        return await administration.remplacer_proposition(db, acces, etablissement_id, entree, adresse_ip(request))


@router_admin.get("/axes")
async def admin_lister_axes(_: Lecteur, db: Base) -> list[AxeAdmin]:
    return await administration.lister_axes(db)


@router_admin.post("/axes", status_code=status.HTTP_201_CREATED)
async def admin_creer_axe(entree: AxeCreation, request: Request, acces: SuperAdmin, db: Base) -> AxeAdmin:
    async with _traduire_refus(db, request, acces, "referentiel:administrer"):
        return await administration.creer_axe(db, acces, entree, adresse_ip(request))


@router_admin.patch("/axes/{code}")
async def admin_modifier_axe(
    code: str, entree: AxeModification, request: Request, acces: SuperAdmin, db: Base
) -> AxeAdmin:
    async with _traduire_refus(db, request, acces, "referentiel:administrer"):
        return await administration.modifier_axe(db, acces, code, entree, adresse_ip(request))
