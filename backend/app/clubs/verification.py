"""Vérification des clubs par l'espace admin (spec 019) : file, activation, refus, passations.

Un collaborateur national voit toutes les demandes. Un collaborateur de DRE ne voit et ne décide que celles
des établissements de sa DRE : pour les autres, il reçoit la même réponse que pour une demande inexistante.
Le périmètre se lit sur l'établissement actuel, sous verrou, au moment de la décision. Le club n'a pas de
compte : la gestion passe par le lien `president_id`.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs.adhesions import adhesion_president
from app.clubs.membres_admin import compter_a_valider
from app.clubs.models import Club, ClubAxe, ClubPassation, EtatClub, EtatPassation
from app.clubs.schemas import DemandeClub, EncadreurAssocie, FileClubs, FilePassations, Passation
from app.comptes.inscription import Refus
from app.comptes.models import StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.referentiel.models import Dre, Etablissement, Iesg, StatutEtablissement
from app.referentiel.schemas import EtablissementRattache

LIMITE_FILE = 200


class Introuvable(Exception):
    pass


def _requete(acces: Acces) -> Select[tuple[Club, Utilisateur, Eleve, Etablissement, Iesg, Dre]]:
    requete = (
        select(Club, Utilisateur, Eleve, Etablissement, Iesg, Dre)
        .join(Utilisateur, Utilisateur.id == Club.demandeur_id)
        .join(Eleve, Eleve.utilisateur_id == Utilisateur.id)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
    )
    if not acces.national:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    return requete


def _etablissement(etablissement: Etablissement, iesg: Iesg, dre: Dre) -> EtablissementRattache:
    return EtablissementRattache(
        id=etablissement.id,
        nom=etablissement.nom,
        statut=etablissement.statut,
        iesg=iesg.nom,
        dre_code=dre.code,
        dre=dre.nom,
    )


async def _demande(
    db: AsyncSession,
    club: Club,
    _utilisateur: Utilisateur,
    eleve: Eleve,
    etablissement: Etablissement,
    iesg: Iesg,
    dre: Dre,
) -> DemandeClub:
    axes = (
        await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id).order_by(ClubAxe.axe_code))
    ).all()
    return DemandeClub(
        id=club.id,
        nom=club.nom,
        description=club.description,
        axes=list(axes),
        demandeur_pseudonyme=eleve.pseudonyme,
        etablissement=_etablissement(etablissement, iesg, dre),
        encadreurs_associes=[EncadreurAssocie(**a) for a in (club.encadreurs_associes or [])],
        etat=club.etat,
        demande_le=club.demande_le,
        decide_le=club.decide_le,
        motif_refus=club.motif_refus,
        version=club.version,
    )


async def file_attente(db: AsyncSession, acces: Acces, etat: EtatClub, page: int = 1, par_page: int = 50) -> FileClubs:
    """Demandes en attente ou refusées seulement : les clubs actifs ne se consultent pas ici."""
    assert etat is not EtatClub.actif
    requete = _requete(acces).where(Club.etat == etat)
    total = await db.scalar(select(func.count()).select_from(requete.with_only_columns(Club.id).subquery()))
    ordre = Club.demande_le.asc() if etat is EtatClub.en_attente else Club.decide_le.desc()
    lignes = (
        await db.execute(
            requete.order_by(ordre, Club.id).offset((page - 1) * par_page).limit(min(par_page, LIMITE_FILE))
        )
    ).all()
    lignes = [tuple(ligne) for ligne in lignes]
    return FileClubs(
        total=total or 0,
        demandes=[await _demande(db, *ligne) for ligne in lignes],  # type: ignore[misc]
    )


async def compter_en_attente(db: AsyncSession, acces: Acces) -> int:
    """Demandes de clubs, passations, affiliations et rattachements à décider, dans le périmètre du collaborateur."""
    membres = await compter_a_valider(db, acces)
    if acces.national:
        demandes = await db.scalar(select(func.count()).where(Club.etat == EtatClub.en_attente))
        passations = await db.scalar(select(func.count()).where(ClubPassation.etat == EtatPassation.en_attente))
        return (demandes or 0) + (passations or 0) + membres
    demandes = await db.scalar(
        select(func.count())
        .select_from(Club)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .where(Club.etat == EtatClub.en_attente, Iesg.dre_code == acces.collaborateur.perimetre_dre)
    )
    passations = await db.scalar(
        select(func.count())
        .select_from(ClubPassation)
        .join(Club, Club.id == ClubPassation.club_id)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .where(ClubPassation.etat == EtatPassation.en_attente, Iesg.dre_code == acces.collaborateur.perimetre_dre)
    )
    return (demandes or 0) + (passations or 0) + membres


Ligne = tuple[Club, Utilisateur, Eleve, Etablissement, Iesg, Dre]


async def _a_decider(db: AsyncSession, acces: Acces, club_id: UUID, version: int | None = None) -> Ligne:
    """La demande, verrouillée : deux décisions simultanées passent l'une après l'autre. Le périmètre se lit
    sur l'établissement actuel : un changement d'établissement concurrent fait sortir la demande du périmètre."""
    ligne = (
        await db.execute(_requete(acces).where(Club.id == club_id).with_for_update(of=[Club, Utilisateur]))
    ).one_or_none()
    if ligne is None:
        raise Introuvable
    club = ligne[0]
    if club.etat is not EtatClub.en_attente:
        raise Refus(f"Cette demande a déjà été traitée : elle est {club.etat.value}.", 409)
    if version is not None and version != club.version:
        raise Refus("Ce club a été modifié depuis que tu l'as ouvert : recharge la page et vérifie-le.", 409)
    return tuple(ligne)  # type: ignore[return-value]


async def activer(db: AsyncSession, acces: Acces, club_id: UUID, ip: str, version: int | None = None) -> DemandeClub:
    """`version` : celle du club que le collaborateur a vérifié. Le site l'envoie toujours."""
    club, demandeur, eleve, etablissement, iesg, dre = await _a_decider(db, acces, club_id, version)
    if demandeur.statut is not StatutCompte.actif:
        raise Refus("Ce compte est suspendu : réactive-le d'abord depuis sa fiche.", 409)
    if etablissement.statut is not StatutEtablissement.actif:
        raise Refus("Cet établissement n'est plus actif : traite-le dans le référentiel avant de valider ce club.", 409)
    if await db.scalar(select(Club).where(Club.etablissement_id == etablissement.id, Club.etat == EtatClub.actif)):
        raise Refus("Cet établissement a déjà un club actif.", 409)
    # Le demandeur ne peut présider qu'un club actif.
    if await db.scalar(select(Club).where(Club.president_id == demandeur.id, Club.etat == EtatClub.actif)):
        raise Refus("Ce demandeur est déjà président d'un club actif.", 409)

    club.etat = EtatClub.actif
    club.president_id = demandeur.id
    club.decide_le = datetime.now(UTC)
    club.decide_par = acces.utilisateur.id
    club.actif_le = datetime.now(UTC)
    # Le président est membre de droit de son club (spec 020).
    await adhesion_president(db, club)
    # Une doublure en attente du même établissement est refusée automatiquement, dans la même transaction.
    doublures = (
        await db.scalars(
            select(Club).where(
                Club.etablissement_id == etablissement.id, Club.etat == EtatClub.en_attente, Club.id != club.id
            )
        )
    ).all()
    for doublure in doublures:
        doublure.etat = EtatClub.refuse
        doublure.motif_refus = "Un club a été activé pour cet établissement."
        doublure.decide_le = datetime.now(UTC)
        doublure.decide_par = acces.utilisateur.id
        journaliser(
            db,
            "club_refuse",
            acces.utilisateur,
            cible_type="club",
            cible_id=doublure.id,
            perimetre=dre.code,
            details={"motif": doublure.motif_refus, "automatique": True},
            adresse_ip=ip,
        )
    journaliser(
        db,
        "club_active",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=dre.code,
        details={"president_pseudonyme": eleve.pseudonyme},
        adresse_ip=ip,
    )
    try:
        await db.commit()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != "23505":
            raise
        raise Refus("Cet établissement a déjà un club actif.", 409) from None
    return await _demande(db, club, demandeur, eleve, etablissement, iesg, dre)


