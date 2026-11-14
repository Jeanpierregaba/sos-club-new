"""Affiliations des élèves (spec 020) : la demande de l'élève, la décision du président, les retraits.

Une demande va de l'élève au président (confirmer ou refuser), puis au collaborateur de la DRE
(`membres_admin.py`). Le président est membre de droit de son club : il ne peut ni se retirer, ni être retiré,
tant qu'il préside. Chaque transition est journalisée ; aucune ligne de points n'est écrite ici.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs.models import (
    ADHESION_EN_COURS,
    CLUB_VIVANT,
    PASSATION_EN_ATTENTE,
    Adhesion,
    Club,
    ClubPassation,
    EtatAdhesion,
    EtatPassation,
    Rattachement,
)
from app.clubs.requetes import encadreurs_actifs
from app.clubs.schemas import AdhesionResume, EncadreurDuClub, MembreClub, MembresDuClub
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur

VIOLATION_UNICITE = "23505"
DEJA_TRAITEE = "Cette demande a déjà été traitée : recharge la page."


async def club_vivant(db: AsyncSession, club_id: UUID) -> Club:
    """Le club, quel que soit son statut calculé (spec 033) ; 404 pour un ancien club refusé ou en attente."""
    club = await db.scalar(select(Club).where(Club.id == club_id, Club.etat.in_(CLUB_VIVANT)))
    if club is None:
        raise Refus("Ce club est introuvable.", 404)
    return club


async def resume(db: AsyncSession, adhesion: Adhesion) -> AdhesionResume:
    club = await db.get(Club, adhesion.club_id)
    return AdhesionResume(
        id=adhesion.id,
        club_id=adhesion.club_id,
        club_nom=club.nom if club else "",
        etat=adhesion.etat.value,
        demande_le=adhesion.demande_le,
        motif_refus=adhesion.motif_refus,
        motif_retrait=adhesion.motif_retrait,
        version=adhesion.version,
    )


async def mon_adhesion(db: AsyncSession, utilisateur: Utilisateur) -> AdhesionResume | None:
    """L'adhésion en cours de l'élève, sinon la dernière terminée : un motif de refus reste lisible."""
    adhesion = await db.scalar(
        select(Adhesion)
        .where(Adhesion.eleve_id == utilisateur.id)
        .order_by(Adhesion.etat.in_(ADHESION_EN_COURS).desc(), Adhesion.demande_le.desc())
        .limit(1)
    )
    return await resume(db, adhesion) if adhesion else None


async def annuler_passation_du_successeur(db: AsyncSession, adhesion: Adhesion) -> None:
    """Un élève qui quitte le club ne peut plus en devenir président : la passation qui le désignait est refusée,
    et le président sortant pourra en proposer une autre."""
    passation = await db.scalar(
        select(ClubPassation)
        .where(
            ClubPassation.club_id == adhesion.club_id,
            ClubPassation.successeur_id == adhesion.eleve_id,
            ClubPassation.etat.in_(PASSATION_EN_ATTENTE),
        )
        .with_for_update()
    )
    if passation is None:
        return
    passation.etat = EtatPassation.refusee
    passation.motif_refus = "Le successeur proposé a quitté le club."
    passation.decide_le = datetime.now(UTC)
    journaliser(
        db,
        "club_passation_annulee",
        cible_type="club",
        cible_id=adhesion.club_id,
        details={"passation_id": str(passation.id), "raison": "successeur_parti"},
    )


# Élève ------------------------------------------------------------------------------------------------------


# Président --------------------------------------------------------------------------------------------------


# Liste des membres et changement d'établissement -------------------------------------------------------------


async def liste_membres(db: AsyncSession, club: Club) -> MembresDuClub:
    """Les membres actifs du club, le président en tête, puis par pseudonyme ; et ses encadreurs rattachés."""
    lignes = await db.execute(
        select(Adhesion, Eleve.pseudonyme)
        .join(Eleve, Eleve.utilisateur_id == Adhesion.eleve_id)
        .where(Adhesion.club_id == club.id, Adhesion.etat == EtatAdhesion.active)
    )
    membres = [
        MembreClub(
            id=adhesion.id,
            pseudonyme=pseudo,
            depuis=adhesion.decide_le or adhesion.demande_le,
            president=adhesion.eleve_id == club.president_id,
            version=adhesion.version,
        )
        for adhesion, pseudo in lignes.all()
    ]
    encadreurs = await db.execute(
        select(Rattachement, Utilisateur, Encadreur)
        .join(Utilisateur, Utilisateur.id == Rattachement.encadreur_id)
        .join(Encadreur, Encadreur.utilisateur_id == Rattachement.encadreur_id)
        .where(Rattachement.id.in_(encadreurs_actifs(club.id).with_only_columns(Rattachement.id)))
        .order_by(Utilisateur.nom, Utilisateur.prenom)
    )
    return MembresDuClub(
        membres=sorted(membres, key=lambda m: (not m.president, m.pseudonyme.casefold())),
        encadreurs=[
            EncadreurDuClub(
                id=rattachement.id,
                prenom=compte.prenom,
                nom=compte.nom,
                fonction=encadreur.fonction.value,
                version=rattachement.version,
            )
            for rattachement, compte, encadreur in encadreurs.all()
        ],
    )


async def membres_du_club(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID) -> MembresDuClub:
    """La liste n'est visible que du président, des membres et des encadreurs rattachés ; pour tout autre, le
    club n'existe pas (404) : rien n'indique qu'il y aurait une liste à voir."""
    club = await club_vivant(db, club_id)
    membre = await db.scalar(
        select(Adhesion.id).where(
            Adhesion.club_id == club.id, Adhesion.eleve_id == utilisateur.id, Adhesion.etat == EtatAdhesion.active
        )
    )
    encadreur = await db.scalar(encadreurs_actifs(club.id).where(Rattachement.encadreur_id == utilisateur.id))
    if club.president_id != utilisateur.id and membre is None and encadreur is None:
        raise Refus("Ce club est introuvable.", 404)
    return await liste_membres(db, club)
