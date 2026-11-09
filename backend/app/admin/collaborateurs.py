"""Comptes collaborateurs : invitation, activation, droits, suspension et révocation (CDC admin, 12A)."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import SENSIBLES, Action, droit_existe
from app.admin.dependances import Acces
from app.admin.double_auth import double_auth_active, reinitialiser
from app.admin.journal import journaliser, libelle
from app.admin.models import Collaborateur, DoubleAuth, EnvoiInvitation, Invitation, Permission
from app.admin.schemas import (
    CollaborateurDetail,
    CollaborateurResume,
    Droit,
    DroitsEntree,
    InvitationEntree,
    StatutCollaborateur,
)
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.comptes.motdepasse import hacher
from app.comptes.service import (
    FORMAT_IDENTIFIANT,
    LONGUEUR_MAX_MOT_DE_PASSE,
    LONGUEUR_MIN_MOT_DE_PASSE,
    VIOLATION_UNICITE,
    couper_sessions,
    empreinte,
    normaliser,
)
from app.config import settings
from app.courriel import envoi as courriel
from app.courriel import messages
from app.referentiel.models import Dre


class Refus(Exception):
    """Le message est destiné au super-administrateur."""

    def __init__(self, message: str, statut: int = 409) -> None:
        super().__init__(message)
        self.statut = statut


class Introuvable(Exception):
    pass


class InvitationInvalide(Exception):
    pass


def _maintenant() -> datetime:
    return datetime.now(UTC)


def _valider_email(email: str) -> str:
    try:
        return validate_email(email.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        raise Refus("Cet e-mail n'est pas valide.", 422) from None


def _droits_valides(droits: list[Droit]) -> set[tuple[str, Action]]:
    resultat = set()
    for droit in droits:
        if not droit_existe(droit.module, droit.action):
            raise Refus(f"Droit inconnu : {droit.module} / {droit.action.value}.", 422)
        resultat.add((droit.module, droit.action))
    return resultat


async def _droits_de(db: AsyncSession, collaborateur_id: UUID) -> set[tuple[str, Action]]:
    lignes = await db.execute(
        select(Permission.module, Permission.action).where(Permission.collaborateur_id == collaborateur_id)
    )
    return {(module, Action(action)) for module, action in lignes}


async def _derniere_invitation(db: AsyncSession, collaborateur_id: UUID) -> Invitation | None:
    return await db.scalar(
        select(Invitation)
        .where(Invitation.collaborateur_id == collaborateur_id)
        .order_by(Invitation.cree_le.desc(), Invitation.id.desc())
        .limit(1)
    )


def _statut(utilisateur: Utilisateur | None, invitation: Invitation | None) -> StatutCollaborateur:
    if utilisateur is None:
        valide = invitation and invitation.annulee_le is None and invitation.expire_le > _maintenant()
        return "invitation_envoyee" if valide else "invitation_expiree"
    return utilisateur.statut.value  # type: ignore[return-value]


async def detail(db: AsyncSession, collaborateur: Collaborateur) -> CollaborateurDetail:
    utilisateur = await db.get(Utilisateur, collaborateur.utilisateur_id) if collaborateur.utilisateur_id else None
    invitation = await _derniere_invitation(db, collaborateur.id)
    droits = await _droits_de(db, collaborateur.id)
    return CollaborateurDetail(
        id=collaborateur.id,
        email=collaborateur.email,
        prenom=collaborateur.prenom,
        nom=collaborateur.nom,
        identifiant=utilisateur.identifiant if utilisateur else None,
        role_depart=collaborateur.role_depart,
        perimetre_dre=collaborateur.perimetre_dre,
        super_admin=collaborateur.super_admin,
        statut=_statut(utilisateur, invitation),
        fin_acces=collaborateur.fin_acces,
        double_auth_active=bool(utilisateur) and await double_auth_active(db, utilisateur.id),
        nb_droits_sensibles=len(droits & SENSIBLES),
        revu_le=collaborateur.revu_le,
        cree_le=collaborateur.cree_le,
        droits=[Droit(module=m, action=a) for m, a in sorted(droits)],
        invitation_expire_le=invitation.expire_le if invitation and utilisateur is None else None,
        invitation_envoi=invitation.envoi.value if invitation and utilisateur is None else None,
    )


async def lister(
    db: AsyncSession,
    *,
    recherche: str | None = None,
    role_depart: str | None = None,
    perimetre_dre: str | None = None,
    statut: str | None = None,
) -> list[CollaborateurResume]:
    requete = select(Collaborateur).order_by(Collaborateur.nom, Collaborateur.prenom)
    if recherche:
        motif = f"%{recherche.strip().lower()}%"
        requete = requete.where(
            func.lower(Collaborateur.email).like(motif)
            | func.lower(Collaborateur.nom).like(motif)
            | func.lower(Collaborateur.prenom).like(motif)
        )
    if role_depart:
        requete = requete.where(Collaborateur.role_depart == role_depart)
    if perimetre_dre == "national":
        requete = requete.where(Collaborateur.perimetre_dre.is_(None))
    elif perimetre_dre:
        requete = requete.where(Collaborateur.perimetre_dre == perimetre_dre)
    resultats = [await detail(db, c) for c in (await db.scalars(requete)).all()]
    return [CollaborateurResume(**r.model_dump()) for r in resultats if not statut or r.statut == statut]


async def charger(db: AsyncSession, collaborateur_id: UUID, *, verrou: bool = False) -> Collaborateur:
    requete = select(Collaborateur).where(Collaborateur.id == collaborateur_id)
    if verrou:
        requete = requete.with_for_update()
    collaborateur = await db.scalar(requete)
    if collaborateur is None:
        raise Introuvable
    return collaborateur


async def _remplacer_droits(db: AsyncSession, collaborateur_id: UUID, droits: set[tuple[str, Action]]) -> None:
    await db.execute(delete(Permission).where(Permission.collaborateur_id == collaborateur_id))
    for module, action in droits:
        db.add(Permission(collaborateur_id=collaborateur_id, module=module, action=action))


async def _nouvelle_invitation(
    db: AsyncSession, collaborateur: Collaborateur, auteur: Utilisateur
) -> tuple[Invitation, str]:
    """Annule les invitations en cours, en crée une, tente l'envoi. Renvoie l'invitation et le lien."""
    maintenant = _maintenant()
    await db.execute(
        update(Invitation)
        .where(
            Invitation.collaborateur_id == collaborateur.id,
            Invitation.utilisee_le.is_(None),
            Invitation.annulee_le.is_(None),
        )
        .values(annulee_le=maintenant)
    )
    jeton = secrets.token_urlsafe(32)
    lien = f"{settings.site_origine}/activation?jeton={jeton}"
    invitation = Invitation(
        collaborateur_id=collaborateur.id,
        jeton_hash=empreinte(jeton),
        expire_le=maintenant + timedelta(hours=settings.duree_invitation_heures),
        envoi=EnvoiInvitation.envoye,
    )
    try:
        message = messages.invitation(collaborateur.prenom, lien, settings.duree_invitation_heures, libelle(auteur))
        await courriel.envoyer(collaborateur.email, message.sujet, message.texte, html=message.html)
    except courriel.EnvoiImpossible:
        invitation.envoi = EnvoiInvitation.echec
    db.add(invitation)
    return invitation, lien


def lien_de_test(lien: str) -> str | None:
    return None if settings.production or courriel.smtp_configure() else lien


async def _verifier_dre(db: AsyncSession, code: str | None) -> None:
    """Un nouveau périmètre est une DRE active du référentiel (spec 016)."""
    # Verrouillée : elle ne peut pas être désactivée pendant qu'on y limite un collaborateur.
    if code is not None and not await db.scalar(select(Dre.actif).where(Dre.code == code).with_for_update()):
        raise Refus("DRE inconnue ou désactivée.", 422)


async def inviter(db: AsyncSession, auteur: Acces, entree: InvitationEntree, ip: str) -> tuple[Collaborateur, str]:
    email = _valider_email(entree.email)
    droits = _droits_valides(entree.droits)
    if entree.fin_acces and entree.fin_acces <= _maintenant():
        raise Refus("La date de fin d'accès doit être dans le futur.", 422)
    await _verifier_dre(db, entree.perimetre_dre)
    if await db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)) or await db.scalar(
        select(Collaborateur.id).where(Collaborateur.email == email)
    ):
        raise Refus("Cet e-mail est déjà utilisé par un compte ou une invitation.")

    collaborateur = Collaborateur(
        email=email,
        prenom=entree.prenom.strip(),
        nom=entree.nom.strip(),
        role_depart=entree.role_depart,
        perimetre_dre=entree.perimetre_dre,
        fin_acces=entree.fin_acces,
        invite_par_id=auteur.utilisateur.id,
    )
    db.add(collaborateur)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Cet e-mail est déjà utilisé par un compte ou une invitation.") from None
    await _remplacer_droits(db, collaborateur.id, droits)
    invitation, lien = await _nouvelle_invitation(db, collaborateur, auteur.utilisateur)
    journaliser(
        db,
        "collaborateur_invite",
        auteur.utilisateur,
        cible_type="collaborateur",
        cible_id=collaborateur.id,
        perimetre=collaborateur.perimetre_dre or "national",
        details={
            "email": email,
            "role_depart": entree.role_depart.value if entree.role_depart else None,
            "droits": sorted(f"{m}:{a.value}" for m, a in droits),
            "envoi": invitation.envoi.value,
        },
        adresse_ip=ip,
    )
    await db.commit()
    return collaborateur, lien


async def annuler_invitation(
    db: AsyncSession, auteur: Acces, collaborateur_id: UUID, motif: str, ip: str
) -> Collaborateur:
    """Invitation partie à la mauvaise adresse, ou plus nécessaire : le lien cesse de fonctionner tout de suite."""
    collaborateur = await charger(db, collaborateur_id, verrou=True)
    if collaborateur.utilisateur_id:
        raise Refus("Ce compte est déjà activé : suspends-le ou révoque-le.")
    resultat = await db.execute(
        update(Invitation)
        .where(
            Invitation.collaborateur_id == collaborateur.id,
            Invitation.utilisee_le.is_(None),
            Invitation.annulee_le.is_(None),
        )
        .values(annulee_le=_maintenant())
    )
    if not resultat.rowcount:
        raise Refus("Aucune invitation en cours à annuler.")
    journaliser(
        db, "invitation_annulee", auteur.utilisateur, cible_type="collaborateur", cible_id=collaborateur.id,
        details={"motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return collaborateur


async def renvoyer(db: AsyncSession, auteur: Acces, collaborateur_id: UUID, ip: str) -> tuple[Collaborateur, str]:
    collaborateur = await charger(db, collaborateur_id)
    if collaborateur.utilisateur_id:
        raise Refus("Ce compte est déjà activé.")
    invitation, lien = await _nouvelle_invitation(db, collaborateur, auteur.utilisateur)
    journaliser(
        db,
        "invitation_renvoyee",
        auteur.utilisateur,
        cible_type="collaborateur",
        cible_id=collaborateur.id,
        details={"envoi": invitation.envoi.value},
        adresse_ip=ip,
    )
    await db.commit()
    return collaborateur, lien


# Activation -------------------------------------------------------------------------------------------------


async def invitation_valide(db: AsyncSession, jeton: str) -> tuple[Invitation, Collaborateur]:
    invitation = await db.scalar(select(Invitation).where(Invitation.jeton_hash == empreinte(jeton)))
    if (
        invitation is None
        or invitation.utilisee_le is not None
        or invitation.annulee_le is not None
        or invitation.expire_le <= _maintenant()
    ):
        raise InvitationInvalide
    collaborateur = await db.get(Collaborateur, invitation.collaborateur_id)
    if collaborateur is None or collaborateur.utilisateur_id is not None:
        raise InvitationInvalide
    return invitation, collaborateur


async def droits_sensibles(db: AsyncSession, collaborateur: Collaborateur) -> bool:
    return collaborateur.super_admin or bool(await _droits_de(db, collaborateur.id) & SENSIBLES)


async def activer(db: AsyncSession, jeton: str, identifiant: str, mot_de_passe: str, ip: str) -> Utilisateur:
    """Crée le compte de l'invité. Le verrou sur l'invitation empêche deux activations avec le même lien."""
    invitation = await db.scalar(select(Invitation).where(Invitation.jeton_hash == empreinte(jeton)).with_for_update())
    if invitation is None:
        raise InvitationInvalide
    invitation, collaborateur = await invitation_valide(db, jeton)

    identifiant = normaliser(identifiant)
    if not FORMAT_IDENTIFIANT.fullmatch(identifiant):
        raise Refus("L'identifiant doit contenir de 3 à 30 lettres, chiffres, points, tirets ou « _ ».", 422)
    if not LONGUEUR_MIN_MOT_DE_PASSE <= len(mot_de_passe) <= LONGUEUR_MAX_MOT_DE_PASSE:
        raise Refus(f"Le mot de passe doit contenir au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères.", 422)
    if await db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == identifiant)):
        raise Refus("Cet identifiant est déjà pris.")
    if await db.scalar(select(Utilisateur.id).where(Utilisateur.email == collaborateur.email)):
        raise Refus("Cet e-mail est déjà utilisé par un autre compte.")

    utilisateur = Utilisateur(
        role=Role.admin,
        identifiant=identifiant,
        email=collaborateur.email,
        prenom=collaborateur.prenom,
        nom=collaborateur.nom,
        mot_de_passe_hash=await hacher(mot_de_passe),
    )
    db.add(utilisateur)
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise Refus("Cet identifiant ou cet e-mail est déjà pris.") from None
    collaborateur.utilisateur_id = utilisateur.id
    invitation.utilisee_le = _maintenant()
    journaliser(
        db,
        "invitation_acceptee",
        utilisateur,
        cible_type="collaborateur",
        cible_id=collaborateur.id,
        adresse_ip=ip,
    )
    # La session est ouverte par l'appelant, qui valide la transaction.
    return utilisateur


# Actions du super-administrateur ----------------------------------------------------------------------------


def _pas_soi_meme(auteur: Acces, collaborateur: Collaborateur) -> None:
    if collaborateur.utilisateur_id == auteur.utilisateur.id:
        raise Refus("Tu ne peux pas faire cette action sur ton propre compte.", 403)


async def _verrouiller_super_admins(db: AsyncSession) -> None:
    """Verrouille tous les super-administrateurs, toujours dans le même ordre : deux retraits simultanés
    s'attendent au lieu de s'interbloquer, et le second voit l'effet du premier."""
    await db.execute(
        select(Collaborateur.id).where(Collaborateur.super_admin.is_(True)).order_by(Collaborateur.id).with_for_update()
    )


