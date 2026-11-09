"""La bibliothèque publique (spec 028) : ressources publiées seulement, ouvertes à tous, visiteurs compris."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.fichiers.stockage import Disque, StockageIndisponible
from tests.bibliotheque import PUBLIC, creer_ressource

MAGAZINE = CategorieRessource.magazine


def il_y_a(jours: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=jours)


def compteur(en_base: Callable[..., Any], ressource: Ressource) -> int:
    return en_base(lambda db: db.scalar(select(Ressource.telechargements).where(Ressource.id == ressource.id)))


def test_un_visiteur_voit_les_ressources_publiees_des_plus_recentes_aux_plus_anciennes(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    creer_ressource(en_base, titre="Ancienne", publie_le=il_y_a(10))
    creer_ressource(en_base, titre="Récente", publie_le=il_y_a(1))
    for etat in (EtatRessource.brouillon, EtatRessource.soumis, EtatRessource.depublie):
        creer_ressource(en_base, etat=etat, titre=f"Cachée {etat}")

    corps = client.get(PUBLIC).json()

    assert [r["titre"] for r in corps["ressources"]] == ["Récente", "Ancienne"]
    premiere = corps["ressources"][0]
    assert premiere["validateur_nom"] == "Dr Afi Mensah"
    assert premiere["pages"] == 2
    assert premiere["fichier_octets"] > 0
    assert premiere["couverture"] is None


def test_la_liste_ne_montre_rien_de_la_preparation(client: TestClient, en_base: Callable[..., Any]) -> None:
    creer_ressource(en_base)

    [ressource] = client.get(PUBLIC).json()["ressources"]

    assert not {"contributeurs", "soumis_par", "decide_par", "motif", "fichier_cle", "etat"} & ressource.keys()


def test_la_liste_se_filtre_par_categorie_et_par_axe(client: TestClient, en_base: Callable[..., Any]) -> None:
    from app.referentiel.models import Axe

    axes = list(en_base(lambda db: db.scalars(select(Axe.code).order_by(Axe.code).limit(2))).all())
    creer_ressource(en_base, titre="Guide A", axe_code=axes[0])
    creer_ressource(en_base, titre="Guide B", axe_code=axes[1])
    creer_ressource(en_base, titre="Fiche A", categorie=CategorieRessource.fiche, axe_code=axes[0])

    par_categorie = client.get(PUBLIC, params={"categorie": "guide"}).json()["ressources"]
    par_axe = client.get(PUBLIC, params={"axe": axes[0]}).json()["ressources"]
    les_deux = client.get(PUBLIC, params={"categorie": "fiche", "axe": axes[0]}).json()["ressources"]

    assert {r["titre"] for r in par_categorie} == {"Guide A", "Guide B"}
    assert {r["titre"] for r in par_axe} == {"Guide A", "Fiche A"}
    assert [r["titre"] for r in les_deux] == ["Fiche A"]
    assert client.get(PUBLIC, params={"categorie": "video"}).status_code == 422


def test_a_la_une_montre_les_3_derniers_magazines(client: TestClient, en_base: Callable[..., Any]) -> None:
    for i in range(4):
        creer_ressource(en_base, categorie=MAGAZINE, titre=f"Magazine {i}", couverture=True, publie_le=il_y_a(10 - i))
    creer_ressource(en_base, titre="Guide récent", publie_le=il_y_a(0))
    creer_ressource(en_base, categorie=MAGAZINE, etat=EtatRessource.depublie, titre="Retiré", couverture=True)

    une = client.get(PUBLIC, params={"categorie": "guide"}).json()["a_la_une"]

    # « À la Une » ignore les filtres de la liste.
    assert [m["titre"] for m in une] == ["Magazine 3", "Magazine 2", "Magazine 1"]
    assert une[0]["couverture"].startswith(f"/api/bibliotheque/{une[0]['id']}/couverture/grande?v=")


def test_les_chiffres_portent_sur_les_ressources_publiees(client: TestClient, en_base: Callable[..., Any]) -> None:
    creer_ressource(en_base, telechargements=10)
    creer_ressource(en_base, telechargements=5, titre="Autre")
    creer_ressource(en_base, etat=EtatRessource.depublie, telechargements=100)

    assert client.get(PUBLIC).json()["chiffres"] == {"documents": 2, "telechargements": 15}


def test_une_bibliotheque_vide(client: TestClient) -> None:
    assert client.get(PUBLIC).json() == {
        "a_la_une": [],
        "ressources": [],
        "chiffres": {"documents": 0, "telechargements": 0},
    }


# Le fichier -------------------------------------------------------------------------------------------------------


def test_un_visiteur_telecharge_le_pdf_et_le_compteur_monte(client: TestClient, en_base: Callable[..., Any]) -> None:
    ressource = creer_ressource(en_base, titre="Guide d'action n° 2 : l'hygiène")

    reponse = client.get(f"{PUBLIC}/{ressource.id}/fichier", params={"telecharger": 1})

    assert reponse.status_code == 200
    assert reponse.content.startswith(b"%PDF-")
    assert reponse.headers["content-type"] == "application/pdf"
    assert reponse.headers["content-length"] == str(ressource.fichier_octets)
    assert reponse.headers["content-disposition"] == 'attachment; filename="guide-d-action-n-2-l-hygiene.pdf"'
    assert reponse.headers["x-content-type-options"] == "nosniff"
    assert reponse.headers["cache-control"] == "no-store"
    assert "accept-ranges" not in reponse.headers
    assert compteur(en_base, ressource) == 1


def test_lire_ouvre_le_pdf_dans_le_navigateur_et_compte_aussi(client: TestClient, en_base: Callable[..., Any]) -> None:
    ressource = creer_ressource(en_base)

    reponse = client.get(f"{PUBLIC}/{ressource.id}/fichier")

    assert reponse.headers["content-disposition"].startswith("inline;")
    assert compteur(en_base, ressource) == 1


@pytest.mark.parametrize("etat", [EtatRessource.brouillon, EtatRessource.soumis, EtatRessource.depublie])
def test_le_fichier_dune_ressource_hors_ligne_repond_404(
    client: TestClient, en_base: Callable[..., Any], etat: EtatRessource
) -> None:
    ressource = creer_ressource(en_base, etat=etat, couverture=True)

    assert client.get(f"{PUBLIC}/{ressource.id}/fichier").status_code == 404
    assert client.get(f"{PUBLIC}/{ressource.id}/couverture/grande").status_code == 404
    assert compteur(en_base, ressource) == 0


def test_une_ressource_inconnue_repond_404(client: TestClient) -> None:
    assert client.get(f"{PUBLIC}/00000000-0000-0000-0000-000000000000/fichier").status_code == 404
    assert client.get(f"{PUBLIC}/pas-un-identifiant/fichier").status_code == 422


def test_la_couverture_publiee_est_servie(client: TestClient, en_base: Callable[..., Any]) -> None:
    ressource = creer_ressource(en_base, couverture=True)

    reponse = client.get(f"{PUBLIC}/{ressource.id}/couverture/vignette")

    assert reponse.status_code == 200
    assert reponse.content == b"RIFF-vignette"
    assert reponse.headers["content-type"] == "image/webp"
    assert client.get(f"{PUBLIC}/{ressource.id}/couverture/geante").status_code == 404


def test_le_stockage_indisponible_repond_503_sans_compter(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    ressource = creer_ressource(en_base)

    async def panne(self: Disque, cle: str) -> None:
        raise StockageIndisponible

    monkeypatch.setattr(Disque, "lire_par_morceaux", panne)

    assert client.get(f"{PUBLIC}/{ressource.id}/fichier").status_code == 503
    assert compteur(en_base, ressource) == 0
