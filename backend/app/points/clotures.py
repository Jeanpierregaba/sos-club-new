"""Clôture d'un semestre et Top 3 (spec 037, R14).

Le gel photographie le classement national des élèves du semestre ; l'admin contrôle les candidats, en écarte avec
un motif, valide le Top 3 puis le publie. La photo n'est jamais une source de points : le registre reste la seule
(ADR-0004). Chaque transition verrouille la clôture et vérifie l'état attendu : deux admins simultanés obtiennent
un conflit, jamais un état mixte.
"""

from uuid import UUID, uuid7

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.comptes.models import StatutCompte, Utilisateur
from app.notifications.service import notifier
from app.points import classements
from app.points.bareme import ACTION_CORRECTION
from app.points.models import CandidatCloture, ClotureSemestre, EtatCloture, MouvementPoints, Semestre
from app.points.registre import _motif
from app.points.schemas import (
    CandidatAdmin,
    ChangementActuel,
    ClotureDetail,
    ClotureResume,
    Distinction,
    EcartActuel,
    EtapesCloture,
    LaureatAdmin,
    LaureatPublic,
    PalmaresPublic,
    SemestreCloture,
    SemestrePalmares,
)
from app.points.service import aujourd_hui, maintenant
from app.referentiel.administration import Introuvable, Refus

TAILLE_PHOTO = 50
DISTINCTIONS = {1: "Grand Champion", 2: "Vice-Champion", 3: "Jeune Talent"}
LIEN_PALMARES = "/hall-of-fame#palmares"


# Lecture -------------------------------------------------------------------------------------------------------


async def _semestre(db: AsyncSession, semestre_id: UUID) -> Semestre:
    semestre = await db.get(Semestre, semestre_id)
    if semestre is None:
        raise Introuvable
    return semestre


async def _verrouiller(db: AsyncSession, semestre_id: UUID) -> ClotureSemestre:
    cloture = await db.scalar(
        select(ClotureSemestre).where(ClotureSemestre.semestre_id == semestre_id).with_for_update()
    )
    if cloture is None:
        raise Introuvable
    return cloture


def _exiger(cloture: ClotureSemestre, etat: EtatCloture, message: str) -> None:
    if cloture.etat is not etat:
        raise Refus(message, 409)


async def _candidats(db: AsyncSession, semestre_id: UUID) -> list[CandidatCloture]:
    return list(
        (
            await db.scalars(
                select(CandidatCloture).where(CandidatCloture.semestre_id == semestre_id).order_by(CandidatCloture.rang)
            )
        ).all()
    )


def _top3(candidats: list[CandidatCloture], etat: EtatCloture) -> list[CandidatCloture]:
    """Après validation, les places figées ; avant, les trois premiers candidats non écartés de la photo."""
    if etat is EtatCloture.gele:
        return [c for c in candidats if c.ecarte_le is None][:3]
    return sorted((c for c in candidats if c.place is not None), key=lambda c: c.place or 0)


def _laureat(candidat: CandidatCloture, position: int) -> LaureatAdmin:
    return LaureatAdmin(
        utilisateur_id=candidat.utilisateur_id,
        place=candidat.place,
        distinction=DISTINCTIONS[candidat.place or position],
        pseudonyme=candidat.pseudonyme,
        club=candidat.club,
        dre=candidat.dre,
        points=candidat.points,
    )


async def lister(db: AsyncSession) -> list[ClotureResume]:
    jour = aujourd_hui()
    lignes = (
        await db.execute(
            select(Semestre, ClotureSemestre)
            .outerjoin(ClotureSemestre, ClotureSemestre.semestre_id == Semestre.id)
            .where(Semestre.debut <= jour)
            .order_by(Semestre.debut.desc())
        )
    ).all()
    return [
        ClotureResume(
            semestre_id=semestre.id,
            libelle=semestre.libelle,
            debut=semestre.debut,
            fin=semestre.fin,
            termine=semestre.fin < jour,
            etat=cloture.etat.value if cloture else "ouvert",
            publie_le=cloture.publie_le if cloture else None,
        )
        for semestre, cloture in lignes
    ]