async def _il_reste_un_super_admin(db: AsyncSession, collaborateur: Collaborateur) -> None:
    if not collaborateur.super_admin:
        return
    autres = await db.scalar(
        select(func.count())
        .select_from(Collaborateur)
        .join(Utilisateur, Utilisateur.id == Collaborateur.utilisateur_id)
        .where(
            Collaborateur.super_admin.is_(True),
            Utilisateur.statut == StatutCompte.actif,
            Collaborateur.id != collaborateur.id,
            # Un super-administrateur dont l'accès prend fin ne compte pas pour la suite.
            Collaborateur.fin_acces.is_(None),
        )
    )
    if not autres:
        raise Refus("Il doit rester au moins un super-administrateur actif.")


async def modifier_droits(
    db: AsyncSession, auteur: Acces, collaborateur_id: UUID, entree: DroitsEntree, ip: str
) -> Collaborateur:
    collaborateur = await charger(db, collaborateur_id, verrou=True)
    _pas_soi_meme(auteur, collaborateur)
    if collaborateur.super_admin and (entree.fin_acces or entree.perimetre_dre):
        # Sinon un super-administrateur pourrait programmer la disparition du dernier autre.
        raise Refus("Un super-administrateur reste national et sans date de fin d'accès.", 422)
    droits = _droits_valides(entree.droits)
    if entree.fin_acces and entree.fin_acces <= _maintenant():
        raise Refus("La date de fin d'accès doit être dans le futur.", 422)
    if entree.perimetre_dre != collaborateur.perimetre_dre:
        await _verifier_dre(db, entree.perimetre_dre)
    avant = await _droits_de(db, collaborateur.id)
    await _remplacer_droits(db, collaborateur.id, droits)
    details: dict[str, Any] = {
        "ajoutes": sorted(f"{m}:{a.value}" for m, a in droits - avant),
        "retires": sorted(f"{m}:{a.value}" for m, a in avant - droits),
        "perimetre_avant": collaborateur.perimetre_dre or "national",
        "perimetre_apres": entree.perimetre_dre or "national",
        "motif": entree.motif,
    }
    collaborateur.perimetre_dre = entree.perimetre_dre
    collaborateur.fin_acces = entree.fin_acces
    collaborateur.revu_le = _maintenant()
    journaliser(
        db, "droits_modifies", auteur.utilisateur, cible_type="collaborateur", cible_id=collaborateur.id,
        perimetre=collaborateur.perimetre_dre or "national", details=details, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return collaborateur


async def _utilisateur_du(db: AsyncSession, collaborateur: Collaborateur) -> Utilisateur:
    if collaborateur.utilisateur_id is None:
        raise Refus("Cette invitation n'a pas encore été acceptée.")
    utilisateur = await db.get(Utilisateur, collaborateur.utilisateur_id)
    assert utilisateur
    return utilisateur


async def changer_statut(
    db: AsyncSession, auteur: Acces, collaborateur_id: UUID, nouveau: StatutCompte, motif: str, ip: str
) -> Collaborateur:
    await _verrouiller_super_admins(db)
    collaborateur = await charger(db, collaborateur_id, verrou=True)
    _pas_soi_meme(auteur, collaborateur)
    utilisateur = await _utilisateur_du(db, collaborateur)
    if utilisateur.statut is StatutCompte.revoque:
        raise Refus("Ce compte est révoqué : il ne peut plus être modifié.")
    if utilisateur.statut is nouveau:
        raise Refus("Ce compte a déjà ce statut.")
    if nouveau is not StatutCompte.actif:
        await _il_reste_un_super_admin(db, collaborateur)
        await couper_sessions(db, utilisateur.id)
    avant = utilisateur.statut
    utilisateur.statut = nouveau
    action = {StatutCompte.actif: "collaborateur_reactive", StatutCompte.suspendu: "collaborateur_suspendu"}.get(
        nouveau, "collaborateur_revoque"
    )
    journaliser(
        db, action, auteur.utilisateur, cible_type="collaborateur", cible_id=collaborateur.id,
        details={"avant": avant.value, "apres": nouveau.value, "motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return collaborateur


async def reinitialiser_double_auth(
    db: AsyncSession, auteur: Acces, collaborateur_id: UUID, motif: str, ip: str
) -> Collaborateur:
    collaborateur = await charger(db, collaborateur_id)
    _pas_soi_meme(auteur, collaborateur)
    utilisateur = await _utilisateur_du(db, collaborateur)
    if not await db.get(DoubleAuth, utilisateur.id):
        raise Refus("Ce compte n'a pas de double authentification.")
    await reinitialiser(db, utilisateur.id)
    await couper_sessions(db, utilisateur.id)
    journaliser(
        db, "double_auth_reinitialisee", auteur.utilisateur, cible_type="collaborateur", cible_id=collaborateur.id,
        details={"motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return collaborateur


async def marquer_revu(db: AsyncSession, auteur: Acces, collaborateur_id: UUID, ip: str) -> Collaborateur:
    collaborateur = await charger(db, collaborateur_id)
    collaborateur.revu_le = _maintenant()
    journaliser(
        db, "droits_revus", auteur.utilisateur, cible_type="collaborateur", cible_id=collaborateur.id, adresse_ip=ip
    )
    await db.commit()
    return collaborateur
