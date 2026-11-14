"""Espace du président (spec 026) : la vue « Mon club », les propositions de fiche et les actualités du club.

Les contenus du club passent par le moteur de modération (ADR-0009). Leur auteur est le président en place :
une passation validée le transfère au successeur (`transferer_contenus`), dans la même transaction. Toute gestion
exige d'être le président d'un club actif (`president_en_place`), en plus d'être l'auteur du contenu.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.articles import public
from app.articles.dependances import auteur as redacteur
from app.articles.schemas import ChampsArticle, ResumeArticleAuteur
from app.clubs import activation, adhesions
from app.clubs.models import CLUB_VIVANT, Adhesion, Club, ClubAxe, EtatAdhesion, Rattachement
from app.clubs.requetes import encadreurs_actifs
from app.clubs.schemas import (
    ClubEspace,
    EspaceClub,
    IndicateursClub,
    PropositionFiche,
    SuiviClub,
)
from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import Refus, etablissement_rattache
from app.comptes.models import Utilisateur
from app.db import get_session
from app.moderation import service as moteur
from app.moderation.models import Contenu, DecisionModeration, EtatContenu, VersionContenu
from app.moderation.types import TypeContenu, enregistrer
from app.referentiel.models import Axe

FICHE = "fiche_club"
ACTUALITE = public.ACTUALITE
LIMITE_SUIVI = 50


# Types de contenu --------------------------------------------------------------------------------------------


class ChampsFiche(BaseModel):
    description: str | None
    axes: list[str]


async def _appliquer_fiche(db: AsyncSession, contenu: Contenu) -> None:
    """À l'approbation : la fiche publique prend la description et les axes proposés, sous le verrou du club."""
    club = await db.get(Club, contenu.club_id, with_for_update=True, populate_existing=True)
    if club is None or not activation.est_en_service(club):
        raise Refus("Ce club n'est pas en service : sa fiche ne peut pas changer.", 409)
    version = await db.get(VersionContenu, contenu.version_publiee_id)
    assert version is not None
    champs = ChampsFiche.model_validate(version.donnees)
    avant = {
        "description": club.description,
        "axes": sorted((await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id))).all()),
    }
    club.description = champs.description
    await db.execute(delete(ClubAxe).where(ClubAxe.club_id == club.id))
    for axe in champs.axes:
        db.add(ClubAxe(club_id=club.id, axe_code=axe))
    journaliser(
        db, "club_fiche_modifiee", None, cible_type="club", cible_id=club.id, perimetre=contenu.dre_code or "national",
        details={
            "proposition": str(contenu.id),
            "avant": avant,
            "apres": {"description": champs.description, "axes": sorted(champs.axes)},
        },
    )  # fmt: skip


enregistrer(
    TypeContenu(
        code=FICHE,
        libelle="changement de fiche",
        schema=ChampsFiche,
        actions_auteur={},
        titre=lambda _donnees: "Fiche du club",
        lien_auteur=lambda _contenu_id: "/mon-club",
        adresse=False,
        correction=False,
        depublication=False,
        a_la_publication=_appliquer_fiche,
    )
)

# Une actualité : les champs d'un article, au nom du club, sans point (le barème n'en prévoit pas).
enregistrer(
    TypeContenu(
        code=ACTUALITE,
        libelle="actualité",
        schema=ChampsArticle,
        actions_auteur={},
        titre=lambda donnees: str(donnees["titre"]),
        lien_auteur=lambda _contenu_id: "/mon-club",
        determinant="Ta",
        accord="e",
    )
)


# Droits ------------------------------------------------------------------------------------------------------


async def club_gere(db: AsyncSession, utilisateur: Utilisateur) -> Club | None:
    """Le club en service (actif ou en régularisation, spec 033) présidé par cet utilisateur, sous verrou partagé : une passation (qui verrouille le club pour
    le modifier) attend la fin de l'opération en cours, et celle-ci ne voit jamais un président déjà remplacé.
    Aucun contenu créé pendant une passation ne reste ainsi à l'ancien président."""
    return await db.scalar(
        select(Club).where(Club.president_id == utilisateur.id, activation.en_service()).with_for_update(read=True)
    )


