"""Registre des points pour l'équipe nationale (spec 036, ADR-0013) : lecture filtrée, recherche de bénéficiaires,
correction motivée et annulation d'une ligne.

Le registre ne se réécrit jamais : une correction est une nouvelle ligne `admin.correction`, une annulation une
ligne de signe opposé liée à l'originale. Chaque écriture laisse une entrée au journal d'audit, dans la même
transaction.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import Select, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.points.bareme import ACTION_CORRECTION, CERTIFICATION_ELEVE, CERTIFICATION_ENCADREUR
from app.points.models import MONTANT_MAX, AnneeAcademique, LigneBareme, MouvementPoints, Semestre
from app.points.service import annee_en_cours, semestre_en_cours
from app.referentiel.administration import Introuvable, Refus

MOTIF_MIN = 10
MOTIF_MAX = 500
ROLES_CORRIGIBLES = (Role.eleve, Role.encadreur)
# Ces points suivent un certificat : on les retire en révoquant le certificat, sinon le certificat resterait valide
# sans ses points et une révocation ultérieure n'aurait plus rien à retirer.
ACTIONS_DE_CERTIFICAT = (CERTIFICATION_ELEVE, CERTIFICATION_ENCADREUR)


@dataclass(frozen=True)
class FiltresRegistre:
    semestre_id: UUID | None = None
    annee_id: UUID | None = None
    du: date | None = None
    au: date | None = None
    action: str | None = None
    beneficiaire: Role | None = None
    club_id: UUID | None = None
    correction: bool | None = None
    recherche: str | None = None


def _motif(motif: str) -> str:
    propre = motif.strip()
    if not MOTIF_MIN <= len(propre) <= MOTIF_MAX:
        raise Refus(f"Le motif doit faire entre {MOTIF_MIN} et {MOTIF_MAX} caractères.", 422)
    return propre


def _motif_like(texte: str) -> str:
    """Un motif LIKE littéral : les jokers saisis sont échappés."""
    echappe = texte.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{echappe.lower()}%"


# Lecture -------------------------------------------------------------------------------------------------------


def _requete_registre(filtres: FiltresRegistre) -> Select:
    auteur = aliased(Utilisateur)
    requete = (
        select(
            MouvementPoints,
            Utilisateur.role,
            Utilisateur.identifiant,
            Utilisateur.prenom,
            Utilisateur.nom,
            Eleve.pseudonyme,
            LigneBareme.libelle.label("action_libelle"),
            Semestre.libelle.label("semestre"),
            AnneeAcademique.libelle.label("annee"),
            Club.nom.label("club_nom"),
            auteur.prenom.label("auteur_prenom"),
            auteur.nom.label("auteur_nom"),
            auteur.identifiant.label("auteur_identifiant"),
        )
        .join(Utilisateur, Utilisateur.id == MouvementPoints.utilisateur_id)
        .join(LigneBareme, LigneBareme.code == MouvementPoints.action)
        .outerjoin(Eleve, Eleve.utilisateur_id == MouvementPoints.utilisateur_id)
        .outerjoin(Semestre, Semestre.id == MouvementPoints.semestre_id)
        .outerjoin(AnneeAcademique, AnneeAcademique.id == MouvementPoints.annee_id)
        .outerjoin(Club, Club.id == MouvementPoints.club_id)
        .outerjoin(auteur, auteur.id == MouvementPoints.valide_par)
    )
    if filtres.semestre_id is not None:
        requete = requete.where(MouvementPoints.semestre_id == filtres.semestre_id)
    if filtres.annee_id is not None:
        requete = requete.where(MouvementPoints.annee_id == filtres.annee_id)
    # Les dates sont celles de Lomé, à UTC+0 toute l'année.
    if filtres.du is not None:
        requete = requete.where(MouvementPoints.cree_le >= datetime.combine(filtres.du, time.min, UTC))
    if filtres.au is not None:
        lendemain = datetime.combine(filtres.au + timedelta(days=1), time.min, UTC)
        requete = requete.where(MouvementPoints.cree_le < lendemain)
    if filtres.action:
        requete = requete.where(MouvementPoints.action == filtres.action)
    if filtres.beneficiaire is not None:
        requete = requete.where(Utilisateur.role == filtres.beneficiaire)
    if filtres.club_id is not None:
        requete = requete.where(MouvementPoints.club_id == filtres.club_id)
    if filtres.correction is not None:
        est_correction = MouvementPoints.action == ACTION_CORRECTION
        requete = requete.where(est_correction if filtres.correction else ~est_correction)
    if filtres.recherche and filtres.recherche.strip():
        motif = _motif_like(filtres.recherche.strip())
        requete = requete.where(
            or_(
                func.lower(Utilisateur.identifiant).like(motif, escape="\\"),
                func.lower(Utilisateur.prenom).like(motif, escape="\\"),
                func.lower(Utilisateur.nom).like(motif, escape="\\"),
                func.lower(func.coalesce(Eleve.pseudonyme, "")).like(motif, escape="\\"),
            )
        )
    return requete


@dataclass(frozen=True)
class PageRegistre:
    total: int
    lignes: list[dict[str, Any]]


def _ligne(rangee: Any) -> dict[str, Any]:
    mouvement: MouvementPoints = rangee.MouvementPoints
    valide_par = None
    if mouvement.valide_par is not None:
        valide_par = {
            "nom": f"{rangee.auteur_prenom} {rangee.auteur_nom}".strip(),
            "identifiant": rangee.auteur_identifiant,
        }
    return {
        "id": mouvement.id,
        "cree_le": mouvement.cree_le,
        "utilisateur_id": mouvement.utilisateur_id,
        "role": rangee.role.value,
        "identifiant": rangee.identifiant,
        "prenom": rangee.prenom,
        "nom": rangee.nom,
        "pseudonyme": rangee.pseudonyme,
        "action": mouvement.action,
        "action_libelle": rangee.action_libelle,
        "montant": mouvement.montant,
        "points_club": mouvement.demi_points_club / 2 if mouvement.demi_points_club is not None else None,
        "semestre": rangee.semestre,
        "annee": rangee.annee,
        "club": {"id": mouvement.club_id, "nom": rangee.club_nom} if mouvement.club_id is not None else None,
        "cle": mouvement.cle,
        "valide_par": valide_par,
        "motif": mouvement.motif,
        "annule_id": mouvement.annule_id,
        "est_annulation": mouvement.annule_id is not None,
        "est_correction": mouvement.action == ACTION_CORRECTION,
    }


async def lister(db: AsyncSession, filtres: FiltresRegistre, page: int, par_page: int) -> PageRegistre:
    requete = _requete_registre(filtres)
    total = int(await db.scalar(select(func.count()).select_from(requete.subquery())) or 0)
    rangees = await db.execute(
        requete.order_by(MouvementPoints.cree_le.desc(), MouvementPoints.id.desc())
        .limit(par_page)
        .offset((page - 1) * par_page)
    )
    # Une ligne annulée est signalée : l'équipe ne tente pas de l'annuler une seconde fois.
    lignes = [_ligne(rangee) for rangee in rangees.all()]
    ids = [ligne["id"] for ligne in lignes]
    annulees = set()
    if ids:
        annulees = set(await db.scalars(select(MouvementPoints.annule_id).where(MouvementPoints.annule_id.in_(ids))))
    for ligne in lignes:
        ligne["annulee"] = ligne["id"] in annulees
    return PageRegistre(total=total, lignes=lignes)


async def lister_une(db: AsyncSession, ligne_id: UUID) -> dict[str, Any]:
    """Une ligne du registre, sous la forme de la liste (réponse d'une correction ou d'une annulation)."""
    rangee = (await db.execute(_requete_registre(FiltresRegistre()).where(MouvementPoints.id == ligne_id))).one()
    ligne = _ligne(rangee)
    ligne["annulee"] = (
        await db.scalar(select(MouvementPoints.id).where(MouvementPoints.annule_id == ligne_id))
    ) is not None
    return ligne


# Recherche de bénéficiaires ------------------------------------------------------------------------------------


async def chercher_beneficiaires(db: AsyncSession, texte: str) -> list[dict[str, Any]]:
    """Au plus 20 élèves ou encadreurs dont le pseudonyme, l'identifiant, le prénom ou le nom contient le texte."""
    motif = _motif_like(texte.strip())
    club_eleve = aliased(Club)
    club_encadreur = aliased(Club)
    total = (
        select(func.coalesce(func.sum(MouvementPoints.montant), 0))
        .where(MouvementPoints.utilisateur_id == Utilisateur.id)
        .correlate(Utilisateur)
        .scalar_subquery()
    )
    eleve = Utilisateur.role == Role.eleve
    requete = (
        select(
            Utilisateur.id,
            Utilisateur.role,
            Utilisateur.identifiant,
            Utilisateur.prenom,
            Utilisateur.nom,
            Eleve.pseudonyme,
            func.coalesce(club_eleve.nom, club_encadreur.nom).label("club"),
            total.label("points_total"),
        )
        .outerjoin(Eleve, Eleve.utilisateur_id == Utilisateur.id)
        .outerjoin(Encadreur, Encadreur.utilisateur_id == Utilisateur.id)
        .outerjoin(Adhesion, (Adhesion.eleve_id == Utilisateur.id) & (Adhesion.etat == EtatAdhesion.active))
        .outerjoin(club_eleve, club_eleve.id == Adhesion.club_id)
        .outerjoin(
            Rattachement,
            (Rattachement.encadreur_id == Utilisateur.id) & (Rattachement.etat == EtatRattachement.actif),
        )
        .outerjoin(club_encadreur, club_encadreur.id == Rattachement.club_id)
        .where(
            Utilisateur.role.in_(ROLES_CORRIGIBLES),
            or_(
                func.lower(Utilisateur.identifiant).like(motif, escape="\\"),
                # Le nom complet d'un élève n'est pas cherché : l'équipe le trouve par pseudonyme ou identifiant.
                (~eleve) & func.lower(Utilisateur.prenom).like(motif, escape="\\"),
                (~eleve) & func.lower(Utilisateur.nom).like(motif, escape="\\"),
                func.lower(func.coalesce(Eleve.pseudonyme, "")).like(motif, escape="\\"),
            ),
        )
        .order_by(Utilisateur.identifiant)
        .limit(20)
    )
    resultats = []
    for rangee in (await db.execute(requete)).all():
        if rangee.role is Role.eleve:
            nom_public = rangee.pseudonyme or rangee.identifiant
        else:
            nom_public = f"{rangee.prenom} {rangee.nom}".strip()
        resultats.append(
            {
                "id": rangee.id,
                "role": rangee.role.value,
                "nom_public": nom_public,
                "identifiant": rangee.identifiant,
                "club": rangee.club,
                "points_total": int(rangee.points_total),
            }
        )
    return resultats


