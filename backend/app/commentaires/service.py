"""Commentaires prémodérés (spec 025) : un type du moteur de modération (ADR-0009), rattaché à un article publié.

Un commentaire s'envoie en une fois (création et soumission dans la même transaction), sans brouillon ni
modification ensuite ; son auteur peut le retirer. Rien n'est public avant l'approbation. Plafonds par auteur et
par jour UTC d'envoi (le Togo est à UTC+0) : 20 envois, dont 5 rémunérés (Q22).
"""

import math
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Select, String, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.articles import public
from app.articles.service import TYPE as ARTICLE
from app.commentaires.schemas import (
    ArticleCommente,
    CommentaireAuteur,
    CommentairePublic,
    CommentairesPublics,
    MesCommentaires,
)
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.moderation import service as moteur
from app.moderation.models import Contenu, DecisionModeration, EtatContenu, EtatVersion, VersionContenu
from app.moderation.types import TypeContenu, enregistrer
from app.notifications.service import notifier
from app.points.bareme import COMMENTAIRE_ELEVE, COMMENTAIRE_ENCADREUR
from app.points.models import MouvementPoints

TYPE = "commentaire"
ENVOIS_PAR_JOUR = 20
REMUNERES_PAR_JOUR = 5
PAR_PAGE = 50
LIMITE_MIENS = 200
# Un double clic, ou un réseau qui renvoie la requête, ne fait qu'un commentaire.
DELAI_DOUBLON = timedelta(minutes=1)
LONGUEUR_EXTRAIT = 60


class ChampsCommentaire(BaseModel):
    texte: str
    # Comme pour un article (Q20) : un élève choisit d'afficher son club à côté de son pseudonyme.
    afficher_club: bool = True


def extrait(texte: str) -> str:
    """Le début du commentaire, sur une ligne : il sert de titre dans la file et les notifications."""
    ligne = " ".join(texte.split())
    return ligne if len(ligne) <= LONGUEUR_EXTRAIT else f"{ligne[: LONGUEUR_EXTRAIT - 1].rstrip()}…"


def _jour(instant: datetime) -> tuple[datetime, datetime]:
    debut = instant.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return debut, debut + timedelta(days=1)


async def _points_permis(db: AsyncSession, contenu: Contenu) -> bool:
    """Moins de 5 commentaires de l'auteur, envoyés le même jour, ont déjà rapporté des points. Appelée à
    l'approbation, sous le verrou de l'auteur : deux approbations simultanées ne dépassent pas le plafond."""
    debut, fin = _jour(contenu.cree_le)
    remuneres = await db.scalar(
        select(func.count())
        .select_from(Contenu)
        .join(MouvementPoints, MouvementPoints.cle == func.concat(f"{TYPE}:", cast(Contenu.id, String)))
        .where(
            Contenu.auteur_id == contenu.auteur_id,
            Contenu.type == TYPE,
            Contenu.cree_le >= debut,
            Contenu.cree_le < fin,
        )
    )
    return (remuneres or 0) < REMUNERES_PAR_JOUR


async def _titre_article(db: AsyncSession, article: Contenu) -> str:
    version = await db.get(VersionContenu, article.version_publiee_id) if article.version_publiee_id else None
    return str(version.donnees.get("titre", "")) if version else ""


async def _prevenir_redacteur(db: AsyncSession, contenu: Contenu) -> None:
    """À la première publication, l'auteur de l'article apprend qu'on l'a commenté (sauf s'il s'est commenté)."""
    article = await db.get(Contenu, contenu.parent_id) if contenu.parent_id else None
    # Article hors ligne (dépublié pendant l'attente) : le commentaire ne se lit pas encore, rien à annoncer.
    if article is None or article.auteur_id == contenu.auteur_id or article.version_publiee_id is None:
        return
    titre = await _titre_article(db, article)
    notifier(
        db,
        article.auteur_id,
        "article_commentaire",
        f"Nouveau commentaire sur ton article « {titre} »",
        None,
        f"/articles/{article.adresse}" if article.adresse else None,
    )


