"""Import de la liste nationale des établissements du Secondaire I (spec 035).

Le fichier Excel du ministère est converti une fois en `alembic/donnees/etablissements_secondaire_1.json`, que la
migration lit. La conversion se relance pour une liste mise à jour :

    cd backend && uv run python -m app.referentiel.import_secondaire chemin/vers/liste.xlsx
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from app.referentiel.chargement import lire_annuaire
from app.referentiel.normalisation import nettoyer, normaliser

FICHIER = Path(__file__).resolve().parents[2] / "alembic" / "donnees" / "etablissements_secondaire_1.json"
SOURCE = "secondaire-1-2026"

# Les sigles d'établissement du fichier, gardés en majuscules.
SIGLES = {
    "CEG", "CEGIL", "CPL", "CPI", "CPC", "CPP", "CPE", "CPA", "CS", "CSI", "CSS", "CSPL", "CGEC", "LPL", "EPL",
    "EPP", "ISAS", "CFSS", "IEG", "NDSS", "AD", "PC", "TV",
}  # fmt: skip
ROMAINS = re.compile(r"^(?=[IVX]+$)M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
# Mots de liaison gardés en minuscules au milieu d'un nom, sauf juste après le sigle (« CPL Les Bâtisseurs »).
LIAISONS = {"de", "du", "des", "la", "le", "les", "et", "au", "aux", "en", "sur", "pour"}
ELISIONS = ("d'", "l'")

# Les mots courants du fichier, écrits sans accents, et leur graphie : seuls des accents sont ajoutés, donc le nom
# normalisé ne change pas.
ACCENTS = {
    "lycee": "Lycée", "college": "Collège", "ecole": "École", "eglise": "Église", "elite": "Élite",
    "elites": "Élites", "esperance": "Espérance", "evangelique": "Évangélique", "academie": "Académie",
    "cite": "Cité", "generation": "Génération", "reussite": "Réussite", "succes": "Succès", "lumiere": "Lumière",
    "pere": "Père", "mere": "Mère", "tresor": "Trésor", "reveil": "Réveil", "verite": "Vérité",
    "prosperite": "Prospérité", "etoile": "Étoile", "etoiles": "Étoiles", "fidelite": "Fidélité",
    "chretien": "Chrétien", "chretienne": "Chrétienne", "therese": "Thérèse",
    "education": "Éducation", "integre": "Intègre", "benediction": "Bénédiction",
    "methodiste": "Méthodiste", "evangile": "Évangile", "reference": "Référence", "realite": "Réalité",
}  # fmt: skip

# Les 39 préfectures du fichier et leur graphie officielle (affichée à l'inscription). Une préfecture absente de
# cette table arrête la conversion.
PREFECTURES = {
    "agoe nyive": "Agoè-Nyivé", "agou": "Agou", "akebou": "Akébou", "amou": "Amou", "anie": "Anié",
    "assoli": "Assoli", "ave": "Avé", "bas mono": "Bas-Mono", "bassar": "Bassar", "binah": "Binah",
    "blitta": "Blitta", "cinkasse": "Cinkassé", "dankpen": "Dankpen", "danyi": "Danyi", "doufelgou": "Doufelgou",
    "est mono": "Est-Mono", "golfe": "Golfe", "haho": "Haho", "keran": "Kéran", "kloto": "Kloto", "kozah": "Kozah",
    "kpele": "Kpélé", "kpendjal": "Kpendjal", "kpendjal ouest": "Kpendjal-Ouest", "lacs": "Lacs", "mo": "Mô",
    "moyen mono": "Moyen-Mono", "ogou": "Ogou", "oti": "Oti", "oti sud": "Oti-Sud", "sotouboua": "Sotouboua",
    "tandjoare": "Tandjouaré", "tchamba": "Tchamba", "tchaoudjo": "Tchaoudjo", "tone": "Tône", "vo": "Vo",
    "wawa": "Wawa", "yoto": "Yoto", "zio": "Zio",
}  # fmt: skip

ALIAS_IESG = {"iesg agoe nyive": "iesg agoenyive"}

ORDRES = {
    "public": "public",
    "prive laic": "prive_laic",
    "prive catholique": "prive_catholique",
    "prive protestant": "prive_protestant",
    "prive islamique": "prive_islamique",
    "communautaire": "communautaire",
}

LYCEES = {"LYCEE", "LPL"}
COMPLEXES = {"COMPLEXE", "CS", "CSI", "CSPL", "GROUPE"}
AUTRES = {"CENTRE", "INSTITUT", "ECOLE", "ISAS", "CFSS", "EPL"}


def _partie(partie: str) -> str:
    bas = partie.lower()
    return ACCENTS.get(bas) or partie[:1].upper() + bas[1:]


def _mot(mot: str) -> str:
    """Une majuscule initiale à chaque partie d'un mot composé (« DASSOUTE-NANIK » → « Dassoute-Nanik »), et ses
    accents pour les mots courants (« LYCEE » → « Lycée »). Le « s » d'un génitif anglais reste minuscule."""
    propre = re.sub(r"[^\W\d_]+", lambda m: _partie(m.group(0)), mot)
    return re.sub(r"'S\b", "'s", propre)


