"""Jeux de l'accueil (spec 021) : « Quel axe est fait pour toi ? », réservé aux élèves actifs, sans point, en
3 parties gardées par l'API (spec 032) ; et le défi du jour, ouvert à tous, qui rapporte des points à un élève actif (spec 022)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.dependances import utilisateur_courant, utilisateur_facultatif
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.db import get_session
from app.jeux import defis, parties_quel_axe, quel_axe
from app.jeux.models import PartieQuelAxe as PartieModele
from app.jeux.schemas import (
    ChoixQuelAxe,
    CorrectionDefi,
    DefiDuJour,
    EtatQuelAxe,
    PartieQuelAxe,
    QuestionQuelAxe,
    ReponseDefi,
    ReponseQuelAxe,
    ResultatQuelAxe,
)
from app.points.service import aujourd_hui

router = APIRouter(prefix="/jeux", tags=["jeux"])


async def eleve_actif(utilisateur: Annotated[Utilisateur, Depends(utilisateur_courant)]) -> Utilisateur:
    """Le jeu est réservé aux élèves inscrits, au compte actif : vérifié ici, pas seulement dans le site."""
    if utilisateur.role is not Role.eleve or utilisateur.statut is not StatutCompte.actif:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ce jeu est réservé aux élèves inscrits.")
    return utilisateur


EleveActif = Annotated[Utilisateur, Depends(eleve_actif)]


Base = Annotated[AsyncSession, Depends(get_session)]
PLUS_DE_PARTICIPATION = (
    "Tu as utilisé tes 3 participations ! Tu peux revoir tes résultats et découvrir les 7 axes des Clubs Santé."
)
PARTIE_INTROUVABLE = "Cette partie est introuvable."


def _questions() -> list[QuestionQuelAxe]:
    return [
        QuestionQuelAxe(
            numero=numero,
            libelle=question.libelle,
            reponses=[ReponseQuelAxe(id=r.lettre, libelle=r.libelle) for r in question.reponses],
        )
        for numero, question in enumerate(quel_axe.QUESTIONNAIRES[quel_axe.VERSION], start=1)
    ]


def _partie(p: PartieModele) -> PartieQuelAxe:
    resultat = (
        ResultatQuelAxe.model_validate({"principal": p.principal, "autres": p.autres})
        if p.principal is not None and p.autres is not None
        else None
    )
    return PartieQuelAxe(
        id=p.id, numero=p.numero, reponses=p.reponses, commencee_le=p.commencee_le, terminee_le=p.terminee_le,
        resultat=resultat,
    )  # fmt: skip


@router.get("/quel-axe")
async def etat_quel_axe(db: Base, eleve: EleveActif) -> EtatQuelAxe:
    """Le questionnaire (sans les axes associés aux réponses), le compteur et les parties de l'élève (spec 032)."""
    etat = await parties_quel_axe.etat(db, eleve)
    return EtatQuelAxe(
        questions=_questions(),
        limite=parties_quel_axe.LIMITE,
        utilisees=etat.utilisees,
        restantes=etat.restantes,
        en_cours=_partie(etat.en_cours) if etat.en_cours else None,
        historique=[_partie(p) for p in etat.historique],
    )


@router.post("/quel-axe/parties", responses={201: {"model": PartieQuelAxe}})
async def commencer_quel_axe(db: Base, eleve: EleveActif, response: Response) -> PartieQuelAxe:
    """Reprend la partie en cours, ou en crée une s'il reste une participation (201). Jamais plus de 3."""
    try:
        partie, creee = await parties_quel_axe.commencer(db, eleve)
    except parties_quel_axe.PlusDeParticipation:
        raise HTTPException(status.HTTP_403_FORBIDDEN, PLUS_DE_PARTICIPATION) from None
    if creee:
        response.status_code = status.HTTP_201_CREATED
    return _partie(partie)


@router.get("/quel-axe/parties/{partie_id}")
async def partie_quel_axe(partie_id: UUID, db: Base, eleve: EleveActif) -> PartieQuelAxe:
    try:
        return _partie(await parties_quel_axe.lire(db, eleve, partie_id))
    except parties_quel_axe.PartieIntrouvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PARTIE_INTROUVABLE) from None


@router.put("/quel-axe/parties/{partie_id}/reponses/{numero}")
async def repondre_quel_axe(
    partie_id: UUID, numero: Annotated[int, Path(ge=1, le=7)], entree: ChoixQuelAxe, db: Base, eleve: EleveActif
) -> PartieQuelAxe:
    """Enregistre la réponse à une question ; elle peut être changée tant que la partie n'est pas terminée."""
    try:
        return _partie(await parties_quel_axe.repondre(db, eleve, partie_id, numero, entree.lettre))
    except parties_quel_axe.PartieIntrouvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PARTIE_INTROUVABLE) from None
    except parties_quel_axe.PartieTerminee:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette partie est terminée : ses réponses sont figées.") from None


@router.post("/quel-axe/parties/{partie_id}/fin")
async def terminer_quel_axe(partie_id: UUID, db: Base, eleve: EleveActif) -> PartieQuelAxe:
    """Calcule le résultat d'une partie aux 7 réponses. Aucun point, badge ni certificat."""
    try:
        return _partie(await parties_quel_axe.terminer(db, eleve, partie_id))
    except parties_quel_axe.PartieIntrouvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, PARTIE_INTROUVABLE) from None
    except parties_quel_axe.PartieIncomplete:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Réponds aux 7 questions pour voir ton résultat.") from None


Facultatif = Annotated[Utilisateur | None, Depends(utilisateur_facultatif)]
AUCUN_DEFI = "Aucun défi n'est disponible pour l'instant."


def _correction(c: defis.Correction) -> CorrectionDefi:
    return CorrectionDefi(
        choix=c.choix,
        correcte=c.correcte,
        bonne_reponse=c.defi.bonne_reponse,
        explication=c.defi.explication,
        points=c.points,
        deja_repondu=c.deja_repondu,
    )


@router.get("/defi-du-jour")
async def defi_du_jour(db: Base, utilisateur: Facultatif) -> DefiDuJour:
    try:
        defi = await defis.du_jour(db, utilisateur=utilisateur)
    except defis.AucunDefi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, AUCUN_DEFI) from None
    deja = await defis.reponse_du_jour(db, utilisateur, aujourd_hui())
    # Une réponse d'avant un changement de la banque peut viser une autre question : elle ne vaut que pour la sienne.
    ma_reponse = _correction(deja) if deja is not None and deja.defi.id == defi.id else None
    return DefiDuJour(
        id=defi.id, categorie=defi.categorie, question=defi.question, options=defi.options, ma_reponse=ma_reponse
    )


@router.post("/defis/{defi_id}/reponse")
async def repondre_au_defi(defi_id: UUID, entree: ReponseDefi, db: Base, utilisateur: Facultatif) -> CorrectionDefi:
    """Ouverte à tous ; un élève actif gagne les points du barème à sa première réponse juste du jour."""
    try:
        correction = await defis.corriger(db, defi_id, entree.choix, utilisateur)
    except defis.AucunDefi:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce défi est introuvable.") from None
    except ValueError as erreur:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erreur)) from None
    return _correction(correction)
