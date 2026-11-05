"""Rattachements des encadreurs (spec 020) : la demande de l'encadreur, la décision du président, les retraits.

Un encadreur actif (spec 018) peut demander à être rattaché à n'importe quel club actif. La demande passe par le
président, puis par un collaborateur (`membres_admin.py`). Au-delà du premier club, le rattachement est
« supplémentaire » : seule l'équipe nationale peut l'autoriser (Q16).
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs.adhesions import DEJA_TRAITEE, VIOLATION_UNICITE, club_actif, club_preside
from app.clubs.models import RATTACHEMENT_EN_COURS, Club, EtatRattachement, Rattachement
from app.clubs.schemas import DemandeRattachement, MesClubs, RattachementResume
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.encadreurs.models import Encadreur, EtatVerification
from app.referentiel.models import Etablissement

TERMINES_AFFICHES = 10


async def encadreur_actif(db: AsyncSession, utilisateur: Utilisateur) -> Encadreur:
    encadreur = await db.get(Encadreur, utilisateur.id) if utilisateur.role is Role.encadreur else None
    if encadreur is None or encadreur.etat is not EtatVerification.actif:
        raise Refus("Cet espace est réservé aux encadreurs dont le compte est actif.", 403)
    return encadreur


async def a_un_rattachement_actif(db: AsyncSession, encadreur_id: UUID, sauf_club: UUID | None = None) -> bool:
    requete = select(Rattachement.id).where(
        Rattachement.encadreur_id == encadreur_id, Rattachement.etat == EtatRattachement.actif
    )
    if sauf_club is not None:
        requete = requete.where(Rattachement.club_id != sauf_club)
    return await db.scalar(requete.limit(1)) is not None


async def resume(db: AsyncSession, rattachement: Rattachement) -> RattachementResume:
    club = await db.get(Club, rattachement.club_id)
    return RattachementResume(
        id=rattachement.id,
        club_id=rattachement.club_id,
        club_nom=club.nom if club else "",
        etat=rattachement.etat.value,
        supplementaire=rattachement.supplementaire,
        demande_le=rattachement.demande_le,
        motif_refus=rattachement.motif_refus,
        motif_retrait=rattachement.motif_retrait,
        version=rattachement.version,
    )


# Encadreur --------------------------------------------------------------------------------------------------


async def mes_clubs(db: AsyncSession, utilisateur: Utilisateur) -> MesClubs:
    await encadreur_actif(db, utilisateur)
    en_cours = (
        await db.scalars(
            select(Rattachement)
            .where(Rattachement.encadreur_id == utilisateur.id, Rattachement.etat.in_(RATTACHEMENT_EN_COURS))
            .order_by(Rattachement.demande_le)
        )
    ).all()
    termines = (
        await db.scalars(
            select(Rattachement)
            .where(Rattachement.encadreur_id == utilisateur.id, Rattachement.etat.not_in(RATTACHEMENT_EN_COURS))
            .order_by(Rattachement.modifie_le.desc())
            .limit(TERMINES_AFFICHES)
        )
    ).all()
    return MesClubs(rattachements=[await resume(db, r) for r in [*en_cours, *termines]])


async def demander(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, adresse_ip: str) -> RattachementResume:
    await encadreur_actif(db, utilisateur)
    club = await club_actif(db, club_id)
    en_cours = await db.scalar(
        select(Rattachement).where(
            Rattachement.encadreur_id == utilisateur.id,
            Rattachement.club_id == club.id,
            Rattachement.etat.in_(RATTACHEMENT_EN_COURS),
        )
    )
    if en_cours is not None:
        if en_cours.etat is EtatRattachement.actif:
            raise Refus("Tu es déjà rattaché à ce club.", 409)
        raise Refus("Ta demande est déjà en cours.", 409)

    rattachement = Rattachement(
        encadreur_id=utilisateur.id,
        club_id=club.id,
        supplementaire=await a_un_rattachement_actif(db, utilisateur.id),
    )
    db.add(rattachement)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Ta demande est déjà en cours.", 409) from None
    journaliser(
        db,
        "rattachement_demande",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        details={"supplementaire": rattachement.supplementaire},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, rattachement)


async def se_retirer(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, adresse_ip: str) -> RattachementResume:
    """L'encadreur annule sa demande ou quitte le club."""
    if utilisateur.role is not Role.encadreur:
        raise Refus("Cet espace est réservé aux encadreurs.", 403)
    rattachement = await db.scalar(
        select(Rattachement)
        .where(
            Rattachement.encadreur_id == utilisateur.id,
            Rattachement.club_id == club_id,
            Rattachement.etat.in_(RATTACHEMENT_EN_COURS),
        )
        .with_for_update()
    )
    if rattachement is None:
        raise Refus("Tu n'as ni demande ni rattachement dans ce club.", 404)
    etat_precedent = rattachement.etat
    rattachement.etat = EtatRattachement.retire
    rattachement.retire_le = datetime.now(UTC)
    rattachement.retire_par = utilisateur.id
    journaliser(
        db,
        "rattachement_retire",
        utilisateur,
        cible_type="rattachement",
        cible_id=rattachement.id,
        details={"club_id": str(club_id), "par": "encadreur", "etat_precedent": etat_precedent.value},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, rattachement)


