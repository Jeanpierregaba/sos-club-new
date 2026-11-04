"""Inscription d'un élève et son espace (spec 017).

L'inscription est une seule transaction : compte, profil, établissement proposé, points de bienvenue et session.
Si une étape échoue, rien n'est écrit. Seule la limite par adresse est validée à part, avant tout le reste.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.admin.journal import journaliser
from app.comptes.models import Role, TentativeConnexion, Utilisateur
from app.comptes.service import (
    VIOLATION_UNICITE,
    CompteInvalide,
    DejaPris,
    TropDEssais,
    _purger_vieux_essais,
    _reserver_essai,
    _valider_email,
    empreinte,
    preparer_utilisateur,
)
from app.comptes.service import normaliser as normaliser_identifiant
from app.config import settings
from app.eleves import pseudonyme
from app.eleves.models import Eleve
from app.eleves.schemas import (
    EspaceEleve,
    EtablissementEleve,
    InscriptionEntree,
    LignePoints,
    PointsEleve,
    ProfilModification,
    SemestreEleve,
)
from app.points import service as points
from app.points.bareme import BIENVENUE_ELEVE
from app.referentiel.models import Dre, Etablissement, Iesg, StatutEtablissement, TypeEtablissement
from app.referentiel.normalisation import normaliser

# Pas une empreinte SHA-256 (64 caractères hexadécimaux) : elle ne se confond avec la clé d'aucune connexion.
CLE_LIMITE = "inscription"
FENETRE_LIMITE = timedelta(hours=1)
MESSAGE_VERSION = "Ton profil a été modifié entre-temps : recharge la page."
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


class PasUnEleve(Exception):
    pass


async def _limiter(db: AsyncSession, adresse_ip: str) -> None:
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


async def _etablissement_actif(db: AsyncSession, etablissement_id: UUID) -> Etablissement:
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


async def _proposer(db: AsyncSession, iesg_id: UUID, nom: str) -> Etablissement:
    iesg = await db.scalar(
        select(Iesg).join(Dre, Dre.code == Iesg.dre_code).where(Iesg.id == iesg_id, Iesg.actif, Dre.actif)
    )
    if iesg is None:
        raise Refus("Cette inspection n'existe pas ou n'est plus active.")
    # Deux élèves peuvent proposer le même établissement au même instant : la base tranche, et le second se
    # rattache à la proposition du premier.
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
    # Verrouillée : l'admin ne peut pas la remplacer pendant qu'un élève s'y rattache.
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


async def _flush(db: AsyncSession) -> None:
    """Un doublon apparu entre la vérification et l'écriture (deux inscriptions simultanées) devient un refus."""
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        contrainte = getattr(getattr(erreur.orig, "__cause__", None), "constraint_name", None) or ""
        raise Refus(DOUBLONS.get(contrainte, "Un de ces éléments est déjà pris."), 409) from None


async def inscrire(db: AsyncSession, entree: InscriptionEntree, adresse_ip: str) -> Utilisateur:
    """Prépare toute l'inscription sans la valider : la session ouverte ensuite valide le tout."""
    if not settings.inscriptions_actives:
        raise InscriptionsFermees
    await _limiter(db, adresse_ip)

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
        etablissement = await _etablissement_actif(db, entree.etablissement_id)
    else:
        assert entree.proposition
        etablissement = await _proposer(db, entree.proposition.iesg_id, entree.proposition.nom)

    try:
        utilisateur = await preparer_utilisateur(
            db, Role.eleve, entree.identifiant, entree.prenom, entree.nom, entree.mot_de_passe, entree.email
        )
    except DejaPris as erreur:
        raise Refus(str(erreur), 409) from None
    except CompteInvalide as erreur:
        raise Refus(str(erreur)) from None
    utilisateur.consentement_le = datetime.now(UTC)
    await _flush(db)

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
    await _flush(db)
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


async def etablissement_eleve(db: AsyncSession, etablissement_id: UUID) -> EtablissementEleve:
    etablissement, iesg, dre = (
        await db.execute(
            select(Etablissement, Iesg, Dre)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Etablissement.id == etablissement_id)
        )
    ).one()
    return EtablissementEleve(
        id=etablissement.id, nom=etablissement.nom, statut=etablissement.statut, iesg=iesg.nom, dre_code=dre.code,
        dre=dre.nom,
    )  # fmt: skip


async def points_eleve(db: AsyncSession, utilisateur_id: UUID, nombre: int) -> PointsEleve:
    totaux = await points.totaux(db, utilisateur_id)
    lignes = await points.dernieres_lignes(db, utilisateur_id, nombre)
    semestre = totaux.semestre
    return PointsEleve(
        semestre=SemestreEleve(libelle=semestre.libelle, debut=semestre.debut, fin=semestre.fin) if semestre else None,
        points_semestre=totaux.points_semestre,
        total=totaux.total,
        lignes=[LignePoints(**ligne.__dict__) for ligne in lignes],
    )


async def espace(db: AsyncSession, utilisateur: Utilisateur) -> EspaceEleve:
    eleve = await _profil(db, utilisateur)
    return EspaceEleve(
        pseudonyme=eleve.pseudonyme,
        classe=eleve.classe,
        email=utilisateur.email,
        etablissement=await etablissement_eleve(db, eleve.etablissement_id),
        version=eleve.version,
        points=await points_eleve(db, utilisateur.id, 20),
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
        await _etablissement_actif(db, entree.etablissement_id)
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
            await _flush(db)
        except StaleDataError:
            await db.rollback()
            raise Refus(MESSAGE_VERSION, 409) from None
        journaliser(
            db, "profil_eleve_modifie", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
            details={"avant": avant, "apres": apres}, adresse_ip=adresse_ip,
        )  # fmt: skip
        await db.commit()
    return await espace(db, utilisateur)
