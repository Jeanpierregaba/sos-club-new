"""Côté modérateur du moteur (ADR-0009) : la file, l'aperçu et les quatre décisions.

Une décision se prend en une transaction, sous verrou de l'en-tête et avec la version que le modérateur a lue :
décision, nouvel état, points, notification et journal sont écrits ensemble, ou pas du tout. Un collaborateur de
DRE ne voit que les contenus des auteurs de sa DRE ; pour les autres, il reçoit la même réponse que pour un
contenu inexistant. Un auteur ne décide jamais de son propre contenu.
"""

import re
import unicodedata
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs.models import Club, ClubAxe
from app.comptes.inscription import Refus
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, EtatVerification
from app.moderation.models import (
    Contenu,
    DecisionModeration,
    EtatContenu,
    EtatVersion,
    Photo,
    TypeDecision,
    VersionContenu,
    VersionPhoto,
)
from app.moderation.photos import photos_de
from app.moderation.schemas import (
    ApercuModeration,
    AuteurFile,
    ClubContenu,
    DecisionPassee,
    ElementFile,
    FicheActuelle,
    FileModeration,
    ParentContenu,
    PhotoModeration,
)
from app.moderation.service import Introuvable
from app.moderation.types import TYPES, type_de
from app.notifications.service import notifier
from app.points import service as points
from app.referentiel.models import Etablissement

LIMITE_FILE = 200


class Interdit(Exception):
    """Un auteur ne décide jamais de son propre contenu."""


_Travail = aliased(VersionContenu)
_EtablissementAuteur = aliased(Etablissement)


# Un contenu dépublié n'a plus de version en ligne ni de travail : la file montre alors sa dernière version.
_Derniere = aliased(VersionContenu)
_derniere = (
    select(_Derniere.id)
    .where(_Derniere.contenu_id == Contenu.id)
    .order_by(_Derniere.numero.desc())
    .limit(1)
    .correlate(Contenu)
    .scalar_subquery()
)


# Le contenu parent d'un commentaire (spec 025) : son adresse et son titre, celui de la version en ligne de
# préférence, sinon celui de la dernière version (un article dépublié depuis).
_Parent = aliased(Contenu)
_VersionParent = aliased(VersionContenu)
_titre_parent = (
    select(_VersionParent.donnees["titre"].astext)
    .where(_VersionParent.contenu_id == Contenu.parent_id)
    .order_by((_VersionParent.id == _Parent.version_publiee_id).desc(), _VersionParent.numero.desc())
    .limit(1)
    .correlate(Contenu, _Parent)
    .scalar_subquery()
)

Ligne = tuple[Contenu, Utilisateur, VersionContenu, str | None, str | None, str | None, str | None]


def _requete(acces: Acces) -> Select[Ligne]:
    """Chaque contenu avec son auteur, la version qu'on modère (de travail, sinon en ligne, sinon la dernière) et l'établissement de
    l'auteur, filtrés par le périmètre du collaborateur."""
    requete = (
        select(Contenu, Utilisateur, _Travail, _EtablissementAuteur.nom, _Parent.adresse, _titre_parent, Club.nom)
        .join(Utilisateur, Utilisateur.id == Contenu.auteur_id)
        .outerjoin(_Parent, _Parent.id == Contenu.parent_id)
        .outerjoin(Club, Club.id == Contenu.club_id)
        .join(_Travail, _Travail.id == func.coalesce(Contenu.version_travail_id, Contenu.version_publiee_id, _derniere))
        .outerjoin(Eleve, Eleve.utilisateur_id == Contenu.auteur_id)
        .outerjoin(Encadreur, Encadreur.utilisateur_id == Contenu.auteur_id)
        .outerjoin(
            _EtablissementAuteur,
            _EtablissementAuteur.id == func.coalesce(Eleve.etablissement_id, Encadreur.etablissement_id),
        )
    )
    if not acces.national:
        requete = requete.where(Contenu.dre_code == acces.collaborateur.perimetre_dre)
    return requete