# Président --------------------------------------------------------------------------------------------------


async def demandes_a_confirmer(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID) -> list[DemandeRattachement]:
    club = await club_preside(db, club_id, utilisateur)
    lignes = await db.execute(
        select(Rattachement, Utilisateur, Encadreur, Etablissement)
        .join(Utilisateur, Utilisateur.id == Rattachement.encadreur_id)
        .join(Encadreur, Encadreur.utilisateur_id == Rattachement.encadreur_id)
        .join(Etablissement, Etablissement.id == Encadreur.etablissement_id)
        .where(Rattachement.club_id == club.id, Rattachement.etat == EtatRattachement.en_attente_president)
        .order_by(Rattachement.demande_le)
    )
    return [
        DemandeRattachement(
            id=rattachement.id,
            prenom=compte.prenom,
            nom=compte.nom,
            fonction=encadreur.fonction.value,
            etablissement=etablissement.nom,
            demande_le=rattachement.demande_le,
            version=rattachement.version,
        )
        for rattachement, compte, encadreur, etablissement in lignes.all()
    ]


async def _a_traiter(
    db: AsyncSession, club: Club, rattachement_id: UUID, version: int, etat: EtatRattachement
) -> Rattachement:
    rattachement = await db.scalar(
        select(Rattachement)
        .where(Rattachement.id == rattachement_id, Rattachement.club_id == club.id)
        .with_for_update()
    )
    if rattachement is None:
        raise Refus("Cette demande est introuvable.", 404)
    if rattachement.etat is not etat or rattachement.version != version:
        raise Refus(DEJA_TRAITEE, 409)
    return rattachement


async def confirmer(
    db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, rattachement_id: UUID, version: int, adresse_ip: str
) -> RattachementResume:
    club = await club_preside(db, club_id, utilisateur)
    rattachement = await _a_traiter(db, club, rattachement_id, version, EtatRattachement.en_attente_president)
    rattachement.etat = EtatRattachement.en_attente_validation
    rattachement.confirme_le = datetime.now(UTC)
    rattachement.confirme_par = utilisateur.id
    journaliser(
        db,
        "rattachement_confirme",
        utilisateur,
        cible_type="rattachement",
        cible_id=rattachement.id,
        details={"club_id": str(club.id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, rattachement)


async def refuser(
    db: AsyncSession,
    utilisateur: Utilisateur,
    club_id: UUID,
    rattachement_id: UUID,
    motif: str,
    version: int,
    adresse_ip: str,
) -> RattachementResume:
    club = await club_preside(db, club_id, utilisateur)
    rattachement = await _a_traiter(db, club, rattachement_id, version, EtatRattachement.en_attente_president)
    rattachement.etat = EtatRattachement.refuse
    rattachement.motif_refus = motif
    rattachement.decide_le = datetime.now(UTC)
    rattachement.decide_par = utilisateur.id
    journaliser(
        db,
        "rattachement_refuse",
        utilisateur,
        cible_type="rattachement",
        cible_id=rattachement.id,
        details={"club_id": str(club.id), "par": "president", "motif": motif},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, rattachement)


async def retirer(
    db: AsyncSession,
    utilisateur: Utilisateur,
    club_id: UUID,
    rattachement_id: UUID,
    motif: str | None,
    version: int,
    adresse_ip: str,
) -> RattachementResume:
    club = await club_preside(db, club_id, utilisateur)
    rattachement = await _a_traiter(db, club, rattachement_id, version, EtatRattachement.actif)
    motif = " ".join(motif.split()) if motif else None
    rattachement.etat = EtatRattachement.retire
    rattachement.retire_le = datetime.now(UTC)
    rattachement.retire_par = utilisateur.id
    rattachement.motif_retrait = motif or None
    journaliser(
        db,
        "rattachement_retire",
        utilisateur,
        cible_type="rattachement",
        cible_id=rattachement.id,
        details={"club_id": str(club.id), "par": "president", "motif": motif},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, rattachement)


async def quitter_au_changement_detablissement(
    db: AsyncSession, utilisateur: Utilisateur, ancien_etablissement_id: UUID, adresse_ip: str
) -> None:
    """Avant qu'un encadreur change d'établissement : ses rattachements en cours au club de l'ancien
    établissement prennent fin. Ceux d'autres établissements (clubs supplémentaires) restent."""
    rattachements = (
        await db.scalars(
            select(Rattachement)
            .join(Club, Club.id == Rattachement.club_id)
            .where(
                Rattachement.encadreur_id == utilisateur.id,
                Rattachement.etat.in_(RATTACHEMENT_EN_COURS),
                Club.etablissement_id == ancien_etablissement_id,
            )
            .with_for_update(of=Rattachement)
        )
    ).all()
    for rattachement in rattachements:
        rattachement.etat = EtatRattachement.retire
        rattachement.retire_le = datetime.now(UTC)
        rattachement.retire_par = utilisateur.id
        rattachement.motif_retrait = "Changement d'établissement."
        journaliser(
            db,
            "rattachement_retire",
            utilisateur,
            cible_type="rattachement",
            cible_id=rattachement.id,
            details={"club_id": str(rattachement.club_id), "par": "changement_etablissement"},
            adresse_ip=adresse_ip,
        )
