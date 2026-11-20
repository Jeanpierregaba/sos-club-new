"""Modification de l'identité et du profil d'un inscrit par l'équipe (spec 045)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin.models import JournalAudit
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Classe, Eleve
from app.encadreurs.models import Encadreur
from tests.conftest import connecter_admin

INSCRITS = "/api/admin/inscrits"
GESTION = {("tableau_de_bord", "consulter"), ("inscrits", "consulter"), ("inscrits", "modifier")}
MOTIF = "Faute de frappe signalée par l'établissement"


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("gestion", droits=GESTION, double_auth=True)
    connecter_admin(client, "gestion")
    return client


def journal(en_base: Callable[..., Any]) -> list[JournalAudit]:
    return en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "profil_modifie_par_equipe"))
    ).all()


def version(client: TestClient, utilisateur_id: Any) -> int | None:
    return client.get(f"{INSCRITS}/{utilisateur_id}").json()["version"]


def modifier(client: TestClient, utilisateur_id: Any, **champs: Any) -> Any:
    corps = {"motif": MOTIF, "version": version(client, utilisateur_id)} | champs
    return client.patch(f"{INSCRITS}/{utilisateur_id}", json=corps)


# Élève --------------------------------------------------------------------------------------------------------


def test_lequipe_modifie_lidentite_et_la_classe_dun_eleve(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()

    reponse = modifier(
        gestionnaire, eleve.id, prenom="  Afi ", nom="Mensah", telephone="+228 90 12 34 56", classe="tle"
    )

    assert reponse.status_code == 200, reponse.text
    fiche = reponse.json()
    assert (fiche["prenom"], fiche["nom"], fiche["telephone"]) == ("Afi", "Mensah", "+22890123456")
    assert fiche["eleve"]["classe"] == "tle"
    assert fiche["historique"][0]["action"] == "profil_modifie_par_equipe"
    (entree,) = journal(en_base)
    assert entree.details["motif"] == MOTIF
    assert sorted(entree.details["champs"]) == ["classe", "nom", "prenom", "telephone"]
    assert entree.details["avant"] == {"classe": Classe.seconde.value}
    assert entree.details["apres"] == {"classe": "tle"}


def test_le_journal_ne_garde_aucune_donnee_didentite(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()

    modifier(gestionnaire, eleve.id, prenom="Kossiwa", nom="Agbeko", email="kossiwa@exemple.tg", telephone="90123456")

    (entree,) = journal(en_base)
    texte = str(entree.details).lower()
    for valeur in ("kossiwa", "agbeko", "exemple.tg", "90123456", "jean", "kodjo"):
        assert valeur not in texte


def test_lemail_dun_eleve_peut_etre_retire(
    gestionnaire: TestClient, creer_utilisateur: Callable[..., Any], creer_eleve: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:  # fmt: skip
    eleve = creer_eleve()
    en_base(lambda db: _changer_email(db, eleve.id, "ancien@exemple.tg"))

    reponse = modifier(gestionnaire, eleve.id, email="")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["email"] is None


async def _changer_email(db: Any, utilisateur_id: Any, email: str) -> None:
    (await db.get(Utilisateur, utilisateur_id)).email = email


def test_une_fonction_est_refusee_pour_un_eleve(gestionnaire: TestClient, creer_eleve: Callable[..., Any]) -> None:
    eleve = creer_eleve()

    assert modifier(gestionnaire, eleve.id, fonction="enseignant").status_code == 422


# Encadreur ----------------------------------------------------------------------------------------------------


def test_lequipe_modifie_le_profil_dun_encadreur(
    gestionnaire: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    encadreur = creer_encadreur()

    reponse = modifier(
        gestionnaire, encadreur.id, fonction="autre", fonction_precision="Bibliothécaire", discipline="SVT",
        commune="Golfe 3",
    )  # fmt: skip

    assert reponse.status_code == 200, reponse.text
    profil = reponse.json()["encadreur"]
    assert (profil["fonction"], profil["fonction_precision"], profil["discipline"], profil["commune"]) == (
        "autre", "Bibliothécaire", "SVT", "Golfe 3",
    )  # fmt: skip
    (entree,) = journal(en_base)
    assert entree.details["avant"] == {
        "fonction": "enseignant", "fonction_precision": None, "discipline": None, "commune": None,
    }  # fmt: skip


@pytest.mark.parametrize(
    "champs",
    [
        {"email": ""},
        {"telephone": ""},
        {"commune": "  "},
        {"fonction": "autre"},
        {"classe": "3e"},
    ],
)
def test_les_regles_de_lencadreur_sappliquent(
    gestionnaire: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any],
    champs: dict[str, Any],
) -> None:  # fmt: skip
    encadreur = creer_encadreur()

    reponse = modifier(gestionnaire, encadreur.id, **champs)

    assert reponse.status_code == 422, reponse.text
    assert journal(en_base) == []


# Règles communes ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "champs",
    [
        {"prenom": "  "},
        {"nom": ""},
        {"email": "pas-un-email"},
        {"telephone": "12"},
        {"classe": "CM2"},
        {"motif": "court"},
    ],
)
def test_une_valeur_invalide_est_refusee(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any], champs: dict[str, Any]
) -> None:
    eleve = creer_eleve()

    reponse = modifier(gestionnaire, eleve.id, **champs)

    assert reponse.status_code == 422, reponse.text
    assert journal(en_base) == []
    utilisateur = en_base(lambda db: db.get(Utilisateur, eleve.id))
    assert (utilisateur.prenom, utilisateur.nom) == ("Jean", "Kodjo")


def test_un_email_deja_pris_est_refuse(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], creer_encadreur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:  # fmt: skip
    eleve = creer_eleve()
    creer_encadreur()

    reponse = modifier(gestionnaire, eleve.id, email="Encadreur1@Ecole.tg")

    assert reponse.status_code == 409
    assert journal(en_base) == []


def test_rien_a_changer_est_refuse(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()

    reponse = modifier(gestionnaire, eleve.id, prenom="Jean", classe="2nde")

    assert reponse.status_code == 422
    assert reponse.json()["detail"] == "Rien n'a changé."
    assert journal(en_base) == []


def test_une_version_perimee_est_refusee(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    perimee = version(gestionnaire, eleve.id)
    assert modifier(gestionnaire, eleve.id, prenom="Afi").status_code == 200

    reponse = gestionnaire.patch(f"{INSCRITS}/{eleve.id}", json={"motif": MOTIF, "version": perimee, "nom": "Autre"})

    assert reponse.status_code == 409
    assert en_base(lambda db: db.get(Utilisateur, eleve.id)).nom == "Kodjo"


def test_la_version_monte_quand_seule_lidentite_change(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()
    avant = version(gestionnaire, eleve.id)

    modifier(gestionnaire, eleve.id, prenom="Afi")

    assert en_base(lambda db: db.get(Eleve, eleve.id)).version == avant + 1


def test_un_compte_sans_profil_se_modifie_sans_version(
    gestionnaire: TestClient, creer_utilisateur: Callable[..., Any]
) -> None:
    ancien = creer_utilisateur("ancien", Role.eleve)

    reponse = gestionnaire.patch(f"{INSCRITS}/{ancien.id}", json={"motif": MOTIF, "version": None, "nom": "Ayivi"})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["nom"] == "Ayivi"


# Droits -------------------------------------------------------------------------------------------------------


def test_un_collaborateur_ne_se_modifie_pas_ici(
    gestionnaire: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    autre = creer_collaborateur("autre")

    reponse = gestionnaire.patch(f"{INSCRITS}/{autre.id}", json={"motif": MOTIF, "version": None, "nom": "X"})

    assert reponse.status_code == 409


def test_un_compte_introuvable(gestionnaire: TestClient) -> None:
    reponse = gestionnaire.patch(
        f"{INSCRITS}/0190a6f6-0000-7000-8000-000000000000", json={"motif": MOTIF, "version": None, "nom": "X"}
    )

    assert reponse.status_code == 404


@pytest.mark.parametrize(
    ("droits", "dre"),
    [
        ({("inscrits", "consulter")}, None),
        ({("inscrits", "consulter"), ("inscrits", "modifier")}, "grand-lome"),
    ],
)
def test_modifier_exige_le_droit_national(
    client: TestClient, creer_collaborateur: Callable[..., Any], creer_eleve: Callable[..., Any],
    en_base: Callable[..., Any], droits: set[tuple[str, str]], dre: str | None,
) -> None:  # fmt: skip
    eleve = creer_eleve()
    creer_collaborateur("lecteur", droits=droits, perimetre_dre=dre, double_auth=True)
    connecter_admin(client, "lecteur")

    reponse = client.patch(f"{INSCRITS}/{eleve.id}", json={"motif": MOTIF, "version": 1, "nom": "Ayivi"})

    assert reponse.status_code == 403
    assert en_base(lambda db: db.get(Utilisateur, eleve.id)).nom == "Kodjo"


def test_un_eleve_ne_modifie_pas_un_inscrit(client: TestClient, creer_eleve: Callable[..., Any]) -> None:
    from tests.conftest import MOT_DE_PASSE

    eleve = creer_eleve()
    autre = creer_eleve("eleve2", affiche="Autre Pseudo")
    client.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": MOT_DE_PASSE})

    reponse = client.patch(f"{INSCRITS}/{autre.id}", json={"motif": MOTIF, "version": 1, "nom": "Ayivi"})

    assert reponse.status_code in (401, 403)
    assert eleve.id != autre.id


def test_la_modification_nest_pas_mise_en_cache(gestionnaire: TestClient, creer_eleve: Callable[..., Any]) -> None:
    eleve = creer_eleve()

    reponse = modifier(gestionnaire, eleve.id, prenom="Afi")

    assert reponse.headers["cache-control"] == "no-store"


def test_lencadreur_garde_son_profil_apres_modification(
    gestionnaire: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    encadreur = creer_encadreur()

    modifier(gestionnaire, encadreur.id, prenom="Komla")

    profil = en_base(lambda db: db.get(Encadreur, encadreur.id))
    assert profil.etat.value == "actif"


# Après relecture ----------------------------------------------------------------------------------------------


def test_un_email_change_nest_plus_confirme_et_son_empreinte_est_journalisee(
    gestionnaire: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    import hashlib
    from datetime import UTC, datetime

    encadreur = creer_encadreur()

    async def confirmer(db: Any) -> None:
        (await db.get(Utilisateur, encadreur.id)).email_confirme_le = datetime.now(UTC)

    en_base(confirmer)

    reponse = modifier(gestionnaire, encadreur.id, email="  Nouveau@Ecole.tg ")

    assert reponse.status_code == 200, reponse.text
    utilisateur = en_base(lambda db: db.get(Utilisateur, encadreur.id))
    assert (utilisateur.email, utilisateur.email_confirme_le) == ("nouveau@ecole.tg", None)
    (entree,) = journal(en_base)
    assert entree.details["email_empreinte"] == hashlib.sha256(b"nouveau@ecole.tg").hexdigest()
    assert "nouveau@ecole.tg" not in str(entree.details)


def test_un_visiteur_ne_se_modifie_pas_ici(gestionnaire: TestClient, creer_utilisateur: Callable[..., Any]) -> None:
    visiteur = creer_utilisateur("curieux", Role.visiteur, email="curieux@exemple.tg")

    reponse = gestionnaire.patch(f"{INSCRITS}/{visiteur.id}", json={"motif": MOTIF, "version": None, "nom": "X"})

    assert reponse.status_code == 409


def test_un_invite_est_introuvable(gestionnaire: TestClient, creer_utilisateur: Callable[..., Any]) -> None:
    invite = creer_utilisateur("invite1", Role.invite)

    reponse = gestionnaire.patch(f"{INSCRITS}/{invite.id}", json={"motif": MOTIF, "version": None, "nom": "X"})

    assert reponse.status_code == 404


def test_quitter_la_fonction_autre_efface_la_precision(
    gestionnaire: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    encadreur = creer_encadreur()
    assert (
        modifier(gestionnaire, encadreur.id, fonction="autre", fonction_precision="Bibliothécaire").status_code == 200
    )

    reponse = modifier(gestionnaire, encadreur.id, fonction="sante")

    assert reponse.status_code == 200, reponse.text
    assert (reponse.json()["encadreur"]["fonction"], reponse.json()["encadreur"]["fonction_precision"]) == (
        "sante", None,
    )  # fmt: skip
    entree = journal(en_base)[-1]
    assert entree.details["avant"] == {"fonction": "autre", "fonction_precision": "Bibliothécaire"}


def test_un_champ_invalide_bloque_tous_les_autres(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve()

    reponse = modifier(gestionnaire, eleve.id, prenom="Afi", classe="tle", email="pas-un-email")

    assert reponse.status_code == 422
    utilisateur = en_base(lambda db: db.get(Utilisateur, eleve.id))
    assert utilisateur.prenom == "Jean"
    assert en_base(lambda db: db.get(Eleve, eleve.id)).classe is Classe.seconde


def test_un_compte_suspendu_reste_modifiable(
    gestionnaire: TestClient, creer_eleve: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.comptes.models import StatutCompte

    eleve = creer_eleve()

    async def suspendre(db: Any) -> None:
        (await db.get(Utilisateur, eleve.id)).statut = StatutCompte.suspendu

    en_base(suspendre)

    assert modifier(gestionnaire, eleve.id, nom="Ayivi").status_code == 200


def test_un_encadreur_connecte_ne_modifie_pas_un_inscrit(
    client: TestClient, creer_eleve: Callable[..., Any], creer_encadreur: Callable[..., Any]
) -> None:
    from tests.conftest import MOT_DE_PASSE

    eleve = creer_eleve()
    creer_encadreur()
    client.post("/api/comptes/connexion", json={"identifiant": "encadreur1", "mot_de_passe": MOT_DE_PASSE})

    reponse = client.patch(f"{INSCRITS}/{eleve.id}", json={"motif": MOTIF, "version": 1, "nom": "Ayivi"})

    assert reponse.status_code in (401, 403)
