"""Envoi des e-mails par SMTP, avec la bibliothèque standard (spec 015, puis 030 pour le HTML).

Hors production et sans SMTP configuré, rien ne part : l'API renvoie alors le lien ou le code de test
(`lien_de_test`, `code_de_test`). Aucune adresse ni aucun contenu n'est journalisé.
"""

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


def composer(destinataire: str, sujet: str, texte: str, html: str | None = None) -> EmailMessage:
    """Texte brut toujours ; HTML en alternative quand il est fourni (multipart/alternative)."""
    message = EmailMessage()
    message["From"] = settings.smtp_expediteur
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(texte)
    if html is not None:
        message.add_alternative(html, subtype="html")
    return message


async def envoyer(destinataire: str, sujet: str, texte: str, html: str | None = None) -> None:
    """Lève EnvoiImpossible si le message n'a pas pu partir. Le contenu n'est jamais écrit dans les journaux."""
    if not smtp_configure():
        if settings.production:
            raise EnvoiImpossible("SMTP non configuré")
        logger.warning("SMTP non configuré : e-mail non envoyé.")
        return
    message = composer(destinataire, sujet, texte, html)
    try:
        await asyncio.to_thread(_envoyer, message)
    except (smtplib.SMTPException, OSError) as erreur:
        logger.error("Échec d'envoi d'e-mail (%s)", type(erreur).__name__)
        raise EnvoiImpossible from erreur
