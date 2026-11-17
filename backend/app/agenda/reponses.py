"""Réponses des membres, liste des réponses et pointage des présents (spec 041).

Les invités sont les membres dont l'adhésion au club est active et le compte actif, lus à chaque fois : un élève qui
rejoint le club peut répondre, un élève qui part n'est plus compté. Aucune de ces données n'est publique.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda.models import Evenement, Reponse, ReponseEvenement
from app.agenda.schemas import ReponseMembre, ReponsesEvenement
from app.agenda.service import _du_club, membres_actifs
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.moderation.service import Introuvable

FENETRE_POINTAGE = timedelta(days=30)


async def _membre(db: AsyncSession, club_id: UUID, eleve_id: UUID) -> bool:
    membres = membres_actifs(club_id).subquery()
    return bool(await db.scalar(select(func.count()).select_from(membres).where(membres.c.eleve_id == eleve_id)))


async def est_invite(db: AsyncSession, evenement: Evenement, utilisateur: Utilisateur) -> bool:
    if utilisateur.role is not Role.eleve or evenement.club_id is None:
        return False
    return await _membre(db, evenement.club_id, utilisateur.id)


async def ma_reponse(db: AsyncSession, evenement_id: UUID, eleve_id: UUID) -> Reponse | None:
    return await db.scalar(
        select(ReponseEvenement.reponse).where(
            ReponseEvenement.evenement_id == evenement_id, ReponseEvenement.eleve_id == eleve_id
        )
    )


async def participants(db: AsyncSession, evenement: Evenement) -> int:
    if evenement.club_id is None:
        return 0
    return int(
        await db.scalar(
            select(func.count())
            .select_from(ReponseEvenement)
            .where(
                ReponseEvenement.evenement_id == evenement.id,
                ReponseEvenement.reponse == Reponse.participe,
                ReponseEvenement.eleve_id.in_(membres_actifs(evenement.club_id)),
            )
        )
        or 0
    )


async def repondre(db: AsyncSession, utilisateur: Utilisateur, evenement_id: UUID, reponse: Reponse) -> Reponse:
    # Le verrou de l'événement sérialise les réponses : la dernière place ne se donne qu'une fois.
    evenement = await db.get(Evenement, evenement_id, with_for_update=True, populate_existing=True)
    if evenement is None or not evenement.publie:
        raise Introuvable
    if evenement.club_id is None or utilisateur.role is not Role.eleve:
        raise Refus("Seuls les membres du club organisateur répondent à cet événement.", 403)
    if not await _membre(db, evenement.club_id, utilisateur.id):
        raise Refus("Seuls les membres du club organisateur répondent à cet événement.", 403)
    if evenement.annule_le is not None:
        raise Refus("Cet événement est annulé.", 409)
    if evenement.debut <= datetime.now(UTC):
        raise Refus("Cet événement a commencé : les réponses sont closes.", 409)
    actuelle = await ma_reponse(db, evenement.id, utilisateur.id)
    if (
        reponse is Reponse.participe
        and actuelle is not Reponse.participe
        and evenement.places is not None
        and await participants(db, evenement) >= evenement.places
    ):
        raise Refus("Cet événement est complet. Tu peux répondre « Peut-être ».", 409)
    maintenant = datetime.now(UTC)
    await db.execute(
        insert(ReponseEvenement)
        .values(evenement_id=evenement.id, eleve_id=utilisateur.id, reponse=reponse, repondu_le=maintenant)
        .on_conflict_do_update(
            index_elements=[ReponseEvenement.evenement_id, ReponseEvenement.eleve_id],
            set_={"reponse": reponse, "repondu_le": maintenant},
        )
    )
    await db.commit()
    return reponse


# Liste des réponses et pointage (gestionnaires du club) -----------------------------------------------------


async def _evenement_du_club(db: AsyncSession, utilisateur: Utilisateur, evenement_id: UUID) -> Evenement:
    contenu = await _du_club(db, utilisateur, evenement_id)
    evenement = await db.get(Evenement, contenu.id, with_for_update=True, populate_existing=True)
    if evenement is None or not evenement.publie:
        raise Refus("Cet événement n'est pas publié.", 409)
    return evenement


def _pointage_ouvert(evenement: Evenement) -> bool:
    maintenant = datetime.now(UTC)
    return evenement.annule_le is None and evenement.debut <= maintenant <= evenement.fin + FENETRE_POINTAGE


async def reponses(db: AsyncSession, utilisateur: Utilisateur, evenement_id: UUID) -> ReponsesEvenement:
    evenement = await _evenement_du_club(db, utilisateur, evenement_id)
    assert evenement.club_id is not None
    membres = membres_actifs(evenement.club_id).subquery()
    lignes = (
        await db.execute(
            select(Utilisateur, Eleve.pseudonyme, ReponseEvenement)
            .join(membres, membres.c.eleve_id == Utilisateur.id)
            .join(Eleve, Eleve.utilisateur_id == Utilisateur.id)
            .outerjoin(
                ReponseEvenement,
                (ReponseEvenement.eleve_id == Utilisateur.id) & (ReponseEvenement.evenement_id == evenement.id),
            )
            .order_by(Utilisateur.nom, Utilisateur.prenom)
        )
    ).all()
    liste = [
        ReponseMembre(
            eleve_id=eleve.id,
            pseudonyme=pseudonyme,
            nom=f"{eleve.prenom} {eleve.nom}",
            reponse=reponse.reponse if reponse else None,
            present=reponse.present if reponse else None,
        )
        for eleve, pseudonyme, reponse in lignes
    ]
    await db.commit()
    return ReponsesEvenement(
        participe=sum(m.reponse is Reponse.participe for m in liste),
        peut_etre=sum(m.reponse is Reponse.peut_etre for m in liste),
        non=sum(m.reponse is Reponse.non for m in liste),
        sans_reponse=sum(m.reponse is None for m in liste),
        presents=sum(m.present is True for m in liste),
        pointage_ouvert=_pointage_ouvert(evenement),
        membres=liste,
    )


async def pointer(
    db: AsyncSession, utilisateur: Utilisateur, evenement_id: UUID, presences: dict[UUID, bool]
) -> ReponsesEvenement:
    evenement = await _evenement_du_club(db, utilisateur, evenement_id)
    assert evenement.club_id is not None
    if not _pointage_ouvert(evenement):
        raise Refus("Le pointage s'ouvre au début de l'événement et se ferme 30 jours après sa fin.", 409)
    membres = membres_actifs(evenement.club_id).subquery()
    connus = set((await db.scalars(select(membres.c.eleve_id).where(membres.c.eleve_id.in_(presences)))).all())
    if connus != set(presences):
        raise Refus("Seuls les membres du club peuvent être pointés.", 422)
    maintenant = datetime.now(UTC)
    for eleve_id, present in presences.items():
        await db.execute(
            insert(ReponseEvenement)
            .values(
                evenement_id=evenement.id, eleve_id=eleve_id, present=present, pointe_par=utilisateur.id,
                pointe_le=maintenant,
            )
            .on_conflict_do_update(
                index_elements=[ReponseEvenement.evenement_id, ReponseEvenement.eleve_id],
                set_={"present": present, "pointe_par": utilisateur.id, "pointe_le": maintenant},
            )
        )  # fmt: skip
    await db.commit()
    return await reponses(db, utilisateur, evenement_id)


# Lien avec un rapport d'activité (spec 038) -----------------------------------------------------------------


async def lier_au_rapport(db: AsyncSession, club_id: UUID, rapport_id: UUID, evenement_id: UUID) -> None:
    """Vérifie qu'un rapport d'activité peut documenter cet événement : publié, de son club, commencé, et lié à aucun
    autre rapport encore en vie. Un rapport refusé libère son événement. L'index unique tranche sous concurrence."""
    from app.moderation.models import Contenu, EtatContenu
    from app.rapports.models import Rapport

    evenement = await db.get(Evenement, evenement_id)
    if evenement is None or not evenement.publie or evenement.club_id != club_id:
        raise Refus("Champ « evenement_id » : choisis un événement publié de ton club.", 422)
    if evenement.debut > datetime.now(UTC):
        raise Refus("Champ « evenement_id » : cet événement n'a pas encore eu lieu.", 422)
    autre = await db.scalar(
        select(Rapport).where(Rapport.evenement_id == evenement_id, Rapport.contenu_id != rapport_id).with_for_update()
    )
    if autre is not None:
        etat = await db.scalar(select(Contenu.etat).where(Contenu.id == autre.contenu_id))
        if etat is not EtatContenu.refuse:
            raise Refus("Cet événement est déjà documenté par un autre rapport.", 409)
        autre.evenement_id = None
        await db.flush()


async def resume_pour_rapport(db: AsyncSession, evenement_id: UUID | None) -> dict[str, object] | None:
    """Ce que le rapport montre de son événement : titre, dates, réponses « Je participe » et présents pointés."""
    if evenement_id is None:
        return None
    evenement = await db.get(Evenement, evenement_id)
    if evenement is None:
        return None
    presents = await db.scalar(
        select(func.count())
        .select_from(ReponseEvenement)
        .where(ReponseEvenement.evenement_id == evenement.id, ReponseEvenement.present.is_(True))
    )
    return {
        "id": evenement.id,
        "titre": evenement.titre,
        "debut": evenement.debut,
        "fin": evenement.fin,
        "participants": await participants(db, evenement),
        "presents": int(presents or 0),
    }
