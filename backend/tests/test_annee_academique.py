"""Année académique, tableau de bord de l'élève et archives (spec 034, lot 4) : partie critique, écrite avant le code
(docs/TESTING.md)."""

import asyncio
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.points import service
from app.points.bareme import BIENVENUE_ELEVE, COMMENTAIRE_ELEVE, ETOILE_NIVEAU, QUIZ_CERTIFICATION_ELEVE
from app.points.models import AnneeAcademique, ClassementAnnuel, MouvementPoints
from tests.conftest import connecter_admin
from tests.quiz import connecter

pytestmark = pytest.mark.usefixtures("annuaire")
TABLEAU = "/api/eleves/moi/gamification"
ANNEES = "/api/admin/points/annees"
AUJOURD_HUI = service.aujourd_hui()
GESTION = {("tableau_de_bord", "consulter"), ("points", "consulter"), ("points", "modifier")}


def annee(en_base: Callable[..., Any], libelle: str, debut: date, fin: date) -> AnneeAcademique:
    async def inserer(db: AsyncSession) -> AnneeAcademique:
        element = AnneeAcademique(libelle=libelle, debut=debut, fin=fin)
        db.add(element)
        return element

    return en_base(inserer)


@pytest.fixture
def en_cours(en_base: Callable[..., Any]) -> AnneeAcademique:
    return annee(en_base, "2026-2027", AUJOURD_HUI - timedelta(days=60), AUJOURD_HUI + timedelta(days=200))


@pytest.fixture
def passee(en_base: Callable[..., Any]) -> AnneeAcademique:
    return annee(en_base, "2025-2026", AUJOURD_HUI - timedelta(days=430), AUJOURD_HUI - timedelta(days=100))


def affilier(en_base: Callable[..., Any], eleve: Utilisateur) -> UUID:
    async def faire(db: AsyncSession) -> UUID:
        profil = await db.get(Eleve, eleve.id)
        assert profil is not None
        club = await activation.club_de(db, profil.etablissement_id)
        await db.execute(update(Club).where(Club.id == club.id).values(etat=EtatClub.actif))
        db.add(Adhesion(eleve_id=eleve.id, club_id=club.id, etat=EtatAdhesion.active))
        return club.id

    return en_base(faire)


def crediter(en_base: Callable[..., Any], action: str, utilisateur_id: UUID, cle: str) -> MouvementPoints | None:
    return en_base(lambda db: service.crediter(db, action, utilisateur_id, cle))


def ancien_gain(en_base: Callable[..., Any], utilisateur_id: UUID, annee_id: UUID, montant: int, cle: str) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(
            MouvementPoints(
                utilisateur_id=utilisateur_id, action=BIENVENUE_ELEVE, montant=montant, annee_id=annee_id, cle=cle
            )
        )

    en_base(inserer)


@pytest.fixture
def eleve(client: TestClient, creer_eleve: Callable[..., Utilisateur]) -> Utilisateur:
    utilisateur = creer_eleve("ama", affiche="Ama du Golfe")
    connecter(client, "ama")
    return utilisateur


# Chaque gain a son année -----------------------------------------------------------------------------------------


def test_un_gain_est_rattache_a_l_annee_en_cours(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur], en_cours: AnneeAcademique
) -> None:
    eleve = creer_eleve("kofi")

    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")

    assert gain is not None and gain.annee_id == en_cours.id


def test_hors_annee_un_gain_compte_seulement_dans_le_total_historique(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    eleve = creer_eleve("kofi")

    gain = crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")

    assert gain is not None and gain.annee_id is None


def test_un_ancien_eleve_ne_gagne_plus_de_points(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur], en_cours: AnneeAcademique
) -> None:
    eleve = creer_eleve("kofi")
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(ancien_eleve_le=service.maintenant())
        )
    )

    assert crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1") is None


# Le tableau de bord ----------------------------------------------------------------------------------------------


