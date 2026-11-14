"""Administration des points (spec 017) : semestres et barème, sous /admin/points."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.clubs import activation
from app.clubs.models import Club
from app.comptes.dependances import utilisateur_courant
from app.comptes.models import Role, Utilisateur
from app.db import get_session
from app.points import administration, annees, classements
from app.points.schemas import (
    ClassementClubAdminInterne,
    ClassementClubInterne,
    ClassementClubsAdmin,
    ClassementClubsPublic,
    ClassementPersonnesAdmin,
    ClassementPersonnesPublic,
    ClubClasse,
    DreResume,
    LigneBaremeAdmin,
    LigneBaremeModification,
    LigneClubAdmin,
    LigneClubAdminInterne,
    LigneClubInterne,
    LigneClubPublic,
    LignePersonneAdmin,
    LignePersonnePublic,
    SemestreAdmin,
    SemestreCreation,
    SemestreModification,
    SemestrePublic,
)
from app.points.schemas import (
    ClassementPersonnel as ClassementPersonnelSchema,
)
from app.points.schemas import (
    RangPersonnel as RangPersonnelSchema,
)
from app.referentiel.administration import Introuvable, Refus

Base = Annotated[AsyncSession, Depends(get_session)]

router_admin = APIRouter(prefix="/admin/points", tags=["admin"])

Lecteur = Annotated[Acces, Depends(exiger_permission("points", Action.consulter))]
# Les semestres et le barème valent pour tout le pays : un responsable de DRE ne les change pas.
Modificateur = Annotated[Acces, Depends(exiger_permission("points", Action.modifier, national=True))]


@contextmanager
def _traduire_refus() -> Iterator[None]:
    try:
        yield
    except Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Élément introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None


@router_admin.get("/semestres")
async def lister_semestres(_: Lecteur, db: Base) -> list[SemestreAdmin]:
    return await administration.lister_semestres(db)


@router_admin.post("/semestres", status_code=status.HTTP_201_CREATED)
async def creer_semestre(entree: SemestreCreation, request: Request, acces: Modificateur, db: Base) -> SemestreAdmin:
    with _traduire_refus():
        return await administration.creer_semestre(db, acces, entree, adresse_ip(request))


@router_admin.patch("/semestres/{semestre_id}")
async def modifier_semestre(
    semestre_id: UUID, entree: SemestreModification, request: Request, acces: Modificateur, db: Base
) -> SemestreAdmin:
    with _traduire_refus():
        return await administration.modifier_semestre(db, acces, semestre_id, entree, adresse_ip(request))


@router_admin.get("/bareme")
async def lister_bareme(_: Lecteur, db: Base) -> list[LigneBaremeAdmin]:
    return await administration.lister_bareme(db)


@router_admin.patch("/bareme/{code}")
async def modifier_bareme(
    code: str, entree: LigneBaremeModification, request: Request, acces: Modificateur, db: Base
) -> LigneBaremeAdmin:
    with _traduire_refus():
        return await administration.modifier_bareme(db, acces, code, entree, adresse_ip(request))


# Années académiques et anciens élèves (spec 034, lot 4) -----------------------------------------------------------


@router_admin.get("/annees")
async def lister_annees(_: Lecteur, db: Base) -> list[annees.AnneeAdmin]:
    return await annees.lister(db)


@router_admin.post("/annees", status_code=status.HTTP_201_CREATED)
async def creer_annee(
    entree: annees.AnneeCreation, request: Request, acces: Modificateur, db: Base
) -> annees.AnneeAdmin:
    with _traduire_refus():
        return await annees.creer(db, acces, entree, adresse_ip(request))


@router_admin.post("/annees/{annee_id}/cloture")
async def cloturer_annee(annee_id: UUID, request: Request, acces: Modificateur, db: Base) -> annees.AnneeAdmin:
    with _traduire_refus():
        return await annees.cloturer(db, acces, annee_id, adresse_ip(request))


@router_admin.post("/anciens-eleves/{eleve_id}")
async def passer_ancien_eleve(eleve_id: UUID, request: Request, acces: Modificateur, db: Base) -> None:
    with _traduire_refus():
        await annees.passer_ancien_eleve(db, acces, eleve_id, adresse_ip(request))


# Le total du club, pour ses membres (spec 034) ------------------------------------------------------------------

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/mon-club")
async def points_de_mon_club(
    moi: Annotated[Utilisateur, Depends(utilisateur_courant)], db: Base
) -> annees.PointsDuClub:
    try:
        return await annees.points_du_club(db, moi)
    except annees.HorsDuClub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu n'es rattaché à aucun club.") from None


# Classements publics et personnels (spec 036) -----------------------------------------------------------------

router_classements = APIRouter(prefix="/classements", tags=["classements"])

CategoriePublique = Annotated[classements.Categorie, Query()]
NiveauPublic = Annotated[classements.Niveau, Query()]
PeriodePublique = Annotated[classements.Periode, Query()]
Page = Annotated[int, Query(ge=1)]
ParPage = Annotated[int, Query(ge=1, le=100)]


def _dre_resume(dre: Any) -> DreResume | None:
    return DreResume(code=dre.code, nom=dre.nom) if dre is not None else None


def _semestre_public(semestre: Any) -> SemestrePublic | None:
    if semestre is None:
        return None
    return SemestrePublic(libelle=semestre.libelle, debut=semestre.debut, fin=semestre.fin)


def _classement_public(
    resultat: classements.Classement, page: int, par_page: int
) -> ClassementPersonnesPublic | ClassementClubsPublic:
    commun = {
        "niveau": resultat.niveau.value,
        "dre": _dre_resume(resultat.dre),
        "periode": resultat.periode.value,
        "semestre": _semestre_public(resultat.semestre),
        "page": page,
        "par_page": par_page,
        "total": resultat.total,
    }
    if resultat.categorie is classements.Categorie.clubs:
        return ClassementClubsPublic(
            categorie="clubs",
            lignes=[
                LigneClubPublic(
                    rang=ligne.rang,
                    club_id=ligne.club_id,
                    nom=ligne.nom,
                    etablissement=ligne.etablissement or "",
                    dre=ligne.dre,
                    points=float(ligne.points),
                )
                for ligne in resultat.lignes
            ],
            **commun,
        )
    return ClassementPersonnesPublic(
        categorie=resultat.categorie.value,
        lignes=[
            LignePersonnePublic(
                rang=ligne.rang,
                nom=ligne.nom,
                club=ligne.club,
                dre=ligne.dre,
                points=int(ligne.points),
            )
            for ligne in resultat.lignes
        ],
        **commun,
    )


def _classement_admin(
    resultat: classements.Classement, page: int, par_page: int
) -> ClassementPersonnesAdmin | ClassementClubsAdmin:
    commun = {
        "niveau": resultat.niveau.value,
        "dre": _dre_resume(resultat.dre),
        "periode": resultat.periode.value,
        "semestre": _semestre_public(resultat.semestre),
        "page": page,
        "par_page": par_page,
        "total": resultat.total,
    }
    if resultat.categorie is classements.Categorie.clubs:
        return ClassementClubsAdmin(
            categorie="clubs",
            lignes=[
                LigneClubAdmin(
                    rang=ligne.rang,
                    club_id=ligne.club_id,
                    nom=ligne.nom,
                    etablissement=ligne.etablissement or "",
                    dre=ligne.dre,
                    points=float(ligne.points),
                )
                for ligne in resultat.lignes
            ],
            **commun,
        )
    return ClassementPersonnesAdmin(
        categorie=resultat.categorie.value,
        lignes=[
            LignePersonneAdmin(
                rang=ligne.rang,
                utilisateur_id=ligne.utilisateur_id,
                nom=ligne.nom,
                club_id=ligne.club_id,
                club=ligne.club,
                dre=ligne.dre,
                points=int(ligne.points),
            )
            for ligne in resultat.lignes
        ],
        **commun,
    )


def _club_interne(resultat: classements.ClassementClub, page: int, par_page: int) -> ClassementClubInterne:
    return ClassementClubInterne(
        club=ClubClasse(id=resultat.club.id, nom=resultat.club.nom),
        categorie=resultat.categorie.value,
        periode=resultat.periode.value,
        semestre=_semestre_public(resultat.semestre),
        page=page,
        par_page=par_page,
        total=resultat.total,
        lignes=[
            LigneClubInterne(
                rang=ligne.rang,
                nom=ligne.nom,
                points=ligne.points,
                est_moi=ligne.est_moi,
            )
            for ligne in resultat.lignes
        ],
    )


def _club_admin(
    club: Club, resultat: classements.ClassementClub, page: int, par_page: int
) -> ClassementClubAdminInterne:
    return ClassementClubAdminInterne(
        club=ClubClasse(id=club.id, nom=club.nom),
        statut=activation.statut_effectif(club, activation.maintenant()).value,
        categorie=resultat.categorie.value,
        periode=resultat.periode.value,
        semestre=_semestre_public(resultat.semestre),
        page=page,
        par_page=par_page,
        total=resultat.total,
        lignes=[
            LigneClubAdminInterne(
                rang=ligne.rang,
                utilisateur_id=ligne.utilisateur_id,
                nom=ligne.nom,
                points=ligne.points,
            )
            for ligne in resultat.lignes
        ],
    )


def _classement_personnel(resultat: classements.ClassementPersonnel) -> ClassementPersonnelSchema:
    return ClassementPersonnelSchema(
        categorie=resultat.categorie.value,
        club=ClubClasse(id=resultat.club.id, nom=resultat.club.nom) if resultat.club is not None else None,
        semestre=RangPersonnelSchema(**resultat.semestre.__dict__),
        historique=RangPersonnelSchema(**resultat.historique.__dict__),
    )


@router_classements.get("", response_model=ClassementPersonnesPublic | ClassementClubsPublic)
async def classement_public(
    db: Base,
    categorie: CategoriePublique = classements.Categorie.eleves,
    niveau: NiveauPublic = classements.Niveau.national,
    dre: Annotated[str | None, Query(max_length=30)] = None,
    periode: PeriodePublique = classements.Periode.semestre,
    page: Page = 1,
    par_page: ParPage = 50,
) -> ClassementPersonnesPublic | ClassementClubsPublic:
    try:
        resultat = await classements.classement_public(
            db,
            categorie=categorie,
            niveau=niveau,
            dre_code=dre,
            periode=periode,
            page=page,
            par_page=par_page,
        )
    except classements.DreRequise:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choisis une DRE pour ce classement.") from None
    except classements.DreIntrouvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette DRE est introuvable.") from None
    return _classement_public(resultat, page, par_page)


@router_classements.get("/moi", response_model=ClassementPersonnelSchema)
async def mon_classement(
    moi: Annotated[Utilisateur, Depends(utilisateur_courant)], db: Base
) -> ClassementPersonnelSchema:
    try:
        resultat = await classements.classement_personnel(db, moi)
    except classements.HorsClassement:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Les classements personnels sont réservés aux élèves et aux encadreurs."
        ) from None
    return _classement_personnel(resultat)


@router_classements.get("/mon-club", response_model=ClassementClubInterne)
async def classement_de_mon_club(
    moi: Annotated[Utilisateur, Depends(utilisateur_courant)],
    db: Base,
    categorie: Annotated[classements.Categorie, Query()] = classements.Categorie.eleves,
    periode: PeriodePublique = classements.Periode.semestre,
    page: Page = 1,
    par_page: ParPage = 50,
) -> ClassementClubInterne:
    if categorie is classements.Categorie.clubs:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choisis les élèves ou les encadreurs.")
    if moi.role not in (Role.eleve, Role.encadreur):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu n'as pas accès à cette page.")
    try:
        club = await classements.club_du_lecteur(db, moi)
    except classements.HorsDuClub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tu n'es rattaché à aucun club.") from None
    resultat = await classements.classement_du_club(
        db,
        club,
        categorie=categorie,
        periode=periode,
        page=page,
        par_page=par_page,
        lecteur_id=moi.id,
    )
    return _club_interne(resultat, page, par_page)


# Admin — classements (spec 036) -------------------------------------------------------------------------------


@router_admin.get(
    "/classements",
    response_model=ClassementPersonnesAdmin | ClassementClubsAdmin | ClassementClubAdminInterne,
)
async def classements_admin(
    _: Lecteur,
    db: Base,
    categorie: CategoriePublique = classements.Categorie.eleves,
    niveau: NiveauPublic = classements.Niveau.national,
    dre: Annotated[str | None, Query(max_length=30)] = None,
    periode: PeriodePublique = classements.Periode.semestre,
    club_id: UUID | None = None,
    page: Page = 1,
    par_page: ParPage = 50,
) -> ClassementPersonnesAdmin | ClassementClubsAdmin | ClassementClubAdminInterne:
    if club_id is not None:
        if categorie is classements.Categorie.clubs:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choisis les élèves ou les encadreurs.")
        club = await db.get(Club, club_id)
        if club is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce club est introuvable.")
        resultat = await classements.classement_du_club(
            db,
            club,
            categorie=categorie,
            periode=periode,
            page=page,
            par_page=par_page,
        )
        return _club_admin(club, resultat, page, par_page)
    try:
        resultat = await classements.classement_public(
            db,
            categorie=categorie,
            niveau=niveau,
            dre_code=dre,
            periode=periode,
            page=page,
            par_page=par_page,
        )
    except classements.DreRequise:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Choisis une DRE pour ce classement.") from None
    except classements.DreIntrouvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cette DRE est introuvable.") from None
    return _classement_admin(resultat, page, par_page)
