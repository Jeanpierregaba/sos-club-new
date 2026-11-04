from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import collaborateurs, double_auth, exports, inscrits, tableau_de_bord
from app.admin.catalogue import DROITS_DES_ROLES, LIBELLES_ACTIONS, LIBELLES_ROLES, MODULES, SENSIBLES, Action
from app.admin.dependances import (
    MESSAGE_DOUBLE_AUTH,
    Acces,
    Collaborateur_,
    adresse_ip,
    exiger_permission,
    exiger_super_admin,
)
from app.admin.journal import journaliser
from app.admin.models import JournalAudit
from app.admin.schemas import (
    ActivationEntree,
    ActivationInfo,
    AdminMoi,
    Apercu,
    Catalogue,
    CodeSaisi,
    CodesSecours,
    CollaborateurDetail,
    CollaborateurResume,
    Droit,
    DroitsEntree,
    Enrolement,
    EvenementJournal,
    ExportCree,
    ExportEntree,
    ExportResume,
    FiltresInscrits,
    InscritDetail,
    InvitationCree,
    InvitationEntree,
    JetonEntree,
    ModuleCatalogue,
    MotifEntree,
    PageInscrits,
    PageJournal,
    RoleCatalogue,
    TableauDeBord,
)
from app.comptes.models import Role, StatutCompte
from app.comptes.router import _poser_cookie
from app.comptes.schemas import Moi
from app.comptes.service import (
    TropDEssais,
    effacer_essais_code,
    noter_echec_code,
    ouvrir_session,
    reserver_essai_code,
)
from app.config import settings
from app.db import get_session
from app.referentiel.models import Dre

router = APIRouter(prefix="/admin", tags=["admin"])
router_activation = APIRouter(prefix="/activation", tags=["admin"])

Base = Annotated[AsyncSession, Depends(get_session)]


def _droits(ensemble: set[tuple[str, Action]] | frozenset[tuple[str, Action]]) -> list[Droit]:
    return [Droit(module=m, action=a) for m, a in sorted(ensemble)]


async def collaborateur_pret(acces: Collaborateur_) -> Acces:
    """Tout collaborateur actif, double authentification faite si ses droits l'exigent."""
    if acces.double_auth_requise:
        raise HTTPException(status.HTTP_403_FORBIDDEN, MESSAGE_DOUBLE_AUTH)
    return acces


Pret = Annotated[Acces, Depends(collaborateur_pret)]


# Profil, catalogue, double authentification -----------------------------------------------------------------


@router.get("/moi")
async def moi(acces: Collaborateur_) -> AdminMoi:
    u, c = acces.utilisateur, acces.collaborateur
    return AdminMoi(
        id=u.id,
        identifiant=u.identifiant,
        prenom=u.prenom,
        nom=u.nom,
        email=u.email,
        super_admin=c.super_admin,
        perimetre_dre=c.perimetre_dre,
        droits=_droits(acces.droits),
        double_auth_active=acces.double_auth_active,
        double_auth_requise=acces.double_auth_requise,
    )


@router.get("/catalogue")
async def catalogue(_: Collaborateur_, db: Base) -> Catalogue:
    dre = (await db.execute(select(Dre.code, Dre.nom, Dre.actif).order_by(Dre.ordre))).all()
    return Catalogue(
        modules=[
            ModuleCatalogue(id=i, libelle=libelle, disponible=disponible, actions=list(actions))
            for i, (libelle, disponible, actions) in MODULES.items()
        ],
        actions=LIBELLES_ACTIONS,
        sensibles=_droits(SENSIBLES),
        roles=[RoleCatalogue(id=r, libelle=LIBELLES_ROLES[r], droits=_droits(d)) for r, d in DROITS_DES_ROLES.items()],
        dre={code: nom for code, nom, _ in dre},
        dre_actives=[code for code, _, actif in dre if actif],
    )


