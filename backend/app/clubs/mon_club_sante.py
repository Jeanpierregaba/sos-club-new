"""« Mon Club Santé » : l'espace partagé des encadreurs d'un club (spec 033).

Un encadreur vérifié, rattaché au club de son établissement, y suit le statut et les effectifs, confirme ou refuse
les affiliations des élèves, retire un élève, signale le désistement d'un autre encadreur et propose un président.
Il ne voit des élèves que le pseudonyme et la classe (décision 4). Pour tout autre compte, le club n'existe pas.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs import activation
from app.clubs.adhesions import DEJA_TRAITEE, VIOLATION_UNICITE
from app.clubs.affiliations import confirmer_affiliation, refuser_affiliation, retirer_affiliation
from app.clubs.models import (
    CLUB_VIVANT,
    PASSATION_EN_ATTENTE,
    Adhesion,
    Club,
    ClubPassation,
    EtatAdhesion,
    EtatPassation,
    EtatRattachement,
    EtatSignalement,
    Rattachement,
    SignalementDesistement,
)
from app.clubs.rattachements import encadreur_actif, passations_a_confirmer
from app.clubs.requetes import encadreurs_actifs
from app.clubs.schemas import (
    AffiliationDuClub,
    AffiliationsDuClub,
    MembreEquipe,
    MonClubSante,
    Seuils,
    SignalementResume,
)
from app.comptes.inscription import Refus, etablissement_rattache
from app.comptes.models import StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur

INTROUVABLE = "Tu n'es rattaché à aucun club pour l'instant."


async def club_de_l_encadreur(db: AsyncSession, utilisateur: Utilisateur, *, verrouiller: bool = False) -> Club:
    """Le club vivant auquel cet encadreur vérifié est rattaché ; 403 pour un autre profil, 404 sans club."""
    await encadreur_actif(db, utilisateur)
    requete = (
        select(Club)
        .join(Rattachement, Rattachement.club_id == Club.id)
        .where(
            Rattachement.encadreur_id == utilisateur.id,
            Rattachement.etat == EtatRattachement.actif,
            Club.etat.in_(CLUB_VIVANT),
        )
    )
    if verrouiller:
        requete = requete.with_for_update(of=Club)
    club = await db.scalar(requete)
    if club is None:
        raise Refus(INTROUVABLE, 404)
    return club


# Lecture ----------------------------------------------------------------------------------------------------


async def _equipe(db: AsyncSession, club: Club, utilisateur: Utilisateur) -> list[MembreEquipe]:
    signales = set(
        await db.scalars(
            select(SignalementDesistement.encadreur_id).where(
                SignalementDesistement.club_id == club.id, SignalementDesistement.etat == EtatSignalement.en_attente
            )
        )
    )
    lignes = await db.execute(
        select(Utilisateur, Encadreur)
        .join(Encadreur, Encadreur.utilisateur_id == Utilisateur.id)
        .where(Utilisateur.id.in_(encadreurs_actifs(club.id)))
        .order_by(Utilisateur.nom, Utilisateur.prenom)
    )
    return [
        MembreEquipe(
            utilisateur_id=compte.id,
            prenom=compte.prenom,
            nom=compte.nom,
            fonction=encadreur.fonction.value,
            moi=compte.id == utilisateur.id,
            signalement_en_attente=compte.id in signales,
        )
        for compte, encadreur in lignes.all()
    ]


async def _signalements(db: AsyncSession, club: Club, utilisateur: Utilisateur) -> list[SignalementResume]:
    """Les signalements faits par cet encadreur dans ce club, les plus récents d'abord."""
    lignes = await db.execute(
        select(SignalementDesistement, Utilisateur)
        .join(Utilisateur, Utilisateur.id == SignalementDesistement.encadreur_id)
        .where(SignalementDesistement.club_id == club.id, SignalementDesistement.signale_par == utilisateur.id)
        .order_by(SignalementDesistement.signale_le.desc())
        .limit(20)
    )
    return [resume_signalement(signalement, vise) for signalement, vise in lignes.all()]


def resume_signalement(signalement: SignalementDesistement, vise: Utilisateur) -> SignalementResume:
    return SignalementResume(
        id=signalement.id,
        encadreur_prenom=vise.prenom,
        encadreur_nom=vise.nom,
        motif=signalement.motif,
        etat=signalement.etat.value,
        signale_le=signalement.signale_le,
        decide_le=signalement.decide_le,
        motif_decision=signalement.motif_decision,
    )


