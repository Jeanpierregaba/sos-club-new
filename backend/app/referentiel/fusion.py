"""Doublons d'établissements et fusion (spec 042).

Les doublons probables se calculent à la demande (`doublons.paires`) sur les établissements actifs et proposés du
périmètre du collaborateur ; seules les paires que l'équipe a jugées distinctes sont stockées (`ecart_doublon`).
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.clubs.affiliations import DeuxClubs, clubs_a_fusionner, fusionner_clubs
from app.clubs.models import CLUB_VIVANT, Adhesion, Club, EtatAdhesion, EtatClub
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur
from app.referentiel.administration import (
    Introuvable,
    Refus,
    _dans_perimetre,
    _detail_etablissement,
    _ecrire,
    _etablissement_admin,
    _inscrits_par_etablissement,
    _verifier_version,
)
from app.referentiel.doublons import Fiche, paires
from app.referentiel.models import Dre, EcartDoublon, Etablissement, Iesg, StatutEtablissement
from app.referentiel.normalisation import normaliser
from app.referentiel.schemas import (
    ApercuFusion,
    ClubResume,
    Ecart,
    EtablissementAdmin,
    FicheDoublon,
    Fusion,
    PageDoublons,
    PaireProbable,
)

CANDIDATS = (StatutEtablissement.actif, StatutEtablissement.propose)


def _ordonner(a: UUID, b: UUID) -> tuple[UUID, UUID]:
    return (a, b) if a < b else (b, a)


async def clubs_vivants(db: AsyncSession, ids: Sequence[UUID]) -> dict[UUID, ClubResume]:
    """Le club vivant de chaque établissement et son nombre de membres actifs."""
    membres = (
        select(func.count()).where(Adhesion.club_id == Club.id, Adhesion.etat == EtatAdhesion.active).scalar_subquery()
    )
    lignes = (
        await db.execute(
            select(Club.etablissement_id, Club.id, Club.nom, Club.etat, membres).where(
                Club.etablissement_id.in_(ids), Club.etat.in_(CLUB_VIVANT)
            )
        )
    ).all()
    return {e: ClubResume(id=i, nom=n, etat=s.value, membres_actifs=m) for e, i, n, s, m in lignes}


async def _fiches(db: AsyncSession, ids: Sequence[UUID]) -> dict[UUID, FicheDoublon]:
    lignes = (
        await db.execute(
            select(Etablissement, Iesg, Dre)
            .join(Iesg, Iesg.id == Etablissement.iesg_id)
            .join(Dre, Dre.code == Iesg.dre_code)
            .where(Etablissement.id.in_(ids))
        )
    ).all()
    inscrits = await _inscrits_par_etablissement(db, ids)
    clubs = await clubs_vivants(db, ids)
    return {
        e.id: FicheDoublon(**_etablissement_admin(e, i, d, inscrits[e.id]).model_dump(), club=clubs.get(e.id))
        for e, i, d in lignes
    }


async def lister_doublons(db: AsyncSession, acces: Acces, *, dre_code: str | None, ecartees: bool) -> PageDoublons:
    perimetre = None if acces.national else acces.collaborateur.perimetre_dre
    requete = (
        select(Etablissement.id, Etablissement.nom, Etablissement.iesg_id, Iesg.dre_code)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .where(Etablissement.statut.in_(CANDIDATS))
    )
    if perimetre:
        requete = requete.where(Iesg.dre_code == perimetre)
    trouvees = paires(Fiche(*ligne) for ligne in (await db.execute(requete)).all())
    ecarts = {
        (a, b)
        for a, b in (await db.execute(select(EcartDoublon.etablissement_a_id, EcartDoublon.etablissement_b_id))).all()
    }

    par_dre: dict[str, int] = {}
    for paire in trouvees:
        if (paire.a.id, paire.b.id) not in ecarts:
            par_dre[paire.a.dre_code] = par_dre.get(paire.a.dre_code, 0) + 1

    if ecartees:
        raisons = {(p.a.id, p.b.id): p.raison for p in trouvees}
        retenues = [(a, b, raisons.get((a, b))) for a, b in sorted(ecarts)]
    else:
        retenues = [(p.a.id, p.b.id, p.raison) for p in trouvees if (p.a.id, p.b.id) not in ecarts]
    fiches = await _fiches(db, list({i for a, b, _ in retenues for i in (a, b)}))
    sortie = [
        PaireProbable(a=fiches[a], b=fiches[b], raison=raison, ecartee=ecartees)
        for a, b, raison in retenues
        if a in fiches and b in fiches
        and (perimetre is None or fiches[a].dre_code == perimetre)
        and (dre_code is None or fiches[a].dre_code == dre_code)
    ]  # fmt: skip
    if ecartees:
        sortie.sort(key=lambda p: (p.a.dre_code, p.a.iesg, p.a.nom))
    return PageDoublons(paires=sortie, par_dre=par_dre)


async def _paire(db: AsyncSession, acces: Acces, entree: Ecart) -> tuple[Etablissement, Etablissement]:
    if entree.a_id == entree.b_id:
        raise Refus("Choisis deux établissements différents.", 422)
    a_id, b_id = _ordonner(entree.a_id, entree.b_id)
    lignes = {
        e.id: (e, dre)
        for e, dre in (
            await db.execute(
                select(Etablissement, Iesg.dre_code)
                .join(Iesg, Iesg.id == Etablissement.iesg_id)
                .where(Etablissement.id.in_((a_id, b_id)))
            )
        ).all()
    }
    if len(lignes) != 2:
        raise Introuvable
    for _, dre in lignes.values():
        _dans_perimetre(acces, dre)
    return lignes[a_id][0], lignes[b_id][0]


def _details(a: Etablissement, b: Etablissement) -> dict[str, str]:
    return {"a_id": str(a.id), "a_nom": a.nom, "b_id": str(b.id), "b_nom": b.nom}


async def ecarter(db: AsyncSession, acces: Acces, entree: Ecart, ip: str) -> None:
    """« Pas un doublon » : la paire n'est plus proposée."""
    a, b = await _paire(db, acces, entree)
    ajoute = await db.scalar(
        insert(EcartDoublon)
        .values(etablissement_a_id=a.id, etablissement_b_id=b.id, ecarte_par=acces.utilisateur.id)
        .on_conflict_do_nothing()
        .returning(EcartDoublon.etablissement_a_id)
    )
    if ajoute is None:
        raise Refus("Cette paire est déjà écartée.", 409)
    dre = await db.scalar(select(Iesg.dre_code).where(Iesg.id == a.iesg_id))
    journaliser(
        db, "doublon_ecarte", acces.utilisateur, cible_type="etablissement", cible_id=a.id, perimetre=dre,
        details=_details(a, b), adresse_ip=ip,
    )  # fmt: skip
    await db.commit()


