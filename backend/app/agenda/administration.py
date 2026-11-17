"""Événements nationaux et régionaux de l'équipe (spec 041) : publiés dès leur création, sans modération ni points,
chaque action journalisée. Un collaborateur de DRE ne gère que les événements régionaux de sa DRE."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.agenda.models import Evenement, NiveauEvenement
from app.agenda.public import vue_publique
from app.agenda.schemas import EvenementEquipeEntree, EvenementPublic
from app.agenda.service import annuler_evenement, copier, verifier_axe
from app.comptes.inscription import Refus
from app.moderation.service import Introuvable
from app.referentiel.models import Dre


def _dans_le_perimetre(acces: Acces, evenement: Evenement) -> bool:
    return acces.national or (
        evenement.dre_code is not None and evenement.dre_code == acces.collaborateur.perimetre_dre
    )


async def _verifier_niveau(db: AsyncSession, acces: Acces, entree: EvenementEquipeEntree) -> None:
    if entree.niveau is NiveauEvenement.national and not acces.national:
        raise Refus("Un événement national est créé par un collaborateur de niveau national.", 403)
    if entree.niveau is NiveauEvenement.regional:
        if entree.dre_code is None or await db.get(Dre, entree.dre_code) is None:
            raise Refus("Cette DRE n'existe pas.", 422)
        if not acces.national and entree.dre_code != acces.collaborateur.perimetre_dre:
            raise Refus("Tu ne gères que les événements de ta DRE.", 403)


async def lister(
    db: AsyncSession, acces: Acces, periode: Literal["a_venir", "passe"] = "a_venir"
) -> list[EvenementPublic]:
    maintenant = datetime.now(UTC)
    requete = select(Evenement)
    if periode == "a_venir":
        requete = requete.where(Evenement.fin > maintenant).order_by(Evenement.debut, Evenement.id)
    else:
        requete = requete.where(Evenement.fin <= maintenant).order_by(Evenement.debut.desc(), Evenement.id)
    if not acces.national:
        requete = requete.where(Evenement.dre_code == acces.collaborateur.perimetre_dre)
    return [await vue_publique(db, e) for e in (await db.scalars(requete.limit(200))).all()]


async def creer(db: AsyncSession, acces: Acces, entree: EvenementEquipeEntree, ip: str) -> EvenementPublic:
    await _verifier_niveau(db, acces, entree)
    await verifier_axe(db, entree.champs.model_dump())
    evenement = Evenement(niveau=entree.niveau, dre_code=entree.dre_code, publie=True, cree_par=acces.utilisateur.id)
    copier(evenement, entree.champs)
    db.add(evenement)
    await db.flush()
    journaliser(
        db, "evenement_cree", acces.utilisateur, cible_type="evenement", cible_id=evenement.id,
        perimetre=evenement.dre_code or "national", details={"niveau": evenement.niveau.value}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await vue_publique(db, evenement)


async def _de_lequipe(db: AsyncSession, acces: Acces, evenement_id: UUID) -> Evenement:
    evenement = await db.get(Evenement, evenement_id, with_for_update=True, populate_existing=True)
    if evenement is None or not _dans_le_perimetre(acces, evenement):
        raise Introuvable
    return evenement


async def modifier(
    db: AsyncSession, acces: Acces, evenement_id: UUID, entree: EvenementEquipeEntree, ip: str
) -> EvenementPublic:
    evenement = await _de_lequipe(db, acces, evenement_id)
    if evenement.niveau is NiveauEvenement.club:
        raise Refus("Un événement de club se modifie par son auteur, puis repasse en modération.", 409)
    if evenement.annule_le is not None:
        raise Refus("Cet événement est annulé.", 409)
    await _verifier_niveau(db, acces, entree)
    await verifier_axe(db, entree.champs.model_dump(), evenement.axe_code)
    evenement.niveau = entree.niveau
    evenement.dre_code = entree.dre_code
    copier(evenement, entree.champs)
    # Un report à un autre jour rouvre le rappel (sans effet pour un événement de l'équipe, qui n'invite personne).
    evenement.rappel_pour = None
    journaliser(
        db, "evenement_modifie", acces.utilisateur, cible_type="evenement", cible_id=evenement.id,
        perimetre=evenement.dre_code or "national", details={"niveau": evenement.niveau.value}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await vue_publique(db, evenement)


async def annuler(db: AsyncSession, acces: Acces, evenement_id: UUID, motif: str, ip: str) -> EvenementPublic:
    evenement = await _de_lequipe(db, acces, evenement_id)
    # Un événement de club se retire avec le droit de dépublier de l'agenda ; ceux de l'équipe avec celui de modifier.
    droit = Action.depublier if evenement.niveau is NiveauEvenement.club else Action.modifier
    if not acces.a("agenda", droit):
        raise Refus("Tu n'as pas le droit d'annuler cet événement.", 403)
    await annuler_evenement(db, evenement, acces.utilisateur, motif, ip, perimetre=evenement.dre_code or "national")
    await db.commit()
    return await vue_publique(db, evenement)