def _element(
    contenu: Contenu,
    auteur: Utilisateur,
    version: VersionContenu,
    etablissement: str | None,
    adresse_parent: str | None,
    titre_parent: str | None,
    nom_club: str | None,
) -> ElementFile:
    return ElementFile(
        id=contenu.id,
        type=contenu.type,
        club=ClubContenu(id=contenu.club_id, nom=nom_club or "") if contenu.club_id is not None else None,
        depublication_possible=type_de(contenu.type).depublication,
        parent=ParentContenu(adresse=adresse_parent, titre=titre_parent or "")
        if contenu.parent_id is not None
        else None,
        correction_possible=type_de(contenu.type).correction,
        titre=type_de(contenu.type).titre(version.donnees),
        etat=contenu.etat,
        axe_code=version.donnees.get("axe_code"),
        auteur=AuteurFile(
            id=auteur.id,
            nom=f"{auteur.prenom} {auteur.nom}",
            identifiant=auteur.identifiant,
            profil=auteur.role.value,
            etablissement=etablissement,
            dre_code=contenu.dre_code,
        ),
        nouvelle_version=contenu.version_publiee_id is not None and contenu.version_travail_id is not None,
        en_ligne=contenu.version_publiee_id is not None,
        adresse=contenu.adresse,
        soumis_le=contenu.soumis_le,
        modifie_le=contenu.modifie_le,
        version=contenu.version,
    )


async def file_attente(
    db: AsyncSession,
    acces: Acces,
    etat: EtatContenu = EtatContenu.en_attente,
    *,
    type: str | None = None,
    axe: str | None = None,
    dre: str | None = None,
    profil: Role | None = None,
) -> FileModeration:
    if etat is EtatContenu.brouillon:
        # Un brouillon est un travail privé de l'auteur : il n'entre jamais dans la file.
        raise Refus("La file ne montre pas les brouillons.", 422)
    if etat is EtatContenu.publie:
        # « En ligne » : un article publié reste en ligne pendant qu'une nouvelle version se prépare.
        # Une proposition de fiche approuvée (spec 026) est appliquée, pas « en ligne » : elle n'a rien à retirer.
        appliques = [code for code, t in TYPES.items() if not t.depublication]
        requete = _requete(acces).where(Contenu.version_publiee_id.is_not(None), Contenu.type.not_in(appliques))
    else:
        requete = _requete(acces).where(Contenu.etat == etat)
    if type:
        requete = requete.where(Contenu.type == type)
    if axe:
        requete = requete.where(_Travail.donnees["axe_code"].astext == axe)
    if dre:
        requete = requete.where(Contenu.dre_code == dre)
    if profil:
        requete = requete.where(Utilisateur.role == profil)
    total = await db.scalar(select(func.count()).select_from(requete.with_only_columns(Contenu.id).subquery()))
    # La file dans l'ordre d'arrivée ; les autres listes, les plus récemment modifiés d'abord.
    ordre = Contenu.soumis_le.asc() if etat is EtatContenu.en_attente else Contenu.modifie_le.desc()
    lignes = (await db.execute(requete.order_by(ordre, Contenu.id).limit(LIMITE_FILE))).all()
    return FileModeration(total=total or 0, contenus=[_element(*ligne) for ligne in lignes])


async def compter_en_attente(db: AsyncSession, acces: Acces) -> int:
    requete = select(func.count()).select_from(Contenu).where(Contenu.etat == EtatContenu.en_attente)
    if not acces.national:
        requete = requete.where(Contenu.dre_code == acces.collaborateur.perimetre_dre)
    return (await db.scalar(requete)) or 0


