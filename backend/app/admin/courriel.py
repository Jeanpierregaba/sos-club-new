"""Envoi des e-mails par SMTP, avec la bibliothèque standard. Hors production et sans SMTP configuré, le lien est
seulement écrit dans le terminal de l'API, pour pouvoir tester."""

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


class EnvoiImpossible(Exception):
    pass


def smtp_configure() -> bool:
    return bool(settings.smtp_hote and settings.smtp_expediteur)


def _envoyer(message: EmailMessage) -> None:
    contexte = ssl.create_default_context()
    if settings.smtp_securite == "ssl":
        serveur: smtplib.SMTP = smtplib.SMTP_SSL(
            settings.smtp_hote or "", settings.smtp_port, context=contexte, timeout=15
        )
    else:
        serveur = smtplib.SMTP(settings.smtp_hote or "", settings.smtp_port, timeout=15)
    with serveur:
        if settings.smtp_securite == "starttls":
            serveur.starttls(context=contexte)
        if settings.smtp_utilisateur:
            serveur.login(settings.smtp_utilisateur, settings.smtp_mot_de_passe or "")
        serveur.send_message(message)


async def envoyer(destinataire: str, sujet: str, texte: str) -> None:
    """Lève EnvoiImpossible si le message n'a pas pu partir. Le contenu n'est jamais écrit dans les journaux."""
    if not smtp_configure():
        if settings.production:
            raise EnvoiImpossible("SMTP non configuré")
        logger.warning("SMTP non configuré : e-mail non envoyé à %s. Contenu :\n%s", destinataire, texte)
        return
    message = EmailMessage()
    message["From"] = settings.smtp_expediteur
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(texte)
    try:
        await asyncio.to_thread(_envoyer, message)
    except (smtplib.SMTPException, OSError) as erreur:
        logger.error("Échec d'envoi d'e-mail (%s)", type(erreur).__name__)
        raise EnvoiImpossible from erreur


def texte_invitation(prenom: str, lien: str, heures: int, invite_par: str) -> str:
    return (
        f"Bonjour {prenom},\n\n"
        f"{invite_par} t'invite à rejoindre l'espace d'administration des Clubs Santé SOS Docteur TV.\n\n"
        f"Pour activer ton compte, ouvre ce lien et choisis ton identifiant et ton mot de passe :\n{lien}\n\n"
        f"Ce lien ne sert qu'une fois et expire dans {heures} heures. Aucun mot de passe ne t'est envoyé par e-mail.\n"
        "Si tu n'attendais pas cette invitation, ignore ce message.\n\n"
        "L'équipe nationale AIMES-AFRIQUE / SOS Docteur TV\n"
    )
