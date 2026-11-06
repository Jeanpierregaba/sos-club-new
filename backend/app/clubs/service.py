"""Demande de création d'un club, sa lecture publique et la passation de présidence (spec 019).

Le club n'a pas de compte : il est rattaché à l'établissement de son demandeur, qui est un élève. Aucune
ligne de points n'est écrite ici. Les décisions (activation, refus, passation) vivent dans `verification.py`.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs.models import (
    PASSATION_EN_ATTENTE,
    Adhesion,
    Club,
    ClubAxe,
    ClubPassation,
    EtatAdhesion,
    EtatClub,
    EtatPassation,
)
from app.clubs.requetes import encadreurs_actifs
from app.clubs.schemas import (
    ClubFiche,
    ClubPublic,
    ClubResume,
    DemandeClubEntree,
    MonClub,
    PassationApercu,
    PassationEntree,
)
from app.comptes.inscription import Refus, etablissement_rattache
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves import pseudonyme
from app.eleves.models import Eleve
from app.referentiel.models import Axe
from app.referentiel.normalisation import normaliser

logger = logging.getLogger(__name__)

VIOLATION_UNICITE = "23505"
MESSAGE_CONFLIT = "Ce club a été modifié entre-temps : recharge la page."


class PasUnEleve(Exception):
    pass


async def eleve_de(db: AsyncSession, utilisateur: Utilisateur) -> Eleve:
    if utilisateur.role is not Role.eleve:
        raise PasUnEleve
    eleve = await db.get(Eleve, utilisateur.id)
    if eleve is None:
        raise PasUnEleve
    return eleve


async def club_lie(db: AsyncSession, utilisateur: Utilisateur) -> ClubResume | None:
    """Le club dont cet élève est le demandeur ou le président, ou None.

    Un club refusé reste visible (avec son motif) tant qu'aucun club actif ou demande en attente ne le remplace :
    c'est ce qui permet au demandeur de lire le refus et de renvoyer sa demande.
    """
    club = await db.scalar(
        select(Club)
        .where(or_(Club.demandeur_id == utilisateur.id, Club.president_id == utilisateur.id))
        .order_by(
            case((Club.etat == EtatClub.actif, 0), (Club.etat == EtatClub.en_attente, 1), else_=2),
            Club.demande_le.desc(),
        )
        .limit(1)
    )
    if club is None:
        return None
    return await _resume(db, club, utilisateur)


async def _resume(db: AsyncSession, club: Club, utilisateur: Utilisateur) -> ClubResume:
    axes = (
        await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id).order_by(ClubAxe.axe_code))
    ).all()
    return ClubResume(
        id=club.id,
        nom=club.nom,
        description=club.description,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        axes=list(axes),
        etat=club.etat.value,
        president=club.president_id == utilisateur.id and club.etat is EtatClub.actif,
        motif_refus=club.motif_refus,
        version=club.version,
    )


async def mon_club(db: AsyncSession, utilisateur: Utilisateur) -> MonClub:
    club = await club_lie(db, utilisateur)
    passation = None
    if club is not None:
        passation = await _derniere_passation(db, club.id)
    return MonClub(club=club, passation=passation)


async def _derniere_passation(db: AsyncSession, club_id: UUID) -> PassationApercu | None:
    """La proposition en attente, sinon la dernière décidée : son motif de refus reste lisible par le président."""
    passation = await db.scalar(
        select(ClubPassation)
        .where(ClubPassation.club_id == club_id)
        .order_by(
            case((ClubPassation.etat.in_(PASSATION_EN_ATTENTE), 0), else_=1),
            ClubPassation.propose_le.desc(),
        )
        .limit(1)
    )
    if passation is None:
        return None
    return await _appercu_passation(db, passation)


def normaliser_nom(nom: str) -> str:
    return " ".join(normaliser(nom).replace("-", " ").split())


async def demarrer(
    db: AsyncSession, utilisateur: Utilisateur, entree: DemandeClubEntree, adresse_ip: str
) -> ClubResume:
    """Une demande de création : le demandeur vient de son établissement, jamais d'un champ libre."""
    eleve = await eleve_de(db, utilisateur)
    nom_normalise = normaliser_nom(entree.nom)
    if not 3 <= len(nom_normalise) <= 150:
        raise Refus("Le nom du club fait de 3 à 150 caractères.")
    if len(set(entree.axes)) != len(entree.axes):
        raise Refus("Un axe ne peut être choisi qu'une fois.")
    for axe_code in entree.axes:
        if await db.scalar(select(Axe).where(Axe.code == axe_code, Axe.actif)) is None:
            raise Refus(f"Axe inconnu : {axe_code}.")

    existant = await db.scalar(
        select(Club).where(Club.etablissement_id == eleve.etablissement_id, Club.nom_normalise == nom_normalise)
    )
    if existant is not None:
        if existant.etat is EtatClub.refuse:
            raise Refus(
                "Une demande portant ce nom a déjà été refusée pour ton établissement : renvoie-la depuis ton espace.",
                409,
            )
        raise Refus("Ce nom de club est déjà demandé pour cet établissement.", 409)
    if await db.scalar(
        select(Club).where(Club.etablissement_id == eleve.etablissement_id, Club.etat == EtatClub.actif)
    ):
        raise Refus("Ton établissement a déjà un club actif.", 409)
    if await db.scalar(select(Club).where(Club.demandeur_id == utilisateur.id, Club.etat == EtatClub.en_attente)):
        raise Refus("Tu as déjà une demande en attente.", 409)
    if await db.scalar(select(Club).where(Club.president_id == utilisateur.id, Club.etat == EtatClub.actif)):
        raise Refus("Tu es déjà président d'un club actif.", 409)

    club = Club(
        etablissement_id=eleve.etablissement_id,
        nom=" ".join(entree.nom.split()),
        nom_normalise=nom_normalise,
        description=(entree.description.strip() or None) if entree.description else None,
        demandeur_id=utilisateur.id,
        encadreurs_associes=[a.model_dump() for a in entree.encadreurs_associes],
    )
    db.add(club)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Ce nom de club est déjà demandé pour cet établissement.", 409) from None
    for axe_code in entree.axes:
        db.add(ClubAxe(club_id=club.id, axe_code=axe_code))
    journaliser(
        db,
        "demande_club",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        details={"nom": club.nom, "etablissement_id": str(club.etablissement_id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await _resume(db, club, utilisateur)


async def renvoyer(db: AsyncSession, utilisateur: Utilisateur, adresse_ip: str) -> ClubResume:
    """Une demande refusée, après correction, repasse en attente. Le motif précédent reste au journal."""
    club = await db.scalar(
        select(Club)
        .where(Club.demandeur_id == utilisateur.id, Club.etat == EtatClub.refuse)
        .order_by(Club.demande_le.desc())
        .limit(1)
        .with_for_update()
    )
    if club is None:
        raise Refus("Seule une demande refusée peut être renvoyée.", 409)
    if await db.scalar(select(Club).where(Club.etablissement_id == club.etablissement_id, Club.etat == EtatClub.actif)):
        raise Refus("Ton établissement a déjà un club actif : cette demande ne peut pas être renvoyée.", 409)
    motif_precedent = club.motif_refus
    club.etat = EtatClub.en_attente
    club.motif_refus = None
    club.demande_le = datetime.now(UTC)
    club.decide_le = None
    club.decide_par = None
    journaliser(
        db,
        "club_redemande",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        details={"motif_precedent": motif_precedent},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await _resume(db, club, utilisateur)


# Lecture publique --------------------------------------------------------------------------------------------


async def _club_public(db: AsyncSession, club: Club) -> ClubPublic:
    axes = (
        await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id).order_by(ClubAxe.axe_code))
    ).all()
    return ClubPublic(
        id=club.id,
        nom=club.nom,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        axes=list(axes),
        actif_le=club.actif_le,
    )


async def clubs_publics(db: AsyncSession) -> list[ClubPublic]:
    """Les clubs actifs seulement, dans l'ordre de leur activation."""
    clubs = (await db.scalars(select(Club).where(Club.etat == EtatClub.actif).order_by(Club.actif_le, Club.nom))).all()
    return [await _club_public(db, club) for club in clubs]


async def club_public(db: AsyncSession, club_id: UUID) -> ClubFiche | None:
    club = await db.scalar(select(Club).where(Club.id == club_id, Club.etat == EtatClub.actif))
    if club is None:
        return None
    axes = (
        await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id).order_by(ClubAxe.axe_code))
    ).all()
    return ClubFiche(
        id=club.id,
        nom=club.nom,
        description=club.description,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        axes=list(axes),
        actif_le=club.actif_le,
    )


