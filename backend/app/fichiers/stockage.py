"""Stockage des fichiers (ADR-0010) : sur le disque du VPS, derrière une seule interface.

Passer à un stockage S3 revient à écrire une seconde implémentation de `Stockage` : les domaines ne connaissent
que `enregistrer`, `lire`, `lire_par_morceaux` et `supprimer`. Les clés sont toujours tirées par l'API
(`photos/<uuid>-<taille>.webp`, `ressources/<uuid>-document.pdf`) : aucun nom choisi par un utilisateur n'arrive sur
le disque.
"""

import asyncio
import os
import re
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

from app.config import settings

FORMAT_CLE = re.compile(r"^[a-z]+/[0-9a-f-]{36}-[a-z]+\.(webp|pdf)$")


class CleInvalide(ValueError):
    pass


class StockageIndisponible(Exception):
    """Disque plein ou inaccessible : l'API répond 503, rien n'est enregistré."""


class Stockage(Protocol):
    async def enregistrer(self, cle: str, octets: bytes) -> None: ...
    async def lire(self, cle: str) -> bytes | None: ...
    async def lire_par_morceaux(self, cle: str) -> tuple[int, AsyncIterator[bytes]] | None: ...
    async def supprimer(self, cle: str) -> None: ...


class Disque:
    # Taille des morceaux d'une lecture en flux : un PDF de 20 Mo ne passe jamais en entier par la mémoire.
    MORCEAU = 256 * 1024

    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def _chemin(self, cle: str) -> Path:
        if not FORMAT_CLE.fullmatch(cle):
            raise CleInvalide(cle)
        return self.racine / cle

    def _ecrire(self, chemin: Path, octets: bytes) -> None:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        # Fichier temporaire dans le même dossier puis renommage : jamais de fichier à moitié écrit.
        descripteur, temporaire = tempfile.mkstemp(dir=chemin.parent, prefix=".envoi-")
        try:
            with os.fdopen(descripteur, "wb") as sortie:
                sortie.write(octets)
                sortie.flush()
                os.fsync(sortie.fileno())
            os.replace(temporaire, chemin)
        except BaseException:
            Path(temporaire).unlink(missing_ok=True)
            raise

    async def enregistrer(self, cle: str, octets: bytes) -> None:
        chemin = self._chemin(cle)
        try:
            await asyncio.to_thread(self._ecrire, chemin, octets)
        except OSError as erreur:
            raise StockageIndisponible from erreur

    async def lire(self, cle: str) -> bytes | None:
        chemin = self._chemin(cle)
        try:
            return await asyncio.to_thread(chemin.read_bytes)
        except FileNotFoundError:
            return None
        except OSError as erreur:
            raise StockageIndisponible from erreur

    async def lire_par_morceaux(self, cle: str) -> tuple[int, AsyncIterator[bytes]] | None:
        """La taille du fichier et ses morceaux ; le fichier reste ouvert jusqu'à la fin de la lecture."""
        chemin = self._chemin(cle)
        try:
            fichier = await asyncio.to_thread(chemin.open, "rb")
        except FileNotFoundError:
            return None
        except OSError as erreur:
            raise StockageIndisponible from erreur
        taille = os.fstat(fichier.fileno()).st_size
        morceau = self.MORCEAU

        async def morceaux() -> AsyncIterator[bytes]:
            try:
                while octets := await asyncio.to_thread(fichier.read, morceau):
                    yield octets
            finally:
                fichier.close()

        return taille, morceaux()

    async def supprimer(self, cle: str) -> None:
        await asyncio.to_thread(self._chemin(cle).unlink, missing_ok=True)


def stockage() -> Stockage:
    """Lu à chaque appel : les tests changent `settings.dossier_fichiers` pour un dossier temporaire."""
    return Disque(Path(settings.dossier_fichiers))