def _garde(mot: str) -> bool:
    """Un mot écrit tel quel : déjà en casse mixte (« Dr »), sigle, chiffre romain, sigle entre parenthèses."""
    nu = re.sub(r"[^\w]", "", mot)
    if mot != mot.upper():
        return True
    if nu and (all(p in SIGLES for p in re.split(r"[^\w]+", mot) if p) or ROMAINS.match(nu)):
        return True
    return mot.startswith("(") and mot.endswith(")") and nu.isalpha() and len(nu) <= 5


def casse(nom: str) -> str:
    """« CPL LA VOIE DE L'UNIVERSITE » → « CPL La Voie de l'Universite » : casse normale, sigles et chiffres
    romains en majuscules, mots de liaison en minuscules au milieu du nom. Un mot déjà en casse mixte (« Dr »)
    est gardé tel quel."""
    mots = nettoyer(nom.replace("’", "'")).split(" ")
    sortie: list[str] = []
    for position, mot in enumerate(mots):
        if _garde(mot):
            sortie.append(mot)
        else:
            bas = mot.lower()
            apres_sigle = position == 1 and mots[0].upper() in SIGLES
            milieu = position > 0 and not apres_sigle
            if re.search(r"\(([A-Z]{2,5})\)$", mot):
                # Un sigle collé au nom : « AGBELOUVE(PC) ».
                debut = mot.rindex("(")
                sortie.append(_mot(mot[:debut]) + mot[debut:])
            elif milieu and bas in LIAISONS:
                sortie.append(bas)
            elif milieu and bas.startswith(ELISIONS) and len(bas) > 2:
                sortie.append(bas[:2] + _mot(mot[2:]))
            else:
                sortie.append(_mot(mot))
    return " ".join(sortie)


def type_de(nom: str) -> str:
    premier = re.split(r"[^\w]+", normaliser(nom).upper(), maxsplit=1)[0]
    if premier in LYCEES:
        return "lycee"
    if premier in COMPLEXES:
        return "complexe"
    if premier in AUTRES:
        return "autre"
    return "college"


def convertir(lignes: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    """Les lignes (nom, région, IESG, préfecture, ordre) du fichier → les établissements à importer. Refuse une IESG
    ou un ordre inconnus ; garde une seule fois deux lignes de même nom dans la même IESG."""
    iesg_connues = {normaliser(i["nom"]): i["nom"] for i in lire_annuaire()["iesg"]}
    sortie: dict[tuple[str, str], dict[str, Any]] = {}
    for nom, _region, iesg, prefecture, ordre in lignes:
        cle_iesg = normaliser(str(iesg))
        cle_iesg = ALIAS_IESG.get(cle_iesg, cle_iesg)
        if cle_iesg not in iesg_connues:
            raise ValueError(f"IESG inconnue : {iesg}")
        cle_ordre = normaliser(str(ordre or ""))
        if cle_ordre and cle_ordre not in ORDRES:
            raise ValueError(f"Ordre inconnu : {ordre}")
        propre = casse(str(nom))
        cle = (cle_iesg, normaliser(propre))
        cle_prefecture = normaliser(str(prefecture or "")).replace("-", " ")
        if cle_prefecture and cle_prefecture not in PREFECTURES:
            raise ValueError(f"Préfecture inconnue : {prefecture}")
        if cle in sortie:
            print(f"Ligne en double écartée : {nom} ({iesg})", file=sys.stderr)
            continue
        sortie.setdefault(
            cle,
            {
                "iesg": iesg_connues[cle_iesg],
                "nom": propre,
                "type": type_de(propre),
                "prefecture": PREFECTURES.get(cle_prefecture),
                "ordre": ORDRES.get(cle_ordre),
            },
        )
    return list(sortie.values())


def lire_excel(chemin: Path) -> list[tuple[Any, ...]]:
    from openpyxl import load_workbook

    classeur = load_workbook(chemin, read_only=True, data_only=True)
    lignes = []
    for ligne in classeur.active.iter_rows(values_only=True):
        numero, nom, region, iesg, prefecture, ordre = ligne[1:7]
        if isinstance(numero, int) and nom:
            lignes.append((nom, region, iesg, prefecture, ordre))
    return lignes


def main() -> None:
    etablissements = convertir(lire_excel(Path(sys.argv[1])))
    lignes = ",\n".join(json.dumps(e, ensure_ascii=False) for e in etablissements)
    FICHIER.write_text(f"[\n{lignes}\n]\n", encoding="utf-8")
    print(f"{len(etablissements)} établissements écrits dans {FICHIER.name}")


if __name__ == "__main__":
    main()
