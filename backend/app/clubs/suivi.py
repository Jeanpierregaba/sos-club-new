"""Suivi des clubs par l'équipe (spec 033) : liste filtrable, fiche avec le journal des statuts, désistements à
confirmer ou rejeter, marqueur « déclaré sur le terrain ».

Un collaborateur national voit tous les clubs ; un collaborateur de DRE, ceux de sa DRE seulement : pour les
autres, la réponse est celle d'un club inexistant (ADR-0008). Les élèves n'apparaissent que par leur pseudonyme.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs import activation
from app.clubs.models import (
    CLUB_VIVANT,
    Club,
    ClubStatut,
    EtatRattachement,
    EtatSignalement,
    Rattachement,
    SignalementDesistement,
)
from app.clubs.rattachements import liberer_passation
from app.clubs.schemas import (
    ClubSuivi,
    EleveDuClub,
    EncadreurSuivi,
    FicheSuivi,
    FileDesistements,
    LigneJournalClub,
    PageSuivi,
    Seuils,
    SignalementAdmin,
)
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.notifications.service import notifier
from app.referentiel.models import Dre, Etablissement, Iesg
from app.referentiel.normalisation import normaliser
from app.referentiel.regions import NOMS as NOMS_REGIONS

INTROUVABLE = "Ce club est introuvable."
LIMITE_FILE = 200


def seuils() -> Seuils:
    return Seuils(
        encadreurs=activation.SEUIL_ENCADREURS,
        eleves=activation.SEUIL_ELEVES,
        delai_jours=activation.DELAI_REGULARISATION.days,
    )


def _avec_territoire[T: Select](requete: T, acces: Acces) -> T:
    requete = (
        requete.join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
    )
    if not acces.national:
        requete = requete.where(Dre.code == acces.collaborateur.perimetre_dre)
    return requete


def _colonnes(instant: datetime) -> tuple:
    a_confirmer = activation.a_confirmer_sql(Club.id).correlate(Club).scalar_subquery()
    return (
        Club,
        Etablissement.nom,
        Iesg.nom,
        Dre.nom,
        Dre.region,
        activation.etat_effectif(instant).label("statut"),
        activation.nb_encadreurs_sql().label("nb_encadreurs"),
        activation.nb_eleves_sql().label("nb_eleves"),
        a_confirmer.label("a_confirmer"),
    )


def _ligne(ligne: tuple) -> ClubSuivi:
    club, etablissement, iesg, dre, region, statut, nb_encadreurs, nb_eleves, a_confirmer = ligne
    return ClubSuivi(
        id=club.id,
        nom=club.nom,
        etablissement=etablissement,
        iesg=iesg,
        dre=dre,
        region=NOMS_REGIONS[region],
        statut=statut,
        nb_encadreurs=nb_encadreurs or 0,
        nb_eleves=nb_eleves or 0,
        a_confirmer=a_confirmer or 0,
        actif_le=club.actif_le,
        regularisation_jusquau=club.regularisation_jusquau if statut == "en_regularisation" else None,
        declare_terrain=club.declare_terrain,
    )


async def lister(
    db: AsyncSession,
    acces: Acces,
    *,
    statut: str | None = None,
    region: str | None = None,
    dre: str | None = None,
    iesg: UUID | None = None,
    recherche: str | None = None,
    terrain: bool | None = None,
    page: int = 1,
    par_page: int = 50,
) -> PageSuivi:
    instant = activation.maintenant()
    requete = _avec_territoire(select(*_colonnes(instant)).where(Club.etat.in_(CLUB_VIVANT)), acces)
    if statut:
        requete = requete.where(activation.etat_effectif(instant) == statut)
    if region:
        requete = requete.where(Dre.region == region)
    if dre:
        requete = requete.where(Dre.code == dre)
    if iesg:
        requete = requete.where(Iesg.id == iesg)
    if terrain is not None:
        requete = requete.where(Club.declare_terrain.is_(terrain))
    if recherche and (cle := normaliser(recherche)):
        requete = requete.where(or_(Etablissement.nom_normalise.contains(cle), Club.nom_normalise.contains(cle)))
    total = await db.scalar(select(func.count()).select_from(requete.with_only_columns(Club.id).subquery()))
    lignes = (
        await db.execute(
            requete.order_by(Dre.ordre, Iesg.nom, Etablissement.nom).offset((page - 1) * par_page).limit(par_page)
        )
    ).all()
    return PageSuivi(total=total or 0, page=page, par_page=par_page, clubs=[_ligne(tuple(ligne)) for ligne in lignes])


async def _club(db: AsyncSession, acces: Acces, club_id: UUID, *, verrouiller: bool = False) -> Club:
    requete = _avec_territoire(select(Club).where(Club.id == club_id, Club.etat.in_(CLUB_VIVANT)), acces)
    if verrouiller:
        requete = requete.with_for_update(of=Club)
    club = await db.scalar(requete)
    if club is None:
        raise Refus(INTROUVABLE, 404)
    return club


async def _signalements(db: AsyncSession, requete: Select) -> list[SignalementAdmin]:
    vise = aliased(Utilisateur)
    auteur = aliased(Utilisateur)
    lignes = await db.execute(
        requete.add_columns(vise, auteur, Dre.nom)
        .join(vise, vise.id == SignalementDesistement.encadreur_id)
        .outerjoin(auteur, auteur.id == SignalementDesistement.signale_par)
    )
    return [
        SignalementAdmin(
            id=signalement.id,
            club_id=club.id,
            club_nom=club.nom,
            dre=dre,
            encadreur_prenom=compte_vise.prenom,
            encadreur_nom=compte_vise.nom,
            signale_par=f"{compte_auteur.prenom} {compte_auteur.nom}" if compte_auteur else None,
            motif=signalement.motif,
            etat=signalement.etat.value,
            signale_le=signalement.signale_le,
            decide_le=signalement.decide_le,
            motif_decision=signalement.motif_decision,
            version=signalement.version,
        )
        for signalement, club, compte_vise, compte_auteur, dre in lignes.all()
    ]


def _requete_signalements(acces: Acces) -> Select:
    return _avec_territoire(
        select(SignalementDesistement, Club).join(Club, Club.id == SignalementDesistement.club_id), acces
    )


async def fiche(db: AsyncSession, acces: Acces, club_id: UUID) -> FicheSuivi:
    club = await _club(db, acces, club_id)
    instant = activation.maintenant()
    ligne = (await db.execute(_avec_territoire(select(*_colonnes(instant)).where(Club.id == club.id), acces))).one()
    encadreurs = await db.execute(
        select(Utilisateur, Encadreur)
        .join(Encadreur, Encadreur.utilisateur_id == Utilisateur.id)
        .where(Utilisateur.id.in_(activation.encadreurs_comptes(club.id)))
        .order_by(Utilisateur.nom, Utilisateur.prenom)
    )
    eleves = await db.scalars(
        select(Eleve)
        .where(Eleve.utilisateur_id.in_(activation.eleves_comptes(club.id)))
        .order_by(Eleve.pseudonyme_normalise)
    )
    journal = await db.scalars(
        select(ClubStatut).where(ClubStatut.club_id == club.id).order_by(ClubStatut.cree_le.desc()).limit(100)
    )
    president = (
        await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == club.president_id))
        if club.president_id
        else None
    )
    return FicheSuivi(
        club=_ligne(tuple(ligne)),
        declare_note=club.declare_note,
        declare_le=club.declare_le,
        president_pseudonyme=president,
        encadreurs=[
            EncadreurSuivi(utilisateur_id=compte.id, prenom=compte.prenom, nom=compte.nom, fonction=e.fonction.value)
            for compte, e in encadreurs.all()
        ],
        eleves=[EleveDuClub(pseudonyme=e.pseudonyme, classe=e.classe.value) for e in eleves.all()],
        journal=[
            LigneJournalClub(
                ancien=ligne.ancien.value if ligne.ancien else None,
                nouveau=ligne.nouveau.value,
                cause=ligne.cause,
                nb_encadreurs=ligne.nb_encadreurs,
                nb_eleves=ligne.nb_eleves,
                cree_le=ligne.cree_le,
            )
            for ligne in journal.all()
        ],
        signalements=await _signalements(
            db,
            _requete_signalements(acces)
            .where(SignalementDesistement.club_id == club.id)
            .order_by(SignalementDesistement.signale_le.desc())
            .limit(50),
        ),
        version=club.version,
    )


async def marquer_terrain(
    db: AsyncSession, acces: Acces, club_id: UUID, declare: bool, note: str | None, version: int, ip: str
) -> FicheSuivi:
    """« Déclaré sur le terrain » : une information à part, sans effet sur le statut ni sur les droits."""
    club = await _club(db, acces, club_id, verrouiller=True)
    if club.version != version:
        raise Refus("Ce club a changé depuis que tu l'as ouvert : recharge la page.", 409)
    club.declare_terrain = declare
    club.declare_note = (note or None) if declare else None
    club.declare_le = datetime.now(UTC) if declare else None
    club.declare_par = acces.utilisateur.id if declare else None
    journaliser(
        db,
        "club_declare_terrain" if declare else "club_non_declare_terrain",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=await activation.dre_du_club(db, club.id),
        details={"note": club.declare_note},
        adresse_ip=ip,
    )
    await db.commit()
    return await fiche(db, acces, club.id)


# Désistements -----------------------------------------------------------------------------------------------


async def file_desistements(db: AsyncSession, acces: Acces) -> FileDesistements:
    requete = _requete_signalements(acces).where(SignalementDesistement.etat == EtatSignalement.en_attente)
    total = await db.scalar(
        select(func.count()).select_from(requete.with_only_columns(SignalementDesistement.id).subquery())
    )
    return FileDesistements(
        total=total or 0,
        signalements=await _signalements(
            db, requete.order_by(SignalementDesistement.signale_le, SignalementDesistement.id).limit(LIMITE_FILE)
        ),
    )


async def _signalement_a_decider(
    db: AsyncSession, acces: Acces, signalement_id: UUID, version: int
) -> tuple[SignalementDesistement, Club]:
    ligne = (
        await db.execute(
            _requete_signalements(acces)
            .where(SignalementDesistement.id == signalement_id)
            .with_for_update(of=[SignalementDesistement, Club])
        )
    ).first()
    if ligne is None:
        raise Refus("Ce signalement est introuvable.", 404)
    signalement, club = ligne
    if signalement.etat is not EtatSignalement.en_attente or signalement.version != version:
        raise Refus("Ce signalement a déjà été traité : recharge la page.", 409)
    return signalement, club


async def _prevenir_signaleur(db: AsyncSession, signalement: SignalementDesistement, titre: str, message: str) -> None:
    if signalement.signale_par is not None:
        notifier(db, signalement.signale_par, "club_desistement", titre, message, activation.LIEN)


async def confirmer_desistement(
    db: AsyncSession, acces: Acces, signalement_id: UUID, version: int, ip: str
) -> FileDesistements:
    """L'encadreur visé quitte le club (son compte et ses contributions restent) ; le club est recalculé."""
    signalement, club = await _signalement_a_decider(db, acces, signalement_id, version)
    signalement.etat = EtatSignalement.confirme
    signalement.decide_le = datetime.now(UTC)
    signalement.decide_par = acces.utilisateur.id
    rattachements = (
        await db.scalars(
            select(Rattachement)
            .where(
                Rattachement.club_id == club.id,
                Rattachement.encadreur_id == signalement.encadreur_id,
                Rattachement.etat == EtatRattachement.actif,
            )
            .with_for_update()
        )
    ).all()
    for rattachement in rattachements:
        rattachement.etat = EtatRattachement.retire
        rattachement.retire_le = signalement.decide_le
        rattachement.retire_par = acces.utilisateur.id
        rattachement.motif_retrait = "Désistement confirmé par l'équipe."
    journaliser(
        db,
        "desistement_confirme",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=await activation.dre_du_club(db, club.id),
        details={"signalement_id": str(signalement.id), "encadreur_id": str(signalement.encadreur_id)},
        adresse_ip=ip,
    )
    await db.flush()
    await liberer_passation(db, club.id)
    await activation.recalculer(db, club.id, "desistement_confirme", acces.utilisateur.id)
    await _prevenir_signaleur(
        db, signalement, "Désistement confirmé", "L'équipe a confirmé le désistement que tu as signalé."
    )
    await db.commit()
    return await file_desistements(db, acces)


async def rejeter_desistement(
    db: AsyncSession, acces: Acces, signalement_id: UUID, motif: str, version: int, ip: str
) -> FileDesistements:
    """Rien ne change pour le club ; l'encadreur visé n'est pas prévenu (spec 033, cas limites)."""
    signalement, club = await _signalement_a_decider(db, acces, signalement_id, version)
    signalement.etat = EtatSignalement.rejete
    signalement.motif_decision = motif
    signalement.decide_le = datetime.now(UTC)
    signalement.decide_par = acces.utilisateur.id
    journaliser(
        db,
        "desistement_rejete",
        acces.utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=await activation.dre_du_club(db, club.id),
        details={"signalement_id": str(signalement.id), "motif": motif},
        adresse_ip=ip,
    )
    await _prevenir_signaleur(db, signalement, "Signalement rejeté", f"L'équipe a rejeté ton signalement : {motif}")
    await db.commit()
    return await file_desistements(db, acces)
