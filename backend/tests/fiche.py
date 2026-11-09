"""Une fiche d'adhésion complète et valide (spec 030), à compléter ou altérer dans les tests."""

from datetime import date
from typing import Any


def fiche(**champs: Any) -> dict[str, Any]:
    valeurs: dict[str, Any] = {
        "numero_adhesion": "CS-042",
        "prefecture": "Golfe",
        "commune": "Golfe 1",
        "canton": "Bè",
        "sexe": "feminin",
        "date_naissance": date(date.today().year - 16, 3, 14).isoformat(),
        "lieu_naissance": "Lomé",
        "telephone": None,
        "pere": {"nom": "Koffi Mensah", "profession": "Commerçant", "telephone": "+228 90 11 22 33"},
        "mere": None,
        "responsable": {"nom": "Koffi Mensah", "telephone": "90 11 22 33"},
        "axes": ["genie-imhotep", "sante-environnement"],
        "parcours": [{"annee": "2025-2026", "etablissement": "CEG Bè", "iesg": "IESG Golfe"}],
        "reseaux": ["facebook", "autre"],
        "reseau_autre": "Snapchat",
        "engagement": True,
    }
    return valeurs | champs
