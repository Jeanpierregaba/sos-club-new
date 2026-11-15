# ruff: noqa: F811
"""Cycle de clôture d'un semestre et palmarès (spec 037, R14) : gel, contrôle, validation, publication, droits et
données publiques. Partie critique, écrite avant le code (docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import JournalAudit
from app.comptes.models import StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.notifications.models import Notification
from app.points import clotures
from app.points.models import CandidatCloture, ClotureSemestre, MouvementPoints, Semestre
from app.points.service import aujourd_hui
from app.referentiel.administration import Refus
from tests.conftest import Navigateur, connecter_admin
from tests.espace_club import connecter
from tests.test_clotures import DEBUT, gain, termine  # noqa: F401

pytestmark = pytest.mark.usefixtures("annuaire")

CLOTURES = "/api/admin/points/clotures"
PALMARES = "/api/palmares"
LECTEUR = {("tableau_de_bord", "consulter"), ("points", "consulter")}
GESTIONNAIRE = LECTEUR | {("points", "modifier")}
MOTIF = "Fraude avérée au quiz du 12 mars."


def admin(client: TestClient, creer_collaborateur: Callable[..., Any], droits: set[Any], **options: Any) -> Navigateur:
    identifiant = options.pop("identifiant", "equipe")
    creer_collaborateur(identifiant, droits=droits, **options)
    navigateur = Navigateur(client)
    connecter_admin(navigateur, identifiant)  # type: ignore[arg-type]
    return navigateur


@pytest.fixture
def equipe(client: TestClient, creer_collaborateur: Callable[..., Any]) -> Navigateur:
    return admin(client, creer_collaborateur, GESTIONNAIRE, double_auth=True)


@pytest.fixture
def podium(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> dict[str, Utilisateur]:
    """Quatre élèves classés : Ama 300 (club Tokoin), Kofi 200, Yao 100, Afi 50."""
    eleves = {
        "ama": creer_eleve("ama", "Ama", dre="grand-lome"),
        "kofi": creer_eleve("kofi", "Kofi", dre="maritime"),
        "yao": creer_eleve("yao", "Yao", dre="kara"),
        "afi": creer_eleve("afi", "Afi", dre="grand-lome"),
    }
    club = creer_club(eleves["ama"], nom="Club Santé Tokoin")
    gain(en_base, eleves["ama"], 300, "ama", termine, club_id=club.id, demi_points=300)
    for nom, montant in (("kofi", 200), ("yao", 100), ("afi", 50)):
        gain(en_base, eleves[nom], montant, nom, termine)
    return eleves


def url(semestre: Semestre, suite: str = "") -> str:
    return f"{CLOTURES}/{semestre.id}{suite}"


def geler(navigateur: Navigateur, semestre: Semestre) -> Any:
    return navigateur.post(url(semestre, "/gel"))


def ecarter(navigateur: Navigateur, semestre: Semestre, eleve: Utilisateur, motif: str = MOTIF) -> Any:
    return navigateur.post(url(semestre, f"/candidats/{eleve.id}/ecart"), json={"motif": motif})


def top3(navigateur: Navigateur, semestre: Semestre) -> list[str]:
    return [laureat["pseudonyme"] for laureat in navigateur.get(url(semestre)).json()["top3"]]


def journal(en_base: Callable[..., Any], action: str) -> list[JournalAudit]:
    return list(en_base(lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == action))).all())


def suspendre(en_base: Callable[..., Any], eleve: Utilisateur) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(statut=StatutCompte.suspendu)
        )
    )


def publier_tout(navigateur: Navigateur, semestre: Semestre) -> None:
    assert geler(navigateur, semestre).status_code == 200
    assert navigateur.post(url(semestre, "/validation")).status_code == 200
    assert navigateur.post(url(semestre, "/publication")).status_code == 200


# Gel -----------------------------------------------------------------------------------------------------------


def test_un_semestre_en_cours_ne_se_gele_pas(equipe: Navigateur, en_base: Callable[..., Any]) -> None:
    async def inserer(db: AsyncSession) -> Semestre:
        element = Semestre(libelle="En cours", debut=aujourd_hui() - timedelta(days=3), fin=aujourd_hui())
        db.add(element)
        return element

    en_cours = en_base(inserer)

    reponse = geler(equipe, en_cours)

    assert reponse.status_code == 409
    assert "fin" in reponse.json()["detail"]


def test_le_gel_photographie_le_classement(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    reponse = geler(equipe, termine)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["etat"] == "gele"
    assert corps["semestre"]["libelle"] == "Semestre 1 2026"
    assert [(c["rang"], c["pseudonyme"], c["club"], c["dre"], c["points"]) for c in corps["candidats"]] == [
        (1, "Ama", "Club Santé Tokoin", "Grand Lomé", 300),
        (2, "Kofi", None, "Maritime", 200),
        (3, "Yao", None, "Kara", 100),
        (4, "Afi", None, "Grand Lomé", 50),
    ]
    assert [l["pseudonyme"] for l in corps["top3"]] == ["Ama", "Kofi", "Yao"]
    assert corps["etapes"]["gele_par"] == "equipe"
    (entree,) = journal(en_base, "semestre_gele")
    assert entree.details["candidats"] == 4


def test_regeler_prend_les_corrections_et_garde_les_ecarts(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    assert ecarter(equipe, termine, podium["kofi"]).status_code == 200
    gain(en_base, podium["afi"], 400, "afi-bonus", termine)

    avant = equipe.get(url(termine)).json()
    assert avant["ecart_actuel"]["top3_different"] is True
    assert {c["pseudonyme"] for c in avant["ecart_actuel"]["changements"]} == {"Afi"}

    reponse = geler(equipe, termine)

    assert reponse.status_code == 200
    corps = reponse.json()
    assert [c["pseudonyme"] for c in corps["candidats"]][:2] == ["Afi", "Ama"]
    kofi = next(c for c in corps["candidats"] if c["pseudonyme"] == "Kofi")
    assert kofi["motif_ecart"] == MOTIF
    assert [l["pseudonyme"] for l in corps["top3"]] == ["Afi", "Ama", "Yao"]
    assert corps["ecart_actuel"]["top3_different"] is False
    assert len(journal(en_base, "semestre_regele")) == 1
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(ClotureSemestre))) == 1


def test_le_photo_garde_le_rang_brut_des_ex_aequo(
    equipe: Navigateur,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    tardif = creer_eleve("eleve-a", "Aaron")
    precoce = creer_eleve("eleve-z", "Zoé")
    gain(en_base, tardif, 50, "aaron", termine, DEBUT + timedelta(days=2))
    gain(en_base, precoce, 50, "zoe", termine, DEBUT)

    candidats = geler(equipe, termine).json()["candidats"]

    assert [(c["rang"], c["rang_brut"], c["pseudonyme"]) for c in candidats] == [(1, 1, "Zoé"), (2, 1, "Aaron")]


# Contrôle ------------------------------------------------------------------------------------------------------


def test_ecarter_fait_monter_le_suivant_et_se_journalise(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)

    reponse = ecarter(equipe, termine, podium["ama"])

    assert reponse.status_code == 200, reponse.text
    assert [l["pseudonyme"] for l in reponse.json()["top3"]] == ["Kofi", "Yao", "Afi"]
    (entree,) = journal(en_base, "candidat_ecarte")
    assert entree.details["motif"] == MOTIF
    assert entree.details["pseudonyme"] == "Ama"


def test_ecarter_exige_un_motif_et_un_candidat_connu(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    termine: Semestre,
    creer_eleve: Callable[..., Utilisateur],
) -> None:
    geler(equipe, termine)
    absent = creer_eleve("absent", "Absent")

    assert ecarter(equipe, termine, podium["ama"], motif="Court").status_code == 422
    assert ecarter(equipe, termine, absent).status_code == 404
    assert ecarter(equipe, termine, podium["ama"]).status_code == 200
    assert ecarter(equipe, termine, podium["ama"]).status_code == 409


def test_reintegrer_rend_sa_place_au_candidat(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    ecarter(equipe, termine, podium["ama"])

    reponse = equipe.post(url(termine, f"/candidats/{podium['ama'].id}/reintegration"))

    assert reponse.status_code == 200
    assert [l["pseudonyme"] for l in reponse.json()["top3"]] == ["Ama", "Kofi", "Yao"]
    assert len(journal(en_base, "candidat_reintegre")) == 1
    assert equipe.post(url(termine, f"/candidats/{podium['kofi'].id}/reintegration")).status_code == 409


def test_le_controle_exige_une_cloture_gelee(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    termine: Semestre,
) -> None:
    assert ecarter(equipe, termine, podium["ama"]).status_code == 404
    geler(equipe, termine)
    equipe.post(url(termine, "/validation"))

    assert ecarter(equipe, termine, podium["ama"]).status_code == 409
    assert geler(equipe, termine).status_code == 409


def test_la_fiche_dun_candidat_montre_ses_corrections_du_semestre(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    gain(
        en_base, podium["kofi"], -20, "kofi-correction", termine, action="admin.correction", motif="Correction de test."
    )

    candidats = geler(equipe, termine).json()["candidats"]

    kofi = next(c for c in candidats if c["pseudonyme"] == "Kofi")
    assert (kofi["identifiant"], kofi["statut"], kofi["corrections"], kofi["points"]) == ("kofi", "actif", 1, 180)


# Validation, annulation et publication -------------------------------------------------------------------------


def test_valider_fige_les_places(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    ecarter(equipe, termine, podium["kofi"])

    reponse = equipe.post(url(termine, "/validation"))

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["etat"] == "valide"
    assert [(l["place"], l["distinction"], l["pseudonyme"]) for l in corps["top3"]] == [
        (1, "Grand Champion", "Ama"),
        (2, "Vice-Champion", "Yao"),
        (3, "Jeune Talent", "Afi"),
    ]
    assert len(journal(en_base, "cloture_validee")) == 1
    assert equipe.post(url(termine, "/validation")).status_code == 409


def test_moins_de_trois_eleves_donnent_un_podium_incomplet(
    equipe: Navigateur,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    seul = creer_eleve("seul", "Seul")
    gain(en_base, seul, 10, "seul", termine)
    geler(equipe, termine)

    reponse = equipe.post(url(termine, "/validation"))

    assert reponse.status_code == 200
    assert [l["pseudonyme"] for l in reponse.json()["top3"]] == ["Seul"]


def test_sans_candidat_la_validation_est_refusee(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    termine: Semestre,
    en_base: Callable[..., Any],
) -> None:
    en_base(lambda db: db.execute(update(MouvementPoints).values(semestre_id=None)))
    assert geler(equipe, termine).json()["candidats"] == []

    assert equipe.post(url(termine, "/validation")).status_code == 422


def test_annuler_la_validation_revient_au_gel(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    equipe.post(url(termine, "/validation"))

    assert equipe.post(url(termine, "/annulation-validation"), json={"motif": "court"}).status_code == 422
    reponse = equipe.post(url(termine, "/annulation-validation"), json={"motif": MOTIF})

    assert reponse.status_code == 200
    assert reponse.json()["etat"] == "gele"
    assert all(l["place"] is None for l in reponse.json()["top3"])
    (entree,) = journal(en_base, "validation_annulee")
    assert entree.details["motif"] == MOTIF
    assert ecarter(equipe, termine, podium["ama"]).status_code == 200


def test_publier_rend_le_palmares_public_et_notifie(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    client: TestClient,
    termine: Semestre,
) -> None:
    lignes_avant = en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints)))

    publier_tout(equipe, termine)

    assert equipe.get(url(termine)).json()["etat"] == "publie"
    palmares = client.get(PALMARES).json()
    (semestre,) = palmares["semestres"]
    assert semestre["libelle"] == "Semestre 1 2026"
    assert [
        (l["place"], l["distinction"], l["pseudonyme"], l["club"], l["dre"], l["points"]) for l in semestre["laureats"]
    ] == [
        (1, "Grand Champion", "Ama", "Club Santé Tokoin", "Grand Lomé", 300),
        (2, "Vice-Champion", "Kofi", None, "Maritime", 200),
        (3, "Jeune Talent", "Yao", None, "Kara", 100),
    ]
    notifications = en_base(
        lambda db: db.scalars(select(Notification).where(Notification.type == "distinction_semestre"))
    ).all()
    assert {n.utilisateur_id for n in notifications} == {podium[n].id for n in ("ama", "kofi", "yao")}
    assert any(n.titre == "Tu es Grand Champion : Semestre 1 2026" for n in notifications)
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(MouvementPoints))) == lignes_avant
    assert len(journal(en_base, "palmares_publie")) == 1


def test_une_cloture_publiee_ne_bouge_plus(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    termine: Semestre,
) -> None:
    publier_tout(equipe, termine)

    assert geler(equipe, termine).status_code == 409
    assert ecarter(equipe, termine, podium["afi"]).status_code == 409
    assert equipe.post(url(termine, "/validation")).status_code == 409
    assert equipe.post(url(termine, "/annulation-validation"), json={"motif": MOTIF}).status_code == 409
    assert equipe.post(url(termine, "/publication")).status_code == 409
    assert equipe.delete(url(termine)).status_code == 405


def test_publier_exige_une_validation_et_des_laureats_actifs(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    assert equipe.post(url(termine, "/publication")).status_code == 409
    equipe.post(url(termine, "/validation"))
    suspendre(en_base, podium["kofi"])

    reponse = equipe.post(url(termine, "/publication"))

    assert reponse.status_code == 422
    assert "Kofi" in reponse.json()["detail"]


# Public et espace ----------------------------------------------------------------------------------------------


def test_le_palmares_public_est_ferme_et_fige(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    client: TestClient,
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    ecarter(equipe, termine, podium["afi"])
    equipe.post(url(termine, "/validation"))
    assert client.get(PALMARES).json()["semestres"] == []

    equipe.post(url(termine, "/publication"))
    en_base(
        lambda db: db.execute(
            update(Eleve).where(Eleve.utilisateur_id == podium["ama"].id).values(pseudonyme="Nouveau")
        )
    )

    corps = client.get(PALMARES).json()
    (semestre,) = corps["semestres"]
    assert set(semestre) == {"libelle", "debut", "fin", "laureats"}
    assert {cle for laureat in semestre["laureats"] for cle in laureat} == {
        "place",
        "distinction",
        "pseudonyme",
        "club",
        "dre",
        "points",
    }
    assert semestre["laureats"][0]["pseudonyme"] == "Ama"
    texte = client.get(PALMARES).text
    assert MOTIF not in texte and "Afi" not in texte and str(podium["ama"].id) not in texte


def test_le_laureat_voit_sa_distinction_dans_son_espace(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    client: TestClient,
    termine: Semestre,
) -> None:
    publier_tout(equipe, termine)

    ama = connecter(client, "ama").get("/api/classements/moi").json()
    afi = connecter(client, "afi").get("/api/classements/moi").json()

    assert ama["distinctions"] == [
        {"semestre": "Semestre 1 2026", "place": 1, "distinction": "Grand Champion", "points": 300}
    ]
    assert afi["distinctions"] == []


def test_la_liste_des_clotures_donne_letat_de_chaque_semestre(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    termine: Semestre,
) -> None:
    avant = equipe.get(CLOTURES).json()
    geler(equipe, termine)
    apres = equipe.get(CLOTURES).json()

    assert [(s["libelle"], s["etat"], s["termine"]) for s in avant] == [("Semestre 1 2026", "ouvert", True)]
    assert apres[0]["etat"] == "gele"


# Droits --------------------------------------------------------------------------------------------------------


def test_les_clotures_exigent_le_droit_la_2fa_et_le_national(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    podium: dict[str, Utilisateur],
    termine: Semestre,
) -> None:
    sans_2fa = admin(client, creer_collaborateur, GESTIONNAIRE, identifiant="sans2fa")
    assert sans_2fa.get(CLOTURES).status_code == 403
    assert geler(sans_2fa, termine).status_code == 403

    lecteur = admin(client, creer_collaborateur, LECTEUR, identifiant="lecteur", double_auth=True)
    assert lecteur.get(CLOTURES).status_code == 200
    assert geler(lecteur, termine).status_code == 403

    dre = admin(
        client, creer_collaborateur, GESTIONNAIRE, identifiant="dre", perimetre_dre="grand-lome", double_auth=True
    )
    assert dre.get(CLOTURES).status_code == 403
    assert geler(dre, termine).status_code == 403


def test_un_eleve_ou_un_anonyme_ne_touche_pas_aux_clotures(
    client: TestClient,
    podium: dict[str, Utilisateur],
    termine: Semestre,
) -> None:
    assert client.get(CLOTURES).status_code == 401
    eleve = connecter(client, "ama")
    assert eleve.get(CLOTURES).status_code in {401, 403}
    assert eleve.post(url(termine, "/gel")).status_code in {401, 403}


ROUTES_ADMIN = [
    ("get", ""),
    ("get", "/{id}"),
    ("post", "/{id}/gel"),
    ("post", "/{id}/candidats/{eleve}/ecart"),
    ("post", "/{id}/candidats/{eleve}/reintegration"),
    ("post", "/{id}/validation"),
    ("post", "/{id}/annulation-validation"),
    ("post", "/{id}/publication"),
]


@pytest.mark.parametrize(("methode", "chemin"), ROUTES_ADMIN)
def test_chaque_route_de_cloture_exige_la_2fa_le_droit_et_le_national(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    podium: dict[str, Utilisateur],
    termine: Semestre,
    methode: str,
    chemin: str,
) -> None:
    adresse = CLOTURES + chemin.format(id=termine.id, eleve=podium["ama"].id)
    corps = {"json": {"motif": MOTIF}} if methode == "post" else {}
    refuses = [
        admin(client, creer_collaborateur, GESTIONNAIRE, identifiant="sans2fa"),
        admin(
            client, creer_collaborateur, GESTIONNAIRE, identifiant="dre", perimetre_dre="grand-lome", double_auth=True
        ),
    ]
    if methode == "post":
        refuses.append(admin(client, creer_collaborateur, LECTEUR, identifiant="lecteur", double_auth=True))

    for navigateur in refuses:
        assert getattr(navigateur, methode)(adresse, **corps).status_code == 403


# Concurrence, comptes disparus et cas secondaires ------------------------------------------------------------------


def acces_de(qui: Utilisateur) -> Callable[[AsyncSession], Any]:
    async def construire(db: AsyncSession) -> Any:
        from app.admin.dependances import Acces
        from app.admin.models import Collaborateur

        collaborateur = await db.scalar(select(Collaborateur).where(Collaborateur.utilisateur_id == qui.id))
        return Acces(utilisateur=await db.get(Utilisateur, qui.id), collaborateur=collaborateur)  # type: ignore[arg-type]

    return construire


def en_parallele(*actions: Callable[[AsyncSession], Any]) -> list[Any]:
    """Lance chaque action dans sa propre session, en même temps ; rend le résultat ou l'exception de chacune."""
    from tests.conftest import moteur_test

    async def une(action: Callable[[AsyncSession], Any]) -> Any:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            return await action(db)

    async def scenario() -> list[Any]:
        return await asyncio.gather(*(une(a) for a in actions), return_exceptions=True)

    return asyncio.run(scenario())


