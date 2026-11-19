"""Partages d'articles vérifiés (spec 044, R17) : un type du moteur de modération (ADR-0009), rattaché à l'article
partagé comme un commentaire.

Une déclaration se crée et se soumet en une fois. Sa nature est fixée à la déclaration : « partage » quand la personne
est l'autrice de l'article (+50 par réseau distinct), « republication » sinon (+10 une fois par article). Aucun point
avant la décision d'un modérateur, qui ouvre lui-même le lien : l'API ne le visite jamais. Plafond : 3 déclarations
par jour UTC (l'heure de Lomé), refusées comprises.
"""

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.articles.service import TYPE as ARTICLE
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.moderation import service as moteur
from app.moderation.models import Contenu, DecisionModeration, EtatContenu, EtatVersion, VersionContenu
from app.moderation.types import TypeContenu, enregistrer
from app.partages.schemas import (
    LIEN_MAX,
    ChampsPartage,
    EtatPartagesArticle,
    MesPartages,
    Nature,
    PartageAuteur,
    ReseauPartage,
)
from app.points import service as points
from app.points.models import MouvementPoints

TYPE = "partage"
PAR_JOUR = 3
LIMITE_MIENS = 200
# Les domaines de chaque réseau ; un sous-domaine en fait partie (www., m., vm.…).
DOMAINES: dict[ReseauPartage, tuple[str, ...]] = {
    ReseauPartage.facebook: ("facebook.com", "fb.com", "fb.watch"),
    ReseauPartage.instagram: ("instagram.com",),
    ReseauPartage.tiktok: ("tiktok.com",),
    ReseauPartage.linkedin: ("linkedin.com", "lnkd.in"),
}
NOMS = {
    ReseauPartage.facebook: "Facebook",
    ReseauPartage.instagram: "Instagram",
    ReseauPartage.tiktok: "TikTok",
    ReseauPartage.linkedin: "LinkedIn",
}
# Une déclaration « vivante » : en attente ou approuvée. Un refus libère le réseau, l'article et le lien.
VIVANTS = (EtatContenu.en_attente, EtatContenu.publie)
ETATS = {EtatContenu.en_attente: "en_attente", EtatContenu.publie: "approuve", EtatContenu.refuse: "refuse"}


def verifier_lien(reseau: ReseauPartage, lien: str) -> str:
    """Le lien d'une publication du réseau choisi, en https. Il n'est jamais visité : seul son texte est contrôlé."""
    lien = lien.strip()
    if len(lien) > LIEN_MAX:
        raise Refus(f"Le lien fait plus de {LIEN_MAX} caractères.", 422)
    try:
        morceaux = urlsplit(lien)
    except ValueError:
        raise Refus("Ce lien n'est pas valide.", 422) from None
    hote = (morceaux.hostname or "").lower().rstrip(".")
    if morceaux.scheme != "https" or not hote or morceaux.username or morceaux.password:
        raise Refus("Colle le lien complet de ta publication, qui commence par https://.", 422)
    if not any(hote == domaine or hote.endswith(f".{domaine}") for domaine in DOMAINES[reseau]):
        raise Refus(f"Ce lien n'est pas une publication {NOMS[reseau]}.", 422)
    return lien


def cle_points(nature: Nature, article_id: UUID, auteur_id: UUID, reseau: ReseauPartage) -> str:
    """La clé du registre : une ligne au plus par article et par personne (et par réseau pour un partage)."""
    if nature == "partage":
        return f"partage:{article_id}:{auteur_id}:{reseau.value}"
    return f"republication:{article_id}:{auteur_id}"


def _titre(donnees: dict[str, Any]) -> str:
    nature = "Partage" if donnees["nature"] == "partage" else "Republication"
    return f"{nature} sur {NOMS[ReseauPartage(donnees['reseau'])]}"


async def _crediter(db: AsyncSession, contenu: Contenu, valide_par: UUID) -> None:
    """À la première approbation : +10 (republication) ou +50 (partage) au barème actuel, sous une clé propre à
    l'article, à la personne et au réseau. Un article retiré du site entre-temps rend l'approbation impossible."""
    article = await db.get(Contenu, contenu.parent_id) if contenu.parent_id else None
    if article is None or article.version_publiee_id is None:
        raise Refus("L'article n'est plus en ligne : refuse ce partage.", 409)
    auteur = await db.get(Utilisateur, contenu.auteur_id)
    version = await db.get(VersionContenu, contenu.version_publiee_id)
    assert auteur is not None and version is not None
    champs = ChampsPartage.model_validate(version.donnees)
    action = f"{auteur.role.value}.{champs.nature}"
    await points.crediter(
        db, action, auteur.id, cle_points(champs.nature, article.id, auteur.id, champs.reseau), valide_par=valide_par
    )


