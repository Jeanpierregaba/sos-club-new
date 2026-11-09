"""Inscription d'un élève (spec 017) : compte, profil, établissement proposé et points de bienvenue."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin.models import JournalAudit
from app.comptes.models import Role, Utilisateur
from app.config import settings
from app.eleves.models import Eleve
from app.points.models import MouvementPoints, Semestre
from app.points.service import aujourd_hui
from app.referentiel.models import Etablissement, Iesg, StatutEtablissement
from tests.fiche import fiche

INSCRIPTION = "/api/eleves/inscription"

pytestmark = pytest.mark.usefixtures("annuaire")


def etablissement_id(en_base: Callable[..., Any], nom: str = "Lycée de Tokoin I") -> str:
    return str(en_base(lambda db: db.scalar(select(Etablissement.id).where(Etablissement.nom == nom))))


def iesg_id(en_base: Callable[..., Any], nom: str = "IESG Golfe") -> str:
    return str(en_base(lambda db: db.scalar(select(Iesg.id).where(Iesg.nom == nom))))


def formulaire(en_base: Callable[..., Any], **champs: Any) -> dict[str, Any]:
    valeurs: dict[str, Any] = {
        "prenom": "Aya",
        "nom": "Mensah",
        "pseudonyme": "Aya la Curieuse",
        "identifiant": "aya.mensah",
        "mot_de_passe": "un-mot-de-passe",
        "classe": "2nde",
        "charte": True,
        "consentement_parent": True,
        "etablissement_id": etablissement_id(en_base),
        "fiche": fiche(),
    }
    return valeurs | champs


def compter(en_base: Callable[..., Any], modele: Any) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(modele)))


@pytest.fixture
def semestre(en_base: Callable[..., Any]) -> Semestre:
    async def inserer(db: Any) -> Semestre:
        element = Semestre(
            libelle="En cours", debut=aujourd_hui() - timedelta(days=5), fin=aujourd_hui() + timedelta(days=5)
        )
        db.add(element)
        return element

    return en_base(inserer)


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


# Parcours ----------------------------------------------------------------------------------------------------


def test_une_inscription_cree_le_compte_le_profil_les_points_et_la_session(
    client: TestClient, en_base: Callable[..., Any], semestre: Semestre
) -> None:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base, email="Aya@Exemple.tg"))

    assert reponse.status_code == 201, reponse.text
    corps = reponse.json()
    assert (corps["identifiant"], corps["role"]) == ("aya.mensah", "eleve")
    assert client.get("/api/comptes/moi").status_code == 200

    utilisateur = en_base(lambda db: db.get(Utilisateur, UUID(corps["id"])))
    eleve = en_base(lambda db: db.get(Eleve, utilisateur.id))
    assert utilisateur.consentement_le is not None
    assert utilisateur.email == "aya@exemple.tg"
    assert (eleve.pseudonyme, eleve.classe.value, eleve.charte_version) == (
        "Aya la Curieuse",
        "2nde",
        settings.version_charte,
    )
    (ligne,) = en_base(lambda db: db.scalars(select(MouvementPoints))).all()
    assert (ligne.montant, ligne.cle, ligne.semestre_id) == (100, f"bienvenue:{utilisateur.id}", semestre.id)
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "inscription_eleve"))
    ).all()
    assert entree.details["etablissement_propose"] is False


def test_letat_des_inscriptions_est_public(client: TestClient) -> None:
    assert client.get(INSCRIPTION).json() == {"ouvertes": True, "version_charte": settings.version_charte}


def test_les_inscriptions_fermees_refusent(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", None)
    monkeypatch.setattr(settings, "site_origine", "https://exemple.test")

    assert client.get(INSCRIPTION).json()["ouvertes"] is False
    assert client.post(INSCRIPTION, json=formulaire(en_base)).status_code == 403
    assert compter(en_base, Utilisateur) == 0


def test_deux_envois_identiques_ne_creent_quun_compte(client: TestClient, en_base: Callable[..., Any]) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base)).status_code == 201
    client.cookies.clear()

    second = client.post(INSCRIPTION, json=formulaire(en_base))

    assert second.status_code == 409
    assert (compter(en_base, Utilisateur), compter(en_base, MouvementPoints)) == (1, 1)


def test_un_eleve_connecte_ne_cree_pas_un_second_compte(client: TestClient, en_base: Callable[..., Any]) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base))

    reponse = client.post(INSCRIPTION, json=formulaire(en_base, identifiant="autre", pseudonyme="Kossi"))

    assert reponse.status_code == 409
    assert compter(en_base, Utilisateur) == 1


# Champs refusés ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["charte", "consentement_parent"])
def test_les_cases_sont_verifiees_par_lapi(client: TestClient, en_base: Callable[..., Any], case: str) -> None:
    assert client.post(INSCRIPTION, json=formulaire(en_base, **{case: False})).status_code == 422
    sans = formulaire(en_base)
    del sans[case]
    assert client.post(INSCRIPTION, json=sans).status_code == 422
    assert compter(en_base, Utilisateur) == 0


@pytest.mark.parametrize(
    ("champs", "message"),
    [
        ({"identifiant": "aya.mensah", "pseudonyme": "Kossi"}, "identifiant"),
        ({"identifiant": "autre", "pseudonyme": "AYA LA CURIEUSE"}, "pseudonyme"),
        ({"identifiant": "autre", "pseudonyme": "Àya-la-curieuse"}, "pseudonyme"),
        ({"identifiant": "autre", "pseudonyme": "Kossi", "email": "aya@exemple.tg"}, "email"),
    ],
)
def test_un_champ_deja_pris_est_nomme(
    client: TestClient, en_base: Callable[..., Any], champs: dict[str, str], message: str
) -> None:
    client.post(INSCRIPTION, json=formulaire(en_base, email="aya@exemple.tg"))
    client.cookies.clear()

    reponse = client.post(INSCRIPTION, json=formulaire(en_base, **champs))

    assert reponse.status_code == 409
    assert message in reponse.json()["detail"]


@pytest.mark.parametrize(
    "champs",
    [
        {"pseudonyme": "aya@mail.tg"},
        {"pseudonyme": "Kofi 90123456"},
        {"pseudonyme": "Admin"},
        {"pseudonyme": "Aya.Mensah"},  # même que l'identifiant
        {"identifiant": "a b"},
        {"mot_de_passe": "court"},
        {"prenom": "   "},
        {"email": "pas-un-email"},
    ],
)
def test_les_champs_invalides_sont_refuses(
    client: TestClient, en_base: Callable[..., Any], champs: dict[str, str]
) -> None:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base, **champs))

    assert reponse.status_code == 422, reponse.text
    assert compter(en_base, Utilisateur) == 0


def test_un_etablissement_inconnu_ou_inactif_est_refuse(client: TestClient, en_base: Callable[..., Any]) -> None:
    inconnu = client.post(INSCRIPTION, json=formulaire(en_base, etablissement_id=str(UUID(int=1))))

    lycee = UUID(etablissement_id(en_base))

    async def desactiver(db: Any) -> None:
        etablissement = await db.get(Etablissement, lycee)
        etablissement.statut = StatutEtablissement.inactif

    en_base(desactiver)
    inactif = client.post(INSCRIPTION, json=formulaire(en_base, etablissement_id=etablissement_id(en_base)))

    assert (inconnu.status_code, inactif.status_code) == (422, 422)
    assert compter(en_base, Utilisateur) == 0


def test_il_faut_un_etablissement_ou_une_proposition_pas_les_deux(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    proposition = {"iesg_id": iesg_id(en_base), "nom": "CEG Nouveau"}
    sans = formulaire(en_base, etablissement_id=None)

    assert client.post(INSCRIPTION, json=sans).status_code == 422
    assert client.post(INSCRIPTION, json=formulaire(en_base, proposition=proposition)).status_code == 422


# Établissement proposé ---------------------------------------------------------------------------------------


def inscrire_avec_proposition(
    client: TestClient, en_base: Callable[..., Any], nom: str, numero: int = 1, iesg: str = "IESG Golfe"
) -> Any:
    client.cookies.clear()
    return client.post(
        INSCRIPTION,
        json=formulaire(
            en_base,
            identifiant=f"eleve{numero}",
            pseudonyme=f"Eleve numero {numero}",
            etablissement_id=None,
            proposition={"iesg_id": iesg_id(en_base, iesg), "nom": nom},
        ),
    )


def test_un_etablissement_propose_est_cree_et_reste_invisible(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = inscrire_avec_proposition(client, en_base, "  CEG   des Étoiles ")

    assert reponse.status_code == 201, reponse.text
    propose = en_base(lambda db: db.scalar(select(Etablissement).where(Etablissement.nom == "CEG des Étoiles")))
    assert propose.statut == StatutEtablissement.propose
    eleve = en_base(lambda db: db.get(Eleve, UUID(reponse.json()["id"])))
    assert eleve.etablissement_id == propose.id
    assert client.get("/api/referentiel/etablissements", params={"recherche": "etoiles"}).json() == []
    assert client.get("/api/referentiel/etablissements", params={"iesg": str(propose.iesg_id)}).status_code == 200
    noms = [
        e["nom"] for e in client.get("/api/referentiel/etablissements", params={"iesg": str(propose.iesg_id)}).json()
    ]
    assert "CEG des Étoiles" not in noms
    (entree,) = en_base(
        lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "inscription_eleve"))
    ).all()
    assert entree.details["etablissement_propose"] is True


def test_une_proposition_deja_faite_est_reutilisee(client: TestClient, en_base: Callable[..., Any]) -> None:
    inscrire_avec_proposition(client, en_base, "CEG des Étoiles", 1)

    reponse = inscrire_avec_proposition(client, en_base, "ceg des etoiles", 2)

    assert reponse.status_code == 201, reponse.text
    nombre = en_base(
        lambda db: db.scalar(
            select(func.count()).select_from(Etablissement).where(Etablissement.statut == StatutEtablissement.propose)
        )
    )
    assert nombre == 1


def test_proposer_un_etablissement_deja_dans_la_liste_est_refuse(
    client: TestClient, en_base: Callable[..., Any]
) -> None:
    reponse = inscrire_avec_proposition(client, en_base, "lycee de tokoin i")

    assert reponse.status_code == 409
    assert "choisis-le" in reponse.json()["detail"]
    assert compter(en_base, Utilisateur) == 0


def test_proposer_dans_une_iesg_inconnue_est_refuse(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = client.post(
        INSCRIPTION,
        json=formulaire(en_base, etablissement_id=None, proposition={"iesg_id": str(UUID(int=1)), "nom": "CEG X"}),
    )

    assert reponse.status_code == 422


# Limites et robustesse ---------------------------------------------------------------------------------------


def test_trop_dinscriptions_depuis_une_adresse(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "inscriptions_max_adresse", 2)
    statuts = []
    for numero in range(3):
        client.cookies.clear()
        statuts.append(
            client.post(
                INSCRIPTION, json=formulaire(en_base, identifiant=f"eleve{numero}", pseudonyme=f"Pseudo {numero}")
            ).status_code
        )

    assert statuts == [201, 201, 429]
    assert compter(en_base, Utilisateur) == 2


def test_les_inscriptions_ne_bloquent_pas_les_connexions(
    client: TestClient, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    for numero in range(3):
        client.cookies.clear()
        client.post(INSCRIPTION, json=formulaire(en_base, identifiant=f"eleve{numero}", pseudonyme=f"Pseudo {numero}"))
    client.cookies.clear()

    reponse = client.post("/api/comptes/connexion", json={"identifiant": "eleve0", "mot_de_passe": "un-mot-de-passe"})

    assert reponse.status_code == 200


def test_un_echec_au_milieu_nécrit_rien(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.eleves import service

    async def echouer(*_: Any, **__: Any) -> None:
        raise RuntimeError("panne")

    monkeypatch.setattr(service.points, "crediter", echouer)

    with pytest.raises(RuntimeError):
        inscrire_avec_proposition(client, en_base, "CEG Fantôme")

    assert compter(en_base, Utilisateur) == 0
    assert compter(en_base, Eleve) == 0
    assert en_base(lambda db: db.scalar(select(Etablissement.id).where(Etablissement.nom == "CEG Fantôme"))) is None


def test_deux_inscriptions_simultanees_avec_le_meme_pseudonyme(en_base: Callable[..., Any]) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.eleves import service
    from app.eleves.schemas import InscriptionEntree
    from tests.conftest import moteur_test

    entrees = {
        numero: InscriptionEntree.model_validate(
            formulaire(en_base, identifiant=f"eleve{numero}", pseudonyme="Même Pseudo")
        )
        for numero in (1, 2)
    }

    async def une(numero: int) -> str:
        entree = entrees[numero]
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            try:
                await service.inscrire(db, entree, f"10.0.0.{numero}")
                await asyncio.sleep(0.2)
                await db.commit()
                return "ok"
            except service.Refus as refus:
                return str(refus)

    async def scenario() -> list[str]:
        return await asyncio.gather(une(1), une(2))

    resultats = asyncio.run(scenario())

    assert sorted(resultats) == ["Ce pseudonyme est déjà pris.", "ok"]
    assert compter(en_base, Eleve) == 1
    assert en_base(lambda db: db.scalar(select(Utilisateur.role))) is Role.eleve


def test_un_refus_pour_trop_dinscriptions_ne_prolonge_pas_le_blocage(
    client: TestClient, en_base: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.comptes.inscription import CLE_LIMITE
    from app.comptes.models import TentativeConnexion

    monkeypatch.setattr(settings, "inscriptions_max_adresse", 1)
    client.post(INSCRIPTION, json=formulaire(en_base))
    for numero in range(3):
        client.cookies.clear()
        corps = formulaire(en_base, identifiant=f"eleve{numero}", pseudonyme=f"Pseudo {numero}")
        assert client.post(INSCRIPTION, json=corps).status_code == 429

    lignes = en_base(
        lambda db: db.scalar(
            select(func.count()).select_from(TentativeConnexion).where(TentativeConnexion.cle_hash == CLE_LIMITE)
        )
    )
    assert lignes == 1


def test_le_pseudonyme_ne_reprend_pas_le_prenom_et_le_nom(client: TestClient, en_base: Callable[..., Any]) -> None:
    reponse = client.post(INSCRIPTION, json=formulaire(en_base, pseudonyme="Mensah Aya"))

    assert reponse.status_code == 422
    assert "prénom" in reponse.json()["detail"]


def test_deux_propositions_simultanees_du_meme_etablissement(en_base: Callable[..., Any]) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.eleves import service
    from app.eleves.schemas import InscriptionEntree
    from tests.conftest import moteur_test

    proposition = {"iesg_id": iesg_id(en_base), "nom": "CEG des Étoiles"}
    entrees = {
        numero: InscriptionEntree.model_validate(
            formulaire(
                en_base,
                identifiant=f"eleve{numero}",
                pseudonyme=f"Pseudo {numero}",
                etablissement_id=None,
                proposition=proposition,
            )
        )
        for numero in (1, 2)
    }

    async def une(numero: int) -> str:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            await service.inscrire(db, entrees[numero], f"10.0.0.{numero}")
            await asyncio.sleep(0.2)
            await db.commit()
            return "ok"

    async def scenario() -> list[str]:
        return await asyncio.gather(une(1), une(2))

    assert asyncio.run(scenario()) == ["ok", "ok"]
    propositions = en_base(
        lambda db: db.scalars(select(Etablissement).where(Etablissement.statut == StatutEtablissement.propose))
    ).all()
    assert len(propositions) == 1
    eleves = en_base(lambda db: db.scalars(select(Eleve.etablissement_id))).all()
    assert eleves == [propositions[0].id, propositions[0].id]