@router.post("/double-auth/enrolement")
async def enrolement(acces: Collaborateur_, db: Base) -> Enrolement:
    try:
        secret, svg = await double_auth.commencer_enrolement(db, acces.utilisateur)
    except double_auth.DejaActive:
        raise HTTPException(status.HTTP_409_CONFLICT, "La double authentification est déjà active.") from None
    return Enrolement(secret=secret, qr_svg=svg)


async def _verifier_avec_limite(
    db: AsyncSession, acces: Acces, request: Request, verification: Callable[[], Awaitable[object]]
) -> object:
    """Un code redemandé dans l'espace admin compte dans la même limite que la connexion : 5 erreurs par 15 minutes.
    Une session volée ne permet donc pas d'essayer tous les codes."""
    ip = adresse_ip(request)
    try:
        essai = await reserver_essai_code(db, acces.utilisateur, ip)
    except TropDEssais:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Trop d'essais. Réessaie dans 15 minutes.") from None
    resultat = await verification()
    # Un code faux n'écrit rien : la transaction ne contient que l'échec à noter.
    if not resultat:
        await noter_echec_code(db, acces.utilisateur, essai, ip)
        await db.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Code incorrect. Vérifie l'heure de ton téléphone.")
    await effacer_essais_code(db, acces.utilisateur)
    return resultat


@router.post("/double-auth/confirmer")
async def confirmer(entree: CodeSaisi, acces: Collaborateur_, db: Base, request: Request) -> CodesSecours:
    async def verification() -> list[str] | None:
        try:
            return await double_auth.confirmer_enrolement(db, acces.utilisateur, entree.code)
        except double_auth.EnrolementAbsent:
            raise HTTPException(status.HTTP_409_CONFLICT, "Commence par scanner le QR code.") from None
        except double_auth.DejaActive:
            raise HTTPException(status.HTTP_409_CONFLICT, "La double authentification est déjà active.") from None

    codes = await _verifier_avec_limite(db, acces, request, verification)
    journaliser(
        db, "double_auth_activee", acces.utilisateur, cible_type="utilisateur", cible_id=acces.utilisateur.id,
        adresse_ip=adresse_ip(request),
    )  # fmt: skip
    await db.commit()
    return CodesSecours(codes=codes)  # type: ignore[arg-type]


@router.post("/double-auth/codes-secours")
async def nouveaux_codes(entree: CodeSaisi, acces: Collaborateur_, db: Base, request: Request) -> CodesSecours:
    """Remplace les codes de secours. Le code de l'application est exigé : une session volée ne suffit pas."""
    if not acces.double_auth_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "Active d'abord la double authentification.")
    await _verifier_avec_limite(
        db, acces, request, lambda: double_auth.verifier_code(db, acces.utilisateur, entree.code)
    )
    codes = await double_auth.regenerer_codes_secours(db, acces.utilisateur)
    journaliser(
        db, "codes_secours_regeneres", acces.utilisateur, cible_type="utilisateur", cible_id=acces.utilisateur.id,
        adresse_ip=adresse_ip(request),
    )  # fmt: skip
    await db.commit()
    return CodesSecours(codes=codes)


# Tableau de bord --------------------------------------------------------------------------------------------


@router.get("/tableau-de-bord")
async def tableau(
    acces: Annotated[Acces, Depends(exiger_permission("tableau_de_bord", Action.consulter))], db: Base
) -> TableauDeBord:
    return await tableau_de_bord.calculer(db, acces)


# Collaborateurs (super-administrateur) ----------------------------------------------------------------------

SuperAdmin = Annotated[Acces, Depends(exiger_super_admin)]


def _refus(erreur: collaborateurs.Refus) -> HTTPException:
    return HTTPException(erreur.statut, str(erreur))


@router.get("/collaborateurs")
async def lister_collaborateurs(
    _: SuperAdmin,
    db: Base,
    recherche: Annotated[str | None, Query(max_length=100)] = None,
    role: str | None = None,
    perimetre: str | None = None,
    statut: str | None = None,
) -> list[CollaborateurResume]:
    return await collaborateurs.lister(
        db, recherche=recherche, role_depart=role, perimetre_dre=perimetre, statut=statut
    )


