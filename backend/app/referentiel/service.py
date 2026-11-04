"""Règles du référentiel (spec 016). Les listes publiques ne montrent que ce qui est actif, à tous les niveaux : un
établissement actif d'une IESG désactivée n'apparaît pas."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.referentiel.models import Axe, Dre, Etablissement, Iesg, StatutEtablissement
from app.referentiel.normalisation import normaliser
from app.referentiel.schemas import (
    AxePublic,
    DreAnnuaire,
    DrePublique,
    EtablissementPublic,
    EtablissementTrouve,
    IesgAnnuaire,
    IesgPublique,
)

RESULTATS_MAX = 20


def _actifs() -> Select[tuple[Etablissement, Iesg, Dre]]:
    return (
        select(Etablissement, Iesg, Dre)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .where(Etablissement.statut == StatutEtablissement.actif, Iesg.actif, Dre.actif)
    )


async def _dre_et_iesg_actives(db: AsyncSession) -> list[tuple[Dre, list[Iesg]]]:
    lignes = await db.execute(
        select(Dre, Iesg)
        .outerjoin(Iesg, (Iesg.dre_code == Dre.code) & Iesg.actif)
        .where(Dre.actif)
        .order_by(Dre.ordre, Dre.code, Iesg.nom_normalise)
    )
    arbre: dict[str, tuple[Dre, list[Iesg]]] = {}
    for dre, iesg in lignes:
        _, liste = arbre.setdefault(dre.code, (dre, []))
        if iesg is not None:
            liste.append(iesg)
    return list(arbre.values())


async def lister_dre(db: AsyncSession) -> list[DrePublique]:
    # Les IESG et DRE inactives sont déjà écartées par l'arbre : il suffit de compter les établissements actifs.
    comptes = dict(
        (
            await db.execute(
                select(Etablissement.iesg_id, func.count())
                .where(Etablissement.statut == StatutEtablissement.actif)
                .group_by(Etablissement.iesg_id)
            )
        ).all()
    )
    resultat = []
    for dre, iesg in await _dre_et_iesg_actives(db):
        publiques = [
            IesgPublique(id=i.id, nom=i.nom, zone=i.zone, nb_etablissements=comptes.get(i.id, 0)) for i in iesg
        ]
        resultat.append(
            DrePublique(
                code=dre.code,
                nom=dre.nom,
                nom_complet=dre.nom_complet,
                nb_etablissements=sum(i.nb_etablissements for i in publiques),
                iesg=publiques,
            )
        )
    return resultat


async def annuaire(db: AsyncSession) -> list[DreAnnuaire]:
    """Tout l'arbre actif, établissements compris : la carte des clubs cherche dedans sans aller-retour."""
    par_iesg: dict[UUID, list[EtablissementPublic]] = defaultdict(list)
    for etablissement, iesg, _ in (await db.execute(_actifs().order_by(Etablissement.nom_normalise))).all():
        par_iesg[iesg.id].append(EtablissementPublic.model_validate(etablissement))
    resultat = []
    for dre, iesg in await _dre_et_iesg_actives(db):
        branches = [
            IesgAnnuaire(
                id=i.id, nom=i.nom, zone=i.zone, nb_etablissements=len(par_iesg[i.id]), etablissements=par_iesg[i.id]
            )
            for i in iesg
        ]
        resultat.append(
            DreAnnuaire(
                code=dre.code,
                nom=dre.nom,
                nom_complet=dre.nom_complet,
                nb_etablissements=sum(b.nb_etablissements for b in branches),
                iesg=branches,
            )
        )
    return resultat


def _trouve(etablissement: Etablissement, iesg: Iesg, dre: Dre) -> EtablissementTrouve:
    return EtablissementTrouve(
        id=etablissement.id,
        nom=etablissement.nom,
        type=etablissement.type,
        iesg_id=iesg.id,
        iesg=iesg.nom,
        dre_code=dre.code,
        dre=dre.nom,
    )


def filtrer_par_mots(requete: Select, recherche: str) -> Select:
    """Chaque mot de la recherche doit se trouver dans le nom, accents et majuscules ignorés."""
    for mot in normaliser(recherche).split():
        requete = requete.where(Etablissement.nom_normalise.contains(mot, autoescape=True))
    return requete


async def chercher_etablissements(
    db: AsyncSession, *, iesg_id: UUID | None, recherche: str | None, dre_code: str | None
) -> list[EtablissementTrouve]:
    requete = _actifs().order_by(Etablissement.nom_normalise)
    if iesg_id is not None:
        requete = requete.where(Etablissement.iesg_id == iesg_id)
    if dre_code is not None:
        requete = requete.where(Iesg.dre_code == dre_code)
    if recherche is not None:
        requete = filtrer_par_mots(requete, recherche).limit(RESULTATS_MAX)
    return [_trouve(*ligne) for ligne in (await db.execute(requete)).all()]


async def lister_axes(db: AsyncSession) -> list[AxePublic]:
    axes = await db.scalars(select(Axe).where(Axe.actif).order_by(Axe.ordre, Axe.code))
    return [AxePublic.model_validate(a) for a in axes.all()]
