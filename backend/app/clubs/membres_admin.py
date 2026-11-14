"""Confirmation des affiliations par les collaborateurs (spec 020, revue par la spec 033).

Une affiliation « à confirmer » peut l'être par un encadreur du club ou, à sa place, par l'équipe (décision 2 de la
spec 033). Un collaborateur national voit toutes les affiliations ; un collaborateur de DRE, celles des clubs de sa
DRE ; pour les autres, la réponse est celle d'une demande inexistante. Les rattachements des encadreurs sont
automatiques : il n'y a plus rien à valider.

Les décisions se prennent en lot : chaque demande est traitée dans son propre point de sauvegarde, et la
réponse dit lesquelles ont réussi et pourquoi les autres ont échoué.
"""

from collections.abc import Awaitable, Callable
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.clubs.adhesions import DEJA_TRAITEE, liste_membres
from app.clubs.affiliations import confirmer_affiliation, refuser_affiliation
from app.clubs.models import CLUB_VIVANT, Adhesion, Club, EtatAdhesion
from app.clubs.schemas import (
    AffiliationAValider,
    EchecLot,
    ElementLot,
    FileAffiliations,
    MembresDuClub,
    ResultatLot,
)
from app.comptes.inscription import Refus
from app.eleves.models import Eleve
from app.referentiel.models import Dre, Etablissement, Iesg

LIMITE_FILE = 200
INTROUVABLE = "Cette demande est introuvable."


def _dans_le_perimetre[T: Select](requete: T, acces: Acces) -> T:
    """Joint le club à sa DRE et filtre sur le périmètre du collaborateur."""
    requete = (
        requete.join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
    )
    if not acces.national:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    return requete


async def compter_a_valider(db: AsyncSession, acces: Acces) -> int:
    """Affiliations que ce collaborateur peut confirmer (tableau de bord)."""
    adhesions = await db.scalar(
        _dans_le_perimetre(
            select(func.count())
            .select_from(Adhesion)
            .join(Club, Club.id == Adhesion.club_id)
            .where(Adhesion.etat == EtatAdhesion.en_attente_validation),
            acces,
        )
    )
    return adhesions or 0


# Files ------------------------------------------------------------------------------------------------------


async def file_affiliations(db: AsyncSession, acces: Acces) -> FileAffiliations:
    requete = _dans_le_perimetre(
        select(Adhesion, Eleve, Club, Etablissement.nom, Dre.nom)
        .join(Eleve, Eleve.utilisateur_id == Adhesion.eleve_id)
        .join(Club, Club.id == Adhesion.club_id)
        .where(Adhesion.etat == EtatAdhesion.en_attente_validation),
        acces,
    )
    total = await db.scalar(select(func.count()).select_from(requete.with_only_columns(Adhesion.id).subquery()))
    lignes = (await db.execute(requete.order_by(Adhesion.demande_le, Adhesion.id).limit(LIMITE_FILE))).all()
    return FileAffiliations(
        total=total or 0,
        demandes=[
            AffiliationAValider(
                id=adhesion.id,
                pseudonyme=eleve.pseudonyme,
                classe=eleve.classe.value,
                club_id=club.id,
                club_nom=club.nom,
                etablissement=etablissement,
                dre=dre,
                demande_le=adhesion.demande_le,
                confirme_le=adhesion.confirme_le,
                version=adhesion.version,
            )
            for adhesion, eleve, club, etablissement, dre in lignes
        ],
    )


# Décisions --------------------------------------------------------------------------------------------------


async def _en_lot(
    db: AsyncSession, elements: list[ElementLot], decider: Callable[[ElementLot], Awaitable[None]]
) -> ResultatLot:
    reussies: list[UUID] = []
    echecs: list[EchecLot] = []
    for element in elements:
        try:
            async with db.begin_nested():
                await decider(element)
        except Refus as refus:
            echecs.append(EchecLot(id=element.id, message=str(refus)))
        else:
            reussies.append(element.id)
    await db.commit()
    return ResultatLot(reussies=reussies, echecs=echecs)


async def _adhesion_a_decider(db: AsyncSession, acces: Acces, element: ElementLot) -> tuple[Adhesion, Club, str]:
    ligne = (
        await db.execute(
            _dans_le_perimetre(
                select(Adhesion, Club, Dre.code)
                .join(Club, Club.id == Adhesion.club_id)
                .where(Adhesion.id == element.id),
                acces,
            ).with_for_update(of=Adhesion)
        )
    ).first()
    if ligne is None:
        raise Refus(INTROUVABLE, 404)
    adhesion, club, dre = ligne
    if adhesion.etat is not EtatAdhesion.en_attente_validation or adhesion.version != element.version:
        raise Refus(DEJA_TRAITEE, 409)
    return adhesion, club, dre


async def valider_affiliations(db: AsyncSession, acces: Acces, elements: list[ElementLot], ip: str) -> ResultatLot:
    async def valider(element: ElementLot) -> None:
        adhesion, club, dre = await _adhesion_a_decider(db, acces, element)
        await confirmer_affiliation(db, adhesion, club, acces.utilisateur, "collaborateur", ip, perimetre=dre)

    return await _en_lot(db, elements, valider)


async def refuser_affiliations(
    db: AsyncSession, acces: Acces, elements: list[ElementLot], motif: str, ip: str
) -> ResultatLot:
    async def refuser(element: ElementLot) -> None:
        adhesion, club, dre = await _adhesion_a_decider(db, acces, element)
        await refuser_affiliation(db, adhesion, club, acces.utilisateur, "collaborateur", motif, ip, perimetre=dre)

    return await _en_lot(db, elements, refuser)


async def membres_du_club(db: AsyncSession, acces: Acces, club_id: UUID) -> MembresDuClub:
    """La liste des membres pour un collaborateur habilité, dans son périmètre ; hors périmètre, 404."""
    club = await db.scalar(
        _dans_le_perimetre(select(Club).where(Club.id == club_id, Club.etat.in_(CLUB_VIVANT)), acces)
    )
    if club is None:
        raise Refus("Ce club est introuvable.", 404)
    return await liste_membres(db, club)
