"""Compte visiteur (spec 030) : inscription, code de confirmation, connexion, quiz « jeux » sans points, purge."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.comptes.models import Role, StatutCompte, Utilisateur
from app.config import settings
from app.courriel import envoi
from app.visiteurs import codes
from app.visiteurs.models import CodeConfirmation, Visiteur
from app.visiteurs.service import purger_non_confirmes
from tests.certification import creer_parcours
from tests.conftest import moteur_test
from tests.quiz import Horloge, creer_quiz, figer_horloge, gains, jouer

INSCRIPTION = "/api/visiteurs/inscription"
CONFIRMATION = "/api/visiteurs/confirmation"
RENVOI = "/api/visiteurs/confirmation/renvoi"
CONNEXION = "/api/comptes/connexion"
MOT_DE_PASSE = "un-mot-de-passe-solide"


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


@pytest.fixture
def boite(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str, str | None]]:
    """Les e-mails « envoyés ». Le SMTP reste non configuré : l'API renvoie aussi le code de test."""
    envoyes: list[tuple[str, str, str, str | None]] = []

    async def envoyer(destinataire: str, sujet: str, texte: str, html: str | None = None) -> None:
        envoyes.append((destinataire, sujet, texte, html))

    monkeypatch.setattr(envoi, "envoyer", envoyer)
    return envoyes


def formulaire(**champs: Any) -> dict[str, Any]:
    valeurs: dict[str, Any] = {
        "prenom": "Koffi Jean",
        "nom": "Amégan",
        "telephone": "+228 90 12 34 56",
        "ville": "Lomé",
        "email": "Koffi.Amegan@Gmail.com",
        "region": "maritime",
        "sexe": "masculin",
        "statut": "Étudiant / Universitaire",
        "mot_de_passe": MOT_DE_PASSE,
        "charte": True,
        "majeur_ou_accord": True,
    }
    return valeurs | champs


def inscrire(client: TestClient, **champs: Any) -> dict[str, Any]:
    reponse = client.post(INSCRIPTION, json=formulaire(**champs))
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def visiteur(en_base: Callable[..., Any]) -> Utilisateur:
    return en_base(lambda db: db.scalar(select(Utilisateur).where(Utilisateur.role == Role.visiteur)))


def code_en_base(en_base: Callable[..., Any]) -> CodeConfirmation | None:
    return en_base(lambda db: db.scalar(select(CodeConfirmation)))


def reculer_envoi(en_base: Callable[..., Any], minutes: float) -> None:
    """Fait comme si le dernier code était parti il y a `minutes` minutes."""
    ligne = code_en_base(en_base)
    assert ligne is not None
    en_base(
        lambda db: db.execute(update(CodeConfirmation).values(envoye_le=ligne.envoye_le - timedelta(minutes=minutes)))
    )


# Inscription -------------------------------------------------------------------------------------------------


def test_linscription_cree_un_compte_non_confirme_et_envoie_un_code(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    corps = inscrire(client)

    compte = visiteur(en_base)
    assert (compte.email, compte.telephone, compte.email_confirme_le) == (
        "koffi.amegan@gmail.com",
        "+22890123456",
        None,
    )
    profil = en_base(lambda db: db.get(Visiteur, compte.id))
    assert (profil.ville, profil.region, profil.statut) == ("Lomé", "maritime", "Étudiant / Universitaire")
    assert corps["email"] == "koffi.amegan@gmail.com"
    assert len(corps["code_de_test"]) == 6 and corps["code_de_test"].isdigit()
    (destinataire, sujet, texte, html) = boite[0]
    assert destinataire == "koffi.amegan@gmail.com"
    assert corps["code_de_test"] in sujet and corps["code_de_test"] in texte and html
    # Pas de session avant la confirmation.
    assert client.get("/api/comptes/moi").status_code == 401
    # Le code n'est gardé que sous forme d'empreinte.
    ligne = code_en_base(en_base)
    assert ligne is not None and corps["code_de_test"] not in ligne.code_hash


@pytest.mark.parametrize(
    "champs",
    [
        {"telephone": ""},
        {"ville": "  "},
        {"email": "pas-une-adresse"},
        {"charte": False},
        {"majeur_ou_accord": False},
        {"region": "lune"},
        {"mot_de_passe": "court"},
        {"role": "eleve"},
    ],
)
def test_un_formulaire_invalide_est_refuse(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any], champs: dict[str, Any]
) -> None:
    assert client.post(INSCRIPTION, json=formulaire(**champs)).status_code == 422
    assert visiteur(en_base) is None
    assert boite == []


