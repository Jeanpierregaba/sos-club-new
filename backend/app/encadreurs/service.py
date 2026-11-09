"""Inscription d'un encadreur et son espace (spec 018).

L'inscription est une seule transaction : compte, profil « en attente », établissement proposé et session. Aucun
point avant la vérification par l'équipe : la bienvenue est créditée à l'activation (`verification.py`).
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.admin.journal import journaliser
from app.comptes.inscription import (
    InscriptionsFermees,
    Refus,
    etablissement_actif,
    etablissement_rattache,
    flush,
    limiter,
    proposer,
)
from app.comptes.models import Role, Utilisateur
from app.comptes.service import CompteInvalide, DejaPris, preparer_utilisateur
from app.config import settings
from app.encadreurs.models import Encadreur, EtatVerification, Fonction
from app.encadreurs.schemas import EspaceEncadreur, InscriptionEncadreur, ProfilEncadreurModification
from app.points import service as points
from app.referentiel.models import Etablissement, Iesg, StatutEtablissement

MESSAGE_VERSION = "Ton profil a été modifié entre-temps : recharge la page."


class PasUnEncadreur(Exception):
    pass


class ProfilAbsent(Exception):
    """Un compte encadreur créé avant la spec 018, sans établissement ni fonction."""


async def _dre(db: AsyncSession, etablissement_id: UUID) -> str:
    return (
        await db.scalar(
            select(Iesg.dre_code)
            .join(Etablissement, Etablissement.iesg_id == Iesg.id)
            .where(Etablissement.id == etablissement_id)
        )
    ) or "national"


async def inscrire(db: AsyncSession, entree: InscriptionEncadreur, adresse_ip: str) -> Utilisateur:
    """Prépare toute l'inscription sans la valider : la session ouverte ensuite valide le tout."""
    if not settings.inscriptions_actives:
        raise InscriptionsFermees
    await limiter(db, adresse_ip)

    if entree.etablissement_id:
        etablissement = await etablissement_actif(db, entree.etablissement_id)
    else:
        assert entree.proposition
        etablissement = await proposer(db, entree.proposition.iesg_id, entree.proposition.nom)

    try:
        utilisateur = await preparer_utilisateur(
            db, Role.encadreur, entree.identifiant, entree.prenom, entree.nom, entree.mot_de_passe, entree.email,
            entree.telephone,
        )  # fmt: skip
    except DejaPris as erreur:
        raise Refus(str(erreur), 409) from None
    except CompteInvalide as erreur:
        raise Refus(str(erreur)) from None
    utilisateur.consentement_le = datetime.now(UTC)
    await flush(db)

    db.add(
        Encadreur(
            utilisateur_id=utilisateur.id,
            etablissement_id=etablissement.id,
            fonction=entree.fonction,
            fonction_precision=entree.fonction_precision,
            discipline=entree.discipline,
            etat=EtatVerification.en_attente,
            demande_le=datetime.now(UTC),
            charte_version=settings.version_charte,
        )
    )
    await flush(db)
    journaliser(
        db, "inscription_encadreur", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        perimetre=await _dre(db, etablissement.id),
        details={"etablissement_id": str(etablissement.id),
                 "etablissement_propose": etablissement.statut == StatutEtablissement.propose},
        adresse_ip=adresse_ip,
    )  # fmt: skip
    return utilisateur


# Espace de l'encadreur -----------------------------------------------------------------------------------------


async def profil(db: AsyncSession, utilisateur: Utilisateur, *, verrouiller: bool = False) -> Encadreur:
    if utilisateur.role is not Role.encadreur:
        raise PasUnEncadreur
    encadreur = await db.get(Encadreur, utilisateur.id, with_for_update=verrouiller)
    if encadreur is None:
        raise ProfilAbsent
    return encadreur


async def espace(db: AsyncSession, utilisateur: Utilisateur) -> EspaceEncadreur:
    encadreur = await profil(db, utilisateur)
    actif = encadreur.etat is EtatVerification.actif
    return EspaceEncadreur(
        etat=encadreur.etat,
        demande_le=encadreur.demande_le,
        decide_le=encadreur.decide_le,
        motif_refus=encadreur.motif_refus,
        fonction=encadreur.fonction,
        fonction_precision=encadreur.fonction_precision,
        discipline=encadreur.discipline,
        email=utilisateur.email,
        telephone=utilisateur.telephone,
        etablissement=await etablissement_rattache(db, encadreur.etablissement_id),
        version=encadreur.version,
        points=await points.resume(db, utilisateur.id, 20) if actif else None,
    )


