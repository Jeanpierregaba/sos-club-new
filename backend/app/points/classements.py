"""Classements courants (spec 036, ADR-0013) : calculés à la demande depuis le registre.

Un score reste une somme de lignes (ADR-0004). Les classements publics ne montrent jamais d'identifiant
utilisateur, de nom complet ni de contact ; le routeur choisit le schéma qui expose ou non les identifiants.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.clubs import activation
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification
from app.points.bareme import ACTION_CORRECTION
from app.points.carte_classement import CarteClassement, Vue
from app.points.models import MouvementPoints, Semestre
from app.points.service import semestre_en_cours
from app.referentiel.models import Dre, Etablissement, Iesg


class Categorie(StrEnum):
    eleves = "eleves"
    encadreurs = "encadreurs"
    clubs = "clubs"


class Niveau(StrEnum):
    national = "national"
    dre = "dre"


class Periode(StrEnum):
    semestre = "semestre"
    historique = "historique"


class DreRequise(Exception):
    """Le niveau DRE exige un code de DRE."""


class DreIntrouvable(Exception):
    """La DRE demandée n'existe pas ou n'est pas active."""


class HorsDuClub(Exception):
    """Le lecteur n'est ni membre, ni encadreur rattaché, ni président d'un club."""


class HorsClassement(Exception):
    """Un visiteur ou un admin n'a pas de classement personnel."""


@dataclass(frozen=True)
class LigneClassement:
    rang: int
    nom: str
    club: str | None
    dre: str
    points: int | float
    # Renseignés pour l'admin seulement ; jamais servis par une route publique.
    utilisateur_id: UUID | None = None
    club_id: UUID | None = None
    etablissement: str | None = None


@dataclass(frozen=True)
class Classement:
    categorie: Categorie
    niveau: Niveau
    dre: Dre | None
    periode: Periode
    semestre: Semestre | None
    total: int
    lignes: list[LigneClassement]


@dataclass(frozen=True)
class LigneClub:
    rang: int
    nom: str
    points: int
    utilisateur_id: UUID
    est_moi: bool


@dataclass(frozen=True)
class ClassementClub:
    club: Club
    categorie: Categorie
    periode: Periode
    semestre: Semestre | None
    total: int
    lignes: list[LigneClub]


@dataclass(frozen=True)
class RangPersonnel:
    points: int
    rang_club: int | None
    rang_dre: int | None
    rang_national: int | None
    classe: bool


@dataclass(frozen=True)
class ClassementPersonnel:
    categorie: Categorie
    club: Club | None
    semestre_en_cours: Semestre | None
    semestre: RangPersonnel
    historique: RangPersonnel


def _nom_encadreur(prenom: str, nom: str) -> str:
    """Le prénom et l'initiale du nom, comme les signatures d'articles."""
    initiale = f" {nom.strip()[:1].upper()}." if nom.strip() else ""
    return f"{prenom.strip()}{initiale}"


async def _resoudre_dre(db: AsyncSession, niveau: Niveau, dre_code: str | None) -> Dre | None:
    if niveau is Niveau.national:
        return None
    if not dre_code:
        raise DreRequise
    dre = await db.scalar(select(Dre).where(Dre.code == dre_code, Dre.actif.is_(True)))
    if dre is None:
        raise DreIntrouvable
    return dre


def _points_par_utilisateur(periode: Periode, semestre: Semestre | None) -> Select:
    requete = select(
        MouvementPoints.utilisateur_id.label("utilisateur_id"),
        func.sum(MouvementPoints.montant).label("points"),
    ).group_by(MouvementPoints.utilisateur_id)
    if periode is Periode.semestre and semestre is not None:
        requete = requete.where(MouvementPoints.semestre_id == semestre.id)
    return requete.subquery()


