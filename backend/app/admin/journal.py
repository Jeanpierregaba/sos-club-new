"""Seule porte d'écriture du journal d'audit. Le journal ne reçoit jamais de mot de passe, de jeton, de code
ni de secret : uniquement des identifiants, des libellés et des chiffres."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.comptes.models import Utilisateur


def libelle(utilisateur: Utilisateur) -> str:
    return f"{utilisateur.prenom} {utilisateur.nom} ({utilisateur.identifiant})"


def journaliser(
    db: AsyncSession,
    action: str,
    auteur: Utilisateur | None = None,
    *,
    cible_type: str | None = None,
    cible_id: UUID | str | None = None,
    perimetre: str | None = None,
    details: dict[str, Any] | None = None,
    adresse_ip: str | None = None,
) -> None:
    """Ajoute une entrée à la transaction en cours : elle est écrite avec l'opération qu'elle décrit, ou pas du tout."""
    db.add(
        JournalAudit(
            auteur_id=auteur.id if auteur else None,
            auteur_libelle=libelle(auteur) if auteur else None,
            action=action,
            cible_type=cible_type,
            cible_id=str(cible_id) if cible_id is not None else None,
            perimetre=perimetre,
            details=details or {},
            adresse_ip=adresse_ip,
        )
    )
