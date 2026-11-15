"""Les vidéos ne sont jamais hébergées : seul un identifiant YouTube est gardé (ADR-0005)."""

import re
from urllib.parse import parse_qs, urlsplit

IDENTIFIANT = re.compile(r"^[A-Za-z0-9_-]{11}$")
HOTES = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def identifiant_youtube(valeur: str) -> str:
    """L'identifiant d'une vidéo YouTube, depuis l'identifiant seul ou un lien youtube.com / youtu.be. Lève
    ValueError pour tout autre lien : jamais d'adresse libre ni de code d'intégration."""
    texte = valeur.strip()
    if IDENTIFIANT.match(texte):
        return texte
    lien = urlsplit(texte if "://" in texte else f"https://{texte}")
    if lien.scheme not in {"http", "https"} or (lien.hostname or "").lower() not in HOTES:
        raise ValueError("Seuls les liens YouTube sont acceptés.")
    if (lien.hostname or "").lower().endswith("youtu.be"):
        candidat = lien.path.strip("/").split("/")[0]
    elif lien.path in {"/watch", "/watch/"}:
        candidat = parse_qs(lien.query).get("v", [""])[0]
    else:
        morceaux = [m for m in lien.path.split("/") if m]
        candidat = morceaux[1] if len(morceaux) == 2 and morceaux[0] in {"shorts", "embed", "live"} else ""
    if not IDENTIFIANT.match(candidat):
        raise ValueError("Ce lien YouTube ne désigne pas une vidéo.")
    return candidat