async def refuser(
    db: AsyncSession, acces: Acces, club_id: UUID, motif: str, ip: str, version: int | None = None
) -> DemandeClub:
    ligne = await _a_decider(db, acces, club_id, version)
    club, demandeur, eleve, etablissement, iesg, dre = ligne
    club.etat = EtatClub.refuse
    club.motif_refus = motif
    club.decide_le = datetime.now(UTC)
    club.decide_par = acces.utilisateur.id
    journaliser(
        db,
        "club_refuse",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=dre.code,
        details={"motif": motif},
        adresse_ip=ip,
    )
    await db.commit()
    return await _demande(db, club, demandeur, eleve, etablissement, iesg, dre)


# Passations -------------------------------------------------------------------------------------------------


def _requete_passation(acces: Acces) -> Select[tuple[ClubPassation, Club, Etablissement, Iesg, Dre]]:
    """Passations en attente, dans le périmètre du collaborateur."""
    requete = (
        select(ClubPassation, Club, Etablissement, Iesg, Dre)
        .join(Club, Club.id == ClubPassation.club_id)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
    )
    if not acces.national:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    return requete


async def _passation(db: AsyncSession, ligne: tuple) -> Passation:
    passation, club, etablissement, iesg, dre = ligne
    successeur = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == passation.successeur_id))
    sortant = (
        await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == club.president_id))
        if club.president_id
        else None
    )
    return Passation(
        id=passation.id,
        club_id=club.id,
        club_nom=club.nom,
        etablissement=_etablissement(etablissement, iesg, dre),
        successeur_pseudonyme=successeur or "",
        president_sortant_pseudonyme=sortant or "",
        etat=passation.etat.value,
        propose_le=passation.propose_le,
        decide_le=passation.decide_le,
        motif_refus=passation.motif_refus,
        version=passation.version,
    )


