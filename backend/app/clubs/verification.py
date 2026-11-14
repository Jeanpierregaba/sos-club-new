"""Décisions de l'équipe sur les clubs : passations (spec 019) et compteur du tableau de bord. Depuis la spec 033,
un club n'est plus activé par l'équipe : `activation.py` s'en charge.

Un collaborateur national voit toutes les demandes. Un collaborateur de DRE ne voit et ne décide que celles
des établissements de sa DRE : pour les autres, il reçoit la même réponse que pour une demande inexistante.
Le périmètre se lit sur l'établissement actuel, sous verrou, au moment de la décision. Le club n'a pas de
compte : la gestion passe par le lien `president_id`.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs import activation
from app.clubs.espace import transferer_contenus
from app.clubs.membres_admin import compter_a_valider
from app.clubs.models import (
    CLUB_VIVANT,
    Adhesion,
    Club,
    ClubPassation,
    EtatAdhesion,
    EtatPassation,
    EtatSignalement,
    SignalementDesistement,
)
from app.clubs.schemas import FilePassations, Passation
from app.comptes.inscription import Refus
from app.comptes.models import StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.referentiel.models import Dre, Etablissement, Iesg
from app.referentiel.schemas import EtablissementRattache

LIMITE_FILE = 200


class Introuvable(Exception):
    pass


def _etablissement(etablissement: Etablissement, iesg: Iesg, dre: Dre) -> EtablissementRattache:
    return EtablissementRattache(
        id=etablissement.id,
        nom=etablissement.nom,
        statut=etablissement.statut,
        iesg=iesg.nom,
        dre_code=dre.code,
        dre=dre.nom,
        localite=etablissement.localite,
    )


async def compter_en_attente(db: AsyncSession, acces: Acces) -> int:
    """Passations, affiliations et désistements à décider, dans le périmètre du collaborateur (spec 033)."""
    membres = await compter_a_valider(db, acces)

    def dans_le_perimetre(requete: Select) -> Select:
        if acces.national:
            return requete
        return (
            requete.join(Etablissement, Etablissement.id == Club.etablissement_id)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
        )

    passations = await db.scalar(
        dans_le_perimetre(
            select(func.count())
            .select_from(ClubPassation)
            .join(Club, Club.id == ClubPassation.club_id)
            .where(ClubPassation.etat == EtatPassation.en_attente)
        )
    )
    desistements = await db.scalar(
        dans_le_perimetre(
            select(func.count())
            .select_from(SignalementDesistement)
            .join(Club, Club.id == SignalementDesistement.club_id)
            .where(SignalementDesistement.etat == EtatSignalement.en_attente)
        )
    )
    return (passations or 0) + (desistements or 0) + membres


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
    if club.etat not in CLUB_VIVANT:
        raise Refus("Ce club n'existe plus : la passation ne peut pas être validée.", 409)
    # Spec 033 (point 14) : un premier président ne se nomme que dans un club en service.
    if club.president_id is None and not activation.est_en_service(club):
        raise Refus("Le club n'est plus actif : un premier président ne peut pas être nommé.", 409)
    avant = club.president_id
    if avant == passation.successeur_id:
        raise Refus("Ce successeur est déjà président du club.", 409)
    if not await db.scalar(
        select(Adhesion.id)
        .where(
            Adhesion.club_id == club.id,
            Adhesion.eleve_id == passation.successeur_id,
            Adhesion.etat == EtatAdhesion.active,
        )
        # Verrou : le successeur ne peut pas quitter le club pendant qu'il en devient président.
        .with_for_update()
    ):
        raise Refus("Le successeur n'est plus membre du club : la passation ne peut pas être validée.", 409)
    club.president_id = passation.successeur_id
    # Les actualités et propositions du club passent au nouveau président (spec 026) : l'ancien perd la main.
    await transferer_contenus(db, club.id, passation.successeur_id)
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
