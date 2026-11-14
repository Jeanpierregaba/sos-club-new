"""Administration du référentiel (spec 016). Rien ne se supprime : on renomme, on déplace, on désactive.

Chaque écriture vérifie la version lue par le formulaire (verrou optimiste) et laisse une entrée au journal d'audit
avec la valeur avant et après. Les DRE, IESG et axes sont réservés au super-administrateur (contrôlé par la route) ;
les établissements se gèrent avec le droit « Clubs et DRE », dans le périmètre du collaborateur, contrôlé ici.
"""

from collections.abc import Sequence
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.admin.models import Collaborateur
from app.comptes.models import StatutCompte, Utilisateur
from app.comptes.service import VIOLATION_UNICITE
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.referentiel.models import (
    Axe,
    Dre,
    Etablissement,
    Iesg,
    OrdreEnseignement,
    StatutEtablissement,
    TypeEtablissement,
)
from app.referentiel.normalisation import normaliser
from app.referentiel.schemas import (
    AxeAdmin,
    AxeCreation,
    AxeModification,
    DreAdmin,
    DreCreation,
    DreModification,
    EtablissementAdmin,
    EtablissementCreation,
    EtablissementModification,
    IesgAdmin,
    IesgCreation,
    IesgModification,
    PageEtablissements,
    Remplacement,
)
from app.referentiel.service import filtrer_par_mots

MESSAGE_VERSION = "Cet élément a été modifié entre-temps : recharge la page."

# Contrainte d'unicité violée → message pour le collaborateur.
DOUBLONS = {
    "pk_dre": "Ce code de DRE existe déjà.",
    "uq_dre_nom_normalise": "Une DRE du même nom existe déjà.",
    "uq_iesg_dre_code_nom_normalise": "Une IESG du même nom existe déjà dans cette DRE.",
    "uq_etablissement_iesg_id_nom_normalise": "Un établissement du même nom existe déjà dans cette IESG.",
    "pk_axe": "Ce code d'axe existe déjà.",
    "uq_axe_libelle_normalise": "Un axe du même libellé existe déjà.",
}


class Refus(Exception):
    def __init__(self, message: str, statut: int = 400) -> None:
        super().__init__(message)
        self.statut = statut


class Introuvable(Exception):
    pass


class HorsPerimetre(Exception):
    """L'élément visé n'est pas dans la DRE du collaborateur : la route répond 403 et journalise le refus."""


# Outils communs -----------------------------------------------------------------------------------------------


def _verifier_version(element: Dre | Iesg | Etablissement | Axe, version: int) -> None:
    if element.version != version:
        raise Refus(MESSAGE_VERSION, 409)


def _dans_perimetre(acces: Acces, dre_code: str) -> None:
    if not acces.national and acces.collaborateur.perimetre_dre != dre_code:
        raise HorsPerimetre


def _valeur(valeur: Any) -> Any:
    if isinstance(valeur, StrEnum):
        return valeur.value
    if isinstance(valeur, UUID):
        return str(valeur)
    return valeur