# Correction et annulation --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Ecriture:
    ligne: MouvementPoints
    creee: bool


async def _contexte_journal(db: AsyncSession, ligne: MouvementPoints) -> dict[str, Any]:
    semestre = await db.get(Semestre, ligne.semestre_id) if ligne.semestre_id else None
    annee = await db.get(AnneeAcademique, ligne.annee_id) if ligne.annee_id else None
    club = await db.get(Club, ligne.club_id) if ligne.club_id else None
    return {
        "beneficiaire": str(ligne.utilisateur_id),
        "montant": ligne.montant,
        "points_club": ligne.demi_points_club / 2 if ligne.demi_points_club is not None else None,
        "motif": ligne.motif,
        "semestre": semestre.libelle if semestre else None,
        "annee": annee.libelle if annee else None,
        "club": {"id": str(club.id), "nom": club.nom} if club else None,
        "ligne_annulee": str(ligne.annule_id) if ligne.annule_id else None,
    }


async def corriger(
    db: AsyncSession, acces: Acces, utilisateur_id: UUID, montant: int, motif: str, cle: UUID, ip: str
) -> Ecriture:
    """Écrit une ligne `admin.correction` motivée, dans le semestre et l'année en cours, sans part de club. Une
    seconde requête avec la même clé renvoie la ligne déjà écrite."""
    if montant == 0 or abs(montant) > MONTANT_MAX:
        raise Refus(f"Le montant doit être non nul et compris entre -{MONTANT_MAX} et {MONTANT_MAX}.", 422)
    motif = _motif(motif)
    cible = await db.get(Utilisateur, utilisateur_id)
    if cible is None:
        raise Introuvable
    if cible.role not in ROLES_CORRIGIBLES:
        raise Refus("Seuls les points d'un élève ou d'un encadreur se corrigent.", 422)

    cle_registre = f"correction:{cle}"
    existante = await db.scalar(select(MouvementPoints).where(MouvementPoints.cle == cle_registre))
    if existante is not None:
        return _deja_ecrite(existante, utilisateur_id, montant, motif)

    semestre = await semestre_en_cours(db)
    annee = await annee_en_cours(db)
    ligne = await db.scalar(
        insert(MouvementPoints)
        .values(
            id=uuid7(),
            utilisateur_id=utilisateur_id,
            action=ACTION_CORRECTION,
            montant=montant,
            semestre_id=semestre.id if semestre else None,
            annee_id=annee.id if annee else None,
            cle=cle_registre,
            valide_par=acces.utilisateur.id,
            motif=motif,
        )
        .on_conflict_do_nothing(index_elements=["cle"])
        .returning(MouvementPoints)
    )
    if ligne is None:
        # Deux envois simultanés : l'autre requête vient d'écrire la ligne.
        existante = await db.scalar(select(MouvementPoints).where(MouvementPoints.cle == cle_registre))
        assert existante is not None
        return _deja_ecrite(existante, utilisateur_id, montant, motif)
    journaliser(
        db, "points_corriges", acces.utilisateur, cible_type="mouvement_points", cible_id=ligne.id,
        perimetre="national", details=await _contexte_journal(db, ligne), adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return Ecriture(ligne=ligne, creee=True)


def _deja_ecrite(existante: MouvementPoints, utilisateur_id: UUID, montant: int, motif: str) -> Ecriture:
    if existante.utilisateur_id != utilisateur_id or existante.montant != montant or existante.motif != motif:
        raise Refus("Cette clé de correction a déjà servi pour une autre correction.", 409)
    return Ecriture(ligne=existante, creee=False)


async def annuler_ligne(db: AsyncSession, acces: Acces, ligne_id: UUID, motif: str, ip: str) -> MouvementPoints:
    """Écrit la ligne opposée, liée à l'originale, dans le semestre et l'année d'origine, avec la part de club
    d'origine : le classement de la période visée est corrigé. L'originale ne change pas."""
    motif = _motif(motif)
    origine = await db.get(MouvementPoints, ligne_id)
    if origine is None:
        raise Introuvable
    if origine.annule_id is not None:
        raise Refus("Une annulation ne s'annule pas : saisis une correction.", 422)
    if origine.action in ACTIONS_DE_CERTIFICAT:
        raise Refus("Ces points suivent un certificat : révoque le certificat pour les retirer.", 422)
    ligne = await db.scalar(
        insert(MouvementPoints)
        .values(
            id=uuid7(),
            utilisateur_id=origine.utilisateur_id,
            action=origine.action,
            montant=-origine.montant,
            semestre_id=origine.semestre_id,
            annee_id=origine.annee_id,
            cle=f"annulation:{origine.id}",
            valide_par=acces.utilisateur.id,
            annule_id=origine.id,
            motif=motif,
            club_id=origine.club_id,
            demi_points_club=-origine.demi_points_club if origine.demi_points_club is not None else None,
        )
        .on_conflict_do_nothing()
        .returning(MouvementPoints)
    )
    if ligne is None:
        raise Refus("Cette ligne est déjà annulée.", 409)
    journaliser(
        db, "points_annules", acces.utilisateur, cible_type="mouvement_points", cible_id=ligne.id,
        perimetre="national", details=await _contexte_journal(db, ligne), adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return ligne
