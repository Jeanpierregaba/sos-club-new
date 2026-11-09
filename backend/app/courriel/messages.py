"""Les e-mails de la plateforme, tous rendus par le gabarit commun (spec 030)."""

from app.config import settings
from app.courriel.gabarit import Bouton, Courriel, rendre


def invitation(prenom: str, lien: str, heures: int, invite_par: str) -> Courriel:
    return rendre(
        "Ton accès à l'espace admin des Clubs Santé",
        surtitre="Espace administrateur",
        titre=("Bienvenue dans", "l'équipe"),
        salutation=f"Bonjour {prenom},",
        paragraphes=[
            f"{invite_par} t'invite à rejoindre l'espace d'administration des Clubs Santé SOS Docteur TV.",
            "Pour activer ton compte, ouvre ce lien et choisis ton identifiant et ton mot de passe.",
        ],
        bouton=Bouton("Activer mon compte", lien),
        apres=[
            f"Ce lien ne sert qu'une fois et expire dans {heures} heures.",
            "Aucun mot de passe ne t'est envoyé par e-mail.",
            "Si tu n'attendais pas cette invitation, ignore ce message.",
        ],
    )


def encadreur_active(prenom: str) -> Courriel:
    return rendre(
        "Ton compte encadreur est activé",
        surtitre="Compte encadreur",
        titre=("Ton compte est", "activé"),
        salutation=f"Bonjour {prenom},",
        paragraphes=["L'équipe des Clubs Santé a vérifié ton inscription : ton compte encadreur est maintenant actif."],
        bouton=Bouton("Me connecter", f"{settings.site_origine}/connexion"),
    )


def encadreur_refuse(prenom: str, motif: str) -> Courriel:
    return rendre(
        "Ton inscription d'encadreur",
        surtitre="Compte encadreur",
        titre=("Ton inscription", "à corriger"),
        salutation=f"Bonjour {prenom},",
        paragraphes=[
            "L'équipe des Clubs Santé n'a pas pu valider ton inscription d'encadreur, pour ce motif :",
            motif,
            "Tu peux corriger ton profil et renvoyer ta demande depuis ton espace.",
        ],
        bouton=Bouton("Ouvrir mon espace", f"{settings.site_origine}/mon-espace"),
    )


def code_visiteur(prenom: str, code: str, minutes: int) -> Courriel:
    return rendre(
        f"Ton code de confirmation : {code}",
        surtitre="Compte visiteur",
        titre=("Confirme ton", "adresse e-mail"),
        salutation=f"Bonjour {prenom},",
        paragraphes=["Voici ton code pour confirmer ton compte sur la plateforme des Clubs Santé SOS Docteur TV :"],
        code=code,
        apres=[
            f"Ce code est valable {minutes} minutes. Ne le donne à personne : l'équipe ne te le demandera jamais.",
            "Si tu n'as pas créé de compte, ignore ce message.",
        ],
    )
