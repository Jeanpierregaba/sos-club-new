"""Suivi des certifications par l'équipe (spec 043) : candidats, entonnoir des 20 places, chiffres par DRE et par
semaine, export nominatif national. Écrit avant le code."""

from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin.models import JournalAudit
from app.certification.models import Certificat, EtatCertificat
from app.comptes.models import Role, Utilisateur
from app.quiz import parametres
from app.quiz.models import EtatTentative, Quiz, TentativeQuiz
from tests.certification import acquerir, creer_parcours, mettre_a_jour
from tests.conftest import connecter_admin
from tests.quiz import DEBUT

SUIVI = "/api/admin/certification/suivi"
LECTURE = {("quiz", "consulter")}
EXPORT = {("quiz", "consulter"), ("inscrits", "exporter")}
MAINTENANT = datetime.now(UTC)


@pytest.fixture
def parcours(en_base: Callable[..., Any]) -> dict[int, Quiz]:
    return creer_parcours(en_base)


def jouer(
    en_base: Callable[..., Any],
    joueur: Utilisateur,
    quiz: Quiz,
    *,
    nombre: int = 1,
    quand: datetime | None = None,
    reussie: bool = False,
    essai: bool = False,
) -> None:
    """Des tentatives terminées sur un quiz du parcours."""
    instant = quand or MAINTENANT

    async def inserer(db: Any) -> None:
        p = await parametres.en_cours(db, "certification")
        for _ in range(nombre):
            db.add(
                TentativeQuiz(
                    quiz_id=quiz.id, joueur_id=joueur.id, parametres_id=p.id, etat=EtatTentative.terminee,
                    jour=instant.date(), commencee_le=instant, derniere_activite=instant, terminee_le=instant,
                    score=10 if reussie else 3, reussie=reussie, essai=essai,
                )
            )  # fmt: skip

    en_base(inserer)


def valider(en_base: Callable[..., Any], joueur: Utilisateur, quiz: dict[int, Quiz], places: Iterable[int]) -> None:
    acquerir(en_base, joueur, quiz, places)
    mettre_a_jour(en_base, joueur)


