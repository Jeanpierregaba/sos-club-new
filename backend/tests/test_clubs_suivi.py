"""Suivi des clubs par l'équipe (spec 033) : liste, fiche, périmètre DRE, désistements, terrain, confirmation des
affiliations par l'équipe, échéances quotidiennes."""

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import echeances
from app.clubs.models import (
    Adhesion,
    Club,
    ClubStatut,
    EtatAdhesion,
    EtatClub,
    EtatRattachement,
    Rattachement,
    SignalementDesistement,
)
from app.notifications.models import Notification
from tests.activation import Horloge, ajouter_eleves, figer, rattacher
from tests.conftest import VERIFICATION_CLUBS, Navigateur, connecter_admin, etablissement_de, moteur_test
from tests.espace_club import connecter

ADMIN = "/api/admin/clubs"
MON_CLUB = "/api/clubs/mon-club-sante"

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer(monkeypatch)


@pytest.fixture
def etab(en_base: Callable[..., Any]) -> UUID:
    return etablissement_de(en_base, "grand-lome")


@pytest.fixture
def equipe(en_base: Callable[..., Any], creer_encadreur: Callable[..., Any], etab: UUID) -> list[Any]:
    encadreurs = [creer_encadreur(f"encadreur{i}", etablissement_id=etab) for i in range(1, 4)]
    for encadreur in encadreurs:
        rattacher(en_base, encadreur.id, etab)
    return encadreurs


