import asyncio
import os
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import make_url, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

# Toujours cette base locale, jamais celle de l'environnement : les tests effacent toutes ses données.
URL_BASE_TEST = "postgresql+asyncpg://sosclub@127.0.0.1:5435/sosclub_test"
os.environ["DATABASE_URL"] = URL_BASE_TEST

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.comptes.models import Role, Utilisateur
from app.comptes.motdepasse import hacher
from app.db import Base
from app.eleves import pseudonyme
from app.eleves.models import Classe, Eleve
from app.main import app
from app.points import bareme
from app.referentiel.chargement import charger
from app.referentiel.models import Dre, Etablissement, Iesg

MOT_DE_PASSE = "mot-de-passe-de-test"
# NullPool : chaque appel ouvre sa connexion, car asyncio.run crée une nouvelle boucle à chaque fois.
moteur_test = create_async_engine(URL_BASE_TEST, poolclass=NullPool)


async def _recreer_base() -> None:
    url = make_url(URL_BASE_TEST)
    moteur_admin = create_async_engine(url.set(database="sosclub"), isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with moteur_admin.connect() as connexion:
        await connexion.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        await connexion.execute(text(f'CREATE DATABASE "{url.database}"'))
    await moteur_admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def base_de_test() -> None:
    asyncio.run(_recreer_base())
    configuration = Config(Path(__file__).resolve().parents[1] / "alembic.ini")
    # L'aller et le retour : une migration qui ne sait pas revenir en arrière fait échouer les tests.
    command.upgrade(configuration, "head")
    command.downgrade(configuration, "base")
    command.upgrade(configuration, "head")


async def _vider_tables() -> None:
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with moteur_test.begin() as connexion:
        await connexion.execute(text(f"TRUNCATE {tables} CASCADE"))
        # Les DRE, IESG et axes de l'annuaire : les périmètres des collaborateurs en ont besoin (spec 016).
        await connexion.run_sync(lambda c: charger(c, etablissements=False))
        # Le barème initial (spec 017) : chaque gain de points y lit son montant.
        await connexion.run_sync(bareme.charger)


async def _charger_annuaire() -> None:
    async with moteur_test.begin() as connexion:
        await connexion.run_sync(charger)


@pytest.fixture(autouse=True)
def tables_vides() -> None:
    asyncio.run(_vider_tables())


@pytest.fixture
def annuaire() -> None:
    """Charge en plus les établissements de l'annuaire (838 lignes)."""
    asyncio.run(_charger_annuaire())


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def en_base() -> Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any]:
    """Exécute une fonction asynchrone sur la base de test, dans une transaction validée."""

    def executer(fonction: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
        async def _executer() -> Any:
            async with AsyncSession(moteur_test, expire_on_commit=False) as db:
                resultat = await fonction(db)
                await db.commit()
                return resultat

        return asyncio.run(_executer())

    return executer


@pytest.fixture
def creer_utilisateur(en_base: Callable[..., Any]) -> Callable[..., Utilisateur]:
    def creer(
        identifiant: str = "jeank",
        role: Role = Role.eleve,
        email: str | None = None,
        mot_de_passe: str = MOT_DE_PASSE,
        **champs: Any,
    ) -> Utilisateur:
        async def inserer(db: AsyncSession) -> Utilisateur:
            utilisateur = Utilisateur(
                identifiant=identifiant,
                role=role,
                email=email,
                prenom=champs.pop("prenom", "Jean"),
                nom=champs.pop("nom", "Kodjo"),
                mot_de_passe_hash=await hacher(mot_de_passe),
                **champs,
            )
            db.add(utilisateur)
            return utilisateur

        return en_base(inserer)

    return creer


def etablissement_de(en_base: Callable[..., Any], dre: str) -> Any:
    """Un établissement de la DRE demandée, pris dans l'annuaire chargé."""
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
def creer_eleve(
    annuaire: None,
    en_base: Callable[..., Any],
    creer_utilisateur: Callable[..., Utilisateur],
) -> Callable[..., Utilisateur]:
    """Un élève avec son profil (spec 017) dans un établissement de la DRE demandée."""

    def creer(
        identifiant: str = "eleve1",
        affiche: str = "Ama du Golfe",
        dre: str = "grand-lome",
        classe: Classe = Classe.seconde,
        etablissement_id: Any = None,
    ) -> Utilisateur:
        utilisateur = creer_utilisateur(identifiant, Role.eleve)
        lieu = etablissement_id or etablissement_de(en_base, dre)

        async def inserer(db: AsyncSession) -> None:
            db.add(
                Eleve(
                    utilisateur_id=utilisateur.id,
                    pseudonyme=affiche,
                    pseudonyme_normalise=pseudonyme.cle(affiche),
                    classe=classe,
                    etablissement_id=lieu,
                    charte_version="test",
                )
            )

        en_base(inserer)
        return utilisateur

    return creer


# Espace administrateur (spec 015) ----------------------------------------------------------------------------

SECRET_TOTP = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"


@pytest.fixture
def creer_collaborateur(
    en_base: Callable[..., Any], creer_utilisateur: Callable[..., Utilisateur]
) -> Callable[..., Any]:
    """Un compte admin et son profil de collaborateur. `double_auth=True` active une double authentification
    dont le secret est SECRET_TOTP."""
    from app.admin.models import Collaborateur, DoubleAuth, Permission
    from app.config import settings

    def creer(
        identifiant: str = "chef",
        email: str | None = None,
        *,
        super_admin: bool = False,
        droits: set[tuple[str, str]] | None = None,
        perimetre_dre: str | None = None,
        fin_acces: Any = None,
        double_auth: bool = False,
    ) -> Utilisateur:
        utilisateur = creer_utilisateur(identifiant, Role.admin, email=email or f"{identifiant}@aimes.tg")

        async def inserer(db: AsyncSession) -> None:
            collaborateur = Collaborateur(
                utilisateur_id=utilisateur.id,
                email=utilisateur.email,
                prenom=utilisateur.prenom,
                nom=utilisateur.nom,
                super_admin=super_admin,
                perimetre_dre=perimetre_dre,
                fin_acces=fin_acces,
            )
            db.add(collaborateur)
            await db.flush()
            for module, action in droits or set():
                db.add(Permission(collaborateur_id=collaborateur.id, module=module, action=action))
            if double_auth:
                from datetime import UTC, datetime

                db.add(
                    DoubleAuth(
                        utilisateur_id=utilisateur.id,
                        secret_chiffre=settings.fernet().encrypt(SECRET_TOTP.encode()).decode(),
                        active_le=datetime.now(UTC),
                    )
                )

        en_base(inserer)
        return utilisateur

    return creer


def code_totp(decalage: int = 0) -> str:
    import time

    import pyotp

    return pyotp.TOTP(SECRET_TOTP).at(time.time() + decalage * 30)


def connecter_admin(client: TestClient, identifiant: str = "chef") -> Any:
    """Connexion complète : mot de passe, puis code si la double authentification est active."""
    reponse = client.post("/api/comptes/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    corps = reponse.json()
    if reponse.status_code == 200 and corps.get("etape") == "code":
        reponse = client.post("/api/comptes/connexion/code", json={"jeton": corps["jeton"], "code": code_totp()})
    return reponse


class Navigateur:
    """Un second navigateur : le même client de test (la même boucle d'événements que la base), avec ses propres
    cookies. Deux TestClient distincts se partageraient mal les connexions de l'API."""

    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.cookies: list[Any] = []

    def request(self, methode: str, url: str, **options: Any) -> Any:
        pot = self.client.cookies.jar
        ceux_du_client = list(pot)
        pot.clear()
        for cookie in self.cookies:
            pot.set_cookie(cookie)
        try:
            return self.client.request(methode, url, **options)
        finally:
            self.cookies = list(pot)
            pot.clear()
            for cookie in ceux_du_client:
                pot.set_cookie(cookie)

    def get(self, url: str, **options: Any) -> Any:
        return self.request("GET", url, **options)

    def post(self, url: str, **options: Any) -> Any:
        return self.request("POST", url, **options)

    def put(self, url: str, **options: Any) -> Any:
        return self.request("PUT", url, **options)


VERIFICATION_CLUBS = {
    ("tableau_de_bord", "consulter"),
    ("clubs", "consulter"),
    ("clubs", "approuver"),
}


@pytest.fixture
def verificateur_clubs(client: TestClient, creer_collaborateur: Callable[..., Any]) -> TestClient:
    """Un collaborateur national qui peut lire et décider les clubs, double authentification faite."""
    creer_collaborateur("verif.clubs", droits=VERIFICATION_CLUBS, double_auth=True)
    connecter_admin(client, "verif.clubs")
    return client


# Clubs, affiliations et rattachements (spec 020) --------------------------------------------------------------


@pytest.fixture
def creer_club(en_base: Callable[..., Any]) -> Callable[..., Any]:
    """Un club actif présidé par `president`, dans l'établissement de ce dernier, avec l'adhésion active du
    président (membre de droit, spec 020). `etat` permet un club en attente ou refusé, sans adhésion."""
    from datetime import UTC, datetime

    from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub

    def creer(president: Utilisateur, nom: str = "Club Santé Test", etat: EtatClub = EtatClub.actif) -> Club:
        async def inserer(db: AsyncSession) -> Club:
            eleve = await db.get(Eleve, president.id)
            assert eleve is not None, "le président doit être un élève"
            actif = etat is EtatClub.actif
            club = Club(
                etablissement_id=eleve.etablissement_id,
                nom=nom,
                nom_normalise=nom.lower(),
                demandeur_id=president.id,
                president_id=president.id if actif else None,
                etat=etat,
                motif_refus="Refus de test." if etat is EtatClub.refuse else None,
                actif_le=datetime.now(UTC) if actif else None,
                encadreurs_associes=[],
            )
            db.add(club)
            await db.flush()
            if actif:
                db.add(Adhesion(eleve_id=president.id, club_id=club.id, etat=EtatAdhesion.active))
            return club

        return en_base(inserer)

    return creer


@pytest.fixture
def creer_encadreur(
    annuaire: None, en_base: Callable[..., Any], creer_utilisateur: Callable[..., Utilisateur]
) -> Callable[..., Utilisateur]:
    """Un encadreur (spec 018), actif par défaut, dans un établissement de la DRE demandée."""
    from app.encadreurs.models import Encadreur, EtatVerification, Fonction

    def creer(
        identifiant: str = "encadreur1",
        dre: str = "grand-lome",
        etablissement_id: Any = None,
        etat: EtatVerification = EtatVerification.actif,
    ) -> Utilisateur:
        utilisateur = creer_utilisateur(identifiant, Role.encadreur, email=f"{identifiant}@ecole.tg")
        lieu = etablissement_id or etablissement_de(en_base, dre)

        async def inserer(db: AsyncSession) -> None:
            db.add(
                Encadreur(
                    utilisateur_id=utilisateur.id,
                    etablissement_id=lieu,
                    fonction=Fonction.enseignant,
                    etat=etat,
                    charte_version="test",
                )
            )

        en_base(inserer)
        return utilisateur

    return creer
