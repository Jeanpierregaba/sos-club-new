"""Affiliations des élèves (spec 020) : la demande de l'élève, la décision du président, les retraits.

Une demande va de l'élève au président (confirmer ou refuser), puis au collaborateur de la DRE
(`membres_admin.py`). Le président est membre de droit de son club : il ne peut ni se retirer, ni être retiré,
tant qu'il préside. Chaque transition est journalisée ; aucune ligne de points n'est écrite ici.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs.models import (
    ADHESION_EN_COURS,
    PASSATION_EN_ATTENTE,
    Adhesion,
    Club,
    ClubPassation,
    EtatAdhesion,
    EtatClub,
    EtatPassation,
    Rattachement,
)
from app.clubs.requetes import encadreurs_actifs
from app.clubs.schemas import AdhesionResume, DemandeAdhesion, EncadreurDuClub, MembreClub, MembresDuClub
from app.clubs.service import eleve_de
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur

VIOLATION_UNICITE = "23505"
DEJA_TRAITEE = "Cette demande a déjà été traitée : recharge la page."


async def club_actif(db: AsyncSession, club_id: UUID) -> Club:
    club = await db.scalar(select(Club).where(Club.id == club_id, Club.etat == EtatClub.actif))
    if club is None:
        raise Refus("Ce club est introuvable.", 404)
    return club


async def club_preside(db: AsyncSession, club_id: UUID, utilisateur: Utilisateur) -> Club:
    """Le club actif demandé, si l'utilisateur en est le président ; sinon 403 (404 si le club n'existe pas)."""
    club = await club_actif(db, club_id)
    if club.president_id != utilisateur.id:
        raise Refus("Seul le président de ce club peut faire cela.", 403)
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


async def adhesion_president(db: AsyncSession, club: Club) -> None:
    """Le président devient membre de droit de son club (activation, passation). Rien s'il l'est déjà."""
    if club.president_id is None:
        return
    en_cours = await db.scalar(
        select(Adhesion).where(Adhesion.eleve_id == club.president_id, Adhesion.etat.in_(ADHESION_EN_COURS))
    )
    if en_cours is not None and en_cours.club_id == club.id:
        if en_cours.etat is not EtatAdhesion.active:
            en_cours.etat = EtatAdhesion.active
            en_cours.decide_le = datetime.now(UTC)
        return
    if en_cours is not None:
        # Une demande en cours ailleurs ne survit pas à la présidence d'un autre club.
        en_cours.etat = EtatAdhesion.retiree
        en_cours.retire_le = datetime.now(UTC)
        en_cours.motif_retrait = "Devenu président d'un autre club."
        await annuler_passation_du_successeur(db, en_cours)
        await db.flush()
    db.add(
        Adhesion(
            eleve_id=club.president_id,
            club_id=club.id,
            etat=EtatAdhesion.active,
            decide_le=datetime.now(UTC),
        )
    )


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


async def demander(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, adresse_ip: str) -> AdhesionResume:
    eleve = await eleve_de(db, utilisateur)
    club = await club_actif(db, club_id)
    if club.etablissement_id != eleve.etablissement_id:
        raise Refus("Tu ne peux rejoindre que le club de ton établissement.", 403)
    en_cours = await db.scalar(
        select(Adhesion).where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat.in_(ADHESION_EN_COURS))
    )
    if en_cours is not None:
        if en_cours.club_id != club.id:
            raise Refus("Tu as déjà une adhésion en cours dans un autre club.", 409)
        if en_cours.etat is EtatAdhesion.active:
            raise Refus("Tu es déjà membre de ce club.", 409)
        raise Refus("Ta demande est déjà en cours.", 409)

    adhesion = Adhesion(eleve_id=utilisateur.id, club_id=club.id)
    db.add(adhesion)
    try:
        await db.flush()
    except IntegrityError as erreur:
        # Deux demandes simultanées : la base n'en garde qu'une.
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Ta demande est déjà en cours.", 409) from None
    journaliser(db, "adhesion_demandee", utilisateur, cible_type="club", cible_id=club.id, adresse_ip=adresse_ip)
    await db.commit()
    return await resume(db, adhesion)


async def se_retirer(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, adresse_ip: str) -> AdhesionResume:
    """L'élève annule sa demande ou quitte le club. Le président, lui, doit d'abord passer la main."""
    await eleve_de(db, utilisateur)
    adhesion = await db.scalar(
        select(Adhesion)
        .where(
            Adhesion.eleve_id == utilisateur.id,
            Adhesion.club_id == club_id,
            Adhesion.etat.in_(ADHESION_EN_COURS),
        )
        .with_for_update()
    )
    if adhesion is None:
        raise Refus("Tu n'as ni demande ni adhésion dans ce club.", 404)
    club = await db.get(Club, club_id)
    if club is not None and club.president_id == utilisateur.id and club.etat is EtatClub.actif:
        raise Refus("Tu présides ce club : propose d'abord une passation à un autre membre.", 409)
    etat_precedent = adhesion.etat
    adhesion.etat = EtatAdhesion.retiree
    adhesion.retire_le = datetime.now(UTC)
    adhesion.retire_par = utilisateur.id
    journaliser(
        db,
        "adhesion_retiree",
        utilisateur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        details={"club_id": str(club_id), "par": "eleve", "etat_precedent": etat_precedent.value},
        adresse_ip=adresse_ip,
    )
    await annuler_passation_du_successeur(db, adhesion)
    await db.commit()
    return await resume(db, adhesion)


# Président --------------------------------------------------------------------------------------------------


async def demandes_a_confirmer(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID) -> list[DemandeAdhesion]:
    club = await club_preside(db, club_id, utilisateur)
    lignes = await db.execute(
        select(Adhesion, Eleve)
        .join(Eleve, Eleve.utilisateur_id == Adhesion.eleve_id)
        .where(Adhesion.club_id == club.id, Adhesion.etat == EtatAdhesion.en_attente_president)
        .order_by(Adhesion.demande_le)
    )
    return [
        DemandeAdhesion(
            id=adhesion.id,
            pseudonyme=eleve.pseudonyme,
            classe=eleve.classe.value,
            demande_le=adhesion.demande_le,
            version=adhesion.version,
        )
        for adhesion, eleve in lignes.all()
    ]


async def _a_traiter(db: AsyncSession, club: Club, adhesion_id: UUID, version: int, etat: EtatAdhesion) -> Adhesion:
    """L'adhésion du club, verrouillée, dans l'état attendu et à la version que le président a lue."""
    adhesion = await db.scalar(
        select(Adhesion).where(Adhesion.id == adhesion_id, Adhesion.club_id == club.id).with_for_update()
    )
    if adhesion is None:
        raise Refus("Cette demande est introuvable.", 404)
    if adhesion.etat is not etat or adhesion.version != version:
        raise Refus(DEJA_TRAITEE, 409)
    return adhesion


async def confirmer(
    db: AsyncSession, utilisateur: Utilisateur, club_id: UUID, adhesion_id: UUID, version: int, adresse_ip: str
) -> AdhesionResume:
    club = await club_preside(db, club_id, utilisateur)
    adhesion = await _a_traiter(db, club, adhesion_id, version, EtatAdhesion.en_attente_president)
    adhesion.etat = EtatAdhesion.en_attente_validation
    adhesion.confirme_le = datetime.now(UTC)
    adhesion.confirme_par = utilisateur.id
    journaliser(
        db,
        "adhesion_confirmee",
        utilisateur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        details={"club_id": str(club.id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, adhesion)


async def refuser(
    db: AsyncSession,
    utilisateur: Utilisateur,
    club_id: UUID,
    adhesion_id: UUID,
    motif: str,
    version: int,
    adresse_ip: str,
) -> AdhesionResume:
    club = await club_preside(db, club_id, utilisateur)
    adhesion = await _a_traiter(db, club, adhesion_id, version, EtatAdhesion.en_attente_president)
    adhesion.etat = EtatAdhesion.refusee
    adhesion.motif_refus = motif
    adhesion.decide_le = datetime.now(UTC)
    adhesion.decide_par = utilisateur.id
    journaliser(
        db,
        "adhesion_refusee",
        utilisateur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        details={"club_id": str(club.id), "par": "president", "motif": motif},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await resume(db, adhesion)


async def retirer(
    db: AsyncSession,
    utilisateur: Utilisateur,
    club_id: UUID,
    adhesion_id: UUID,
    motif: str | None,
    version: int,
    adresse_ip: str,
) -> AdhesionResume:
    club = await club_preside(db, club_id, utilisateur)
    adhesion = await _a_traiter(db, club, adhesion_id, version, EtatAdhesion.active)
    if adhesion.eleve_id == club.president_id:
        raise Refus("Le président ne peut pas être retiré : une passation d'abord.", 409)
    motif = " ".join(motif.split()) if motif else None
    adhesion.etat = EtatAdhesion.retiree
    adhesion.retire_le = datetime.now(UTC)
    adhesion.retire_par = utilisateur.id
    adhesion.motif_retrait = motif or None
    journaliser(
        db,
        "adhesion_retiree",
        utilisateur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        details={"club_id": str(club.id), "par": "president", "motif": motif},
        adresse_ip=adresse_ip,
    )
    await annuler_passation_du_successeur(db, adhesion)
    await db.commit()
    return await resume(db, adhesion)


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
    club = await club_actif(db, club_id)
    membre = await db.scalar(
        select(Adhesion.id).where(
            Adhesion.club_id == club.id, Adhesion.eleve_id == utilisateur.id, Adhesion.etat == EtatAdhesion.active
        )
    )
    encadreur = await db.scalar(encadreurs_actifs(club.id).where(Rattachement.encadreur_id == utilisateur.id))
    if club.president_id != utilisateur.id and membre is None and encadreur is None:
        raise Refus("Ce club est introuvable.", 404)
    return await liste_membres(db, club)


async def quitter_au_changement_detablissement(db: AsyncSession, utilisateur: Utilisateur, adresse_ip: str) -> None:
    """Avant qu'un élève change d'établissement : un président doit d'abord passer la main ; sinon son adhésion
    en cours prend fin. Appelé dans la transaction du changement de profil, qui la valide."""
    preside = await db.scalar(select(Club.id).where(Club.president_id == utilisateur.id, Club.etat == EtatClub.actif))
    if preside is not None:
        raise Refus("Tu présides le club de ton établissement : propose d'abord une passation à un autre membre.", 409)
    adhesion = await db.scalar(
        select(Adhesion)
        .where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat.in_(ADHESION_EN_COURS))
        .with_for_update()
    )
    if adhesion is None:
        return
    adhesion.etat = EtatAdhesion.retiree
    adhesion.retire_le = datetime.now(UTC)
    adhesion.retire_par = utilisateur.id
    adhesion.motif_retrait = "Changement d'établissement."
    journaliser(
        db,
        "adhesion_retiree",
        utilisateur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        details={"club_id": str(adhesion.club_id), "par": "changement_etablissement"},
        adresse_ip=adresse_ip,
    )
    await annuler_passation_du_successeur(db, adhesion)
