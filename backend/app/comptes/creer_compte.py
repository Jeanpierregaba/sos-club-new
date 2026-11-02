"""Crée un compte en ligne de commande, en attendant les inscriptions depuis le site (specs 003 et 004).

Le mot de passe n'est jamais passé en argument : il finirait dans l'historique du terminal.
"""

import argparse
import asyncio
import getpass
import sys

from app.comptes.models import Role
from app.comptes.service import CompteInvalide, creer_compte
from app.db import SessionLocal, engine


def _lire_mot_de_passe() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline().rstrip("\r\n")
    mot_de_passe = getpass.getpass("Mot de passe : ")
    if getpass.getpass("Confirme le mot de passe : ") != mot_de_passe:
        raise CompteInvalide("Les deux mots de passe sont différents.")
    return mot_de_passe


async def _creer(arguments: argparse.Namespace, mot_de_passe: str) -> None:
    try:
        async with SessionLocal() as db:
            await creer_compte(
                db,
                role=Role(arguments.role),
                identifiant=arguments.identifiant,
                prenom=arguments.prenom,
                nom=arguments.nom,
                mot_de_passe=mot_de_passe,
                email=arguments.email,
                telephone=arguments.telephone,
            )
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Crée un compte sur la plateforme.")
    parser.add_argument("--role", required=True, choices=[role.value for role in Role])
    parser.add_argument("--identifiant", required=True)
    parser.add_argument("--prenom", required=True)
    parser.add_argument("--nom", required=True)
    parser.add_argument("--email")
    parser.add_argument("--telephone")
    arguments = parser.parse_args()

    try:
        asyncio.run(_creer(arguments, _lire_mot_de_passe()))
    except CompteInvalide as erreur:
        print(erreur, file=sys.stderr)
        return 1
    print(f"Compte {arguments.role} créé : {arguments.identifiant.strip().lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