def test_deux_gels_simultanes_ne_creent_quune_cloture(
    creer_collaborateur: Callable[..., Any],
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    premier = creer_collaborateur("premier", droits=GESTIONNAIRE, double_auth=True)
    second = creer_collaborateur("second", droits=GESTIONNAIRE, double_auth=True)

    def gel(qui: Utilisateur) -> Callable[[AsyncSession], Any]:
        async def action(db: AsyncSession) -> Any:
            return await clotures.geler(db, await acces_de(qui)(db), termine.id, "127.0.0.1")

        return action

    resultats = en_parallele(gel(premier), gel(second))

    assert [type(r).__name__ for r in resultats] == ["ClotureDetail", "ClotureDetail"]
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(ClotureSemestre))) == 1
    assert sorted(e.action for e in journal(en_base, "semestre_gele") + journal(en_base, "semestre_regele")) == [
        "semestre_gele",
        "semestre_regele",
    ]
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(CandidatCloture))) == 4


def test_deux_publications_simultanees_nen_font_quune(
    creer_collaborateur: Callable[..., Any],
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    equipe.post(url(termine, "/validation"))
    premier = creer_collaborateur("premier", droits=GESTIONNAIRE, double_auth=True)
    second = creer_collaborateur("second", droits=GESTIONNAIRE, double_auth=True)

    def publication(qui: Utilisateur) -> Callable[[AsyncSession], Any]:
        async def action(db: AsyncSession) -> Any:
            return await clotures.publier(db, await acces_de(qui)(db), termine.id, "127.0.0.1")

        return action

    resultats = en_parallele(publication(premier), publication(second))

    refus = [r for r in resultats if isinstance(r, Refus)]
    assert len(refus) == 1 and refus[0].statut == 409
    assert len(journal(en_base, "palmares_publie")) == 1
    assert (
        en_base(
            lambda db: db.scalar(
                select(func.count()).select_from(Notification).where(Notification.type == "distinction_semestre")
            )
        )
        == 3
    )


def test_un_laureat_disparu_bloque_la_publication(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    equipe.post(url(termine, "/validation"))
    # Un élève qui a des points ne se supprime pas (FK RESTRICT du registre) : on simule la ligne disparue.
    en_base(lambda db: db.execute(delete(CandidatCloture).where(CandidatCloture.utilisateur_id == podium["kofi"].id)))

    reponse = equipe.post(url(termine, "/publication"))

    assert reponse.status_code == 422
    assert "annule la validation" in reponse.json()["detail"]
    assert equipe.get(PALMARES).json() == {"semestres": []}


def test_le_palmares_garde_le_club_du_gel(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    publier_tout(equipe, termine)
    from app.clubs.models import Club

    en_base(lambda db: db.execute(update(Club).values(nom="Club renommé")))

    (semestre,) = equipe.get(PALMARES).json()["semestres"]
    assert semestre["laureats"][0]["club"] == "Club Santé Tokoin"


def test_on_ne_reintegre_pas_sur_une_cloture_validee(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    ecarter(equipe, termine, podium["ama"])
    equipe.post(url(termine, "/validation"))

    reponse = equipe.post(url(termine, f"/candidats/{podium['ama'].id}/reintegration"))

    assert reponse.status_code == 409


def test_le_journal_nomme_lauteur_et_le_semestre(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    ecarter(equipe, termine, podium["kofi"])
    auteur = en_base(lambda db: db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == "equipe")))

    for action in ("semestre_gele", "candidat_ecarte"):
        (entree,) = journal(en_base, action)
        assert (entree.auteur_id, entree.cible_id) == (auteur, str(termine.id))

    (candidat,) = [c for c in equipe.get(url(termine)).json()["candidats"] if c["pseudonyme"] == "Kofi"]
    assert candidat["ecarte_par"] == "equipe"


def test_le_regel_ne_compte_que_les_ecarts_reportes(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    ecarter(equipe, termine, podium["kofi"])
    ecarter(equipe, termine, podium["yao"])
    suspendre(en_base, podium["yao"])

    geler(equipe, termine)

    (entree,) = journal(en_base, "semestre_regele")
    assert (entree.details["ecartes_reportes"], entree.details["ecarts_perdus"]) == (1, 1)


def test_un_eleve_sorti_des_cinquante_reste_distinct_dun_exclu(
    equipe: Navigateur,
    podium: dict[str, Utilisateur],
    en_base: Callable[..., Any],
    termine: Semestre,
) -> None:
    geler(equipe, termine)
    suspendre(en_base, podium["afi"])
    with patch.object(clotures, "TAILLE_PHOTO", 2):
        changements = equipe.get(url(termine)).json()["ecart_actuel"]["changements"]

    par_nom = {c["pseudonyme"]: c for c in changements}
    assert par_nom["Yao"] == {"pseudonyme": "Yao", "points_gel": 100, "points_actuels": 100, "hors_photo": True}
    assert par_nom["Afi"]["points_actuels"] is None
    assert "Ama" not in par_nom
