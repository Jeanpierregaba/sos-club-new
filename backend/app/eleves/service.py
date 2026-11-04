"""Inscription d'un élève et son espace (spec 017).

L'inscription est une seule transaction : compte, profil, établissement proposé, points de bienvenue et session.
Si une étape échoue, rien n'est écrit. Seule la limite par adresse est validée à part, avant tout le reste.
"""

from datetime import UTC, datetime

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
from app.comptes.service import (
    CompteInvalide,
    DejaPris,
    TropDEssais,
    _reserver_essai,
    _valider_email,
    empreinte,
    preparer_utilisateur,
)
from app.comptes.service import normaliser as normaliser_identifiant
from app.config import settings
from app.eleves import pseudonyme
from app.eleves.models import Eleve
from app.eleves.schemas import EspaceEleve, InscriptionEntree, ProfilModification
from app.points import service as points
from app.points.bareme import BIENVENUE_ELEVE
from app.referentiel.models import StatutEtablissement

MESSAGE_VERSION = "Ton profil a été modifié entre-temps : recharge la page."


class PasUnEleve(Exception):
    pass


async def inscrire(db: AsyncSession, entree: InscriptionEntree, adresse_ip: str) -> Utilisateur:
    """Prépare toute l'inscription sans la valider : la session ouverte ensuite valide le tout."""
    if not settings.inscriptions_actives:
        raise InscriptionsFermees
    await limiter(db, adresse_ip)

    try:
        affiche = pseudonyme.valider(entree.pseudonyme)
    except pseudonyme.PseudonymeInvalide as erreur:
        raise Refus(str(erreur)) from None
    cle = pseudonyme.cle(affiche)
    if cle == pseudonyme.cle(normaliser_identifiant(entree.identifiant)):
        raise Refus("Ton pseudonyme doit être différent de ton identifiant : l'identifiant reste secret.")
    if pseudonyme.contient_le_nom(affiche, entree.prenom, entree.nom):
        raise Refus("Ton pseudonyme ne doit pas contenir ton prénom et ton nom : ils restent privés.")
    if await db.scalar(select(Eleve.utilisateur_id).where(Eleve.pseudonyme_normalise == cle)):
        raise Refus("Ce pseudonyme est déjà pris.", 409)

    if entree.etablissement_id:
        etablissement = await etablissement_actif(db, entree.etablissement_id)
    else:
        assert entree.proposition
        etablissement = await proposer(db, entree.proposition.iesg_id, entree.proposition.nom)

    try:
        utilisateur = await preparer_utilisateur(
            db, Role.eleve, entree.identifiant, entree.prenom, entree.nom, entree.mot_de_passe, entree.email
        )
    except DejaPris as erreur:
        raise Refus(str(erreur), 409) from None
    except CompteInvalide as erreur:
        raise Refus(str(erreur)) from None
    utilisateur.consentement_le = datetime.now(UTC)
    await flush(db)

    db.add(
        Eleve(
            utilisateur_id=utilisateur.id,
            pseudonyme=affiche,
            pseudonyme_normalise=cle,
            classe=entree.classe,
            etablissement_id=etablissement.id,
            charte_version=settings.version_charte,
        )
    )
    await flush(db)
    await points.crediter(db, BIENVENUE_ELEVE, utilisateur.id, f"bienvenue:{utilisateur.id}")
    journaliser(
        db, "inscription_eleve", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        details={"etablissement_id": str(etablissement.id),
                 "etablissement_propose": etablissement.statut == StatutEtablissement.propose},
        adresse_ip=adresse_ip,
    )  # fmt: skip
    return utilisateur


# Espace de l'élève -------------------------------------------------------------------------------------------


async def _profil(db: AsyncSession, utilisateur: Utilisateur, *, verrouiller: bool = False) -> Eleve:
    if utilisateur.role is not Role.eleve:
        raise PasUnEleve
    eleve = await db.get(Eleve, utilisateur.id, with_for_update=verrouiller)
    if eleve is None:
        raise PasUnEleve
    return eleve


async def espace(db: AsyncSession, utilisateur: Utilisateur) -> EspaceEleve:
    eleve = await _profil(db, utilisateur)
    return EspaceEleve(
        pseudonyme=eleve.pseudonyme,
        classe=eleve.classe,
        email=utilisateur.email,
        etablissement=await etablissement_rattache(db, eleve.etablissement_id),
        version=eleve.version,
        points=await points.resume(db, utilisateur.id, 20),
    )


async def modifier_profil(
    db: AsyncSession, utilisateur: Utilisateur, entree: ProfilModification, adresse_ip: str
) -> EspaceEleve:
    if "email" in entree.model_fields_set and (entree.email or None) != utilisateur.email:
        # Chaque essai compte, accepté ou non : « Cet email est déjà pris » ne doit pas servir à repérer les comptes.
        # Validé à part, avant le verrou du profil.
        try:
            await _reserver_essai(db, empreinte(f"email:{utilisateur.identifiant}"), adresse_ip)
        except TropDEssais:
            raise Refus("Trop de changements d'email. Réessaie dans 15 minutes.", 429) from None
    eleve = await _profil(db, utilisateur, verrouiller=True)
    if eleve.version != entree.version:
        raise Refus(MESSAGE_VERSION, 409)
    avant: dict[str, str | None] = {}
    apres: dict[str, str | None] = {}
    if entree.classe and entree.classe != eleve.classe:
        avant["classe"], apres["classe"] = eleve.classe.value, entree.classe.value
        eleve.classe = entree.classe
    if entree.etablissement_id and entree.etablissement_id != eleve.etablissement_id:
        await etablissement_actif(db, entree.etablissement_id)
        avant["etablissement_id"], apres["etablissement_id"] = str(eleve.etablissement_id), str(entree.etablissement_id)
        eleve.etablissement_id = entree.etablissement_id
    if "email" in entree.model_fields_set:
        try:
            email = _valider_email(entree.email, Role.eleve)
        except CompteInvalide as erreur:
            raise Refus(str(erreur)) from None
        if email != utilisateur.email:
            if email and await db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)):
                raise Refus("Cet email est déjà pris.", 409)
            utilisateur.email = email
            # L'adresse elle-même n'entre pas au journal.
            avant["email"], apres["email"] = "ancien", "nouveau" if email else None
    if apres:
        # Le verrou optimiste ne voit que les colonnes du profil : l'email seul doit aussi faire monter la version.
        eleve.modifie_le = datetime.now(UTC)
        try:
            await flush(db)
        except StaleDataError:
            await db.rollback()
            raise Refus(MESSAGE_VERSION, 409) from None
        journaliser(
            db, "profil_eleve_modifie", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
            details={"avant": avant, "apres": apres}, adresse_ip=adresse_ip,
        )  # fmt: skip
        await db.commit()
    return await espace(db, utilisateur)
