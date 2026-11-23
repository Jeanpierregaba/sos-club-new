"""Page « Activité » de l'admin (spec 051) : réservée au super-administrateur, bloc par bloc, avec export CSV."""

import csv
import io
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite import indicateurs, service
from app.activite.schemas_admin import Bloc, NomBloc
from app.admin.dependances import Acces, adresse_ip, exiger_super_admin_pour
from app.admin.journal import journaliser
from app.db import get_session

Base = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_super_admin_pour("activite:voir"))]
Exportateur = Annotated[Acces, Depends(exiger_super_admin_pour("activite:exporter"))]

router_admin = APIRouter(prefix="/admin/activite", tags=["admin"])

DUREE_MAX = 366
PAR_DEFAUT = 30


def periode(du: date | None, au: date | None) -> indicateurs.Periode:
    """Par défaut les 30 derniers jours ; au plus 366 jours, jamais dans le futur."""
    aujourdhui = service.aujourdhui()
    fin = min(au or aujourdhui, aujourdhui)
    debut = du or fin - timedelta(days=PAR_DEFAUT - 1)
    if debut > fin:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "La date de début doit précéder la date de fin.")
    if (fin - debut).days + 1 > DUREE_MAX:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choisis une période d'au plus 366 jours.")
    return indicateurs.Periode(debut, fin)


Du = Annotated[date | None, Query()]
Au = Annotated[date | None, Query()]


@router_admin.get("/{bloc}", response_model=Bloc)
async def lire_bloc(bloc: NomBloc, _: Lecteur, db: Base, du: Du = None, au: Au = None) -> Bloc:
    return await indicateurs.calculer(db, bloc, periode(du, au), service.aujourdhui())


def _cellule(valeur: object) -> object:
    """Un entier s'écrit sans « ,0 » ; une valeur absente, vide."""
    if isinstance(valeur, float) and valeur.is_integer():
        return int(valeur)
    return "" if valeur is None else valeur


def _csv(bloc: Bloc) -> str:
    """Les chiffres puis chaque tableau, l'un sous l'autre : des totaux seulement, jamais une ligne par personne."""
    sortie = io.StringIO()
    ecrire = csv.writer(sortie, delimiter=";")
    ecrire.writerow([f"Activité : {bloc.bloc}", f"du {bloc.du.isoformat()} au {bloc.au.isoformat()}"])
    ecrire.writerow([])
    ecrire.writerow(["Indicateur", "Valeur", "Période précédente"])
    for chiffre in bloc.chiffres:
        ecrire.writerow([chiffre.libelle, _cellule(chiffre.valeur), _cellule(chiffre.precedent)])
    for tableau in bloc.tableaux:
        ecrire.writerow([])
        ecrire.writerow([tableau.titre])
        ecrire.writerow([c.libelle or c.cle for c in tableau.colonnes])
        for ligne in tableau.lignes:
            ecrire.writerow([_cellule(ligne.get(c.cle)) for c in tableau.colonnes])
    for serie in bloc.series:
        ecrire.writerow([])
        ecrire.writerow([serie.libelle])
        for point in serie.points:
            ecrire.writerow([point.jour.isoformat(), _cellule(point.valeur)])
    return sortie.getvalue()


@router_admin.get("/{bloc}/export.csv", response_class=Response)
async def exporter_bloc(
    bloc: NomBloc, acces: Exportateur, request: Request, db: Base, du: Du = None, au: Au = None
) -> Response:
    p = periode(du, au)
    resultat = await indicateurs.calculer(db, bloc, p, service.aujourdhui())
    journaliser(
        db, "activite_exportee", acces.utilisateur, cible_type="activite", cible_id=bloc,
        details={"du": p.du.isoformat(), "au": p.au.isoformat()}, adresse_ip=adresse_ip(request),
    )  # fmt: skip
    await db.commit()
    nom = f"activite-{bloc}-{p.du.isoformat()}-{p.au.isoformat()}.csv"
    # Le BOM fait lire les accents à Excel.
    return Response(
        "﻿" + _csv(resultat),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nom}"'},
    )