async def apercu(db: AsyncSession, acces: Acces, contenu_id: UUID) -> ApercuModeration:
    ligne = (await db.execute(_requete(acces).where(Contenu.id == contenu_id))).one_or_none()
    if ligne is None:
        raise Introuvable
    contenu = ligne[0]
    # La dernière version soumise : jamais une version de travail, que l'auteur n'a pas envoyée.
    soumise = await db.scalar(
        select(VersionContenu)
        .where(VersionContenu.contenu_id == contenu.id, VersionContenu.etat != EtatVersion.travail)
        .order_by(VersionContenu.numero.desc())
        .limit(1)
    )
    if soumise is None:
        raise Introuvable
    publiee = await db.get(VersionContenu, contenu.version_publiee_id) if contenu.version_publiee_id else None
    decideurs = aliased(Utilisateur)
    passees = await db.execute(
        select(DecisionModeration, decideurs)
        .outerjoin(decideurs, decideurs.id == DecisionModeration.decide_par)
        .where(DecisionModeration.contenu_id == contenu.id)
        .order_by(DecisionModeration.decide_le.desc(), DecisionModeration.id.desc())
    )
    autre = soumise.id != contenu.version_publiee_id
    fiche_actuelle = None
    if contenu.club_id is not None and contenu.type == "fiche_club":
        club = await db.get(Club, contenu.club_id)
        axes = await db.scalars(
            select(ClubAxe.axe_code).where(ClubAxe.club_id == contenu.club_id).order_by(ClubAxe.axe_code)
        )
        fiche_actuelle = FicheActuelle(description=club.description if club else None, axes=list(axes))
    return ApercuModeration(
        fiche_actuelle=fiche_actuelle,
        **_element(*ligne).model_dump(),
        soumise=soumise.donnees if autre else None,
        photos_soumises=[_photo(p, ph) for p, ph in await photos_de(db, soumise.id)] if autre else [],
        photos_publiees=[_photo(p, ph) for p, ph in await photos_de(db, contenu.version_publiee_id)],
        publiee=publiee.donnees if publiee else None,
        decisions=[
            DecisionPassee(
                decision=decision.decision,
                motif=decision.motif,
                decide_par=f"{decideur.prenom} {decideur.nom}" if decideur else None,
                decide_le=decision.decide_le,
            )
            for decision, decideur in passees
        ],
    )


def _photo(placement: VersionPhoto, photo: Photo) -> PhotoModeration:
    return PhotoModeration(
        id=photo.id, legende=placement.legende, couverture=placement.couverture, ordre=placement.ordre,
        largeur=photo.largeur, hauteur=photo.hauteur, attestation=photo.attestation, attestee_le=photo.attestee_le,
        effacee=photo.efface_le is not None,
    )  # fmt: skip


# Décisions -----------------------------------------------------------------------------------------------------


async def _a_decider(db: AsyncSession, acces: Acces, contenu_id: UUID, version: int) -> Contenu:
    contenu = await db.get(Contenu, contenu_id, with_for_update=True, populate_existing=True)
    if contenu is None or (not acces.national and contenu.dre_code != acces.collaborateur.perimetre_dre):
        raise Introuvable
    if contenu.auteur_id == acces.utilisateur.id:
        raise Interdit
    if contenu.version != version:
        raise Refus("Ce contenu a changé depuis que tu l'as ouvert : recharge la page et relis-le.", 409)
    return contenu


def _en_attente(contenu: Contenu) -> None:
    if contenu.etat is not EtatContenu.en_attente:
        raise Refus("Ce contenu n'est pas en attente de modération : il a peut-être déjà été traité.", 409)


async def _travail(db: AsyncSession, contenu: Contenu) -> VersionContenu:
    travail = await db.get(VersionContenu, contenu.version_travail_id) if contenu.version_travail_id else None
    assert travail is not None
    return travail


