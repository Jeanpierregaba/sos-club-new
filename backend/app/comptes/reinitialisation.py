"""Réinitialisation du mot de passe d'un élève (specs 017 et 039, Q4), commune à l'équipe et à l'encadreur.

Le mot de passe provisoire est rendu une seule fois à celui qui l'a demandé : il n'est écrit ni au journal, ni dans
une notification, ni dans un e-mail. Les sessions de l'élève sont coupées et il est prévenu dans son espace.
"""

import secrets
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.comptes.models import Utilisateur
from app.comptes.motdepasse import hacher
from app.comptes.service import couper_sessions
from app.notifications.service import notifier

# Sans caractères qui se confondent à l'écrit ou à l'oral : 0 et o, 1, l et i.
ALPHABET_PROVISOIRE = "abcdefghjkmnpqrstuvwxyz23456789"
LONGUEUR_PROVISOIRE = 12
EQUIPE = "l'équipe des Clubs Santé"


def provisoire() -> str:
    return "".join(secrets.choice(ALPHABET_PROVISOIRE) for _ in range(LONGUEUR_PROVISOIRE))


async def reinitialiser(
    db: AsyncSession,
    eleve: Utilisateur,
    auteur: Utilisateur,
    motif: str,
    adresse_ip: str,
    *,
    par: str,
    details: dict[str, Any] | None = None,
) -> str:
    """`par` est le nom montré à l'élève : celui de l'encadreur, ou « l'équipe des Clubs Santé ». Ne valide pas la
    transaction : l'appelant le fait après ses propres contrôles."""
    mot_de_passe = provisoire()
    eleve.mot_de_passe_hash = await hacher(mot_de_passe)
    eleve.mot_de_passe_provisoire_le = datetime.now(UTC)
    await couper_sessions(db, eleve.id)
    notifier(
        db, eleve.id, "mot_de_passe_reinitialise", f"Ton mot de passe a été réinitialisé par {par}",
        "Choisis maintenant ton propre mot de passe dans ton espace. Si tu ne l'as pas demandé, préviens un "
        "encadreur ou l'équipe des Clubs Santé.",
        "/mon-espace",
    )  # fmt: skip
    journaliser(
        db, "mot_de_passe_reinitialise", auteur, cible_type="utilisateur", cible_id=eleve.id,
        details={"motif": motif, **(details or {})}, adresse_ip=adresse_ip,
    )  # fmt: skip
    return mot_de_passe
