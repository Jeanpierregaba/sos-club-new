"""L'heure du serveur, seule juge du temps de réponse (ADR-0004). Les tests la remplacent."""

from datetime import UTC, datetime


def maintenant() -> datetime:
    return datetime.now(UTC)
