"""Lecture publique des articles (spec 023). Seule la version approuvée (`version_publiee_id`) se lit ; rien d'un
brouillon, d'une version en attente, refusée ou dépubliée. La signature ne montre jamais un nom complet : un élève
par son pseudonyme (et son club s'il l'a choisi), un encadreur par son prénom, l'initiale de son nom et sa fonction.
"""

import math

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import ArticlePublic, ArticlesPublics, AxeArticle, ResumeArticle, Signature
from app.articles.service import TYPE
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatClub
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, Fonction
from app.moderation.models import Contenu, VersionContenu
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


def _publics() -> Select[tuple[Contenu, VersionContenu, Axe]]:
    return (
        select(Contenu, VersionContenu, Axe)
        .join(VersionContenu, VersionContenu.id == Contenu.version_publiee_id)
        .join(Axe, Axe.code == Contenu.axe_code)
        .where(Contenu.type == TYPE, Contenu.version_publiee_id.is_not(None))
    )


async def signature(db: AsyncSession, contenu: Contenu) -> Signature:
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


async def _resume(db: AsyncSession, contenu: Contenu, version: VersionContenu, axe: Axe) -> ResumeArticle:
    assert contenu.adresse is not None and contenu.publie_le is not None
    return ResumeArticle(
        adresse=contenu.adresse,
        titre=version.donnees["titre"],
        chapo=version.donnees["chapo"],
        axe=AxeArticle(code=axe.code, libelle=axe.libelle),
        signature=await signature(db, contenu),
        publie_le=contenu.publie_le.date(),
    )


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
        articles=[await _resume(db, *ligne) for ligne in lignes],
        page=page,
        pages=max(1, math.ceil(total / PAR_PAGE)),
        total=total,
    )


async def lire(db: AsyncSession, adresse: str) -> ArticlePublic | None:
    ligne = (await db.execute(_publics().where(Contenu.adresse == adresse))).one_or_none()
    if ligne is None:
        return None
    contenu, version, axe = ligne
    resume = await _resume(db, contenu, version, axe)
    return ArticlePublic(**resume.model_dump(), texte=version.donnees["texte"])