async def president_en_place(
    utilisateur: Annotated[Utilisateur, Depends(redacteur)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Utilisateur:
    """Le président d'un club actif ; sinon 403. Vérifié à chaque route de gestion."""
    if await club_gere(db, utilisateur) is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Seul le président d'un club actif gère son espace.")
    return utilisateur


President = Annotated[Utilisateur, Depends(president_en_place)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]


async def club_du_president(db: AsyncSession, president: Utilisateur) -> UUID:
    club = await club_gere(db, president)
    if club is None:
        raise Refus("Seul le président d'un club actif gère son espace.", 403)
    return club.id


async def transferer_contenus(db: AsyncSession, club_id: UUID, successeur_id: UUID) -> None:
    """À la passation : les actualités et propositions du club passent au nouveau président."""
    await db.execute(
        update(Contenu)
        .where(Contenu.club_id == club_id, Contenu.type.in_((ACTUALITE, FICHE)))
        .values(auteur_id=successeur_id)
        .execution_options(synchronize_session=False)
    )


# Vue « Mon club » --------------------------------------------------------------------------------------------


async def _role(db: AsyncSession, club: Club, utilisateur: Utilisateur) -> str | None:
    if club.president_id == utilisateur.id:
        return "president"
    membre = await db.scalar(
        select(Adhesion.id).where(
            Adhesion.club_id == club.id, Adhesion.eleve_id == utilisateur.id, Adhesion.etat == EtatAdhesion.active
        )
    )
    if membre is not None:
        return "membre"
    if await db.scalar(encadreurs_actifs(club.id).where(Rattachement.encadreur_id == utilisateur.id)):
        return "encadreur"
    return None


async def _propositions(db: AsyncSession, club_id: UUID) -> list[PropositionFiche]:
    motif = (
        select(DecisionModeration.motif)
        .where(DecisionModeration.contenu_id == Contenu.id)
        .order_by(DecisionModeration.decide_le.desc(), DecisionModeration.id.desc())
        .limit(1)
        .correlate(Contenu)
        .scalar_subquery()
    )
    lignes = await db.execute(
        select(Contenu, VersionContenu, motif)
        .join(VersionContenu, (VersionContenu.contenu_id == Contenu.id) & (VersionContenu.numero == 1))
        .where(Contenu.club_id == club_id, Contenu.type == FICHE)
        .order_by(Contenu.cree_le.desc(), Contenu.id.desc())
        .limit(LIMITE_SUIVI)
    )
    return [
        PropositionFiche(
            id=contenu.id,
            etat=contenu.etat,
            description=version.donnees.get("description"),
            axes=list(version.donnees.get("axes", [])),
            motif=dernier_motif if contenu.etat is EtatContenu.refuse else None,
            soumis_le=contenu.soumis_le,
            version=contenu.version,
        )
        for contenu, version, dernier_motif in lignes
    ]


async def _actualites_suivies(db: AsyncSession, club_id: UUID) -> list[ResumeArticleAuteur]:
    """Toutes les actualités du club, quel que soit leur état, pour le suivi du président."""
    contenus = await db.scalars(
        select(Contenu)
        .where(Contenu.club_id == club_id, Contenu.type == ACTUALITE)
        .order_by(Contenu.modifie_le.desc(), Contenu.id.desc())
        .limit(LIMITE_SUIVI)
    )
    resumes = []
    for contenu in contenus:
        visible = await moteur.version_visible_auteur(db, contenu)
        resumes.append(
            ResumeArticleAuteur(
                id=contenu.id,
                titre=str(visible.donnees["titre"]),
                etat=contenu.etat,
                en_ligne=contenu.version_publiee_id is not None,
                adresse=contenu.adresse,
                modifie_le=contenu.modifie_le,
            )
        )
    return resumes


async def espace(db: AsyncSession, utilisateur: Utilisateur, club_id: UUID) -> EspaceClub:
    club = await db.scalar(select(Club).where(Club.id == club_id, Club.etat.in_(CLUB_VIVANT)))
    role = await _role(db, club, utilisateur) if club else None
    if club is None or role is None:
        # Pour les autres, le club n'a pas d'espace à montrer : même réponse que s'il n'existait pas.
        raise Refus("Ce club est introuvable.", 404)
    president = role == "president"
    axes = (
        await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id).order_by(ClubAxe.axe_code))
    ).all()
    membres = (
        await db.scalar(
            select(func.count())
            .select_from(Adhesion)
            .where(Adhesion.club_id == club.id, Adhesion.etat == EtatAdhesion.active)
        )
    ) or 0
    encadreurs = (await db.scalar(select(func.count()).select_from(encadreurs_actifs(club.id).subquery()))) or 0
    publiees = (
        await db.scalar(
            select(func.count())
            .select_from(Contenu)
            .where(Contenu.club_id == club.id, Contenu.type == ACTUALITE, Contenu.version_publiee_id.is_not(None))
        )
    ) or 0
    suivi = None
    if president:
        suivi = SuiviClub(
            propositions=await _propositions(db, club.id),
            actualites=await _actualites_suivies(db, club.id),
        )
    return EspaceClub(
        club=ClubEspace(
            id=club.id,
            nom=club.nom,
            description=club.description,
            etablissement=await etablissement_rattache(db, club.etablissement_id),
            axes=list(axes),
            actif_le=club.actif_le,
        ),
        role=role,
        indicateurs=IndicateursClub(
            membres=membres,
            encadreurs=encadreurs,
            actualites=publiees,
        ),
        statut=activation.statut_effectif(club, activation.maintenant()).value,
        actualites=await public.actualites_du_club(db, club.id),
        membres=await adhesions.liste_membres(db, club),
        suivi=suivi,
    )


