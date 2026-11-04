"""Le pseudonyme, seule identité publique d'un élève (Q20, docs/RULES.md).

Il ne doit permettre ni de joindre l'élève (e-mail, téléphone), ni de se faire passer pour l'équipe, ni d'insulter.
La liste des mots interdits est courte : l'admin peut toujours imposer un autre pseudonyme.
"""

import unicodedata

from app.referentiel.normalisation import normaliser

LONGUEUR_MIN = 3
LONGUEUR_MAX = 30
CHIFFRES_MAX = 5
PONCTUATION = " -."

# Comparés mot à mot, après normalisation : « con » n'interdit pas « Constance ».
MOTS_INTERDITS = frozenset(
    {
        "con", "conne", "connard", "connasse", "salope", "salaud", "pute", "putain", "merde", "encule", "batard",
        "nique", "niquer", "pd", "fdp", "ntm", "tg", "sexe", "sexy", "porno", "bite", "couille", "chienne",
        "admin", "administrateur", "administration", "moderateur", "moderation", "officiel", "equipe", "support",
    }
)  # fmt: skip
# Interdits même collés à d'autres lettres : ils sont assez longs pour ne pas toucher un prénom.
RACINES_INTERDITES = ("connard", "connasse", "salope", "putain", "encule", "batard", "porno", "superadmin",
                      "administrat", "moderat", "sosdocteur", "aimesafrique")  # fmt: skip


class PseudonymeInvalide(ValueError):
    pass


def cle(texte: str) -> str:
    """Clé d'unicité : sans accents, sans majuscules, sans espaces ni ponctuation. « Aya-K » et « aya k » sont le
    même pseudonyme, pour qu'un élève ne puisse pas se faire passer pour un autre."""
    return "".join(caractere for caractere in normaliser(texte) if caractere.isalnum())


def _autorise(caractere: str) -> bool:
    """Lettres latines (accents compris), chiffres 0 à 9, espace, « - » et « . ». Les autres alphabets
    permettraient d'imiter un pseudonyme avec des lettres semblables (un « А » cyrillique pour un « A »)."""
    if caractere in PONCTUATION or "0" <= caractere <= "9":
        return True
    return caractere.isalpha() and unicodedata.name(caractere, "").startswith("LATIN ")


def contient_le_nom(texte: str, prenom: str, nom: str) -> bool:
    """Vrai si le pseudonyme reprend à la fois le prénom et le nom : ils ne doivent jamais être publics (Q20)."""
    collee = cle(texte)
    return bool(cle(prenom)) and bool(cle(nom)) and cle(prenom) in collee and cle(nom) in collee


def valider(texte: str) -> str:
    """Le pseudonyme tel qu'il sera affiché, ou PseudonymeInvalide avec un message pour l'élève."""
    propre = " ".join(texte.split())
    if not LONGUEUR_MIN <= len(propre) <= LONGUEUR_MAX:
        raise PseudonymeInvalide(f"Le pseudonyme fait de {LONGUEUR_MIN} à {LONGUEUR_MAX} caractères.")
    if not all(_autorise(caractere) for caractere in propre):
        raise PseudonymeInvalide(
            "Le pseudonyme ne contient que des lettres, des chiffres, des espaces, « - » et « . »."
        )
    if not any(caractere.isalpha() for caractere in propre):
        raise PseudonymeInvalide("Le pseudonyme contient au moins une lettre.")
    if sum(caractere.isdigit() for caractere in propre) > CHIFFRES_MAX:
        raise PseudonymeInvalide("Le pseudonyme ne peut pas contenir de numéro de téléphone.")
    # Une ligature (« ﬀ ») s'allonge une fois décomposée : la clé doit tenir dans sa colonne.
    if len(cle(propre)) > LONGUEUR_MAX:
        raise PseudonymeInvalide(f"Le pseudonyme fait de {LONGUEUR_MIN} à {LONGUEUR_MAX} caractères.")
    mots = normaliser(propre).replace("-", " ").replace(".", " ").split()
    collee = cle(propre)
    if any(mot in MOTS_INTERDITS for mot in mots) or any(racine in collee for racine in RACINES_INTERDITES):
        raise PseudonymeInvalide("Ce pseudonyme n'est pas autorisé : choisis-en un autre.")
    return propre
