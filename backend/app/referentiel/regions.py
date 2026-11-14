"""Les 5 régions du Togo, niveau au-dessus des DRE (spec 033). Liste fixe : pas de table."""

from enum import StrEnum


class RegionScolaire(StrEnum):
    maritime = "maritime"
    plateaux = "plateaux"
    centrale = "centrale"
    kara = "kara"
    savanes = "savanes"


# Du sud au nord, l'ordre de la carte.
NOMS = {
    RegionScolaire.maritime: "Maritime",
    RegionScolaire.plateaux: "Plateaux",
    RegionScolaire.centrale: "Centrale",
    RegionScolaire.kara: "Kara",
    RegionScolaire.savanes: "Savanes",
}
ORDRE = list(NOMS)

# Région des DRE de l'annuaire (codes stables) ; une DRE créée ensuite par l'équipe choisit la sienne.
REGION_PAR_DRE = {
    "grand-lome": RegionScolaire.maritime,
    "maritime": RegionScolaire.maritime,
    "plateaux-est": RegionScolaire.plateaux,
    "plateaux-ouest": RegionScolaire.plateaux,
    "centrale": RegionScolaire.centrale,
    "kara": RegionScolaire.kara,
    "savanes": RegionScolaire.savanes,
}