def test_un_email_deja_pris_est_refuse(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur], boite: list[Any]
) -> None:
    creer_utilisateur("kofi", Role.encadreur, email="koffi.amegan@gmail.com")

    reponse = client.post(INSCRIPTION, json=formulaire())

    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Cet email est déjà pris."


def test_un_compte_non_confirme_de_plus_de_7_jours_libere_ladresse(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    inscrire(client)
    assert client.post(INSCRIPTION, json=formulaire()).status_code == 409
    en_base(lambda db: db.execute(update(Utilisateur).values(cree_le=func.now() - timedelta(days=8))))

    assert client.post(INSCRIPTION, json=formulaire()).status_code == 201
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(Visiteur))) == 1


def test_inscriptions_fermees(client: TestClient, monkeypatch: pytest.MonkeyPatch, boite: list[Any]) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", False)

    assert client.post(INSCRIPTION, json=formulaire()).status_code == 403
    assert boite == []


def test_la_limite_par_adresse_sapplique(client: TestClient, monkeypatch: pytest.MonkeyPatch, boite: list[Any]) -> None:
    monkeypatch.setattr(settings, "inscriptions_max_adresse", 1)
    inscrire(client)

    assert client.post(INSCRIPTION, json=formulaire(email="autre@gmail.com")).status_code == 429


