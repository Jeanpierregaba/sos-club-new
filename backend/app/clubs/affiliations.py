"""Affiliations automatiques des membres (spec 033).

Un élève est affilié « à confirmer » au club de son établissement dès son inscription ; un encadreur est rattaché
au club de son établissement dès que l'équipe l'a vérifié. Un changement d'établissement clôt le lien précédent et
en ouvre un nouveau. Chaque fonction qui change un effectif recalcule le club concerné, dans la transaction de
l'appelant, qui la valide.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.clubs import activation
from app.clubs.adhesions import annuler_passation_du_successeur
from app.clubs.models import (
    ADHESION_EN_COURS,
    CLUB_VIVANT,
    RATTACHEMENT_EN_COURS,
    Adhesion,
    Club,
    EtatAdhesion,
    EtatClub,
    EtatRattachement,
    Rattachement,
)
from app.clubs.rattachements import liberer_passation
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification

CHANGEMENT = "Changement d'établissement."


async def affilier_eleve(db: AsyncSession, eleve_id: UUID, etablissement_id: UUID) -> Adhesion:
    """L'affiliation « à confirmer » de l'élève au club de son établissement (créé au besoin)."""
    club = await activation.club_de(db, etablissement_id)
    adhesion = Adhesion(eleve_id=eleve_id, club_id=club.id, etat=EtatAdhesion.en_attente_validation)
    db.add(adhesion)
    await db.flush()
    return adhesion


# Décisions sur une affiliation à confirmer (encadreur du club ou équipe) ---------------------------------------


async def confirmer_affiliation(
    db: AsyncSession,
    adhesion: Adhesion,
    club: Club,
    auteur: Utilisateur,
    par: str,
    adresse_ip: str | None,
    perimetre: str | None = None,
) -> None:
    """L'affiliation verrouillée par l'appelant devient active ; le club est recalculé."""
    if club.etat not in CLUB_VIVANT:
        raise Refus("Ce club n'existe plus.", 409)
    eleve = await db.get(Eleve, adhesion.eleve_id)
    if eleve is None or eleve.etablissement_id != club.etablissement_id:
        raise Refus("Cet élève a changé d'établissement depuis sa demande.", 409)
    adhesion.etat = EtatAdhesion.active
    adhesion.decide_le = datetime.now(UTC)
    adhesion.decide_par = auteur.id
    perimetre = perimetre or await activation.dre_du_club(db, club.id)
    journaliser(
        db,
        "adhesion_validee",
        auteur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        perimetre=perimetre,
        details={"club_id": str(club.id), "par": par},
        adresse_ip=adresse_ip,
    )
    await db.flush()
    await activation.recalculer(db, club.id, "affiliation_confirmee", auteur.id)


async def refuser_affiliation(
    db: AsyncSession,
    adhesion: Adhesion,
    club: Club,
    auteur: Utilisateur,
    par: str,
    motif: str,
    adresse_ip: str | None,
    perimetre: str | None = None,
) -> None:
    """Une affiliation à confirmer est refusée, avec son motif. Elle ne comptait pas : rien à recalculer."""
    adhesion.etat = EtatAdhesion.refusee
    adhesion.motif_refus = motif
    adhesion.decide_le = datetime.now(UTC)
    adhesion.decide_par = auteur.id
    perimetre = perimetre or await activation.dre_du_club(db, club.id)
    journaliser(
        db,
        "adhesion_refusee",
        auteur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        perimetre=perimetre,
        details={"club_id": str(club.id), "par": par, "motif": motif},
        adresse_ip=adresse_ip,
    )
    await db.flush()


async def retirer_affiliation(
    db: AsyncSession,
    adhesion: Adhesion,
    club: Club,
    auteur: Utilisateur,
    par: str,
    motif: str,
    adresse_ip: str | None,
    perimetre: str | None = None,
) -> None:
    """Un élève confirmé quitte le club (encadreur du club ou équipe, spec 033) ; le club est recalculé."""
    if adhesion.eleve_id == club.president_id:
        raise Refus("Le président ne peut pas être retiré : une passation d'abord.", 409)
    adhesion.etat = EtatAdhesion.retiree
    adhesion.retire_le = datetime.now(UTC)
    adhesion.retire_par = auteur.id
    adhesion.motif_retrait = motif
    perimetre = perimetre or await activation.dre_du_club(db, club.id)
    journaliser(
        db,
        "adhesion_retiree",
        auteur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        perimetre=perimetre,
        details={"club_id": str(club.id), "par": par, "motif": motif},
        adresse_ip=adresse_ip,
    )
    await annuler_passation_du_successeur(db, adhesion)
    await db.flush()
    await activation.recalculer(db, club.id, "affiliation_retiree", auteur.id)


async def _clore_adhesion(
    db: AsyncSession, utilisateur: Utilisateur, motif: str, adresse_ip: str | None
) -> UUID | None:
    """Termine l'affiliation en cours de l'élève et renvoie son club, ou None."""
    adhesion = await db.scalar(
        select(Adhesion)
        .where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat.in_(ADHESION_EN_COURS))
        .with_for_update()
    )
    if adhesion is None:
        return None
    adhesion.etat = EtatAdhesion.retiree
    adhesion.retire_le = datetime.now(UTC)
    adhesion.retire_par = utilisateur.id
    adhesion.motif_retrait = motif
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
    return adhesion.club_id


async def changer_etablissement_eleve(
    db: AsyncSession, utilisateur: Utilisateur, nouvel_etablissement_id: UUID, adresse_ip: str
) -> None:
    """Avant que l'élève change d'établissement : un président passe d'abord la main ; son affiliation prend fin et
    une nouvelle, à confirmer, s'ouvre dans le club du nouvel établissement."""
    if await db.scalar(select(Club.id).where(Club.president_id == utilisateur.id)):
        raise Refus("Tu présides le club de ton établissement : propose d'abord une passation à un autre membre.", 409)
    ancien_club = await _clore_adhesion(db, utilisateur, CHANGEMENT, adresse_ip)
    await db.flush()
    await affilier_eleve(db, utilisateur.id, nouvel_etablissement_id)
    if ancien_club is not None:
        await activation.recalculer(db, ancien_club, "changement_etablissement", utilisateur.id)


