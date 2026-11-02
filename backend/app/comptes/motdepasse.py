import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hacheur = PasswordHasher()
# Argon2 prend environ 64 Mio à chaque calcul : ce plafond protège la mémoire quand une classe se connecte en même temps.
_calculs = ThreadPoolExecutor(max_workers=4, thread_name_prefix="argon2")


async def _en_arriere_plan[T](fonction: Callable[..., T], *arguments: str) -> T:
    return await asyncio.get_running_loop().run_in_executor(_calculs, fonction, *arguments)


def _verifier(empreinte: str, mot_de_passe: str) -> bool:
    try:
        return _hacheur.verify(empreinte, mot_de_passe)
    except VerificationError, InvalidHashError:
        return False


@cache
def _empreinte_factice() -> str:
    return _hacheur.hash("empreinte-factice-pour-compte-inconnu")


async def hacher(mot_de_passe: str) -> str:
    return await _en_arriere_plan(_hacheur.hash, mot_de_passe)


async def verifier(empreinte: str, mot_de_passe: str) -> bool:
    return await _en_arriere_plan(_verifier, empreinte, mot_de_passe)


async def verifier_factice(mot_de_passe: str) -> bool:
    """Prend le même temps qu'une vraie vérification : un compte inconnu ne se repère pas au temps de réponse."""
    await _en_arriere_plan(_verifier, await _en_arriere_plan(_empreinte_factice), mot_de_passe)
    return False


def doit_rehacher(empreinte: str) -> bool:
    return _hacheur.check_needs_rehash(empreinte)