async def _identifiants(db: AsyncSession, ids: set[UUID]) -> dict[UUID, Utilisateur]:
    if not ids:
        return {}
    return {u.id: u for u in (await db.scalars(select(Utilisateur).where(Utilisateur.id.in_(ids)))).all()}


async def _registre_du_semestre(db: AsyncSession, semestre_id: UUID, ids: set[UUID]) -> dict[UUID, tuple[int, int]]:
    """Corrections et annulations du semestre par candidat : ce que l'admin examine avant de valider."""
    if not ids:
        return {}
    lignes = await db.execute(
        select(
            MouvementPoints.utilisateur_id,
            func.count().filter(MouvementPoints.action == ACTION_CORRECTION, MouvementPoints.annule_id.is_(None)),
            func.count().filter(MouvementPoints.annule_id.is_not(None)),
        )
        .where(MouvementPoints.semestre_id == semestre_id, MouvementPoints.utilisateur_id.in_(ids))
        .group_by(MouvementPoints.utilisateur_id)
    )
    return {utilisateur_id: (int(c), int(a)) for utilisateur_id, c, a in lignes.all()}


async def _ecart_actuel(
    db: AsyncSession, semestre: Semestre, cloture: ClotureSemestre, candidats: list[CandidatCloture]
) -> EcartActuel:
    """Ce que donnerait un regel maintenant : candidats dont les points ont changé, entrants, sortants (exclus ou
    simplement au-delà des 50 premiers) et Top 3 différent."""
    complet = await classements.classement_a_figer(db, semestre, limite=None)
    ecartes = {c.utilisateur_id for c in candidats if c.ecarte_le is not None}
    gel = {c.utilisateur_id: c for c in candidats}
    tous = {ligne.utilisateur_id: ligne for ligne in complet}
    photo = {ligne.utilisateur_id for ligne in complet[:TAILLE_PHOTO]}
    changements = [
        ChangementActuel(pseudonyme=ligne.pseudonyme, points_gel=gel[uid].points if uid in gel else None,
                         points_actuels=ligne.points, hors_photo=uid not in photo)
        for uid, ligne in tous.items()
        if (uid in photo and uid not in gel)
        or (uid in gel and (gel[uid].points != ligne.points or uid not in photo))
    ] + [
        ChangementActuel(pseudonyme=candidat.pseudonyme, points_gel=candidat.points, points_actuels=None)
        for uid, candidat in gel.items()
        if uid not in tous
    ]  # fmt: skip
    top_actuel = [ligne.utilisateur_id for ligne in complet if ligne.utilisateur_id not in ecartes][:3]
    top_gel = [c.utilisateur_id for c in _top3(candidats, cloture.etat)]
    return EcartActuel(top3_different=top_actuel != top_gel, changements=changements)


async def detail(db: AsyncSession, semestre_id: UUID) -> ClotureDetail:
    semestre = await _semestre(db, semestre_id)
    cloture = await db.get(ClotureSemestre, semestre_id)
    if cloture is None:
        raise Introuvable
    candidats = await _candidats(db, semestre_id)
    ids = {c.utilisateur_id for c in candidats}
    etapes = (cloture.gele_par, cloture.valide_par, cloture.publie_par, *(c.ecarte_par for c in candidats))
    auteurs = await _identifiants(db, ids | {u for u in etapes if u is not None})
    registre = await _registre_du_semestre(db, semestre_id, ids)

    def identifiant(utilisateur_id: UUID | None) -> str | None:
        return auteurs[utilisateur_id].identifiant if utilisateur_id in auteurs else None

    return ClotureDetail(
        semestre=SemestreCloture(id=semestre.id, libelle=cloture.libelle, debut=cloture.debut, fin=cloture.fin),
        etat=cloture.etat.value,
        etapes=EtapesCloture(
            gele_le=cloture.gele_le,
            gele_par=identifiant(cloture.gele_par) or "",
            valide_le=cloture.valide_le,
            valide_par=identifiant(cloture.valide_par),
            publie_le=cloture.publie_le,
            publie_par=identifiant(cloture.publie_par),
        ),
        candidats=[
            CandidatAdmin(
                utilisateur_id=c.utilisateur_id,
                rang=c.rang,
                rang_brut=c.rang_brut,
                pseudonyme=c.pseudonyme,
                identifiant=identifiant(c.utilisateur_id) or "",
                statut=auteurs[c.utilisateur_id].statut.value if c.utilisateur_id in auteurs else "inconnu",
                club=c.club,
                dre=c.dre,
                points=c.points,
                atteint_le=c.atteint_le,
                corrections=registre.get(c.utilisateur_id, (0, 0))[0],
                annulations=registre.get(c.utilisateur_id, (0, 0))[1],
                ecarte=c.ecarte_le is not None,
                motif_ecart=c.motif_ecart,
                ecarte_le=c.ecarte_le,
                ecarte_par=identifiant(c.ecarte_par),
            )
            for c in candidats
        ],
        top3=[_laureat(c, position) for position, c in enumerate(_top3(candidats, cloture.etat), start=1)],
        ecart_actuel=(
            await _ecart_actuel(db, semestre, cloture, candidats)
            if cloture.etat is not EtatCloture.publie
            else EcartActuel(top3_different=False, changements=[])
        ),
    )


