"""Moteur d'activation des clubs (spec 033, ADR-0011).

Le statut d'un club n'est écrit qu'ici, par `recalculer`, appelé dans la transaction de chaque événement qui change
ses effectifs. Le club est verrouillé pendant le calcul : deux événements simultanés passent l'un après l'autre, et le
journal n'a qu'une ligne par changement réel. Les lectures appliquent l'échéance elles-mêmes (`statut_effectif`) : un
club en régularisation dont l'échéance est passée est suspendu, même si personne ne l'a encore écrit.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

from sqlalchemy import ColumnElement, Select, and_, case, func, literal, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import (
    CLUB_EN_SERVICE,
    CLUB_VIVANT,
    Adhesion,
    Club,
    ClubStatut,
    EtatAdhesion,
    EtatClub,
    Rattachement,
)
from app.clubs.requetes import encadreurs_actifs
from app.comptes.models import StatutCompte, Utilisateur
from app.notifications.service import notifier
from app.referentiel.models import Etablissement, Iesg
from app.referentiel.normalisation import normaliser

# Fixés par le cahier des charges du 2026-11-10 ; les changer passe par une revue (spec 033, décision du plan).
SEUIL_ENCADREURS = 3
SEUIL_ELEVES = 21
DELAI_REGULARISATION = timedelta(days=15)

LIEN = "/mon-club-sante"


def maintenant() -> datetime:
    """L'heure du moteur ; les tests la remplacent."""
    return datetime.now(UTC)


# Lecture -----------------------------------------------------------------------------------------------------


def statut_effectif(club: Club, instant: datetime) -> EtatClub:
    if (
        club.etat is EtatClub.en_regularisation
        and club.regularisation_jusquau
        and club.regularisation_jusquau <= instant
    ):
        return EtatClub.suspendu
    return club.etat


def etat_effectif(instant: datetime) -> ColumnElement[str]:
    """`statut_effectif` en SQL, pour les lectures en lot."""
    return case(
        (
            and_(Club.etat == EtatClub.en_regularisation, Club.regularisation_jusquau <= instant),
            literal(EtatClub.suspendu.value),
        ),
        else_=Club.etat,
    )


def en_service(instant: datetime | None = None) -> ColumnElement[bool]:
    """Le club publie et gagne des points : actif, ou en régularisation dont l'échéance n'est pas passée."""
    instant = instant or maintenant()
    return and_(
        Club.etat.in_(CLUB_EN_SERVICE),
        or_(Club.regularisation_jusquau.is_(None), Club.regularisation_jusquau > instant),
    )


def est_en_service(club: Club, instant: datetime | None = None) -> bool:
    return statut_effectif(club, instant or maintenant()) in CLUB_EN_SERVICE


def eleves_comptes(club_id: UUID | ColumnElement[UUID]):
    """Les élèves qui comptent : affiliation confirmée, compte actif."""
    return (
        select(Adhesion.eleve_id)
        .join(Utilisateur, Utilisateur.id == Adhesion.eleve_id)
        .where(
            Adhesion.club_id == club_id,
            Adhesion.etat == EtatAdhesion.active,
            Utilisateur.statut == StatutCompte.actif,
        )
    )


def encadreurs_comptes(club_id: UUID | ColumnElement[UUID]) -> Select[tuple[UUID]]:
    """Les encadreurs qui comptent : rattachement actif, compte vérifié par l'équipe et actif (même règle que pour
    confirmer une passation, `requetes.encadreurs_actifs`)."""
    return encadreurs_actifs(club_id)  # type: ignore[arg-type]


def a_confirmer_sql(club_id: UUID | ColumnElement[UUID]) -> Select[tuple[int]]:
    """Le nombre d'affiliations à confirmer du club, comptes actifs seulement (comme la liste affichée)."""
    return (
        select(func.count())
        .select_from(Adhesion)
        .join(Utilisateur, Utilisateur.id == Adhesion.eleve_id)
        .where(
            Adhesion.club_id == club_id,
            Adhesion.etat == EtatAdhesion.en_attente_validation,
            Utilisateur.statut == StatutCompte.actif,
        )
    )