def _appliquer(element: Any, changements: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Applique les champs qui changent vraiment et renvoie leurs valeurs avant et après, pour le journal. Le nom
    normalisé suit le nom ; il ne figure pas au journal."""
    if "nom" in changements:
        changements["nom_normalise"] = normaliser(changements["nom"])
    if "libelle" in changements:
        changements["libelle_normalise"] = normaliser(changements["libelle"])
    avant: dict[str, Any] = {}
    apres: dict[str, Any] = {}
    for champ, nouvelle in changements.items():
        ancienne = getattr(element, champ)
        if ancienne != nouvelle:
            setattr(element, champ, nouvelle)
            if not champ.endswith("_normalise"):
                avant[champ], apres[champ] = _valeur(ancienne), _valeur(nouvelle)
    return avant, apres


def _changements(entree: BaseModel, effacables: tuple[str, ...] = ()) -> dict[str, Any]:
    """Les champs envoyés par le formulaire, sauf la version. Un champ envoyé vide ne compte que s'il peut
    s'effacer, comme la zone d'une IESG ou la localité d'un établissement."""
    return {
        champ: getattr(entree, champ)
        for champ in entree.model_fields_set
        if champ != "version" and (getattr(entree, champ) is not None or champ in effacables)
    }


def _journaliser(
    db: AsyncSession,
    acces: Acces,
    cible_type: str,
    cible_id: UUID | str,
    perimetre: str,
    avant: dict[str, Any],
    apres: dict[str, Any],
    *,
    ip: str,
    creation: bool = False,
) -> None:
    if creation:
        action = "referentiel_cree"
    elif apres.get("actif") is False or apres.get("statut") == StatutEtablissement.inactif.value:
        action = "referentiel_desactive"
    elif apres.get("actif") is True or apres.get("statut") == StatutEtablissement.actif.value:
        action = "referentiel_reactive"
    else:
        action = "referentiel_modifie"
    journaliser(
        db,
        action,
        acces.utilisateur,
        cible_type=cible_type,
        cible_id=cible_id,
        perimetre=perimetre,
        details={"apres": apres} if creation else {"avant": avant, "apres": apres},
        adresse_ip=ip,
    )


async def _ecrire(db: AsyncSession) -> None:
    """Envoie les changements ; un doublon ou une écriture concurrente devient un refus lisible."""
    try:
        await db.flush()
    except StaleDataError:
        await db.rollback()
        raise Refus(MESSAGE_VERSION, 409) from None
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        contrainte = getattr(getattr(erreur.orig, "__cause__", None), "constraint_name", None)
        raise Refus(DOUBLONS.get(contrainte or "", "Cet élément existe déjà."), 409) from None


async def _prochain_ordre(db: AsyncSession, colonne: Any) -> int:
    return (await db.scalar(select(func.max(colonne))) or 0) + 1


async def _obtenir[T](db: AsyncSession, modele: type[T], cle: Any) -> T:
    """Verrouille l'élément jusqu'à la fin de la transaction : un garde-fou qui compte ses enfants ne peut pas être
    contourné par une écriture simultanée."""
    element = await db.get(modele, cle, with_for_update=True)
    if element is None:
        raise Introuvable
    return element


async def _etablissements_actifs_par_iesg(db: AsyncSession) -> dict[UUID, int]:
    lignes = await db.execute(
        select(Etablissement.iesg_id, func.count())
        .where(Etablissement.statut == StatutEtablissement.actif)
        .group_by(Etablissement.iesg_id)
    )
    return dict(lignes.all())


def _iesg_admin(iesg: Iesg, comptes: dict[UUID, int]) -> IesgAdmin:
    return IesgAdmin(
        id=iesg.id,
        dre_code=iesg.dre_code,
        nom=iesg.nom,
        zone=iesg.zone,
        actif=iesg.actif,
        version=iesg.version,
        nb_etablissements=comptes.get(iesg.id, 0),
    )


# DRE et IESG ----------------------------------------------------------------------------------------------------


async def lister_dre(db: AsyncSession, acces: Acces, code: str | None = None) -> list[DreAdmin]:
    """Toutes les DRE, actives ou non, avec leurs IESG ; un collaborateur limité à une DRE ne voit que la sienne."""
    requete = select(Dre).order_by(Dre.ordre, Dre.code)
    if not acces.national:
        requete = requete.where(Dre.code == acces.collaborateur.perimetre_dre)
    if code is not None:
        requete = requete.where(Dre.code == code)
    dres: Sequence[Dre] = (await db.scalars(requete)).all()
    iesg = (
        await db.scalars(select(Iesg).where(Iesg.dre_code.in_([d.code for d in dres])).order_by(Iesg.nom_normalise))
    ).all()
    comptes = await _etablissements_actifs_par_iesg(db)
    resultat = []
    for dre in dres:
        branches = [_iesg_admin(i, comptes) for i in iesg if i.dre_code == dre.code]
        resultat.append(
            DreAdmin(
                code=dre.code,
                nom=dre.nom,
                nom_complet=dre.nom_complet,
                region=dre.region,
                ordre=dre.ordre,
                actif=dre.actif,
                version=dre.version,
                nb_etablissements=sum(b.nb_etablissements for b in branches if b.actif),
                iesg=branches,
            )
        )
    return resultat


async def _une_dre(db: AsyncSession, acces: Acces, code: str) -> DreAdmin:
    return (await lister_dre(db, acces, code))[0]


async def creer_dre(db: AsyncSession, acces: Acces, entree: DreCreation, ip: str) -> DreAdmin:
    dre = Dre(
        code=entree.code,
        nom=entree.nom,
        nom_normalise=normaliser(entree.nom),
        nom_complet=entree.nom_complet,
        region=entree.region,
        ordre=entree.ordre or await _prochain_ordre(db, Dre.ordre),
        actif=True,
    )
    if await db.get(Dre, entree.code) is not None:
        raise Refus(DOUBLONS["pk_dre"], 409)
    db.add(dre)
    await _ecrire(db)
    apres = {
        "code": dre.code, "nom": dre.nom, "nom_complet": dre.nom_complet, "region": dre.region.value,
        "ordre": dre.ordre,
    }  # fmt: skip
    _journaliser(db, acces, "dre", dre.code, dre.code, {}, apres, ip=ip, creation=True)
    await db.commit()
    return await _une_dre(db, acces, dre.code)


async def _collaborateurs_sur(db: AsyncSession, code: str) -> list[str]:
    """Les collaborateurs, actifs ou invités, dont le périmètre est cette DRE."""
    lignes = await db.execute(
        select(Collaborateur.prenom, Collaborateur.nom)
        .outerjoin(Utilisateur, Utilisateur.id == Collaborateur.utilisateur_id)
        .where(Collaborateur.perimetre_dre == code)
        .where(or_(Utilisateur.id.is_(None), Utilisateur.statut != StatutCompte.revoque))
        .order_by(Collaborateur.nom, Collaborateur.prenom)
    )
    return [f"{prenom} {nom}" for prenom, nom in lignes]


async def modifier_dre(db: AsyncSession, acces: Acces, code: str, entree: DreModification, ip: str) -> DreAdmin:
    dre = await _obtenir(db, Dre, code)
    _verifier_version(dre, entree.version)
    changements = _changements(entree)
    if changements.get("actif") is False and dre.actif:
        iesg_actives = await db.scalar(select(func.count()).where(Iesg.dre_code == code, Iesg.actif))
        if iesg_actives:
            raise Refus(f"Cette DRE a encore {iesg_actives} IESG actives : déplace-les ou désactive-les d'abord.")
        if noms := await _collaborateurs_sur(db, code):
            raise Refus(f"Change d'abord le périmètre de : {', '.join(noms)}.")
    avant, apres = _appliquer(dre, changements)
    await _ecrire(db)
    if apres:
        _journaliser(db, acces, "dre", dre.code, dre.code, avant, apres, ip=ip)
    await db.commit()
    return await _une_dre(db, acces, dre.code)


async def _dre_active(db: AsyncSession, code: str) -> Dre:
    # Verrouillée : elle ne peut pas être désactivée pendant qu'on y range une IESG.
    dre = await db.get(Dre, code, with_for_update=True)
    if dre is None:
        raise Refus("Cette DRE n'existe pas.")
    if not dre.actif:
        raise Refus("Cette DRE est désactivée : réactive-la d'abord.")
    return dre


async def creer_iesg(db: AsyncSession, acces: Acces, entree: IesgCreation, ip: str) -> IesgAdmin:
    await _dre_active(db, entree.dre_code)
    iesg = Iesg(
        dre_code=entree.dre_code, nom=entree.nom, nom_normalise=normaliser(entree.nom), zone=entree.zone, actif=True
    )
    db.add(iesg)
    await _ecrire(db)
    apres = {"dre_code": iesg.dre_code, "nom": iesg.nom, "zone": iesg.zone}
    _journaliser(db, acces, "iesg", iesg.id, iesg.dre_code, {}, apres, ip=ip, creation=True)
    await db.commit()
    return _iesg_admin(iesg, {})


async def modifier_iesg(db: AsyncSession, acces: Acces, iesg_id: UUID, entree: IesgModification, ip: str) -> IesgAdmin:
    iesg = await _obtenir(db, Iesg, iesg_id)
    _verifier_version(iesg, entree.version)
    changements = _changements(entree, effacables=("zone",))
    if changements.get("dre_code") not in (None, iesg.dre_code):
        await _dre_active(db, changements["dre_code"])
    if changements.get("actif") is True and not iesg.actif:
        await _dre_active(db, changements.get("dre_code") or iesg.dre_code)
    if changements.get("actif") is False and iesg.actif:
        actifs = await db.scalar(
            select(func.count()).where(
                Etablissement.iesg_id == iesg.id, Etablissement.statut == StatutEtablissement.actif
            )
        )
        if actifs:
            raise Refus(f"Cette IESG a encore {actifs} établissements actifs : déplace-les ou désactive-les d'abord.")
    avant, apres = _appliquer(iesg, changements)
    await _ecrire(db)
    if apres:
        _journaliser(db, acces, "iesg", iesg.id, iesg.dre_code, avant, apres, ip=ip)
    await db.commit()
    return _iesg_admin(iesg, await _etablissements_actifs_par_iesg(db))


# Établissements -------------------------------------------------------------------------------------------------


async def _inscrits_par_etablissement(db: AsyncSession, ids: Sequence[UUID]) -> dict[UUID, tuple[int, int]]:
    """Nombre d'élèves et d'encadreurs rattachés à chaque établissement."""
    eleves = dict(
        (await db.execute(
            select(Eleve.etablissement_id, func.count()).where(Eleve.etablissement_id.in_(ids))
            .group_by(Eleve.etablissement_id)
        )).all()
    )  # fmt: skip
    encadreurs = dict(
        (await db.execute(
            select(Encadreur.etablissement_id, func.count()).where(Encadreur.etablissement_id.in_(ids))
            .group_by(Encadreur.etablissement_id)
        )).all()
    )  # fmt: skip
    return {i: (eleves.get(i, 0), encadreurs.get(i, 0)) for i in ids}


def _etablissement_admin(
    etablissement: Etablissement, iesg: Iesg, dre: Dre, inscrits: tuple[int, int] = (0, 0)
) -> EtablissementAdmin:
    return EtablissementAdmin(
        id=etablissement.id,
        nom=etablissement.nom,
        type=etablissement.type,
        localite=etablissement.localite,
        statut=etablissement.statut,
        version=etablissement.version,
        iesg_id=iesg.id,
        iesg=iesg.nom,
        dre_code=dre.code,
        dre=dre.nom,
        modifie_le=etablissement.modifie_le,
        prefecture=etablissement.prefecture,
        ordre=etablissement.ordre,
        import_source=etablissement.import_source,
        nb_eleves=inscrits[0],
        nb_encadreurs=inscrits[1],
    )


async def lister_etablissements(
    db: AsyncSession,
    acces: Acces,
    *,
    recherche: str | None,
    dre_code: str | None,
    iesg_id: UUID | None,
    type_: TypeEtablissement | None,
    statut: StatutEtablissement | None,
    page: int,
    par_page: int,
    ordre: OrdreEnseignement | None = None,
    prefecture: str | None = None,
    importes: bool | None = None,
) -> PageEtablissements:
    requete = (
        select(Etablissement, Iesg, Dre)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
    )
    if not acces.national:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    if recherche:
        requete = filtrer_par_mots(requete, recherche)
    if dre_code:
        requete = requete.where(Iesg.dre_code == dre_code)
    if iesg_id:
        requete = requete.where(Etablissement.iesg_id == iesg_id)
    if type_:
        requete = requete.where(Etablissement.type == type_)
    if statut:
        requete = requete.where(Etablissement.statut == statut)
    if ordre:
        requete = requete.where(Etablissement.ordre == ordre)
    if prefecture:
        # Les préfectures ont une graphie officielle (spec 035) : le back office les propose dans une liste fermée.
        requete = requete.where(Etablissement.prefecture == prefecture.strip())
    if importes is not None:
        # Spec 035 : les établissements créés par l'import de la liste nationale, pour repérer les doublons.
        importe = Etablissement.import_source.is_not(None)
        requete = requete.where(importe if importes else ~importe)
    total = await db.scalar(select(func.count()).select_from(requete.subquery())) or 0
    lignes = (
        await db.execute(
            requete.order_by(Dre.ordre, Iesg.nom_normalise, Etablissement.nom_normalise, Etablissement.id)
            .offset((page - 1) * par_page)
            .limit(par_page)
        )
    ).all()
    inscrits = await _inscrits_par_etablissement(db, [ligne[0].id for ligne in lignes])
    return PageEtablissements(
        total=total,
        page=page,
        par_page=par_page,
        etablissements=[_etablissement_admin(*ligne, inscrits[ligne[0].id]) for ligne in lignes],
    )


async def _iesg_cible(db: AsyncSession, acces: Acces, iesg_id: UUID) -> Iesg:
    # Verrouillée : elle ne peut pas être désactivée pendant qu'on y range un établissement.
    iesg = await db.get(Iesg, iesg_id, with_for_update=True)
    if iesg is None:
        raise Refus("Cette IESG n'existe pas.")
    _dans_perimetre(acces, iesg.dre_code)
    if not iesg.actif:
        raise Refus("Cette IESG est désactivée : réactive-la d'abord.")
    return iesg


async def _detail_etablissement(db: AsyncSession, etablissement_id: UUID) -> EtablissementAdmin:
    ligne = (
        await db.execute(
            select(Etablissement, Iesg, Dre)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Etablissement.id == etablissement_id)
        )
    ).one()
    inscrits = await _inscrits_par_etablissement(db, [etablissement_id])
    return _etablissement_admin(*ligne, inscrits[etablissement_id])


