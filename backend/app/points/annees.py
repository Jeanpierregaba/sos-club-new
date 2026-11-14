"""Années académiques, tableau de bord de l'élève et archives (spec 034, lot 4, ADR-0012).

Une année va de septembre à juillet ; l'équipe en fixe les dates. Chaque gain porte l'année où il a été crédité : un
compteur annuel est une somme filtrée, rien n'est remis à zéro ni effacé. La clôture fige le classement régional
annuel (pseudonyme et club seulement) ; après elle, aucun gain n'entre plus dans l'année.
"""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Integer, String, cast, func, literal, or_, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.certification.models import BadgeObtenu, Certificat, EtatCertificat, PlaceReussie
from app.clubs.models import Adhesion, Club, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.jeux import progression as jeux
from app.jeux.progression import ProgressionJeux
from app.moderation.models import Contenu, EtatContenu
from app.points.models import AnneeAcademique, ClassementAnnuel, LigneBareme, MouvementPoints, Parcours, SousCompte
from app.points.service import aujourd_hui, maintenant
from app.referentiel.administration import Introuvable, Refus
from app.referentiel.models import Dre, Etablissement, Iesg

VIOLATION_EXCLUSION = "23P01"
VIOLATION_UNICITE = "23505"


class AnneeAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    libelle: str
    debut: date
    fin: date
    cloturee_le: date | None = None
    version: int


class AnneeCreation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    libelle: str = Field(pattern=r"^\d{4}-\d{4}$")
    debut: date
    fin: date


class AnneeResume(BaseModel):
    libelle: str
    debut: date
    fin: date


class Archive(BaseModel):
    libelle: str
    points: int
    region: str | None
    rang: int | None


class DecompteCertification(BaseModel):
    quiz_valides: int
    badges: int
    certificat: bool
    points_quiz: int
    points_badges: int
    points_certificat: int


class DecompteVie(BaseModel):
    en_attente: int
    approuvees: int
    points: int


class TableauGamification(BaseModel):
    annee: AnneeResume | None
    total_annuel: int
    total_historique: int
    # La part de l'élève dans les points de son club cette année : la moitié de ses gains crédités au club.
    apport_club: float
    rang_regional: int | None
    region: str | None
    place_club: int | None
    parcours: dict[str, int]
    certification: DecompteCertification
    jeux: ProgressionJeux
    vie: DecompteVie
    archives: list[Archive]
    ancien_eleve: bool


def _admin(annee: AnneeAcademique) -> AnneeAdmin:
    return AnneeAdmin(
        id=annee.id,
        libelle=annee.libelle,
        debut=annee.debut,
        fin=annee.fin,
        cloturee_le=annee.cloturee_le.date() if annee.cloturee_le else None,
        version=annee.version,
    )


# Administration ----------------------------------------------------------------------------------------------------


async def lister(db: AsyncSession) -> list[AnneeAdmin]:
    return [_admin(a) for a in await db.scalars(select(AnneeAcademique).order_by(AnneeAcademique.debut.desc()))]


