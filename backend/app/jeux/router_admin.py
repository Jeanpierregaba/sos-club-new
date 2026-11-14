"""Les élèves à la carte Gold (spec 034, lot 2), pour l'équipe : éligibles au tirage au sort des fournitures
scolaires, dont le règlement reste à écrire. Pseudonyme, club et DRE seulement : aucun nom ni contact (RULES)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, exiger_permission
from app.clubs.models import Adhesion, Club, EtatAdhesion
from app.db import get_session
from app.eleves.models import Eleve
from app.jeux.models import EtoileObtenue
from app.quiz.models import NIVEAUX
from app.referentiel.models import Dre, Etablissement, Iesg

router = APIRouter(prefix="/admin/jeux", tags=["admin"])

Base = Annotated[AsyncSession, Depends(get_session)]
Lecteur = Annotated[Acces, Depends(exiger_permission("points", Action.consulter))]


class EleveGold(BaseModel):
    utilisateur_id: UUID
    pseudonyme: str
    club: str | None
    etablissement: str
    dre: str
    # La date de la quatrième étoile.
    gold_le: datetime


@router.get("/gold")
async def eleves_gold(acces: Lecteur, db: Base) -> list[EleveGold]:
    """Les élèves aux quatre étoiles, du plus ancien Gold au plus récent ; un responsable de DRE voit les siens."""
    gold = (
        select(EtoileObtenue.utilisateur_id, func.max(EtoileObtenue.obtenue_le).label("gold_le"))
        .group_by(EtoileObtenue.utilisateur_id)
        .having(func.count() == len(NIVEAUX))
        .subquery()
    )
    requete = (
        select(Eleve.utilisateur_id, Eleve.pseudonyme, Club.nom, Etablissement.nom, Dre.nom, gold.c.gold_le)
        .join(gold, gold.c.utilisateur_id == Eleve.utilisateur_id)
        .join(Etablissement, Etablissement.id == Eleve.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .outerjoin(Adhesion, (Adhesion.eleve_id == Eleve.utilisateur_id) & (Adhesion.etat == EtatAdhesion.active))
        .outerjoin(Club, Club.id == Adhesion.club_id)
        .order_by(gold.c.gold_le, Eleve.pseudonyme)
    )
    if acces.collaborateur.perimetre_dre is not None:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    return [
        EleveGold(utilisateur_id=uid, pseudonyme=pseudo, club=club, etablissement=etab, dre=dre, gold_le=le)
        for uid, pseudo, club, etab, dre, le in (await db.execute(requete)).all()
    ]
