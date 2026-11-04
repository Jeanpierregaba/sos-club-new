"""Vérification des encadreurs par l'espace admin (spec 018) : file, activation avec la bienvenue, refus, périmètre
DRE, droits. Écrits avant le code : l'activation crédite des points (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import courriel
from app.admin.catalogue import Action
from app.admin.dependances import Acces
from app.admin.models import Collaborateur, JournalAudit
from app.comptes.inscription import Refus
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.encadreurs import verification
from app.encadreurs.models import Encadreur, EtatVerification, Fonction
from app.points.models import LigneBareme, MouvementPoints, Semestre
from app.points.service import aujourd_hui
from app.referentiel.models import Dre, Etablissement, Iesg
from tests.conftest import MOT_DE_PASSE, connecter_admin, moteur_test

FILE = "/api/admin/encadreurs"
VERIFICATION = {("tableau_de_bord", "consulter"), ("encadreurs", "consulter"), ("encadreurs", "approuver")}

pytestmark = pytest.mark.usefixtures("annuaire")


def etablissement_de(en_base: Callable[..., Any], dre: str) -> UUID:
    return en_base(
        lambda db: db.scalar(
            select(Etablissement.id)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Dre.code == dre)
            .order_by(Etablissement.nom)
            .limit(1)
        )
    )


@pytest.fixture
def demande(creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]) -> Callable[..., Utilisateur]:
    """Un encadreur inscrit, en attente de vérification, dans un établissement de la DRE donnée."""

    def creer(identifiant: str = "prof.kodjo", dre: str = "grand-lome", *, il_y_a: int = 0) -> Utilisateur:
        utilisateur = creer_utilisateur(identifiant, Role.encadreur, email=f"{identifiant}@ecole.tg")
        etablissement_id = etablissement_de(en_base, dre)

        async def inserer(db: AsyncSession) -> None:
            db.add(
                Encadreur(
                    utilisateur_id=utilisateur.id,
                    etablissement_id=etablissement_id,
                    fonction=Fonction.enseignant,
                    etat=EtatVerification.en_attente,
                    demande_le=datetime.now(UTC) - timedelta(days=il_y_a),
                    charte_version="test",
                )
            )

        en_base(inserer)
        return utilisateur

    return creer


@pytest.fixture
def semestre(en_base: Callable[..., Any]) -> Semestre:
    async def inserer(db: AsyncSession) -> Semestre:
        element = Semestre(libelle="S1", debut=aujourd_hui() - timedelta(days=1), fin=aujourd_hui() + timedelta(days=9))
        db.add(element)
        return element

    return en_base(inserer)


@pytest.fixture
def verificateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("verif", droits=VERIFICATION, double_auth=True)
    connecter_admin(client, "verif")
    return client


def lignes(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[MouvementPoints]:
    return en_base(
        lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == utilisateur_id))
    ).all()


def profil(en_base: Callable[..., Any], utilisateur_id: UUID) -> Encadreur:
    return en_base(lambda db: db.get(Encadreur, utilisateur_id))


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all()


# File ----------------------------------------------------------------------------------------------------------


def test_la_file_montre_les_demandes_en_attente_des_plus_anciennes_aux_plus_recentes(
    verificateur: TestClient, demande: Callable[..., Utilisateur]
) -> None:
    demande("prof.recent", il_y_a=1)
    demande("prof.ancien", il_y_a=5)

    file = verificateur.get(FILE).json()

    assert file["total"] == 2
    assert [d["identifiant"] for d in file["demandes"]] == ["prof.ancien", "prof.recent"]
    premiere = file["demandes"][0]
    assert premiere["email"] == "prof.ancien@ecole.tg"
    assert premiere["fonction"] == "enseignant"
    assert premiere["etablissement"]["dre_code"] == "grand-lome"


def test_la_file_des_refuses_est_a_part(verificateur: TestClient, demande: Callable[..., Utilisateur]) -> None:
    refuse = demande("prof.refuse")
    demande("prof.attente")
    verificateur.post(f"{FILE}/{refuse.id}/refuser", json={"motif": "Inconnu de l'établissement"})

    assert [d["identifiant"] for d in verificateur.get(FILE).json()["demandes"]] == ["prof.attente"]
    refuses = verificateur.get(FILE, params={"etat": "refuse"}).json()["demandes"]
    assert [(d["identifiant"], d["motif_refus"]) for d in refuses] == [("prof.refuse", "Inconnu de l'établissement")]


# Activation ----------------------------------------------------------------------------------------------------


def test_activer_rend_le_compte_actif_et_credite_la_bienvenue(
    verificateur: TestClient, demande: Callable[..., Utilisateur], semestre: Semestre, en_base: Callable[..., Any]
) -> None:
    encadreur = demande()

    reponse = verificateur.post(f"{FILE}/{encadreur.id}/activer")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["etat"] == "actif"
    apres = profil(en_base, encadreur.id)
    assert apres.etat is EtatVerification.actif
    assert apres.decide_le is not None and apres.decide_par is not None
    (ligne,) = lignes(en_base, encadreur.id)
    assert (ligne.action, ligne.montant, ligne.semestre_id) == ("encadreur.bienvenue", 100, semestre.id)
    assert ligne.valide_par == apres.decide_par
    (entree,) = journal(en_base, "encadreur_active")
    assert entree.cible_id == str(encadreur.id)
    assert entree.perimetre == "grand-lome"


def test_activer_deux_fois_repond_409_et_ne_credite_quune_fois(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    verificateur.post(f"{FILE}/{encadreur.id}/activer")

    reponse = verificateur.post(f"{FILE}/{encadreur.id}/activer")

    assert reponse.status_code == 409
    assert len(lignes(en_base, encadreur.id)) == 1


def test_deux_activations_simultanees_ne_creditent_quune_fois(
    demande: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    chef = creer_collaborateur("verif", droits=VERIFICATION, double_auth=True)

    async def une_decision() -> bool:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
            assert collaborateur is not None
            acces = Acces(
                utilisateur=await db.get(Utilisateur, chef.id),  # type: ignore[arg-type]
                collaborateur=collaborateur,
                droits={("encadreurs", Action.consulter), ("encadreurs", Action.approuver)},
                double_auth_active=True,
            )
            try:
                await verification.activer(db, acces, encadreur.id, "127.0.0.1")
            except Refus as refus:
                assert refus.statut == 409
                return False
            return True

    async def scenario() -> list[bool]:
        return await asyncio.gather(une_decision(), une_decision())

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert len(lignes(en_base, encadreur.id)) == 1


def acces_de(db: AsyncSession, collaborateur: Collaborateur, utilisateur: Utilisateur) -> Acces:
    return Acces(
        utilisateur=utilisateur,
        collaborateur=collaborateur,
        droits={("encadreurs", Action.consulter), ("encadreurs", Action.approuver)},
        double_auth_active=True,
    )


def test_un_changement_detablissement_pendant_la_decision_sort_du_perimetre(
    demande: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    """Le profil passe dans une autre DRE pendant qu'un collaborateur de la DRE d'origine l'active : la décision
    ne trouve plus la demande, et rien n'est crédité."""
    encadreur = demande(dre="grand-lome")
    chef = creer_collaborateur("verif.lome", droits=VERIFICATION, perimetre_dre="grand-lome", double_auth=True)
    ailleurs = etablissement_de(en_base, "kara")

    async def scenario() -> str:
        async with AsyncSession(moteur_test) as modification, AsyncSession(moteur_test) as decision:
            profil = await modification.get(Encadreur, encadreur.id, with_for_update=True)
            assert profil is not None
            profil.etablissement_id = ailleurs
            await modification.flush()
            collaborateur = await decision.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
            auteur = await decision.get(Utilisateur, chef.id)
            assert collaborateur is not None and auteur is not None
            # La décision attend le verrou du profil, puis relit la ligne modifiée.
            tache = asyncio.create_task(
                verification.activer(decision, acces_de(decision, collaborateur, auteur), encadreur.id, "127.0.0.1")
            )
            await asyncio.sleep(0.3)
            await modification.commit()
            try:
                await tache
            except verification.Introuvable:
                return "introuvable"
            return "activee"

    assert asyncio.run(scenario()) == "introuvable"
    assert lignes(en_base, encadreur.id) == []
    assert profil(en_base, encadreur.id).etat is EtatVerification.en_attente