COMMENTAIRE = enregistrer(
    TypeContenu(
        code=TYPE,
        libelle="commentaire",
        schema=ChampsCommentaire,
        actions_auteur={Role.eleve: COMMENTAIRE_ELEVE, Role.encadreur: COMMENTAIRE_ENCADREUR},
        titre=lambda donnees: extrait(str(donnees["texte"])),
        lien_auteur=lambda _contenu_id: "/mes-commentaires",
        adresse=False,
        correction=False,
        points_permis=_points_permis,
        a_la_publication=_prevenir_redacteur,
    )
)


async def _article_publie(db: AsyncSession, adresse: str) -> Contenu:
    article = await db.scalar(
        select(Contenu).where(
            Contenu.adresse == adresse, Contenu.type == ARTICLE, Contenu.version_publiee_id.is_not(None)
        )
    )
    if article is None:
        raise moteur.Introuvable
    return article


# Envoi ---------------------------------------------------------------------------------------------------------


async def envoyer(
    db: AsyncSession, auteur: Utilisateur, adresse: str, texte: str, afficher_club: bool, adresse_ip: str
) -> tuple[CommentaireAuteur, bool]:
    """Crée et soumet le commentaire ; renvoie aussi faux s'il s'agissait d'un double envoi (le même commentaire)."""
    article = await _article_publie(db, adresse)
    # Sous le verrou de l'auteur : le doublon et le plafond du jour se comptent sans course.
    await moteur.verrouiller_auteur(db, auteur)
    maintenant = datetime.now(UTC)
    doublon = await db.scalar(
        select(Contenu)
        .join(VersionContenu, VersionContenu.contenu_id == Contenu.id)
        .where(
            Contenu.auteur_id == auteur.id,
            Contenu.type == TYPE,
            Contenu.parent_id == article.id,
            Contenu.etat != EtatContenu.retire,
            Contenu.cree_le > maintenant - DELAI_DOUBLON,
            VersionContenu.donnees["texte"].astext == texte,
        )
        .limit(1)
    )
    if doublon is not None:
        return await commentaire_auteur(db, doublon), False
    debut, _fin = _jour(maintenant)
    envoyes = await db.scalar(
        select(func.count())
        .select_from(Contenu)
        .where(Contenu.auteur_id == auteur.id, Contenu.type == TYPE, Contenu.cree_le >= debut)
    )
    if (envoyes or 0) >= ENVOIS_PAR_JOUR:
        raise Refus(f"Tu as déjà envoyé {ENVOIS_PAR_JOUR} commentaires aujourd'hui : réessaie demain.", 429)
    donnees = ChampsCommentaire(texte=texte, afficher_club=afficher_club).model_dump()
    contenu = await moteur.creer(db, auteur, TYPE, donnees, parent_id=article.id)
    await moteur.soumettre(db, contenu, auteur, adresse_ip)
    await db.commit()
    return await commentaire_auteur(db, contenu), True


# Auteur --------------------------------------------------------------------------------------------------------

_Article = aliased(Contenu)
_VersionArticle = aliased(VersionContenu)
# Le titre de la dernière version approuvée de l'article : jamais un brouillon de son auteur, que le commentateur
# n'a pas à lire (ADR-0009).
_titre = (
    select(_VersionArticle.donnees["titre"].astext)
    .where(_VersionArticle.contenu_id == _Article.id, _VersionArticle.etat == EtatVersion.approuvee)
    .order_by(_VersionArticle.numero.desc())
    .limit(1)
    .correlate(_Article)
    .scalar_subquery()
)
_motif = (
    select(DecisionModeration.motif)
    .where(DecisionModeration.contenu_id == Contenu.id)
    .order_by(DecisionModeration.decide_le.desc(), DecisionModeration.id.desc())
    .limit(1)
    .correlate(Contenu)
    .scalar_subquery()
)


