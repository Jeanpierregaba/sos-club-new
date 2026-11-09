"""Fiche d'adhésion de l'élève (spec 030) : enregistrement, lecture et correction.

Données personnelles d'un mineur. Elles ne sortent que vers l'élève lui-même et, par `lire_pour_equipe`, vers un
collaborateur ayant le droit sensible `fiches_eleves:consulter` dans son périmètre ; chaque lecture de l'équipe est
journalisée. Le journal ne contient jamais le contenu de la fiche.
"""

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.comptes.inscription import Refus, flush
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve, FicheEleve, FicheEleveAxe, FicheEleveParcours
from app.eleves.schemas_fiche import FicheEntree, FicheModification, FicheSortie, ParcoursAnterieur, Parent, Responsable
from app.referentiel.models import Axe, Etablissement, Iesg

MESSAGE_VERSION = "Ta fiche a été modifiée entre-temps : recharge la page."


class Introuvable(Exception):
    pass


def annee_scolaire(jour: date) -> str:
    """L'année scolaire togolaise commence en septembre : « 2026-2027 » à partir du 1er septembre 2026."""
    debut = jour.year if jour.month >= 9 else jour.year - 1
    return f"{debut}-{debut + 1}"


async def _verifier_axes(db: AsyncSession, axes: list[str]) -> None:
    actifs = set((await db.scalars(select(Axe.code).where(Axe.code.in_(axes), Axe.actif))).all())
    if actifs != set(axes):
        raise Refus("Un des axes choisis n'existe pas ou n'est plus proposé : choisis-en un autre.")


def _remplir(fiche: FicheEleve, entree: FicheEntree, maintenant: datetime) -> None:
    fiche.numero_adhesion = entree.numero_adhesion
    fiche.prefecture, fiche.commune, fiche.canton = entree.prefecture, entree.commune, entree.canton
    fiche.sexe = entree.sexe
    fiche.date_naissance, fiche.lieu_naissance = entree.date_naissance, entree.lieu_naissance
    fiche.telephone = entree.telephone
    pere, mere = entree.pere or Parent(), entree.mere or Parent()
    fiche.pere_nom, fiche.pere_profession, fiche.pere_telephone = pere.nom, pere.profession, pere.telephone
    fiche.mere_nom, fiche.mere_profession, fiche.mere_telephone = mere.nom, mere.profession, mere.telephone
    fiche.responsable_nom, fiche.responsable_telephone = entree.responsable.nom, entree.responsable.telephone
    fiche.reseaux = [r.value for r in entree.reseaux]
    fiche.reseau_autre = entree.reseau_autre
    fiche.engagement_le = fiche.engagement_le or maintenant
    fiche.complete_le = fiche.complete_le or maintenant


async def _remplacer_listes(db: AsyncSession, utilisateur_id: UUID, entree: FicheEntree) -> None:
    await db.execute(delete(FicheEleveAxe).where(FicheEleveAxe.utilisateur_id == utilisateur_id))
    await db.execute(delete(FicheEleveParcours).where(FicheEleveParcours.utilisateur_id == utilisateur_id))
    db.add_all(FicheEleveAxe(utilisateur_id=utilisateur_id, axe_code=code) for code in entree.axes)
    db.add_all(
        FicheEleveParcours(utilisateur_id=utilisateur_id, rang=rang, annee=p.annee, etablissement=p.etablissement,
                           iesg=p.iesg)
        for rang, p in enumerate(entree.parcours, start=1)
    )  # fmt: skip


async def enregistrer_a_linscription(db: AsyncSession, utilisateur_id: UUID, entree: FicheEntree) -> None:
    """Dans la transaction de l'inscription : le profil `eleve` est déjà ajouté."""
    await _verifier_axes(db, entree.axes)
    maintenant = datetime.now(UTC)
    fiche = FicheEleve(utilisateur_id=utilisateur_id, annee_scolaire=annee_scolaire(maintenant.date()))
    _remplir(fiche, entree, maintenant)
    db.add(fiche)
    await flush(db)
    await _remplacer_listes(db, utilisateur_id, entree)