def test_activer_un_profil_modifie_depuis_son_ouverture_repond_409(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    version = verificateur.get(FILE).json()["demandes"][0]["version"]
    en_base(
        lambda db: db.execute(
            update(Encadreur).where(Encadreur.utilisateur_id == encadreur.id).values(version=Encadreur.version + 1)
        )
    )

    reponse = verificateur.post(f"{FILE}/{encadreur.id}/activer", json={"version": version})

    assert reponse.status_code == 409
    assert verificateur.post(f"{FILE}/{encadreur.id}/activer", json={"version": version + 1}).status_code == 200


def test_refuser_un_profil_modifie_depuis_son_ouverture_repond_409(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    version = verificateur.get(FILE).json()["demandes"][0]["version"]
    en_base(
        lambda db: db.execute(
            update(Encadreur).where(Encadreur.utilisateur_id == encadreur.id).values(version=Encadreur.version + 1)
        )
    )

    reponse = verificateur.post(
        f"{FILE}/{encadreur.id}/refuser", json={"version": version, "motif": "Test du garde-fou"}
    )

    assert reponse.status_code == 409
    assert verificateur.get(FILE).json()["demandes"][0]["etat"] == "en_attente"
    assert (
        verificateur.post(
            f"{FILE}/{encadreur.id}/refuser", json={"version": version + 1, "motif": "Test du garde-fou"}
        ).status_code
        == 200
    )


def test_un_refus_puis_une_activation_ne_donnent_quune_bienvenue(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    verificateur.post(f"{FILE}/{encadreur.id}/activer")
    # Cas extrême : un compte déjà crédité qui repasserait en attente ne doit pas être crédité deux fois.
    en_base(
        lambda db: db.execute(
            update(Encadreur)
            .where(Encadreur.utilisateur_id == encadreur.id)
            .values(etat=EtatVerification.en_attente, decide_le=None, decide_par=None)
        )
    )

    assert verificateur.post(f"{FILE}/{encadreur.id}/activer").status_code == 200
    assert len(lignes(en_base, encadreur.id)) == 1


def test_avec_la_bienvenue_desactivee_lactivation_reussit_sans_points(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    en_base(
        lambda db: db.execute(update(LigneBareme).where(LigneBareme.code == "encadreur.bienvenue").values(actif=False))
    )

    assert verificateur.post(f"{FILE}/{encadreur.id}/activer").status_code == 200
    assert lignes(en_base, encadreur.id) == []


def test_hors_semestre_la_bienvenue_na_pas_de_semestre(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()

    verificateur.post(f"{FILE}/{encadreur.id}/activer")

    (ligne,) = lignes(en_base, encadreur.id)
    assert ligne.semestre_id is None


def test_un_compte_suspendu_ne_sactive_pas(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == encadreur.id).values(statut=StatutCompte.suspendu)
        )
    )

    reponse = verificateur.post(f"{FILE}/{encadreur.id}/activer")

    assert reponse.status_code == 409
    assert profil(en_base, encadreur.id).etat is EtatVerification.en_attente
    assert lignes(en_base, encadreur.id) == []


def test_un_compte_qui_nest_pas_une_demande_dencadreur_est_introuvable(
    verificateur: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    eleve = creer_utilisateur("eleve1")

    assert verificateur.post(f"{FILE}/{eleve.id}/activer").status_code == 404
    assert verificateur.post(f"{FILE}/00000000-0000-7000-8000-000000000000/activer").status_code == 404


def test_lactivation_envoie_un_email_sans_dependre_de_son_envoi(
    verificateur: TestClient,
    demande: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envoyes: list[str] = []

    async def envoyer(destinataire: str, sujet: str, texte: str) -> None:
        envoyes.append(destinataire)
        raise courriel.EnvoiImpossible

    monkeypatch.setattr(courriel, "envoyer", envoyer)
    encadreur = demande()

    reponse = verificateur.post(f"{FILE}/{encadreur.id}/activer")

    assert reponse.status_code == 200
    assert envoyes == ["prof.kodjo@ecole.tg"]
    assert profil(en_base, encadreur.id).etat is EtatVerification.actif


# Refus ---------------------------------------------------------------------------------------------------------


def test_refuser_garde_le_motif_et_ne_credite_rien(
    verificateur: TestClient, demande: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    encadreur = demande()

    reponse = verificateur.post(f"{FILE}/{encadreur.id}/refuser", json={"motif": "  Fonction non confirmée  "})

    assert reponse.status_code == 200, reponse.text
    apres = profil(en_base, encadreur.id)
    assert (apres.etat, apres.motif_refus) == (EtatVerification.refuse, "Fonction non confirmée")
    assert lignes(en_base, encadreur.id) == []
    (entree,) = journal(en_base, "encadreur_refuse")
    assert entree.details == {"motif": "Fonction non confirmée"}


@pytest.mark.parametrize("corps", [{}, {"motif": ""}, {"motif": "  "}, {"motif": "x" * 501}])
def test_un_refus_exige_un_motif(
    verificateur: TestClient, demande: Callable[..., Utilisateur], corps: dict[str, str]
) -> None:
    encadreur = demande()

    assert verificateur.post(f"{FILE}/{encadreur.id}/refuser", json=corps).status_code == 422


def test_une_demande_deja_traitee_ne_se_decide_plus(
    verificateur: TestClient, demande: Callable[..., Utilisateur]
) -> None:
    encadreur = demande()
    verificateur.post(f"{FILE}/{encadreur.id}/refuser", json={"motif": "Doublon"})

    assert verificateur.post(f"{FILE}/{encadreur.id}/refuser", json={"motif": "Doublon"}).status_code == 409
    assert verificateur.post(f"{FILE}/{encadreur.id}/activer").status_code == 409


# Périmètre et droits --------------------------------------------------------------------------------------------


def test_un_collaborateur_de_dre_ne_voit_et_ne_decide_que_sa_dre(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    demande: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    demande("prof.kara", dre="kara")
    lome = demande("prof.lome", dre="grand-lome")
    creer_collaborateur("verif.kara", droits=VERIFICATION, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "verif.kara")

    file = client.get(FILE).json()

    assert (file["total"], [d["identifiant"] for d in file["demandes"]]) == (1, ["prof.kara"])
    assert client.post(f"{FILE}/{lome.id}/activer").status_code == 404
    assert client.post(f"{FILE}/{lome.id}/refuser", json={"motif": "Hors DRE"}).status_code == 404
    assert profil(en_base, lome.id).etat is EtatVerification.en_attente


def test_un_collaborateur_national_voit_toutes_les_dre(
    verificateur: TestClient, demande: Callable[..., Utilisateur]
) -> None:
    demande("prof.kara", dre="kara")
    demande("prof.lome", dre="grand-lome")

    assert verificateur.get(FILE).json()["total"] == 2


def test_sans_le_droit_la_file_est_refusee(
    client: TestClient, creer_collaborateur: Callable[..., Any], demande: Callable[..., Utilisateur]
) -> None:
    encadreur = demande()
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})
    connecter_admin(client, "autre")

    assert client.get(FILE).status_code == 403
    assert client.post(f"{FILE}/{encadreur.id}/activer").status_code == 403


def test_consulter_ne_permet_pas_de_decider(
    client: TestClient, creer_collaborateur: Callable[..., Any], demande: Callable[..., Utilisateur]
) -> None:
    encadreur = demande()
    creer_collaborateur("lecteur", droits={("encadreurs", "consulter")}, double_auth=True)
    connecter_admin(client, "lecteur")

    assert client.get(FILE).status_code == 200
    assert client.post(f"{FILE}/{encadreur.id}/activer").status_code == 403


def test_lire_la_file_exige_aussi_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any], demande: Callable[..., Utilisateur]
) -> None:
    demande()
    creer_collaborateur("lecteur", droits={("encadreurs", "consulter")})
    connecter_admin(client, "lecteur")

    assert client.get(FILE).status_code == 403
    assert client.get("/api/admin/moi").json()["encadreurs_a_verifier"] is None


def test_la_file_ne_liste_pas_les_encadreurs_actifs(
    verificateur: TestClient, demande: Callable[..., Utilisateur]
) -> None:
    encadreur = demande()
    verificateur.post(f"{FILE}/{encadreur.id}/activer")

    assert verificateur.get(FILE, params={"etat": "actif"}).status_code == 422


def test_decider_exige_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any], demande: Callable[..., Utilisateur]
) -> None:
    encadreur = demande()
    creer_collaborateur("sans2fa", droits=VERIFICATION)
    connecter_admin(client, "sans2fa")

    reponse = client.post(f"{FILE}/{encadreur.id}/activer")

    assert reponse.status_code == 403
    assert "double authentification" in reponse.json()["detail"]


def test_un_encadreur_ou_un_eleve_na_pas_acces_a_la_file(
    client: TestClient, creer_utilisateur: Callable[..., Utilisateur]
) -> None:
    creer_utilisateur("eleve1")
    client.post("/api/comptes/connexion", json={"identifiant": "eleve1", "mot_de_passe": MOT_DE_PASSE})

    assert client.get(FILE).status_code == 403