@router.get("/collaborateurs/{collaborateur_id}")
async def voir_collaborateur(collaborateur_id: UUID, _: SuperAdmin, db: Base) -> CollaborateurDetail:
    try:
        return await collaborateurs.detail(db, await collaborateurs.charger(db, collaborateur_id))
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None


@router.post("/collaborateurs", status_code=status.HTTP_201_CREATED)
async def inviter(entree: InvitationEntree, acces: SuperAdmin, db: Base, request: Request) -> InvitationCree:
    try:
        collaborateur, lien = await collaborateurs.inviter(db, acces, entree, adresse_ip(request))
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    return InvitationCree(
        collaborateur=await collaborateurs.detail(db, collaborateur), lien_de_test=collaborateurs.lien_de_test(lien)
    )


@router.post("/collaborateurs/{collaborateur_id}/invitation")
async def renvoyer(collaborateur_id: UUID, acces: SuperAdmin, db: Base, request: Request) -> InvitationCree:
    try:
        collaborateur, lien = await collaborateurs.renvoyer(db, acces, collaborateur_id, adresse_ip(request))
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    return InvitationCree(
        collaborateur=await collaborateurs.detail(db, collaborateur), lien_de_test=collaborateurs.lien_de_test(lien)
    )


@router.post("/collaborateurs/{collaborateur_id}/invitation/annuler")
async def annuler_invitation(
    collaborateur_id: UUID, entree: MotifEntree, acces: SuperAdmin, db: Base, request: Request
) -> CollaborateurDetail:
    try:
        collaborateur = await collaborateurs.annuler_invitation(
            db, acces, collaborateur_id, entree.motif, adresse_ip(request)
        )
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    return await collaborateurs.detail(db, collaborateur)


@router.put("/collaborateurs/{collaborateur_id}/permissions")
async def modifier_droits(
    collaborateur_id: UUID, entree: DroitsEntree, acces: SuperAdmin, db: Base, request: Request
) -> CollaborateurDetail:
    try:
        collaborateur = await collaborateurs.modifier_droits(db, acces, collaborateur_id, entree, adresse_ip(request))
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    return await collaborateurs.detail(db, collaborateur)


async def _changer_statut(
    collaborateur_id: UUID, nouveau: StatutCompte, entree: MotifEntree, acces: Acces, db: AsyncSession, request: Request
) -> CollaborateurDetail:
    try:
        collaborateur = await collaborateurs.changer_statut(
            db, acces, collaborateur_id, nouveau, entree.motif, adresse_ip(request)
        )
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    return await collaborateurs.detail(db, collaborateur)


@router.post("/collaborateurs/{collaborateur_id}/suspendre")
async def suspendre(
    collaborateur_id: UUID, entree: MotifEntree, acces: SuperAdmin, db: Base, request: Request
) -> CollaborateurDetail:
    return await _changer_statut(collaborateur_id, StatutCompte.suspendu, entree, acces, db, request)


@router.post("/collaborateurs/{collaborateur_id}/reactiver")
async def reactiver(
    collaborateur_id: UUID, entree: MotifEntree, acces: SuperAdmin, db: Base, request: Request
) -> CollaborateurDetail:
    return await _changer_statut(collaborateur_id, StatutCompte.actif, entree, acces, db, request)


@router.post("/collaborateurs/{collaborateur_id}/revoquer")
async def revoquer(
    collaborateur_id: UUID, entree: MotifEntree, acces: SuperAdmin, db: Base, request: Request
) -> CollaborateurDetail:
    return await _changer_statut(collaborateur_id, StatutCompte.revoque, entree, acces, db, request)


@router.post("/collaborateurs/{collaborateur_id}/double-auth/reinitialiser")
async def reinitialiser_double_auth(
    collaborateur_id: UUID, entree: MotifEntree, acces: SuperAdmin, db: Base, request: Request
) -> CollaborateurDetail:
    try:
        collaborateur = await collaborateurs.reinitialiser_double_auth(
            db, acces, collaborateur_id, entree.motif, adresse_ip(request)
        )
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    return await collaborateurs.detail(db, collaborateur)


