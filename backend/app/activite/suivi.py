"""Événements vus par l'API elle-même (spec 051) : étapes d'inscription, téléchargements, erreurs, présence.

Chacun s'écrit dans sa propre transaction et n'échoue jamais : le suivi ne casse aucune action.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException, Request

from app.activite import service
from app.activite.models import TypeEvenement
from app.db import SessionLocal

journal = logging.getLogger(__name__)

# Le motif d'un refus, par code HTTP : jamais le message, qui peut citer une saisie.
MOTIFS = {
    400: "invalide",
    403: "fermees",
    404: "introuvable",
    409: "doublon",
    422: "invalide",
    429: "debit",
    503: "indisponible",
}


async def etape(request: Request, profil: str, nom: str) -> None:
    await service.enregistrer(request, TypeEvenement.etape_inscription, "/inscription", f"{profil}:{nom}")


@asynccontextmanager
async def suivre_inscription(
    request: Request, profil: str, reussite: str = "cree", *, debut: str | None = "envoye", refus: str = "refuse"
) -> AsyncIterator[None]:
    """Autour d'une route d'inscription : `debut`, puis `<refus>-<motif>` ou `reussite`."""
    if debut:
        await etape(request, profil, debut)
    try:
        yield
    except HTTPException as erreur:
        await etape(request, profil, f"{refus}-{MOTIFS.get(erreur.status_code, 'autre')}")
        raise
    except Exception:
        await etape(request, profil, f"{refus}-erreur")
        raise
    await etape(request, profil, reussite)


# Présence hebdomadaire (rétention) -------------------------------------------------------------------------------

# Les comptes déjà notés cette semaine dans ce processus : une écriture par compte et par semaine, pas par requête.
_notes: set[UUID] = set()
_semaine: list[date] = []


def oublier_presences() -> None:
    _notes.clear()
    _semaine.clear()


async def noter_presence(utilisateur_id: UUID) -> None:
    jour = service.aujourdhui()
    lundi = jour - timedelta(days=jour.weekday())
    if _semaine != [lundi]:
        oublier_presences()
        _semaine.append(lundi)
    if utilisateur_id in _notes:
        return
    try:
        async with SessionLocal() as db:
            await service.noter_presence(db, utilisateur_id)
            await db.commit()
        _notes.add(utilisateur_id)
    except Exception:  # noqa: BLE001 - le suivi ne doit jamais faire échouer la requête de l'utilisateur
        journal.exception("Suivi d'activité : présence non notée")