# Gel -----------------------------------------------------------------------------------------------------------


async def geler(db: AsyncSession, acces: Acces, semestre_id: UUID, ip: str) -> ClotureDetail:
    """Gèle le semestre, ou le regèle tant que la clôture est à l'état gelé ; un regel reporte les écarts sur les
    élèves toujours présents dans la photo."""
    semestre = await _semestre(db, semestre_id)
    if aujourd_hui() <= semestre.fin:
        raise Refus("Un semestre se gèle seulement après sa date de fin.", 409)
    instant = maintenant()
    # Deux gels simultanés : la clé primaire n'en garde qu'un, le second attend le verrou puis regèle.
    creee = await db.scalar(
        insert(ClotureSemestre)
        .values(
            semestre_id=semestre.id, etat=EtatCloture.gele, libelle=semestre.libelle, debut=semestre.debut,
            fin=semestre.fin, gele_le=instant, gele_par=acces.utilisateur.id,
        )
        .on_conflict_do_nothing(index_elements=["semestre_id"])
        .returning(ClotureSemestre.semestre_id)
    )  # fmt: skip
    regel = creee is None
    cloture = await _verrouiller(db, semestre.id)
    _exiger(cloture, EtatCloture.gele, "Cette clôture est validée ou publiée : elle ne se regèle plus.")

    # Un second gel concurrent devient un regel journalisé : le regel est permis tant que la clôture est gelée.
    anciens = {c.utilisateur_id: c for c in await _candidats(db, semestre.id) if c.ecarte_le is not None}
    await db.execute(delete(CandidatCloture).where(CandidatCloture.semestre_id == semestre.id))
    photo = await classements.classement_a_figer(db, semestre, limite=TAILLE_PHOTO)
    reportes = sum(1 for ligne in photo if ligne.utilisateur_id in anciens)
    for ligne in photo:
        ecart = anciens.get(ligne.utilisateur_id)
        db.add(
            CandidatCloture(
                id=uuid7(), semestre_id=semestre.id, utilisateur_id=ligne.utilisateur_id, rang=ligne.rang,
                rang_brut=ligne.rang_brut, pseudonyme=ligne.pseudonyme, club=ligne.club, dre=ligne.dre,
                points=ligne.points, atteint_le=ligne.atteint_le,
                ecarte_le=ecart.ecarte_le if ecart else None, ecarte_par=ecart.ecarte_par if ecart else None,
                motif_ecart=ecart.motif_ecart if ecart else None,
            )
        )  # fmt: skip
    cloture.libelle, cloture.debut, cloture.fin = semestre.libelle, semestre.debut, semestre.fin
    cloture.gele_le, cloture.gele_par = instant, acces.utilisateur.id
    journaliser(
        db, "semestre_regele" if regel else "semestre_gele", acces.utilisateur, cible_type="semestre",
        cible_id=semestre.id, perimetre="national",
        details={"libelle": semestre.libelle, "candidats": len(photo), "ecartes_reportes": reportes,
                 "ecarts_perdus": len(anciens) - reportes},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await detail(db, semestre.id)


# Contrôle ------------------------------------------------------------------------------------------------------


async def _candidat(db: AsyncSession, semestre_id: UUID, utilisateur_id: UUID) -> CandidatCloture:
    candidat = await db.scalar(
        select(CandidatCloture).where(
            CandidatCloture.semestre_id == semestre_id, CandidatCloture.utilisateur_id == utilisateur_id
        )
    )
    if candidat is None:
        raise Introuvable
    return candidat


async def ecarter(
    db: AsyncSession, acces: Acces, semestre_id: UUID, utilisateur_id: UUID, motif: str, ip: str
) -> ClotureDetail:
    motif = _motif(motif)
    cloture = await _verrouiller(db, semestre_id)
    _exiger(cloture, EtatCloture.gele, "On n'écarte un candidat que sur une clôture gelée.")
    candidat = await _candidat(db, semestre_id, utilisateur_id)
    if candidat.ecarte_le is not None:
        raise Refus("Ce candidat est déjà écarté.", 409)
    candidat.ecarte_le, candidat.ecarte_par, candidat.motif_ecart = maintenant(), acces.utilisateur.id, motif
    journaliser(
        db, "candidat_ecarte", acces.utilisateur, cible_type="semestre", cible_id=semestre_id, perimetre="national",
        details={"libelle": cloture.libelle, "candidat": str(utilisateur_id), "pseudonyme": candidat.pseudonyme,
                 "rang": candidat.rang, "motif": motif},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await detail(db, semestre_id)


async def reintegrer(db: AsyncSession, acces: Acces, semestre_id: UUID, utilisateur_id: UUID, ip: str) -> ClotureDetail:
    cloture = await _verrouiller(db, semestre_id)
    _exiger(cloture, EtatCloture.gele, "On ne réintègre un candidat que sur une clôture gelée.")
    candidat = await _candidat(db, semestre_id, utilisateur_id)
    if candidat.ecarte_le is None:
        raise Refus("Ce candidat n'est pas écarté.", 409)
    candidat.ecarte_le = candidat.ecarte_par = candidat.motif_ecart = None
    journaliser(
        db, "candidat_reintegre", acces.utilisateur, cible_type="semestre", cible_id=semestre_id,
        perimetre="national",
        details={"libelle": cloture.libelle, "candidat": str(utilisateur_id), "pseudonyme": candidat.pseudonyme},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await detail(db, semestre_id)


# Validation et publication -------------------------------------------------------------------------------------


def _resume_laureats(laureats: list[CandidatCloture]) -> list[dict[str, object]]:
    return [{"place": c.place, "pseudonyme": c.pseudonyme, "points": c.points} for c in laureats]


async def valider(db: AsyncSession, acces: Acces, semestre_id: UUID, ip: str) -> ClotureDetail:
    cloture = await _verrouiller(db, semestre_id)
    _exiger(cloture, EtatCloture.gele, "Seule une clôture gelée se valide.")
    candidats = await _candidats(db, semestre_id)
    laureats = [c for c in candidats if c.ecarte_le is None][:3]
    if not laureats:
        raise Refus("Aucun candidat retenu : il n'y a rien à valider.", 422)
    for place, candidat in enumerate(laureats, start=1):
        candidat.place = place
    cloture.etat, cloture.valide_le, cloture.valide_par = EtatCloture.valide, maintenant(), acces.utilisateur.id
    journaliser(
        db, "cloture_validee", acces.utilisateur, cible_type="semestre", cible_id=semestre_id, perimetre="national",
        details={"libelle": cloture.libelle, "laureats": _resume_laureats(laureats)}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await detail(db, semestre_id)


async def annuler_validation(db: AsyncSession, acces: Acces, semestre_id: UUID, motif: str, ip: str) -> ClotureDetail:
    motif = _motif(motif)
    cloture = await _verrouiller(db, semestre_id)
    _exiger(cloture, EtatCloture.valide, "Seule une clôture validée et non publiée peut revenir au gel.")
    for candidat in await _candidats(db, semestre_id):
        candidat.place = None
    cloture.etat, cloture.valide_le, cloture.valide_par = EtatCloture.gele, None, None
    journaliser(
        db, "validation_annulee", acces.utilisateur, cible_type="semestre", cible_id=semestre_id,
        perimetre="national", details={"libelle": cloture.libelle, "motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await detail(db, semestre_id)


async def publier(db: AsyncSession, acces: Acces, semestre_id: UUID, ip: str) -> ClotureDetail:
    """Publie le palmarès et notifie les lauréats, dans une seule transaction ; aucun point n'est écrit."""
    cloture = await _verrouiller(db, semestre_id)
    _exiger(cloture, EtatCloture.valide, "Seule une clôture validée se publie.")
    laureats = _top3(await _candidats(db, semestre_id), cloture.etat)
    if [c.place for c in laureats] != list(range(1, len(laureats) + 1)) or not laureats:
        # Un lauréat validé a disparu (compte supprimé) : publier laisserait une place vide sans le dire.
        raise Refus("Un lauréat validé n'existe plus : annule la validation pour recalculer le Top 3.", 422)
    comptes = await _identifiants(db, {c.utilisateur_id for c in laureats})
    inactifs = [
        c.pseudonyme
        for c in laureats
        if c.utilisateur_id not in comptes or comptes[c.utilisateur_id].statut is not StatutCompte.actif
    ]
    if inactifs:
        raise Refus(
            f"Compte inactif parmi les lauréats ({', '.join(inactifs)}) : annule la validation pour corriger le Top 3.",
            422,
        )
    cloture.etat, cloture.publie_le, cloture.publie_par = EtatCloture.publie, maintenant(), acces.utilisateur.id
    for candidat in laureats:
        distinction = DISTINCTIONS[candidat.place or 0]
        notifier(
            db, candidat.utilisateur_id, "distinction_semestre",
            f"Tu es {distinction} : {cloture.libelle}",
            f"Bravo ! Tu termines {_ordinal(candidat.place or 0)} du classement national avec {candidat.points} "
            "points. Ton nom de joueur rejoint le palmarès du Hall of Fame.",
            LIEN_PALMARES,
        )  # fmt: skip
    journaliser(
        db, "palmares_publie", acces.utilisateur, cible_type="semestre", cible_id=semestre_id, perimetre="national",
        details={"libelle": cloture.libelle, "laureats": _resume_laureats(laureats)}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await detail(db, semestre_id)


def _ordinal(place: int) -> str:
    return "1re" if place == 1 else f"{place}e"


# Public et espace ----------------------------------------------------------------------------------------------


async def palmares_public(db: AsyncSession) -> PalmaresPublic:
    lignes = (
        await db.execute(
            select(ClotureSemestre, CandidatCloture)
            .join(CandidatCloture, CandidatCloture.semestre_id == ClotureSemestre.semestre_id)
            .where(ClotureSemestre.etat == EtatCloture.publie, CandidatCloture.place.is_not(None))
            .order_by(ClotureSemestre.debut.desc(), CandidatCloture.place)
        )
    ).all()
    semestres: dict[UUID, SemestrePalmares] = {}
    for cloture, candidat in lignes:
        semestre = semestres.setdefault(
            cloture.semestre_id,
            SemestrePalmares(libelle=cloture.libelle, debut=cloture.debut, fin=cloture.fin, laureats=[]),
        )
        semestre.laureats.append(
            LaureatPublic(
                place=candidat.place or 0,
                distinction=DISTINCTIONS[candidat.place or 0],
                pseudonyme=candidat.pseudonyme,
                club=candidat.club,
                dre=candidat.dre,
                points=candidat.points,
            )
        )
    return PalmaresPublic(semestres=list(semestres.values()))


async def distinctions_de(db: AsyncSession, utilisateur_id: UUID) -> list[Distinction]:
    lignes = (
        await db.execute(
            select(ClotureSemestre.libelle, CandidatCloture.place, CandidatCloture.points)
            .join(ClotureSemestre, ClotureSemestre.semestre_id == CandidatCloture.semestre_id)
            .where(
                CandidatCloture.utilisateur_id == utilisateur_id,
                CandidatCloture.place.is_not(None),
                ClotureSemestre.etat == EtatCloture.publie,
            )
            .order_by(ClotureSemestre.debut.desc())
        )
    ).all()
    return [
        Distinction(semestre=libelle, place=place, distinction=DISTINCTIONS[place], points=points)
        for libelle, place, points in lignes
    ]