def test_en_production_sans_smtp_aucun_compte_nest_cree(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(type(settings), "production", property(lambda _: True))
    monkeypatch.setattr(settings, "smtp_hote", None)

    reponse = client.post(INSCRIPTION, json=formulaire())

    assert reponse.status_code == 503
    assert visiteur(en_base) is None


def test_un_envoi_en_echec_ne_cree_pas_de_compte(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def panne(*_: Any, **__: Any) -> None:
        raise envoi.EnvoiImpossible

    monkeypatch.setattr(envoi, "envoyer", panne)

    assert client.post(INSCRIPTION, json=formulaire()).status_code == 503
    assert visiteur(en_base) is None


# Confirmation ------------------------------------------------------------------------------------------------


def test_le_bon_code_confirme_et_ouvre_la_session(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    code = inscrire(client)["code_de_test"]

    reponse = client.post(CONFIRMATION, json={"email": "KOFFI.AMEGAN@gmail.com", "code": f" {code[:3]} {code[3:]} "})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["role"] == "visiteur"
    assert visiteur(en_base).email_confirme_le is not None
    assert code_en_base(en_base) is None
    assert client.get("/api/visiteurs/moi").json()["ville"] == "Lomé"
    # Le code ne resert pas.
    client.cookies.clear()
    assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": code}).status_code == 400


def test_un_mauvais_code_est_compte_et_cinq_echecs_lannulent(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    code = inscrire(client)["code_de_test"]
    faux = f"{(int(code) + 1) % 10**6:06d}"

    for _ in range(5):
        assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": faux}).status_code == 400

    ligne = code_en_base(en_base)
    assert ligne is not None and ligne.essais == 5
    # Même le bon code ne passe plus.
    assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": code}).status_code == 400
    assert visiteur(en_base).email_confirme_le is None


def test_un_code_expire_est_refuse(client: TestClient, en_base: Callable[..., Any], boite: list[Any]) -> None:
    code = inscrire(client)["code_de_test"]
    en_base(lambda db: db.execute(update(CodeConfirmation).values(expire_le=func.now() - timedelta(seconds=1))))

    assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": code}).status_code == 400


def test_le_code_dun_autre_compte_ne_confirme_pas(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    code = inscrire(client)["code_de_test"]
    autre = inscrire(client, email="ama@gmail.com", telephone="91000000")["code_de_test"]
    if autre == code:
        pytest.skip("Les deux codes tirés coïncident (une chance sur un million).")

    reponse = client.post(CONFIRMATION, json={"email": "ama@gmail.com", "code": code})

    assert reponse.status_code == 400
    confirmee = en_base(
        lambda db: db.scalar(select(Utilisateur.email_confirme_le).where(Utilisateur.email == "ama@gmail.com"))
    )
    assert confirmee is None


def test_une_adresse_inconnue_recoit_la_meme_reponse(client: TestClient, boite: list[Any]) -> None:
    reponse = client.post(CONFIRMATION, json={"email": "inconnu@gmail.com", "code": "123456"})

    assert reponse.status_code == 400
    assert client.post(RENVOI, json={"email": "inconnu@gmail.com"}).json() == {"code_de_test": None}
    assert boite == []


def test_deux_confirmations_simultanees_nen_valident_quune(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    from app.visiteurs import service

    code = inscrire(client)["code_de_test"]

    async def tenter() -> bool:
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            try:
                await service.confirmer(db, "koffi.amegan@gmail.com", code, "127.0.0.1")
            except service.Refus:
                return False
            await db.commit()
            return True

    async def deux() -> list[bool]:
        return list(await asyncio.gather(tenter(), tenter()))

    assert sorted(asyncio.run(deux())) == [False, True]


# Renvoi --------------------------------------------------------------------------------------------------------


def test_le_renvoi_remplace_le_code_une_fois_par_minute(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    ancien = inscrire(client)["code_de_test"]

    assert client.post(RENVOI, json={"email": "koffi.amegan@gmail.com"}).json() == {"code_de_test": None}
    assert len(boite) == 1

    reculer_envoi(en_base, 1.5)
    nouveau = client.post(RENVOI, json={"email": "koffi.amegan@gmail.com"}).json()["code_de_test"]

    assert nouveau and len(boite) == 2
    if nouveau != ancien:
        assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": ancien}).status_code == 400
    assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": nouveau}).status_code == 200


def test_au_plus_cinq_codes_par_heure(client: TestClient, en_base: Callable[..., Any], boite: list[Any]) -> None:
    inscrire(client)
    for _ in range(6):
        reculer_envoi(en_base, 2)
        client.post(RENVOI, json={"email": "koffi.amegan@gmail.com"})

    assert len(boite) == codes.ENVOIS_PAR_FENETRE

    # Une heure plus tard, la fenêtre repart.
    en_base(lambda db: db.execute(update(CodeConfirmation).values(fenetre_le=func.now() - timedelta(hours=1))))
    reculer_envoi(en_base, 2)
    client.post(RENVOI, json={"email": "koffi.amegan@gmail.com"})
    assert len(boite) == codes.ENVOIS_PAR_FENETRE + 1


# Connexion -------------------------------------------------------------------------------------------------------


def test_un_visiteur_non_confirme_qui_se_connecte_recoit_un_nouveau_code(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    inscrire(client)
    reculer_envoi(en_base, 2)

    reponse = client.post(CONNEXION, json={"identifiant": "koffi.amegan@gmail.com", "mot_de_passe": MOT_DE_PASSE})

    assert reponse.status_code == 200
    corps = reponse.json()
    assert (corps["etape"], corps["email"]) == ("confirmation", "koffi.amegan@gmail.com")
    assert corps["code_de_test"] and len(boite) == 2
    assert client.get("/api/comptes/moi").status_code == 401


def test_un_mauvais_mot_de_passe_ne_renvoie_pas_de_code(client: TestClient, boite: list[Any]) -> None:
    inscrire(client)

    reponse = client.post(
        CONNEXION, json={"identifiant": "koffi.amegan@gmail.com", "mot_de_passe": "faux-mot-de-passe"}
    )

    assert reponse.status_code == 401
    assert len(boite) == 1


def test_un_visiteur_confirme_se_connecte_par_son_email(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    code = inscrire(client)["code_de_test"]
    client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": code})
    client.cookies.clear()

    reponse = client.post(CONNEXION, json={"identifiant": "koffi.amegan@gmail.com", "mot_de_passe": MOT_DE_PASSE})

    assert reponse.json()["role"] == "visiteur"


# Droits du visiteur ----------------------------------------------------------------------------------------------


@pytest.fixture
def confirme(client: TestClient, boite: list[Any]) -> None:
    code = inscrire(client)["code_de_test"]
    assert client.post(CONFIRMATION, json={"email": "koffi.amegan@gmail.com", "code": code}).status_code == 200


@pytest.fixture
def heure(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    return figer_horloge(monkeypatch)


def test_un_visiteur_joue_aux_quiz_jeux_sans_points(
    client: TestClient, en_base: Callable[..., Any], confirme: None, heure: Horloge
) -> None:
    quiz = creer_quiz(en_base)

    etat = jouer(client, quiz, justes=15)

    assert etat["resultat"]["reussie"] is True
    assert gains(en_base, visiteur(en_base).id) == []


def test_un_visiteur_na_ni_certification_ni_parcours(
    client: TestClient, en_base: Callable[..., Any], confirme: None
) -> None:
    quiz = creer_parcours(en_base, places=[1])

    assert client.get("/api/certification").status_code == 403
    assert client.post(f"/api/quiz/{quiz[1].id}/tentatives").status_code == 403


def test_un_visiteur_na_ni_espace_eleve_ni_club_ni_article(client: TestClient, confirme: None) -> None:
    assert client.get("/api/eleves/moi").status_code == 403
    assert client.get("/api/encadreurs/moi").status_code == 403
    club = "00000000-0000-0000-0000-000000000001"
    assert client.post(f"/api/clubs/{club}/adhesions", json={}).status_code in (403, 404, 422)
    assert client.get("/api/mes-articles").status_code == 403


def test_un_visiteur_suspendu_ne_joue_plus(client: TestClient, en_base: Callable[..., Any], confirme: None) -> None:
    quiz = creer_quiz(en_base)
    en_base(lambda db: db.execute(update(Utilisateur).values(statut=StatutCompte.suspendu)))

    assert client.post(f"/api/quiz/{quiz.id}/tentatives").status_code in (401, 403)


# Purge -------------------------------------------------------------------------------------------------------------


def test_la_purge_efface_les_non_confirmes_de_plus_de_7_jours(
    client: TestClient, en_base: Callable[..., Any], boite: list[Any]
) -> None:
    inscrire(client, email="ancien@gmail.com")
    inscrire(client, email="recent@gmail.com")
    code = inscrire(client, email="confirme@gmail.com")["code_de_test"]
    client.post(CONFIRMATION, json={"email": "confirme@gmail.com", "code": code})
    en_base(
        lambda db: db.execute(
            update(Utilisateur)
            .where(Utilisateur.email.in_(["ancien@gmail.com", "confirme@gmail.com"]))
            .values(cree_le=datetime.now(UTC) - timedelta(days=8))
        )
    )

    assert en_base(purger_non_confirmes) == 1

    restants = en_base(lambda db: db.scalars(select(Utilisateur.email).where(Utilisateur.role == Role.visiteur)))
    assert sorted(restants) == ["confirme@gmail.com", "recent@gmail.com"]


def test_les_inscrits_se_filtrent_sur_les_visiteurs(
    client: TestClient, creer_collaborateur: Callable[..., Any], boite: list[Any]
) -> None:
    from tests.conftest import connecter_admin

    inscrire(client)
    creer_collaborateur("chef", droits={("inscrits", "consulter")})
    connecter_admin(client, "chef")

    corps = client.get("/api/admin/inscrits", params={"profil": "visiteur"}).json()

    assert corps["total"] == 1
    assert client.get(f"/api/admin/inscrits/{corps['inscrits'][0]['id']}").status_code == 200