async def retablir(db: AsyncSession, acces: Acces, entree: Ecart, ip: str) -> None:
    """Annule un « Pas un doublon » : la paire est de nouveau proposée."""
    a, b = await _paire(db, acces, entree)
    retire = await db.scalar(
        delete(EcartDoublon)
        .where(EcartDoublon.etablissement_a_id == a.id, EcartDoublon.etablissement_b_id == b.id)
        .returning(EcartDoublon.etablissement_a_id)
    )
    if retire is None:
        raise Introuvable
    dre = await db.scalar(select(Iesg.dre_code).where(Iesg.id == a.iesg_id))
    journaliser(
        db, "doublon_retabli", acces.utilisateur, cible_type="etablissement", cible_id=a.id, perimetre=dre,
        details=_details(a, b), adresse_ip=ip,
    )  # fmt: skip
    await db.commit()


# Fusion -------------------------------------------------------------------------------------------------------


async def _deux(
    db: AsyncSession, acces: Acces, garde_id: UUID, absorbe_id: UUID
) -> tuple[Etablissement, Etablissement, str]:
    """Le gardé et l'absorbé, verrouillés dans l'ordre de leur identifiant (pas d'interblocage entre deux fusions
    croisées), après les vérifications qui ne dépendent pas des clubs."""
    if garde_id == absorbe_id:
        raise Refus("Choisis deux établissements différents.", 422)
    charges: dict[UUID, Etablissement] = {}
    for id_ in sorted((garde_id, absorbe_id)):
        etablissement = await db.get(Etablissement, id_, with_for_update=True, populate_existing=True)
        if etablissement is None:
            raise Introuvable
        charges[id_] = etablissement
    garde, absorbe = charges[garde_id], charges[absorbe_id]
    dre = dict(
        (await db.execute(select(Iesg.id, Iesg.dre_code).where(Iesg.id.in_((garde.iesg_id, absorbe.iesg_id))))).all()
    )
    _dans_perimetre(acces, dre[garde.iesg_id])
    _dans_perimetre(acces, dre[absorbe.iesg_id])
    if dre[garde.iesg_id] != dre[absorbe.iesg_id]:
        raise Refus("Les deux établissements doivent être dans la même DRE : déplace d'abord l'un des deux.", 422)
    if garde.statut is not StatutEtablissement.actif:
        raise Refus("L'établissement gardé doit être actif : inverse les rôles ou réactive-le.", 422)
    if absorbe.fusionne_dans_id is not None:
        raise Refus("Cet établissement a déjà été fusionné dans un autre.", 409)
    return garde, absorbe, dre[garde.iesg_id]


def _pluriel(nombre: int, mot: str) -> str:
    return f"{nombre} {mot}{'s' if nombre > 1 else ''}"