async def _pseudonyme(db: AsyncSession, utilisateur_id: UUID | None) -> str | None:
    if utilisateur_id is None:
        return None
    return await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == utilisateur_id))


async def fiche(db: AsyncSession, utilisateur: Utilisateur) -> MonClubSante:
    club = await club_de_l_encadreur(db, utilisateur)
    statut = activation.statut_effectif(club, activation.maintenant())
    nb_encadreurs, nb_eleves = await activation.effectifs(db, club.id)
    a_confirmer = await db.scalar(activation.a_confirmer_sql(club.id))
    propose = await db.scalar(
        select(ClubPassation.successeur_id).where(
            ClubPassation.club_id == club.id, ClubPassation.etat.in_(PASSATION_EN_ATTENTE)
        )
    )
    return MonClubSante(
        id=club.id,
        nom=club.nom,
        etablissement=await etablissement_rattache(db, club.etablissement_id),
        statut=statut.value,
        actif_le=club.actif_le,
        regularisation_jusquau=club.regularisation_jusquau if statut.value == "en_regularisation" else None,
        declare_terrain=club.declare_terrain,
        seuils=Seuils(
            encadreurs=activation.SEUIL_ENCADREURS,
            eleves=activation.SEUIL_ELEVES,
            delai_jours=activation.DELAI_REGULARISATION.days,
        ),
        nb_encadreurs=nb_encadreurs,
        nb_eleves=nb_eleves,
        a_confirmer=a_confirmer or 0,
        equipe=await _equipe(db, club, utilisateur),
        president_pseudonyme=await _pseudonyme(db, club.president_id),
        president_propose=await _pseudonyme(db, propose),
        passations_a_confirmer=await passations_a_confirmer(db, utilisateur),
        mes_signalements=await _signalements(db, club, utilisateur),
    )


async def affiliations(db: AsyncSession, utilisateur: Utilisateur) -> AffiliationsDuClub:
    club = await club_de_l_encadreur(db, utilisateur)
    lignes = await db.execute(
        select(Adhesion, Eleve)
        .join(Eleve, Eleve.utilisateur_id == Adhesion.eleve_id)
        .join(Utilisateur, Utilisateur.id == Adhesion.eleve_id)
        .where(
            Adhesion.club_id == club.id,
            Adhesion.etat.in_((EtatAdhesion.en_attente_validation, EtatAdhesion.active)),
            Utilisateur.statut == StatutCompte.actif,
        )
        .order_by(Adhesion.demande_le, Adhesion.id)
    )
    a_confirmer, confirmees = [], []
    for adhesion, eleve in lignes.all():
        ligne = AffiliationDuClub(
            id=adhesion.id,
            pseudonyme=eleve.pseudonyme,
            classe=eleve.classe.value,
            etat=adhesion.etat.value,
            demande_le=adhesion.demande_le,
            depuis=adhesion.decide_le,
            president=adhesion.eleve_id == club.president_id,
            version=adhesion.version,
        )
        (confirmees if adhesion.etat is EtatAdhesion.active else a_confirmer).append(ligne)
    confirmees.sort(key=lambda a: (not a.president, a.pseudonyme.casefold()))
    return AffiliationsDuClub(a_confirmer=a_confirmer, confirmees=confirmees)


# Décisions sur les affiliations ------------------------------------------------------------------------------


async def _affiliation(
    db: AsyncSession, club: Club, affiliation_id: UUID, version: int, etat: EtatAdhesion
) -> Adhesion:
    adhesion = await db.scalar(
        select(Adhesion).where(Adhesion.id == affiliation_id, Adhesion.club_id == club.id).with_for_update()
    )
    if adhesion is None:
        raise Refus("Cette affiliation est introuvable.", 404)
    if adhesion.etat is not etat or adhesion.version != version:
        raise Refus(DEJA_TRAITEE, 409)
    return adhesion


async def confirmer(
    db: AsyncSession, utilisateur: Utilisateur, affiliation_id: UUID, version: int, adresse_ip: str
) -> AffiliationsDuClub:
    club = await club_de_l_encadreur(db, utilisateur)
    adhesion = await _affiliation(db, club, affiliation_id, version, EtatAdhesion.en_attente_validation)
    await confirmer_affiliation(db, adhesion, club, utilisateur, "encadreur", adresse_ip)
    await db.commit()
    return await affiliations(db, utilisateur)