async def _clore_rattachements(
    db: AsyncSession, encadreur_id: UUID, motif: str, par: UUID | None, adresse_ip: str | None, sauf: UUID | None = None
) -> list[UUID]:
    """Termine les rattachements en cours de l'encadreur (sauf au club `sauf`) et renvoie leurs clubs."""
    requete = select(Rattachement).where(
        Rattachement.encadreur_id == encadreur_id, Rattachement.etat.in_(RATTACHEMENT_EN_COURS)
    )
    if sauf is not None:
        requete = requete.where(Rattachement.club_id != sauf)
    clubs = []
    for rattachement in (await db.scalars(requete.with_for_update())).all():
        rattachement.etat = EtatRattachement.retire
        rattachement.retire_le = datetime.now(UTC)
        rattachement.retire_par = par
        rattachement.motif_retrait = motif
        journaliser(
            db,
            "rattachement_retire",
            cible_type="rattachement",
            cible_id=rattachement.id,
            details={"club_id": str(rattachement.club_id), "motif": motif},
            adresse_ip=adresse_ip,
        )
        clubs.append(rattachement.club_id)
    await db.flush()
    for club_id in clubs:
        await liberer_passation(db, club_id)
    return clubs


async def rattacher_encadreur(
    db: AsyncSession, encadreur_id: UUID, etablissement_id: UUID, cause: str, par: UUID | None
) -> None:
    """Le rattachement actif de l'encadreur vérifié au club de son établissement, et à lui seul (amende Q16)."""
    club = await activation.club_de(db, etablissement_id)
    anciens = await _clore_rattachements(db, encadreur_id, CHANGEMENT, par, None, sauf=club.id)
    deja = await db.scalar(
        select(Rattachement.id).where(
            Rattachement.encadreur_id == encadreur_id,
            Rattachement.club_id == club.id,
            Rattachement.etat == EtatRattachement.actif,
        )
    )
    if deja is None:
        db.add(
            Rattachement(
                encadreur_id=encadreur_id,
                club_id=club.id,
                etat=EtatRattachement.actif,
                decide_le=datetime.now(UTC),
                decide_par=par,
            )
        )
        await db.flush()
    # Les clubs se verrouillent dans l'ordre de leur identifiant : deux changements croisés ne s'interbloquent pas.
    causes = dict.fromkeys(anciens, "changement_etablissement") | {club.id: cause}
    for club_id in sorted(causes):
        await activation.recalculer(db, club_id, causes[club_id], par)


