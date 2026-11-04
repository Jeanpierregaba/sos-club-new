"""Administration des semestres et du barème (spec 017). Un changement vaut pour les gains à venir : les lignes déjà
écrites gardent leur montant et leur semestre.

Un semestre commencé est figé, sauf pour prolonger un semestre en cours : sinon des lignes déjà écrites
tomberaient hors de leur semestre. Chaque écriture vérifie la version lue et laisse une entrée au journal.
"""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.comptes.service import VIOLATION_UNICITE
from app.points.models import LigneBareme, Semestre
from app.points.schemas import (
    LigneBaremeAdmin,
    LigneBaremeModification,
    SemestreAdmin,
    SemestreCreation,
    SemestreModification,
)
from app.points.service import aujourd_hui
from app.referentiel.administration import MESSAGE_VERSION, Introuvable, Refus

VIOLATION_EXCLUSION = "23P01"


def _etat(semestre: Semestre, jour: date) -> str:
    if jour < semestre.debut:
        return "a_venir"
    return "en_cours" if jour <= semestre.fin else "termine"


def _semestre_admin(semestre: Semestre, jour: date) -> SemestreAdmin:
    return SemestreAdmin(
        id=semestre.id,
        libelle=semestre.libelle,
        debut=semestre.debut,
        fin=semestre.fin,
        etat=_etat(semestre, jour),
        version=semestre.version,
    )


def _valeur(valeur: Any) -> Any:
    return valeur.isoformat() if isinstance(valeur, date) else valeur


def _appliquer(element: Any, changements: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    avant: dict[str, Any] = {}
    apres: dict[str, Any] = {}
    for champ, nouvelle in changements.items():
        ancienne = getattr(element, champ)
        if nouvelle is not None and ancienne != nouvelle:
            setattr(element, champ, nouvelle)
            avant[champ], apres[champ] = _valeur(ancienne), _valeur(nouvelle)
    return avant, apres


async def _chevauche(db: AsyncSession, debut: date, fin: date, sauf: UUID | None = None) -> Semestre | None:
    requete = select(Semestre).where(Semestre.debut <= fin, Semestre.fin >= debut)
    if sauf:
        requete = requete.where(Semestre.id != sauf)
    return await db.scalar(requete.limit(1))


async def _ecrire(db: AsyncSession) -> None:
    try:
        await db.flush()
    except StaleDataError:
        await db.rollback()
        raise Refus(MESSAGE_VERSION, 409) from None
    except IntegrityError as erreur:
        await db.rollback()
        code = getattr(erreur.orig, "sqlstate", None)
        if code == VIOLATION_EXCLUSION:
            # Un autre semestre a été créé entre la vérification et l'écriture.
            raise Refus("Ce semestre chevauche un autre semestre.", 409) from None
        if code == VIOLATION_UNICITE:
            raise Refus("Un semestre porte déjà ce libellé.", 409) from None
        raise


# Semestres -----------------------------------------------------------------------------------------------------


async def lister_semestres(db: AsyncSession) -> list[SemestreAdmin]:
    jour = aujourd_hui()
    semestres = await db.scalars(select(Semestre).order_by(Semestre.debut.desc()))
    return [_semestre_admin(s, jour) for s in semestres]


async def _verifier_dates(db: AsyncSession, debut: date, fin: date, sauf: UUID | None = None) -> None:
    if fin < debut:
        raise Refus("La fin du semestre précède son début.", 422)
    autre = await _chevauche(db, debut, fin, sauf)
    if autre:
        raise Refus(f"Ce semestre chevauche « {autre.libelle} ».", 409)


async def creer_semestre(db: AsyncSession, acces: Acces, entree: SemestreCreation, ip: str) -> SemestreAdmin:
    jour = aujourd_hui()
    # Des lignes ont pu être écrites hors semestre : un semestre qui commencerait avant aujourd'hui ne les
    # contiendrait pas.
    if entree.debut < jour:
        raise Refus("Un semestre ne peut pas commencer dans le passé.", 422)
    await _verifier_dates(db, entree.debut, entree.fin)
    semestre = Semestre(libelle=entree.libelle, debut=entree.debut, fin=entree.fin)
    db.add(semestre)
    await _ecrire(db)
    journaliser(
        db, "semestre_cree", acces.utilisateur, cible_type="semestre", cible_id=semestre.id, perimetre="national",
        details={"apres": {"libelle": semestre.libelle, "debut": semestre.debut.isoformat(),
                           "fin": semestre.fin.isoformat()}},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return _semestre_admin(semestre, jour)


async def modifier_semestre(
    db: AsyncSession, acces: Acces, semestre_id: UUID, entree: SemestreModification, ip: str
) -> SemestreAdmin:
    jour = aujourd_hui()
    semestre = await db.get(Semestre, semestre_id, with_for_update=True)
    if semestre is None:
        raise Introuvable
    if semestre.version != entree.version:
        raise Refus(MESSAGE_VERSION, 409)
    debut = entree.debut or semestre.debut
    fin = entree.fin or semestre.fin
    etat = _etat(semestre, jour)
    if etat == "a_venir":
        if debut < jour:
            raise Refus("Un semestre ne peut pas commencer dans le passé.", 422)
    elif debut != semestre.debut or fin < semestre.fin or (etat == "termine" and fin != semestre.fin):
        raise Refus("Ce semestre a commencé : seule sa date de fin peut être repoussée, tant qu'il est en cours.", 409)
    await _verifier_dates(db, debut, fin, sauf=semestre.id)
    avant, apres = _appliquer(semestre, {"libelle": entree.libelle, "debut": debut, "fin": fin})
    if apres:
        await _ecrire(db)
        journaliser(
            db, "semestre_modifie", acces.utilisateur, cible_type="semestre", cible_id=semestre.id,
            perimetre="national", details={"avant": avant, "apres": apres}, adresse_ip=ip,
        )  # fmt: skip
        await db.commit()
    return _semestre_admin(semestre, jour)


# Barème ------------------------------------------------------------------------------------------------------


async def lister_bareme(db: AsyncSession) -> list[LigneBaremeAdmin]:
    lignes = await db.scalars(select(LigneBareme).order_by(LigneBareme.ordre))
    return [LigneBaremeAdmin.model_validate(ligne) for ligne in lignes]


async def modifier_bareme(
    db: AsyncSession, acces: Acces, code: str, entree: LigneBaremeModification, ip: str
) -> LigneBaremeAdmin:
    ligne = await db.get(LigneBareme, code, with_for_update=True)
    if ligne is None:
        raise Introuvable
    if ligne.version != entree.version:
        raise Refus(MESSAGE_VERSION, 409)
    avant, apres = _appliquer(ligne, {"montant": entree.montant, "propose": entree.propose, "actif": entree.actif})
    if apres:
        await _ecrire(db)
        journaliser(
            db, "bareme_modifie", acces.utilisateur, cible_type="bareme", cible_id=code, perimetre="national",
            details={"avant": avant, "apres": apres}, adresse_ip=ip,
        )  # fmt: skip
        await db.commit()
    return LigneBaremeAdmin.model_validate(ligne)