def _adresse_de(titre: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", titre).encode("ascii", "ignore").decode()
    adresse = re.sub(r"[^a-z0-9]+", "-", sans_accents.lower()).strip("-")[:100].strip("-")
    return adresse or "article"


async def _adresse_libre(db: AsyncSession, titre: str) -> str:
    base = _adresse_de(titre)
    # Verrou de transaction sur cette adresse : deux approbations simultanées de même titre passent l'une après
    # l'autre, et la seconde voit l'adresse prise par la première.
    await db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"adresse:{base}"))))
    adresse, numero = base, 1
    while await db.scalar(select(Contenu.id).where(Contenu.adresse == adresse)):
        numero += 1
        adresse = f"{base}-{numero}"
    return adresse


def _consigner(
    db: AsyncSession,
    acces: Acces,
    contenu: Contenu,
    version: VersionContenu,
    decision: TypeDecision,
    motif: str | None,
    ip: str,
    titre_avis: str,
    type_avis: str,
) -> None:
    """La décision, la notification de l'auteur et le journal : dans la même transaction que le nouvel état."""
    type_contenu = type_de(contenu.type)
    db.add(
        DecisionModeration(
            contenu_id=contenu.id,
            version_id=version.id,
            decision=decision,
            motif=motif,
            decide_par=acces.utilisateur.id,
        )
    )
    notifier(
        db, contenu.auteur_id, f"{contenu.type}_{type_avis}", titre_avis, motif, type_contenu.lien_auteur(contenu.id)
    )
    details: dict[str, Any] = {"version": version.numero}
    if motif:
        details["motif"] = motif
    journaliser(
        db, f"{contenu.type}_{type_avis}", acces.utilisateur, cible_type="contenu", cible_id=contenu.id,
        perimetre=contenu.dre_code or "national", details=details, adresse_ip=ip,
    )  # fmt: skip


async def approuver(db: AsyncSession, acces: Acces, contenu_id: UUID, version: int, ip: str) -> None:
    contenu = await _a_decider(db, acces, contenu_id, version)
    _en_attente(contenu)
    auteur = await db.get(Utilisateur, contenu.auteur_id, with_for_update=True, populate_existing=True)
    assert auteur is not None
    if auteur.statut is not StatutCompte.actif:
        raise Refus("Le compte de l'auteur est suspendu : rien n'est publié tant qu'il l'est.", 409)
    if auteur.role is Role.encadreur:
        encadreur = await db.get(Encadreur, auteur.id)
        if encadreur is None or encadreur.etat is not EtatVerification.actif:
            raise Refus("L'encadreur n'est plus vérifié : son contenu ne peut pas être publié.", 409)
    type_contenu = type_de(contenu.type)
    travail = await _travail(db, contenu)
    donnees = type_contenu.schema.model_validate(travail.donnees).model_dump()
    titre = type_contenu.titre(donnees)
    premiere = contenu.publie_le is None
    revision = contenu.version_publiee_id is not None

    # Les lectures d'abord : une requête déclenche l'écriture des changements en attente (autoflush).
    adresse = await _adresse_libre(db, titre) if premiere and type_contenu.adresse else contenu.adresse
    club_id = None
    # Le club bénéficiaire d'un contenu qui rapporte des points seulement : pas d'une actualité ni d'une fiche.
    if premiere and auteur.role is Role.eleve and type_contenu.actions_auteur:
        # Le club de l'élève affilié à la première approbation, celui qui reçoit la moitié de ses points (spec 034).
        club_id = await points.club_beneficiaire(db, auteur.id)

    travail.etat = EtatVersion.approuvee
    contenu.version_publiee_id = travail.id
    contenu.version_travail_id = None
    contenu.etat = EtatContenu.publie
    contenu.axe_code = donnees.get("axe_code")
    contenu.afficher_club = bool(donnees.get("afficher_club", True))
    contenu.adresse = adresse
    if premiere:
        contenu.publie_le = datetime.now(UTC)
        contenu.club_beneficiaire_id = club_id
    # Les points à la première approbation seulement (jamais pour une révision ni une republication), et une seule
    # ligne par contenu grâce à la clé.
    action = type_contenu.actions_auteur.get(auteur.role)
    if action and premiere and (type_contenu.points_permis is None or await type_contenu.points_permis(db, contenu)):
        await points.crediter(db, action, auteur.id, f"{contenu.type}:{contenu.id}", valide_par=acces.utilisateur.id)
    if premiere and type_contenu.a_la_publication is not None:
        await type_contenu.a_la_publication(db, contenu)
    titre_avis = (
        f"Ta nouvelle version de « {titre} » est en ligne"
        if revision
        else f"{type_contenu.determinant} {type_contenu.libelle} « {titre} » est publié{type_contenu.accord}"
    )
    _consigner(db, acces, contenu, travail, TypeDecision.approuver, None, ip, titre_avis, "approuve")
    await db.commit()