async def _sortie(db: AsyncSession, fiche: FicheEleve) -> FicheSortie:
    axes = (
        await db.scalars(
            select(FicheEleveAxe.axe_code)
            .join(Axe, Axe.code == FicheEleveAxe.axe_code)
            .where(FicheEleveAxe.utilisateur_id == fiche.utilisateur_id)
            .order_by(Axe.ordre)
        )
    ).all()
    parcours = (
        await db.scalars(
            select(FicheEleveParcours)
            .where(FicheEleveParcours.utilisateur_id == fiche.utilisateur_id)
            .order_by(FicheEleveParcours.rang)
        )
    ).all()

    def parent(nom: str | None, profession: str | None, telephone: str | None) -> Parent | None:
        return Parent(nom=nom, profession=profession, telephone=telephone) if nom or profession or telephone else None

    return FicheSortie(
        annee_scolaire=fiche.annee_scolaire,
        numero_adhesion=fiche.numero_adhesion,
        prefecture=fiche.prefecture,
        commune=fiche.commune,
        canton=fiche.canton,
        sexe=fiche.sexe,
        date_naissance=fiche.date_naissance,
        lieu_naissance=fiche.lieu_naissance,
        telephone=fiche.telephone,
        pere=parent(fiche.pere_nom, fiche.pere_profession, fiche.pere_telephone),
        mere=parent(fiche.mere_nom, fiche.mere_profession, fiche.mere_telephone),
        responsable=Responsable(nom=fiche.responsable_nom, telephone=fiche.responsable_telephone)
        if fiche.responsable_nom and fiche.responsable_telephone
        else None,
        axes=list(axes),
        parcours=[ParcoursAnterieur(annee=p.annee, etablissement=p.etablissement, iesg=p.iesg) for p in parcours],
        reseaux=fiche.reseaux,
        reseau_autre=fiche.reseau_autre,
        engagement_le=fiche.engagement_le,
        complete_le=fiche.complete_le,
        cree_le=fiche.cree_le,
        version=fiche.version,
    )


async def est_complete(db: AsyncSession, utilisateur_id: UUID) -> bool:
    return (
        await db.scalar(select(FicheEleve.complete_le).where(FicheEleve.utilisateur_id == utilisateur_id)) is not None
    )


async def _eleve(db: AsyncSession, utilisateur: Utilisateur) -> Eleve:
    from app.eleves.service import PasUnEleve

    eleve = await db.get(Eleve, utilisateur.id) if utilisateur.role is Role.eleve else None
    if eleve is None:
        raise PasUnEleve
    return eleve


async def ma_fiche(db: AsyncSession, utilisateur: Utilisateur) -> FicheSortie | None:
    await _eleve(db, utilisateur)
    fiche = await db.get(FicheEleve, utilisateur.id)
    return await _sortie(db, fiche) if fiche else None


async def corriger(
    db: AsyncSession, utilisateur: Utilisateur, entree: FicheModification, adresse_ip: str
) -> FicheSortie:
    await _eleve(db, utilisateur)
    await _verifier_axes(db, entree.axes)
    fiche = await db.get(FicheEleve, utilisateur.id, with_for_update=True)
    maintenant = datetime.now(UTC)
    if fiche is None:
        if entree.version is not None:
            raise Refus(MESSAGE_VERSION, 409)
        fiche = FicheEleve(utilisateur_id=utilisateur.id, annee_scolaire=annee_scolaire(maintenant.date()))
        db.add(fiche)
    elif entree.version != fiche.version:
        raise Refus(MESSAGE_VERSION, 409)
    _remplir(fiche, entree, maintenant)
    # Les axes et le parcours sont dans d'autres tables : la date suffit à faire monter la version.
    fiche.modifie_le = maintenant
    try:
        await flush(db)
    except StaleDataError:
        await db.rollback()
        raise Refus(MESSAGE_VERSION, 409) from None
    await _remplacer_listes(db, utilisateur.id, entree)
    # Le contenu de la fiche n'entre jamais au journal.
    journaliser(db, "fiche_eleve_modifiee", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
                adresse_ip=adresse_ip)  # fmt: skip
    await db.commit()
    await db.refresh(fiche)
    return await _sortie(db, fiche)


async def lire_pour_equipe(db: AsyncSession, acces: Acces, utilisateur_id: UUID, adresse_ip: str) -> FicheSortie:
    """Le droit et la double authentification sont vérifiés par la route ; ici, le périmètre et le journal.
    Hors périmètre, la fiche est « introuvable » : on ne révèle pas qu'elle existe."""
    ligne = (
        await db.execute(
            select(FicheEleve, Iesg.dre_code)
            .join(Eleve, Eleve.utilisateur_id == FicheEleve.utilisateur_id)
            .join(Etablissement, Etablissement.id == Eleve.etablissement_id)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .where(FicheEleve.utilisateur_id == utilisateur_id)
        )
    ).one_or_none()
    perimetre = acces.collaborateur.perimetre_dre
    if ligne is None or (perimetre is not None and ligne[1] != perimetre):
        raise Introuvable
    fiche, dre = ligne
    journaliser(
        db, "fiche_eleve_consultee", acces.utilisateur, cible_type="utilisateur", cible_id=utilisateur_id,
        perimetre=dre, adresse_ip=adresse_ip,
    )  # fmt: skip
    sortie = await _sortie(db, fiche)
    await db.commit()
    return sortie