async def dre_du_club(db: AsyncSession, club_id: UUID) -> str | None:
    """Le code de la DRE du club : le périmètre de ses lignes au journal d'audit (ADR-0008)."""
    return await db.scalar(
        select(Iesg.dre_code)
        .join(Etablissement, Etablissement.iesg_id == Iesg.id)
        .join(Club, Club.etablissement_id == Etablissement.id)
        .where(Club.id == club_id)
    )


def nb_encadreurs_sql() -> ColumnElement[int]:
    """Le nombre d'encadreurs qui comptent, corrélé au club de la requête englobante (lectures en lot)."""
    return (
        encadreurs_comptes(Club.id)
        .with_only_columns(func.count(func.distinct(Rattachement.encadreur_id)))
        .correlate(Club)
        .scalar_subquery()
    )


def nb_eleves_sql() -> ColumnElement[int]:
    """Le nombre d'élèves qui comptent, corrélé au club de la requête englobante (lectures en lot)."""
    return (
        eleves_comptes(Club.id)
        .with_only_columns(func.count(func.distinct(Adhesion.eleve_id)))
        .correlate(Club)
        .scalar_subquery()
    )


async def effectifs(db: AsyncSession, club_id: UUID) -> tuple[int, int]:
    """(encadreurs, élèves) distincts qui comptent pour le seuil."""
    encadreurs = encadreurs_comptes(club_id).subquery()
    eleves = eleves_comptes(club_id).subquery()
    nb_encadreurs = await db.scalar(select(func.count(func.distinct(encadreurs.c.encadreur_id))))
    nb_eleves = await db.scalar(select(func.count(func.distinct(eleves.c.eleve_id))))
    return nb_encadreurs or 0, nb_eleves or 0


# Création ----------------------------------------------------------------------------------------------------


async def club_de(db: AsyncSession, etablissement_id: UUID) -> Club:
    """Le club vivant de l'établissement, créé « en constitution » s'il n'existe pas encore."""
    club = await db.scalar(select(Club).where(Club.etablissement_id == etablissement_id, Club.etat.in_(CLUB_VIVANT)))
    if club is not None:
        return club
    nom_etablissement = await db.scalar(select(Etablissement.nom).where(Etablissement.id == etablissement_id))
    if nom_etablissement is None:
        raise ValueError("Établissement inconnu")
    nom = f"Club Santé — {nom_etablissement}"[:150]
    cree = await db.scalar(
        insert(Club)
        .values(
            id=uuid7(),
            etablissement_id=etablissement_id,
            nom=nom,
            nom_normalise=normaliser(nom)[:150],
            etat=EtatClub.en_constitution,
        )
        .on_conflict_do_nothing(
            index_elements=["etablissement_id"],
            index_where=Club.etat.in_(CLUB_VIVANT),
        )
        .returning(Club.id)
    )
    if cree is not None:
        # La naissance du club ouvre son journal, comme pour les clubs repris par la migration.
        db.add(
            ClubStatut(
                id=uuid7(), club_id=cree, ancien=None, nouveau=EtatClub.en_constitution, cause="creation",
                nb_encadreurs=0, nb_eleves=0, cree_le=maintenant(),
            )
        )  # fmt: skip
        await db.flush()
    club = await db.scalar(
        select(Club)
        .where(Club.etablissement_id == etablissement_id, Club.etat.in_(CLUB_VIVANT))
        .execution_options(populate_existing=True)
    )
    assert club is not None
    return club


# Recalcul ----------------------------------------------------------------------------------------------------


def _suivant(ancien: EtatClub, au_seuil: bool) -> EtatClub:
    """La transition due aux effectifs ; l'échéance, elle, est appliquée avant par `recalculer`."""
    if au_seuil:
        return EtatClub.actif
    if ancien is EtatClub.actif:
        return EtatClub.en_regularisation
    return ancien


