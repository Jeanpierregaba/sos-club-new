"""L'agenda public (spec 041) : seulement les événements publiés, sans aucun nom ni pseudonyme d'élève.

Il ne lit que la table `evenement` : la copie approuvée d'un événement de club, ou un événement de l'équipe.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda.models import Evenement, NiveauEvenement, TypeEvenement
from app.agenda.reponses import est_invite, ma_reponse, participants
from app.agenda.schemas import EvenementPublic, PageAgenda
from app.clubs.models import Adhesion, Club, EtatAdhesion
from app.comptes.models import Utilisateur
from app.moderation.service import Introuvable
from app.referentiel.models import Dre, Etablissement

PAR_PAGE = 50
PROCHAINS = 3


def _publies() -> Select[tuple[Evenement]]:
    return select(Evenement).where(Evenement.publie)


async def vue_publique(db: AsyncSession, evenement: Evenement, moi: Utilisateur | None = None) -> EvenementPublic:
    club = await db.get(Club, evenement.club_id) if evenement.club_id else None
    etablissement = await db.get(Etablissement, club.etablissement_id) if club else None
    dre = await db.get(Dre, evenement.dre_code) if evenement.dre_code else None
    nombre = await participants(db, evenement)
    invite = moi is not None and await est_invite(db, evenement, moi)
    return EvenementPublic(
        id=evenement.id,
        niveau=evenement.niveau,
        type=evenement.type,
        axe_code=evenement.axe_code,
        titre=evenement.titre,
        objectif=evenement.objectif,
        description=evenement.description,
        lieu=evenement.lieu,
        en_ligne=evenement.en_ligne,
        lien=evenement.lien,
        public_vise=evenement.public_vise,
        debut=evenement.debut,
        fin=evenement.fin,
        places=evenement.places,
        participants=nombre,
        complet=evenement.places is not None and nombre >= evenement.places,
        annule=evenement.annule_le is not None,
        motif_annulation=evenement.motif_annulation,
        dre_code=evenement.dre_code,
        dre=dre.nom if dre else None,
        club_id=evenement.club_id,
        club=club.nom if club else None,
        etablissement=etablissement.nom if etablissement else None,
        peut_repondre=invite and evenement.annule_le is None and evenement.debut > datetime.now(UTC),
        ma_reponse=await ma_reponse(db, evenement.id, moi.id) if invite and moi is not None else None,
    )


async def lister(
    db: AsyncSession,
    *,
    periode: Literal["a_venir", "passe"] = "a_venir",
    dre: str | None = None,
    club: UUID | None = None,
    type: TypeEvenement | None = None,
    axe: str | None = None,
    niveau: NiveauEvenement | None = None,
    page: int = 1,
) -> PageAgenda:
    maintenant = datetime.now(UTC)
    requete = _publies()
    if periode == "a_venir":
        requete = requete.where(Evenement.fin > maintenant).order_by(Evenement.debut, Evenement.id)
    else:
        requete = requete.where(Evenement.fin <= maintenant).order_by(Evenement.debut.desc(), Evenement.id)
    if dre:
        requete = requete.where(Evenement.dre_code == dre)
    if club:
        requete = requete.where(Evenement.club_id == club)
    if type:
        requete = requete.where(Evenement.type == type)
    if axe:
        requete = requete.where(Evenement.axe_code == axe)
    if niveau:
        requete = requete.where(Evenement.niveau == niveau)
    total = await db.scalar(select(func.count()).select_from(requete.order_by(None).subquery()))
    lignes = (await db.scalars(requete.limit(PAR_PAGE).offset((max(page, 1) - 1) * PAR_PAGE))).all()
    return PageAgenda(total=total or 0, evenements=[await vue_publique(db, e) for e in lignes])


async def prochains(db: AsyncSession) -> list[EvenementPublic]:
    lignes = (
        await db.scalars(
            _publies()
            .where(Evenement.debut > datetime.now(UTC), Evenement.annule_le.is_(None))
            .order_by(Evenement.debut, Evenement.id)
            .limit(PROCHAINS)
        )
    ).all()
    return [await vue_publique(db, e) for e in lignes]


async def detail(db: AsyncSession, evenement_id: UUID, moi: Utilisateur | None) -> EvenementPublic:
    evenement = await db.get(Evenement, evenement_id)
    if evenement is None or not evenement.publie:
        raise Introuvable
    return await vue_publique(db, evenement, moi)


async def mes_evenements(db: AsyncSession, moi: Utilisateur) -> list[EvenementPublic]:
    """Les événements publiés à venir du club de l'élève (adhésion active), avec sa réponse."""
    club_id = await db.scalar(
        select(Adhesion.club_id).where(Adhesion.eleve_id == moi.id, Adhesion.etat == EtatAdhesion.active)
    )
    if club_id is None:
        return []
    lignes = (
        await db.scalars(
            _publies()
            .where(Evenement.club_id == club_id, Evenement.fin > datetime.now(UTC))
            .order_by(Evenement.debut, Evenement.id)
        )
    ).all()
    return [await vue_publique(db, e, moi) for e in lignes]