@router.post("/collaborateurs/{collaborateur_id}/revue")
async def marquer_revu(collaborateur_id: UUID, acces: SuperAdmin, db: Base, request: Request) -> CollaborateurDetail:
    try:
        collaborateur = await collaborateurs.marquer_revu(db, acces, collaborateur_id, adresse_ip(request))
    except collaborateurs.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collaborateur introuvable.") from None
    return await collaborateurs.detail(db, collaborateur)


# Activation d'une invitation (public, avec le jeton) --------------------------------------------------------

INVITATION_INVALIDE = "Ce lien d'invitation n'est plus valide. Demande une nouvelle invitation."


@router_activation.post("/info")
async def voir_invitation(entree: JetonEntree, db: Base) -> ActivationInfo:
    """Le jeton passe dans le corps : dans l'adresse, il finirait dans les journaux d'accès du proxy."""
    try:
        _, collaborateur = await collaborateurs.invitation_valide(db, entree.jeton)
    except collaborateurs.InvitationInvalide:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INVITATION_INVALIDE) from None
    return ActivationInfo(
        prenom=collaborateur.prenom,
        email=collaborateur.email,
        double_auth_requise=await collaborateurs.droits_sensibles(db, collaborateur),
    )


@router_activation.post("")
async def activer(entree: ActivationEntree, db: Base, request: Request, response: Response) -> Moi:
    try:
        utilisateur = await collaborateurs.activer(
            db, entree.jeton, entree.identifiant, entree.mot_de_passe, adresse_ip(request)
        )
    except collaborateurs.InvitationInvalide:
        raise HTTPException(status.HTTP_404_NOT_FOUND, INVITATION_INVALIDE) from None
    except collaborateurs.Refus as erreur:
        raise _refus(erreur) from None
    jeton_session = await ouvrir_session(db, utilisateur, adresse_ip=adresse_ip(request))
    _poser_cookie(response, utilisateur, jeton_session)
    return Moi.model_validate(utilisateur)


# Inscrits ---------------------------------------------------------------------------------------------------

LecteurInscrits = Annotated[Acces, Depends(exiger_permission("inscrits", Action.consulter, national=True))]
GestionnaireInscrits = Annotated[Acces, Depends(exiger_permission("inscrits", Action.modifier, national=True))]


@router.get("/inscrits")
async def lister_inscrits(
    _: LecteurInscrits,
    db: Base,
    recherche: Annotated[str | None, Query(max_length=100)] = None,
    profil: Role | None = None,
    statut: StatutCompte | None = None,
    inscrit_depuis: datetime | None = None,
    inscrit_avant: datetime | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    par_page: Annotated[int, Query(ge=1, le=100)] = 25,
) -> PageInscrits:
    filtres = FiltresInscrits(
        recherche=recherche, profil=profil, statut=statut, inscrit_depuis=inscrit_depuis, inscrit_avant=inscrit_avant
    )
    return await inscrits.lister(db, filtres, page, par_page)


@router.get("/inscrits/{utilisateur_id}")
async def voir_inscrit(utilisateur_id: UUID, _: LecteurInscrits, db: Base) -> InscritDetail:
    try:
        return await inscrits.detail(db, utilisateur_id)
    except inscrits.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compte introuvable.") from None


async def _statut_inscrit(
    utilisateur_id: UUID, nouveau: StatutCompte, entree: MotifEntree, acces: Acces, db: AsyncSession, request: Request
) -> InscritDetail:
    try:
        return await inscrits.changer_statut(db, acces, utilisateur_id, nouveau, entree.motif, adresse_ip(request))
    except inscrits.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compte introuvable.") from None
    except inscrits.Refus as erreur:
        raise HTTPException(status.HTTP_409_CONFLICT, str(erreur)) from None


@router.post("/inscrits/{utilisateur_id}/suspendre")
async def suspendre_inscrit(
    utilisateur_id: UUID, entree: MotifEntree, acces: GestionnaireInscrits, db: Base, request: Request
) -> InscritDetail:
    return await _statut_inscrit(utilisateur_id, StatutCompte.suspendu, entree, acces, db, request)


