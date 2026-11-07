"""Annuaire des inscrits (CDC admin, 4.1 et 12B.1). Les filtres par club, DRE et établissement arrivent avec les
specs des clubs."""

from typing import Any
from uuid import UUID

from sqlalchemy import Select, String, and_, case, cast, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.admin.models import JournalAudit
from app.admin.schemas import (
    ClubInscrit,
    EvenementJournal,
    FiltresInscrits,
    Inscrit,
    InscritDetail,
    PageInscrits,
    ProfilEleveAdmin,
    ProfilEncadreurAdmin,
)
from app.clubs.models import Club, EtatClub, EtatRattachement, Rattachement
from app.clubs.rattachements import liberer_passation
from app.comptes.inscription import etablissement_rattache
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.comptes.service import couper_sessions
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.moderation.models import Contenu
from app.points import service as points

HISTORIQUE = [
    "inscrit_suspendu",
    "inscrit_reactive",
    "inscription_eleve",
    "profil_eleve_modifie",
    "pseudonyme_impose",
    "mot_de_passe_change",
    "mot_de_passe_reinitialise",
    "inscription_encadreur",
    "profil_encadreur_modifie",
    "encadreur_active",
    "encadreur_refuse",
    "encadreur_redemande",
    "demande_club",
    "club_active",
    "club_refuse",
    "club_redemande",
    "club_passation_proposee",
    "club_passation",
    "club_passation_refusee",
    "club_passation_annulee",
    # Ses articles (spec 023) : soumission, retrait et décisions.
    "article_soumis",
    "article_retire",
    "article_approuve",
    "article_a_corriger",
    "article_refuse",
    "article_depublie",
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
        chiffres = "".join(c for c in texte if c.isdigit())
        requete = requete.where(
            or_(
                func.lower(Utilisateur.nom).like(motif, escape="\\"),
                func.lower(Utilisateur.prenom).like(motif, escape="\\"),
                func.lower(Utilisateur.identifiant).like(motif, escape="\\"),
                func.lower(Utilisateur.email).like(motif, escape="\\"),
                func.lower(Eleve.pseudonyme).like(motif, escape="\\"),
                # Le téléphone se cherche sans ses séparateurs, comme il est enregistré pour un encadreur. À partir de
                # 4 chiffres : « eleve1 » ne doit pas trouver tous les numéros qui contiennent un 1.
                Utilisateur.telephone.like(f"%{chiffres}%") if len(chiffres) >= 4 else false(),
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
        .where(
            or_(
                and_(JournalAudit.cible_type == "utilisateur", JournalAudit.cible_id == str(utilisateur_id)),
                # Les événements de ses contenus (spec 023) : le journal les cible par contenu.
                and_(
                    JournalAudit.cible_type == "contenu",
                    JournalAudit.cible_id.in_(
                        select(cast(Contenu.id, String)).where(Contenu.auteur_id == utilisateur_id)
                    ),
                ),
            )
        )
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
            etablissement=await etablissement_rattache(db, eleve.etablissement_id),
            points=await points.resume(db, utilisateur.id, 50),
            club=await _club_de(db, utilisateur.id),
        )
        if eleve
        else None
    )
    return InscritDetail(
        **donnees,
        historique=await historique(db, utilisateur.id),
        eleve=profil,
        encadreur=await _profil_encadreur(db, utilisateur.id),
    )


async def _club_de(db: AsyncSession, utilisateur_id: UUID) -> ClubInscrit | None:
    """Le club dont cet élève est demandeur ou président, actif ou en attente d'abord (spec 019)."""
    club = await db.scalar(
        select(Club)
        .where(or_(Club.demandeur_id == utilisateur_id, Club.president_id == utilisateur_id))
        .order_by(
            case((Club.etat == EtatClub.actif, 0), (Club.etat == EtatClub.en_attente, 1), else_=2),
            Club.demande_le.desc(),
        )
        .limit(1)
    )
    if club is None:
        return None
    return ClubInscrit(
        id=club.id,
        nom=club.nom,
        etat=club.etat,
        president=club.president_id == utilisateur_id and club.etat is EtatClub.actif,
        motif_refus=club.motif_refus,
    )


async def _profil_encadreur(db: AsyncSession, utilisateur_id: UUID) -> ProfilEncadreurAdmin | None:
    encadreur = await db.get(Encadreur, utilisateur_id)
    if encadreur is None:
        return None
    decideur = await db.get(Utilisateur, encadreur.decide_par) if encadreur.decide_par else None
    return ProfilEncadreurAdmin(
        fonction=encadreur.fonction,
        fonction_precision=encadreur.fonction_precision,
        charte_version=encadreur.charte_version,
        etablissement=await etablissement_rattache(db, encadreur.etablissement_id),
        etat=encadreur.etat,
        demande_le=encadreur.demande_le,
        decide_le=encadreur.decide_le,
        decide_par=f"{decideur.prenom} {decideur.nom}" if decideur else None,
        motif_refus=encadreur.motif_refus,
        points=await points.resume(db, utilisateur_id, 50),
    )


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
        if utilisateur.role is Role.encadreur:
            # Un encadreur suspendu ne confirme plus de passation : celles qui l'attendaient passent à l'admin
            # si le club n'a pas d'autre encadreur actif (spec 020).
            clubs = await db.scalars(
                select(Rattachement.club_id).where(
                    Rattachement.encadreur_id == utilisateur.id, Rattachement.etat == EtatRattachement.actif
                )
            )
            for club_id in clubs.all():
                await liberer_passation(db, club_id)
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