async def changer_etablissement_encadreur(
    db: AsyncSession, utilisateur: Utilisateur, encadreur: Encadreur, nouvel_etablissement_id: UUID, adresse_ip: str
) -> None:
    """Un encadreur vérifié suit son établissement ; un encadreur en attente sera rattaché à sa vérification."""
    if encadreur.etat is EtatVerification.actif:
        await rattacher_encadreur(
            db, utilisateur.id, nouvel_etablissement_id, "changement_etablissement", utilisateur.id
        )
        return
    for club_id in await _clore_rattachements(db, utilisateur.id, CHANGEMENT, utilisateur.id, adresse_ip):
        await activation.recalculer(db, club_id, "changement_etablissement", utilisateur.id)


async def recalculer_clubs_du_membre(db: AsyncSession, utilisateur_id: UUID, cause: str, par: UUID | None) -> None:
    """Après un changement du compte (suspension, réactivation) : recalcule les clubs dont il est membre."""
    await db.flush()
    clubs = set(
        await db.scalars(
            select(Adhesion.club_id).where(Adhesion.eleve_id == utilisateur_id, Adhesion.etat.in_(ADHESION_EN_COURS))
        )
    ) | set(
        await db.scalars(
            select(Rattachement.club_id).where(
                Rattachement.encadreur_id == utilisateur_id, Rattachement.etat == EtatRattachement.actif
            )
        )
    )
    for club_id in sorted(clubs):
        await activation.recalculer(db, club_id, cause, par)


class DeuxClubs(Exception):
    """Les deux établissements d'une fusion ont chacun un club au-delà de « en constitution » (spec 042)."""

    def __init__(self, absorbe: Club, garde: Club) -> None:
        super().__init__(
            f"Les deux établissements ont chacun un vrai club (« {absorbe.nom} » et « {garde.nom} ») : "
            "deux clubs ne se fusionnent pas ici."
        )


def _au_dela(club: Club | None) -> bool:
    return club is not None and club.etat is not EtatClub.en_constitution


async def clubs_a_fusionner(db: AsyncSession, absorbe_id: UUID, garde_id: UUID) -> tuple[Club | None, Club | None]:
    """Les clubs vivants de l'absorbé et du gardé, verrouillés. Lève `DeuxClubs` si la fusion est impossible."""
    clubs = {
        c.etablissement_id: c
        for c in (
            await db.scalars(
                select(Club)
                .where(Club.etablissement_id.in_((absorbe_id, garde_id)), Club.etat.in_(CLUB_VIVANT))
                .order_by(Club.id)
                .with_for_update()
            )
        ).all()
    }
    absorbe, garde = clubs.get(absorbe_id), clubs.get(garde_id)
    if absorbe is not None and garde is not None and _au_dela(absorbe) and _au_dela(garde):
        raise DeuxClubs(absorbe, garde)
    return absorbe, garde