PARTAGE = enregistrer(
    TypeContenu(
        code=TYPE,
        libelle="partage",
        schema=ChampsPartage,
        actions_auteur={Role.eleve: "eleve.partage", Role.encadreur: "encadreur.partage"},
        titre=_titre,
        lien_auteur=lambda _contenu_id: "/mon-espace#mes-partages",
        adresse=False,
        correction=False,
        depublication=False,
        avis_approbation="est validé",
        domaine_droit="partages",
        max_en_attente=PAR_JOUR,
        crediter=_crediter,
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


def _debut_du_jour(instant: datetime) -> datetime:
    return instant.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


async def _du_jour(db: AsyncSession, auteur_id: UUID) -> int:
    debut = _debut_du_jour(datetime.now(UTC))
    return int(
        await db.scalar(
            select(func.count())
            .select_from(Contenu)
            .where(Contenu.auteur_id == auteur_id, Contenu.type == TYPE, Contenu.cree_le >= debut)
        )
        or 0
    )


def _nature(article: Contenu, auteur: Utilisateur) -> Nature:
    return "partage" if article.auteur_id == auteur.id else "republication"


async def _reseaux_declares(db: AsyncSession, article_id: UUID, auteur_id: UUID) -> list[ReseauPartage]:
    reseaux = await db.scalars(
        select(VersionContenu.donnees["reseau"].astext)
        .join(Contenu, Contenu.id == VersionContenu.contenu_id)
        .where(
            Contenu.type == TYPE,
            Contenu.parent_id == article_id,
            Contenu.auteur_id == auteur_id,
            Contenu.etat.in_(VIVANTS),
        )
    )
    return sorted({ReseauPartage(r) for r in reseaux.all()}, key=list(ReseauPartage).index)


# Déclaration ---------------------------------------------------------------------------------------------------


async def etat_article(db: AsyncSession, auteur: Utilisateur, adresse: str) -> EtatPartagesArticle:
    article = await _article_publie(db, adresse)
    return EtatPartagesArticle(
        nature=_nature(article, auteur),
        reseaux_declares=await _reseaux_declares(db, article.id, auteur.id),
        restantes_aujourdhui=max(0, PAR_JOUR - await _du_jour(db, auteur.id)),
    )


async def declarer(
    db: AsyncSession, auteur: Utilisateur, adresse: str, reseau: ReseauPartage, lien: str, adresse_ip: str
) -> PartageAuteur:
    lien = verifier_lien(reseau, lien)
    article = await _article_publie(db, adresse)
    # Sous le verrou de l'auteur : le plafond du jour et les doublons se comptent sans course.
    await moteur.verrouiller_auteur(db, auteur)
    if await _du_jour(db, auteur.id) >= PAR_JOUR:
        raise Refus(f"Tu as déjà déclaré {PAR_JOUR} partages aujourd'hui : réessaie demain.", 429)
    nature = _nature(article, auteur)
    declares = await _reseaux_declares(db, article.id, auteur.id)
    if nature == "partage" and reseau in declares:
        raise Refus(f"Tu as déjà déclaré le partage de cet article sur {NOMS[reseau]}.", 409)
    if nature == "republication" and declares:
        raise Refus("Tu as déjà déclaré la republication de cet article.", 409)
    # Sous un verrou propre au lien : deux personnes ne déclarent pas la même publication en même temps.
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:lien, 44))"), {"lien": lien})
    deja = await db.scalar(
        select(VersionContenu.id)
        .join(Contenu, Contenu.id == VersionContenu.contenu_id)
        .where(
            VersionContenu.donnees.has_key("lien"),
            VersionContenu.etat != EtatVersion.travail,
            VersionContenu.donnees["lien"].astext == lien,
            Contenu.type == TYPE,
            Contenu.etat.in_(VIVANTS),
        )
        .limit(1)
    )
    if deja is not None:
        raise Refus("Ce lien a déjà été déclaré.", 409)
    donnees = ChampsPartage(reseau=reseau, lien=lien, nature=nature).model_dump(mode="json")
    contenu = await moteur.creer(db, auteur, TYPE, donnees, parent_id=article.id)
    await moteur.soumettre(db, contenu, auteur, adresse_ip)
    await db.commit()
    return (await _miens(db, auteur.id, contenu.id))[0]


# Mes partages --------------------------------------------------------------------------------------------------

_Article = aliased(Contenu)
_VersionArticle = aliased(VersionContenu)
# Le titre de la dernière version approuvée de l'article, jamais un brouillon de son auteur.
_titre_article = (
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


async def _miens(db: AsyncSession, auteur_id: UUID, contenu_id: UUID | None = None) -> list[PartageAuteur]:
    requete = (
        select(Contenu, VersionContenu, _titre_article, _Article.adresse, _Article.version_publiee_id, _motif)
        .join(VersionContenu, VersionContenu.contenu_id == Contenu.id)
        .join(_Article, _Article.id == Contenu.parent_id)
        .where(Contenu.type == TYPE, Contenu.auteur_id == auteur_id, Contenu.etat.in_(tuple(ETATS)))
    )
    if contenu_id is not None:
        requete = requete.where(Contenu.id == contenu_id)
    lignes = (await db.execute(requete.order_by(Contenu.cree_le.desc(), Contenu.id.desc()).limit(LIMITE_MIENS))).all()
    cles = {
        cle_points(v.donnees["nature"], c.parent_id, auteur_id, ReseauPartage(v.donnees["reseau"])): c.id
        for c, v, *_ in lignes
        if c.etat is EtatContenu.publie
    }
    montants: dict[UUID, int] = {}
    if cles:
        for cle, montant in await db.execute(
            select(MouvementPoints.cle, MouvementPoints.montant).where(
                MouvementPoints.utilisateur_id == auteur_id, MouvementPoints.cle.in_(list(cles))
            )
        ):
            montants[cles[cle]] = montant
    return [
        PartageAuteur(
            id=contenu.id,
            article_titre=titre or "",
            # Le lien vers l'article seulement s'il est en ligne : sinon la page serait introuvable.
            article_adresse=adresse if en_ligne else None,
            reseau=ReseauPartage(version.donnees["reseau"]),
            lien=str(version.donnees["lien"]),
            nature=version.donnees["nature"],
            etat=ETATS[contenu.etat],  # type: ignore[arg-type]
            motif=motif if contenu.etat is EtatContenu.refuse else None,
            points=montants.get(contenu.id),
            declare_le=contenu.cree_le,
        )
        for contenu, version, titre, adresse, en_ligne, motif in lignes
    ]


async def mes_partages(db: AsyncSession, auteur: Utilisateur) -> MesPartages:
    return MesPartages(partages=await _miens(db, auteur.id))
