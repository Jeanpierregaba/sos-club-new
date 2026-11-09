"""Gestion de la certification par l'équipe (spec 029) : règles des badges, certificats et badges délivrés,
révocation et réémission. Droits `quiz` vérifiés par les routes ; chaque écriture entre au journal d'audit."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.certification import regles
from app.certification.models import BadgeObtenu, Certificat, EtatCertificat, ReglesBadges
from app.certification.progression import LIEN, nouveau_numero
from app.certification.schemas import (
    BadgeGestion,
    CertificatGestion,
    HistoriqueRegles,
    ListeBadges,
    ListeCertificats,
    ReglesEntree,
    ReglesSortie,
)
from app.clubs.models import Club
from app.comptes.models import Utilisateur
from app.notifications.service import notifier
from app.points import service as points
from app.points.models import MouvementPoints
from app.quiz import horloge

LIMITE_BADGES = 200
LIMITE_CERTIFICATS = 500


class Introuvable(Exception):
    pass


class EtatInvalide(Exception):
    """L'opération ne vaut pas dans l'état actuel (409)."""


# Règles des badges ------------------------------------------------------------------------------------------------


def _regles(r: ReglesBadges) -> ReglesSortie:
    return ReglesSortie(version=r.version, noms=r.noms, paliers=r.paliers, cree_le=r.cree_le)


async def historique_regles(db: AsyncSession) -> HistoriqueRegles:
    en_cours = await regles.en_cours(db)
    versions = (await db.scalars(select(ReglesBadges).order_by(ReglesBadges.version.desc()))).all()
    return HistoriqueRegles(en_cours=_regles(en_cours), versions=[_regles(r) for r in versions])


async def changer_regles(db: AsyncSession, acces: Acces, entree: ReglesEntree, ip: str) -> ReglesSortie:
    """Ajoute une version : seuls les badges à venir la suivent."""
    actuelles = await regles.en_cours(db)
    nouvelle = ReglesBadges(
        version=actuelles.version + 1, noms=entree.noms, paliers=entree.paliers, cree_par=acces.utilisateur.id
    )
    db.add(nouvelle)
    try:
        async with db.begin_nested():
            await db.flush()
    except IntegrityError:
        raise EtatInvalide("Les règles viennent d'être changées par quelqu'un d'autre : recharge la page.") from None
    journaliser(
        db, "certification_regles_modifiees", acces.utilisateur, cible_type="regles_badges", cible_id=nouvelle.id,
        perimetre="national", details={"version": nouvelle.version, **entree.model_dump()}, adresse_ip=ip,
    )  # fmt: skip
    await db.refresh(nouvelle)
    return _regles(nouvelle)


# Listes -----------------------------------------------------------------------------------------------------------


async def lister_certificats(
    db: AsyncSession, etat: EtatCertificat | None = None, certificat_id: UUID | None = None
) -> ListeCertificats:
    remplace = aliased(Certificat)
    requete = (
        select(Certificat, Club.nom, remplace.numero)
        .outerjoin(Club, Club.id == Certificat.club_id)
        .outerjoin(remplace, remplace.id == Certificat.remplace_id)
        .order_by(Certificat.delivre_le.desc())
    )
    if etat is not None:
        requete = requete.where(Certificat.etat == etat)
    if certificat_id is not None:
        requete = requete.where(Certificat.id == certificat_id)
    requete = requete.limit(LIMITE_CERTIFICATS)
    return ListeCertificats(
        certificats=[
            CertificatGestion(
                id=c.id,
                numero=c.numero,
                etat=c.etat,
                role=c.role,
                titulaire=f"{c.titulaire_prenom} {c.titulaire_nom}",
                utilisateur_id=c.utilisateur_id,
                club=club,
                delivre_le=c.delivre_le,
                motif=c.motif,
                decide_le=c.decide_le,
                remplace_numero=numero,
            )
            for c, club, numero in (await db.execute(requete)).all()
        ]
    )


async def lister_badges(db: AsyncSession) -> ListeBadges:
    lignes = await db.execute(
        select(BadgeObtenu, Utilisateur.prenom, Utilisateur.nom, Utilisateur.role)
        .join(Utilisateur, Utilisateur.id == BadgeObtenu.utilisateur_id)
        .order_by(BadgeObtenu.obtenu_le.desc(), BadgeObtenu.rang.desc())
        .limit(LIMITE_BADGES)
    )
    return ListeBadges(
        badges=[
            BadgeGestion(
                titulaire=f"{prenom} {nom}", role=role.value, nom=b.nom, palier=b.palier, obtenu_le=b.obtenu_le
            )
            for b, prenom, nom, role in lignes.all()
        ]
    )


# Révoquer, réémettre ----------------------------------------------------------------------------------------------


async def _verrouiller(db: AsyncSession, certificat_id: UUID) -> Certificat:
    certificat = await db.scalar(
        select(Certificat)
        .where(Certificat.id == certificat_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if certificat is None:
        raise Introuvable
    return certificat


def _journal(db: AsyncSession, action: str, acces: Acces, certificat: Certificat, ip: str, **details: object) -> None:
    journaliser(
        db, f"certificat_{action}", acces.utilisateur, cible_type="certificat", cible_id=certificat.id,
        perimetre="national", details={"numero": certificat.numero, **details}, adresse_ip=ip,
    )  # fmt: skip


async def revoquer(db: AsyncSession, acces: Acces, certificat_id: UUID, motif: str, ip: str) -> CertificatGestion:
    """La vérification affiche « révoqué », le PDF n'est plus servi, et les points du certificat sont retirés par
    une ligne négative (une seule fois, même après une réémission)."""
    certificat = await _verrouiller(db, certificat_id)
    if certificat.etat is not EtatCertificat.valide:
        raise EtatInvalide("Seul un certificat valide se révoque.")
    certificat.etat = EtatCertificat.revoque
    certificat.motif = motif
    certificat.decide_par, certificat.decide_le = acces.utilisateur.id, horloge.maintenant()
    retrait = None
    if certificat.mouvement_id is not None:
        gain = await db.get(MouvementPoints, certificat.mouvement_id)
        assert gain is not None
        retrait = await points.annuler(db, gain, valide_par=acces.utilisateur.id)
    notifier(
        db, certificat.utilisateur_id, "certification_revocation", "Ton certificat Génie Imhotep est révoqué",
        motif, LIEN,
    )  # fmt: skip
    _journal(db, "revoque", acces, certificat, ip, motif=motif, points_retires=-retrait.montant if retrait else 0)
    await db.flush()
    return await _gestion(db, certificat.id)


async def reemettre(db: AsyncSession, acces: Acces, certificat_id: UUID, ip: str) -> CertificatGestion:
    """Un nouveau numéro remplace l'ancien, avec le nom actuel du compte (correction du nom) ; aucun point de plus.
    Un certificat révoqué est ainsi rétabli, sans lui rendre ses points."""
    ancien = await _verrouiller(db, certificat_id)
    if ancien.etat is EtatCertificat.remplace:
        raise EtatInvalide("Ce certificat a déjà été remplacé : réémets le plus récent.")
    titulaire = await db.get(Utilisateur, ancien.utilisateur_id)
    assert titulaire is not None
    maintenant = horloge.maintenant()
    ancien.etat = EtatCertificat.remplace
    ancien.decide_par, ancien.decide_le = acces.utilisateur.id, maintenant
    # L'ancien quitte l'état « valide » avant que le nouveau n'y entre (un seul certificat valide par personne).
    await db.flush()
    nouveau = Certificat(
        numero=nouveau_numero(),
        utilisateur_id=ancien.utilisateur_id,
        role=ancien.role,
        titulaire_prenom=titulaire.prenom,
        titulaire_nom=titulaire.nom,
        etat=EtatCertificat.valide,
        delivre_le=maintenant,
        club_id=ancien.club_id,
        afficher_club=ancien.afficher_club,
        mouvement_id=ancien.mouvement_id,
        remplace_id=ancien.id,
    )
    db.add(nouveau)
    await db.flush()
    notifier(
        db, ancien.utilisateur_id, "certification_reemission", "Ton certificat Génie Imhotep est réémis",
        f"Ton nouveau certificat porte le numéro {nouveau.numero}.", LIEN,
    )  # fmt: skip
    _journal(db, "reemis", acces, ancien, ip, nouveau_numero=nouveau.numero)
    return await _gestion(db, nouveau.id)


async def _gestion(db: AsyncSession, certificat_id: UUID) -> CertificatGestion:
    [certificat] = (await lister_certificats(db, certificat_id=certificat_id)).certificats
    return certificat