def test_le_tableau_de_bord_ne_compte_que_l_annee_en_cours(
    client: TestClient,
    en_base: Callable[..., Any],
    eleve: Utilisateur,
    en_cours: AnneeAcademique,
    passee: AnneeAcademique,
) -> None:
    ancien_gain(en_base, eleve.id, passee.id, 700, "ancien:1")
    crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")

    corps = client.get(TABLEAU).json()

    assert corps["annee"]["libelle"] == "2026-2027"
    assert corps["total_annuel"] == 5
    assert corps["total_historique"] == 705
    assert [(a["libelle"], a["points"]) for a in corps["archives"]] == [("2025-2026", 700)]


def test_le_tableau_de_bord_decompte_les_trois_parcours_et_la_part_du_club(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, en_cours: AnneeAcademique
) -> None:
    affilier(en_base, eleve)
    crediter(en_base, QUIZ_CERTIFICATION_ELEVE, eleve.id, "certification:place:1")
    crediter(en_base, ETOILE_NIVEAU["debutant"], eleve.id, "etoile:debutant")
    crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")

    corps = client.get(TABLEAU).json()

    assert corps["parcours"] == {"certification": 50, "jeux": 500, "vie": 5}
    assert corps["total_annuel"] == 555
    assert corps["apport_club"] == 277.5
    assert corps["jeux"]["points_etoiles"] == 500
    assert corps["certification"]["quiz_valides"] == 0
    assert corps["vie"]["en_attente"] == 0


def test_le_rang_regional_et_la_place_dans_le_club(
    client: TestClient,
    en_base: Callable[..., Any],
    eleve: Utilisateur,
    creer_eleve: Callable[..., Utilisateur],
    en_cours: AnneeAcademique,
) -> None:
    affilier(en_base, eleve)
    voisin = creer_eleve("kossi", affiche="Kossi")
    affilier(en_base, voisin)
    crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")
    crediter(en_base, BIENVENUE_ELEVE, voisin.id, "bienvenue:voisin")

    corps = client.get(TABLEAU).json()

    assert (corps["rang_regional"], corps["place_club"]) == (2, 2)


def test_le_tableau_de_bord_est_reserve_aux_eleves(client: TestClient) -> None:
    assert client.get(TABLEAU).status_code == 401