async def destinataires(db: AsyncSession, club: Club) -> list[UUID]:
    """Les encadreurs qui comptent et le président : ceux que les changements de statut concernent."""
    ids = list(await db.scalars(encadreurs_comptes(club.id).distinct()))
    if club.president_id is not None and club.president_id not in ids:
        ids.append(club.president_id)
    return ids


def _date(instant: datetime) -> str:
    return instant.strftime("%d/%m/%Y")


async def _prevenir(db: AsyncSession, club: Club, nouveau: EtatClub) -> None:
    match nouveau:
        case EtatClub.actif:
            type_, titre, message = (
                "club_active",
                f"{club.nom} est actif",
                "Ton club a atteint 3 encadreurs et 21 élèves.",
            )
        case EtatClub.en_regularisation:
            assert club.regularisation_jusquau is not None
            type_, titre = "club_en_regularisation", f"{club.nom} est en régularisation"
            message = (
                f"Le club est passé sous le seuil de 3 encadreurs et 21 élèves. Il a jusqu'au "
                f"{_date(club.regularisation_jusquau)} pour le retrouver, sinon il sera suspendu."
            )
        case EtatClub.suspendu:
            type_, titre = "club_suspendu", f"{club.nom} est suspendu"
            message = "Le club n'a pas retrouvé son seuil à temps. Il redeviendra actif dès qu'il l'atteindra."
        case _:
            return
    for utilisateur_id in await destinataires(db, club):
        notifier(db, utilisateur_id, type_, titre, message, LIEN)


async def _transition(
    db: AsyncSession,
    club: Club,
    nouveau: EtatClub,
    cause: str,
    effectifs_: tuple[int, int],
    par: UUID | None,
    instant: datetime,
) -> None:
    ancien = club.etat
    club.etat = nouveau
    if nouveau is EtatClub.actif and club.actif_le is None:
        club.actif_le = instant
    if nouveau is EtatClub.en_regularisation:
        club.regularisation_jusquau = instant + DELAI_REGULARISATION
        club.rappels_envoyes = 0
    else:
        club.regularisation_jusquau = None
    db.add(
        ClubStatut(
            id=uuid7(),
            club_id=club.id,
            ancien=ancien,
            nouveau=nouveau,
            cause=cause,
            nb_encadreurs=effectifs_[0],
            nb_eleves=effectifs_[1],
            par=par,
            cree_le=instant,
        )
    )
    await db.flush()
    await _prevenir(db, club, nouveau)


async def recalculer(db: AsyncSession, club_id: UUID, cause: str, par: UUID | None = None) -> EtatClub:
    """Recompte les membres du club et applique la transition qui en découle. Ne valide pas la transaction."""
    club = await db.scalar(
        select(Club).where(Club.id == club_id).with_for_update().execution_options(populate_existing=True)
    )
    if club is None:
        raise ValueError("Club inconnu")
    if club.etat not in CLUB_VIVANT:
        return club.etat
    instant = maintenant()
    compte = await effectifs(db, club.id)
    au_seuil = compte[0] >= SEUIL_ENCADREURS and compte[1] >= SEUIL_ELEVES
    # Une échéance passée mais pas encore écrite s'inscrit d'abord au journal avec sa vraie cause : l'événement qui
    # la révèle n'en est pas la raison.
    if statut_effectif(club, instant) is EtatClub.suspendu and club.etat is EtatClub.en_regularisation:
        await _transition(db, club, EtatClub.suspendu, "echeance", compte, None, instant)
    nouveau = _suivant(club.etat, au_seuil)
    if nouveau is not club.etat:
        await _transition(db, club, nouveau, cause, compte, par, instant)
    return club.etat


async def recalculer_etablissement(
    db: AsyncSession, etablissement_id: UUID | None, cause: str, par: UUID | None = None
) -> None:
    """Recalcule le club vivant de l'établissement, s'il en a un."""
    if etablissement_id is None:
        return
    club_id = await db.scalar(
        select(Club.id).where(Club.etablissement_id == etablissement_id, Club.etat.in_(CLUB_VIVANT))
    )
    if club_id is not None:
        await recalculer(db, club_id, cause, par)