def admin(
    client: Any, creer_collaborateur: Callable[..., Any], identifiant: str = "verif.clubs", **options: Any
) -> Any:
    creer_collaborateur(identifiant, droits=VERIFICATION_CLUBS, double_auth=True, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


def club(en_base: Callable[..., Any], etab: UUID) -> Club:
    return en_base(
        lambda db: db.scalar(
            select(Club).where(Club.etablissement_id == etab).execution_options(populate_existing=True)
        )
    )


def club_actif(en_base: Callable[..., Any], equipe: list[Any], etab: UUID) -> Club:
    ajouter_eleves(en_base, etab, 21)
    rattacher(en_base, equipe[0].id, etab)
    lu = club(en_base, etab)
    assert lu.etat is EtatClub.actif
    return lu


def signaler(client: Any, vise: Any) -> dict[str, Any]:
    reponse = connecter(client, "encadreur1").post(
        f"{MON_CLUB}/desistements", json={"encadreur_id": str(vise.id), "motif": "Parti à la retraite."}
    )
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


# Liste et fiche ---------------------------------------------------------------------------------------------


def test_l_equipe_suit_les_clubs_avec_leurs_effectifs(
    client: Any, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    club_actif(en_base, equipe, etab)
    navigateur = admin(client, creer_collaborateur)

    page = navigateur.get(f"{ADMIN}/suivi").json()
    actifs = navigateur.get(f"{ADMIN}/suivi", params={"statut": "actif"}).json()
    ailleurs = navigateur.get(f"{ADMIN}/suivi", params={"region": "kara"}).json()

    assert page["total"] == 1
    ligne = page["clubs"][0]
    assert (ligne["statut"], ligne["nb_encadreurs"], ligne["nb_eleves"], ligne["region"]) == (
        "actif",
        3,
        21,
        "Maritime",
    )
    assert actifs["total"] == 1
    assert ailleurs["total"] == 0

    fiche = navigateur.get(f"{ADMIN}/{ligne['id']}/suivi").json()
    assert len(fiche["encadreurs"]) == 3
    assert len(fiche["eleves"]) == 21
    assert set(fiche["eleves"][0]) == {"pseudonyme", "classe"}
    assert fiche["journal"][0]["nouveau"] == "actif"


def test_un_collaborateur_de_dre_ne_voit_que_sa_dre(
    client: Any, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    club_id = club(en_base, etab).id
    navigateur = admin(client, creer_collaborateur, "dre.kara", perimetre_dre="kara")

    assert navigateur.get(f"{ADMIN}/suivi").json()["total"] == 0
    assert navigateur.get(f"{ADMIN}/{club_id}/suivi").status_code == 404
    assert navigateur.post(f"{ADMIN}/{club_id}/terrain", json={"declare": True, "version": 1}).status_code == 404


def test_les_seuils_se_lisent(client: Any, creer_collaborateur: Callable[..., Any]) -> None:
    navigateur = admin(client, creer_collaborateur)
    assert navigateur.get(f"{ADMIN}/seuils").json() == {"encadreurs": 3, "eleves": 21, "delai_jours": 15}


def test_l_equipe_marque_un_club_declare_sur_le_terrain(
    client: Any, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    lu = club(en_base, etab)
    navigateur = admin(client, creer_collaborateur)

    reponse = navigateur.post(
        f"{ADMIN}/{lu.id}/terrain", json={"declare": True, "note": "Visite du 4 novembre.", "version": lu.version}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["club"]["declare_terrain"] is True
    assert reponse.json()["club"]["statut"] == "en_constitution"
    assert client.get("/api/clubs/carte").json()["chiffres"]["clubs"] == 1
    perime = navigateur.post(f"{ADMIN}/{lu.id}/terrain", json={"declare": False, "version": lu.version})
    assert perime.status_code == 409


# Désistements -----------------------------------------------------------------------------------------------


def test_un_desistement_confirme_ouvre_la_regularisation(
    client: Any, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    lu = club_actif(en_base, equipe, etab)
    signalement = signaler(client, equipe[2])
    navigateur = admin(client, creer_collaborateur)
    file = navigateur.get(f"{ADMIN}/desistements").json()
    assert file["total"] == 1

    reponse = navigateur.post(
        f"{ADMIN}/desistements/{signalement['id']}/confirmer", json={"version": file["signalements"][0]["version"]}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["total"] == 0
    apres = club(en_base, etab)
    assert apres.etat is EtatClub.en_regularisation
    assert apres.regularisation_jusquau is not None
    rattachement = en_base(lambda db: db.scalar(select(Rattachement).where(Rattachement.encadreur_id == equipe[2].id)))
    assert rattachement.etat is EtatRattachement.retire
    cause = en_base(
        lambda db: db.scalar(
            select(ClubStatut.cause).where(ClubStatut.club_id == lu.id).order_by(ClubStatut.cree_le.desc()).limit(1)
        )
    )
    assert cause == "desistement_confirme"
    types = set(
        en_base(lambda db: db.scalars(select(Notification.type).where(Notification.utilisateur_id == equipe[0].id)))
    )
    assert {"club_desistement", "club_en_regularisation"} <= types


def test_un_desistement_rejete_ne_change_rien(
    client: Any, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    club_actif(en_base, equipe, etab)
    signalement = signaler(client, equipe[2])
    navigateur = admin(client, creer_collaborateur)
    url = f"{ADMIN}/desistements/{signalement['id']}/rejeter"

    assert navigateur.post(url, json={"version": 1}).status_code == 422
    reponse = navigateur.post(url, json={"motif": "Il est toujours en poste.", "version": 1})

    assert reponse.status_code == 200, reponse.text
    assert club(en_base, etab).etat is EtatClub.actif
    vise = set(
        en_base(lambda db: db.scalars(select(Notification.type).where(Notification.utilisateur_id == equipe[2].id)))
    )
    assert "club_desistement" not in vise
    assert en_base(lambda db: db.scalar(select(SignalementDesistement.etat))).value == "rejete"


def test_un_troisieme_encadreur_avant_l_echeance_rend_le_club_actif(
    client: Any,
    en_base: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    equipe: list[Any],
    etab: UUID,
) -> None:
    club_actif(en_base, equipe, etab)
    signalement = signaler(client, equipe[2])
    navigateur = admin(client, creer_collaborateur)
    navigateur.post(f"{ADMIN}/desistements/{signalement['id']}/confirmer", json={"version": 1})
    assert club(en_base, etab).etat is EtatClub.en_regularisation

    nouveau = creer_encadreur("nouveau", etablissement_id=etab)
    rattacher(en_base, nouveau.id, etab)

    assert club(en_base, etab).etat is EtatClub.actif


# Confirmation par l'équipe (décision 2) ---------------------------------------------------------------------


def test_l_equipe_confirme_une_affiliation_et_le_club_est_recalcule(
    client: Any, en_base: Callable[..., Any], creer_collaborateur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    ajouter_eleves(en_base, etab, 20)
    attente = ajouter_eleves(en_base, etab, 1, etat=EtatAdhesion.en_attente_validation)[0]
    adhesion = en_base(lambda db: db.scalar(select(Adhesion).where(Adhesion.eleve_id == attente)))
    navigateur = admin(client, creer_collaborateur)

    reponse = navigateur.post(
        f"{ADMIN}/affiliations/valider", json={"elements": [{"id": str(adhesion.id), "version": adhesion.version}]}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["echecs"] == []
    assert club(en_base, etab).etat is EtatClub.actif


# Échéances quotidiennes -------------------------------------------------------------------------------------


def traiter() -> echeances.Bilan:
    async def executer() -> echeances.Bilan:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            return await echeances.traiter(db)

    return asyncio.run(executer())


def rappels(en_base: Callable[..., Any]) -> int:
    return len(
        list(
            en_base(
                lambda db: db.scalars(select(Notification.id).where(Notification.type == "club_rappel_regularisation"))
            )
        )
    )


def test_les_rappels_partent_a_j7_et_j14_une_seule_fois_puis_la_suspension(
    en_base: Callable[..., Any], heure: Horloge, equipe: list[Any], etab: UUID
) -> None:
    club_actif(en_base, equipe, etab)
    en_base(lambda db: _retirer_un_eleve(db, etab))
    rattacher(en_base, equipe[0].id, etab)
    assert club(en_base, etab).etat is EtatClub.en_regularisation

    heure.avancer(6)
    assert traiter() == echeances.Bilan(0, 0)
    heure.avancer(1)
    assert traiter() == echeances.Bilan(0, 1)
    assert traiter() == echeances.Bilan(0, 0)
    assert rappels(en_base) == 3
    heure.avancer(7)
    assert traiter() == echeances.Bilan(0, 1)
    assert rappels(en_base) == 6
    heure.avancer(1)
    assert traiter() == echeances.Bilan(1, 0)
    assert club(en_base, etab).etat is EtatClub.suspendu
    assert traiter() == echeances.Bilan(0, 0)


async def _retirer_un_eleve(db: AsyncSession, etab: UUID) -> None:
    adhesion = await db.scalar(
        select(Adhesion)
        .join(Club, Club.id == Adhesion.club_id)
        .where(Club.etablissement_id == etab, Adhesion.etat == EtatAdhesion.active)
        .limit(1)
    )
    adhesion.etat = EtatAdhesion.retiree