async def club_par_etablissement(db: AsyncSession, etablissement_id: UUID) -> ClubPublic | None:
    club = await db.scalar(select(Club).where(Club.etat == EtatClub.actif, Club.etablissement_id == etablissement_id))
    if club is None:
        return None
    return await _club_public(db, club)


# Passation --------------------------------------------------------------------------------------------------


async def club_preside(db: AsyncSession, utilisateur: Utilisateur) -> Club | None:
    """Le club actif dont cet utilisateur est le président, ou None."""
    return await db.scalar(select(Club).where(Club.president_id == utilisateur.id, Club.etat == EtatClub.actif))


async def proposer_passation(
    db: AsyncSession, utilisateur: Utilisateur, entree: PassationEntree, adresse_ip: str
) -> PassationApercu:
    """Le président sortant désigne un successeur parmi les membres du club (spec 020). Si le club a un encadreur
    rattaché, celui-ci confirme d'abord le successeur (Q19) ; l'admin valide ou refuse ensuite."""
    club = await club_preside(db, utilisateur)
    if club is None:
        raise Refus("Tu n'es pas président d'un club actif.", 403)
    if club.version != entree.version:
        raise Refus(MESSAGE_CONFLIT, 409)
    cle = pseudonyme.cle(entree.pseudonyme)
    eleve_succ = await db.scalar(
        select(Eleve).where(Eleve.pseudonyme_normalise == cle, Eleve.etablissement_id == club.etablissement_id)
    )
    if eleve_succ is None:
        raise Refus("Ce pseudonyme n'existe pas dans ton établissement.")
    if eleve_succ.utilisateur_id == utilisateur.id:
        raise Refus("Tu ne peux pas te proposer toi-même.")
    successeur = await db.get(Utilisateur, eleve_succ.utilisateur_id)
    if successeur.statut is not StatutCompte.actif:
        raise Refus("Cet élève n'est pas actif. Choisis un élève dont le compte est actif.", 409)
    membre = await db.scalar(
        select(Adhesion.id).where(
            Adhesion.club_id == club.id,
            Adhesion.eleve_id == eleve_succ.utilisateur_id,
            Adhesion.etat == EtatAdhesion.active,
        )
    )
    if membre is None:
        raise Refus("Cet élève n'est pas membre de ton club : il doit d'abord le rejoindre.", 409)
    if await db.scalar(
        select(ClubPassation).where(ClubPassation.club_id == club.id, ClubPassation.etat.in_(PASSATION_EN_ATTENTE))
    ):
        raise Refus("Une passation est déjà en attente pour ce club.", 409)
    # Verrou du club : un rattachement qui se termine en même temps ne laisse pas la passation attendre un
    # encadreur qui n'existe plus (`rattachements.liberer_passation` prend le même verrou).
    await db.execute(select(Club.id).where(Club.id == club.id).with_for_update())
    encadre = await db.scalar(encadreurs_actifs(club.id).limit(1))
    passation = ClubPassation(
        club_id=club.id,
        successeur_id=eleve_succ.utilisateur_id,
        propose_par=utilisateur.id,
        etat=EtatPassation.en_attente_encadreur if encadre else EtatPassation.en_attente,
    )
    db.add(passation)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Une passation est déjà en attente pour ce club.", 409) from None
    journaliser(
        db,
        "club_passation_proposee",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        details={"successeur_pseudonyme": eleve_succ.pseudonyme, "passation_id": str(passation.id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await _appercu_passation(db, passation)


async def annuler_passation(db: AsyncSession, utilisateur: Utilisateur, adresse_ip: str) -> PassationApercu:
    """Le président sortant annule sa propre proposition avant sa décision."""
    club = await club_preside(db, utilisateur)
    if club is None:
        raise Refus("Tu n'es pas président d'un club actif.", 403)
    passation = await db.scalar(
        select(ClubPassation)
        .where(
            ClubPassation.club_id == club.id,
            ClubPassation.propose_par == utilisateur.id,
            ClubPassation.etat.in_(PASSATION_EN_ATTENTE),
        )
        .with_for_update()
    )
    if passation is None:
        raise Refus("Aucune passation en attente à annuler.", 409)
    passation.etat = EtatPassation.refusee
    passation.motif_refus = "Annulée par le président."
    passation.decide_le = datetime.now(UTC)
    passation.decide_par = utilisateur.id
    journaliser(
        db,
        "club_passation_annulee",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        details={"passation_id": str(passation.id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await _appercu_passation(db, passation)


async def _appercu_passation(db: AsyncSession, passation: ClubPassation) -> PassationApercu:
    successeur = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == passation.successeur_id))
    return PassationApercu(
        id=passation.id,
        etat=passation.etat.value,
        successeur_pseudonyme=successeur or "",
        propose_le=passation.propose_le,
        confirmee_le=passation.confirmee_le,
        decide_le=passation.decide_le,
        motif_refus=passation.motif_refus,
        version=passation.version,
    )
