"""Articles des élèves et des encadreurs (spec 023) : rédaction par l'auteur, sur le moteur de modération."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import (
    ArticleAuteur,
    ArticleEcriture,
    ChampsArticle,
    DerniereDecision,
    MesArticles,
    PhotoAuteur,
    PhotoModification,
    ResumeArticleAuteur,
)
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.moderation import photos
from app.moderation import service as moteur
from app.moderation.models import Contenu, DecisionModeration, EtatVersion
from app.moderation.types import TypeContenu, enregistrer
from app.points.bareme import ARTICLE_ELEVE, ARTICLE_ENCADREUR
from app.referentiel.models import Axe

TYPE = "article"

ARTICLE = enregistrer(
    TypeContenu(
        code=TYPE,
        libelle="article",
        schema=ChampsArticle,
        actions_auteur={Role.eleve: ARTICLE_ELEVE, Role.encadreur: ARTICLE_ENCADREUR},
        titre=lambda donnees: str(donnees["titre"]),
        lien_auteur=lambda contenu_id: f"/mes-articles/{contenu_id}",
    )
)


async def _verifier_axe(db: AsyncSession, axe_code: str, actuel: str | None) -> None:
    """Un axe désactivé reste accepté s'il était déjà celui de l'article (spec 016) ; sinon, il doit être actif."""
    if axe_code == actuel:
        return
    axe = await db.get(Axe, axe_code)
    if axe is None or not axe.actif:
        raise Refus("Choisis un axe parmi les axes proposés.")


def _donnees(entree: ArticleEcriture) -> dict[str, Any]:
    return ChampsArticle.model_validate(entree.model_dump(exclude={"version"})).model_dump()


async def _derniere_decision(db: AsyncSession, contenu: Contenu) -> DerniereDecision | None:
    decision = await db.scalar(
        select(DecisionModeration)
        .where(DecisionModeration.contenu_id == contenu.id)
        .order_by(DecisionModeration.decide_le.desc(), DecisionModeration.id.desc())
        .limit(1)
    )
    if decision is None:
        return None
    return DerniereDecision(decision=decision.decision, motif=decision.motif, decide_le=decision.decide_le)


async def article_auteur(db: AsyncSession, contenu: Contenu) -> ArticleAuteur:
    # Les dates calculées par la base (`modifie_le`) sont relues après chaque écriture.
    await db.refresh(contenu)
    visible = await moteur.version_visible_auteur(db, contenu)
    travail = await moteur.version(db, contenu.version_travail_id)
    return ArticleAuteur(
        id=contenu.id,
        etat=contenu.etat,
        version=contenu.version,
        champs=ChampsArticle.model_validate(visible.donnees),
        en_ligne=contenu.version_publiee_id is not None,
        adresse=contenu.adresse,
        modifiable=contenu.etat in moteur.MODIFIABLES,
        soumettable=contenu.etat in moteur.SOUMETTABLES and travail is not None and travail.etat is EtatVersion.travail,
        supprimable=await moteur.jamais_soumis(db, contenu),
        derniere_decision=await _derniere_decision(db, contenu),
        photos=[
            PhotoAuteur(
                id=photo.id,
                legende=placement.legende,
                couverture=placement.couverture,
                ordre=placement.ordre,
                largeur=photo.largeur,
                hauteur=photo.hauteur,
                effacee=photo.efface_le is not None,
            )
            for placement, photo in await photos.photos_de(db, visible.id)
        ],
        soumis_le=contenu.soumis_le,
        publie_le=contenu.publie_le,
        modifie_le=contenu.modifie_le,
    )


async def mes_articles(db: AsyncSession, auteur: Utilisateur, *, type: str = TYPE) -> MesArticles:
    contenus = await db.scalars(
        select(Contenu)
        .where(Contenu.auteur_id == auteur.id, Contenu.type == type)
        .order_by(Contenu.modifie_le.desc(), Contenu.id.desc())
    )
    articles = []
    for contenu in contenus:
        visible = await moteur.version_visible_auteur(db, contenu)
        articles.append(
            ResumeArticleAuteur(
                id=contenu.id,
                titre=visible.donnees["titre"],
                etat=contenu.etat,
                en_ligne=contenu.version_publiee_id is not None,
                adresse=contenu.adresse,
                modifie_le=contenu.modifie_le,
            )
        )
    return MesArticles(articles=articles)


async def creer(
    db: AsyncSession, auteur: Utilisateur, entree: ArticleEcriture, *, type: str = TYPE, club_id: UUID | None = None
) -> ArticleAuteur:
    await _verifier_axe(db, entree.axe_code, None)
    contenu = await moteur.creer(db, auteur, type, _donnees(entree), club_id=club_id)
    await db.commit()
    return await article_auteur(db, contenu)


async def lire(db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, *, type: str = TYPE) -> ArticleAuteur:
    return await article_auteur(db, await moteur.contenu_de(db, auteur, contenu_id, type))


async def modifier(
    db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, entree: ArticleEcriture, *, type: str = TYPE
) -> ArticleAuteur:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    moteur.verifier_version(contenu, entree.version)
    actuelle = await moteur.version_visible_auteur(db, contenu)
    await _verifier_axe(db, entree.axe_code, actuelle.donnees.get("axe_code"))
    await moteur.modifier(db, contenu, _donnees(entree))
    await db.commit()
    return await article_auteur(db, contenu)


async def soumettre(
    db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, version: int, adresse_ip: str, *, type: str = TYPE
) -> ArticleAuteur:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    moteur.verifier_version(contenu, version)
    await moteur.soumettre(db, contenu, auteur, adresse_ip)
    await db.commit()
    return await article_auteur(db, contenu)


async def retirer(
    db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, version: int, adresse_ip: str, *, type: str = TYPE
) -> ArticleAuteur:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    moteur.verifier_version(contenu, version)
    await moteur.retirer(db, contenu, auteur, adresse_ip)
    await db.commit()
    return await article_auteur(db, contenu)


async def supprimer(db: AsyncSession, auteur: Utilisateur, contenu_id: UUID, *, type: str = TYPE) -> None:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    if not await moteur.jamais_soumis(db, contenu):
        raise Refus("Seul un brouillon jamais soumis peut être supprimé.", 409)
    a_effacer = await photos.effacer_du_brouillon(db, contenu)
    await moteur.supprimer(db, contenu)
    await db.commit()
    # Les fichiers après la validation : jamais un fichier effacé pour une suppression annulée.
    await photos.effacer_fichiers(a_effacer)


# Photos (spec 024) ----------------------------------------------------------------------------------------------


async def ajouter_photo(
    db: AsyncSession,
    auteur: Utilisateur,
    contenu_id: UUID,
    version: int,
    octets: bytes,
    legende: str | None,
    couverture: bool,
    adresse_ip: str,
    *,
    type: str = TYPE,
) -> ArticleAuteur:
    # L'image d'abord, sans verrou ni transaction : le traitement est long, et un refus ne touche à rien.
    preparees = await photos.preparer(octets)
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    moteur.verifier_version(contenu, version)
    await photos.ajouter(db, contenu, auteur, preparees, legende, couverture, adresse_ip)
    return await article_auteur(db, contenu)


async def modifier_photo(
    db: AsyncSession,
    auteur: Utilisateur,
    contenu_id: UUID,
    photo_id: UUID,
    entree: PhotoModification,
    *,
    type: str = TYPE,
) -> ArticleAuteur:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    moteur.verifier_version(contenu, entree.version)
    await photos.modifier(
        db, contenu, photo_id, legende=entree.legende or None, changer_legende="legende" in entree.model_fields_set,
        couverture=entree.couverture, ordre=entree.ordre,
    )  # fmt: skip
    return await article_auteur(db, contenu)


async def retirer_photo(
    db: AsyncSession,
    auteur: Utilisateur,
    contenu_id: UUID,
    photo_id: UUID,
    version: int,
    adresse_ip: str,
    *,
    type: str = TYPE,
) -> ArticleAuteur:
    contenu = await moteur.contenu_de(db, auteur, contenu_id, type, verrouiller=True)
    moteur.verifier_version(contenu, version)
    await photos.retirer(db, contenu, auteur, photo_id, adresse_ip)
    return await article_auteur(db, contenu)
