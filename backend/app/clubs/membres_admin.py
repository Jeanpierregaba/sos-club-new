"""Validation des affiliations et des rattachements par les collaborateurs (spec 020).

Un collaborateur national voit et décide toutes les demandes confirmées par un président. Un collaborateur de
DRE ne voit que celles des clubs de sa DRE ; pour les autres, la réponse est celle d'une demande inexistante.
Un rattachement « supplémentaire » (l'encadreur a déjà un club) n'est décidé que par l'équipe nationale (Q16) :
il est recalculé sous verrou au moment de la décision.

Les décisions se prennent en lot : chaque demande est traitée dans son propre point de sauvegarde, et la
réponse dit lesquelles ont réussi et pourquoi les autres ont échoué.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import ColumnElement, Select, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs.adhesions import DEJA_TRAITEE, liste_membres
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub, EtatRattachement, Rattachement
from app.clubs.rattachements import a_un_rattachement_actif
from app.clubs.schemas import (
    AffiliationAValider,
    EchecLot,
    ElementLot,
    FileAffiliations,
    FileRattachements,
    MembresDuClub,
    RattachementAValider,
    ResultatLot,
)
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification
from app.referentiel.models import Dre, Etablissement, Iesg

LIMITE_FILE = 200
INTROUVABLE = "Cette demande est introuvable."
NATIONAL_REQUIS = "Autorisation nationale requise : cet encadreur est déjà rattaché à un autre club."


def _supplementaire() -> ColumnElement[bool]:
    """Vrai si l'encadreur du rattachement a déjà un autre club actif, calculé à la lecture : la colonne
    `supplementaire` peut dater de la demande (le premier club a pu se terminer depuis)."""
    autre = aliased(Rattachement)
    return exists().where(
        autre.encadreur_id == Rattachement.encadreur_id,
        autre.etat == EtatRattachement.actif,
        autre.club_id != Rattachement.club_id,
    )


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
    """Affiliations et rattachements que ce collaborateur peut décider (tableau de bord)."""
    adhesions = await db.scalar(
        _dans_le_perimetre(
            select(func.count())
            .select_from(Adhesion)
            .join(Club, Club.id == Adhesion.club_id)
            .where(Adhesion.etat == EtatAdhesion.en_attente_validation),
            acces,
        )
    )
    rattachements = select(func.count()).select_from(Rattachement).join(Club, Club.id == Rattachement.club_id)
    rattachements = rattachements.where(Rattachement.etat == EtatRattachement.en_attente_validation)
    if not acces.national:
        rattachements = rattachements.where(~_supplementaire())
    return (adhesions or 0) + (await db.scalar(_dans_le_perimetre(rattachements, acces)) or 0)


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
    lignes = (await db.execute(requete.order_by(Adhesion.confirme_le, Adhesion.id).limit(LIMITE_FILE))).all()
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


async def file_rattachements(db: AsyncSession, acces: Acces) -> FileRattachements:
    EtablissementEncadreur = Etablissement.__table__.alias("etablissement_encadreur")
    requete = _dans_le_perimetre(
        select(
            Rattachement,
            Utilisateur,
            Encadreur,
            Club,
            Etablissement.nom,
            Dre.nom,
            EtablissementEncadreur.c.nom,
            _supplementaire().label("supplementaire"),
        )
        .join(Utilisateur, Utilisateur.id == Rattachement.encadreur_id)
        .join(Encadreur, Encadreur.utilisateur_id == Rattachement.encadreur_id)
        .join(EtablissementEncadreur, EtablissementEncadreur.c.id == Encadreur.etablissement_id)
        .join(Club, Club.id == Rattachement.club_id)
        .where(Rattachement.etat == EtatRattachement.en_attente_validation),
        acces,
    )
    total = await db.scalar(select(func.count()).select_from(requete.with_only_columns(Rattachement.id).subquery()))
    lignes = (await db.execute(requete.order_by(Rattachement.confirme_le, Rattachement.id).limit(LIMITE_FILE))).all()
    return FileRattachements(
        total=total or 0,
        demandes=[
            RattachementAValider(
                id=rattachement.id,
                prenom=compte.prenom,
                nom=compte.nom,
                fonction=encadreur.fonction.value,
                etablissement_encadreur=etablissement_encadreur,
                club_id=club.id,
                club_nom=club.nom,
                club_etablissement=etablissement,
                dre=dre,
                supplementaire=supplementaire,
                decidable=acces.national or not supplementaire,
                demande_le=rattachement.demande_le,
                confirme_le=rattachement.confirme_le,
                version=rattachement.version,
            )
            for rattachement, compte, encadreur, club, etablissement, dre, etablissement_encadreur, supplementaire in lignes
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
        if club.etat is not EtatClub.actif:
            raise Refus("Ce club n'est plus actif.", 409)
        eleve = await db.get(Eleve, adhesion.eleve_id)
        if eleve is None or eleve.etablissement_id != club.etablissement_id:
            raise Refus("Cet élève a changé d'établissement depuis sa demande.", 409)
        adhesion.etat = EtatAdhesion.active
        adhesion.decide_le = datetime.now(UTC)
        adhesion.decide_par = acces.utilisateur.id
        journaliser(
            db,
            "adhesion_validee",
            acces.utilisateur,
            cible_type="adhesion",
            cible_id=adhesion.id,
            perimetre=dre,
            details={"club_id": str(club.id)},
            adresse_ip=ip,
        )
        await db.flush()

    return await _en_lot(db, elements, valider)


async def refuser_affiliations(
    db: AsyncSession, acces: Acces, elements: list[ElementLot], motif: str, ip: str
) -> ResultatLot:
    async def refuser(element: ElementLot) -> None:
        adhesion, club, dre = await _adhesion_a_decider(db, acces, element)
        adhesion.etat = EtatAdhesion.refusee
        adhesion.motif_refus = motif
        adhesion.decide_le = datetime.now(UTC)
        adhesion.decide_par = acces.utilisateur.id
        journaliser(
            db,
            "adhesion_refusee",
            acces.utilisateur,
            cible_type="adhesion",
            cible_id=adhesion.id,
            perimetre=dre,
            details={"club_id": str(club.id), "par": "collaborateur", "motif": motif},
            adresse_ip=ip,
        )
        await db.flush()

    return await _en_lot(db, elements, refuser)


async def _par_encadreur(db: AsyncSession, elements: list[ElementLot]) -> list[ElementLot]:
    """Les rattachements d'un lot dans l'ordre de leurs encadreurs : deux lots simultanés verrouillent les
    profils d'encadreur dans le même ordre et ne peuvent pas s'attendre l'un l'autre (pas d'interblocage)."""
    lignes = await db.execute(
        select(Rattachement.id, Rattachement.encadreur_id).where(Rattachement.id.in_([e.id for e in elements]))
    )
    encadreurs = {id_: encadreur_id for id_, encadreur_id in lignes}
    return sorted(elements, key=lambda e: (str(encadreurs.get(e.id, "")), str(e.id)))


async def _rattachement_a_decider(
    db: AsyncSession, acces: Acces, element: ElementLot, *, valider: bool
) -> tuple[Rattachement, Club, str]:
    ligne = (
        await db.execute(
            _dans_le_perimetre(
                select(Rattachement, Club, Dre.code)
                .join(Club, Club.id == Rattachement.club_id)
                .where(Rattachement.id == element.id),
                acces,
            ).with_for_update(of=Rattachement)
        )
    ).first()
    if ligne is None:
        raise Refus(INTROUVABLE, 404)
    rattachement, club, dre = ligne
    if rattachement.etat is not EtatRattachement.en_attente_validation or rattachement.version != element.version:
        raise Refus(DEJA_TRAITEE, 409)
    # Le profil de l'encadreur, verrouillé : deux validations simultanées pour le même encadreur passent l'une
    # après l'autre, et la seconde voit le rattachement créé par la première.
    encadreur = await db.get(Encadreur, rattachement.encadreur_id, with_for_update=True)
    if valider and (encadreur is None or encadreur.etat is not EtatVerification.actif):
        raise Refus("Le compte de cet encadreur n'est plus actif.", 409)
    rattachement.supplementaire = await a_un_rattachement_actif(db, rattachement.encadreur_id, sauf_club=club.id)
    if rattachement.supplementaire and not acces.national:
        raise Refus(NATIONAL_REQUIS, 403)
    return rattachement, club, dre


async def valider_rattachements(db: AsyncSession, acces: Acces, elements: list[ElementLot], ip: str) -> ResultatLot:
    async def valider(element: ElementLot) -> None:
        rattachement, club, dre = await _rattachement_a_decider(db, acces, element, valider=True)
        if club.etat is not EtatClub.actif:
            raise Refus("Ce club n'est plus actif.", 409)
        rattachement.etat = EtatRattachement.actif
        rattachement.decide_le = datetime.now(UTC)
        rattachement.decide_par = acces.utilisateur.id
        journaliser(
            db,
            "rattachement_valide",
            acces.utilisateur,
            cible_type="rattachement",
            cible_id=rattachement.id,
            perimetre=dre,
            details={"club_id": str(club.id), "supplementaire": rattachement.supplementaire},
            adresse_ip=ip,
        )
        await db.flush()

    return await _en_lot(db, await _par_encadreur(db, elements), valider)


async def refuser_rattachements(
    db: AsyncSession, acces: Acces, elements: list[ElementLot], motif: str, ip: str
) -> ResultatLot:
    async def refuser(element: ElementLot) -> None:
        rattachement, club, dre = await _rattachement_a_decider(db, acces, element, valider=False)
        rattachement.etat = EtatRattachement.refuse
        rattachement.motif_refus = motif
        rattachement.decide_le = datetime.now(UTC)
        rattachement.decide_par = acces.utilisateur.id
        journaliser(
            db,
            "rattachement_refuse",
            acces.utilisateur,
            cible_type="rattachement",
            cible_id=rattachement.id,
            perimetre=dre,
            details={"club_id": str(club.id), "par": "collaborateur", "motif": motif},
            adresse_ip=ip,
        )
        await db.flush()

    return await _en_lot(db, await _par_encadreur(db, elements), refuser)


async def membres_du_club(db: AsyncSession, acces: Acces, club_id: UUID) -> MembresDuClub:
    """La liste des membres pour un collaborateur habilité, dans son périmètre ; hors périmètre, 404."""
    club = await db.scalar(
        _dans_le_perimetre(select(Club).where(Club.id == club_id, Club.etat == EtatClub.actif), acces)
    )
    if club is None:
        raise Refus("Ce club est introuvable.", 404)
    return await liste_membres(db, club)