async def _verser(db: AsyncSession, source: Club, cible: Club, par: Utilisateur, adresse_ip: str | None) -> None:
    """Les affiliations et rattachements en cours de `source` passent, dans leur état, à `cible` ; `source` est clos."""
    for adhesion in (
        await db.scalars(
            select(Adhesion)
            .where(Adhesion.club_id == source.id, Adhesion.etat.in_(ADHESION_EN_COURS))
            .with_for_update()
        )
    ).all():
        adhesion.club_id = cible.id
    for rattachement in (
        await db.scalars(
            select(Rattachement)
            .where(Rattachement.club_id == source.id, Rattachement.etat.in_(RATTACHEMENT_EN_COURS))
            .with_for_update()
        )
    ).all():
        rattachement.club_id = cible.id
    source.etat = EtatClub.refuse
    source.motif_refus = "Établissement fusionné avec un autre du référentiel."
    source.regularisation_jusquau = None
    journaliser(
        db,
        "club_fusionne",
        par,
        cible_type="club",
        cible_id=source.id,
        details={"vers": str(cible.id)},
        adresse_ip=adresse_ip,
    )
    await db.flush()


async def fusionner_clubs(
    db: AsyncSession, absorbe_id: UUID, garde_id: UUID, par: Utilisateur, adresse_ip: str | None
) -> dict[str, str]:
    """Le club de l'absorbé suit le gardé (spec 042), dans la transaction de la fusion, après le déplacement des
    profils. Un club au-delà de « en constitution » est rattaché tel quel au gardé (même identifiant : ses membres,
    ses points et ses contenus le suivent) et recueille le club en constitution du gardé ; sinon le club en
    constitution de l'absorbé est clos et ses affiliations en cours rejoignent le club du gardé, créé au besoin.
    Renvoie ce qui a été fait, pour le journal."""
    absorbe, garde = await clubs_a_fusionner(db, absorbe_id, garde_id)
    if absorbe is None:
        return {"action": "aucun"}
    if _au_dela(absorbe):
        resultat = {"action": "rattache", "club_id": str(absorbe.id)}
        if garde is not None:
            await _verser(db, garde, absorbe, par, adresse_ip)
            resultat |= {"action": "rattache_et_clos", "clos_id": str(garde.id)}
        absorbe.etablissement_id = garde_id
        await db.flush()
        await activation.recalculer(db, absorbe.id, "etablissement_fusionne", par.id)
        return resultat
    restant = garde or await activation.club_de(db, garde_id)
    await _verser(db, absorbe, restant, par, adresse_ip)
    await activation.recalculer(db, restant.id, "etablissement_fusionne", par.id)
    return {"action": "clos", "club_id": str(restant.id), "clos_id": str(absorbe.id)}


async def redemander(db: AsyncSession, utilisateur: Utilisateur, adresse_ip: str) -> None:
    """Après un refus ou un retrait, l'élève redemande son affiliation au club de son établissement : elle repart
    « à confirmer ». Une seule affiliation en cours à la fois (index unique)."""
    eleve = await db.get(Eleve, utilisateur.id) if utilisateur.role is Role.eleve else None
    if eleve is None:
        raise Refus("Cet espace est réservé aux élèves.", 403)
    if await db.scalar(
        select(Adhesion.id).where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat.in_(ADHESION_EN_COURS))
    ):
        raise Refus("Ton affiliation est déjà en cours.", 409)
    try:
        adhesion = await affilier_eleve(db, utilisateur.id, eleve.etablissement_id)
    except IntegrityError:
        await db.rollback()
        raise Refus("Ton affiliation est déjà en cours.", 409) from None
    journaliser(
        db,
        "adhesion_redemandee",
        utilisateur,
        cible_type="adhesion",
        cible_id=adhesion.id,
        perimetre=await activation.dre_du_club(db, adhesion.club_id),
        details={"club_id": str(adhesion.club_id)},
        adresse_ip=adresse_ip,
    )
    await db.commit()
