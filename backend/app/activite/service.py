"""Collecte anonyme des événements d'activité (spec 051, ADR-0014).

Le site envoie le type, le gabarit de la route et, à la première page, le référent ; l'API calcule seule l'empreinte
du jour, l'appareil, le navigateur et la provenance, puis jette l'adresse IP et le User-Agent. Rien n'est enregistré
pour un navigateur qui demande à ne pas être suivi, un robot ou un compte de l'équipe.
"""

import hashlib
import hmac
import json
import logging
import re
import secrets
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Request
from sqlalchemy import delete, insert, select
from sqlalchemy.dialects.postgresql import insert as insert_pg
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite.models import EvenementActivite, PresenceSemaine, SelActivite, TypeEvenement
from app.comptes.models import Role
from app.comptes.service import cle_adresse, utilisateur_de_la_session
from app.config import settings
from app.db import SessionLocal

journal = logging.getLogger(__name__)

# Appels de collecte par adresse et par fenêtre des essais (15 minutes) : large, une classe partage souvent une adresse.
PLAFOND = 600
CHEMINS = frozenset(json.loads((Path(__file__).parent / "chemins.json").read_text()))
AUTRE = "autre"

ROBOT = re.compile(
    r"bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp/|headless|lighthouse|curl/|wget/|python-|httpx",
    re.IGNORECASE,
)
MOTEURS = ("google.", "bing.", "duckduckgo.", "yahoo.", "ecosia.", "qwant.", "yandex.", "baidu.")
RESEAUX = (
    ("facebook", ("facebook.", "fb.", "fb.me", "messenger.")),
    ("whatsapp", ("whatsapp.", "wa.me")),
    ("tiktok", ("tiktok.",)),
    ("youtube", ("youtube.", "youtu.be")),
    ("instagram", ("instagram.",)),
    ("x", ("twitter.", "x.com", "t.co")),
    ("linkedin", ("linkedin.", "lnkd.in")),
)
UTM = re.compile(r"[a-z0-9][a-z0-9_-]{0,29}")


def maintenant() -> datetime:
    return datetime.now(UTC)


def aujourdhui() -> date:
    # Lomé est à UTC+0 toute l'année : le jour UTC est le jour local.
    return maintenant().date()


# Description de la requête ---------------------------------------------------------------------------------------


def appareil(agent: str) -> str:
    a = agent.lower()
    if "ipad" in a or "tablet" in a or ("android" in a and "mobile" not in a):
        return "tablette"
    if "mobi" in a or "iphone" in a or "android" in a:
        return "telephone"
    return "ordinateur"


def navigateur(agent: str) -> str:
    a = agent.lower()
    for nom, marques in (
        ("edge", ("edg/",)),
        ("opera", ("opr/", "opera")),
        ("samsung", ("samsungbrowser",)),
        ("firefox", ("firefox", "fxios")),
        ("chrome", ("crios", "chrome")),
        ("safari", ("safari",)),
    ):
        if any(m in a for m in marques):
            return nom
    return AUTRE


def _hote(referent: str) -> str | None:
    try:
        hote = urlsplit(referent).hostname
    except ValueError:
        return None
    return hote.removeprefix("www.").removeprefix("m.").removeprefix("l.") if hote else None


def provenance(referent: str | None, utm: str | None) -> str:
    """Une catégorie, jamais l'adresse : `direct`, `interne`, `recherche`, un réseau, `autre`, ou la campagne."""
    if utm and UTM.fullmatch(utm.strip().lower()):
        return utm.strip().lower()
    if not referent:
        return "direct"
    hote = _hote(referent)
    if hote is None:
        return AUTRE
    if hote == urlsplit(settings.site_origine).hostname:
        return "interne"
    if any(hote.startswith(m) or f".{m}" in f".{hote}" for m in MOTEURS):
        return "recherche"
    for reseau, domaines in RESEAUX:
        if any(hote == d or hote.startswith(d) or hote.endswith(f".{d}") for d in domaines):
            return reseau
    return AUTRE


def gabarit(chemin: str) -> str:
    """Le gabarit d'une route publique du site, sinon `autre` : un code ou un jeton n'est jamais gardé."""
    propre = chemin.split("?", 1)[0].split("#", 1)[0]
    if propre != "/" and propre.endswith("/"):
        propre = propre[:-1]
    return propre if propre in CHEMINS else AUTRE