async def creer_etablissement(
    db: AsyncSession, acces: Acces, entree: EtablissementCreation, ip: str
) -> EtablissementAdmin:
    iesg = await _iesg_cible(db, acces, entree.iesg_id)
    etablissement = Etablissement(
        iesg_id=iesg.id,
        nom=entree.nom,
        nom_normalise=normaliser(entree.nom),
        type=entree.type,
        localite=entree.localite,
        prefecture=entree.prefecture,
        ordre=entree.ordre,
        statut=StatutEtablissement.actif,
    )
    db.add(etablissement)
    await _ecrire(db)
    apres = {
        "iesg_id": str(iesg.id),
        "nom": etablissement.nom,
        "type": etablissement.type.value,
        "prefecture": etablissement.prefecture,
        "ordre": etablissement.ordre.value if etablissement.ordre else None,
    }
    _journaliser(db, acces, "etablissement", etablissement.id, iesg.dre_code, {}, apres, ip=ip, creation=True)
    await db.commit()
    return await _detail_etablissement(db, etablissement.id)


async def modifier_etablissement(
    db: AsyncSession, acces: Acces, etablissement_id: UUID, entree: EtablissementModification, ip: str
) -> EtablissementAdmin:
    etablissement = await _obtenir(db, Etablissement, etablissement_id)
    iesg = await _obtenir(db, Iesg, etablissement.iesg_id)
    _dans_perimetre(acces, iesg.dre_code)
    _verifier_version(etablissement, entree.version)
    changements = _changements(entree, effacables=("localite", "prefecture", "ordre"))
    if changements.get("iesg_id") not in (None, iesg.id):
        iesg = await _iesg_cible(db, acces, changements["iesg_id"])
    reactivation = (
        changements.get("statut") == StatutEtablissement.actif and etablissement.statut != StatutEtablissement.actif
    )
    if reactivation and not iesg.actif:
        raise Refus("Son IESG est désactivée : réactive-la d'abord.")
    avant, apres = _appliquer(etablissement, changements)
    await _ecrire(db)
    if apres:
        _journaliser(db, acces, "etablissement", etablissement.id, iesg.dre_code, avant, apres, ip=ip)
    await db.commit()
    return await _detail_etablissement(db, etablissement.id)