async def file_passations(db: AsyncSession, acces: Acces) -> FilePassations:
    requete = _requete_passation(acces).where(ClubPassation.etat == EtatPassation.en_attente)
    total = await db.scalar(select(func.count()).select_from(requete.with_only_columns(ClubPassation.id).subquery()))
    lignes = (
        await db.execute(requete.order_by(ClubPassation.propose_le.asc(), ClubPassation.id).limit(LIMITE_FILE))
    ).all()
    lignes = [tuple(ligne) for ligne in lignes]
    return FilePassations(
        total=total or 0,
        passations=[await _passation(db, ligne) for ligne in lignes],
    )


async def _passation_a_decider(db: AsyncSession, acces: Acces, passation_id: UUID, version: int | None) -> tuple:
    """La passation, verrouillée ; le périmètre se relit sur le club au moment de la décision."""
    ligne = (
        await db.execute(
            _requete_passation(acces).where(ClubPassation.id == passation_id).with_for_update(of=[ClubPassation, Club])
        )
    ).one_or_none()
    if ligne is None:
        raise Introuvable
    passation = ligne[0]
    if passation.etat is not EtatPassation.en_attente:
        raise Refus("Cette passation a déjà été traitée.", 409)
    if version is not None and version != passation.version:
        raise Refus("Cette passation a changé depuis que tu l'as ouverte : recharge la page.", 409)
    return tuple(ligne)


async def valider_passation(
    db: AsyncSession, acces: Acces, passation_id: UUID, ip: str, version: int | None = None
) -> Passation:
    """Le successeur devient président ; l'ancien perd la gestion. Le club garde tout."""
    ligne = await _passation_a_decider(db, acces, passation_id, version)
    passation, club, _, _, dre = ligne
    successeur = await db.get(Utilisateur, passation.successeur_id)
    if successeur is None or successeur.statut is not StatutCompte.actif:
        raise Refus("Le successeur n'est plus actif : il ne peut pas devenir président.", 409)
    eleve_succ = await db.get(Eleve, passation.successeur_id)
    if eleve_succ is None or eleve_succ.etablissement_id != club.etablissement_id:
        raise Refus("Le successeur n'est plus dans l'établissement du club : la passation est refusée.", 409)
    if club.etat is not EtatClub.actif:
        raise Refus("Ce club n'est plus actif : la passation ne peut pas être validée.", 409)
    avant = club.president_id
    if avant == passation.successeur_id:
        raise Refus("Ce successeur est déjà président du club.", 409)
    club.president_id = passation.successeur_id
    passation.etat = EtatPassation.validee
    passation.decide_le = datetime.now(UTC)
    passation.decide_par = acces.utilisateur.id
    eleve_sortant = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == avant)) if avant else None
    journaliser(
        db,
        "club_passation",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=dre.code,
        details={
            "avant": str(avant) if avant else None,
            "avant_pseudonyme": eleve_sortant,
            "apres": str(passation.successeur_id),
            "apres_pseudonyme": eleve_succ.pseudonyme,
            "passation_id": str(passation.id),
        },
        adresse_ip=ip,
    )
    await db.commit()
    return await _passation(db, ligne)


async def refuser_passation(
    db: AsyncSession, acces: Acces, passation_id: UUID, motif: str, ip: str, version: int | None = None
) -> Passation:
    ligne = await _passation_a_decider(db, acces, passation_id, version)
    passation, club, _, _, dre = ligne
    passation.etat = EtatPassation.refusee
    passation.motif_refus = motif
    passation.decide_le = datetime.now(UTC)
    passation.decide_par = acces.utilisateur.id
    journaliser(
        db,
        "club_passation_refusee",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=dre.code,
        details={"motif": motif, "passation_id": str(passation.id)},
        adresse_ip=ip,
    )
    await db.commit()
    return await _passation(db, ligne)
