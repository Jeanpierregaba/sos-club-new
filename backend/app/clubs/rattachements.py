"""Rattachements des encadreurs (spec 020) : la demande de l'encadreur, la décision du président, les retraits.

Un encadreur actif (spec 018) peut demander à être rattaché à n'importe quel club actif. La demande passe par le
président, puis par un collaborateur (`membres_admin.py`). Au-delà du premier club, le rattachement est
« supplémentaire » : seule l'équipe nationale peut l'autoriser (Q16).
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs.models import (
    Club,
    ClubPassation,
    EtatPassation,
    EtatRattachement,
    Rattachement,
)
from app.clubs.requetes import encadreurs_actifs
from app.clubs.schemas import PassationAConfirmer
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification


async def encadreur_actif(db: AsyncSession, utilisateur: Utilisateur) -> Encadreur:
    encadreur = await db.get(Encadreur, utilisateur.id) if utilisateur.role is Role.encadreur else None
    if encadreur is None or encadreur.etat is not EtatVerification.actif:
        raise Refus("Cet espace est réservé aux encadreurs dont le compte est actif.", 403)
    return encadreur


# Encadreur --------------------------------------------------------------------------------------------------


# Président --------------------------------------------------------------------------------------------------


# Confirmation du président par un encadreur rattaché (Q19) ----------------------------------------------------


async def passations_a_confirmer(db: AsyncSession, utilisateur: Utilisateur) -> list[PassationAConfirmer]:
    lignes = await db.execute(
        select(ClubPassation, Club)
        .join(Club, Club.id == ClubPassation.club_id)
        .join(Rattachement, Rattachement.club_id == Club.id)
        .where(
            Rattachement.encadreur_id == utilisateur.id,
            Rattachement.etat == EtatRattachement.actif,
            ClubPassation.etat == EtatPassation.en_attente_encadreur,
        )
        .order_by(ClubPassation.propose_le)
    )
    resultat = []
    for passation, club in lignes.all():
        successeur = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == passation.successeur_id))
        sortant = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == club.president_id))
        resultat.append(
            PassationAConfirmer(
                id=passation.id,
                club_id=club.id,
                club_nom=club.nom,
                successeur_pseudonyme=successeur or "",
                president_sortant_pseudonyme=sortant or "",
                propose_le=passation.propose_le,
                version=passation.version,
            )
        )
    return resultat


async def _passation_a_confirmer(
    db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, version: int
) -> ClubPassation:
    """La passation du club, verrouillée, si l'utilisateur est un encadreur actif rattaché à ce club."""
    await encadreur_actif(db, utilisateur)
    rattache = await db.scalar(
        select(Rattachement.id).where(
            Rattachement.encadreur_id == utilisateur.id,
            Rattachement.club_id == club_id,
            Rattachement.etat == EtatRattachement.actif,
        )
    )
    if rattache is None:
        raise Refus("Seul un encadreur rattaché à ce club peut confirmer son président.", 403)
    passation = await db.scalar(
        select(ClubPassation)
        .where(ClubPassation.club_id == club_id, ClubPassation.etat == EtatPassation.en_attente_encadreur)
        .with_for_update()
    )
    if passation is None:
        raise Refus("Aucune passation n'attend ta confirmation dans ce club.", 404)
    if passation.version != version:
        raise Refus("Cette passation a changé depuis que tu l'as ouverte : recharge la page.", 409)
    return passation


async def confirmer_passation(
    db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, version: int, adresse_ip: str
) -> PassationAConfirmer:
    passation = await _passation_a_confirmer(db, utilisateur, club_id, version)
    passation.etat = EtatPassation.en_attente
    passation.confirmee_le = datetime.now(UTC)
    passation.confirmee_par = utilisateur.id
    journaliser(
        db,
        "club_passation_confirmee",
        utilisateur,
        cible_type="club",
        cible_id=club_id,
        details={"passation_id": str(passation.id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await _apercu_a_confirmer(db, passation)


async def refuser_passation(
    db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, motif: str, version: int, adresse_ip: str
) -> PassationAConfirmer:
    passation = await _passation_a_confirmer(db, utilisateur, club_id, version)
    passation.etat = EtatPassation.refusee
    passation.motif_refus = motif
    passation.decide_le = datetime.now(UTC)
    passation.decide_par = utilisateur.id
    journaliser(
        db,
        "club_passation_refusee",
        utilisateur,
        cible_type="club",
        cible_id=club_id,
        details={"passation_id": str(passation.id), "par": "encadreur", "motif": motif},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await _apercu_a_confirmer(db, passation)


async def _apercu_a_confirmer(db: AsyncSession, passation: ClubPassation) -> PassationAConfirmer:
    club = await db.get(Club, passation.club_id)
    successeur = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == passation.successeur_id))
    sortant = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == club.president_id))
    return PassationAConfirmer(
        id=passation.id,
        club_id=club.id,
        club_nom=club.nom,
        successeur_pseudonyme=successeur or "",
        president_sortant_pseudonyme=sortant or "",
        propose_le=passation.propose_le,
        version=passation.version,
    )


async def liberer_passation(db: AsyncSession, club_id: UUID) -> None:
    """Quand le club n'a plus d'encadreur actif rattaché (retrait, départ, suspension), une passation qui
    l'attendait passe directement à l'admin."""
    await db.flush()
    await db.execute(select(Club.id).where(Club.id == club_id).with_for_update())
    if await db.scalar(encadreurs_actifs(club_id).limit(1)):
        return
    passation = await db.scalar(
        select(ClubPassation)
        .where(ClubPassation.club_id == club_id, ClubPassation.etat == EtatPassation.en_attente_encadreur)
        .with_for_update()
    )
    if passation is None:
        return
    passation.etat = EtatPassation.en_attente
    journaliser(
        db,
        "club_passation_sans_encadreur",
        cible_type="club",
        cible_id=club_id,
        details={"passation_id": str(passation.id)},
    )
