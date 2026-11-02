from app.export_openapi import FICHIER_OPENAPI, contenu_openapi


def test_le_schema_versionne_est_a_jour() -> None:
    # En cas d'échec : cd backend && uv run python -m app.export_openapi, puis npm run api:types.
    assert FICHIER_OPENAPI.read_text(encoding="utf-8") == contenu_openapi()