async def demander_correction(
    db: AsyncSession, acces: Acces, contenu_id: UUID, version: int, motif: str, ip: str
) -> None:
    contenu = await _a_decider(db, acces, contenu_id, version)
    _en_attente(contenu)
    if not type_de(contenu.type).correction:
        raise Refus("Ce contenu ne se corrige pas : approuve-le ou refuse-le avec un motif.", 409)
    travail = await _travail(db, contenu)
    titre = type_de(contenu.type).titre(travail.donnees)
    travail.etat = EtatVersion.a_corriger
    contenu.etat = EtatContenu.a_corriger
    _consigner(
        db, acces, contenu, travail, TypeDecision.corriger, motif, ip, f"« {titre} » est à corriger", "a_corriger"
    )
    await db.commit()


async def refuser(db: AsyncSession, acces: Acces, contenu_id: UUID, version: int, motif: str, ip: str) -> None:
    contenu = await _a_decider(db, acces, contenu_id, version)
    _en_attente(contenu)
    travail = await _travail(db, contenu)
    titre = type_de(contenu.type).titre(travail.donnees)
    travail.etat = EtatVersion.refusee
    if contenu.version_publiee_id is not None:
        # Seule la nouvelle version est refusée : la version en ligne reste, l'auteur peut en proposer une autre.
        contenu.version_travail_id = None
        contenu.etat = EtatContenu.publie
        titre_avis = f"Ta nouvelle version de « {titre} » n'a pas été retenue"
    else:
        contenu.etat = EtatContenu.refuse
        titre_avis = f"« {titre} » n'a pas été retenu"
    _consigner(db, acces, contenu, travail, TypeDecision.refuser, motif, ip, titre_avis, "refuse")
    await db.commit()


async def depublier(db: AsyncSession, acces: Acces, contenu_id: UUID, version: int, motif: str, ip: str) -> None:
    contenu = await _a_decider(db, acces, contenu_id, version)
    if not type_de(contenu.type).depublication:
        raise Refus("Ce contenu ne se retire pas du site : il a déjà été appliqué.", 409)
    if contenu.version_publiee_id is None:
        raise Refus("Ce contenu n'est pas en ligne.", 409)
    publiee = await db.get(VersionContenu, contenu.version_publiee_id)
    assert publiee is not None
    titre = type_de(contenu.type).titre(publiee.donnees)
    if contenu.version_travail_id is not None:
        travail = await _travail(db, contenu)
        if travail.etat is EtatVersion.soumise:
            # Une révision en attente tombe avec la version en ligne : elle est refusée, avec le même motif.
            travail.etat = EtatVersion.refusee
            contenu.version_travail_id = None
            db.add(
                DecisionModeration(
                    contenu_id=contenu.id,
                    version_id=travail.id,
                    decision=TypeDecision.refuser,
                    motif=motif,
                    decide_par=acces.utilisateur.id,
                )
            )
    contenu.version_publiee_id = None
    contenu.etat = EtatContenu.depublie
    _consigner(
        db, acces, contenu, publiee, TypeDecision.depublier, motif, ip, f"« {titre} » a été retiré du site", "depublie"
    )
    await db.commit()
