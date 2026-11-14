"""« Mon Club Santé » de l'encadreur (spec 033) : fiche, affiliations à confirmer, retrait, désistement, président."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select

from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub, SignalementDesistement
from app.encadreurs.models import EtatVerification
from app.notifications.models import Notification
from tests.activation import affilier, ajouter_eleves, rattacher
from tests.conftest import VERIFICATION_CLUBS, Navigateur, connecter_admin, etablissement_de
from tests.espace_club import connecter

MON_CLUB = "/api/clubs/mon-club-sante"

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def etab(en_base: Callable[..., Any]) -> UUID:
    return etablissement_de(en_base, "grand-lome")


@pytest.fixture
def equipe(en_base: Callable[..., Any], creer_encadreur: Callable[..., Any], etab: UUID) -> list[Any]:
    """Trois encadreurs vérifiés du même établissement, rattachés au club."""
    encadreurs = [creer_encadreur(f"encadreur{i}", etablissement_id=etab) for i in range(1, 4)]
    for encadreur in encadreurs:
        rattacher(en_base, encadreur.id, etab)
    return encadreurs


def club(en_base: Callable[..., Any], etab: UUID) -> Club:
    return en_base(lambda db: db.scalar(select(Club).where(Club.etablissement_id == etab, Club.etat != "refuse")))


def affiliation(en_base: Callable[..., Any], affiliation_id: UUID) -> Adhesion:
    return en_base(lambda db: db.get(Adhesion, affiliation_id))


def eleve_a_confirmer(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Any], etab: UUID, identifiant: str = "eleve1"
) -> tuple[Any, UUID]:
    eleve = creer_eleve(identifiant, affiche=f"Pseudo {identifiant}", etablissement_id=etab)
    return eleve, affilier(en_base, eleve.id, etab)


# Accès ------------------------------------------------------------------------------------------------------


def test_l_encadreur_voit_son_club_ses_seuils_et_son_equipe(
    client: Any, en_base: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    navigateur = connecter(client, "encadreur1")

    reponse = navigateur.get(MON_CLUB)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["statut"] == "en_constitution"
    assert (corps["nb_encadreurs"], corps["nb_eleves"]) == (3, 0)
    assert corps["seuils"] == {"encadreurs": 3, "eleves": 21, "delai_jours": 15}
    assert corps["etablissement"]["region"] == "Maritime"
    assert [m["moi"] for m in corps["equipe"]].count(True) == 1


def test_un_eleve_n_a_pas_d_espace_encadreur(client: Any, creer_eleve: Callable[..., Any]) -> None:
    creer_eleve("eleve1")
    assert connecter(client, "eleve1").get(MON_CLUB).status_code == 403


def test_un_encadreur_non_verifie_n_a_pas_de_club(client: Any, creer_encadreur: Callable[..., Any], etab: UUID) -> None:
    creer_encadreur("nouveau", etablissement_id=etab, etat=EtatVerification.en_attente)
    assert connecter(client, "nouveau").get(MON_CLUB).status_code == 403


def test_un_encadreur_verifie_sans_rattachement_recoit_404(
    client: Any, creer_encadreur: Callable[..., Any], etab: UUID
) -> None:
    creer_encadreur("seul", etablissement_id=etab)
    assert connecter(client, "seul").get(MON_CLUB).status_code == 404


# Affiliations -----------------------------------------------------------------------------------------------


def test_l_encadreur_voit_le_pseudonyme_et_la_classe_jamais_le_nom(
    client: Any, en_base: Callable[..., Any], creer_eleve: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    eleve_a_confirmer(en_base, creer_eleve, etab)

    corps = connecter(client, "encadreur1").get(f"{MON_CLUB}/affiliations").json()

    assert [(a["pseudonyme"], a["classe"]) for a in corps["a_confirmer"]] == [("Pseudo eleve1", "2nde")]
    texte = str(corps)
    assert "Kodjo" not in texte and "Jean" not in texte


def test_confirmer_le_21e_eleve_active_le_club(
    client: Any, en_base: Callable[..., Any], creer_eleve: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    ajouter_eleves(en_base, etab, 20)
    _, affiliation_id = eleve_a_confirmer(en_base, creer_eleve, etab)
    navigateur = connecter(client, "encadreur2")
    version = affiliation(en_base, affiliation_id).version

    reponse = navigateur.post(f"{MON_CLUB}/affiliations/{affiliation_id}/confirmer", json={"version": version})

    assert reponse.status_code == 200, reponse.text
    assert affiliation(en_base, affiliation_id).etat is EtatAdhesion.active
    assert club(en_base, etab).etat is EtatClub.actif
    assert navigateur.get(MON_CLUB).json()["statut"] == "actif"
    notifies = en_base(
        lambda db: db.scalars(select(Notification.utilisateur_id).where(Notification.type == "club_active"))
    )
    assert set(notifies) == {e.id for e in equipe}


def test_un_encadreur_d_un_autre_etablissement_ne_peut_pas_confirmer(
    client: Any,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Any],
    creer_encadreur: Callable[..., Any],
    equipe: list[Any],
    etab: UUID,
) -> None:
    _, affiliation_id = eleve_a_confirmer(en_base, creer_eleve, etab)
    ailleurs = etablissement_de(en_base, "kara")
    etranger = creer_encadreur("etranger", etablissement_id=ailleurs)
    rattacher(en_base, etranger.id, ailleurs)
    navigateur = connecter(client, "etranger")

    assert navigateur.get(f"{MON_CLUB}/affiliations").json()["a_confirmer"] == []
    reponse = navigateur.post(f"{MON_CLUB}/affiliations/{affiliation_id}/confirmer", json={"version": 1})

    assert reponse.status_code == 404
    assert affiliation(en_base, affiliation_id).etat is EtatAdhesion.en_attente_validation


def test_refuser_une_affiliation_demande_un_motif(
    client: Any, en_base: Callable[..., Any], creer_eleve: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    _, affiliation_id = eleve_a_confirmer(en_base, creer_eleve, etab)
    navigateur = connecter(client, "encadreur1")
    url = f"{MON_CLUB}/affiliations/{affiliation_id}/refuser"

    assert navigateur.post(url, json={"motif": "  ", "version": 1}).status_code == 422
    reponse = navigateur.post(url, json={"motif": "Pas inscrit dans notre lycée.", "version": 1})

    assert reponse.status_code == 200, reponse.text
    lue = affiliation(en_base, affiliation_id)
    assert (lue.etat, lue.motif_refus) == (EtatAdhesion.refusee, "Pas inscrit dans notre lycée.")


def test_une_double_confirmation_est_refusee(
    client: Any, en_base: Callable[..., Any], creer_eleve: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    _, affiliation_id = eleve_a_confirmer(en_base, creer_eleve, etab)
    url = f"{MON_CLUB}/affiliations/{affiliation_id}/confirmer"
    assert connecter(client, "encadreur1").post(url, json={"version": 1}).status_code == 200

    assert connecter(client, "encadreur2").post(url, json={"version": 1}).status_code == 409


def test_retirer_un_eleve_d_un_club_actif_ouvre_la_regularisation(
    client: Any, en_base: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    eleves = ajouter_eleves(en_base, etab, 21)
    rattacher(en_base, equipe[0].id, etab)
    assert club(en_base, etab).etat is EtatClub.actif
    adhesion = en_base(lambda db: db.scalar(select(Adhesion).where(Adhesion.eleve_id == eleves[0])))
    navigateur = connecter(client, "encadreur1")

    reponse = navigateur.post(
        f"{MON_CLUB}/affiliations/{adhesion.id}/retirer",
        json={"motif": "A quitté le lycée.", "version": adhesion.version},
    )

    assert reponse.status_code == 200, reponse.text
    lu = club(en_base, etab)
    assert lu.etat is EtatClub.en_regularisation
    assert navigateur.get(MON_CLUB).json()["regularisation_jusquau"] is not None


# Désistement ------------------------------------------------------------------------------------------------


def test_signaler_un_desistement_ne_change_rien_au_club(
    client: Any, en_base: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    navigateur = connecter(client, "encadreur1")
    corps = {"encadreur_id": str(equipe[1].id), "motif": "Muté dans un autre lycée."}

    reponse = navigateur.post(f"{MON_CLUB}/desistements", json=corps)

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["etat"] == "en_attente"
    assert navigateur.post(f"{MON_CLUB}/desistements", json=corps).status_code == 409
    fiche = navigateur.get(MON_CLUB).json()
    assert fiche["nb_encadreurs"] == 3
    assert [m["signalement_en_attente"] for m in fiche["equipe"] if m["utilisateur_id"] == str(equipe[1].id)] == [True]
    assert len(fiche["mes_signalements"]) == 1


def test_on_ne_signale_ni_soi_meme_ni_un_encadreur_d_ailleurs(
    client: Any, en_base: Callable[..., Any], creer_encadreur: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    ailleurs = etablissement_de(en_base, "kara")
    etranger = creer_encadreur("etranger", etablissement_id=ailleurs)
    rattacher(en_base, etranger.id, ailleurs)
    navigateur = connecter(client, "encadreur1")

    soi = navigateur.post(f"{MON_CLUB}/desistements", json={"encadreur_id": str(equipe[0].id), "motif": "Moi."})
    autre = navigateur.post(f"{MON_CLUB}/desistements", json={"encadreur_id": str(etranger.id), "motif": "Lui."})

    assert soi.status_code == 422
    assert autre.status_code == 404
    assert en_base(lambda db: db.scalar(select(SignalementDesistement.id))) is None


# Président --------------------------------------------------------------------------------------------------


def test_un_club_en_constitution_ne_recoit_pas_de_president(
    client: Any, en_base: Callable[..., Any], creer_eleve: Callable[..., Any], equipe: list[Any], etab: UUID
) -> None:
    eleves = ajouter_eleves(en_base, etab, 1)
    adhesion = en_base(lambda db: db.scalar(select(Adhesion.id).where(Adhesion.eleve_id == eleves[0])))

    reponse = connecter(client, "encadreur1").post(f"{MON_CLUB}/president", json={"affiliation_id": str(adhesion)})

    assert reponse.status_code == 409


def test_l_encadreur_propose_un_president_que_l_equipe_valide(
    client: Any,
    en_base: Callable[..., Any],
    creer_collaborateur: Callable[..., Any],
    equipe: list[Any],
    etab: UUID,
) -> None:
    eleves = ajouter_eleves(en_base, etab, 21)
    rattacher(en_base, equipe[0].id, etab)
    adhesion = en_base(lambda db: db.scalar(select(Adhesion.id).where(Adhesion.eleve_id == eleves[3])))
    navigateur = connecter(client, "encadreur1")

    reponse = navigateur.post(f"{MON_CLUB}/president", json={"affiliation_id": str(adhesion)})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["president_propose"] is not None
    assert navigateur.post(f"{MON_CLUB}/president", json={"affiliation_id": str(adhesion)}).status_code == 409

    creer_collaborateur("verif.clubs", droits=VERIFICATION_CLUBS, double_auth=True)
    admin = Navigateur(client)
    connecter_admin(admin, "verif.clubs")  # type: ignore[arg-type]
    passation = admin.get("/api/admin/clubs/passations").json()["passations"][0]
    assert admin.post(f"/api/admin/clubs/passations/{passation['id']}/valider", json={}).status_code == 200
    assert club(en_base, etab).president_id == eleves[3]