PREMIER_SEGMENT = re.compile(r"/[a-z][a-z-]{1,38}[a-z]")


def segment_introuvable(chemin: str) -> str:
    """Pour une page introuvable : le premier segment s'il est fait de mots (un ancien lien), sinon `autre`."""
    propre = chemin.split("?", 1)[0].split("#", 1)[0]
    premier = "/" + propre.lstrip("/").split("/", 1)[0]
    reste = propre.lstrip("/").split("/", 1)[1:] if "/" in propre.lstrip("/") else []
    return premier if PREMIER_SEGMENT.fullmatch(premier) and not reste else AUTRE


# Exclusions et empreinte -----------------------------------------------------------------------------------------


def ne_pas_suivre(request: Request) -> bool:
    agent = request.headers.get("user-agent", "")
    return (
        request.headers.get("sec-gpc") == "1"
        or request.headers.get("dnt") == "1"
        or not agent
        or ROBOT.search(agent) is not None
    )


async def _connecte(db: AsyncSession, request: Request) -> bool | None:
    """True pour un compte, False pour un visiteur, None pour un compte de l'équipe (jamais compté)."""
    jeton = request.cookies.get(settings.cookie_session)
    utilisateur = await utilisateur_de_la_session(db, jeton) if jeton else None
    if utilisateur is None or utilisateur.role is Role.invite:
        return False
    return None if utilisateur.role is Role.admin else True


async def _sel(db: AsyncSession, jour: date) -> bytes:
    nouveau = await db.scalar(
        insert_pg(SelActivite)
        .values(jour=jour, sel=secrets.token_bytes(32))
        .on_conflict_do_nothing()
        .returning(SelActivite.sel)
    )
    if nouveau is not None:
        # Premier événement du jour : les sels passés ne servent plus et ne doivent plus exister.
        await db.execute(delete(SelActivite).where(SelActivite.jour < jour))
        return nouveau
    return await db.scalar(select(SelActivite.sel).where(SelActivite.jour == jour))


def _empreinte(sel: bytes, request: Request) -> str:
    adresse = cle_adresse(request.client.host if request.client else None)
    agent = request.headers.get("user-agent", "")
    return hmac.new(sel, f"{adresse}|{agent}".encode(), hashlib.sha256).hexdigest()[:16]


async def ecrire(
    db: AsyncSession,
    request: Request,
    type_: TypeEvenement,
    chemin: str,
    detail: str | None = None,
    *,
    referent: str | None = None,
    utm: str | None = None,
) -> bool:
    """Enregistre l'événement, déjà validé, sauf exclusion. Ne valide pas la transaction. Renvoie True s'il est écrit."""
    if ne_pas_suivre(request):
        return False
    connecte = await _connecte(db, request)
    if connecte is None:
        return False
    jour = aujourdhui()
    agent = request.headers.get("user-agent", "")
    await db.execute(
        insert(EvenementActivite).values(
            cree_le=maintenant(), jour=jour, type=type_, visiteur=_empreinte(await _sel(db, jour), request),
            chemin=chemin, detail=detail, provenance=provenance(referent, utm), appareil=appareil(agent),
            navigateur=navigateur(agent), connecte=connecte,
        )
    )  # fmt: skip
    return True


async def enregistrer(request: Request, type_: TypeEvenement, chemin: str, detail: str | None = None) -> None:
    """Pour les événements vus par l'API (étapes d'inscription, téléchargements, erreurs) : dans sa propre
    transaction, pour survivre au refus d'une action, et sans jamais lever : le suivi ne casse aucune action."""
    try:
        async with SessionLocal() as db:
            await ecrire(db, request, type_, chemin, detail[:60] if detail else None)
            await db.commit()
    except Exception:  # noqa: BLE001 - le suivi ne doit jamais faire échouer l'action de l'utilisateur
        journal.exception("Suivi d'activité : événement %s non enregistré", type_)


async def noter_presence(db: AsyncSession, utilisateur_id: object) -> None:
    """Une ligne par compte et par semaine (rétention), sans rien d'autre ; idempotente."""
    jour = aujourdhui()
    lundi = jour - timedelta(days=jour.weekday())
    await db.execute(
        insert_pg(PresenceSemaine).values(utilisateur_id=utilisateur_id, semaine=lundi).on_conflict_do_nothing()
    )
