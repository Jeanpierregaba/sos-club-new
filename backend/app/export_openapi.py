"""Écrit backend/openapi.json, d'où `npm run api:types` génère les types du site (ADR-0002)."""

import json
from pathlib import Path

from app.main import app

FICHIER_OPENAPI = Path(__file__).resolve().parents[1] / "openapi.json"


def contenu_openapi() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    FICHIER_OPENAPI.write_text(contenu_openapi(), encoding="utf-8")