# Propositions de fiche ---------------------------------------------------------------------------------------


async def proposer_fiche(
    db: AsyncSession, president: Utilisateur, description: str | None, axes: list[str], adresse_ip: str
) -> PropositionFiche:
    club = await club_gere(db, president)
    if club is None:
        raise Refus("Seul le président d'un club actif gère son espace.", 403)
    actuels = set((await db.scalars(select(ClubAxe.axe_code).where(ClubAxe.club_id == club.id))).all())
    # Un axe actif, ou déjà sur la fiche (comme pour un article : un axe désactivé depuis reste accepté).
    connus = set(
        (await db.scalars(select(Axe.code).where(Axe.code.in_(axes), or_(Axe.actif, Axe.code.in_(actuels))))).all()
    )
    if connus != set(axes):
        raise Refus("Choisis des axes parmi les axes actifs du programme.", 422)
    if description == club.description and set(axes) == actuels:
        raise Refus("Rien n'a changé par rapport à la fiche actuelle.", 422)
    # Le verrou de l'auteur sérialise ses envois ; l'index unique tient même entre deux présidents successifs.
    await moteur.verrouiller_auteur(db, president)
    en_attente = await db.scalar(
        select(Contenu.id).where(
            Contenu.club_id == club.id, Contenu.type == FICHE, Contenu.etat == EtatContenu.en_attente
        )
    )
    if en_attente is not None:
        raise Refus("Une proposition attend déjà la modération : retire-la pour en faire une autre.", 409)
    try:
        contenu = await moteur.creer(
            db, president, FICHE, ChampsFiche(description=description, axes=axes).model_dump(), club_id=club.id
        )
        await moteur.soumettre(db, contenu, president, adresse_ip)
        await db.flush()
    except IntegrityError:
        # L'index unique, dernier garde-fou si deux propositions arrivaient malgré le verrou.
        await db.rollback()
        raise Refus("Une proposition attend déjà la modération : retire-la pour en faire une autre.", 409) from None
    await db.commit()
    return next(p for p in await _propositions(db, club.id) if p.id == contenu.id)


async def retirer_fiche(db: AsyncSession, president: Utilisateur, contenu_id: UUID, adresse_ip: str) -> None:
    contenu = await moteur.contenu_de(db, president, contenu_id, FICHE, verrouiller=True)
    if contenu.etat is not EtatContenu.en_attente:
        raise Refus("Seule une proposition en attente peut être retirée.", 409)
    await moteur.retirer_definitivement(db, contenu, president, adresse_ip)
    await db.commit()
