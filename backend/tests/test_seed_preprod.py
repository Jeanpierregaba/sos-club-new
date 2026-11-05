"""Comptes de test de la préproduction : refus hors préproduction, comptes par profil, club de test,
double authentification de l'administrateur et fichier d'accès privé."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Club, ClubPassation, EtatClub
from app.comptes.models import Utilisateur
from app.config import settings
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.points.models import MouvementPoints
from app.seed_commun import ecrire_fichier
from app.seed_preprod import ENTETE, PreparationImpossible, PreprodRefusee, semer

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def en_preprod(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le seed ne tourne que si l'environnement est la préproduction."""
    monkeypatch.setattr(settings, "environnement", "preprod")


def acces_de(acces: list[dict[str, str]], identifiant: str) -> dict[str, str]:
    return next(a for a in acces if a["identifiant"] == identifiant)


def test_refuse_en_developpement(en_base: Callable[..., Any]) -> None:
    with pytest.raises(PreprodRefusee):
        en_base(semer)


def test_refuse_en_production(en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environnement", "prod")

    with pytest.raises(PreprodRefusee):
        en_base(semer)


def test_cree_un_compte_par_profil(en_preprod: None, en_base: Callable[..., Any]) -> None:
    acces = en_base(semer)

    identifiants = {ligne["identifiant"] for ligne in acces}
    assert identifiants == {"preprod.admin", "preprod.encadreur", "preprod.eleve", "preprod.president"}

    async def comptes(db: AsyncSession) -> list[Utilisateur]:
        return list((await db.scalars(select(Utilisateur).where(Utilisateur.identifiant.like("preprod.%")))).all())

    assert len(en_base(comptes)) == 4


def test_prepare_un_club_actif_preside_par_un_eleve(en_preprod: None, en_base: Callable[..., Any]) -> None:
    en_base(semer)

    async def clubs(db: AsyncSession) -> list[Club]:
        return list((await db.scalars(select(Club).where(Club.etat == EtatClub.actif))).all())

    actifs = en_base(clubs)
    assert len(actifs) == 1
    club = actifs[0]
    president = en_base(lambda db: db.get(Utilisateur, club.president_id))
    assert president is not None
    assert president.identifiant == "preprod.president"


def test_le_super_admin_se_connecte_avec_le_secret_ecrit(
    en_preprod: None, client: TestClient, en_base: Callable[..., Any]
) -> None:
    admin = acces_de(en_base(semer), "preprod.admin")

    etape = client.post(
        "/api/comptes/connexion", json={"identifiant": "preprod.admin", "mot_de_passe": admin["mot_de_passe"]}
    ).json()
    code = pyotp.TOTP(admin["secret_totp"]).now()
    reponse = client.post("/api/comptes/connexion/code", json={"jeton": etape["jeton"], "code": code})

    assert reponse.status_code == 200
    assert client.get("/api/admin/tableau-de-bord").status_code == 200


def test_l_eleve_et_l_encadreur_se_connectent(
    en_preprod: None, client: TestClient, en_base: Callable[..., Any]
) -> None:
    acces = en_base(semer)

    client.post(
        "/api/comptes/connexion",
        json={"identifiant": "preprod.eleve", "mot_de_passe": acces_de(acces, "preprod.eleve")["mot_de_passe"]},
    )
    eleve = client.get("/api/eleves/moi").json()
    client.post(
        "/api/comptes/connexion",
        json={"identifiant": "preprod.encadreur", "mot_de_passe": acces_de(acces, "preprod.encadreur")["mot_de_passe"]},
    )
    encadreur = client.get("/api/encadreurs/moi").json()

    assert eleve["pseudonyme"] == "Koffi Preprod"
    assert encadreur["etat"] == "actif"
    # L'élève et l'encadreur sont du même établissement : c'est ce qui permet les demandes de la spec 020.
    assert eleve["etablissement"]["id"] == encadreur["etablissement"]["id"]


def test_relancer_change_les_mots_de_passe(en_preprod: None, client: TestClient, en_base: Callable[..., Any]) -> None:
    ancien = acces_de(en_base(semer), "preprod.eleve")["mot_de_passe"]
    nouveau = acces_de(en_base(semer), "preprod.eleve")["mot_de_passe"]

    assert ancien != nouveau
    assert (
        client.post("/api/comptes/connexion", json={"identifiant": "preprod.eleve", "mot_de_passe": ancien}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/comptes/connexion", json={"identifiant": "preprod.eleve", "mot_de_passe": nouveau}
        ).status_code
        == 200
    )


def test_le_fichier_d_acces_est_prive(en_preprod: None, en_base: Callable[..., Any], tmp_path: Path) -> None:
    chemin = tmp_path / "acces-preprod.txt"

    ecrire_fichier(en_base(semer), chemin, ENTETE)

    assert oct(chemin.stat().st_mode & 0o777) == "0o600"
    texte = chemin.read_text()
    assert "[preprod.admin] Super-administrateur" in texte
    assert "identifiant    : preprod.admin" in texte
    assert "secret 2FA" in texte


def test_relancer_remet_le_club_en_etat_sans_doublon(en_preprod: None, en_base: Callable[..., Any]) -> None:
    en_base(semer)

    async def derouter(db: AsyncSession) -> None:
        # Pendant les tests, le club a été refusé et confié à un autre élève.
        club = await db.scalar(select(Club))
        eleve = await db.scalar(select(Utilisateur).where(Utilisateur.identifiant == "preprod.eleve"))
        club.etat = EtatClub.refuse
        club.motif_refus = "Test de refus."
        club.president_id = eleve.id

    en_base(derouter)
    en_base(semer)

    async def etat(db: AsyncSession) -> dict[str, Any]:
        clubs = list((await db.scalars(select(Club))).all())
        president = await db.get(Utilisateur, clubs[0].president_id)
        bienvenues = list(
            (await db.scalars(select(MouvementPoints.cle).where(MouvementPoints.cle.like("bienvenue:%")))).all()
        )
        return {
            "clubs": clubs,
            "president": president.identifiant,
            "bienvenues": bienvenues,
            "eleves": len((await db.scalars(select(Eleve))).all()),
            "encadreurs": len((await db.scalars(select(Encadreur))).all()),
        }

    resultat = en_base(etat)
    assert len(resultat["clubs"]) == 1
    club = resultat["clubs"][0]
    assert club.etat == EtatClub.actif
    assert club.motif_refus is None
    assert resultat["president"] == "preprod.president"
    # Élève, président et encadreur : un seul crédit de bienvenue chacun, même après deux lancements.
    assert len(resultat["bienvenues"]) == len(set(resultat["bienvenues"])) == 3
    assert resultat["eleves"] == 2
    assert resultat["encadreurs"] == 1


def test_refuse_si_un_autre_club_actif_occupe_l_etablissement(en_preprod: None, en_base: Callable[..., Any]) -> None:
    en_base(semer)

    async def occuper(db: AsyncSession) -> None:
        club = await db.scalar(select(Club))
        club.etat = EtatClub.refuse
        club.motif_refus = "Test de refus."
        await db.flush()
        db.add(
            Club(
                etablissement_id=club.etablissement_id,
                nom="Club d'un testeur",
                nom_normalise="club d un testeur",
                demandeur_id=club.demandeur_id,
                president_id=club.demandeur_id,
                etat=EtatClub.actif,
            )
        )

    en_base(occuper)

    with pytest.raises(PreparationImpossible, match="autre club actif"):
        en_base(semer)


def test_refuse_si_une_passation_est_en_attente(en_preprod: None, en_base: Callable[..., Any]) -> None:
    en_base(semer)

    async def proposer(db: AsyncSession) -> None:
        club = await db.scalar(select(Club))
        eleve = await db.scalar(select(Utilisateur).where(Utilisateur.identifiant == "preprod.eleve"))
        db.add(ClubPassation(club_id=club.id, successeur_id=eleve.id, propose_par=club.president_id))

    en_base(proposer)

    with pytest.raises(PreparationImpossible, match="passation"):
        en_base(semer)
