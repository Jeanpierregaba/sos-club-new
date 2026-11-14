"""Classements courants (spec 036, ADR-0013) : partie critique, écrite avant le code (docs/TESTING.md)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub, EtatRattachement, Rattachement
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves.models import Classe, Eleve
from app.encadreurs.models import EtatVerification
from app.points import classements
from app.points.bareme import ACTION_CORRECTION, BIENVENUE_ELEVE
from app.points.models import MouvementPoints, Semestre
from app.points.service import aujourd_hui
from app.referentiel.models import Dre, Etablissement, Iesg

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture
def semestre(en_base: Callable[..., Any]) -> Semestre:
    async def inserer(db: AsyncSession) -> Semestre:
        element = Semestre(
            libelle="Semestre en cours",
            debut=aujourd_hui() - timedelta(days=10),
            fin=aujourd_hui() + timedelta(days=10),
        )
        db.add(element)
        return element

    return en_base(inserer)


def point(
    en_base: Callable[..., Any],
    utilisateur_id: UUID,
    montant: int,
    cle: str,
    *,
    semestre_id: UUID | None = None,
    club_id: UUID | None = None,
    demi_points: int | None = None,
    action: str = BIENVENUE_ELEVE,
    motif: str | None = None,
    annule_id: UUID | None = None,
) -> MouvementPoints:
    async def inserer(db: AsyncSession) -> MouvementPoints:
        ligne = MouvementPoints(
            utilisateur_id=utilisateur_id,
            action=action,
            montant=montant,
            semestre_id=semestre_id,
            cle=cle,
            club_id=club_id,
            demi_points_club=demi_points if club_id is not None else None,
            motif=motif,
            annule_id=annule_id,
        )
        db.add(ligne)
        return ligne

    return en_base(inserer)


def affilier(en_base: Callable[..., Any], eleve_id: UUID, club_id: UUID) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(Adhesion(eleve_id=eleve_id, club_id=club_id, etat=EtatAdhesion.active))

    en_base(inserer)


def rattacher(en_base: Callable[..., Any], encadreur_id: UUID, club_id: UUID) -> None:
    async def inserer(db: AsyncSession) -> None:
        db.add(Rattachement(encadreur_id=encadreur_id, club_id=club_id, etat=EtatRattachement.actif))

    en_base(inserer)


def renommer(en_base: Callable[..., Any], utilisateur_id: UUID, prenom: str, nom: str) -> None:
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == utilisateur_id).values(prenom=prenom, nom=nom)
        )
    )


def etat_club(
    en_base: Callable[..., Any],
    club_id: UUID,
    etat: EtatClub,
    *,
    echeance: datetime | None = None,
) -> None:
    en_base(
        lambda db: db.execute(update(Club).where(Club.id == club_id).values(etat=etat, regularisation_jusquau=echeance))
    )


def etablissements_de(en_base: Callable[..., Any], dre: str, nombre: int) -> list[UUID]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(Etablissement.id)
                .join(Iesg, Iesg.id == Etablissement.iesg_id)
                .join(Dre, Dre.code == Iesg.dre_code)
                .where(Dre.code == dre)
                .order_by(Etablissement.nom)
                .limit(nombre)
            )
        )
    )


def club_dans(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    dre: str,
    etablissement_id: UUID,
    identifiant: str,
    nom: str,
    etat: EtatClub = EtatClub.actif,
) -> Club:
    president = creer_eleve(identifiant, f"Président {nom}", dre=dre, etablissement_id=etablissement_id)
    return creer_club(president, nom=nom, etat=etat)


def classement(
    en_base: Callable[..., Any],
    *,
    categorie: classements.Categorie = classements.Categorie.eleves,
    niveau: classements.Niveau = classements.Niveau.national,
    dre: str | None = None,
    periode: classements.Periode = classements.Periode.semestre,
    page: int = 1,
    par_page: int = 50,
) -> classements.Classement:
    return en_base(
        lambda db: classements.classement_public(
            db,
            categorie=categorie,
            niveau=niveau,
            dre_code=dre,
            periode=periode,
            page=page,
            par_page=par_page,
        )
    )


# Élèves -------------------------------------------------------------------------------------------------------


def test_classement_national_des_eleves_par_points(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    aya = creer_eleve("eleve-a", "Aya", dre="grand-lome")
    ben = creer_eleve("eleve-b", "Ben", dre="maritime")
    celine = creer_eleve("eleve-c", "Céline", dre="grand-lome")
    point(en_base, aya.id, 100, "aya", semestre_id=semestre.id)
    point(en_base, ben.id, 50, "ben", semestre_id=semestre.id)
    point(en_base, celine.id, 75, "celine", semestre_id=semestre.id)

    resultat = classement(en_base)

    assert [(ligne.rang, ligne.nom, ligne.club, ligne.dre, ligne.points) for ligne in resultat.lignes] == [
        (1, "Aya", None, "Grand Lomé", 100),
        (2, "Céline", None, "Grand Lomé", 75),
        (3, "Ben", None, "Maritime", 50),
    ]
    assert resultat.total == 3
    assert resultat.semestre is not None and resultat.semestre.libelle == "Semestre en cours"
    assert resultat.dre is None


def test_le_classement_dune_dre_suit_letablissement_actuel_de_leleve(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    aya = creer_eleve("eleve-a", "Aya", dre="grand-lome")
    ben = creer_eleve("eleve-b", "Ben", dre="maritime")
    point(en_base, aya.id, 100, "aya", semestre_id=semestre.id)
    point(en_base, ben.id, 50, "ben", semestre_id=semestre.id)

    resultat = classement(en_base, niveau=classements.Niveau.dre, dre="grand-lome")

    assert [ligne.nom for ligne in resultat.lignes] == ["Aya"]
    assert resultat.dre is not None and resultat.dre.code == "grand-lome"
    assert resultat.total == 1


def test_les_eleves_sans_point_ou_a_total_nul_ne_sont_pas_classes(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    sans_point = creer_eleve("eleve-sans", "Sans point", dre="grand-lome")
    annule = creer_eleve("eleve-annule", "Total nul", dre="grand-lome")
    point(en_base, annule.id, 10, "gain", semestre_id=semestre.id)
    point(
        en_base,
        annule.id,
        -10,
        "correction",
        semestre_id=semestre.id,
        action=ACTION_CORRECTION,
        motif="Annulation de test.",
    )

    resultat = classement(en_base)

    assert resultat.total == 0
    assert resultat.lignes == []
    assert sans_point.id != annule.id


def test_un_ancien_eleve_quitte_le_semestre_mais_reste_dans_lhistorique(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    ancien = creer_eleve("eleve-ancien", "Ancien", dre="grand-lome")
    point(en_base, ancien.id, 80, "ancien", semestre_id=semestre.id)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == ancien.id).values(ancien_eleve_le=datetime.now(UTC))
        )
    )

    semestre_courant = classement(en_base)
    historique = classement(en_base, periode=classements.Periode.historique)

    assert semestre_courant.total == 0
    assert [(ligne.nom, ligne.points) for ligne in historique.lignes] == [("Ancien", 80)]


def test_un_compte_suspendu_est_exclu_des_classements(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    suspendu = creer_eleve("eleve-suspendu", "Suspendu", dre="grand-lome")
    point(en_base, suspendu.id, 80, "suspendu", semestre_id=semestre.id)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == suspendu.id).values(statut=StatutCompte.suspendu)
        )
    )

    assert classement(en_base).total == 0


def test_a_egalite_les_eleves_partagent_le_rang_et_lordre_est_stable(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    zoe = creer_eleve("eleve-z", "Zoé", dre="grand-lome")
    ama = creer_eleve("eleve-a", "Ama", dre="grand-lome")
    ben = creer_eleve("eleve-b", "Ben", dre="grand-lome")
    point(en_base, zoe.id, 50, "zoe", semestre_id=semestre.id)
    point(en_base, ama.id, 50, "ama", semestre_id=semestre.id)
    point(en_base, ben.id, 100, "ben", semestre_id=semestre.id)

    resultat = classement(en_base)

    assert [(ligne.rang, ligne.nom) for ligne in resultat.lignes] == [
        (1, "Ben"),
        (2, "Ama"),
        (2, "Zoé"),
    ]


def test_le_semestre_et_lhistorique_additionnent_des_periodes_differentes(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    eleve = creer_eleve("eleve-a", "Aya", dre="grand-lome")
    point(en_base, eleve.id, 30, "hors-semestre")
    point(en_base, eleve.id, 70, "semestre", semestre_id=semestre.id)

    semestre_courant = classement(en_base)
    historique = classement(en_base, periode=classements.Periode.historique)

    assert [ligne.points for ligne in semestre_courant.lignes] == [70]
    assert [ligne.points for ligne in historique.lignes] == [100]


# Encadreurs ---------------------------------------------------------------------------------------------------


def test_classement_des_encadreurs_avec_prenom_initiale_et_club(
    creer_encadreur: Callable[..., Utilisateur],
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    etab = etablissements_de(en_base, "grand-lome", 1)[0]
    club = club_dans(creer_eleve, creer_club, "grand-lome", etab, "president", "Club Alpha")
    kossi = creer_encadreur("enc-kossi", dre="grand-lome", etablissement_id=etab)
    aya = creer_encadreur("enc-aya", dre="grand-lome", etablissement_id=etab)
    en_attente = creer_encadreur(
        "enc-attente", dre="grand-lome", etablissement_id=etab, etat=EtatVerification.en_attente
    )
    renommer(en_base, kossi.id, "Kossi", "Adjo")
    renommer(en_base, aya.id, "Aya", "Kponvi")
    rattacher(en_base, kossi.id, club.id)
    point(en_base, kossi.id, 80, "kossi", semestre_id=semestre.id)
    point(en_base, aya.id, 120, "aya", semestre_id=semestre.id)
    point(en_base, en_attente.id, 500, "attente", semestre_id=semestre.id)

    resultat = classement(en_base, categorie=classements.Categorie.encadreurs)

    assert [(ligne.rang, ligne.nom, ligne.club, ligne.points) for ligne in resultat.lignes] == [
        (1, "Aya K.", None, 120),
        (2, "Kossi A.", "Club Alpha", 80),
    ]


def test_un_encadreur_suspendu_est_exclu(
    creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    suspendu = creer_encadreur("enc-suspendu")
    point(en_base, suspendu.id, 80, "suspendu", semestre_id=semestre.id)
    en_base(
        lambda db: db.execute(
            update(Utilisateur).where(Utilisateur.id == suspendu.id).values(statut=StatutCompte.suspendu)
        )
    )

    assert classement(en_base, categorie=classements.Categorie.encadreurs).total == 0


def test_le_classement_des_encadreurs_filtre_par_dre(
    creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any], semestre: Semestre
) -> None:
    lome = creer_encadreur("enc-lome", dre="grand-lome")
    maritime = creer_encadreur("enc-maritime", dre="maritime")
    renommer(en_base, lome.id, "Kossi", "Adjo")
    renommer(en_base, maritime.id, "Aya", "Kponvi")
    point(en_base, lome.id, 10, "lome", semestre_id=semestre.id)
    point(en_base, maritime.id, 20, "maritime", semestre_id=semestre.id)

    resultat = classement(
        en_base,
        categorie=classements.Categorie.encadreurs,
        niveau=classements.Niveau.dre,
        dre="grand-lome",
    )

    assert [ligne.nom for ligne in resultat.lignes] == ["Kossi A."]


# Clubs --------------------------------------------------------------------------------------------------------


def test_classement_des_clubs_avec_score_decimal_et_exclusions(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    lieux = etablissements_de(en_base, "grand-lome", 5)
    actif = club_dans(creer_eleve, creer_club, "grand-lome", lieux[0], "pres-actif", "Club Actif")
    regulier = club_dans(creer_eleve, creer_club, "grand-lome", lieux[1], "pres-regulier", "Club Régulier")
    suspendu = club_dans(creer_eleve, creer_club, "grand-lome", lieux[2], "pres-suspendu", "Club Suspendu")
    constitution = club_dans(
        creer_eleve,
        creer_club,
        "grand-lome",
        lieux[3],
        "pres-constitution",
        "Club En Constitution",
        etat=EtatClub.en_constitution,
    )
    contributeur = creer_eleve("contributeur", "Contributeur", dre="grand-lome")
    point(en_base, contributeur.id, 10, "actif-1", semestre_id=semestre.id, club_id=actif.id, demi_points=10)
    point(en_base, contributeur.id, 5, "actif-2", semestre_id=semestre.id, club_id=actif.id, demi_points=5)
    point(en_base, contributeur.id, 5, "regulier", semestre_id=semestre.id, club_id=regulier.id, demi_points=5)
    point(en_base, contributeur.id, 100, "suspendu", semestre_id=semestre.id, club_id=suspendu.id, demi_points=100)
    point(
        en_base,
        contributeur.id,
        100,
        "constitution",
        semestre_id=semestre.id,
        club_id=constitution.id,
        demi_points=100,
    )
    etat_club(
        en_base,
        regulier.id,
        EtatClub.en_regularisation,
        echeance=datetime.now(UTC) + timedelta(days=15),
    )
    etat_club(en_base, suspendu.id, EtatClub.suspendu)

    resultat = classement(en_base, categorie=classements.Categorie.clubs)

    assert [(ligne.rang, ligne.nom, ligne.points) for ligne in resultat.lignes] == [
        (1, "Club Actif", 7.5),
        (2, "Club Régulier", 2.5),
    ]
    assert all(ligne.etablissement for ligne in resultat.lignes)
    assert resultat.total == 2


def test_un_club_en_regularisation_echue_est_exclu(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    etab = etablissements_de(en_base, "grand-lome", 1)[0]
    club = club_dans(creer_eleve, creer_club, "grand-lome", etab, "pres", "Club Tardif")
    point(en_base, club.president_id, 10, "tardif", semestre_id=semestre.id, club_id=club.id, demi_points=10)
    etat_club(
        en_base,
        club.id,
        EtatClub.en_regularisation,
        echeance=datetime.now(UTC) - timedelta(days=1),
    )

    assert classement(en_base, categorie=classements.Categorie.clubs).total == 0


def test_le_classement_des_clubs_filtre_par_dre(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    lome = etablissements_de(en_base, "grand-lome", 1)[0]
    maritime = etablissements_de(en_base, "maritime", 1)[0]
    club_lome = club_dans(creer_eleve, creer_club, "grand-lome", lome, "pres-lome", "Club Lomé")
    club_maritime = club_dans(creer_eleve, creer_club, "maritime", maritime, "pres-maritime", "Club Maritime")
    contributeur = creer_eleve("contributeur", "Contributeur", dre="grand-lome")
    point(en_base, contributeur.id, 10, "lome", semestre_id=semestre.id, club_id=club_lome.id, demi_points=10)
    point(
        en_base,
        contributeur.id,
        20,
        "maritime",
        semestre_id=semestre.id,
        club_id=club_maritime.id,
        demi_points=20,
    )

    resultat = classement(
        en_base,
        categorie=classements.Categorie.clubs,
        niveau=classements.Niveau.dre,
        dre="grand-lome",
    )

    assert [(ligne.nom, ligne.points) for ligne in resultat.lignes] == [("Club Lomé", 5.0)]


def test_un_club_a_total_nul_ou_negatif(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
    semestre: Semestre,
) -> None:
    lieux = etablissements_de(en_base, "grand-lome", 2)
    nul = club_dans(creer_eleve, creer_club, "grand-lome", lieux[0], "pres-nul", "Club Nul")
    negatif = club_dans(creer_eleve, creer_club, "grand-lome", lieux[1], "pres-negatif", "Club Négatif")
    gain_nul = point(en_base, nul.president_id, 10, "nul-gain", semestre_id=semestre.id, club_id=nul.id, demi_points=10)
    point(
        en_base,
        nul.president_id,
        -10,
        "nul-annulation",
        semestre_id=semestre.id,
        club_id=nul.id,
        demi_points=-10,
        annule_id=gain_nul.id,
    )
    gain_negatif = point(
        en_base,
        negatif.president_id,
        10,
        "negatif-gain",
        semestre_id=semestre.id,
        club_id=negatif.id,
        demi_points=10,
    )
    point(
        en_base,
        negatif.president_id,
        -30,
        "negatif-annulation",
        semestre_id=semestre.id,
        club_id=negatif.id,
        demi_points=-30,
        annule_id=gain_negatif.id,
    )

    resultat = classement(en_base, categorie=classements.Categorie.clubs)

    assert [(ligne.nom, ligne.points) for ligne in resultat.lignes] == [("Club Négatif", -10.0)]


# Pagination, semestre absent, DRE -----------------------------------------------------------------------------


def test_la_pagination_annonce_le_total_et_la_page_suivante(en_base: Callable[..., Any], semestre: Semestre) -> None:
    async def creer(db: AsyncSession) -> list[UUID]:
        etab = await db.scalar(
            select(Etablissement.id)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Dre.code == "grand-lome")
            .limit(1)
        )
        ids = []
        for numero in range(55):
            compte = Utilisateur(
                identifiant=f"eleve-{numero:03d}",
                role=Role.eleve,
                prenom="Test",
                nom="Test",
                mot_de_passe_hash="inutilise",
            )
            db.add(compte)
            await db.flush()
            db.add(
                Eleve(
                    utilisateur_id=compte.id,
                    pseudonyme=f"Élève {numero:03d}",
                    pseudonyme_normalise=f"eleve{numero:03d}",
                    classe=Classe.seconde,
                    etablissement_id=etab,
                    charte_version="test",
                )
            )
            db.add(
                MouvementPoints(
                    utilisateur_id=compte.id,
                    action=BIENVENUE_ELEVE,
                    montant=numero + 1,
                    semestre_id=semestre.id,
                    cle=f"pagination-{numero:03d}",
                )
            )
            ids.append(compte.id)
        return ids

    en_base(creer)

    page_1 = classement(en_base, page=1, par_page=50)
    page_2 = classement(en_base, page=2, par_page=50)

    assert page_1.total == page_2.total == 55
    assert len(page_1.lignes) == 50
    assert len(page_2.lignes) == 5
    assert [ligne.rang for ligne in page_1.lignes[:2]] == [1, 2]
    assert [ligne.rang for ligne in page_2.lignes] == [51, 52, 53, 54, 55]


def test_sans_semestre_le_semestre_est_vide_et_lhistorique_reste_lisible(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("eleve-a", "Aya", dre="grand-lome")
    point(en_base, eleve.id, 40, "hors-semestre")

    semestre = classement(en_base)
    historique = classement(en_base, periode=classements.Periode.historique)

    assert semestre.semestre is None
    assert semestre.total == 0
    assert semestre.lignes == []
    assert [(ligne.nom, ligne.points) for ligne in historique.lignes] == [("Aya", 40)]


def test_le_niveau_dre_exige_une_dre_connue_et_active(en_base: Callable[..., Any], semestre: Semestre) -> None:
    with pytest.raises(classements.DreRequise):
        classement(en_base, niveau=classements.Niveau.dre)
    with pytest.raises(classements.DreIntrouvable):
        classement(en_base, niveau=classements.Niveau.dre, dre="inconnue")
    en_base(lambda db: db.execute(update(Dre).where(Dre.code == "maritime").values(actif=False)))
    with pytest.raises(classements.DreIntrouvable):
        classement(en_base, niveau=classements.Niveau.dre, dre="maritime")