@router.post("/inscrits/{utilisateur_id}/reactiver")
async def reactiver_inscrit(
    utilisateur_id: UUID, entree: MotifEntree, acces: GestionnaireInscrits, db: Base, request: Request
) -> InscritDetail:
    return await _statut_inscrit(utilisateur_id, StatutCompte.actif, entree, acces, db, request)


# Exports ----------------------------------------------------------------------------------------------------


async def _refuser_export(db: AsyncSession, request: Request, acces: Acces, erreur: exports.Refus) -> HTTPException:
    if erreur.statut == status.HTTP_403_FORBIDDEN:
        journaliser(
            db, "acces_refuse", acces.utilisateur, perimetre=acces.collaborateur.perimetre_dre or "national",
            details={"droit": "exports", "route": f"{request.method} {request.url.path}"}, adresse_ip=adresse_ip(request),
        )  # fmt: skip
        await db.commit()
    return HTTPException(erreur.statut, str(erreur))


@router.post("/exports/apercu")
async def apercu_export(entree: ExportEntree, acces: Pret, db: Base, request: Request) -> Apercu:
    try:
        nombre = await exports.apercu(db, acces, entree)
    except exports.Refus as erreur:
        raise await _refuser_export(db, request, acces, erreur) from None
    return Apercu(nb_lignes=nombre, plafond=settings.export_lignes_max)


@router.post("/exports", status_code=status.HTTP_201_CREATED)
async def creer_export(entree: ExportEntree, acces: Pret, db: Base, request: Request) -> ExportCree:
    try:
        export, lien = await exports.creer(db, acces, entree, adresse_ip(request))
    except exports.Refus as erreur:
        raise await _refuser_export(db, request, acces, erreur) from None
    return ExportCree(export=ExportResume.model_validate(export), lien=lien)


@router.get("/exports")
async def historique_exports(acces: Pret, db: Base, request: Request) -> list[ExportResume]:
    if not (acces.a("statistiques", Action.exporter) or (acces.a("inscrits", Action.exporter) and acces.national)):
        raise await _refuser_export(db, request, acces, exports.Refus("Tu n'as pas accès aux exports.", 403))
    return await exports.historique(db, acces)


@router.get("/exports/{export_id}/fichier")
async def telecharger_export(
    export_id: UUID, jeton: Annotated[str, Query(max_length=100)], acces: Pret, db: Base, request: Request
) -> Response:
    try:
        export, contenu = await exports.telecharger(db, acces, export_id, jeton, adresse_ip(request))
    except exports.LienInvalide:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Ce lien de téléchargement n'est plus valide. Relance l'export."
        ) from None
    return Response(
        contenu,
        media_type=exports.TYPES_MIME[export.format],
        headers={"Content-Disposition": f'attachment; filename="{exports.nom_de_fichier(export)}"'},
    )


# Journal ----------------------------------------------------------------------------------------------------


@router.get("/journal")
async def journal(
    _: Annotated[Acces, Depends(exiger_permission("journal", Action.consulter, national=True))],
    db: Base,
    auteur: UUID | None = None,
    action: Annotated[str | None, Query(max_length=50)] = None,
    depuis: datetime | None = None,
    avant: datetime | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    par_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PageJournal:
    requete = select(JournalAudit)
    if auteur:
        requete = requete.where(JournalAudit.auteur_id == auteur)
    if action:
        requete = requete.where(JournalAudit.action == action)
    if depuis:
        requete = requete.where(JournalAudit.quand >= depuis)
    if avant:
        requete = requete.where(JournalAudit.quand < avant)
    total = await db.scalar(select(func.count()).select_from(requete.subquery())) or 0
    evenements = await db.scalars(
        requete.order_by(JournalAudit.quand.desc(), JournalAudit.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    return PageJournal(
        total=total,
        page=page,
        par_page=par_page,
        evenements=[EvenementJournal.model_validate(e) for e in evenements.all()],
    )
