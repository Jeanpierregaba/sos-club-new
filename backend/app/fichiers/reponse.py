"""Réponse HTTP d'une image servie par l'API (ADR-0010)."""

from fastapi import Response

TYPE_IMAGE = "image/webp"


def image(octets: bytes, *, publique: bool) -> Response:
    """Une photo publique ne change jamais sous sa clé : elle se garde un an. Une photo privée ne se garde nulle part."""
    return Response(
        content=octets,
        media_type=TYPE_IMAGE,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable" if publique else "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
