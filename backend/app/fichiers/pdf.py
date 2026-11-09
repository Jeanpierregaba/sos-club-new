"""Contrôle des PDF déposés dans la bibliothèque (spec 028).

Un PDF publié est servi depuis le domaine du site et ouvert par le lecteur du navigateur : il ne doit rien
exécuter ni rien transporter. On refuse un fichier illisible, chiffré, sans page, ou dont un objet atteignable
porte du JavaScript, une action de lancement, un fichier joint, un contenu multimédia, un formulaire XFA ou une
action d'envoi ou d'import de données. Les liens vers des sites restent permis.

Le parcours part du trailer et suit chaque référence une seule fois : une structure en boucle ne le bloque pas,
et un nombre de nœuds plafonné borne le temps d'analyse.
"""

import asyncio
import io
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, PdfObject

# Ce que pypdf lève, en plus de ses propres erreurs, sur un fichier abîmé ou trompeur.
LECTURE_IMPOSSIBLE = (PyPdfError, OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, RecursionError)

NOEUDS_MAX = 500_000

# Nom (clé ou valeur) → la raison donnée au collaborateur.
INTERDITS: dict[str, str] = {
    "/JavaScript": "Ce PDF contient du JavaScript.",
    "/JS": "Ce PDF contient du JavaScript.",
    "/Launch": "Ce PDF contient une action qui lance un programme.",
    "/EmbeddedFile": "Ce PDF contient un fichier joint.",
    "/EmbeddedFiles": "Ce PDF contient un fichier joint.",
    "/RichMedia": "Ce PDF contient un contenu multimédia intégré.",
    "/XFA": "Ce PDF contient un formulaire XFA.",
    "/SubmitForm": "Ce PDF contient un formulaire qui envoie des données.",
    "/ImportData": "Ce PDF contient une action qui importe des données.",
}
CONSEIL = " Exporte-le de nouveau en PDF simple (« Enregistrer sous » ou « Imprimer en PDF »)."
ILLISIBLE = "Ce fichier n'est pas un PDF lisible."
CHIFFRE = "Ce PDF est protégé par un mot de passe : dépose une version sans protection."
SANS_PAGE = "Ce PDF ne contient aucune page."
TROP_COMPLEXE = "Ce PDF est trop complexe pour être vérifié." + CONSEIL


class PdfRefuse(ValueError):
    """Le message s'affiche tel quel au collaborateur."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class InfosPdf:
    pages: int


def _interdit(nom: str) -> None:
    if nom in INTERDITS:
        raise PdfRefuse(INTERDITS[nom] + CONSEIL)


def _parcourir(racine: PdfObject) -> None:
    vus: set[tuple[int, int]] = set()
    pile: list[PdfObject] = [racine]
    noeuds = 0
    while pile:
        objet = pile.pop()
        noeuds += 1
        if noeuds > NOEUDS_MAX:
            raise PdfRefuse(TROP_COMPLEXE)
        if isinstance(objet, IndirectObject):
            reference = (objet.idnum, objet.generation)
            if reference in vus:
                continue
            vus.add(reference)
            objet = objet.get_object()
        # Un flux est aussi un dictionnaire : son en-tête est examiné, pas son contenu.
        if isinstance(objet, DictionaryObject):
            for cle, valeur in objet.items():
                _interdit(str(cle))
                pile.append(valeur)
        elif isinstance(objet, ArrayObject):
            pile.extend(objet)
        elif isinstance(objet, NameObject):
            _interdit(str(objet))


def verifier(octets: bytes) -> InfosPdf:
    # La norme tolère quelques octets avant l'en-tête ; au-delà, ce n'est pas un PDF.
    if b"%PDF-" not in octets[:1024]:
        raise PdfRefuse(ILLISIBLE)
    try:
        lecteur = PdfReader(io.BytesIO(octets), strict=False)
        if lecteur.is_encrypted:
            raise PdfRefuse(CHIFFRE)
        pages = len(lecteur.pages)
        if pages == 0:
            raise PdfRefuse(SANS_PAGE)
        _parcourir(lecteur.trailer)
    except PdfRefuse:
        raise
    except LECTURE_IMPOSSIBLE:
        raise PdfRefuse(ILLISIBLE) from None
    return InfosPdf(pages=pages)


async def examiner(octets: bytes) -> InfosPdf:
    """`verifier` dans un fil à part : l'analyse d'un gros PDF ne bloque pas les autres requêtes."""
    return await asyncio.to_thread(verifier, octets)