def test_le_tableau_de_bord_est_refuse_a_un_encadreur(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    encadreur = creer_encadreur()
    connecter(client, encadreur.identifiant)

    assert client.get(TABLEAU).status_code == 403


def test_un_eleve_sans_points_n_est_pas_classe(
    client: TestClient, eleve: Utilisateur, en_cours: AnneeAcademique
) -> None:
    corps = client.get(TABLEAU).json()

    assert (corps["total_annuel"], corps["rang_regional"], corps["place_club"]) == (0, None, None)


def test_le_rang_regional_partage_les_ex_aequo_et_ignore_les_autres_regions(
    client: TestClient,
    en_base: Callable[..., Any],
    eleve: Utilisateur,
    creer_eleve: Callable[..., Utilisateur],
    en_cours: AnneeAcademique,
) -> None:
    egal = creer_eleve("egal", affiche="Egal")
    devant = creer_eleve("devant", affiche="Devant")
    loin = creer_eleve("loin", affiche="Loin", dre="kara")
    for compte, montant in ((eleve, 50), (egal, 50), (devant, 80), (loin, 900)):
        ancien_gain(en_base, compte.id, en_cours.id, montant, f"gain:{compte.identifiant}")

    corps = client.get(TABLEAU).json()

    assert (corps["rang_regional"], corps["region"]) == (2, "maritime")


def test_les_points_jeux_du_tableau_sont_ceux_de_l_annee(
    client: TestClient,
    en_base: Callable[..., Any],
    eleve: Utilisateur,
    en_cours: AnneeAcademique,
    passee: AnneeAcademique,
) -> None:
    async def gain_passe(db: AsyncSession) -> None:
        db.add(
            MouvementPoints(
                utilisateur_id=eleve.id, action=ETOILE_NIVEAU["expert"], montant=2000, annee_id=passee.id,
                cle="etoile:passee",
            )
        )  # fmt: skip

    en_base(gain_passe)
    crediter(en_base, ETOILE_NIVEAU["debutant"], eleve.id, "etoile:debutant")

    jeux = client.get(TABLEAU).json()["jeux"]

    assert (jeux["points_etoiles"], jeux["points_quiz"], jeux["total"]) == (500, 0, 500)


def test_une_archive_montre_le_rang_fige_a_la_cloture(
    client: TestClient,
    en_base: Callable[..., Any],
    eleve: Utilisateur,
    en_cours: AnneeAcademique,
    passee: AnneeAcademique,
) -> None:
    ancien_gain(en_base, eleve.id, passee.id, 40, "ancien:1")

    async def figer(db: AsyncSession) -> None:
        db.add(
            ClassementAnnuel(
                annee_id=passee.id, region="maritime", utilisateur_id=eleve.id, pseudonyme="Ama du Golfe", club=None,
                points=40, rang=3,
            )
        )  # fmt: skip

    en_base(figer)

    archives = client.get(TABLEAU).json()["archives"]

    assert archives == [{"libelle": "2025-2026", "points": 40, "region": "maritime", "rang": 3}]


# Années et clôture, dans l'admin ---------------------------------------------------------------------------------


@pytest.fixture
def gestionnaire(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("points", droits=GESTION, double_auth=True)
    connecter_admin(client, "points")
    return client


def test_l_equipe_cree_une_annee_et_refuse_un_chevauchement(gestionnaire: TestClient) -> None:
    corps = {"libelle": "2027-2028", "debut": "2027-09-01", "fin": "2028-07-31"}

    assert gestionnaire.post(ANNEES, json=corps).status_code == 201
    assert gestionnaire.post(ANNEES, json=corps | {"libelle": "2028-2029"}).status_code == 409
    assert [a["libelle"] for a in gestionnaire.get(ANNEES).json()] == ["2027-2028"]


def test_la_cloture_fige_le_classement_regional_une_seule_fois(
    gestionnaire: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    passee: AnneeAcademique,
) -> None:
    premier = creer_eleve("kofi", affiche="Kofi")
    second = creer_eleve("ama", affiche="Ama")
    club_id = affilier(en_base, premier)
    ancien_gain(en_base, premier.id, passee.id, 100, "ancien:kofi")
    ancien_gain(en_base, second.id, passee.id, 5, "ancien:ama")

    reponse = gestionnaire.post(f"{ANNEES}/{passee.id}/cloture")
    encore = gestionnaire.post(f"{ANNEES}/{passee.id}/cloture")

    assert reponse.status_code == 200, reponse.text
    assert encore.status_code == 409
    assert classement(en_base) == [("Kofi", 100, 1), ("Ama", 5, 2)]
    clubs = en_base(lambda db: db.execute(select(ClassementAnnuel.pseudonyme, ClassementAnnuel.club))).all()
    nom = en_base(lambda db: db.scalar(select(Club.nom).where(Club.id == club_id)))
    assert dict(clubs) == {"Kofi": nom, "Ama": None}


def classement(en_base: Callable[..., Any]) -> list[tuple[str, int, int]]:
    lignes = en_base(
        lambda db: db.scalars(
            select(ClassementAnnuel).order_by(
                ClassementAnnuel.region, ClassementAnnuel.rang, ClassementAnnuel.pseudonyme
            )
        )
    ).all()
    return [(c.pseudonyme, c.points, c.rang) for c in lignes]


def test_la_cloture_classe_les_ex_aequo_au_meme_rang_et_par_region(
    gestionnaire: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    passee: AnneeAcademique,
) -> None:
    a = creer_eleve("eleve.aa", affiche="Aa")
    b = creer_eleve("eleve.bb", affiche="Bb")
    c = creer_eleve("eleve.cc", affiche="Cc")
    loin = creer_eleve("kara", affiche="Kara", dre="kara")
    sans_points = creer_eleve("zero", affiche="Zero")
    ancien = creer_eleve("ancien", affiche="Ancien")
    for eleve, montant in ((a, 50), (b, 50), (c, 10), (loin, 5), (ancien, 900)):
        ancien_gain(en_base, eleve.id, passee.id, montant, f"ancien:{eleve.identifiant}")
    en_base(
        lambda db: db.execute(
            update(Utilisateur)
            .where(Utilisateur.id == ancien.id)
            .values(ancien_eleve_le=datetime.combine(passee.fin - timedelta(days=10), time(12), tzinfo=UTC))
        )
    )

    assert gestionnaire.post(f"{ANNEES}/{passee.id}/cloture").status_code == 200

    lignes = en_base(lambda db: db.scalars(select(ClassementAnnuel))).all()
    par_pseudo = {c.pseudonyme: (c.region, c.rang) for c in lignes}
    assert {p: r for p, (_, r) in par_pseudo.items()} == {"Aa": 1, "Bb": 1, "Cc": 3, "Kara": 1}
    assert par_pseudo["Kara"][0] != par_pseudo["Aa"][0]
    assert sans_points.id not in {c.utilisateur_id for c in lignes}


def test_une_annee_ne_se_cloture_pas_avant_le_lendemain_de_sa_fin(
    gestionnaire: TestClient, en_base: Callable[..., Any]
) -> None:
    derniere_journee = annee(en_base, "2026-2027", AUJOURD_HUI - timedelta(days=300), AUJOURD_HUI)

    reponse = gestionnaire.post(f"{ANNEES}/{derniere_journee.id}/cloture")

    assert reponse.status_code == 409
    assert gestionnaire.get(ANNEES).json()[0]["cloturee_le"] is None


def test_un_eleve_passe_ancien_apres_la_fin_reste_dans_le_classement_de_l_annee(
    gestionnaire: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    passee: AnneeAcademique,
) -> None:
    pendant = creer_eleve("pendant", affiche="Pendant")
    apres = creer_eleve("apres", affiche="Apres")
    ancien_gain(en_base, pendant.id, passee.id, 50, "ancien:pendant")
    ancien_gain(en_base, apres.id, passee.id, 40, "ancien:apres")
    for compte, quand in ((pendant, passee.fin - timedelta(days=10)), (apres, passee.fin + timedelta(days=5))):
        moment = datetime.combine(quand, time(12), tzinfo=UTC)
        en_base(
            lambda db, c=compte, m=moment: db.execute(
                update(Utilisateur).where(Utilisateur.id == c.id).values(ancien_eleve_le=m)
            )
        )

    assert gestionnaire.post(f"{ANNEES}/{passee.id}/cloture").status_code == 200

    assert classement(en_base) == [("Apres", 40, 1)]


def test_le_credit_verrouille_l_annee_ouverte_contre_une_cloture(
    en_base: Callable[..., Any], en_cours: AnneeAcademique
) -> None:
    """Le crédit (`annee_en_cours`) pose un verrou partagé sur l'année ouverte jusqu'à la fin de sa transaction : un
    verrou exclusif, celui que prend la clôture, ne peut pas l'obtenir entre la lecture de l'année et l'écriture du
    gain."""
    from sqlalchemy.exc import DBAPIError

    from tests.conftest import moteur_test

    async def scenario() -> bool:
        async with AsyncSession(moteur_test) as credit, AsyncSession(moteur_test) as cloture:
            assert (await service.annee_en_cours(credit)) is not None
            try:
                await cloture.execute(
                    select(AnneeAcademique).where(AnneeAcademique.id == en_cours.id).with_for_update(nowait=True)
                )
            except DBAPIError:
                return True
            return False

    assert asyncio.run(scenario())


def test_une_annulation_reste_dans_l_annee_du_gain(
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_cours: AnneeAcademique,
    passee: AnneeAcademique,
) -> None:
    eleve = creer_eleve("kofi")
    ancien_gain(en_base, eleve.id, passee.id, 100, "ancien:1")

    async def annuler(db: AsyncSession) -> MouvementPoints | None:
        gain = await db.scalar(select(MouvementPoints).where(MouvementPoints.cle == "ancien:1"))
        assert gain is not None
        return await service.annuler(db, gain)

    annulation = en_base(annuler)

    assert annulation is not None and annulation.annee_id == passee.id


def test_l_equipe_passe_un_eleve_en_ancien_eleve(
    gestionnaire: TestClient, en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    eleve = creer_eleve("kofi")

    reponse = gestionnaire.post(f"/api/admin/points/anciens-eleves/{eleve.id}")

    assert reponse.status_code == 200, reponse.text
    compte = en_base(lambda db: db.get(Utilisateur, eleve.id))
    assert compte.ancien_eleve_le is not None


def test_le_club_voit_son_total_annuel_par_parcours(
    client: TestClient, en_base: Callable[..., Any], eleve: Utilisateur, en_cours: AnneeAcademique
) -> None:
    affilier(en_base, eleve)
    crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")
    crediter(en_base, ETOILE_NIVEAU["debutant"], eleve.id, "etoile:debutant")

    corps = client.get("/api/points/mon-club").json()

    assert corps["total_annuel"] == 252.5
    assert corps["parcours"] == {"certification": 0, "jeux": 250, "vie": 2.5}
    assert (corps["jeux_quiz"], corps["jeux_etoiles"]) == (0, 250)


def test_hors_d_un_club_pas_de_total(client: TestClient, eleve: Utilisateur) -> None:
    assert client.get("/api/points/mon-club").status_code == 404


def test_le_club_est_visible_par_son_encadreur(
    client: TestClient,
    en_base: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    en_cours: AnneeAcademique,
) -> None:
    eleve = creer_eleve("kofi")
    club_id = affilier(en_base, eleve)
    encadreur = creer_encadreur()

    async def rattacher(db: AsyncSession) -> None:
        from app.clubs.models import EtatRattachement, Rattachement

        db.add(Rattachement(encadreur_id=encadreur.id, club_id=club_id, etat=EtatRattachement.actif))

    en_base(rattacher)
    crediter(en_base, COMMENTAIRE_ELEVE, eleve.id, "commentaire:1")
    connecter(client, encadreur.identifiant)

    corps = client.get("/api/points/mon-club").json()

    assert corps["total_annuel"] == 2.5


def test_creer_ou_cloturer_une_annee_demande_le_droit_de_modifier_les_points(
    client: TestClient, creer_collaborateur: Callable[..., Any], passee: AnneeAcademique
) -> None:
    creer_collaborateur("lecteur", droits={("tableau_de_bord", "consulter"), ("points", "consulter")}, double_auth=True)
    connecter_admin(client, "lecteur")
    corps = {"libelle": "2027-2028", "debut": "2027-09-01", "fin": "2028-07-31"}

    assert client.post(ANNEES, json=corps).status_code == 403
    assert client.post(f"{ANNEES}/{passee.id}/cloture").status_code == 403
    assert client.post(f"/api/admin/points/anciens-eleves/{passee.id}").status_code == 403


def test_le_libelle_d_une_annee_suit_le_format_aaaa_aaaa(gestionnaire: TestClient) -> None:
    corps = {"libelle": "2027-2028b", "debut": "2027-09-01", "fin": "2028-07-31"}

    assert gestionnaire.post(ANNEES, json=corps).status_code == 422
    assert gestionnaire.post(ANNEES, json=corps | {"libelle": "27-28"}).status_code == 422


def test_seul_un_eleve_passe_en_ancien_eleve(
    gestionnaire: TestClient, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    encadreur = creer_encadreur()

    assert gestionnaire.post(f"/api/admin/points/anciens-eleves/{encadreur.id}").status_code == 404


def test_un_ancien_eleve_ne_recoit_plus_ni_badge_ni_certificat(
    en_base: Callable[..., Any], creer_eleve: Callable[..., Utilisateur]
) -> None:
    from tests.certification import acquerir, badges, certificats, creer_parcours, mettre_a_jour

    eleve = creer_eleve("kofi")
    acquerir(en_base, eleve, creer_parcours(en_base), range(1, 21))
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == eleve.id).values(ancien_eleve_le=service.maintenant())
        )
    )

    mettre_a_jour(en_base, eleve)

    assert badges(en_base, eleve.id) == []
    assert certificats(en_base, eleve.id) == []
