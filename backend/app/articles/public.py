"""Lecture publique des articles (spec 023). Seule la version approuvée (`version_publiee_id`) se lit ; rien d'un
brouillon, d'une version en attente, refusée ou dépubliée. La signature ne montre jamais un nom complet : un élève
par son pseudonyme (et son club s'il l'a choisi), un encadreur par son prénom, l'initiale de son nom et sa fonction.
"""

import math
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import ArticlePublic, ArticlesPublics, AxeArticle, PhotoPublique, ResumeArticle, Signature
from app.articles.service import TYPE
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, Fonction
from app.moderation import photos
from app.moderation.models import Contenu, Photo, VersionContenu, VersionPhoto
from app.referentiel.models import Axe

PAR_PAGE = 20

# Libellés courts, pour la signature : « Kossi A., enseignant ».
FONCTIONS = {
    Fonction.enseignant: "enseignant",
    Fonction.responsable: "responsable pédagogique",
    Fonction.sante: "agent de santé scolaire",
    Fonction.accompagnateur: "accompagnateur",
    Fonction.autre: "encadreur",
}


# Les articles personnels et les actualités des clubs (spec 026) : même lecture publique, même adresse.
ACTUALITE = "actualite"
TYPES = (TYPE, ACTUALITE)


def _publics() -> Select[tuple[Contenu, VersionContenu, Axe]]:
    return (
        select(Contenu, VersionContenu, Axe)
        .join(VersionContenu, VersionContenu.id == Contenu.version_publiee_id)
        .join(Axe, Axe.code == Contenu.axe_code)
        .where(Contenu.type.in_(TYPES), Contenu.version_publiee_id.is_not(None))
    )


async def signature(db: AsyncSession, contenu: Contenu) -> Signature:
    if contenu.club_id is not None:
        # Une actualité parle au nom du club : jamais le nom ni le pseudonyme du président.
        nom = await db.scalar(select(Club.nom).where(Club.id == contenu.club_id))
        return Signature(profil="club", nom=nom or "Club Santé")
    auteur = await db.get(Utilisateur, contenu.auteur_id)
    assert auteur is not None
    if auteur.role is Role.eleve:
        eleve = await db.get(Eleve, auteur.id)
        club = None
        if contenu.afficher_club:
            club = await db.scalar(
                select(Club.nom)
                .join(Adhesion, Adhesion.club_id == Club.id)
                .where(
                    Adhesion.eleve_id == auteur.id, Adhesion.etat == EtatAdhesion.active, Club.etat == EtatClub.actif
                )
            )
        return Signature(profil="eleve", nom=eleve.pseudonyme if eleve else "Un élève", club=club)
    encadreur = await db.get(Encadreur, auteur.id)
    # Le libellé de la liste seulement : la précision d'une fonction « autre » est un texte libre, jamais publié.
    fonction = FONCTIONS[encadreur.fonction] if encadreur else None
    initiale = f" {auteur.nom.strip()[:1].upper()}." if auteur.nom.strip() else ""
    return Signature(profil="encadreur", nom=f"{auteur.prenom.strip()}{initiale}", fonction=fonction)


async def _photos(db: AsyncSession, version: VersionContenu) -> list[tuple[bool, PhotoPublique]]:
    return [
        (
            placement.couverture,
            _publique(placement, photo),
        )
        for placement, photo in await photos.photos_de(db, version.id)
        if photo.efface_le is None
    ]


def _publique(placement: VersionPhoto, photo: Photo) -> PhotoPublique:
    return PhotoPublique(id=photo.id, legende=placement.legende, largeur=photo.largeur, hauteur=photo.hauteur)


async def _resume(
    db: AsyncSession, contenu: Contenu, version: VersionContenu, axe: Axe, couverture: PhotoPublique | None
) -> ResumeArticle:
    assert contenu.adresse is not None and contenu.publie_le is not None
    return ResumeArticle(
        nature="actualite" if contenu.type == ACTUALITE else "article",
        adresse=contenu.adresse,
        titre=version.donnees["titre"],
        chapo=version.donnees["chapo"],
        axe=AxeArticle(code=axe.code, libelle=axe.libelle),
        signature=await signature(db, contenu),
        couverture=couverture,
        publie_le=contenu.publie_le.date(),
    )


async def _resumes(db: AsyncSession, lignes: Sequence[Row[tuple[Contenu, VersionContenu, Axe]]]) -> list[ResumeArticle]:
    # Les couvertures en une seule requête.
    trouvees = await photos.couvertures(db, [version.id for _, version, _ in lignes])
    return [
        await _resume(db, contenu, version, axe, _publique(*trouvees[version.id]) if version.id in trouvees else None)
        for contenu, version, axe in lignes
    ]


async def actualites_du_club(db: AsyncSession, club_id: UUID, limite: int = 6) -> list[ResumeArticle]:
    """Les dernières actualités publiées d'un club (spec 026), pour sa fiche et « Mon club »."""
    lignes = (
        await db.execute(
            _publics()
            .where(Contenu.type == ACTUALITE, Contenu.club_id == club_id)
            .order_by(Contenu.publie_le.desc(), Contenu.id.desc())
            .limit(limite)
        )
    ).all()
    return await _resumes(db, lignes)


async def lister(db: AsyncSession, page: int, axe: str | None) -> ArticlesPublics:
    requete = _publics()
    if axe:
        requete = requete.where(Contenu.axe_code == axe)
    total = (await db.scalar(select(func.count()).select_from(requete.with_only_columns(Contenu.id).subquery()))) or 0
    lignes = (
        await db.execute(
            requete.order_by(Contenu.publie_le.desc(), Contenu.id.desc()).offset((page - 1) * PAR_PAGE).limit(PAR_PAGE)
        )
    ).all()
    return ArticlesPublics(
        articles=await _resumes(db, lignes),
        page=page,
        pages=max(1, math.ceil(total / PAR_PAGE)),
        total=total,
    )


async def lire(db: AsyncSession, adresse: str) -> ArticlePublic | None:
    ligne = (await db.execute(_publics().where(Contenu.adresse == adresse))).one_or_none()
    if ligne is None:
        return None
    contenu, version, axe = ligne
    toutes = await _photos(db, version)
    couverture = next((p for est_couverture, p in toutes if est_couverture), None)
    resume = await _resume(db, contenu, version, axe, couverture)
    galerie = [p for est_couverture, p in toutes if not est_couverture]
    return ArticlePublic(**resume.model_dump(), texte=version.donnees["texte"], photos=galerie)