async def remplacer_proposition(
    db: AsyncSession, acces: Acces, etablissement_id: UUID, entree: Remplacement, ip: str
) -> EtablissementAdmin:
    """Un établissement proposé à l'inscription existait déjà sous un autre nom : ses élèves et ses encadreurs
    rejoignent le bon, et la proposition est désactivée. Le journal garde l'un et l'autre."""
    proposition = await _obtenir(db, Etablissement, etablissement_id)
    iesg = await _obtenir(db, Iesg, proposition.iesg_id)
    _dans_perimetre(acces, iesg.dre_code)
    _verifier_version(proposition, entree.version)
    if proposition.statut != StatutEtablissement.propose:
        raise Refus("Seul un établissement proposé peut être remplacé.", 409)
    cible = await db.get(Etablissement, entree.cible_id, with_for_update=True)
    if cible is None or cible.id == proposition.id or cible.statut != StatutEtablissement.actif:
        raise Refus("Choisis un établissement actif de la liste.")
    iesg_cible = await _obtenir(db, Iesg, cible.iesg_id)
    _dans_perimetre(acces, iesg_cible.dre_code)
    deplaces = await db.execute(
        # La version monte : un profil ouvert avant le remplacement ne l'écrase pas ensuite.
        update(Eleve)
        .where(Eleve.etablissement_id == proposition.id)
        .values(etablissement_id=cible.id, version=Eleve.version + 1)
    )
    encadreurs_deplaces = await db.execute(
        update(Encadreur)
        .where(Encadreur.etablissement_id == proposition.id)
        .values(etablissement_id=cible.id, version=Encadreur.version + 1)
    )
    proposition.statut = StatutEtablissement.inactif
    await _ecrire(db)
    # Spec 033 : le club de la proposition et ses membres rejoignent le club du bon établissement.
    from app.clubs.affiliations import remplacer_etablissement

    await remplacer_etablissement(db, proposition.id, cible.id, acces.utilisateur, ip)
    journaliser(
        db, "etablissement_remplace", acces.utilisateur, cible_type="etablissement", cible_id=proposition.id,
        perimetre=iesg.dre_code,
        details={"avant": {"etablissement_id": str(proposition.id), "nom": proposition.nom},
                 "apres": {"etablissement_id": str(cible.id), "nom": cible.nom}, "nb_eleves": deplaces.rowcount,
                 "nb_encadreurs": encadreurs_deplaces.rowcount},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await _detail_etablissement(db, cible.id)


# Axes -----------------------------------------------------------------------------------------------------------


async def lister_axes(db: AsyncSession) -> list[AxeAdmin]:
    return [AxeAdmin.model_validate(a) for a in (await db.scalars(select(Axe).order_by(Axe.ordre, Axe.code))).all()]


async def creer_axe(db: AsyncSession, acces: Acces, entree: AxeCreation, ip: str) -> AxeAdmin:
    if await db.get(Axe, entree.code) is not None:
        raise Refus(DOUBLONS["pk_axe"], 409)
    axe = Axe(
        code=entree.code,
        libelle=entree.libelle,
        libelle_normalise=normaliser(entree.libelle),
        description=entree.description,
        ordre=entree.ordre or await _prochain_ordre(db, Axe.ordre),
        actif=True,
    )
    db.add(axe)
    await _ecrire(db)
    apres = {"code": axe.code, "libelle": axe.libelle, "ordre": axe.ordre}
    _journaliser(db, acces, "axe", axe.code, "national", {}, apres, ip=ip, creation=True)
    await db.commit()
    return AxeAdmin.model_validate(axe)


async def modifier_axe(db: AsyncSession, acces: Acces, code: str, entree: AxeModification, ip: str) -> AxeAdmin:
    axe = await _obtenir(db, Axe, code)
    _verifier_version(axe, entree.version)
    changements = _changements(entree)
    if changements.get("actif") is False and axe.actif:
        autres = await db.scalar(select(func.count()).where(Axe.actif, Axe.code != code))
        if not autres:
            raise Refus("Il faut garder au moins un axe actif.")
    avant, apres = _appliquer(axe, changements)
    await _ecrire(db)
    if apres:
        _journaliser(db, acces, "axe", axe.code, "national", avant, apres, ip=ip)
    await db.commit()
    return AxeAdmin.model_validate(axe)