async def creer(db: AsyncSession, acces: Acces, entree: AnneeCreation, ip: str) -> AnneeAdmin:
    if entree.fin < entree.debut:
        raise Refus("La fin de l'année précède son début.", 422)
    autre = await db.scalar(
        select(AnneeAcademique).where(AnneeAcademique.debut <= entree.fin, AnneeAcademique.fin >= entree.debut)
    )
    if autre is not None:
        raise Refus(f"Cette année chevauche « {autre.libelle} ».", 409)
    annee = AnneeAcademique(libelle=entree.libelle, debut=entree.debut, fin=entree.fin)
    db.add(annee)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        code = getattr(erreur.orig, "sqlstate", None)
        if code == VIOLATION_EXCLUSION:
            raise Refus("Cette année chevauche une autre année.", 409) from None
        if code == VIOLATION_UNICITE:
            raise Refus("Une année porte déjà ce libellé.", 409) from None
        raise
    journaliser(
        db, "annee_creee", acces.utilisateur, cible_type="annee_academique", cible_id=annee.id, perimetre="national",
        details={"libelle": annee.libelle, "debut": annee.debut.isoformat(), "fin": annee.fin.isoformat()},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return _admin(annee)


def _points_annuels(annee: AnneeAcademique):
    """Les points annuels de chaque élève, avec la région de son établissement. Un élève passé ancien élève pendant
    l'année n'est pas classé ; passé ancien après la fin de l'année (fin de cursus), il garde sa place dans le
    classement de l'année où il a concouru."""
    apres_la_fin = datetime.combine(annee.fin + timedelta(days=1), time.min, tzinfo=UTC)
    return (
        select(
            MouvementPoints.utilisateur_id,
            func.sum(MouvementPoints.montant).label("points"),
            Dre.region.label("region"),
        )
        .join(Utilisateur, Utilisateur.id == MouvementPoints.utilisateur_id)
        .join(Eleve, Eleve.utilisateur_id == MouvementPoints.utilisateur_id)
        .join(Etablissement, Etablissement.id == Eleve.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .where(
            MouvementPoints.annee_id == annee.id,
            Utilisateur.role == Role.eleve,
            or_(Utilisateur.ancien_eleve_le.is_(None), Utilisateur.ancien_eleve_le >= apres_la_fin),
        )
        .group_by(MouvementPoints.utilisateur_id, Dre.region)
    )


async def cloturer(db: AsyncSession, acces: Acces, annee_id: UUID, ip: str) -> AnneeAdmin:
    """Fige le classement régional de l'année, une seule fois et après sa date de fin ; les gains suivants vont dans
    une autre année. Le verrou de l'année attend les crédits en cours (`points.annee_en_cours`)."""
    annee = await db.scalar(select(AnneeAcademique).where(AnneeAcademique.id == annee_id).with_for_update())
    if annee is None:
        raise Introuvable
    if annee.cloturee_le is not None:
        raise Refus("Cette année est déjà clôturée.", 409)
    if aujourd_hui() <= annee.fin:
        raise Refus("Une année se clôture seulement après sa date de fin.", 409)
    points = _points_annuels(annee).subquery()
    classes = (
        select(
            func.uuidv7(),
            literal(annee.id),
            cast(points.c.region, String),
            points.c.utilisateur_id,
            Eleve.pseudonyme,
            Club.nom,
            cast(points.c.points, Integer),
            func.rank().over(partition_by=points.c.region, order_by=points.c.points.desc()),
        )
        .join(Eleve, Eleve.utilisateur_id == points.c.utilisateur_id)
        .outerjoin(Adhesion, (Adhesion.eleve_id == points.c.utilisateur_id) & (Adhesion.etat == EtatAdhesion.active))
        .outerjoin(Club, Club.id == Adhesion.club_id)
        .where(points.c.points > 0)
    )
    resultat = await db.execute(
        insert(ClassementAnnuel)
        .from_select(["id", "annee_id", "region", "utilisateur_id", "pseudonyme", "club", "points", "rang"], classes)
        .on_conflict_do_nothing(index_elements=["annee_id", "utilisateur_id"])
    )
    annee.cloturee_le, annee.cloturee_par = maintenant(), acces.utilisateur.id
    journaliser(
        db, "annee_cloturee", acces.utilisateur, cible_type="annee_academique", cible_id=annee.id,
        perimetre="national", details={"libelle": annee.libelle, "classes": resultat.rowcount}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return _admin(annee)


async def passer_ancien_eleve(db: AsyncSession, acces: Acces, eleve_id: UUID, ip: str) -> None:
    compte = await db.get(Utilisateur, eleve_id)
    if compte is None or compte.role is not Role.eleve:
        raise Introuvable
    if compte.ancien_eleve_le is None:
        compte.ancien_eleve_le = maintenant()
        journaliser(
            db, "ancien_eleve", acces.utilisateur, cible_type="utilisateur", cible_id=compte.id, perimetre="national",
            details={}, adresse_ip=ip,
        )  # fmt: skip
    await db.commit()


# Tableau de bord de l'élève ----------------------------------------------------------------------------------------


async def _annee_du_jour(db: AsyncSession) -> AnneeAcademique | None:
    """L'année qui contient aujourd'hui. Entre la fin d'une année et la rentrée suivante, il n'y en a pas : l'année
    terminée passe dans les archives."""
    jour = aujourd_hui()
    return await db.scalar(
        select(AnneeAcademique).where(AnneeAcademique.debut <= jour, AnneeAcademique.fin >= jour).limit(1)
    )


async def tableau_gamification(db: AsyncSession, eleve: Utilisateur) -> TableauGamification:
    annee = await _annee_du_jour(db)
    du_joueur = MouvementPoints.utilisateur_id == eleve.id
    total_historique = int(
        await db.scalar(select(func.coalesce(func.sum(MouvementPoints.montant), 0)).where(du_joueur))
    )
    parcours = {p.value: 0 for p in Parcours}
    par_action: dict[str, int] = {}
    par_sous_compte = {sous_compte: 0 for sous_compte in SousCompte}
    total_annuel, apport = 0, 0.0
    rang_regional = place_club = None
    region = None
    if annee is not None:
        de_l_annee = (du_joueur, MouvementPoints.annee_id == annee.id)
        for parcours_action, sous_compte, action, montant in (
            await db.execute(
                select(
                    LigneBareme.parcours, LigneBareme.sous_compte, LigneBareme.code, func.sum(MouvementPoints.montant)
                )
                .join(LigneBareme, LigneBareme.code == MouvementPoints.action)
                .where(*de_l_annee)
                .group_by(LigneBareme.parcours, LigneBareme.sous_compte, LigneBareme.code)
            )
        ).all():
            if parcours_action is not None:
                parcours[parcours_action.value] += int(montant)
            if sous_compte is not None:
                par_sous_compte[sous_compte] += int(montant)
            par_action[action] = int(montant)
        total_annuel = int(
            await db.scalar(select(func.coalesce(func.sum(MouvementPoints.montant), 0)).where(*de_l_annee))
        )
        apport = (
            await db.scalar(select(func.coalesce(func.sum(MouvementPoints.demi_points_club), 0)).where(*de_l_annee))
        ) / 2
        # L'année du jour n'est jamais clôturée (la clôture vient après la fin) : le rang se calcule en direct ; le
        # rang figé se lit dans les archives.
        if total_annuel > 0 and eleve.ancien_eleve_le is None:
            sa_region = await _region(db, eleve.id)
            points = _points_annuels(annee).subquery()
            # Le rang sans fenêtre sur tout le pays : 1 + le nombre d'élèves de la même région qui ont plus de points.
            devant = await db.scalar(
                select(func.count())
                .select_from(points)
                .where(points.c.region == sa_region, points.c.points > total_annuel)
            )
            rang_regional, region = int(devant or 0) + 1, str(sa_region)
        club_id = await db.scalar(
            select(Adhesion.club_id).where(Adhesion.eleve_id == eleve.id, Adhesion.etat == EtatAdhesion.active)
        )
        if club_id is not None and total_annuel > 0 and eleve.ancien_eleve_le is None:
            membres = (
                select(MouvementPoints.utilisateur_id, func.sum(MouvementPoints.montant).label("points"))
                .join(
                    Adhesion,
                    (Adhesion.eleve_id == MouvementPoints.utilisateur_id) & (Adhesion.etat == EtatAdhesion.active),
                )
                .join(Utilisateur, Utilisateur.id == MouvementPoints.utilisateur_id)
                .where(
                    Adhesion.club_id == club_id,
                    MouvementPoints.annee_id == annee.id,
                    Utilisateur.ancien_eleve_le.is_(None),
                )
                .group_by(MouvementPoints.utilisateur_id)
                .subquery()
            )
            place_club = (
                int(
                    await db.scalar(select(func.count()).select_from(membres).where(membres.c.points > total_annuel))
                    or 0
                )
                + 1
            )

    places = int(
        await db.scalar(select(func.count()).select_from(PlaceReussie).where(PlaceReussie.utilisateur_id == eleve.id))
        or 0
    )
    badges = int(
        await db.scalar(select(func.count()).select_from(BadgeObtenu).where(BadgeObtenu.utilisateur_id == eleve.id))
        or 0
    )
    certificat = bool(
        await db.scalar(
            select(func.count())
            .select_from(Certificat)
            .where(Certificat.utilisateur_id == eleve.id, Certificat.etat == EtatCertificat.valide)
        )
    )
    contenus = dict(
        (
            await db.execute(
                select(Contenu.etat, func.count())
                .where(Contenu.auteur_id == eleve.id, Contenu.etat.in_((EtatContenu.en_attente, EtatContenu.publie)))
                .group_by(Contenu.etat)
            )
        ).all()
    )
    archives = await _archives(db, eleve.id, annee.id if annee else None)
    return TableauGamification(
        annee=AnneeResume(libelle=annee.libelle, debut=annee.debut, fin=annee.fin) if annee else None,
        total_annuel=total_annuel,
        total_historique=total_historique,
        apport_club=apport,
        rang_regional=rang_regional,
        region=region,
        place_club=place_club,
        parcours=parcours,
        certification=DecompteCertification(
            quiz_valides=places,
            badges=badges,
            certificat=certificat,
            points_quiz=par_action.get("eleve.quiz_certification", 0),
            points_badges=par_action.get("eleve.badge", 0),
            points_certificat=par_action.get("eleve.certification", 0),
        ),
        # La progression (quiz réussis, étoiles, carte Gold) court sur tout le parcours ; les points sont ceux de
        # l'année, comme pour la certification et la vie du site.
        jeux=(await jeux.progression(db, eleve.id)).model_copy(
            update={
                "points_quiz": par_sous_compte[SousCompte.quiz],
                "points_etoiles": par_sous_compte[SousCompte.etoiles],
                "total": parcours[Parcours.jeux.value],
            }
        ),
        vie=DecompteVie(
            en_attente=contenus.get(EtatContenu.en_attente, 0),
            approuvees=contenus.get(EtatContenu.publie, 0),
            points=parcours[Parcours.vie.value],
        ),
        archives=archives,
        ancien_eleve=eleve.ancien_eleve_le is not None,
    )


async def _region(db: AsyncSession, eleve_id: UUID) -> str | None:
    return await db.scalar(
        select(Dre.region)
        .join(Iesg, Iesg.dre_code == Dre.code)
        .join(Etablissement, Etablissement.iesg_id == Iesg.id)
        .join(Eleve, Eleve.etablissement_id == Etablissement.id)
        .where(Eleve.utilisateur_id == eleve_id)
    )


async def _archives(db: AsyncSession, eleve_id: UUID, sauf: UUID | None) -> list[Archive]:
    """Les années passées où l'élève a des points, avec son rang figé à la clôture s'il y en a un."""
    lignes = (
        await db.execute(
            select(
                AnneeAcademique.libelle,
                func.sum(MouvementPoints.montant),
                ClassementAnnuel.region,
                ClassementAnnuel.rang,
            )
            .join(MouvementPoints, MouvementPoints.annee_id == AnneeAcademique.id)
            .outerjoin(
                ClassementAnnuel,
                (ClassementAnnuel.annee_id == AnneeAcademique.id) & (ClassementAnnuel.utilisateur_id == eleve_id),
            )
            .where(MouvementPoints.utilisateur_id == eleve_id, AnneeAcademique.id != sauf if sauf else true())
            .group_by(AnneeAcademique.id, AnneeAcademique.libelle, ClassementAnnuel.region, ClassementAnnuel.rang)
            .order_by(AnneeAcademique.debut.desc())
        )
    ).all()
    return [
        Archive(libelle=libelle, points=int(points), region=region, rang=rang)
        for libelle, points, region, rang in lignes
    ]


# Le total du club (spec 034) ----------------------------------------------------------------------------------------


class PointsDuClub(BaseModel):
    annee: AnneeResume | None
    # La moitié des gains de ses élèves affiliés, cette année et depuis le début.
    total_annuel: float
    total_historique: float
    parcours: dict[str, float]
    # Jeux : points des quiz et points des étoiles, séparés (spec 034, section 3).
    jeux_quiz: float
    jeux_etoiles: float


class HorsDuClub(Exception):
    pass


async def points_du_club(db: AsyncSession, utilisateur: Utilisateur) -> PointsDuClub:
    """Le total annuel du club de l'utilisateur, par parcours : un encadreur rattaché ou un élève affilié le voit."""
    club_id = await db.scalar(
        select(Adhesion.club_id).where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat == EtatAdhesion.active)
    ) or await db.scalar(
        select(Rattachement.club_id).where(
            Rattachement.encadreur_id == utilisateur.id, Rattachement.etat == EtatRattachement.actif
        )
    )
    if club_id is None:
        raise HorsDuClub
    annee = await _annee_du_jour(db)
    du_club = MouvementPoints.club_id == club_id
    historique = await db.scalar(select(func.coalesce(func.sum(MouvementPoints.demi_points_club), 0)).where(du_club))
    parcours = {p.value: 0.0 for p in Parcours}
    quiz = etoiles = total = 0.0
    if annee is not None:
        for parcours_action, sous_compte, demi in (
            await db.execute(
                select(LigneBareme.parcours, LigneBareme.sous_compte, func.sum(MouvementPoints.demi_points_club))
                .join(LigneBareme, LigneBareme.code == MouvementPoints.action)
                .where(du_club, MouvementPoints.annee_id == annee.id)
                .group_by(LigneBareme.parcours, LigneBareme.sous_compte)
            )
        ).all():
            valeur = int(demi) / 2
            total += valeur
            if parcours_action is not None:
                parcours[parcours_action.value] += valeur
            if sous_compte is SousCompte.quiz:
                quiz += valeur
            elif sous_compte is SousCompte.etoiles:
                etoiles += valeur
    return PointsDuClub(
        annee=AnneeResume(libelle=annee.libelle, debut=annee.debut, fin=annee.fin) if annee else None,
        total_annuel=total,
        total_historique=int(historique) / 2,
        parcours=parcours,
        jeux_quiz=quiz,
        jeux_etoiles=etoiles,
    )
