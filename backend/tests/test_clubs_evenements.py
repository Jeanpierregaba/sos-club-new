"""Événements qui changent les effectifs, passés par leurs routes (spec 033, relecture) : suspension d'un compte,
changements d'établissement, gel d'un club suspendu, confirmations simultanées, nouvelle demande d'affiliation,
remplacement d'un établissement proposé, journal de création."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.affiliations import confirmer_affiliation, remplacer_etablissement
from app.clubs.models import Adhesion, Club, ClubStatut, EtatAdhesion, EtatClub
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.referentiel.models import Etablissement, StatutEtablissement, TypeEtablissement
from tests.activation import ajouter_eleves, peupler, rattacher
from tests.conftest import Navigateur, connecter_admin, etablissement_de, moteur_test
from tests.espace_club import FICHE, connecter

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def etab(en_base: Callable[..., Any]) -> UUID:
    return etablissement_de(en_base, "grand-lome")


def club(en_base: Callable[..., Any], etab: UUID) -> Club:
    return en_base(
        lambda db: db.scalar(
            select(Club)
            .where(Club.etablissement_id == etab, Club.etat != EtatClub.refuse)
            .execution_options(populate_existing=True)
        )
    )


def dernieres_causes(en_base: Callable[..., Any], club_id: UUID) -> list[str]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(ClubStatut.cause).where(ClubStatut.club_id == club_id).order_by(ClubStatut.cree_le)
            )
        )
    )


def changer_detablissement(navigateur: Navigateur, chemin: str, etablissement_id: UUID) -> int:
    version = navigateur.get(chemin).json()["version"]
    return navigateur.patch(chemin, json={"version": version, "etablissement_id": str(etablissement_id)}).status_code


def club_actif_avec(
    en_base: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_eleve: Callable[..., Any],
    etab: UUID,
) -> tuple[Any, Any]:
    """Un club actif dont un encadreur (« prof ») et un élève (« ama », confirmé) peuvent se connecter."""
    peupler(en_base, etab, 2, 20)
    prof = creer_encadreur("prof", etablissement_id=etab)
    rattacher(en_base, prof.id, etab)
    ama = creer_eleve("ama", "Ama Confirmée", etablissement_id=etab)
    club_id = club(en_base, etab).id
    en_base(lambda db: _confirmee(db, ama.id, club_id))
    en_base(lambda db: activation.recalculer(db, club_id, "test"))
    assert club(en_base, etab).etat is EtatClub.actif
    return prof, ama


async def _confirmee(db: AsyncSession, eleve_id: UUID, club_id: UUID) -> None:
    db.add(Adhesion(eleve_id=eleve_id, club_id=club_id, etat=EtatAdhesion.active))


# Événements passés par leurs routes --------------------------------------------------------------------------


def test_suspendre_un_encadreur_depuis_l_admin_ouvre_la_regularisation_et_le_reactiver_la_referme(
    client: Any,
    en_base: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_eleve: Callable[..., Any],
    etab: UUID,
) -> None:
    prof, _ = club_actif_avec(en_base, creer_encadreur, creer_eleve, etab)
    creer_collaborateur("gestion", droits={("inscrits", "consulter"), ("inscrits", "modifier")}, double_auth=True)
    admin = Navigateur(client)
    connecter_admin(admin, "gestion")  # type: ignore[arg-type]

    reponse = admin.post(f"/api/admin/inscrits/{prof.id}/suspendre", json={"motif": "Compte à vérifier."})

    assert reponse.status_code == 200, reponse.text
    assert club(en_base, etab).etat is EtatClub.en_regularisation
    assert dernieres_causes(en_base, club(en_base, etab).id)[-1] == "compte_suspendu"

    admin.post(f"/api/admin/inscrits/{prof.id}/reactiver", json={"motif": "Vérifié."})

    assert club(en_base, etab).etat is EtatClub.actif
    assert dernieres_causes(en_base, club(en_base, etab).id)[-1] == "compte_reactive"


def test_un_eleve_qui_change_d_etablissement_fait_passer_l_ancien_club_sous_le_seuil(
    client: Any,
    en_base: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_eleve: Callable[..., Any],
    etab: UUID,
) -> None:
    club_actif_avec(en_base, creer_encadreur, creer_eleve, etab)

    assert changer_detablissement(connecter(client, "ama"), "/api/eleves/moi", etablissement_de(en_base, "kara")) == 200

    assert club(en_base, etab).etat is EtatClub.en_regularisation
    assert dernieres_causes(en_base, club(en_base, etab).id)[-1] == "changement_etablissement"


def test_un_encadreur_qui_change_d_etablissement_fait_passer_l_ancien_club_sous_le_seuil(
    client: Any,
    en_base: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_eleve: Callable[..., Any],
    etab: UUID,
) -> None:
    club_actif_avec(en_base, creer_encadreur, creer_eleve, etab)
    kara = etablissement_de(en_base, "kara")

    assert changer_detablissement(connecter(client, "prof"), "/api/encadreurs/moi", kara) == 200

    assert club(en_base, etab).etat is EtatClub.en_regularisation
    assert club(en_base, kara).etat is EtatClub.en_constitution


# Gel d'un club suspendu --------------------------------------------------------------------------------------


def test_un_club_dont_l_echeance_est_passee_ne_publie_plus_et_quitte_la_liste_publique(
    client: Any,
    en_base: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    creer_eleve: Callable[..., Any],
    etab: UUID,
) -> None:
    _, ama = club_actif_avec(en_base, creer_encadreur, creer_eleve, etab)
    club_id = club(en_base, etab).id
    # Ama préside ; l'échéance de la régularisation est passée, sans que personne ne l'ait encore écrite.
    en_base(
        lambda db: db.execute(
            update(Club)
            .where(Club.id == club_id)
            .values(
                president_id=ama.id,
                etat=EtatClub.en_regularisation,
                regularisation_jusquau=activation.maintenant() - timedelta(hours=1),
            )
        )
    )

    proposition = connecter(client, "ama").post(FICHE, json={"axes": ["sante-environnement"]})

    assert proposition.status_code == 403
    assert client.get("/api/clubs").json() == []
    assert client.get(f"/api/clubs/{club_id}").json()["statut"] == "suspendu"
    # Ses points personnels et son compte restent.
    assert en_base(lambda db: db.get(Eleve, ama.id)) is not None


# Concurrence -------------------------------------------------------------------------------------------------


def test_deux_confirmations_simultanees_qui_franchissent_le_seuil_n_activent_qu_une_fois(
    en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any], etab: UUID
) -> None:
    effectif = peupler(en_base, etab, 3, 19)
    attente = ajouter_eleves(en_base, etab, 2, etat=EtatAdhesion.en_attente_validation)
    auteur = creer_utilisateur("auteur")

    async def confirmer(eleve_id: UUID) -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            adhesion = await db.scalar(select(Adhesion).where(Adhesion.eleve_id == eleve_id).with_for_update())
            club_lu = await db.get(Club, adhesion.club_id)
            compte = await db.get(Utilisateur, auteur.id)
            await confirmer_affiliation(db, adhesion, club_lu, compte, "test", None)
            await db.commit()

    async def deux() -> None:
        await asyncio.gather(confirmer(attente[0]), confirmer(attente[1]))

    asyncio.run(deux())

    assert club(en_base, etab).etat is EtatClub.actif
    activations = en_base(
        lambda db: db.scalars(
            select(ClubStatut.id).where(ClubStatut.club_id == effectif.club_id, ClubStatut.nouveau == EtatClub.actif)
        )
    )
    assert len(list(activations)) == 1


# Nouvelle demande d'affiliation, remplacement d'établissement, journal de création -------------------------


def test_un_eleve_refuse_redemande_son_affiliation(
    client: Any, en_base: Callable[..., Any], creer_eleve: Callable[..., Any], etab: UUID
) -> None:
    eleve = creer_eleve("kofi", "Kofi Refusé", etablissement_id=etab)
    club_id = activation_club(en_base, etab)
    en_base(lambda db: _refusee(db, eleve.id, club_id))
    navigateur = connecter(client, "kofi")

    reponse = navigateur.post("/api/clubs/moi/affiliation")

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["affiliation"]["etat"] == "en_attente_validation"
    assert navigateur.post("/api/clubs/moi/affiliation").status_code == 409


def activation_club(en_base: Callable[..., Any], etab: UUID) -> UUID:
    return en_base(lambda db: activation.club_de(db, etab)).id


async def _refusee(db: AsyncSession, eleve_id: UUID, club_id: UUID) -> None:
    db.add(Adhesion(eleve_id=eleve_id, club_id=club_id, etat=EtatAdhesion.refusee, motif_refus="Erreur."))


def test_remplacer_un_etablissement_propose_deplace_son_club(
    en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any], etab: UUID
) -> None:
    async def proposer(db: AsyncSession) -> UUID:
        cible = await db.get(Etablissement, etab)
        proposition = Etablissement(
            iesg_id=cible.iesg_id, nom="Lycée proposé", nom_normalise="lycee propose",
            type=TypeEtablissement.lycee, statut=StatutEtablissement.propose,
        )  # fmt: skip
        db.add(proposition)
        await db.flush()
        return proposition.id

    propose = en_base(proposer)
    peupler(en_base, propose, 3, 21)
    ancien = club(en_base, propose)
    auteur = creer_utilisateur("equipe")

    async def remplacer(db: AsyncSession) -> None:
        await db.execute(update(Eleve).where(Eleve.etablissement_id == propose).values(etablissement_id=etab))
        await remplacer_etablissement(db, propose, etab, await db.get(Utilisateur, auteur.id), None)

    en_base(remplacer)

    assert en_base(lambda db: db.get(Club, ancien.id)).etat is EtatClub.refuse
    nouveau = club(en_base, etab)
    assert nouveau.etat is EtatClub.actif
    assert en_base(lambda db: activation.effectifs(db, nouveau.id)) == (3, 21)


def test_la_naissance_d_un_club_ouvre_son_journal(en_base: Callable[..., Any], etab: UUID) -> None:
    club_id = activation_club(en_base, etab)
    activation_club(en_base, etab)

    assert dernieres_causes(en_base, club_id) == ["creation"]
