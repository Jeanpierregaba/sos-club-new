"""Double authentification par codes TOTP (RFC 6238) et codes de secours (ADR-0008)."""

import hashlib
import secrets
import time
from datetime import UTC, datetime

import pyotp
import segno
from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import CodeSecours, DoubleAuth
from app.comptes.models import Utilisateur
from app.config import settings

EMETTEUR = "Clubs Santé SOS Docteur TV"
NB_CODES_SECOURS = 10
# 16 caractères en base 32 : 80 bits d'aléa. Une empreinte SHA-256 suffit, aucune attaque par force brute
# n'en vient à bout, contrairement à un mot de passe choisi par une personne.
ALPHABET_SECOURS = "abcdefghijkmnpqrstuvwxyz23456789"


class DejaActive(Exception):
    pass


class EnrolementAbsent(Exception):
    pass


def _empreinte(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _normaliser(code: str) -> str:
    return code.replace(" ", "").replace("-", "").lower()


def _totp(double_auth: DoubleAuth) -> pyotp.TOTP:
    return pyotp.TOTP(settings.fernet().decrypt(double_auth.secret_chiffre.encode()).decode())


def generer_codes_secours() -> list[str]:
    codes = []
    for _ in range(NB_CODES_SECOURS):
        brut = "".join(secrets.choice(ALPHABET_SECOURS) for _ in range(16))
        codes.append("-".join(brut[i : i + 4] for i in range(0, 16, 4)))
    return codes


async def _remplacer_codes_secours(db: AsyncSession, utilisateur_id: object) -> list[str]:
    await db.execute(delete(CodeSecours).where(CodeSecours.utilisateur_id == utilisateur_id))
    codes = generer_codes_secours()
    for code in codes:
        db.add(CodeSecours(utilisateur_id=utilisateur_id, code_hash=_empreinte(_normaliser(code))))
    return codes


async def commencer_enrolement(db: AsyncSession, utilisateur: Utilisateur) -> tuple[str, str]:
    """Crée (ou recrée) un secret en attente de confirmation. Renvoie le secret, à saisir à la main au besoin, et
    le QR code en SVG. Valide la transaction."""
    actuelle = await db.get(DoubleAuth, utilisateur.id)
    if actuelle and actuelle.active_le:
        raise DejaActive
    secret = pyotp.random_base32()
    chiffre = settings.fernet().encrypt(secret.encode()).decode()
    if actuelle:
        actuelle.secret_chiffre = chiffre
        actuelle.dernier_pas = None
    else:
        db.add(DoubleAuth(utilisateur_id=utilisateur.id, secret_chiffre=chiffre))
    await db.commit()

    uri = pyotp.TOTP(secret).provisioning_uri(name=utilisateur.email or utilisateur.identifiant, issuer_name=EMETTEUR)
    svg = segno.make(uri, error="m").svg_inline(scale=5, border=2, dark="#1e3a6e")
    return secret, svg


async def _accepter_totp(db: AsyncSession, double_auth: DoubleAuth, code: str) -> bool:
    """Accepte le code du pas courant ou d'un pas voisin (décalage d'horloge). Un pas déjà utilisé est refusé :
    la mise à jour conditionnelle tranche même entre deux requêtes simultanées."""
    if not (len(code) == 6 and code.isdigit()):
        return False
    totp = _totp(double_auth)
    pas_courant = int(time.time()) // totp.interval
    for pas in (pas_courant, pas_courant - 1, pas_courant + 1):
        if secrets.compare_digest(totp.generate_otp(pas), code):
            resultat = await db.execute(
                update(DoubleAuth)
                .where(
                    DoubleAuth.utilisateur_id == double_auth.utilisateur_id,
                    or_(DoubleAuth.dernier_pas.is_(None), DoubleAuth.dernier_pas < pas),
                )
                .values(dernier_pas=pas)
            )
            return resultat.rowcount == 1
    return False


async def verifier_code(db: AsyncSession, utilisateur: Utilisateur, saisie: str) -> bool:
    """Code de l'application ou code de secours, pour une double authentification active. Ne valide pas la
    transaction : l'appelant le fait avec la suite de l'opération."""
    double_auth = await db.get(DoubleAuth, utilisateur.id)
    if double_auth is None or double_auth.active_le is None:
        return False
    code = _normaliser(saisie)
    if await _accepter_totp(db, double_auth, code):
        return True
    if len(code) != 16:
        return False
    resultat = await db.execute(
        update(CodeSecours)
        .where(
            CodeSecours.utilisateur_id == utilisateur.id,
            CodeSecours.code_hash == _empreinte(code),
            CodeSecours.utilise_le.is_(None),
        )
        .values(utilise_le=datetime.now(UTC))
    )
    return resultat.rowcount == 1


async def confirmer_enrolement(db: AsyncSession, utilisateur: Utilisateur, code: str) -> list[str] | None:
    """Active la double authentification si le code est juste. Renvoie les codes de secours, montrés une seule
    fois, ou None si le code est faux. Ne valide pas la transaction."""
    double_auth = await db.get(DoubleAuth, utilisateur.id)
    if double_auth is None:
        raise EnrolementAbsent
    if double_auth.active_le:
        raise DejaActive
    if not await _accepter_totp(db, double_auth, _normaliser(code)):
        return None
    double_auth.active_le = datetime.now(UTC)
    return await _remplacer_codes_secours(db, utilisateur.id)


async def regenerer_codes_secours(db: AsyncSession, utilisateur: Utilisateur) -> list[str]:
    return await _remplacer_codes_secours(db, utilisateur.id)


async def reinitialiser(db: AsyncSession, utilisateur_id: object) -> None:
    """Efface la double authentification : elle sera à réactiver à la prochaine connexion."""
    await db.execute(delete(CodeSecours).where(CodeSecours.utilisateur_id == utilisateur_id))
    await db.execute(delete(DoubleAuth).where(DoubleAuth.utilisateur_id == utilisateur_id))


async def double_auth_active(db: AsyncSession, utilisateur_id: object) -> bool:
    return bool(
        await db.scalar(
            select(DoubleAuth.utilisateur_id).where(
                DoubleAuth.utilisateur_id == utilisateur_id, DoubleAuth.active_le.is_not(None)
            )
        )
    )
