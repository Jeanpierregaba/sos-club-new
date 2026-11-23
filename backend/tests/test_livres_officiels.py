"""Les 4 livres de l'Académie Génie Imhotep publiés dans la bibliothèque au déploiement (spec 050)."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.bibliotheque import livres_officiels
from app.bibliotheque.models import EtatRessource, Ressource
from app.fichiers.stockage import Disque

TITRES = [livre.titre for livre in livres_officiels.LIVRES]


def _charger(en_base: Callable[..., Any]) -> list[str]:
    return en_base(livres_officiels.charger)


def test_publie_les_4_livres_telechargeables(
    client: TestClient, en_base: Callable[..., Any], dossier_fichiers: Path
) -> None:
    assert _charger(en_base) == TITRES

    publiques = {r["titre"]: r for r in client.get("/api/bibliotheque?categorie=fascicule").json()["ressources"]}
    assert sorted(publiques) == sorted(TITRES)
    for r in publiques.values():
        assert (r["axe_code"], r["validateur_nom"], r["contenu_de_test"]) == (
            "genie-imhotep",
            livres_officiels.VALIDATEUR,
            False,
        )
        assert r["pages"] > 50 and r["couverture"]
    assert {r["pages"] for r in publiques.values()} == {148, 177, 80, 115}

    livre = publiques[TITRES[0]]
    reponse = client.get(f"/api/bibliotheque/{livre['id']}/fichier?telecharger=1")
    assert reponse.status_code == 200
    assert reponse.content.startswith(b"%PDF-") and len(reponse.content) == livre["fichier_octets"]
    assert "attachment" in reponse.headers["content-disposition"]
    assert client.get(f"/api/bibliotheque/{livre['id']}/couverture/vignette").status_code == 200


def test_relance_sans_doublon_ni_retouche(en_base: Callable[..., Any], dossier_fichiers: Path) -> None:
    _charger(en_base)
    # L'équipe a dépublié un livre : le chargement ne le republie pas.
    en_base(
        lambda db: db.execute(update(Ressource).where(Ressource.titre == TITRES[1]).values(etat=EtatRessource.depublie))
    )
    fichiers = sorted(p.name for p in dossier_fichiers.rglob("*") if p.is_file())

    assert _charger(en_base) == []

    async def lire(db: AsyncSession) -> list[tuple[str, EtatRessource]]:
        return sorted((await db.execute(select(Ressource.titre, Ressource.etat))).all())

    lignes = en_base(lire)
    assert len(lignes) == 4
    assert dict(lignes)[TITRES[1]] is EtatRessource.depublie
    assert sorted(p.name for p in dossier_fichiers.rglob("*") if p.is_file()) == fichiers


def test_un_echec_ne_laisse_aucun_fichier(
    en_base: Callable[..., Any], dossier_fichiers: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    enregistrer = Disque.enregistrer
    appels = 0

    async def panne_au_troisieme(self: Disque, cle: str, octets: bytes) -> None:
        nonlocal appels
        appels += 1
        if appels == 3:
            raise OSError("disque plein")
        await enregistrer(self, cle, octets)

    monkeypatch.setattr(Disque, "enregistrer", panne_au_troisieme)

    with pytest.raises(OSError, match="disque plein"):
        _charger(en_base)

    assert [p for p in dossier_fichiers.rglob("*") if p.is_file()] == []
    assert en_base(lambda db: db.scalar(select(Ressource.id))) is None
