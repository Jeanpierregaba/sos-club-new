"""La bibliothèque publique (spec 028) : les ressources publiées, ouvertes à tous, visiteurs compris.

Rien de la préparation n'en sort (contributeurs, motifs, clés de stockage). Chaque ouverture ou téléchargement
ajoute 1 au compteur de la ressource ; on ne garde pas qui a téléchargé.
"""

from typing import Literal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.bibliotheque.models import CategorieRessource, EtatRessource, Ressource
from app.bibliotheque.schemas import Bibliotheque, Chiffres, RessourcePublique

A_LA_UNE = 3
PUBLIEE = Ressource.etat == EtatRessource.publie


def _couverture(ressource: Ressource, taille: Literal["grande", "vignette"]) -> str | None:
    cle = ressource.couverture_grande if taille == "grande" else ressource.couverture_vignette
    if cle is None:
        return None
    # La clé change avec l'image : l'adresse aussi, et aucun navigateur ne garde l'ancienne.
    version = cle.split("/")[1].rsplit("-", 1)[0]
    return f"/api/bibliotheque/{ressource.id}/couverture/{taille}?v={version}"


def _publique(ressource: Ressource, taille: Literal["grande", "vignette"]) -> RessourcePublique:
    assert ressource.publie_le and ressource.validateur_nom and ressource.validateur_qualite
    return RessourcePublique(
        id=ressource.id,
        titre=ressource.titre,
        description=ressource.description,
        categorie=ressource.categorie,
        axe_code=ressource.axe_code,
        parution=ressource.parution,
        fichier_octets=ressource.fichier_octets or 0,
        pages=ressource.pages,
        telechargements=ressource.telechargements,
        publie_le=ressource.publie_le,
        validateur_nom=ressource.validateur_nom,
        validateur_qualite=ressource.validateur_qualite,
        contenu_de_test=ressource.contenu_de_test,
        couverture=_couverture(ressource, taille),
    )


async def bibliotheque(
    db: AsyncSession, categorie: CategorieRessource | None = None, axe: str | None = None
) -> Bibliotheque:
    ordre = (Ressource.publie_le.desc(), Ressource.id)
    requete = select(Ressource).where(PUBLIEE)
    if categorie is not None:
        requete = requete.where(Ressource.categorie == categorie)
    if axe:
        requete = requete.where(Ressource.axe_code == axe)
    ressources = (await db.scalars(requete.order_by(*ordre))).all()
    # « À la Une » ne suit pas les filtres : ce sont toujours les derniers magazines.
    une = (
        await db.scalars(
            select(Ressource)
            .where(PUBLIEE, Ressource.categorie == CategorieRessource.magazine)
            .order_by(*ordre)
            .limit(A_LA_UNE)
        )
    ).all()
    documents, telechargements = (
        await db.execute(select(func.count(), func.coalesce(func.sum(Ressource.telechargements), 0)).where(PUBLIEE))
    ).one()
    return Bibliotheque(
        a_la_une=[_publique(r, "grande") for r in une],
        ressources=[_publique(r, "vignette") for r in ressources],
        chiffres=Chiffres(documents=documents, telechargements=telechargements),
    )


async def publiee(db: AsyncSession, ressource_id: UUID) -> Ressource | None:
    return await db.scalar(select(Ressource).where(Ressource.id == ressource_id, PUBLIEE))


async def compter(db: AsyncSession, ressource_id: UUID) -> None:
    """+1 en une seule instruction : deux téléchargements simultanés comptent deux fois. La date de modification
    de la ressource ne bouge pas."""
    await db.execute(
        update(Ressource)
        .where(Ressource.id == ressource_id, PUBLIEE)
        .values(telechargements=Ressource.telechargements + 1, modifie_le=Ressource.modifie_le)
        .execution_options(synchronize_session=False)
    )
    await db.commit()
