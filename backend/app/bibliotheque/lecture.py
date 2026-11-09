"""Lecture des fichiers de la bibliothèque (spec 028), pour la relecture de l'équipe comme pour le public.

Le PDF part en flux, par morceaux, avec sa taille : il ne passe jamais en entier par la mémoire. Rien n'est gardé
en cache : une ressource dépubliée cesse aussitôt d'être servie. Le type exact et `nosniff` empêchent le
navigateur de le traiter comme une page du site.
"""

import re
import unicodedata

from fastapi import HTTPException, Response, status
from fastapi.responses import StreamingResponse

from app.bibliotheque.models import Ressource
from app.fichiers.stockage import StockageIndisponible, stockage

INTROUVABLE = "Ce document est introuvable."
INDISPONIBLE = "La bibliothèque est indisponible pour le moment : réessaie plus tard."
TAILLES = ("grande", "vignette")


def nom_de_fichier(titre: str) -> str:
    """Le titre en minuscules, sans accent ni caractère spécial : « Guide d'action n° 2 » → guide-d-action-n-2.pdf."""
    ascii_seul = unicodedata.normalize("NFKD", titre).encode("ascii", "ignore").decode()
    nom = re.sub(r"[^a-z0-9]+", "-", ascii_seul.lower()).strip("-")[:80].strip("-")
    return f"{nom or 'document'}.pdf"


async def pdf(ressource: Ressource, *, telecharger: bool) -> StreamingResponse:
    if ressource.fichier_cle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INTROUVABLE)
    try:
        flux = await stockage().lire_par_morceaux(ressource.fichier_cle)
    except StockageIndisponible:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, INDISPONIBLE) from None
    if flux is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INTROUVABLE)
    taille, morceaux = flux
    disposition = "attachment" if telecharger else "inline"
    return StreamingResponse(
        morceaux,
        media_type="application/pdf",
        headers={
            "Content-Length": str(taille),
            "Content-Disposition": f'{disposition}; filename="{nom_de_fichier(ressource.titre)}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )


async def couverture(ressource: Ressource, taille: str) -> Response:
    cle = ressource.couverture_grande if taille == "grande" else ressource.couverture_vignette
    if taille not in TAILLES or cle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INTROUVABLE)
    try:
        octets = await stockage().lire(cle)
    except StockageIndisponible:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, INDISPONIBLE) from None
    if octets is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INTROUVABLE)
    return Response(
        content=octets,
        media_type="image/webp",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
