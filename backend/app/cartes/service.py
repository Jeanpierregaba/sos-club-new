"""Délivrance et état des cartes numériques (spec 040).

La validité, le club et le rôle ne sont pas stockés : ils se lisent ici, à chaque fois, depuis le compte, l'affiliation
ou le rattachement et la présidence. Une suspension de compte, une affiliation retirée ou une passation se voient donc
sur la carte sans qu'aucune autre partie du code n'ait à la tenir à jour.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid7

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.cartes.models import PREFIXES, SEQUENCE_NUMERO, Carte, TypeCarte
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification
from app.referentiel.models import Etablissement

Role = Literal["membre", "president", "encadreur"]
Cause = Literal["compte_supprime", "compte_suspendu", "suspendue_par_l_equipe", "non_verifie", "sans_rattachement"]


@dataclass(frozen=True)
class EtatCarte:
    """Tout ce qu'on sait d'une carte à cet instant. Seuls `type`, `numero`, `club` et `valide` sont publics."""

    carte_id: UUID
    type: TypeCarte
    numero: str
    code: str
    delivree_le: datetime
    valide: bool
    cause: Cause | None
    role: Role
    prenom: str | None
    nom: str | None
    etablissement: str | None
    club: str | None
    suspendue_le: datetime | None
    motif_suspension: str | None


async def delivrer(db: AsyncSession, utilisateur_id: UUID, type_carte: TypeCarte) -> None:
    """Délivre la carte du compte s'il n'en a pas. Idempotente, y compris sous appels simultanés (contrainte unique
    sur le compte) ; un numéro tiré pour rien laisse un trou dans la séquence, jamais un doublon."""
    if await db.scalar(select(Carte.id).where(Carte.utilisateur_id == utilisateur_id)) is not None:
        return
    rang = await db.scalar(SEQUENCE_NUMERO.next_value())
    await db.execute(
        insert(Carte)
        .values(
            id=uuid7(),
            utilisateur_id=utilisateur_id,
            type=type_carte,
            numero=f"{PREFIXES[type_carte]}-{rang:06d}",
            code=secrets.token_urlsafe(24),
        )
        .on_conflict_do_nothing(index_elements=[Carte.utilisateur_id])
    )


async def carte_du_compte(db: AsyncSession, utilisateur_id: UUID) -> Carte | None:
    return await db.scalar(select(Carte).where(Carte.utilisateur_id == utilisateur_id))


async def etat_du_compte(db: AsyncSession, utilisateur_id: UUID) -> EtatCarte | None:
    carte = await carte_du_compte(db, utilisateur_id)
    return await etat_de(db, carte) if carte is not None else None


async def _club_membre(db: AsyncSession, eleve_id: UUID) -> Club | None:
    return await db.scalar(
        select(Club)
        .join(Adhesion, Adhesion.club_id == Club.id)
        .where(Adhesion.eleve_id == eleve_id, Adhesion.etat == EtatAdhesion.active)
    )


async def _club_encadreur(db: AsyncSession, encadreur_id: UUID) -> Club | None:
    return await db.scalar(
        select(Club)
        .join(Rattachement, Rattachement.club_id == Club.id)
        .where(Rattachement.encadreur_id == encadreur_id, Rattachement.etat == EtatRattachement.actif)
        .limit(1)
    )


async def etat_de(db: AsyncSession, carte: Carte) -> EtatCarte:
    utilisateur = await db.get(Utilisateur, carte.utilisateur_id) if carte.utilisateur_id else None
    role: Role = "encadreur" if carte.type is TypeCarte.encadreur else "membre"
    club: Club | None = None
    etablissement_id: UUID | None = None
    cause: Cause | None = None
    if utilisateur is None:
        cause = "compte_supprime"
    elif carte.type is TypeCarte.membre:
        eleve = await db.get(Eleve, utilisateur.id)
        etablissement_id = eleve.etablissement_id if eleve else None
        club = await _club_membre(db, utilisateur.id)
        if club is not None and club.president_id == utilisateur.id:
            role = "president"
    else:
        encadreur = await db.get(Encadreur, utilisateur.id)
        etablissement_id = encadreur.etablissement_id if encadreur else None
        club = await _club_encadreur(db, utilisateur.id)
        if encadreur is None or encadreur.etat is not EtatVerification.actif:
            cause = "non_verifie"
        elif club is None:
            cause = "sans_rattachement"
    if utilisateur is not None and utilisateur.statut is not StatutCompte.actif:
        cause = "compte_suspendu"
    elif utilisateur is not None and carte.suspendue_le is not None:
        cause = "suspendue_par_l_equipe"
    etablissement = await db.get(Etablissement, etablissement_id) if etablissement_id else None
    return EtatCarte(
        carte_id=carte.id,
        type=carte.type,
        numero=carte.numero,
        code=carte.code,
        delivree_le=carte.delivree_le,
        valide=cause is None,
        cause=cause,
        role=role,
        prenom=utilisateur.prenom if utilisateur else None,
        nom=utilisateur.nom if utilisateur else None,
        etablissement=etablissement.nom if etablissement else None,
        club=club.nom if club else None,
        suspendue_le=carte.suspendue_le,
        motif_suspension=carte.motif_suspension,
    )