async def _ecrire(db: AsyncSession) -> None:
    try:
        await flush(db)
    except StaleDataError:
        await db.rollback()
        raise Refus(MESSAGE_VERSION, 409) from None


async def modifier_profil(
    db: AsyncSession, utilisateur: Utilisateur, entree: ProfilEncadreurModification, adresse_ip: str
) -> EspaceEncadreur:
    encadreur = await profil(db, utilisateur, verrouiller=True)
    if encadreur.version != entree.version:
        raise Refus(MESSAGE_VERSION, 409)
    avant: dict[str, str | None] = {}
    apres: dict[str, str | None] = {}
    if "telephone" in entree.model_fields_set and entree.telephone is None and utilisateur.telephone:
        raise Refus("Ton téléphone est obligatoire : remplace-le plutôt que de l'effacer.")
    if "telephone" in entree.model_fields_set and entree.telephone != utilisateur.telephone:
        # Le numéro lui-même n'entre pas au journal.
        avant["telephone"] = "ancien" if utilisateur.telephone else None
        apres["telephone"] = "nouveau" if entree.telephone else None
        utilisateur.telephone = entree.telephone
    if entree.etablissement_id and entree.etablissement_id != encadreur.etablissement_id:
        await etablissement_actif(db, entree.etablissement_id)
        # Spec 020 : les rattachements au club de l'ancien établissement prennent fin.
        from app.clubs.rattachements import quitter_au_changement_detablissement

        await quitter_au_changement_detablissement(db, utilisateur, encadreur.etablissement_id, adresse_ip)
        avant["etablissement_id"], apres["etablissement_id"] = (
            str(encadreur.etablissement_id), str(entree.etablissement_id)
        )  # fmt: skip
        encadreur.etablissement_id = entree.etablissement_id
    fonction = entree.fonction or encadreur.fonction
    precision = (
        entree.fonction_precision if "fonction_precision" in entree.model_fields_set else encadreur.fonction_precision
    )
    precision = precision if fonction is Fonction.autre else None
    if fonction is Fonction.autre and not precision:
        raise Refus("Précise ta fonction.")
    if (fonction, precision) != (encadreur.fonction, encadreur.fonction_precision):
        avant["fonction"], apres["fonction"] = encadreur.fonction.value, fonction.value
        avant["fonction_precision"], apres["fonction_precision"] = encadreur.fonction_precision, precision
        encadreur.fonction, encadreur.fonction_precision = fonction, precision
    if "discipline" in entree.model_fields_set and entree.discipline != encadreur.discipline:
        avant["discipline"], apres["discipline"] = encadreur.discipline, entree.discipline
        encadreur.discipline = entree.discipline
    if apres:
        # Le verrou optimiste ne voit que les colonnes du profil : le téléphone seul doit aussi faire monter la version.
        encadreur.modifie_le = datetime.now(UTC)
        await _ecrire(db)
        journaliser(
            db, "profil_encadreur_modifie", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
            perimetre=await _dre(db, encadreur.etablissement_id), details={"avant": avant, "apres": apres},
            adresse_ip=adresse_ip,
        )  # fmt: skip
        await db.commit()
    return await espace(db, utilisateur)


async def renvoyer(db: AsyncSession, utilisateur: Utilisateur, adresse_ip: str) -> EspaceEncadreur:
    """Un encadreur refusé, après correction, repasse en fin de file. Le motif précédent reste au journal."""
    encadreur = await profil(db, utilisateur, verrouiller=True)
    if encadreur.etat is not EtatVerification.refuse:
        raise Refus("Seule une demande refusée peut être renvoyée.", 409)
    motif = encadreur.motif_refus
    encadreur.etat = EtatVerification.en_attente
    encadreur.motif_refus = None
    encadreur.demande_le = datetime.now(UTC)
    encadreur.decide_le = None
    encadreur.decide_par = None
    await _ecrire(db)
    journaliser(
        db, "encadreur_redemande", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        perimetre=await _dre(db, encadreur.etablissement_id), details={"motif_precedent": motif},
        adresse_ip=adresse_ip,
    )  # fmt: skip
    await db.commit()
    return await espace(db, utilisateur)