async def refuser(
    db: AsyncSession, utilisateur: Utilisateur, affiliation_id: UUID, motif: str, version: int, adresse_ip: str
) -> AffiliationsDuClub:
    club = await club_de_l_encadreur(db, utilisateur)
    adhesion = await _affiliation(db, club, affiliation_id, version, EtatAdhesion.en_attente_validation)
    await refuser_affiliation(db, adhesion, club, utilisateur, "encadreur", motif, adresse_ip)
    await db.commit()
    return await affiliations(db, utilisateur)


async def retirer(
    db: AsyncSession, utilisateur: Utilisateur, affiliation_id: UUID, motif: str, version: int, adresse_ip: str
) -> AffiliationsDuClub:
    club = await club_de_l_encadreur(db, utilisateur)
    adhesion = await _affiliation(db, club, affiliation_id, version, EtatAdhesion.active)
    await retirer_affiliation(db, adhesion, club, utilisateur, "encadreur", motif, adresse_ip)
    await db.commit()
    return await affiliations(db, utilisateur)


# Désistement et président ------------------------------------------------------------------------------------


async def signaler_desistement(
    db: AsyncSession, utilisateur: Utilisateur, encadreur_id: UUID, motif: str, adresse_ip: str
) -> SignalementResume:
    """Le signalement ne retire personne : l'équipe le confirme ou le rejette (spec 033, point 12)."""
    club = await club_de_l_encadreur(db, utilisateur)
    if encadreur_id == utilisateur.id:
        raise Refus("Tu ne peux pas signaler ton propre désistement.")
    vise = await db.scalar(encadreurs_actifs(club.id).where(Rattachement.encadreur_id == encadreur_id))
    if vise is None:
        raise Refus("Cet encadreur ne fait pas partie de ton club.", 404)
    signalement = SignalementDesistement(
        club_id=club.id, encadreur_id=encadreur_id, signale_par=utilisateur.id, motif=motif
    )
    db.add(signalement)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Un signalement attend déjà l'équipe pour cet encadreur.", 409) from None
    journaliser(
        db,
        "desistement_signale",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=await activation.dre_du_club(db, club.id),
        details={"signalement_id": str(signalement.id), "encadreur_id": str(encadreur_id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    compte = await db.get(Utilisateur, encadreur_id)
    assert compte is not None
    await db.refresh(signalement)
    return resume_signalement(signalement, compte)


async def proposer_president(
    db: AsyncSession, utilisateur: Utilisateur, affiliation_id: UUID, adresse_ip: str
) -> MonClubSante:
    """Un club en service sans président en reçoit un : l'encadreur propose, l'équipe valide (Q19 amendé)."""
    club = await club_de_l_encadreur(db, utilisateur, verrouiller=True)
    if not activation.est_en_service(club):
        raise Refus("Le club doit être actif pour recevoir un président.", 409)
    if club.president_id is not None:
        raise Refus("Le club a déjà un président : il lui revient de proposer une passation.", 409)
    if await db.scalar(
        select(ClubPassation.id).where(ClubPassation.club_id == club.id, ClubPassation.etat.in_(PASSATION_EN_ATTENTE))
    ):
        raise Refus("Une proposition attend déjà l'équipe.", 409)
    adhesion = await db.scalar(
        select(Adhesion).where(
            Adhesion.id == affiliation_id, Adhesion.club_id == club.id, Adhesion.etat == EtatAdhesion.active
        )
    )
    eleve = await db.get(Utilisateur, adhesion.eleve_id) if adhesion else None
    if adhesion is None or eleve is None or eleve.statut is not StatutCompte.actif:
        raise Refus("Choisis un élève confirmé du club, dont le compte est actif.", 409)
    passation = ClubPassation(
        club_id=club.id, successeur_id=adhesion.eleve_id, propose_par=utilisateur.id, etat=EtatPassation.en_attente
    )
    db.add(passation)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Une proposition attend déjà l'équipe.", 409) from None
    journaliser(
        db,
        "club_president_propose",
        utilisateur,
        cible_type="club",
        cible_id=club.id,
        perimetre=await activation.dre_du_club(db, club.id),
        details={"passation_id": str(passation.id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
    return await fiche(db, utilisateur)