def _miens() -> Select[tuple[Contenu, VersionContenu, str | None, str | None, str | None]]:
    # Un commentaire n'a qu'une version : il ne se modifie pas après l'envoi.
    return (
        # L'adresse seulement si l'article est en ligne : sinon le lien mènerait à une page introuvable.
        select(
            Contenu,
            VersionContenu,
            case((_Article.version_publiee_id.is_not(None), _Article.adresse)),
            _titre,
            _motif,
        )
        .join(VersionContenu, (VersionContenu.contenu_id == Contenu.id) & (VersionContenu.numero == 1))
        .join(_Article, _Article.id == Contenu.parent_id)
        .where(Contenu.type == TYPE)
    )


def _auteur(
    contenu: Contenu, version: VersionContenu, adresse: str | None, titre: str | None, motif: str | None
) -> CommentaireAuteur:
    return CommentaireAuteur(
        id=contenu.id,
        texte=str(version.donnees["texte"]),
        etat=contenu.etat,
        cree_le=contenu.cree_le,
        publie_le=contenu.publie_le,
        article=ArticleCommente(adresse=adresse, titre=titre or ""),
        motif=motif if contenu.etat in {EtatContenu.refuse, EtatContenu.depublie} else None,
    )


async def commentaire_auteur(db: AsyncSession, contenu: Contenu) -> CommentaireAuteur:
    ligne = (await db.execute(_miens().where(Contenu.id == contenu.id))).one()
    return _auteur(*ligne)


async def mes_commentaires(db: AsyncSession, auteur: Utilisateur, adresse: str | None) -> MesCommentaires:
    requete = _miens().where(Contenu.auteur_id == auteur.id)
    if adresse:
        requete = requete.where(_Article.adresse == adresse)
    lignes = await db.execute(requete.order_by(Contenu.cree_le.desc(), Contenu.id.desc()).limit(LIMITE_MIENS))
    return MesCommentaires(commentaires=[_auteur(*ligne) for ligne in lignes])


async def retirer(db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, adresse_ip: str) -> None:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, TYPE, verrouiller=True)
    await moteur.retirer_definitivement(db, contenu, auteur, adresse_ip)
    await db.commit()


# Lecture publique ----------------------------------------------------------------------------------------------


async def lister(db: AsyncSession, adresse: str, page: int) -> CommentairesPublics:
    """Les commentaires publiés d'un article publié, du plus ancien au plus récent."""
    article = await _article_publie(db, adresse)
    filtre = (Contenu.type == TYPE, Contenu.parent_id == article.id, Contenu.version_publiee_id.is_not(None))
    total = (await db.scalar(select(func.count()).select_from(Contenu).where(*filtre))) or 0
    lignes = await db.execute(
        select(Contenu, VersionContenu)
        .join(VersionContenu, VersionContenu.id == Contenu.version_publiee_id)
        .where(*filtre)
        .order_by(Contenu.publie_le, Contenu.id)
        .offset((page - 1) * PAR_PAGE)
        .limit(PAR_PAGE)
    )
    # Une signature par auteur : un même élève qui commente souvent ne coûte qu'une lecture.
    signatures: dict[Any, Any] = {}
    commentaires = []
    for contenu, version in lignes:
        if contenu.auteur_id not in signatures:
            signatures[contenu.auteur_id] = await public.signature(db, contenu)
        assert contenu.publie_le is not None
        commentaires.append(
            CommentairePublic(
                id=contenu.id,
                texte=str(version.donnees["texte"]),
                signature=signatures[contenu.auteur_id],
                publie_le=contenu.publie_le,
            )
        )
    return CommentairesPublics(
        commentaires=commentaires, page=page, pages=max(1, math.ceil(total / PAR_PAGE)), total=total
    )