def _base_eleves(points: Select, periode: Periode, dre_code: str | None) -> Select:
    club = aliased(Club)
    requete = (
        select(
            Eleve.utilisateur_id,
            Eleve.pseudonyme.label("nom"),
            club.id.label("club_id"),
            club.nom.label("club"),
            Dre.nom.label("dre"),
            points.c.points,
        )
        .join(points, points.c.utilisateur_id == Eleve.utilisateur_id)
        .join(Utilisateur, Utilisateur.id == Eleve.utilisateur_id)
        .join(Etablissement, Etablissement.id == Eleve.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .outerjoin(
            Adhesion,
            and_(Adhesion.eleve_id == Eleve.utilisateur_id, Adhesion.etat == EtatAdhesion.active),
        )
        .outerjoin(club, club.id == Adhesion.club_id)
        .where(
            Utilisateur.role == Role.eleve,
            Utilisateur.statut == StatutCompte.actif,
            points.c.points > 0,
        )
    )
    if periode is Periode.semestre:
        # Un ancien élève garde ses archives et le total historique, jamais le classement du semestre.
        requete = requete.where(Utilisateur.ancien_eleve_le.is_(None))
    if dre_code is not None:
        requete = requete.where(Dre.code == dre_code)
    return requete


def _base_encadreurs(points: Select, dre_code: str | None) -> Select:
    club = aliased(Club)
    requete = (
        select(
            Encadreur.utilisateur_id,
            Utilisateur.prenom,
            Utilisateur.nom,
            club.id.label("club_id"),
            club.nom.label("club"),
            Dre.nom.label("dre"),
            points.c.points,
        )
        .join(points, points.c.utilisateur_id == Encadreur.utilisateur_id)
        .join(Utilisateur, Utilisateur.id == Encadreur.utilisateur_id)
        .join(Etablissement, Etablissement.id == Encadreur.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .outerjoin(
            Rattachement,
            and_(
                Rattachement.encadreur_id == Encadreur.utilisateur_id,
                Rattachement.etat == EtatRattachement.actif,
            ),
        )
        .outerjoin(club, club.id == Rattachement.club_id)
        .where(
            Utilisateur.role == Role.encadreur,
            Utilisateur.statut == StatutCompte.actif,
            Encadreur.etat == EtatVerification.actif,
            points.c.points > 0,
        )
    )
    if dre_code is not None:
        requete = requete.where(Dre.code == dre_code)
    return requete


def _base_clubs(periode: Periode, semestre: Semestre | None, dre_code: str | None) -> Select:
    requete = (
        select(
            Club.id.label("club_id"),
            Club.nom.label("nom"),
            Etablissement.nom.label("etablissement"),
            Dre.nom.label("dre"),
            func.sum(MouvementPoints.demi_points_club).label("demi_points"),
        )
        .join(MouvementPoints, MouvementPoints.club_id == Club.id)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .where(activation.en_service(), MouvementPoints.demi_points_club.is_not(None))
        .group_by(Club.id, Club.nom, Etablissement.nom, Dre.nom)
        .having(func.sum(MouvementPoints.demi_points_club) > 0)
    )
    if periode is Periode.semestre and semestre is not None:
        requete = requete.where(MouvementPoints.semestre_id == semestre.id)
    if dre_code is not None:
        requete = requete.where(Dre.code == dre_code)
    return requete


async def _compter(db: AsyncSession, requete: Select) -> int:
    return int(await db.scalar(select(func.count()).select_from(requete.subquery())) or 0)


async def classement_public(
    db: AsyncSession,
    *,
    categorie: Categorie = Categorie.eleves,
    niveau: Niveau = Niveau.national,
    dre_code: str | None = None,
    periode: Periode = Periode.semestre,
    page: int = 1,
    par_page: int = 50,
) -> Classement:
    dre = await _resoudre_dre(db, niveau, dre_code)
    semestre = await semestre_en_cours(db)
    if periode is Periode.semestre and semestre is None:
        return Classement(categorie, niveau, dre, periode, None, 0, [])

    if categorie is Categorie.clubs:
        base = _base_clubs(periode, semestre, dre.code if dre else None)
        sous = base.subquery()
        requete = select(
            sous.c.club_id,
            sous.c.nom,
            sous.c.etablissement,
            sous.c.dre,
            sous.c.demi_points,
            func.rank().over(order_by=sous.c.demi_points.desc()).label("rang"),
        ).order_by(
            sous.c.demi_points.desc(),
            func.lower(sous.c.nom),
            sous.c.club_id,
        )
        total = await _compter(db, base)
        lignes = [
            LigneClassement(
                rang=int(ligne.rang),
                nom=ligne.nom,
                club=None,
                dre=ligne.dre,
                points=float(ligne.demi_points) / 2,
                club_id=ligne.club_id,
                etablissement=ligne.etablissement,
            )
            for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
        ]
        return Classement(categorie, niveau, dre, periode, semestre, total, lignes)

    points = _points_par_utilisateur(periode, semestre)
    if categorie is Categorie.eleves:
        base = _base_eleves(points, periode, dre.code if dre else None)
        sous = base.subquery()
        requete = select(
            sous.c.utilisateur_id,
            sous.c.nom,
            sous.c.club_id,
            sous.c.club,
            sous.c.dre,
            sous.c.points,
            func.rank().over(order_by=sous.c.points.desc()).label("rang"),
        ).order_by(
            sous.c.points.desc(),
            func.lower(sous.c.nom),
            func.coalesce(sous.c.club, ""),
            sous.c.utilisateur_id,
        )
        total = await _compter(db, base)
        lignes = [
            LigneClassement(
                rang=int(ligne.rang),
                nom=ligne.nom,
                club=ligne.club,
                dre=ligne.dre,
                points=int(ligne.points),
                utilisateur_id=ligne.utilisateur_id,
                club_id=ligne.club_id,
            )
            for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
        ]
        return Classement(categorie, niveau, dre, periode, semestre, total, lignes)

    base = _base_encadreurs(points, dre.code if dre else None)
    sous = base.subquery()
    requete = select(
        sous.c.utilisateur_id,
        sous.c.prenom,
        sous.c.nom,
        sous.c.club_id,
        sous.c.club,
        sous.c.dre,
        sous.c.points,
        func.rank().over(order_by=sous.c.points.desc()).label("rang"),
    ).order_by(
        sous.c.points.desc(),
        func.lower(sous.c.prenom),
        func.lower(sous.c.nom),
        sous.c.utilisateur_id,
    )
    total = await _compter(db, base)
    lignes = [
        LigneClassement(
            rang=int(ligne.rang),
            nom=_nom_encadreur(ligne.prenom, ligne.nom),
            club=ligne.club,
            dre=ligne.dre,
            points=int(ligne.points),
            utilisateur_id=ligne.utilisateur_id,
            club_id=ligne.club_id,
        )
        for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
    ]
    return Classement(categorie, niveau, dre, periode, semestre, total, lignes)


# Classement interne d'un club ---------------------------------------------------------------------------------


def _points_du_club(periode: Periode, semestre: Semestre | None, club_id: UUID) -> Select:
    requete = (
        select(
            MouvementPoints.utilisateur_id.label("utilisateur_id"),
            func.sum(MouvementPoints.montant).label("points"),
        )
        # Les gains comptent pour le club où ils ont été faits ; une correction de l'équipe (et son annulation) n'a
        # pas de club et vaut pour le club actuel, sinon elle ne changerait jamais le classement interne.
        .where(
            or_(
                MouvementPoints.club_id == club_id,
                and_(MouvementPoints.club_id.is_(None), MouvementPoints.action == ACTION_CORRECTION),
            )
        )
        .group_by(MouvementPoints.utilisateur_id)
    )
    if periode is Periode.semestre and semestre is not None:
        requete = requete.where(MouvementPoints.semestre_id == semestre.id)
    return requete.subquery()


def _base_club_eleves(points: Select, club_id: UUID, periode: Periode) -> Select:
    requete = (
        select(
            Eleve.utilisateur_id,
            Eleve.pseudonyme.label("nom"),
            points.c.points,
        )
        .join(points, points.c.utilisateur_id == Eleve.utilisateur_id)
        .join(Utilisateur, Utilisateur.id == Eleve.utilisateur_id)
        .join(
            Adhesion,
            and_(
                Adhesion.eleve_id == Eleve.utilisateur_id,
                Adhesion.club_id == club_id,
                Adhesion.etat == EtatAdhesion.active,
            ),
        )
        .where(
            Utilisateur.role == Role.eleve,
            Utilisateur.statut == StatutCompte.actif,
            points.c.points > 0,
        )
    )
    if periode is Periode.semestre:
        requete = requete.where(Utilisateur.ancien_eleve_le.is_(None))
    return requete


def _base_club_encadreurs(points: Select, club_id: UUID) -> Select:
    return (
        select(
            Encadreur.utilisateur_id,
            Utilisateur.prenom,
            Utilisateur.nom,
            points.c.points,
        )
        .join(points, points.c.utilisateur_id == Encadreur.utilisateur_id)
        .join(Utilisateur, Utilisateur.id == Encadreur.utilisateur_id)
        .join(
            Rattachement,
            and_(
                Rattachement.encadreur_id == Encadreur.utilisateur_id,
                Rattachement.club_id == club_id,
                Rattachement.etat == EtatRattachement.actif,
            ),
        )
        .where(
            Utilisateur.role == Role.encadreur,
            Utilisateur.statut == StatutCompte.actif,
            Encadreur.etat == EtatVerification.actif,
            points.c.points > 0,
        )
    )


async def _club_de(db: AsyncSession, utilisateur: Utilisateur) -> Club | None:
    if utilisateur.role is Role.eleve:
        club = await db.scalar(
            select(Club)
            .join(Adhesion, Adhesion.club_id == Club.id)
            .where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat == EtatAdhesion.active)
            .limit(1)
        )
        if club is not None:
            return club
        return await db.scalar(select(Club).where(Club.president_id == utilisateur.id).limit(1))
    if utilisateur.role is Role.encadreur:
        return await db.scalar(
            select(Club)
            .join(Rattachement, Rattachement.club_id == Club.id)
            .where(
                Rattachement.encadreur_id == utilisateur.id,
                Rattachement.etat == EtatRattachement.actif,
            )
            .limit(1)
        )
    return None


async def club_du_lecteur(db: AsyncSession, utilisateur: Utilisateur) -> Club:
    club = await _club_de(db, utilisateur)
    if club is None:
        raise HorsDuClub
    return club


async def classement_du_club(
    db: AsyncSession,
    club: Club,
    *,
    categorie: Categorie = Categorie.eleves,
    periode: Periode = Periode.semestre,
    page: int = 1,
    par_page: int = 50,
    lecteur_id: UUID | None = None,
) -> ClassementClub:
    if categorie not in (Categorie.eleves, Categorie.encadreurs):
        raise ValueError("Un classement interne oppose les élèves ou les encadreurs, jamais les clubs.")
    semestre = await semestre_en_cours(db)
    if periode is Periode.semestre and semestre is None:
        return ClassementClub(club, categorie, periode, None, 0, [])

    if categorie is Categorie.eleves:
        base = _base_club_eleves(_points_du_club(periode, semestre, club.id), club.id, periode)
        sous = base.subquery()
        requete = select(
            sous.c.utilisateur_id,
            sous.c.nom,
            sous.c.points,
            func.rank().over(order_by=sous.c.points.desc()).label("rang"),
        ).order_by(sous.c.points.desc(), func.lower(sous.c.nom), sous.c.utilisateur_id)
        total = await _compter(db, base)
        lignes = [
            LigneClub(
                rang=int(ligne.rang),
                nom=ligne.nom,
                points=int(ligne.points),
                utilisateur_id=ligne.utilisateur_id,
                est_moi=ligne.utilisateur_id == lecteur_id,
            )
            for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
        ]
        return ClassementClub(club, categorie, periode, semestre, total, lignes)

    points = _points_par_utilisateur(periode, semestre)
    base = _base_club_encadreurs(points, club.id)
    sous = base.subquery()
    requete = select(
        sous.c.utilisateur_id,
        sous.c.prenom,
        sous.c.nom,
        sous.c.points,
        func.rank().over(order_by=sous.c.points.desc()).label("rang"),
    ).order_by(
        sous.c.points.desc(),
        func.lower(sous.c.prenom),
        func.lower(sous.c.nom),
        sous.c.utilisateur_id,
    )
    total = await _compter(db, base)
    lignes = [
        LigneClub(
            rang=int(ligne.rang),
            nom=_nom_encadreur(ligne.prenom, ligne.nom),
            points=int(ligne.points),
            utilisateur_id=ligne.utilisateur_id,
            est_moi=ligne.utilisateur_id == lecteur_id,
        )
        for ligne in (await db.execute(requete.limit(par_page).offset((page - 1) * par_page))).all()
    ]
    return ClassementClub(club, categorie, periode, semestre, total, lignes)


# Rangs personnels ---------------------------------------------------------------------------------------------


async def _rang_dans(db: AsyncSession, base: Select, utilisateur_id: UUID) -> int | None:
    sous = base.subquery()
    classe = select(
        sous.c.utilisateur_id,
        func.rank().over(order_by=sous.c.points.desc()).label("rang"),
    ).subquery()
    rang = await db.scalar(select(classe.c.rang).where(classe.c.utilisateur_id == utilisateur_id))
    return int(rang) if rang is not None else None


async def _points_utilisateur(
    db: AsyncSession,
    periode: Periode,
    semestre: Semestre | None,
    utilisateur_id: UUID,
    *,
    club_id: UUID | None = None,
) -> int:
    requete = select(func.coalesce(func.sum(MouvementPoints.montant), 0)).where(
        MouvementPoints.utilisateur_id == utilisateur_id
    )
    if club_id is not None:
        requete = requete.where(MouvementPoints.club_id == club_id)
    if periode is Periode.semestre and semestre is not None:
        requete = requete.where(MouvementPoints.semestre_id == semestre.id)
    return int(await db.scalar(requete) or 0)


async def _dre_code_de(db: AsyncSession, utilisateur: Utilisateur) -> str | None:
    if utilisateur.role is Role.eleve:
        return await db.scalar(
            select(Iesg.dre_code)
            .join(Etablissement, Etablissement.iesg_id == Iesg.id)
            .join(Eleve, Eleve.etablissement_id == Etablissement.id)
            .where(Eleve.utilisateur_id == utilisateur.id)
        )
    if utilisateur.role is Role.encadreur:
        return await db.scalar(
            select(Iesg.dre_code)
            .join(Etablissement, Etablissement.iesg_id == Iesg.id)
            .join(Encadreur, Encadreur.etablissement_id == Etablissement.id)
            .where(Encadreur.utilisateur_id == utilisateur.id)
        )
    return None


async def _rang_personnel(
    db: AsyncSession,
    utilisateur: Utilisateur,
    categorie: Categorie,
    club: Club | None,
    periode: Periode,
    semestre: Semestre | None,
) -> RangPersonnel:
    points = await _points_utilisateur(db, periode, semestre, utilisateur.id)
    if periode is Periode.semestre and semestre is None:
        return RangPersonnel(points=points, rang_club=None, rang_dre=None, rang_national=None, classe=False)

    points_par_utilisateur = _points_par_utilisateur(periode, semestre)
    if categorie is Categorie.eleves:
        base_national = _base_eleves(points_par_utilisateur, periode, None)
    else:
        base_national = _base_encadreurs(points_par_utilisateur, None)
    rang_national = await _rang_dans(db, base_national, utilisateur.id)

    dre_code = await _dre_code_de(db, utilisateur)
    rang_dre = None
    if dre_code is not None:
        if categorie is Categorie.eleves:
            base_dre = _base_eleves(points_par_utilisateur, periode, dre_code)
        else:
            base_dre = _base_encadreurs(points_par_utilisateur, dre_code)
        rang_dre = await _rang_dans(db, base_dre, utilisateur.id)

    rang_club = None
    if club is not None:
        if categorie is Categorie.eleves:
            base_club = _base_club_eleves(_points_du_club(periode, semestre, club.id), club.id, periode)
        else:
            base_club = _base_club_encadreurs(points_par_utilisateur, club.id)
        rang_club = await _rang_dans(db, base_club, utilisateur.id)

    return RangPersonnel(
        points=points,
        rang_club=rang_club,
        rang_dre=rang_dre,
        rang_national=rang_national,
        classe=rang_national is not None,
    )


async def classement_personnel(db: AsyncSession, utilisateur: Utilisateur) -> ClassementPersonnel:
    if utilisateur.role is Role.eleve:
        categorie = Categorie.eleves
    elif utilisateur.role is Role.encadreur:
        categorie = Categorie.encadreurs
    else:
        raise HorsClassement
    club = await _club_de(db, utilisateur)
    semestre = await semestre_en_cours(db)
    return ClassementPersonnel(
        categorie=categorie,
        club=club,
        semestre_en_cours=semestre,
        semestre=await _rang_personnel(db, utilisateur, categorie, club, Periode.semestre, semestre),
        historique=await _rang_personnel(db, utilisateur, categorie, club, Periode.historique, semestre),
    )


# La carte « Partager mon classement » (spec 044) ------------------------------------------------------------


class NonClasse(Exception):
    """Aucun point dans cette vue : pas de rang à montrer."""


class SansSemestre(Exception):
    """Pas de semestre en cours : seule la vue historique existe."""


async def carte_personnelle(db: AsyncSession, utilisateur: Utilisateur, vue: Vue, periode: Periode) -> CarteClassement:
    """Le rang de la personne dans la vue choisie, avec les mêmes bases que `/hall-of-fame` et « Mon espace »."""
    if utilisateur.role is Role.eleve:
        categorie = Categorie.eleves
    elif utilisateur.role is Role.encadreur:
        categorie = Categorie.encadreurs
    else:
        raise HorsClassement
    semestre = await semestre_en_cours(db)
    if periode is Periode.semestre and semestre is None:
        raise SansSemestre
    club = await _club_de(db, utilisateur)
    dre_code = await _dre_code_de(db, utilisateur)
    points_par_utilisateur = _points_par_utilisateur(periode, semestre)
    if vue is Vue.club:
        if club is None:
            raise HorsDuClub
        base = (
            _base_club_eleves(_points_du_club(periode, semestre, club.id), club.id, periode)
            if categorie is Categorie.eleves
            else _base_club_encadreurs(points_par_utilisateur, club.id)
        )
    else:
        perimetre = dre_code if vue is Vue.dre else None
        if vue is Vue.dre and perimetre is None:
            raise NonClasse
        base = (
            _base_eleves(points_par_utilisateur, periode, perimetre)
            if categorie is Categorie.eleves
            else _base_encadreurs(points_par_utilisateur, perimetre)
        )
    rang = await _rang_dans(db, base, utilisateur.id)
    if rang is None:
        raise NonClasse
    sous = base.subquery()
    points_vue = await db.scalar(select(sous.c.points).where(sous.c.utilisateur_id == utilisateur.id))
    if categorie is Categorie.eleves:
        nom = await db.scalar(select(Eleve.pseudonyme).where(Eleve.utilisateur_id == utilisateur.id)) or ""
    else:
        nom = _nom_encadreur(utilisateur.prenom, utilisateur.nom)
    return CarteClassement(
        nom=nom,
        niveau=vue.value,
        dre=await db.scalar(select(Dre.nom).where(Dre.code == dre_code)) if dre_code else None,
        club=club.nom if club else None,
        periode=periode.value,
        semestre=semestre.libelle if periode is Periode.semestre and semestre else None,
        rang=rang,
        classes=await _compter(db, base),
        points=int(points_vue or 0),
        le=datetime.now(UTC),
    )


# Le rang du club, pour ses membres et ses encadreurs ----------------------------------------------------------


@dataclass(frozen=True)
class RangDuClub:
    club: Club
    semestre: Semestre | None
    # Les points du club sur le semestre en cours : la moitié des gains de ses élèves (ADR-0012).
    points: float
    rang_dre: int | None
    rang_national: int | None


async def _rang_club_dans(db: AsyncSession, base: Select, club_id: UUID) -> int | None:
    sous = base.subquery()
    classe = select(sous.c.club_id, func.rank().over(order_by=sous.c.demi_points.desc()).label("rang")).subquery()
    rang = await db.scalar(select(classe.c.rang).where(classe.c.club_id == club_id))
    return int(rang) if rang is not None else None


async def rang_du_club(db: AsyncSession, club: Club) -> RangDuClub:
    """Le rang du club au classement public des clubs du semestre en cours, dans sa DRE et au national. Un club
    hors service ou sans point n'est pas classé, comme sur `/hall-of-fame`."""
    semestre = await semestre_en_cours(db)
    if semestre is None:
        return RangDuClub(club=club, semestre=None, points=0, rang_dre=None, rang_national=None)
    demi = await db.scalar(
        select(func.coalesce(func.sum(MouvementPoints.demi_points_club), 0)).where(
            MouvementPoints.club_id == club.id, MouvementPoints.semestre_id == semestre.id
        )
    )
    dre_code = await db.scalar(
        select(Iesg.dre_code)
        .join(Etablissement, Etablissement.iesg_id == Iesg.id)
        .where(Etablissement.id == club.etablissement_id)
    )
    periode = Periode.semestre
    return RangDuClub(
        club=club,
        semestre=semestre,
        points=int(demi or 0) / 2,
        rang_dre=await _rang_club_dans(db, _base_clubs(periode, semestre, dre_code), club.id) if dre_code else None,
        rang_national=await _rang_club_dans(db, _base_clubs(periode, semestre, None), club.id),
    )


# Photo de fin de semestre (spec 037) ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LigneAFiger:
    utilisateur_id: UUID
    rang: int
    rang_brut: int
    pseudonyme: str
    club: str | None
    dre: str
    points: int
    atteint_le: datetime


async def classement_a_figer(db: AsyncSession, semestre: Semestre, *, limite: int | None = 50) -> list[LigneAFiger]:
    """Le classement national des élèves d'un semestre, tel que le public le voit (mêmes exclusions), avec les
    égalités départagées par la règle publiée : à points égaux, passe devant l'élève dont la dernière ligne de points
    du semestre est la plus ancienne (c'est elle qui a fixé le total final), puis l'ordre alphabétique du pseudonyme.
    `limite=None` rend tout le classement. `rang_brut` garde l'égalité visible dans l'archive."""
    points = (
        select(
            MouvementPoints.utilisateur_id.label("utilisateur_id"),
            func.sum(MouvementPoints.montant).label("points"),
            func.max(MouvementPoints.cree_le).label("atteint_le"),
        )
        .where(MouvementPoints.semestre_id == semestre.id)
        .group_by(MouvementPoints.utilisateur_id)
        .subquery()
    )
    sous = _base_eleves(points, Periode.semestre, None).add_columns(points.c.atteint_le).subquery()
    requete = (
        select(
            sous.c.utilisateur_id,
            sous.c.nom,
            sous.c.club,
            sous.c.dre,
            sous.c.points,
            sous.c.atteint_le,
            func.rank().over(order_by=sous.c.points.desc()).label("rang_brut"),
            func.row_number()
            .over(
                order_by=(sous.c.points.desc(), sous.c.atteint_le.asc(), func.lower(sous.c.nom), sous.c.utilisateur_id)
            )
            .label("rang"),
        )
        .order_by("rang")
        .limit(limite)
    )
    return [
        LigneAFiger(
            utilisateur_id=ligne.utilisateur_id,
            rang=int(ligne.rang),
            rang_brut=int(ligne.rang_brut),
            pseudonyme=ligne.nom,
            club=ligne.club,
            dre=ligne.dre,
            points=int(ligne.points),
            atteint_le=ligne.atteint_le,
        )
        for ligne in (await db.execute(requete)).all()
    ]
