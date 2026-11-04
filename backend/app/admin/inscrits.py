"""Annuaire des inscrits (CDC admin, 4.1 et 12B.1). Les filtres par club, DRE et établissement arrivent avec les
specs des clubs."""

from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.admin.models import JournalAudit
from app.admin.schemas import (
    EvenementJournal,
    FiltresInscrits,
    Inscrit,
    InscritDetail,
    PageInscrits,
    ProfilEleveAdmin,
)
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.comptes.service import couper_sessions
from app.eleves.models import Eleve
from app.eleves.service import etablissement_eleve, points_eleve

HISTORIQUE = [
    "inscrit_suspendu",
    "inscrit_reactive",
    "inscription_eleve",
    "profil_eleve_modifie",
    "pseudonyme_impose",
    "mot_de_passe_change",
    "mot_de_passe_reinitialise",
]


class Introuvable(Exception):
    pass


class Refus(Exception):
    pass


def requete_filtree(filtres: FiltresInscrits) -> Select[tuple[Utilisateur]]:
    requete = select(Utilisateur).outerjoin(Eleve, Eleve.utilisateur_id == Utilisateur.id)
    if filtres.recherche and filtres.recherche.strip():
        # Les caractères spéciaux de LIKE sont échappés : « 100% » cherche bien « 100% ».
        texte = filtres.recherche.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        motif = f"%{texte}%"
        requete = requete.where(
            or_(
                func.lower(Utilisateur.nom).like(motif, escape="\\"),
                func.lower(Utilisateur.prenom).like(motif, escape="\\"),
                func.lower(Utilisateur.identifiant).like(motif, escape="\\"),
                func.lower(Utilisateur.email).like(motif, escape="\\"),
                func.lower(Eleve.pseudonyme).like(motif, escape="\\"),
            )
        )
    if filtres.profil:
        requete = requete.where(Utilisateur.role == filtres.profil)
    if filtres.statut:
        requete = requete.where(Utilisateur.statut == filtres.statut)
    if filtres.inscrit_depuis:
        requete = requete.where(Utilisateur.cree_le >= filtres.inscrit_depuis)
    if filtres.inscrit_avant:
        requete = requete.where(Utilisateur.cree_le < filtres.inscrit_avant)
    return requete


async def compter(db: AsyncSession, filtres: FiltresInscrits) -> int:
    sous_requete = requete_filtree(filtres).with_only_columns(Utilisateur.id).subquery()
    return await db.scalar(select(func.count()).select_from(sous_requete)) or 0


async def lister(db: AsyncSession, filtres: FiltresInscrits, page: int, par_page: int) -> PageInscrits:
    requete = (
        requete_filtree(filtres)
        .order_by(Utilisateur.cree_le.desc(), Utilisateur.id)
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    inscrits = [Inscrit.model_validate(u) for u in (await db.scalars(requete)).all()]
    return PageInscrits(total=await compter(db, filtres), page=page, par_page=par_page, inscrits=inscrits)


async def historique(db: AsyncSession, utilisateur_id: UUID) -> list[EvenementJournal]:
    """Événements d'un compte, lus dans le journal : il fait foi."""
    requete = (
        select(JournalAudit)
        .where(JournalAudit.cible_type == "utilisateur", JournalAudit.cible_id == str(utilisateur_id))
        .where(JournalAudit.action.in_(HISTORIQUE))
        .order_by(JournalAudit.quand.desc())
    )
    return [EvenementJournal.model_validate(e) for e in (await db.scalars(requete)).all()]


async def detail(db: AsyncSession, utilisateur_id: UUID) -> InscritDetail:
    utilisateur = await db.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise Introuvable
    donnees: dict[str, Any] = Inscrit.model_validate(utilisateur).model_dump()
    eleve = await db.get(Eleve, utilisateur.id)
    profil = (
        ProfilEleveAdmin(
            pseudonyme=eleve.pseudonyme,
            classe=eleve.classe,
            charte_version=eleve.charte_version,
            etablissement=await etablissement_eleve(db, eleve.etablissement_id),
            points=await points_eleve(db, utilisateur.id, 50),
        )
        if eleve
        else None
    )
    return InscritDetail(**donnees, historique=await historique(db, utilisateur.id), eleve=profil)


async def changer_statut(
    db: AsyncSession, auteur: Acces, utilisateur_id: UUID, nouveau: StatutCompte, motif: str, ip: str
) -> InscritDetail:
    """Élèves et encadreurs seulement : les collaborateurs se gèrent depuis leur propre écran."""
    utilisateur = await db.scalar(select(Utilisateur).where(Utilisateur.id == utilisateur_id).with_for_update())
    if utilisateur is None:
        raise Introuvable
    if utilisateur.role is Role.admin:
        raise Refus("Un collaborateur se gère depuis l'écran des collaborateurs.")
    if utilisateur.statut is nouveau:
        raise Refus("Ce compte a déjà ce statut.")
    avant = utilisateur.statut
    utilisateur.statut = nouveau
    if nouveau is not StatutCompte.actif:
        await couper_sessions(db, utilisateur.id)
    journaliser(
        db,
        "inscrit_suspendu" if nouveau is StatutCompte.suspendu else "inscrit_reactive",
        auteur.utilisateur,
        cible_type="utilisateur",
        cible_id=utilisateur.id,
        details={"avant": avant.value, "apres": nouveau.value, "motif": motif},
        adresse_ip=ip,
    )
    await db.commit()
    return await detail(db, utilisateur.id)
