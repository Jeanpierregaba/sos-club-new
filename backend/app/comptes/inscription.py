"""Mécanismes communs aux inscriptions des élèves (spec 017) et des encadreurs (spec 018).

Chaque inscription est une seule transaction : si une étape échoue, rien n'est écrit. Seule la limite par adresse
est validée à part, avant tout le reste, et elle est partagée par les deux profils.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import TentativeConnexion
from app.comptes.service import VIOLATION_UNICITE, _purger_vieux_essais
from app.config import settings
from app.referentiel.models import Dre, Etablissement, Iesg, StatutEtablissement, TypeEtablissement
from app.referentiel.normalisation import normaliser
from app.referentiel.schemas import EtablissementRattache

# Pas une empreinte SHA-256 (64 caractères hexadécimaux) : elle ne se confond avec la clé d'aucune connexion.
CLE_LIMITE = "inscription"
FENETRE_LIMITE = timedelta(hours=1)
DOUBLONS = {
    "uq_utilisateur_identifiant": "Cet identifiant est déjà pris.",
    "uq_utilisateur_email": "Cet email est déjà pris.",
    "uq_eleve_pseudonyme_normalise": "Ce pseudonyme est déjà pris.",
}


class Refus(Exception):
    def __init__(self, message: str, statut: int = 422) -> None:
        super().__init__(message)
        self.statut = statut


class InscriptionsFermees(Exception):
    pass


class TropDInscriptions(Exception):
    pass


async def limiter(db: AsyncSession, adresse_ip: str) -> None:
    """Compte l'inscription avant de la traiter, dans sa propre transaction : une rafale simultanée ne dépasse pas
    le seuil. `en_cours` reste vrai : la limite des connexions ne compte que les échecs, pas ces lignes."""
    await _purger_vieux_essais(db)
    reservation = TentativeConnexion(cle_hash=CLE_LIMITE, adresse_ip=adresse_ip, en_cours=True)
    db.add(reservation)
    await db.commit()
    nombre = await db.scalar(
        select(func.count())
        .select_from(TentativeConnexion)
        .where(
            TentativeConnexion.cle_hash == CLE_LIMITE,
            TentativeConnexion.adresse_ip == adresse_ip,
            TentativeConnexion.cree_le > datetime.now(UTC) - FENETRE_LIMITE,
        )
    )
    if nombre > settings.inscriptions_max_adresse:
        # Un essai refusé ne compte pas : réessayer pendant le blocage ne le prolonge pas.
        await db.execute(delete(TentativeConnexion).where(TentativeConnexion.id == reservation.id))
        await db.commit()
        raise TropDInscriptions


async def etablissement_actif(db: AsyncSession, etablissement_id: UUID) -> Etablissement:
    etablissement = await db.scalar(
        select(Etablissement)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .where(
            Etablissement.id == etablissement_id,
            Etablissement.statut == StatutEtablissement.actif,
            Iesg.actif,
            Dre.actif,
        )
    )
    if etablissement is None:
        raise Refus("Cet établissement n'existe pas ou n'est plus actif : choisis-en un autre.")
    return etablissement


async def proposer(db: AsyncSession, iesg_id: UUID, nom: str) -> Etablissement:
    iesg = await db.scalar(
        select(Iesg).join(Dre, Dre.code == Iesg.dre_code).where(Iesg.id == iesg_id, Iesg.actif, Dre.actif)
    )
    if iesg is None:
        raise Refus("Cette inspection n'existe pas ou n'est plus active.")
    # Deux personnes peuvent proposer le même établissement au même instant : la base tranche, et la seconde se
    # rattache à la proposition de la première.
    await db.execute(
        insert(Etablissement)
        .values(
            id=uuid7(),
            iesg_id=iesg_id,
            nom=nom,
            nom_normalise=normaliser(nom),
            type=TypeEtablissement.autre,
            statut=StatutEtablissement.propose,
        )
        .on_conflict_do_nothing(index_elements=["iesg_id", "nom_normalise"])
    )
    # Verrouillée : l'admin ne peut pas la remplacer pendant qu'un inscrit s'y rattache.
    existant = await db.scalar(
        select(Etablissement)
        .where(Etablissement.iesg_id == iesg_id, Etablissement.nom_normalise == normaliser(nom))
        .with_for_update()
    )
    assert existant is not None
    if existant.statut == StatutEtablissement.actif:
        raise Refus(f"« {existant.nom} » est déjà dans la liste : choisis-le dans la recherche.", 409)
    if existant.statut == StatutEtablissement.inactif:
        raise Refus(f"« {existant.nom} » n'est plus actif : choisis un autre établissement.", 409)
    return existant


async def flush(db: AsyncSession) -> None:
    """Un doublon apparu entre la vérification et l'écriture (deux inscriptions simultanées) devient un refus."""
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        contrainte = getattr(getattr(erreur.orig, "__cause__", None), "constraint_name", None) or ""
        raise Refus(DOUBLONS.get(contrainte, "Un de ces éléments est déjà pris."), 409) from None


async def etablissement_rattache(db: AsyncSession, etablissement_id: UUID) -> EtablissementRattache:
    etablissement, iesg, dre = (
        await db.execute(
            select(Etablissement, Iesg, Dre)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Etablissement.id == etablissement_id)
        )
    ).one()
    return EtablissementRattache(
        id=etablissement.id, nom=etablissement.nom, statut=etablissement.statut, iesg=iesg.nom, dre_code=dre.code,
        dre=dre.nom, localite=etablissement.localite,
    )  # fmt: skip