def _effet(garde: FicheDoublon, absorbe: FicheDoublon) -> str:
    inscrits = f"{_pluriel(absorbe.nb_eleves, 'élève')} et {_pluriel(absorbe.nb_encadreurs, 'encadreur')}"
    phrases = [f"{inscrits} rejoindront « {garde.nom} »."]
    club, autre = absorbe.club, garde.club
    if club is not None and club.etat != EtatClub.en_constitution:
        phrases.append(f"Le club « {club.nom} » rejoindra cet établissement, avec ses membres et ses points.")
        if autre is not None:
            phrases.append(
                f"Le club en constitution « {autre.nom} » sera clos et ses demandes en cours le rejoindront."
            )
    elif club is not None:
        cible = f"le club « {autre.nom} »" if autre is not None else "le club de l'établissement gardé"
        phrases.append(
            f"Le club en constitution « {club.nom} » sera clos et ses demandes en cours rejoindront {cible}."
        )
    phrases.append(f"« {absorbe.nom} » sera désactivé et renverra vers l'établissement gardé.")
    return " ".join(phrases)


async def apercu(db: AsyncSession, acces: Acces, garde_id: UUID, absorbe_id: UUID) -> ApercuFusion:
    """Ce que ferait la fusion, et pourquoi elle serait refusée : les mêmes vérifications, sans rien écrire."""
    try:
        await _deux(db, acces, garde_id, absorbe_id)
        refus = None
        try:
            await clubs_a_fusionner(db, absorbe_id, garde_id)
        except DeuxClubs as erreur:
            refus = str(erreur)
        fiches = await _fiches(db, [garde_id, absorbe_id])
    finally:
        await db.rollback()
    garde, absorbe = fiches[garde_id], fiches[absorbe_id]
    return ApercuFusion(garde=garde, absorbe=absorbe, effet=_effet(garde, absorbe), refus=refus)


def _etat(e: Etablissement) -> dict[str, Any]:
    return {
        "id": str(e.id), "nom": e.nom, "statut": e.statut.value, "iesg_id": str(e.iesg_id),
        "prefecture": e.prefecture, "ordre": e.ordre.value if e.ordre else None,
    }  # fmt: skip


async def fusionner(db: AsyncSession, acces: Acces, garde_id: UUID, entree: Fusion, ip: str) -> EtablissementAdmin:
    """Réunit l'absorbé dans le gardé (spec 042), tout ou rien : ses élèves et encadreurs rejoignent le gardé, son
    club le suit, il devient inactif et renvoie vers le gardé. Le journal garde les identifiants déplacés."""
    garde, absorbe, dre = await _deux(db, acces, garde_id, entree.absorbe_id)
    _verifier_version(garde, entree.version_garde)
    _verifier_version(absorbe, entree.version_absorbe)
    try:
        # Vérifié avant toute écriture : deux vrais clubs arrêtent la fusion.
        await clubs_a_fusionner(db, absorbe.id, garde.id)
    except DeuxClubs as erreur:
        await db.rollback()
        raise Refus(str(erreur), 409) from None
    nom = garde.nom if entree.nom == "garde" else absorbe.nom
    if normaliser(nom) != garde.nom_normalise:
        occupant = await db.scalar(
            select(Etablissement.nom).where(
                Etablissement.iesg_id == garde.iesg_id,
                Etablissement.nom_normalise == normaliser(nom),
                Etablissement.fusionne_dans_id.is_(None),
                Etablissement.id.not_in((garde.id, absorbe.id)),
            )
        )
        if occupant is not None:
            await db.rollback()
            raise Refus(f"« {occupant} » porte déjà ce nom dans l'IESG de l'établissement gardé.", 409)
    avant = {"garde": _etat(garde), "absorbe": _etat(absorbe)}

    eleves = (
        await db.scalars(
            # La version monte : un profil ouvert avant la fusion ne réécrit pas l'ancien établissement.
            update(Eleve)
            .where(Eleve.etablissement_id == absorbe.id)
            .values(etablissement_id=garde.id, version=Eleve.version + 1)
            .returning(Eleve.utilisateur_id)
        )
    ).all()
    encadreurs = (
        await db.scalars(
            update(Encadreur)
            .where(Encadreur.etablissement_id == absorbe.id)
            .values(etablissement_id=garde.id, version=Encadreur.version + 1)
            .returning(Encadreur.utilisateur_id)
        )
    ).all()

    # L'absorbé libère son nom avant que le gardé ne le reprenne.
    absorbe.statut = StatutEtablissement.inactif
    absorbe.fusionne_dans_id = garde.id
    await _ecrire(db)
    garde.nom, garde.nom_normalise = nom, normaliser(nom)
    garde.prefecture = garde.prefecture or absorbe.prefecture
    garde.ordre = garde.ordre or absorbe.ordre
    await _ecrire(db)
    clubs = await fusionner_clubs(db, absorbe.id, garde.id, acces.utilisateur, ip)

    journaliser(
        db, "etablissement_fusionne", acces.utilisateur, cible_type="etablissement", cible_id=absorbe.id,
        perimetre=dre,
        details={
            "garde_id": str(garde.id), "avant": avant,
            "apres": {"nom": garde.nom, "prefecture": garde.prefecture, "ordre": garde.ordre.value if garde.ordre else None},
            "eleves": sorted(str(i) for i in eleves), "encadreurs": sorted(str(i) for i in encadreurs), "clubs": clubs,
        },
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return await _detail_etablissement(db, garde.id)
