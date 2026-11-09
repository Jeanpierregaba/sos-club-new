"""Jouer aux quiz sans compte (spec 031), depuis la page des jeux.

À sa première partie, le joueur reçoit un compte « invite » sans e-mail ni mot de passe, reconnu par un cookie à
part du cookie de session : il ne se connecte à rien d'autre. Le serveur arbitre ses parties comme les autres
(ADR-0004), sans points. Deux quiz au plus ; au-delà, il crée un compte visiteur. Effacé au bout de 7 jours.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, Session, StatutCompte, TentativeConnexion, Utilisateur
from app.comptes.service import _purger_vieux_essais, empreinte, utilisateur_de_la_session
from app.quiz.models import ReponseQuiz, TentativeQuiz

COOKIE = "sosclub_invite"
LIMITE_QUIZ = 2
DUREE = timedelta(days=7)
# Une salle informatique partage une adresse : la limite freine seulement qui efface ses cookies en boucle.
CLE_LIMITE = "invite"
INVITES_PAR_HEURE = 30
MESSAGE_LIMITE = (
    f"Tu as joué tes {LIMITE_QUIZ} quiz gratuits. Crée ton compte visiteur pour continuer à jouer : c'est gratuit."
)


class LimiteAtteinte(Exception):
    pass


class TropDInvites(Exception):
    pass


async def invite_du_cookie(db: AsyncSession, jeton: str | None) -> Utilisateur | None:
    if not jeton:
        return None
    utilisateur = await utilisateur_de_la_session(db, jeton)
    if utilisateur is None or utilisateur.role is not Role.invite or utilisateur.statut is not StatutCompte.actif:
        return None
    return utilisateur


async def nouvel_invite(db: AsyncSession, adresse_ip: str) -> tuple[Utilisateur, str]:
    """Crée le joueur et sa session de 7 jours ; renvoie le jeton du cookie. Valide la transaction."""
    await _purger_vieux_essais(db)
    recents = await db.scalar(
        select(func.count())
        .select_from(TentativeConnexion)
        .where(
            TentativeConnexion.cle_hash == CLE_LIMITE,
            TentativeConnexion.adresse_ip == adresse_ip,
            TentativeConnexion.cree_le > datetime.now(UTC) - timedelta(hours=1),
        )
    )
    if (recents or 0) >= INVITES_PAR_HEURE:
        raise TropDInvites
    db.add(TentativeConnexion(cle_hash=CLE_LIMITE, adresse_ip=adresse_ip, en_cours=True))
    invite = Utilisateur(
        role=Role.invite,
        identifiant=f"i.{secrets.token_hex(8)}",
        prenom="Joueur",
        nom="sans compte",
        # Aucune empreinte valable : aucune connexion par mot de passe n'est possible.
        mot_de_passe_hash="",
    )
    db.add(invite)
    await db.flush()
    jeton = secrets.token_urlsafe(32)
    db.add(Session(utilisateur_id=invite.id, jeton_hash=empreinte(jeton), expire_le=datetime.now(UTC) + DUREE))
    await db.commit()
    return invite, jeton


async def quiz_joues(db: AsyncSession, invite: Utilisateur) -> int:
    """Le nombre de quiz différents lancés : rejouer un quiz déjà commencé ne compte pas une seconde fois."""
    return int(
        await db.scalar(
            select(func.count(func.distinct(TentativeQuiz.quiz_id))).where(
                TentativeQuiz.joueur_id == invite.id, TentativeQuiz.essai.is_(False)
            )
        )
        or 0
    )


async def verifier_limite(db: AsyncSession, invite: Utilisateur, quiz_id: object) -> None:
    """Verrouille le joueur : deux lancements simultanés de quiz différents ne dépassent pas la limite."""
    await db.execute(select(Utilisateur.id).where(Utilisateur.id == invite.id).with_for_update(key_share=True))
    deja = await db.scalar(
        select(TentativeQuiz.id).where(TentativeQuiz.joueur_id == invite.id, TentativeQuiz.quiz_id == quiz_id).limit(1)
    )
    if deja is None and await quiz_joues(db, invite) >= LIMITE_QUIZ:
        raise LimiteAtteinte


async def purger(db: AsyncSession) -> int:
    """Efface les joueurs sans compte de plus de 7 jours, avec leurs parties."""
    limite = datetime.now(UTC) - DUREE
    anciens = select(Utilisateur.id).where(Utilisateur.role == Role.invite, Utilisateur.cree_le < limite)
    tentatives = select(TentativeQuiz.id).where(TentativeQuiz.joueur_id.in_(anciens))
    await db.execute(delete(ReponseQuiz).where(ReponseQuiz.tentative_id.in_(tentatives)))
    await db.execute(delete(TentativeQuiz).where(TentativeQuiz.joueur_id.in_(anciens)))
    resultat = await db.execute(delete(Utilisateur).where(Utilisateur.id.in_(anciens)))
    await db.commit()
    return int(getattr(resultat, "rowcount", 0) or 0)
