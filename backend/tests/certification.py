"""Aides des tests de la certification (spec 029) : un parcours publié, des places acquises sans jouer, des règles
de badges et la progression appelée directement."""

from collections.abc import Callable, Iterable
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification.models import BadgeObtenu, Certificat, PlaceReussie, ReglesBadges
from app.comptes.models import Utilisateur
from app.quiz import parametres
from app.quiz.models import EtatTentative, Quiz, TentativeQuiz
from tests.quiz import DEBUT, creer_quiz

CERTIFICATION = "/api/certification"
NUMERO = r"^GI-[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}$"


def creer_parcours(en_base: Callable[..., Any], places: Iterable[int] = range(1, 21), **champs: Any) -> dict[int, Quiz]:
    """Un quiz publié sur chaque place demandée."""
    return {place: creer_quiz(en_base, titre=f"Place {place}", place=place, **champs) for place in places}


def acquerir(en_base: Callable[..., Any], joueur: Utilisateur, quiz: dict[int, Quiz], places: Iterable[int]) -> None:
    """Des places réussies, comme si le joueur les avait jouées : une tentative terminée et réussie par place."""

    async def inserer(db: AsyncSession) -> None:
        p = await parametres.en_cours(db, "certification")
        for place in places:
            tentative = TentativeQuiz(
                quiz_id=quiz[place].id,
                joueur_id=joueur.id,
                parametres_id=p.id,
                etat=EtatTentative.terminee,
                jour=DEBUT.date(),
                commencee_le=DEBUT,
                derniere_activite=DEBUT,
                terminee_le=DEBUT,
                score=p.nb_questions,
                reussie=True,
            )
            db.add(tentative)
            await db.flush()
            db.add(
                PlaceReussie(
                    utilisateur_id=joueur.id, place=place, quiz_id=quiz[place].id, tentative_id=tentative.id,
                    reussie_le=DEBUT,
                )
            )  # fmt: skip

    en_base(inserer)


def regles(en_base: Callable[..., Any], noms: list[str], paliers: list[int]) -> None:
    """Une nouvelle version des règles des badges."""

    async def inserer(db: AsyncSession) -> None:
        derniere = await db.scalar(select(ReglesBadges.version).order_by(ReglesBadges.version.desc()).limit(1))
        db.add(ReglesBadges(version=(derniere or 0) + 1, noms=noms, paliers=paliers))

    en_base(inserer)


def mettre_a_jour(en_base: Callable[..., Any], joueur: Utilisateur) -> None:
    from app.certification import progression

    async def appeler(db: AsyncSession) -> None:
        compte = await db.get(Utilisateur, joueur.id)
        assert compte is not None
        await progression.mettre_a_jour(db, compte)

    en_base(appeler)


def badges(en_base: Callable[..., Any], joueur_id: UUID) -> list[BadgeObtenu]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(BadgeObtenu).where(BadgeObtenu.utilisateur_id == joueur_id).order_by(BadgeObtenu.rang)
            )
        ).all()
    )


def certificats(en_base: Callable[..., Any], joueur_id: UUID) -> list[Certificat]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(Certificat).where(Certificat.utilisateur_id == joueur_id).order_by(Certificat.delivre_le)
            )
        ).all()
    )


def places(en_base: Callable[..., Any], joueur_id: UUID) -> list[int]:
    return list(
        en_base(
            lambda db: db.scalars(
                select(PlaceReussie.place).where(PlaceReussie.utilisateur_id == joueur_id).order_by(PlaceReussie.place)
            )
        ).all()
    )
