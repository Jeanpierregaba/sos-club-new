"""Contrôle d'un document Word `.docx` (spec 038) sans jamais l'ouvrir ni l'afficher : une archive ZIP valide, avec
les parties d'un document Word, sans macro, contrôle actif, objet intégré (OLE) ni relation externe (modèle
distant qui chargerait des macros), et de taille décompressée bornée (bombe ZIP)."""

import re
import zipfile
from io import BytesIO

ENTREES_MAX = 1000
DECOMPRESSE_MAX = 50 * 1024 * 1024
RATIO_MAX = 200
INTERDITS = ("vbaproject.bin", "/activex/", "vbadata.xml", "oleobject", "/embeddings/")
RELATIONS_MAX = 1024 * 1024
RELATION = re.compile(r"<relationship\b[^>]*>")


class DocxRefuse(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def verifier(octets: bytes) -> None:
    try:
        archive = zipfile.ZipFile(BytesIO(octets))
        entrees = archive.infolist()
    except zipfile.BadZipFile, ValueError, OSError:
        raise DocxRefuse("Ce fichier n'est pas un document Word valide.") from None
    if len(entrees) > ENTREES_MAX:
        raise DocxRefuse("Ce document Word contient trop d'éléments.")
    noms = {e.filename for e in entrees}
    if "[Content_Types].xml" not in noms or "word/document.xml" not in noms:
        raise DocxRefuse("Ce fichier n'est pas un document Word (.docx).")
    total = 0
    for entree in entrees:
        nom = f"/{entree.filename.lower()}"
        if entree.flag_bits & 0x1:
            raise DocxRefuse("Un document Word protégé par mot de passe n'est pas accepté.")
        if any(interdit in nom for interdit in INTERDITS):
            raise DocxRefuse("Les documents Word avec macros ou contrôles actifs ne sont pas acceptés.")
        total += entree.file_size
        if entree.compress_size and entree.file_size / entree.compress_size > RATIO_MAX:
            raise DocxRefuse("Ce document Word est anormalement compressé.")
    if total > DECOMPRESSE_MAX:
        raise DocxRefuse("Ce document Word est trop volumineux une fois ouvert.")
    try:
        types = archive.read("[Content_Types].xml").decode("utf-8", "replace").lower()
    except zipfile.BadZipFile, KeyError, OSError:
        raise DocxRefuse("Ce fichier n'est pas un document Word valide.") from None
    if "macroenabled" in types or "vbaproject" in types:
        raise DocxRefuse("Les documents Word avec macros ne sont pas acceptés.")
    # Une relation externe (modèle attaché, cadre, objet lié) ferait charger un fichier distant à l'ouverture.
    for entree in entrees:
        if entree.filename.lower().endswith(".rels"):
            if entree.file_size > RELATIONS_MAX:
                raise DocxRefuse("Ce document Word est anormal.")
            relations = archive.read(entree.filename).decode("utf-8", "replace").lower().replace("'", '"')
            for relation in RELATION.findall(relations):
                # Un lien hypertexte reste permis : il ne s'ouvre que si le lecteur clique.
                if 'targetmode="external"' in relation and not re.search(r'type="[^"]*/hyperlink"', relation):
                    raise DocxRefuse(
                        "Les documents Word qui chargent un modèle ou un fichier distant ne sont pas acceptés."
                    )
