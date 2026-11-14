"""Carte nationale des Clubs Santé (spec 033) : trois chiffres et l'arbre région → DRE → inspection → établissement.

Les chiffres se calculent à partir des données réelles, un établissement à la fois : un club ne peut pas être compté
deux fois. Aucune donnée personnelle ne sort d'ici : ni nom, ni contact, ni effectif.
"""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import CLUB_VIVANT, Club, EtatClub
from app.clubs.schemas import Carte, CarteDre, CarteEtablissement, CarteIesg, CarteRegion, ChiffresCarte
from app.referentiel.models import Dre, Etablissement, Iesg, StatutEtablissement
from app.referentiel.regions import NOMS, ORDRE

EXISTANTS = {"actif", "en_regularisation", "suspendu"}
ACTIFS = {"actif", "en_regularisation"}


def _statut_public(statut: str | None) -> str:
    if statut is None:
        return "reference"
    if statut == EtatClub.en_regularisation.value:
        return "actif"
    return statut


async def carte(db: AsyncSession) -> Carte:
    instant = activation.maintenant()
    clubs = {
        etablissement_id: (club_id, statut, terrain)
        for etablissement_id, club_id, statut, terrain in (
            await db.execute(
                select(Club.etablissement_id, Club.id, activation.etat_effectif(instant), Club.declare_terrain).where(
                    Club.etat.in_(CLUB_VIVANT)
                )
            )
        ).all()
    }
    lignes = (
        await db.execute(
            select(Etablissement, Iesg, Dre)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Etablissement.statut == StatutEtablissement.actif, Iesg.actif, Dre.actif)
            .order_by(Dre.ordre, Iesg.nom_normalise, Etablissement.nom_normalise)
        )
    ).all()

    par_iesg: dict[UUID, list[CarteEtablissement]] = defaultdict(list)
    iesg_de: dict[UUID, Iesg] = {}
    iesg_par_dre: dict[str, list[UUID]] = defaultdict(list)
    dres: dict[str, Dre] = {}
    existant: dict[UUID, bool] = {}
    actif: dict[UUID, bool] = {}
    for etablissement, iesg, dre in lignes:
        club_id, statut, terrain = clubs.get(etablissement.id, (None, None, False))
        existant[etablissement.id] = bool(terrain) or statut in EXISTANTS
        actif[etablissement.id] = statut in ACTIFS
        par_iesg[iesg.id].append(
            CarteEtablissement(
                id=etablissement.id,
                nom=etablissement.nom,
                localite=etablissement.localite,
                statut=_statut_public(statut),
                declare_terrain=bool(terrain),
                club_id=club_id,
            )
        )
        if iesg.id not in iesg_de:
            iesg_de[iesg.id] = iesg
            iesg_par_dre[dre.code].append(iesg.id)
        dres[dre.code] = dre

    def compter(etablissements: list[CarteEtablissement]) -> tuple[int, int, int]:
        return (
            len(etablissements),
            sum(existant[e.id] for e in etablissements),
            sum(actif[e.id] for e in etablissements),
        )

    regions: dict[str, list[CarteDre]] = defaultdict(list)
    for code, dre in dres.items():
        branches = []
        for iesg_id in iesg_par_dre[code]:
            iesg = iesg_de[iesg_id]
            n, c, a = compter(par_iesg[iesg_id])
            branches.append(
                CarteIesg(
                    id=iesg.id, nom=iesg.nom, zone=iesg.zone, nb_etablissements=n, nb_clubs=c, nb_actifs=a,
                    etablissements=par_iesg[iesg_id],
                )
            )  # fmt: skip
        regions[dre.region.value].append(
            CarteDre(
                code=dre.code,
                nom=dre.nom,
                nom_complet=dre.nom_complet,
                nb_etablissements=sum(b.nb_etablissements for b in branches),
                nb_clubs=sum(b.nb_clubs for b in branches),
                nb_actifs=sum(b.nb_actifs for b in branches),
                iesg=branches,
            )
        )
    resultat = [
        CarteRegion(
            code=region.value,
            nom=NOMS[region],
            nb_etablissements=sum(d.nb_etablissements for d in regions[region.value]),
            nb_clubs=sum(d.nb_clubs for d in regions[region.value]),
            nb_actifs=sum(d.nb_actifs for d in regions[region.value]),
            dres=regions[region.value],
        )
        for region in ORDRE
        if regions[region.value]
    ]
    return Carte(
        chiffres=ChiffresCarte(
            etablissements=len(existant), clubs=sum(existant.values()), clubs_actifs=sum(actif.values())
        ),
        regions=resultat,
    )
