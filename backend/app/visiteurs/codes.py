"""Code de confirmation de l'e-mail d'un visiteur (spec 030).

Six chiffres tirés par `secrets`, gardés sous forme d'empreinte Argon2 (un million de possibilités : une empreinte
rapide se casserait hors ligne). Valable 15 minutes, 5 essais faux l'annulent ; au plus un envoi par minute et
cinq par heure. Ni le code ni l'adresse n'entrent dans les journaux.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Utilisateur
from app.comptes.motdepasse import hacher, verifier, verifier_factice
from app.config import settings
from app.courriel import envoi, messages
from app.visiteurs.models import CodeConfirmation

DUREE = timedelta(minutes=15)
ESSAIS_MAX = 5
INTERVALLE = timedelta(minutes=1)
FENETRE = timedelta(hours=1)
ENVOIS_PAR_FENETRE = 5


class TropTot(Exception):
    """Un code vient de partir : attendre une minute."""


class TropDeCodes(Exception):
    """Cinq codes dans l'heure."""


def _maintenant() -> datetime:
    return datetime.now(UTC)


def code_de_test(code: str) -> str | None:
    """Hors production et sans SMTP, l'API renvoie le code pour pouvoir tester (comme le lien d'invitation)."""
    return None if settings.production or envoi.smtp_configure() else code


async def envoyer(db: AsyncSession, utilisateur: Utilisateur) -> str | None:
    """Tire un nouveau code, remplace le précédent et l'envoie. Lève TropTot, TropDeCodes ou EnvoiImpossible.
    N'enregistre rien : l'appelant valide la transaction. Renvoie le code de test, s'il y a lieu."""
    assert utilisateur.email
    maintenant = _maintenant()
    ligne = await db.get(CodeConfirmation, utilisateur.id, with_for_update=True)
    if ligne is not None:
        if maintenant - ligne.envoye_le < INTERVALLE:
            raise TropTot
        if maintenant - ligne.fenetre_le >= FENETRE:
            ligne.fenetre_le, ligne.envois = maintenant, 0
        if ligne.envois >= ENVOIS_PAR_FENETRE:
            raise TropDeCodes
    else:
        ligne = CodeConfirmation(utilisateur_id=utilisateur.id, envois=0, fenetre_le=maintenant)
        db.add(ligne)
    code = f"{secrets.randbelow(10**6):06d}"
    ligne.code_hash = await hacher(code)
    ligne.expire_le = maintenant + DUREE
    ligne.essais = 0
    ligne.envoye_le = maintenant
    ligne.envois += 1
    courriel = messages.code_visiteur(utilisateur.prenom, code, int(DUREE.total_seconds() // 60))
    await envoi.envoyer(utilisateur.email, courriel.sujet, courriel.texte, html=courriel.html)
    return code_de_test(code)


async def verifier_code(db: AsyncSession, utilisateur: Utilisateur | None, code: str) -> bool:
    """Vrai si le code est le bon et encore valable ; le code est alors consommé. Un essai faux est compté.
    Le temps de réponse ne dit pas si l'adresse existe."""
    propre = "".join(code.split())
    ligne = await db.get(CodeConfirmation, utilisateur.id, with_for_update=True) if utilisateur else None
    if ligne is None or ligne.essais >= ESSAIS_MAX or ligne.expire_le <= _maintenant():
        await verifier_factice(propre)
        return False
    if not await verifier(ligne.code_hash, propre):
        ligne.essais += 1
        return False
    await db.delete(ligne)
    return True
