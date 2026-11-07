"""Décisions de modération (spec 023, ADR-0009) : file, approbation et points, révision d'un contenu publié,
correction, refus, dépublication, concurrence, droits, double authentification et périmètre DRE.

Écrits avant le code : la modération décide de ce qui devient public et crédite des points (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import UUID, uuid7

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces
from app.admin.models import Collaborateur, JournalAudit
from app.articles.schemas import ChampsArticle
from app.comptes.inscription import Refus
from app.comptes.models import StatutCompte, Utilisateur
from app.moderation import decisions
from app.moderation.models import Contenu, EtatContenu, EtatVersion, VersionContenu
from app.notifications.models import Notification
from app.points.models import LigneBareme, MouvementPoints
from tests.conftest import MOT_DE_PASSE, Navigateur, connecter_admin, moteur_test

FILE = "/api/admin/moderation"
ARTICLES = "/api/mes-articles"
MODERATION = {("tableau_de_bord", "consulter"), ("moderation", "consulter"), ("moderation", "approuver"),
              ("moderation", "depublier")}  # fmt: skip
TEXTE = "Parce que **les mains** transportent les microbes."

pytestmark = pytest.mark.usefixtures("annuaire")


def connecter(client: Any, identifiant: str) -> None:
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert reponse.status_code == 200, reponse.text


def champs(**autres: Any) -> dict[str, Any]:
    return {
        "titre": "Le lavage des mains au lycée",
        "chapo": "Notre club a installé trois points d'eau dans la cour.",
        "texte": TEXTE,
        "axe_code": "sante-environnement",
        "afficher_club": True,
    } | autres


@pytest.fixture
def auteur(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Navigateur:
    """Un élève de Grand Lomé, connecté dans son propre navigateur."""
    creer_eleve()
    navigateur = Navigateur(client)
    connecter(navigateur, "eleve1")
    return navigateur


def soumettre(auteur: Any, **autres: Any) -> dict[str, Any]:
    article = auteur.post(ARTICLES, json=champs(**autres)).json()
    reponse = auteur.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"]})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def reviser(auteur: Any, article_id: str, **autres: Any) -> dict[str, Any]:
    actuel = auteur.get(f"{ARTICLES}/{article_id}").json()
    modifie = auteur.request(
        "PATCH", f"{ARTICLES}/{article_id}", json=champs(**autres) | {"version": actuel["version"]}
    ).json()
    reponse = auteur.post(f"{ARTICLES}/{article_id}/soumettre", json={"version": modifie["version"]})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


@pytest.fixture
def moderateur(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)
    connecter_admin(client, "moderateur")
    return client


def version_de(client: Any, contenu_id: str) -> int:
    reponse = client.get(f"{FILE}/{contenu_id}")
    assert reponse.status_code == 200, reponse.text
    return int(reponse.json()["version"])


def decider(client: Any, contenu_id: str, decision: str, motif: str | None = None) -> Any:
    corps: dict[str, Any] = {"version": version_de(client, contenu_id)}
    if motif is not None:
        corps["motif"] = motif
    return client.post(f"{FILE}/{contenu_id}/{decision}", json=corps)


def lignes(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[MouvementPoints]:
    return list(
        en_base(lambda db: db.scalars(select(MouvementPoints).where(MouvementPoints.utilisateur_id == utilisateur_id)))
    )


def contenu(en_base: Callable[..., Any], contenu_id: str) -> Contenu:
    return en_base(lambda db: db.get(Contenu, UUID(contenu_id)))


def notifications(en_base: Callable[..., Any], utilisateur_id: UUID) -> list[Notification]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(Notification).where(Notification.utilisateur_id == utilisateur_id).order_by(Notification.cree_le)
            )
        )
    )


def eleve1(en_base: Callable[..., Any]) -> Utilisateur:
    return en_base(lambda db: db.scalar(select(Utilisateur).where(Utilisateur.identifiant == "eleve1")))


# File ----------------------------------------------------------------------------------------------------------


def test_la_file_montre_les_contenus_en_attente_des_plus_anciens_aux_plus_recents(
    moderateur: TestClient, auteur: Navigateur
) -> None:
    premier = soumettre(auteur, titre="Premier article")
    second = soumettre(auteur, titre="Second article")
    auteur.post(ARTICLES, json=champs(titre="Un brouillon"))

    file = moderateur.get(FILE)

    assert file.status_code == 200, file.text
    contenus = file.json()["contenus"]
    assert [c["id"] for c in contenus] == [premier["id"], second["id"]]
    assert contenus[0]["titre"] == "Premier article"
    # Le modérateur voit qui écrit : nom complet, profil, établissement et DRE.
    assert contenus[0]["auteur"]["nom"] == "Jean Kodjo"
    assert contenus[0]["auteur"]["profil"] == "eleve"
    assert contenus[0]["auteur"]["dre_code"] == "grand-lome"
    assert contenus[0]["nouvelle_version"] is False


def test_la_file_se_filtre_par_axe_et_par_profil(
    moderateur: TestClient, auteur: Navigateur, client: TestClient, creer_encadreur: Callable[..., Any]
) -> None:
    soumettre(auteur, axe_code="genie-imhotep")
    creer_encadreur()
    encadreur = Navigateur(client)
    connecter(encadreur, "encadreur1")
    soumettre(encadreur)

    par_axe = moderateur.get(FILE, params={"axe": "genie-imhotep"}).json()["contenus"]
    par_profil = moderateur.get(FILE, params={"profil": "encadreur"}).json()["contenus"]

    assert [c["auteur"]["profil"] for c in par_axe] == ["eleve"]
    assert [c["auteur"]["profil"] for c in par_profil] == ["encadreur"]


def test_lapercu_montre_le_contenu_soumis(moderateur: TestClient, auteur: Navigateur) -> None:
    article = soumettre(auteur)

    apercu = moderateur.get(f"{FILE}/{article['id']}").json()

    assert apercu["soumise"]["texte"] == TEXTE
    assert apercu["publiee"] is None
    assert apercu["etat"] == "en_attente"


# Approbation ---------------------------------------------------------------------------------------------------


def test_approuver_publie_credite_lauteur_et_le_notifie(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)

    reponse = decider(moderateur, article["id"], "approuver")

    assert reponse.status_code == 200, reponse.text
    publie = contenu(en_base, article["id"])
    assert publie.etat is EtatContenu.publie
    assert publie.version_publiee_id is not None and publie.version_travail_id is None
    assert publie.adresse == "le-lavage-des-mains-au-lycee"
    assert publie.axe_code == "sante-environnement"
    assert publie.publie_le is not None
    eleve = eleve1(en_base)
    (ligne,) = lignes(en_base, eleve.id)
    assert (ligne.action, ligne.montant, ligne.cle) == ("eleve.article", 50, f"article:{article['id']}")
    (avis,) = notifications(en_base, eleve.id)
    assert avis.type == "article_approuve"
    assert avis.lien == f"/mes-articles/{article['id']}"
    entree = en_base(lambda db: db.scalar(select(JournalAudit).where(JournalAudit.action == "article_approuve")))
    assert entree.perimetre == "grand-lome"
    assert entree.auteur_libelle is not None
    # Le journal ne garde jamais le texte d'un article.
    assert TEXTE not in str(entree.details)


def test_approuver_deux_fois_repond_409_et_ne_credite_quune_fois(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")

    assert decider(moderateur, article["id"], "approuver").status_code == 409
    assert len(lignes(en_base, eleve1(en_base).id)) == 1


def test_une_version_perimee_est_refusee(moderateur: TestClient, auteur: Navigateur) -> None:
    article = soumettre(auteur)
    perimee = version_de(moderateur, article["id"])
    auteur.post(f"{ARTICLES}/{article['id']}/retirer", json={"version": article["version"]})
    soumis = auteur.post(f"{ARTICLES}/{article['id']}/soumettre", json={"version": article["version"] + 1})
    assert soumis.status_code == 200, soumis.text

    reponse = moderateur.post(f"{FILE}/{article['id']}/approuver", json={"version": perimee})

    assert reponse.status_code == 409


def test_deux_approbations_simultanees_ne_creditent_quune_fois(
    auteur: Navigateur, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    chef = creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)
    version = contenu(en_base, article["id"]).version

    async def une_decision() -> bool:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
            assert collaborateur is not None
            acces = Acces(
                utilisateur=await db.get(Utilisateur, chef.id),  # type: ignore[arg-type]
                collaborateur=collaborateur,
                droits={("moderation", Action.consulter), ("moderation", Action.approuver)},
                double_auth_active=True,
            )
            try:
                await decisions.approuver(db, acces, UUID(article["id"]), version, "127.0.0.1")
            except Refus as refus:
                assert refus.statut == 409
                return False
            return True

    async def scenario() -> list[bool]:
        return await asyncio.gather(une_decision(), une_decision())

    assert sorted(asyncio.run(scenario())) == [False, True]
    assert len(lignes(en_base, eleve1(en_base).id)) == 1


def test_le_club_de_lauteur_affilie_est_enregistre_comme_beneficiaire(
    moderateur: TestClient,
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    president = creer_eleve("president", "La Présidente")
    club = creer_club(president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    article = soumettre(navigateur)

    decider(moderateur, article["id"], "approuver")

    assert contenu(en_base, article["id"]).club_beneficiaire_id == club.id


def test_un_eleve_sans_club_na_pas_de_club_beneficiaire(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)

    decider(moderateur, article["id"], "approuver")

    assert contenu(en_base, article["id"]).club_beneficiaire_id is None


def test_un_encadreur_recoit_les_points_de_son_profil(
    moderateur: TestClient, client: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    encadreur = creer_encadreur()
    navigateur = Navigateur(client)
    connecter(navigateur, "encadreur1")
    article = soumettre(navigateur)

    decider(moderateur, article["id"], "approuver")

    (ligne,) = lignes(en_base, encadreur.id)
    assert ligne.action == "encadreur.article"


def test_avec_laction_desactivee_lapprobation_reussit_sans_points(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    en_base(lambda db: db.execute(update(LigneBareme).where(LigneBareme.code == "eleve.article").values(actif=False)))

    assert decider(moderateur, article["id"], "approuver").status_code == 200
    assert lignes(en_base, eleve1(en_base).id) == []


def test_deux_titres_identiques_ont_des_adresses_distinctes(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    premier = soumettre(auteur)
    second = soumettre(auteur)

    decider(moderateur, premier["id"], "approuver")
    decider(moderateur, second["id"], "approuver")

    adresses = {contenu(en_base, premier["id"]).adresse, contenu(en_base, second["id"]).adresse}
    assert len(adresses) == 2
    assert "le-lavage-des-mains-au-lycee" in adresses


def test_un_auteur_suspendu_nest_pas_publie(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    eleve = eleve1(en_base)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=StatutCompte.suspendu)
        )
    )

    assert decider(moderateur, article["id"], "approuver").status_code == 409
    assert decider(moderateur, article["id"], "refuser", "Compte suspendu.").status_code == 200


# Révision d'un contenu publié ----------------------------------------------------------------------------------


def test_une_revision_reste_masquee_puis_remplace_la_version_en_ligne_sans_nouveaux_points(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")
    en_ligne = contenu(en_base, article["id"]).version_publiee_id

    reviser(auteur, article["id"], titre="Le lavage des mains, deuxième version", axe_code="genie-imhotep")

    pendant = contenu(en_base, article["id"])
    assert pendant.version_publiee_id == en_ligne
    assert pendant.etat is EtatContenu.en_attente
    # L'axe public ne change pas avant l'approbation.
    assert pendant.axe_code == "sante-environnement"
    apercu = moderateur.get(f"{FILE}/{article['id']}").json()
    assert apercu["publiee"]["titre"] == "Le lavage des mains au lycée"
    assert apercu["soumise"]["titre"] == "Le lavage des mains, deuxième version"
    assert moderateur.get(FILE).json()["contenus"][0]["nouvelle_version"] is True

    decider(moderateur, article["id"], "approuver")

    apres = contenu(en_base, article["id"])
    assert apres.version_publiee_id != en_ligne
    assert (apres.etat, apres.axe_code) == (EtatContenu.publie, "genie-imhotep")
    # L'adresse reste stable même si le titre change.
    assert apres.adresse == "le-lavage-des-mains-au-lycee"
    assert len(lignes(en_base, eleve1(en_base).id)) == 1


def test_refuser_une_revision_garde_la_version_en_ligne(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")
    en_ligne = contenu(en_base, article["id"]).version_publiee_id
    reviser(auteur, article["id"], titre="Une révision refusée")

    assert decider(moderateur, article["id"], "refuser", "Hors sujet.").status_code == 200

    apres = contenu(en_base, article["id"])
    assert (apres.etat, apres.version_publiee_id, apres.version_travail_id) == (EtatContenu.publie, en_ligne, None)
    # L'auteur peut proposer une autre version.
    assert auteur.get(f"{ARTICLES}/{article['id']}").json()["modifiable"] is True


# Correction, refus, dépublication -------------------------------------------------------------------------------


def test_demander_une_correction_rend_larticle_a_lauteur_avec_le_motif(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)

    assert decider(moderateur, article["id"], "corriger", "Ajoute une source.").status_code == 200

    vu = auteur.get(f"{ARTICLES}/{article['id']}").json()
    assert (vu["etat"], vu["modifiable"], vu["soumettable"]) == ("a_corriger", True, False)
    assert vu["derniere_decision"] == {
        "decision": "corriger",
        "motif": "Ajoute une source.",
        "decide_le": vu["derniere_decision"]["decide_le"],
    }
    (avis,) = notifications(en_base, eleve1(en_base).id)
    assert (avis.type, avis.message) == ("article_a_corriger", "Ajoute une source.")

    reviser(auteur, article["id"], texte=TEXTE + "\n\nSource : OMS.")
    assert decider(moderateur, article["id"], "approuver").status_code == 200
    versions = en_base(lambda db: db.scalars(select(VersionContenu).order_by(VersionContenu.numero))).all()
    assert [v.etat for v in versions] == [EtatVersion.a_corriger, EtatVersion.approuvee]


def test_refuser_clot_larticle(moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]) -> None:
    article = soumettre(auteur)

    assert decider(moderateur, article["id"], "refuser", "Contenu inexact.").status_code == 200

    assert contenu(en_base, article["id"]).etat is EtatContenu.refuse
    vu = auteur.get(f"{ARTICLES}/{article['id']}").json()
    assert (vu["modifiable"], vu["soumettable"]) == (False, False)
    assert lignes(en_base, eleve1(en_base).id) == []
    (avis,) = notifications(en_base, eleve1(en_base).id)
    assert (avis.type, avis.message) == ("article_refuse", "Contenu inexact.")


def test_depublier_retire_larticle_du_site_et_garde_les_points(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")

    assert decider(moderateur, article["id"], "depublier", "Photo d'élève sans accord.").status_code == 200

    apres = contenu(en_base, article["id"])
    assert (apres.etat, apres.version_publiee_id) == (EtatContenu.depublie, None)
    assert len(lignes(en_base, eleve1(en_base).id)) == 1
    assert notifications(en_base, eleve1(en_base).id)[-1].type == "article_depublie"

    # Une nouvelle version approuvée le republie, sans nouveaux points.
    reviser(auteur, article["id"], titre="Le lavage des mains, corrigé")
    decider(moderateur, article["id"], "approuver")
    assert contenu(en_base, article["id"]).etat is EtatContenu.publie
    assert len(lignes(en_base, eleve1(en_base).id)) == 1


def test_depublier_pendant_une_revision_refuse_aussi_la_revision(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")
    reviser(auteur, article["id"], titre="Une révision en attente")

    assert decider(moderateur, article["id"], "depublier", "Contenu signalé.").status_code == 200

    apres = contenu(en_base, article["id"])
    assert (apres.etat, apres.version_publiee_id, apres.version_travail_id) == (EtatContenu.depublie, None, None)
    assert moderateur.get(FILE).json()["contenus"] == []


def test_on_ne_depublie_pas_un_article_jamais_publie(moderateur: TestClient, auteur: Navigateur) -> None:
    article = soumettre(auteur)

    assert decider(moderateur, article["id"], "depublier", "Motif.").status_code == 409


@pytest.mark.parametrize("decision", ["corriger", "refuser", "depublier"])
@pytest.mark.parametrize("motif", [None, "   "])
def test_un_motif_est_obligatoire(moderateur: TestClient, auteur: Navigateur, decision: str, motif: str | None) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver") if decision == "depublier" else None

    assert decider(moderateur, article["id"], decision, motif).status_code == 422


def test_une_decision_sur_un_contenu_qui_nest_pas_en_attente_repond_409(
    moderateur: TestClient, auteur: Navigateur
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "refuser", "Hors sujet.")

    assert decider(moderateur, article["id"], "approuver").status_code == 409
    assert decider(moderateur, article["id"], "corriger", "Motif.").status_code == 409


# Droits ---------------------------------------------------------------------------------------------------------


def test_sans_le_droit_la_file_est_refusee(
    client: TestClient, creer_collaborateur: Callable[..., Any], auteur: Navigateur
) -> None:
    article = soumettre(auteur)
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})
    connecter_admin(client, "autre")

    assert client.get(FILE).status_code == 403
    assert client.post(f"{FILE}/{article['id']}/approuver", json={"version": 1}).status_code == 403


def test_consulter_ne_permet_pas_de_decider_et_approuver_ne_permet_pas_de_depublier(
    client: TestClient, creer_collaborateur: Callable[..., Any], auteur: Navigateur
) -> None:
    article = soumettre(auteur)
    creer_collaborateur("lecteur", droits={("moderation", "consulter")}, double_auth=True)
    lecteur = Navigateur(client)
    connecter_admin(lecteur, "lecteur")  # type: ignore[arg-type]
    creer_collaborateur(
        "approbateur", droits={("moderation", "consulter"), ("moderation", "approuver")}, double_auth=True
    )
    approbateur = Navigateur(client)
    connecter_admin(approbateur, "approbateur")  # type: ignore[arg-type]

    assert decider(lecteur, article["id"], "approuver").status_code == 403
    assert decider(approbateur, article["id"], "approuver").status_code == 200
    assert decider(approbateur, article["id"], "depublier", "Motif.").status_code == 403


def test_lire_la_file_exige_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("sans2fa", droits={("moderation", "consulter")})
    connecter_admin(client, "sans2fa")

    reponse = client.get(FILE)

    assert reponse.status_code == 403
    assert "double authentification" in reponse.json()["detail"]


def test_un_collaborateur_de_dre_ne_voit_et_ne_decide_que_sa_dre(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    auteur: Navigateur,
    creer_eleve: Callable[..., Utilisateur],
) -> None:
    lome = soumettre(auteur, titre="Article de Lomé")
    creer_eleve("eleve2", "Kofi de Kara", dre="kara")
    kara_auteur = Navigateur(client)
    connecter(kara_auteur, "eleve2")
    kara = soumettre(kara_auteur, titre="Article de Kara")
    creer_collaborateur("moderateur.kara", droits=MODERATION, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "moderateur.kara")

    assert [c["id"] for c in client.get(FILE).json()["contenus"]] == [kara["id"]]
    assert client.get(f"{FILE}/{lome['id']}").status_code == 404
    assert client.post(f"{FILE}/{lome['id']}/approuver", json={"version": 1}).status_code == 404
    assert decider(client, kara["id"], "approuver").status_code == 200


def test_un_collaborateur_ne_decide_jamais_de_son_propre_contenu(
    moderateur: TestClient, en_base: Callable[..., Any]
) -> None:
    # Un compte admin ne rédige pas par l'API ; le contenu est écrit en base pour éprouver la règle elle-même.
    chef = en_base(lambda db: db.scalar(select(Utilisateur).where(Utilisateur.identifiant == "moderateur")))
    contenu_id = uuid7()

    async def inserer(db: AsyncSession) -> None:
        db.add(Contenu(id=contenu_id, type="article", auteur_id=chef.id, etat=EtatContenu.en_attente, dre_code=None))
        await db.flush()
        version = VersionContenu(
            id=uuid7(), contenu_id=contenu_id, numero=1, donnees=champs(), etat=EtatVersion.soumise
        )
        db.add(version)
        await db.flush()
        await db.execute(update(Contenu).where(Contenu.id == contenu_id).values(version_travail_id=version.id))

    en_base(inserer)

    assert decider(moderateur, str(contenu_id), "approuver").status_code == 403


def test_un_eleve_na_pas_acces_a_la_file(auteur: Navigateur) -> None:
    assert auteur.get(FILE).status_code in {401, 403}


def test_chaque_version_en_base_respecte_le_schema_de_son_type(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "corriger", "Précise.")
    reviser(auteur, article["id"], titre="Version corrigée")
    decider(moderateur, article["id"], "approuver")

    for version in en_base(lambda db: db.scalars(select(VersionContenu))).all():
        ChampsArticle.model_validate(version.donnees)


# Écrans admin existants ------------------------------------------------------------------------------------------


def test_le_tableau_de_bord_et_le_menu_comptent_les_contenus_du_perimetre(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    auteur: Navigateur,
    creer_eleve: Callable[..., Utilisateur],
) -> None:
    soumettre(auteur)
    creer_eleve("eleve2", "Kofi de Kara", dre="kara")
    kara = Navigateur(client)
    connecter(kara, "eleve2")
    soumettre(kara)
    creer_collaborateur("national", droits=MODERATION, double_auth=True)
    creer_collaborateur("kara", droits=MODERATION, perimetre_dre="kara", double_auth=True)
    creer_collaborateur("autre", droits={("tableau_de_bord", "consulter")})

    comptes = {}
    for identifiant in ("national", "kara", "autre"):
        navigateur = Navigateur(client)
        connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
        comptes[identifiant] = (
            navigateur.get("/api/admin/tableau-de-bord").json()["contenus_a_moderer"],
            navigateur.get("/api/admin/moi").json()["contenus_a_moderer"],
        )

    assert comptes == {"national": (2, 2), "kara": (1, 1), "autre": (None, None)}


def test_la_fiche_dun_inscrit_montre_lhistorique_de_ses_articles(
    client: TestClient, creer_collaborateur: Callable[..., Any], auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    creer_collaborateur("gestion", droits=MODERATION | {("inscrits", "consulter")}, double_auth=True)
    connecter_admin(client, "gestion")
    article = soumettre(auteur)
    decider(client, article["id"], "approuver")

    fiche = client.get(f"/api/admin/inscrits/{eleve1(en_base).id}").json()

    actions = [e["action"] for e in fiche["historique"]]
    assert actions[:2] == ["article_approuve", "article_soumis"]


# Constats de la relecture ------------------------------------------------------------------------------------------


def test_une_revision_approuvee_ne_rapporte_rien_meme_si_laction_a_ete_reactivee(
    moderateur: TestClient, auteur: Navigateur, en_base: Callable[..., Any]
) -> None:
    article = soumettre(auteur)
    bareme = update(LigneBareme).where(LigneBareme.code == "eleve.article")
    en_base(lambda db: db.execute(bareme.values(actif=False)))
    decider(moderateur, article["id"], "approuver")
    en_base(lambda db: db.execute(bareme.values(actif=True)))

    reviser(auteur, article["id"], titre="Une révision")
    decider(moderateur, article["id"], "approuver")

    assert lignes(en_base, eleve1(en_base).id) == []


def test_un_article_en_ligne_avec_une_revision_en_brouillon_reste_dans_longlet_publies(
    moderateur: TestClient, auteur: Navigateur
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")
    actuel = auteur.get(f"{ARTICLES}/{article['id']}").json()
    auteur.request(
        "PATCH", f"{ARTICLES}/{article['id']}", json=champs(titre="Brouillon") | {"version": actuel["version"]}
    )

    publies = moderateur.get(FILE, params={"etat": "publie"}).json()["contenus"]

    assert [(c["id"], c["etat"], c["en_ligne"]) for c in publies] == [(article["id"], "brouillon", True)]
    # L'aperçu montre la version en ligne, jamais le brouillon de l'auteur.
    apercu = moderateur.get(f"{FILE}/{article['id']}").json()
    assert apercu["soumise"] is None
    assert apercu["publiee"]["titre"] == "Le lavage des mains au lycée"
    assert decider(moderateur, article["id"], "depublier", "Signalé.").status_code == 200


def test_la_file_ne_montre_jamais_un_brouillon(moderateur: TestClient, auteur: Navigateur) -> None:
    brouillon = auteur.post(ARTICLES, json=champs()).json()

    assert moderateur.get(FILE, params={"etat": "brouillon"}).status_code == 422
    assert moderateur.get(f"{FILE}/{brouillon['id']}").status_code == 404


def test_depublier_pendant_une_revision_garde_la_trace_du_refus_de_la_revision(
    moderateur: TestClient, auteur: Navigateur
) -> None:
    article = soumettre(auteur)
    decider(moderateur, article["id"], "approuver")
    reviser(auteur, article["id"], titre="Une révision en attente")

    decider(moderateur, article["id"], "depublier", "Contenu signalé.")

    decisions_passees = moderateur.get(f"{FILE}/{article['id']}").json()["decisions"]
    assert [(d["decision"], d["motif"]) for d in decisions_passees[:2]] == [
        ("depublier", "Contenu signalé."),
        ("refuser", "Contenu signalé."),
    ] or [(d["decision"], d["motif"]) for d in decisions_passees[:2]] == [
        ("refuser", "Contenu signalé."),
        ("depublier", "Contenu signalé."),
    ]


def test_le_club_beneficiaire_doit_etre_actif(
    moderateur: TestClient,
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    from app.clubs.models import Club, EtatClub

    president = creer_eleve("president", "La Présidente")
    club = creer_club(president)
    navigateur = Navigateur(client)
    connecter(navigateur, "president")
    article = soumettre(navigateur)
    en_base(
        lambda db: db.execute(update(Club).where(Club.id == club.id).values(etat=EtatClub.refuse, motif_refus="Test."))
    )

    decider(moderateur, article["id"], "approuver")

    assert contenu(en_base, article["id"]).club_beneficiaire_id is None


def test_un_encadreur_qui_nest_plus_verifie_nest_pas_publie(
    moderateur: TestClient, client: TestClient, creer_encadreur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.encadreurs.models import Encadreur, EtatVerification

    encadreur = creer_encadreur()
    navigateur = Navigateur(client)
    connecter(navigateur, "encadreur1")
    article = soumettre(navigateur)
    en_base(
        lambda db: db.execute(
            update(Encadreur)
            .where(Encadreur.utilisateur_id == encadreur.id)
            .values(etat=EtatVerification.refuse, motif_refus="Test.")
        )
    )

    assert decider(moderateur, article["id"], "approuver").status_code == 409
    assert lignes(en_base, encadreur.id) == []


def test_deux_approbations_simultanees_de_meme_titre_donnent_deux_adresses(
    auteur: Navigateur,
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_collaborateur: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    premier = soumettre(auteur)
    creer_eleve("eleve2", "Kofi de Lomé")
    autre = Navigateur(client)
    connecter(autre, "eleve2")
    second = soumettre(autre)
    chef = creer_collaborateur("moderateur", droits=MODERATION, double_auth=True)

    async def une_decision(contenu_id: str) -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == chef.id))
            assert collaborateur is not None
            acces = Acces(
                utilisateur=await db.get(Utilisateur, chef.id),  # type: ignore[arg-type]
                collaborateur=collaborateur,
                droits={("moderation", Action.consulter), ("moderation", Action.approuver)},
                double_auth_active=True,
            )
            version = (await db.get(Contenu, UUID(contenu_id))).version  # type: ignore[union-attr]
            await decisions.approuver(db, acces, UUID(contenu_id), version, "127.0.0.1")

    async def scenario() -> None:
        await asyncio.gather(une_decision(premier["id"]), une_decision(second["id"]))

    asyncio.run(scenario())

    adresses = {contenu(en_base, premier["id"]).adresse, contenu(en_base, second["id"]).adresse}
    assert adresses == {"le-lavage-des-mains-au-lycee", "le-lavage-des-mains-au-lycee-2"}