@pytest.fixture
def national(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    creer_collaborateur("chef", droits=EXPORT, double_auth=True)
    connecter_admin(client, "chef")
    return client


def lire(client: TestClient, **filtres: Any) -> dict[str, Any]:
    reponse = client.get(f"{SUIVI}/candidats", params=filtres)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


# Les candidats ----------------------------------------------------------------------------------------------------


def test_un_candidat_apparait_des_sa_premiere_tentative(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama", "Ama du Golfe")
    creer_eleve("kofi", "Kofi")  # inscrit, jamais venu à la certification
    valider(en_base, ama, parcours, range(1, 5))
    jouer(en_base, ama, parcours[5], nombre=3, quand=MAINTENANT - timedelta(days=2))

    page = lire(national)

    assert page["total"] == 1
    candidat = page["candidats"][0]
    assert candidat["id"] == str(ama.id)
    assert candidat["nom"] == "Jean Kodjo"
    assert candidat["pseudonyme"] == "Ama du Golfe"
    assert candidat["role"] == "eleve"
    assert candidat["dre"] == "Grand Lomé"
    assert candidat["places_validees"] == 4
    assert candidat["badges"] == [1]
    assert candidat["place_en_cours"] == 5
    assert candidat["tentatives_place"] == 3
    assert candidat["tentatives"] == 7
    assert candidat["certificat"] is None
    assert candidat["ancien_eleve"] is False


def test_les_parties_d_essai_et_les_joueurs_sans_compte_sont_exclus(
    national: TestClient,
    creer_utilisateur: Callable[..., Utilisateur],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    jouer(en_base, creer_eleve("ama"), parcours[1], essai=True)
    jouer(en_base, creer_utilisateur("invite1", Role.invite), parcours[1])

    assert lire(national)["total"] == 0


def test_un_encadreur_candidat_et_le_filtre_par_role(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    jouer(en_base, creer_eleve("ama"), parcours[1])
    kofi = creer_encadreur("kofi", dre="kara")
    jouer(en_base, kofi, parcours[1])

    page = lire(national, role="encadreur")
    assert [c["id"] for c in page["candidats"]] == [str(kofi.id)]
    assert page["candidats"][0]["dre"] == "Kara"
    assert page["candidats"][0]["club"] is None
    assert lire(national, dre="kara")["total"] == 1
    assert lire(national)["total"] == 2


def test_le_filtre_par_club(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama")
    club = creer_club(ama, nom="Club Santé du Golfe")
    jouer(en_base, ama, parcours[1])
    jouer(en_base, creer_eleve("kofi", "Kofi"), parcours[1])

    page = lire(national, club_id=str(club.id))
    assert [c["id"] for c in page["candidats"]] == [str(ama.id)]
    assert page["candidats"][0]["club"] == {"id": str(club.id), "nom": "Club Santé du Golfe"}


def test_les_etats_en_cours_inactif_et_certifie(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    actif = creer_eleve("ama", "Ama")
    jouer(en_base, actif, parcours[1])
    endormi = creer_eleve("kofi", "Kofi")
    jouer(en_base, endormi, parcours[1], quand=MAINTENANT - timedelta(days=31))
    certifie = creer_eleve("yao", "Yao")
    valider(en_base, certifie, parcours, range(1, 21))

    def ids(etat: str) -> list[str]:
        return [c["id"] for c in lire(national, etat=etat)["candidats"]]

    assert ids("en_cours") == [str(actif.id)]
    assert ids("inactif") == [str(endormi.id)]
    assert ids("certifie") == [str(certifie.id)]
    yao = lire(national, etat="certifie")["candidats"][0]
    assert yao["certificat"].startswith("GI-")
    assert yao["place_en_cours"] is None
    assert yao["badges"] == [1, 2, 3, 4, 5]


def test_un_certificat_revoque_ne_compte_pas_et_un_certificat_reemis_compte_une_fois(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    revoque, reemis = creer_eleve("ama", "Ama"), creer_eleve("kofi", "Kofi")
    for joueur in (revoque, reemis):
        valider(en_base, joueur, parcours, range(1, 21))

    async def decider(db: Any) -> None:
        await db.execute(
            update(Certificat)
            .where(Certificat.utilisateur_id == revoque.id)
            .values(etat=EtatCertificat.revoque, motif="Fraude.", decide_le=MAINTENANT)
        )
        ancien = await db.scalar(select(Certificat).where(Certificat.utilisateur_id == reemis.id))
        ancien.etat, ancien.decide_le = EtatCertificat.remplace, MAINTENANT
        await db.flush()
        db.add(
            Certificat(
                numero="GI-REEM-ISSI-ON00", utilisateur_id=reemis.id, role="eleve", titulaire_prenom="Kofi",
                titulaire_nom="K", delivre_le=MAINTENANT, remplace_id=ancien.id,
            )
        )  # fmt: skip

    en_base(decider)

    assert [c["id"] for c in lire(national, etat="certifie")["candidats"]] == [str(reemis.id)]
    stats = national.get(f"{SUIVI}/statistiques").json()
    assert stats["totaux"]["certifies"] == 1


def test_la_recherche_et_la_pagination(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    for i, pseudo in enumerate(["Ama", "Kofi", "Yawa"]):
        jouer(en_base, creer_eleve(f"eleve{i}", pseudo), parcours[1], quand=MAINTENANT - timedelta(hours=i))

    assert [c["pseudonyme"] for c in lire(national, recherche="kofi")["candidats"]] == ["Kofi"]
    page = lire(national, par_page=2, page=2)
    assert page["total"] == 3
    # Triés par dernière activité, la plus récente d'abord.
    assert [c["pseudonyme"] for c in page["candidats"]] == ["Yawa"]


def test_un_ancien_eleve_est_marque(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama")
    jouer(en_base, ama, parcours[1])
    en_base(
        lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == ama.id).values(ancien_eleve_le=MAINTENANT))
    )

    assert lire(national)["candidats"][0]["ancien_eleve"] is True


def test_un_collaborateur_de_dre_ne_voit_que_sa_dre_et_les_pseudonymes(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama", "Ama du Golfe")
    jouer(en_base, ama, parcours[1])
    jouer(en_base, creer_eleve("kofi", "Kofi de Kara", dre="kara"), parcours[1])
    creer_collaborateur("dre", droits=LECTURE, perimetre_dre="grand-lome")
    connecter_admin(client, "dre")

    page = lire(client)
    assert [c["id"] for c in page["candidats"]] == [str(ama.id)]
    assert page["candidats"][0]["nom"] == "Ama du Golfe"
    assert lire(client, dre="kara")["total"] == 0
    # La recherche ne passe pas par le nom réel.
    assert lire(client, recherche="Kodjo")["total"] == 0

    stats = client.get(f"{SUIVI}/statistiques").json()
    assert stats["totaux"]["candidats"] == 1
    assert [d["dre"] for d in stats["par_dre"]] == ["Grand Lomé"]


def test_sans_le_droit_de_consulter_les_quiz_le_suivi_est_refuse(
    client: TestClient, creer_collaborateur: Callable[..., Any]
) -> None:
    creer_collaborateur("chef", droits={("inscrits", "consulter")})
    connecter_admin(client, "chef")

    assert client.get(f"{SUIVI}/candidats").status_code == 403
    assert client.get(f"{SUIVI}/statistiques").status_code == 403


# Les statistiques -------------------------------------------------------------------------------------------------


def test_aucun_candidat(national: TestClient, parcours: dict[int, Quiz]) -> None:
    stats = national.get(f"{SUIVI}/statistiques").json()

    assert stats["totaux"] == {
        "candidats": 0,
        "actifs_30_jours": 0,
        "certifies": 0,
        "badges": [{"rang": r, "nom": n, "nombre": 0} for r, n in enumerate(stats_noms(stats), start=1)],
    }
    assert [(e["place"], e["tentes"], e["reussis"]) for e in stats["entonnoir"]] == [(p, 0, 0) for p in range(1, 21)]
    assert all(e["taux_reussite"] is None and e["tentatives_avant_reussite"] is None for e in stats["entonnoir"])
    assert stats["par_dre"] == []
    assert len(stats["par_semaine"]) == 12
    assert all(s["candidats"] == 0 and s["certifies"] == 0 for s in stats["par_semaine"])


def stats_noms(stats: dict[str, Any]) -> list[str]:
    return [b["nom"] for b in stats["totaux"]["badges"]]


def test_l_entonnoir_des_20_places(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama, yao, kofi = creer_eleve("ama", "Ama"), creer_eleve("yao", "Yao"), creer_eleve("kofi", "Kofi")
    # Ama : 2 échecs puis la réussite de la place 1 (acquerir date la réussite à DEBUT), soit 3 tentatives ;
    # Yao : réussite du premier coup ; Kofi : 3 échecs.
    jouer(en_base, ama, parcours[1], nombre=2, quand=DEBUT - timedelta(days=3))
    valider(en_base, ama, parcours, [1])
    valider(en_base, yao, parcours, [1])
    jouer(en_base, kofi, parcours[1], nombre=3)
    # Plus de quiz publié sur la place 20.
    en_base(lambda db: db.execute(update(Quiz).where(Quiz.id == parcours[20].id).values(etat="depublie")))

    entonnoir = {e["place"]: e for e in national.get(f"{SUIVI}/statistiques").json()["entonnoir"]}

    assert (entonnoir[1]["tentes"], entonnoir[1]["reussis"]) == (3, 2)
    # 2 tentatives réussies sur 7 terminées.
    assert entonnoir[1]["taux_reussite"] == pytest.approx(2 / 7)
    # (3 + 1) / 2 tentatives jusqu'à la réussite.
    assert entonnoir[1]["tentatives_avant_reussite"] == pytest.approx(2.0)
    assert (entonnoir[2]["tentes"], entonnoir[2]["reussis"]) == (0, 0)
    assert entonnoir[2]["tentatives_avant_reussite"] is None
    assert entonnoir[2]["quiz_publie"] is True
    assert entonnoir[20]["quiz_publie"] is False


def _lundi(jour: date) -> str:
    return (jour - timedelta(days=jour.weekday())).isoformat()


def test_les_totaux_par_dre_et_par_semaine(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama", "Ama")
    valider(en_base, ama, parcours, range(1, 21))
    jouer(en_base, ama, parcours[20])
    kofi = creer_eleve("kofi", "Kofi", dre="kara")
    il_y_a_40_jours = MAINTENANT - timedelta(days=40)
    jouer(en_base, kofi, parcours[1], quand=il_y_a_40_jours)

    stats = national.get(f"{SUIVI}/statistiques").json()

    assert stats["totaux"]["candidats"] == 2
    assert stats["totaux"]["actifs_30_jours"] == 1
    assert stats["totaux"]["certifies"] == 1
    assert [b["nombre"] for b in stats["totaux"]["badges"]] == [1, 1, 1, 1, 1]
    assert {d["dre"]: (d["candidats"], d["badges"], d["certifies"]) for d in stats["par_dre"]} == {
        "Grand Lomé": (1, 5, 1),
        "Kara": (1, 0, 0),
    }
    semaines = {s["debut"]: (s["candidats"], s["certifies"]) for s in stats["par_semaine"]}
    assert len(semaines) == 12
    assert list(semaines)[-1] == _lundi(MAINTENANT.date())
    # Ama a commencé à DEBUT (sa première tentative) et a été certifiée cette semaine ; Kofi il y a 40 jours.
    attendu: dict[str, list[int]] = {jour: [0, 0] for jour in semaines}
    for jour, colonne in ((DEBUT.date(), 0), (il_y_a_40_jours.date(), 0), (MAINTENANT.date(), 1)):
        if _lundi(jour) in attendu:
            attendu[_lundi(jour)][colonne] += 1
    assert semaines == {jour: tuple(n) for jour, n in attendu.items()}


def test_le_perimetre_dre_s_applique_aux_chiffres(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    valider(en_base, creer_eleve("ama", "Ama"), parcours, range(1, 5))
    valider(en_base, creer_eleve("kofi", "Kofi", dre="kara"), parcours, range(1, 9))
    creer_collaborateur("dre", droits=LECTURE, perimetre_dre="grand-lome")
    connecter_admin(client, "dre")

    stats = client.get(f"{SUIVI}/statistiques").json()

    assert stats["entonnoir"][0]["tentes"] == 1
    assert stats["entonnoir"][4]["tentes"] == 0
    assert [b["nombre"] for b in stats["totaux"]["badges"]] == [1, 0, 0, 0, 0]
    assert sum(s["candidats"] for s in stats["par_semaine"]) <= 1


def test_un_national_sans_double_authentification_voit_les_pseudonymes(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    jouer(en_base, creer_eleve("ama", "Ama du Golfe"), parcours[1])
    jouer(en_base, creer_encadreur("kofi"), parcours[1])
    creer_collaborateur("lecteur", droits=LECTURE)
    connecter_admin(client, "lecteur")

    noms = {c["role"]: c["nom"] for c in lire(client)["candidats"]}
    assert noms == {"eleve": "Ama du Golfe", "encadreur": "Jean Kodjo"}
    assert [c["role"] for c in lire(client, recherche="Kodjo")["candidats"]] == ["encadreur"]


def test_certificats_et_badges_suivent_le_perimetre_et_la_regle_des_noms(
    client: TestClient,
    creer_collaborateur: Callable[..., Any],
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama", "Ama du Golfe")
    valider(en_base, ama, parcours, range(1, 21))
    valider(en_base, creer_eleve("kofi", "Kofi de Kara", dre="kara"), parcours, range(1, 21))
    creer_collaborateur("dre", droits=LECTURE, perimetre_dre="grand-lome")
    connecter_admin(client, "dre")

    certificats = client.get("/api/admin/certification/certificats").json()["certificats"]
    assert [(c["utilisateur_id"], c["titulaire"]) for c in certificats] == [(str(ama.id), "Ama du Golfe")]
    badges = client.get("/api/admin/certification/badges").json()["badges"]
    assert {b["titulaire"] for b in badges} == {"Ama du Golfe"}
    assert len(badges) == 5


# L'export ---------------------------------------------------------------------------------------------------------


def journal_export(en_base: Callable[..., Any]) -> list[JournalAudit]:
    return list(
        en_base(
            lambda db: db.scalars(select(JournalAudit).where(JournalAudit.action == "export_suivi_certification"))
        ).all()
    )


def test_l_export_csv_reprend_les_filtres_et_est_journalise(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
) -> None:
    ama = creer_eleve("ama", "=HYPERLIEN()")
    jouer(en_base, ama, parcours[1])
    jouer(en_base, creer_encadreur("kofi"), parcours[1])

    reponse = national.post(
        f"{SUIVI}/candidats/export", json={"filtres": {"role": "eleve"}, "finalite": "Relance des candidats"}
    )

    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["content-type"].startswith("text/csv")
    lignes = reponse.content.decode("utf-8-sig").strip().splitlines()
    assert len(lignes) == 2
    assert lignes[0].startswith("Nom;Pseudonyme;Rôle")
    assert "'=HYPERLIEN()" in lignes[1]
    [entree] = journal_export(en_base)
    assert entree.details["finalite"] == "Relance des candidats"
    assert entree.details["lignes"] == 1
    assert entree.details["filtres"]["role"] == "eleve"


def test_l_export_demande_une_finalite(national: TestClient) -> None:
    assert national.post(f"{SUIVI}/candidats/export", json={"filtres": {}, "finalite": " "}).status_code == 422


def test_l_export_est_refuse_sans_le_droit_ou_hors_du_national(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    corps = {"filtres": {}, "finalite": "Relance des candidats"}
    creer_collaborateur("lecteur", droits=LECTURE)
    connecter_admin(client, "lecteur")
    assert client.post(f"{SUIVI}/candidats/export", json=corps).status_code == 403

    creer_collaborateur("dre", droits=EXPORT, perimetre_dre="kara", double_auth=True)
    connecter_admin(client, "dre")
    assert client.post(f"{SUIVI}/candidats/export", json=corps).status_code == 403
    assert journal_export(en_base) == []


def test_l_export_est_limite(
    national: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
    parcours: dict[int, Quiz],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "export_lignes_max", 1)
    for i in range(2):
        jouer(en_base, creer_eleve(f"eleve{i}", f"Élève {i}"), parcours[1])

    reponse = national.post(f"{SUIVI}/candidats/export", json={"filtres": {}, "finalite": "Relance des candidats"})
    assert reponse.status_code == 422
    assert "précise les filtres" in reponse.json()["detail"]


def test_l_export_demande_la_double_authentification(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    creer_collaborateur("chef", droits=EXPORT)
    connecter_admin(client, "chef")

    reponse = client.post(f"{SUIVI}/candidats/export", json={"filtres": {}, "finalite": "Relance des candidats"})

    assert reponse.status_code == 403
    assert journal_export(en_base) == []
