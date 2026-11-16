"""Cartes numériques (spec 040) : délivrance, numéro unique et statut calculé. Partie critique (comptes, données
publiques), écrite avant le code."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartes import service
from app.cartes.models import Carte, TypeCarte
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import StatutCompte, Utilisateur
from app.config import settings
from app.encadreurs.models import Encadreur, EtatVerification
from tests.conftest import Navigateur, connecter_admin, moteur_test
from tests.espace_club import adherer, rattacher
from tests.test_eleves_espace import inscrire

pytestmark = pytest.mark.usefixtures("annuaire")


@pytest.fixture(autouse=True)
def inscriptions_ouvertes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "inscriptions_ouvertes", True)


def etat(en_base: Callable[..., Any], utilisateur_id: Any) -> service.EtatCarte | None:
    return en_base(lambda db: service.etat_du_compte(db, UUID(str(utilisateur_id))))


def cartes(en_base: Callable[..., Any], utilisateur_id: Any) -> list[Carte]:
    return list(en_base(lambda db: db.scalars(select(Carte).where(Carte.utilisateur_id == utilisateur_id))).all())


def statut(en_base: Callable[..., Any], utilisateur_id: Any, valeur: StatutCompte) -> None:
    en_base(lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == utilisateur_id).values(statut=valeur)))


# Délivrance -----------------------------------------------------------------------------------------------------


def test_une_inscription_delivre_une_carte_non_affiliee(client: TestClient, en_base: Callable[..., Any]) -> None:
    eleve = inscrire(client, en_base)

    (carte,) = cartes(en_base, eleve["id"])
    assert carte.type is TypeCarte.membre
    assert carte.numero.startswith("CS-M-") and len(carte.numero) == 11
    assert len(carte.code) == 32
    vue = etat(en_base, eleve["id"])
    assert vue is not None
    assert (vue.valide, vue.club, vue.role, vue.prenom, vue.nom) == (True, None, "membre", "Aya", "Mensah")
    assert vue.etablissement == "Lycée de Tokoin I"


def test_delivrer_deux_fois_ne_cree_rien(creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]) -> None:
    eleve = creer_eleve("ama")
    avant = cartes(en_base, eleve.id)

    en_base(lambda db: service.delivrer(db, eleve.id, TypeCarte.membre))

    assert [c.id for c in cartes(en_base, eleve.id)] == [c.id for c in avant] and len(avant) == 1


def test_numeros_et_codes_uniques_sous_delivrances_simultanees(
    creer_utilisateur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    comptes = [creer_utilisateur(f"compte{i}") for i in range(20)]

    async def une(utilisateur_id: UUID) -> None:
        async with AsyncSession(moteur_test, expire_on_commit=False) as db:
            await service.delivrer(db, utilisateur_id, TypeCarte.membre)
            await db.commit()

    async def scenario() -> None:
        await asyncio.gather(*(une(c.id) for c in comptes for _ in range(2)))

    asyncio.run(scenario())

    lignes = en_base(lambda db: db.execute(select(Carte.numero, Carte.code, Carte.utilisateur_id))).all()
    assert len(lignes) == 20
    assert len({n for n, _, _ in lignes}) == 20 and len({c for _, c, _ in lignes}) == 20


def test_un_numero_nest_jamais_reattribue(creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]) -> None:
    eleve = creer_eleve("ama")
    (carte,) = cartes(en_base, eleve.id)
    en_base(lambda db: db.execute(update(Carte).where(Carte.id == carte.id).values(utilisateur_id=None)))

    nouveau = creer_eleve("kofi", "Kofi du Golfe")

    (autre,) = cartes(en_base, nouveau.id)
    assert autre.numero != carte.numero
    assert en_base(lambda db: db.scalar(select(func.count()).select_from(Carte))) == 2


def test_un_visiteur_ou_un_collaborateur_na_pas_de_carte(
    creer_utilisateur: Callable[..., Utilisateur], creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from app.comptes.models import Role

    visiteur = creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg")
    chef = creer_collaborateur("chef")

    assert etat(en_base, visiteur.id) is None and etat(en_base, chef.id) is None


# Élève --------------------------------------------------------------------------------------------------------


def test_laffiliation_affiche_le_club_puis_non_affilie_sans_changer_de_numero(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    presidente = creer_eleve("presidente", "Ama")
    club = creer_club(presidente, nom="Club Santé Tokoin")
    membre = creer_eleve("membre", "Yao")
    numero = cartes(en_base, membre.id)[0].numero
    adhesion = adherer(en_base, membre, club, EtatAdhesion.en_attente_validation)
    assert etat(en_base, membre.id).club is None

    en_base(lambda db: db.execute(update(Adhesion).where(Adhesion.id == adhesion.id).values(etat=EtatAdhesion.active)))
    vue = etat(en_base, membre.id)
    assert (vue.club, vue.role, vue.numero, vue.valide) == ("Club Santé Tokoin", "membre", numero, True)

    en_base(lambda db: db.execute(update(Adhesion).where(Adhesion.id == adhesion.id).values(etat=EtatAdhesion.retiree)))
    vue = etat(en_base, membre.id)
    assert (vue.club, vue.valide, vue.numero) == (None, True, numero)


def test_la_presidence_change_le_role(
    creer_eleve: Callable[..., Utilisateur], creer_club: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    presidente = creer_eleve("presidente", "Ama")
    club = creer_club(presidente)
    assert etat(en_base, presidente.id).role == "president"

    en_base(lambda db: db.execute(update(Club).where(Club.id == club.id).values(president_id=None)))

    assert etat(en_base, presidente.id).role == "membre"


def test_un_compte_suspendu_puis_reactive_garde_son_numero(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("ama")
    numero = etat(en_base, eleve.id).numero

    statut(en_base, eleve.id, StatutCompte.suspendu)
    vue = etat(en_base, eleve.id)
    assert (vue.valide, vue.cause) == (False, "compte_suspendu")

    statut(en_base, eleve.id, StatutCompte.actif)
    vue = etat(en_base, eleve.id)
    assert (vue.valide, vue.cause, vue.numero) == (True, None, numero)


def test_la_suspension_par_lequipe_tient_apres_la_reactivation_du_compte(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    from datetime import UTC, datetime

    eleve = creer_eleve("ama")
    en_base(
        lambda db: db.execute(
            update(Carte)
            .where(Carte.utilisateur_id == eleve.id)
            .values(suspendue_le=datetime.now(UTC), motif_suspension="Carte falsifiée signalée.")
        )
    )
    statut(en_base, eleve.id, StatutCompte.suspendu)
    statut(en_base, eleve.id, StatutCompte.actif)

    vue = etat(en_base, eleve.id)
    assert (vue.valide, vue.cause) == (False, "suspendue_par_l_equipe")


def test_une_carte_sans_compte_nest_pas_valide(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    eleve = creer_eleve("ama")
    (carte,) = cartes(en_base, eleve.id)
    en_base(lambda db: db.execute(update(Carte).where(Carte.id == carte.id).values(utilisateur_id=None)))

    async def lire(db: AsyncSession) -> service.EtatCarte:
        relue = await db.get(Carte, carte.id)
        assert relue is not None
        return await service.etat_de(db, relue)

    vue = en_base(lire)

    assert (vue.valide, vue.cause, vue.prenom, vue.club) == (False, "compte_supprime", None, None)


# Encadreur ----------------------------------------------------------------------------------------------------


def test_lencadreur_en_attente_na_pas_de_carte(
    creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    prof = creer_encadreur("prof", etat=EtatVerification.en_attente)

    assert etat(en_base, prof.id) is None


def test_la_carte_de_lencadreur_suit_son_rattachement(
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    creer_encadreur: Callable[..., Utilisateur],
    en_base: Callable[..., Any],
) -> None:
    club = creer_club(creer_eleve("presidente", "Ama"), nom="Club Santé Tokoin")
    prof = creer_encadreur("prof")
    vue = etat(en_base, prof.id)
    assert vue.numero.startswith("CS-E-")
    assert (vue.valide, vue.cause, vue.role, vue.club) == (False, "sans_rattachement", "encadreur", None)

    lien = rattacher(en_base, prof, club)
    vue = etat(en_base, prof.id)
    assert (vue.valide, vue.cause, vue.club) == (True, None, "Club Santé Tokoin")

    en_base(
        lambda db: db.execute(
            update(Rattachement).where(Rattachement.id == lien.id).values(etat=EtatRattachement.retire)
        )
    )
    assert etat(en_base, prof.id).valide is False

    en_base(
        lambda db: db.execute(
            update(Encadreur).where(Encadreur.utilisateur_id == prof.id).values(etat=EtatVerification.en_attente)
        )
    )
    rattacher(en_base, prof, club)
    assert etat(en_base, prof.id).cause == "non_verifie"


def test_lactivation_par_lequipe_delivre_la_carte(
    client: TestClient, creer_collaborateur: Callable[..., Any], en_base: Callable[..., Any]
) -> None:
    from tests.test_encadreurs_admin import GESTION
    from tests.test_encadreurs_admin import inscrire as inscrire_encadreur

    creer_collaborateur("gestion", droits=GESTION, double_auth=True)
    connecter_admin(client, "gestion")
    prof = inscrire_encadreur(Navigateur(client), en_base, 1)
    assert etat(en_base, prof["id"]) is None

    assert client.post(f"/api/admin/encadreurs/{prof['id']}/activer").status_code == 200

    vue = etat(en_base, prof["id"])
    assert vue is not None and vue.type is TypeCarte.encadreur


# Migration ----------------------------------------------------------------------------------------------------


def test_la_migration_delivre_les_cartes_des_comptes_existants(
    creer_eleve: Callable[..., Utilisateur], creer_encadreur: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    from alembic.config import Config

    from alembic import command

    eleve = creer_eleve("ama")
    prof = creer_encadreur("prof")
    attente = creer_encadreur("nouveau", etat=EtatVerification.en_attente)
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
    command.downgrade(configuration, "865d24f039ea")
    command.upgrade(configuration, "head")

    assert [c.type for c in cartes(en_base, eleve.id)] == [TypeCarte.membre]
    assert [c.type for c in cartes(en_base, prof.id)] == [TypeCarte.encadreur]
    assert cartes(en_base, attente.id) == []
    assert all(len(c.code) == 32 for c in cartes(en_base, eleve.id))


# Espace et fichiers ----------------------------------------------------------------------------------------------

MOI = "/api/cartes/moi"


def test_le_titulaire_voit_sa_carte_et_seulement_la_sienne(
    client: TestClient,
    creer_eleve: Callable[..., Utilisateur],
    creer_club: Callable[..., Any],
    en_base: Callable[..., Any],
) -> None:
    from tests.espace_club import connecter

    presidente = creer_eleve("presidente", "Ama")
    creer_club(presidente, nom="Club Santé Tokoin")
    creer_eleve("autre", "Kofi")
    reponse = connecter(client, "presidente").get(MOI)

    assert reponse.status_code == 200, reponse.text
    assert reponse.headers["cache-control"] == "no-store"
    carte = reponse.json()
    assert carte["numero"] == cartes(en_base, presidente.id)[0].numero
    assert (carte["role"], carte["club"], carte["valide"], carte["cause"]) == (
        "president",
        "Club Santé Tokoin",
        True,
        None,
    )
    code = cartes(en_base, presidente.id)[0].code
    assert carte["adresse_verification"].endswith(f"/carte/{code}")


def test_sans_carte_la_page_repond_404(
    client: TestClient,
    creer_utilisateur: Callable[..., Utilisateur],
    creer_encadreur: Callable[..., Utilisateur],
) -> None:
    from app.comptes.models import Role
    from tests.espace_club import connecter

    creer_utilisateur("passant", Role.visiteur, email="passant@exemple.tg", email_confirme_le=None)
    creer_encadreur("nouveau", etat=EtatVerification.en_attente)

    assert connecter(client, "nouveau").get(MOI).status_code == 404
    assert Navigateur(client).get(MOI).status_code == 401


def test_le_pdf_et_limage_de_la_carte(
    client: TestClient, creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    import io

    from PIL import Image

    from tests.espace_club import connecter

    eleve = creer_eleve("ama")
    navigateur = connecter(client, "ama")

    document = navigateur.get(f"{MOI}.pdf")
    assert document.status_code == 200, document.text
    assert document.headers["content-type"] == "application/pdf"
    assert document.headers["cache-control"] == "no-store"
    numero = cartes(en_base, eleve.id)[0].numero
    assert f'filename="carte-membre-{numero}.pdf"' in document.headers["content-disposition"]
    assert document.content.startswith(b"%PDF")

    image = navigateur.get(f"{MOI}.png")
    assert image.status_code == 200 and image.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(image.content)).size == (1012, 638)


def test_le_rendu_porte_le_nom_le_numero_et_ladresse(
    creer_eleve: Callable[..., Utilisateur], en_base: Callable[..., Any]
) -> None:
    from app.cartes import rendu

    eleve = creer_eleve("ama")
    en_base(
        lambda db: db.execute(update(Utilisateur).where(Utilisateur.id == eleve.id).values(prenom="Ɖɔkɔ", nom="Ŋʋɛ"))
    )
    vue = etat(en_base, eleve.id)
    vus: list[str] = []
    adresses: list[str] = []
    origine = rendu._qr

    def qr_espion(e: service.EtatCarte) -> Any:
        adresses.append(rendu.adresse_de_verification(e.code))
        return origine(e)

    with pytest.MonkeyPatch.context() as m:
        m.setattr(rendu, "_qr", qr_espion)
        textes = [t.texte for t in rendu._textes(vue)]
        vus.extend(textes)
        assert rendu.pdf(vue).startswith(b"%PDF")
        rendu.png(vue)

    assert "Ɖɔkɔ ŊƲƐ" in vus and vue.numero in vus and "Non affilié" in vus
    assert adresses == [f"{settings.site_origine.rstrip('/')}/carte/{vue.code}"] * 2


def test_un_nom_trop_long_est_coupe() -> None:
    from app.cartes import rendu
    from app.certification.certificat_pdf import GRASSE

    texte, taille = rendu._ajuster("Prénom " * 20, GRASSE, 11, 50)

    assert texte.endswith("…") and taille < 11


def test_une_carte_non_valide_ne_se_telecharge_pas(
    client: TestClient, creer_encadreur: Callable[..., Utilisateur]
) -> None:
    from tests.espace_club import connecter

    creer_encadreur("prof")
    navigateur = connecter(client, "prof")

    assert navigateur.get(MOI).json()["cause"] == "sans_rattachement"
    assert navigateur.get(f"{MOI}.pdf").status_code == 409
    assert navigateur.get(f"{MOI}.png").status_code == 409
