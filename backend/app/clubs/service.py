"""Demande de création d'un club, sa lecture publique et la passation de présidence (spec 019).

Le club n'a pas de compte : il est rattaché à l'établissement de son demandeur, qui est un élève. Aucune
ligne de points n'est écrite ici. Les décisions (activation, refus, passation) vivent dans `verification.py`.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.articles.public import actualites_du_club
from app.clubs import activation
from app.clubs.models import (
    CLUB_VIVANT,
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
    ClubPodium,
    ClubPublic,
    ClubResume,
    MonClub,
    PassationApercu,
    PassationEntree,
)
from app.comptes.inscription import Refus, etablissement_rattache
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves import pseudonyme
from app.eleves.models import Eleve
from app.points import service as points
from app.referentiel.models import Dre, Etablissement, Iesg
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
    """Le club de l'établissement de l'élève (spec 033), quel que soit son statut, ou None s'il n'en a pas encore."""
    eleve = await db.get(Eleve, utilisateur.id) if utilisateur.role is Role.eleve else None
    if eleve is None:
        return None
    club = await db.scalar(
        select(Club).where(Club.etablissement_id == eleve.etablissement_id, Club.etat.in_(CLUB_VIVANT))
    )
    if club is None:
        return None
    return await _resume(db, club, utilisateur)


async def _axes(db: AsyncSession, club_id: UUID) -> list[str]:
    return list(await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club_id).order_by(ClubAxe.axe_code)))


async def _resume(db: AsyncSession, club: Club, utilisateur: Utilisateur) -> ClubResume:
    statut = activation.statut_effectif(club, activation.maintenant())
    return ClubResume(
        id=club.id,
        nom=club.nom,
        description=club.description,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        axes=await _axes(db, club.id),
        statut=statut.value,
        actif_le=club.actif_le,
        regularisation_jusquau=club.regularisation_jusquau if statut is EtatClub.en_regularisation else None,
        president=club.president_id == utilisateur.id,
        version=club.version,
    )


async def mon_club(db: AsyncSession, utilisateur: Utilisateur) -> MonClub:
    from app.clubs.adhesions import mon_adhesion

    club = await club_lie(db, utilisateur)
    passation = await _derniere_passation(db, club.id) if club is not None and club.president else None
    return MonClub(club=club, affiliation=await mon_adhesion(db, utilisateur), passation=passation)


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


# Lecture publique --------------------------------------------------------------------------------------------


def _statut_public(club: Club) -> str:
    return activation.statut_effectif(club, activation.maintenant()).value


async def _club_public(db: AsyncSession, club: Club) -> ClubPublic:
    return ClubPublic(
        id=club.id,
        nom=club.nom,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        axes=await _axes(db, club.id),
        statut=_statut_public(club),
        actif_le=club.actif_le,
    )


async def clubs_publics(db: AsyncSession) -> list[ClubPublic]:
    """Les clubs en service (actifs ou en régularisation), dans l'ordre de leur première activation."""
    clubs = (await db.scalars(select(Club).where(activation.en_service()).order_by(Club.actif_le, Club.nom))).all()
    return [await _club_public(db, club) for club in clubs]


async def podium(db: AsyncSession, limite: int = 3) -> list[ClubPodium]:
    """Les clubs en service qui ont le plus de points (au moins un), à égalité par nom (spec 021)."""
    lignes = (
        await db.execute(
            select(Club, Etablissement.nom, Dre.nom)
            .join(Etablissement, Etablissement.id == Club.etablissement_id)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(activation.en_service())
        )
    ).all()
    scores = await points.scores_des_clubs(db, [club.id for club, _, _ in lignes])
    classes = sorted(
        ((scores.get(club.id, 0), club, etablissement, dre) for club, etablissement, dre in lignes),
        key=lambda ligne: (-ligne[0], ligne[1].nom.casefold()),
    )
    retenus = [ligne for ligne in classes if ligne[0] > 0][:limite]
    return [
        ClubPodium(rang=rang, id=club.id, nom=club.nom, etablissement=etablissement, dre=dre, points=score)
        for rang, (score, club, etablissement, dre) in enumerate(retenus, start=1)
    ]


async def club_public(db: AsyncSession, club_id: UUID) -> ClubFiche | None:
    club = await db.scalar(select(Club).where(Club.id == club_id, Club.etat.in_(CLUB_VIVANT)))
    if club is None:
        return None
    return ClubFiche(
        id=club.id,
        nom=club.nom,
        description=club.description,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        axes=await _axes(db, club.id),
        statut=_statut_public(club),
        actif_le=club.actif_le,
        actualites=await actualites_du_club(db, club.id),
    )


async def club_par_etablissement(db: AsyncSession, etablissement_id: UUID) -> ClubPublic | None:
    club = await db.scalar(select(Club).where(Club.etat.in_(CLUB_VIVANT), Club.etablissement_id == etablissement_id))
    if club is None:
        return None
    return await _club_public(db, club)


# Passation --------------------------------------------------------------------------------------------------


async def club_preside(db: AsyncSession, utilisateur: Utilisateur) -> Club | None:
    """Le club dont cet utilisateur est le président, ou None. Un club suspendu garde son président, qui peut
    passer la main (spec 033)."""
    return await db.scalar(select(Club).where(Club.president_id == utilisateur.id, Club.etat.in_(CLUB_VIVANT)))


async def proposer_passation(
    db: AsyncSession, utilisateur: Utilisateur, entree: PassationEntree, adresse_ip: str
) -> PassationApercu:
    """Le président sortant désigne un successeur parmi les membres du club (spec 020). Si le club a un encadreur
    rattaché, celui-ci confirme d'abord le successeur (Q19) ; l'admin valide ou refuse ensuite."""
    club = await club_preside(db, utilisateur)
    if club is None:
        raise Refus("Tu n'es pas président d'un club.", 403)
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
        raise Refus("Tu n'es pas président d'un club.", 403)
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
