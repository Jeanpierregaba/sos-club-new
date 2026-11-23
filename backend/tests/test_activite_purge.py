"""Purge du suivi d'activité (spec 051) : totaux à 90 jours, sels, recherches rares, présences."""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activite import purge
from app.activite.models import (
    EvenementActivite,
    PresenceSemaine,
    SelActivite,
    TotalActiviteJour,
    TypeEvenement,
    VisiteursJour,
)

AUJOURDHUI = date(2026, 11, 23)  # un lundi


def evenement(jour: date, visiteur: str, type_: TypeEvenement = TypeEvenement.page_vue, **champs: Any) -> Any:
    return EvenementActivite(
        jour=jour, type=type_, visiteur=visiteur, chemin=champs.pop("chemin", "/"), appareil="telephone", **champs
    )


def ajouter(en_base: Callable[..., Any], *lignes: Any) -> None:
    async def _ajouter(db: AsyncSession) -> None:
        db.add_all(lignes)

    en_base(_ajouter)


def purger(en_base: Callable[..., Any]) -> int:
    return en_base(lambda db: purge.purger(db, AUJOURDHUI))


def compter(en_base: Callable[..., Any], modele: Any) -> int:
    return en_base(lambda db: db.scalar(select(func.count()).select_from(modele)))


def pages_par_chemin(en_base: Callable[..., Any]) -> dict[str, int]:
    """Ce que lit la page : événements bruts plus totaux."""

    async def lire(db: AsyncSession) -> dict[str, int]:
        bruts = dict(
            (await db.execute(select(EvenementActivite.chemin, func.count()).group_by(EvenementActivite.chemin))).all()
        )
        totaux = dict(
            (
                await db.execute(
                    select(TotalActiviteJour.chemin, func.sum(TotalActiviteJour.evenements)).group_by(
                        TotalActiviteJour.chemin
                    )
                )
            ).all()
        )
        return {c: bruts.get(c, 0) + int(totaux.get(c, 0)) for c in bruts.keys() | totaux.keys()}

    return en_base(lire)


def test_au_dela_de_90_jours_les_totaux_remplacent_le_detail_sans_changer(en_base: Callable[..., Any]) -> None:
    vieux = AUJOURDHUI - timedelta(days=91)
    recent = AUJOURDHUI - timedelta(days=10)
    ajouter(
        en_base,
        evenement(vieux, "a", chemin="/jeux"),
        evenement(vieux, "a", chemin="/jeux"),
        evenement(vieux, "b", chemin="/jeux"),
        evenement(vieux, "b", chemin="/"),
        evenement(recent, "c", chemin="/jeux"),
    )
    avant = pages_par_chemin(en_base)
    assert purger(en_base) == 4
    assert pages_par_chemin(en_base) == avant == {"/jeux": 4, "/": 1}
    assert compter(en_base, EvenementActivite) == 1
    jeux = en_base(lambda db: db.scalar(select(TotalActiviteJour).where(TotalActiviteJour.chemin == "/jeux")))
    assert (jeux.evenements, jeux.visiteurs, jeux.detail) == (3, 2, "")
    assert en_base(lambda db: db.get(VisiteursJour, vieux)).visiteurs == 2


def test_la_purge_se_relance_sans_rien_doubler(en_base: Callable[..., Any]) -> None:
    ajouter(en_base, evenement(AUJOURDHUI - timedelta(days=100), "a"))
    purger(en_base)
    assert purger(en_base) == 0
    assert compter(en_base, TotalActiviteJour) == 1


def test_un_mot_cherche_par_moins_de_3_visiteurs_part_au_bout_de_7_jours(en_base: Callable[..., Any]) -> None:
    il_y_a_8 = AUJOURDHUI - timedelta(days=8)
    recherche = TypeEvenement.recherche
    ajouter(
        en_base,
        evenement(il_y_a_8, "a", recherche, chemin="/inscription", detail="kodjo mensah"),
        evenement(il_y_a_8, "a", recherche, chemin="/inscription", detail="kodjo mensah"),
        evenement(AUJOURDHUI, "b", recherche, chemin="/inscription", detail="lycée de kpalimé"),
        *[evenement(il_y_a_8, v, recherche, chemin="/inscription", detail="lycée de tsévié") for v in "xyz"],
    )
    purger(en_base)
    restants = en_base(lambda db: db.scalars(select(EvenementActivite.detail)))
    assert sorted(restants) == ["lycée de kpalimé", "lycée de tsévié", "lycée de tsévié", "lycée de tsévié"]


def test_les_sels_passes_et_les_vieilles_presences_sont_effaces(
    en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]
) -> None:
    eleve = creer_utilisateur()
    ajouter(
        en_base,
        SelActivite(jour=AUJOURDHUI - timedelta(days=1), sel=b"x" * 32),
        SelActivite(jour=AUJOURDHUI, sel=b"y" * 32),
        PresenceSemaine(utilisateur_id=eleve.id, semaine=AUJOURDHUI - timedelta(weeks=27)),
        PresenceSemaine(utilisateur_id=eleve.id, semaine=AUJOURDHUI - timedelta(weeks=26)),
    )
    purger(en_base)
    assert list(en_base(lambda db: db.scalars(select(SelActivite.jour)))) == [AUJOURDHUI]
    assert list(en_base(lambda db: db.scalars(select(PresenceSemaine.semaine)))) == [AUJOURDHUI - timedelta(weeks=26)]


def test_une_presence_part_avec_le_compte(en_base: Callable[..., Any], creer_utilisateur: Callable[..., Any]) -> None:
    from app.comptes.models import Utilisateur

    eleve = creer_utilisateur()
    ajouter(en_base, PresenceSemaine(utilisateur_id=eleve.id, semaine=AUJOURDHUI))

    async def effacer(db: AsyncSession) -> None:
        await db.delete(await db.get(Utilisateur, eleve.id))

    en_base(effacer)
    assert compter(en_base, PresenceSemaine) == 0
