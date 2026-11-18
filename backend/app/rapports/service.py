"""Rapports d'activité, rapports mensuels et bilans semestriels (spec 038) : dépôt, soumission et lecture.

Un rapport se rédige par son auteur seul ; une fois soumis, il a sa référence et le club le reçoit : les encadreurs
du club et, pour un rapport d'activité, le président. Pour tout autre, il n'existe pas (404). Rien n'est public.
"""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import Uuid, delete, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda import reponses as reponses_agenda
from app.clubs import activation
from app.clubs.espace import club_gere
from app.clubs.models import Club
from app.clubs.mon_club_sante import club_de_l_encadreur
from app.clubs.requetes import encadreurs_actifs
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.eleves.models import Eleve
from app.fichiers.stockage import StockageIndisponible, stockage
from app.moderation import service as moteur
from app.moderation.models import Contenu, DecisionModeration, EtatContenu, Photo, VersionContenu, VersionPhoto
from app.moderation.photos import effacer_du_brouillon, effacer_fichiers
from app.moderation.service import Introuvable
from app.notifications.service import notifier
from app.points.models import Semestre
from app.points.service import aujourd_hui
from app.rapports import types as types_rapport
from app.rapports.models import (
    PREFIXES,
    SEQUENCES,
    TYPES_CONTENU,
    LectureRapport,
    ModeleRapport,
    PieceRapport,
    Rapport,
    TypeActivite,
    VersionPiece,
)
from app.rapports.schemas import (
    SCHEMAS,
    ClubRapport,
    DecisionRapport,
    DocumentRapport,
    EtatRapport,
    Lecture,
    MesRapports,
    PhotoRapport,
    RapportDetail,
    RapportResume,
    manquants,
    titre_de,
)
from app.referentiel.models import Axe

ANCIENNETE_MAX = timedelta(days=365)
LIMITE_LISTE = 200
MOIS = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
    "décembre",
)  # fmt: skip
ETATS: dict[EtatContenu, EtatRapport] = {
    EtatContenu.brouillon: "brouillon",
    EtatContenu.en_attente: "soumis",
    EtatContenu.a_corriger: "a_corriger",
    EtatContenu.publie: "approuve",
    EtatContenu.refuse: "refuse",
}


# Qui dépose, qui lit -------------------------------------------------------------------------------------------


async def club_de_l_auteur(db: AsyncSession, utilisateur: Utilisateur) -> tuple[Club, bool]:
    """Le club au nom duquel cet utilisateur dépose, et s'il en est le président. 403 sinon."""
    if utilisateur.role is Role.encadreur:
        club = await club_de_l_encadreur(db, utilisateur)
        if not activation.est_en_service(club):
            raise Refus("Ton club n'est pas en service : il ne dépose pas de rapport pour l'instant.", 403)
        return club, False
    if utilisateur.role is Role.eleve:
        club = await club_gere(db, utilisateur)
        if club is not None:
            return club, True
    raise Refus("Les rapports sont déposés par les encadreurs vérifiés et le président d'un club en service.", 403)


async def _lecteur(db: AsyncSession, utilisateur: Utilisateur, contenu: Contenu, rapport: Rapport) -> str | None:
    """« auteur », « encadreur » ou « president » ; None si ce rapport n'existe pas pour lui."""
    if contenu.auteur_id == utilisateur.id:
        return "auteur"
    if rapport.reference is None:
        return None
    if utilisateur.role is Role.encadreur and utilisateur.id in set(
        (await db.scalars(encadreurs_actifs(rapport.club_id))).all()
    ):
        return "encadreur"
    if rapport.modele is ModeleRapport.activite and utilisateur.role is Role.eleve:
        president = await db.scalar(select(Club.president_id).where(Club.id == rapport.club_id))
        if president == utilisateur.id:
            return "president"
    return None


async def _charger(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, *, verrouiller: bool = False
) -> tuple[Contenu, Rapport, str]:
    contenu = await db.get(Contenu, contenu_id, with_for_update=verrouiller, populate_existing=verrouiller)
    rapport = await db.get(Rapport, contenu_id) if contenu is not None else None
    if contenu is None or rapport is None:
        raise Introuvable
    lecteur = await _lecteur(db, utilisateur, contenu, rapport)
    if lecteur is None:
        raise Introuvable
    return contenu, rapport, lecteur


async def _du_redacteur(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int | None
) -> tuple[Contenu, Rapport]:
    contenu, rapport, lecteur = await _charger(db, utilisateur, contenu_id, verrouiller=True)
    if lecteur != "auteur":
        raise Introuvable
    moteur.verifier_version(contenu, version)
    # Seul un brouillon ou un rapport à corriger se modifie : approuvé, refusé ou en examen, il est figé (spec 038).
    if contenu.etat not in (EtatContenu.brouillon, EtatContenu.a_corriger):
        raise Refus("Ce rapport est soumis, approuvé ou refusé : il ne se modifie plus.", 409)
    return contenu, rapport


# Présentation --------------------------------------------------------------------------------------------------


def _periode(rapport: Rapport, semestres: dict[UUID, str]) -> str | None:
    if rapport.date_activite is not None:
        return f"{rapport.date_activite:%d/%m/%Y}"
    if rapport.mois is not None:
        return f"{MOIS[rapport.mois.month - 1]} {rapport.mois.year}"
    if rapport.semestre_id is not None:
        return semestres.get(rapport.semestre_id)
    return None


async def _noms(db: AsyncSession, ids: set[UUID]) -> dict[UUID, str]:
    """Le nom d'un encadreur, le pseudonyme d'un élève : ce que le club voit déjà de son équipe."""
    if not ids:
        return {}
    lignes = await db.execute(
        select(Utilisateur.id, Utilisateur.prenom, Utilisateur.nom, Eleve.pseudonyme)
        .outerjoin(Eleve, Eleve.utilisateur_id == Utilisateur.id)
        .where(Utilisateur.id.in_(ids))
    )
    return {i: pseudonyme or f"{prenom} {nom}".strip() for i, prenom, nom, pseudonyme in lignes.all()}


async def _resumes(
    db: AsyncSession, utilisateur: Utilisateur, lignes: list[tuple[Contenu, Rapport]]
) -> list[RapportResume]:
    if not lignes:
        return []
    ids = [c.id for c, _ in lignes]
    clubs = {
        c.id: c.nom for c in (await db.scalars(select(Club).where(Club.id.in_({r.club_id for _, r in lignes})))).all()
    }
    semestres = {
        s.id: s.libelle
        for s in (
            await db.scalars(
                select(Semestre).where(Semestre.id.in_({r.semestre_id for _, r in lignes if r.semestre_id}))
            )
        ).all()
    }
    # Le titre de la version que chacun voit : de travail pour l'auteur, la dernière soumise pour le club.
    versions: dict[UUID, VersionContenu] = {}
    for version in (
        await db.scalars(
            select(VersionContenu).where(VersionContenu.contenu_id.in_(ids)).order_by(VersionContenu.numero)
        )
    ).all():
        contenu = next(c for c, _ in lignes if c.id == version.contenu_id)
        if contenu.auteur_id == utilisateur.id or version.soumise_le is not None:
            versions[version.contenu_id] = version
    # Les rapports approuvés comme doublons de chacun : le lien se voit des deux côtés.
    lies: dict[UUID, list[str]] = {}
    for original_id, reference in (
        await db.execute(
            select(Rapport.doublon_de_id, Rapport.reference)
            .where(Rapport.doublon_de_id.in_(ids))
            .order_by(Rapport.reference)
        )
    ).all():
        lies.setdefault(original_id, []).append(reference or "")
    references = {
        r.contenu_id: r.reference
        for r in (
            await db.scalars(
                select(Rapport).where(Rapport.contenu_id.in_({r.doublon_de_id for _, r in lignes if r.doublon_de_id}))
            )
        ).all()
    }
    equipes: dict[UUID, list[UUID]] = {}
    for club_id in {r.club_id for _, r in lignes}:
        equipes[club_id] = list((await db.scalars(encadreurs_actifs(club_id))).all())
    lu = {
        (l.contenu_id, l.utilisateur_id): l.consulte_le
        for l in (await db.scalars(select(LectureRapport).where(LectureRapport.contenu_id.in_(ids)))).all()
    }
    noms = await _noms(db, {c.auteur_id for c, _ in lignes} | {i for e in equipes.values() for i in e})
    resultats = []
    for contenu, rapport in lignes:
        version = versions.get(contenu.id)
        lectures = (
            [
                Lecture(nom=noms.get(i, ""), consulte_le=lu.get((contenu.id, i)))
                for i in equipes[rapport.club_id]
                if i != contenu.auteur_id
            ]
            if rapport.reference is not None
            else []
        )
        resultats.append(
            RapportResume(
                id=contenu.id,
                modele=rapport.modele,
                reference=rapport.reference,
                etat=ETATS.get(contenu.etat, "brouillon"),
                titre=titre_de(rapport.modele, version.donnees if version else {}),
                periode=_periode(rapport, semestres),
                club=ClubRapport(id=rapport.club_id, nom=clubs.get(rapport.club_id, "")),
                auteur=noms.get(contenu.auteur_id, ""),
                mien=contenu.auteur_id == utilisateur.id,
                soumis_le=contenu.soumis_le,
                modifie_le=contenu.modifie_le,
                points=rapport.points_auteur if contenu.auteur_id == utilisateur.id else None,
                doublon_de=references.get(rapport.doublon_de_id) if rapport.doublon_de_id else None,
                doublons=lies.get(contenu.id, []),
                lectures=lectures,
            )
        )
    return resultats


async def _version_lue(db: AsyncSession, contenu: Contenu, lecteur: str) -> VersionContenu:
    """L'auteur voit sa version de travail ; le club, la dernière version soumise."""
    if lecteur == "auteur":
        return await moteur.version_visible_auteur(db, contenu)
    version = await db.scalar(
        select(VersionContenu)
        .where(VersionContenu.contenu_id == contenu.id, VersionContenu.soumise_le.is_not(None))
        .order_by(VersionContenu.numero.desc())
        .limit(1)
    )
    assert version is not None
    return version


async def doublons_probables(db: AsyncSession, contenu: Contenu, rapport: Rapport) -> list[str]:
    """Les autres rapports du même club soumis ou approuvés sur la même activité (même date et même type), ou, pour
    un mensuel ou un bilan, du même auteur sur la même période."""
    requete = (
        select(Rapport.reference)
        .join(Contenu, Contenu.id == Rapport.contenu_id)
        .where(
            Rapport.club_id == rapport.club_id,
            Rapport.modele == rapport.modele,
            Rapport.contenu_id != rapport.contenu_id,
            Rapport.reference.is_not(None),
            Contenu.etat.in_((EtatContenu.en_attente, EtatContenu.a_corriger, EtatContenu.publie)),
        )
        .order_by(Rapport.reference)
    )
    if rapport.modele is ModeleRapport.activite:
        requete = requete.where(
            Rapport.date_activite == rapport.date_activite, Rapport.type_activite == rapport.type_activite
        )
    elif rapport.modele is ModeleRapport.mensuel:
        requete = requete.where(Rapport.mois == rapport.mois, Contenu.auteur_id == contenu.auteur_id)
    else:
        requete = requete.where(Rapport.semestre_id == rapport.semestre_id, Contenu.auteur_id == contenu.auteur_id)
    return [r for r in (await db.scalars(requete)).all() if r]


async def detail(
    db: AsyncSession, utilisateur: Utilisateur, contenu: Contenu, rapport: Rapport, lecteur: str
) -> RapportDetail:
    # Après une validation de transaction, les objets sont expirés : on les relit avant de les présenter.
    await db.refresh(contenu)
    await db.refresh(rapport)
    (resume,) = await _resumes(db, utilisateur, [(contenu, rapport)])
    version = await _version_lue(db, contenu, lecteur)
    photos = (
        await db.execute(
            select(VersionPhoto, Photo)
            .join(Photo, Photo.id == VersionPhoto.photo_id)
            .where(VersionPhoto.version_id == version.id, Photo.efface_le.is_(None))
            .order_by(VersionPhoto.ordre)
        )
    ).all()
    documents = (
        await db.scalars(
            select(PieceRapport)
            .join(VersionPiece, VersionPiece.piece_id == PieceRapport.id)
            .where(VersionPiece.version_id == version.id, PieceRapport.efface_le.is_(None))
            .order_by(VersionPiece.ordre)
        )
    ).all()
    decisions = (
        await db.execute(
            select(DecisionModeration, VersionContenu.numero)
            .join(VersionContenu, VersionContenu.id == DecisionModeration.version_id)
            .where(DecisionModeration.contenu_id == contenu.id)
            .order_by(DecisionModeration.decide_le)
        )
    ).all()
    return RapportDetail(
        **resume.model_dump(),
        version=contenu.version,
        donnees=dict(version.donnees),
        photos=[PhotoRapport(id=p.id, legende=vp.legende) for vp, p in photos],
        documents=[DocumentRapport(id=d.id, nom=d.nom, type=d.type.value, octets=d.octets) for d in documents],
        historique=[
            DecisionRapport(decision=d.decision.value, motif=d.motif, decide_le=d.decide_le, version=numero)
            for d, numero in decisions
        ],
        modifiable=lecteur == "auteur" and contenu.etat in (EtatContenu.brouillon, EtatContenu.a_corriger),
        doublons_probables=await doublons_probables(db, contenu, rapport) if rapport.reference else [],
        evenement=await reponses_agenda.resume_pour_rapport(db, rapport.evenement_id),
    )


# Liste et lecture ----------------------------------------------------------------------------------------------


async def mes_rapports(db: AsyncSession, utilisateur: Utilisateur) -> MesRapports:
    """Mes rapports, puis ceux du club que je reçois, du plus récent au plus ancien. Un auteur garde toujours la
    liste des siens, même si son club n'est plus en service ou qu'il l'a quitté (spec 038, 7)."""
    try:
        club, president = await club_de_l_auteur(db, utilisateur)
    except Refus:
        club, president = None, False
    visibles = Contenu.auteur_id == utilisateur.id
    if club is not None:
        du_club = (Rapport.club_id == club.id) & Rapport.reference.is_not(None)
        if president:
            du_club = du_club & (Rapport.modele == ModeleRapport.activite)
        visibles = visibles | du_club
    elif not await db.scalar(
        select(Contenu.id).join(Rapport, Rapport.contenu_id == Contenu.id).where(visibles).limit(1)
    ):
        # Ni club ni rapport : la page explique pourquoi.
        await club_de_l_auteur(db, utilisateur)
    lignes = (
        await db.execute(
            select(Contenu, Rapport)
            .join(Rapport, Rapport.contenu_id == Contenu.id)
            .where(visibles)
            .order_by(Contenu.modifie_le.desc())
            .limit(LIMITE_LISTE)
        )
    ).all()
    return MesRapports(
        rapports=await _resumes(db, utilisateur, [(c, r) for c, r in lignes]),
        club=ClubRapport(id=club.id, nom=club.nom) if club is not None else None,
        modeles=[] if club is None else [ModeleRapport.activite] if president else list(ModeleRapport),
    )


async def lire(db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID) -> RapportDetail:
    contenu, rapport, lecteur = await _charger(db, utilisateur, contenu_id)
    if lecteur == "encadreur":
        # « Consulté » : la première ouverture seulement.
        await db.execute(
            insert(LectureRapport).values(contenu_id=contenu.id, utilisateur_id=utilisateur.id).on_conflict_do_nothing()
        )
        await db.commit()
    return await detail(db, utilisateur, contenu, rapport, lecteur)


async def types_activite(db: AsyncSession) -> list[TypeActivite]:
    return list((await db.scalars(select(TypeActivite).where(TypeActivite.actif).order_by(TypeActivite.ordre))).all())


# Écriture ------------------------------------------------------------------------------------------------------


async def creer(db: AsyncSession, utilisateur: Utilisateur, modele: ModeleRapport) -> RapportDetail:
    club, president = await club_de_l_auteur(db, utilisateur)
    if president and modele is not ModeleRapport.activite:
        raise Refus("Le rapport mensuel et le bilan semestriel sont réservés aux encadreurs.", 403)
    contenu = await moteur.creer(db, utilisateur, TYPES_CONTENU[modele], {}, club_id=club.id)
    rapport = Rapport(contenu_id=contenu.id, modele=modele, club_id=club.id)
    db.add(rapport)
    await db.commit()
    return await detail(db, utilisateur, contenu, rapport, "auteur")


def _valider(modele: ModeleRapport, donnees: dict[str, Any]) -> dict[str, Any]:
    try:
        return SCHEMAS[modele].model_validate(donnees).model_dump(mode="json")
    except ValidationError as erreur:
        premiere = erreur.errors()[0]
        message = str(premiere.get("msg", "")).removeprefix("Value error, ")
        raise Refus(f"Champ « {'.'.join(str(x) for x in premiere['loc'])} » : {message}", 422) from None


async def _verifier_references(db: AsyncSession, champs: dict[str, Any], actuels: dict[str, Any]) -> None:
    """Un axe ou un type d'activité désactivé reste accepté s'il était déjà celui du rapport ; sinon, il doit être
    actif. Un semestre doit exister."""
    for cle, modele in (("axe_code", Axe), ("type_activite", TypeActivite)):
        valeur = champs.get(cle)
        if valeur and valeur != actuels.get(cle):
            element = await db.get(modele, valeur)
            if element is None or not element.actif:
                raise Refus(f"Champ « {cle} » : cette valeur n'existe pas ou n'est plus proposée.", 422)
    if champs.get("semestre_id") and await db.get(Semestre, UUID(str(champs["semestre_id"]))) is None:
        raise Refus("Champ « semestre_id » : ce semestre n'existe pas.", 422)


async def ouvrir_travail(db: AsyncSession, contenu: Contenu) -> VersionContenu:
    """La version de travail d'un rapport verrouillé. Une nouvelle version reprend les documents de la précédente,
    comme le moteur reprend les photos (spec 024)."""
    avant = contenu.version_travail_id
    precedente = await moteur.version_visible_auteur(db, contenu)
    travail = await moteur.ouvrir_travail(db, contenu)
    if travail.id != avant and precedente.id != travail.id:
        await db.execute(
            insert(VersionPiece).from_select(
                ["version_id", "piece_id", "ordre"],
                select(literal(travail.id, type_=Uuid), VersionPiece.piece_id, VersionPiece.ordre)
                .join(PieceRapport, PieceRapport.id == VersionPiece.piece_id)
                .where(VersionPiece.version_id == precedente.id, PieceRapport.efface_le.is_(None)),
            )
        )
    return travail


async def modifier(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int, donnees: dict[str, Any]
) -> RapportDetail:
    contenu, rapport = await _du_redacteur(db, utilisateur, contenu_id, version)
    champs = _valider(rapport.modele, donnees)
    actuels = (await moteur.version_visible_auteur(db, contenu)).donnees
    await _verifier_references(db, champs, actuels)
    travail = await ouvrir_travail(db, contenu)
    travail.donnees = champs
    rapport.date_activite = date.fromisoformat(champs["date_activite"]) if champs.get("date_activite") else None
    rapport.type_activite = champs.get("type_activite")
    rapport.mois = date.fromisoformat(champs["mois"]) if champs.get("mois") else None
    rapport.semestre_id = UUID(champs["semestre_id"]) if champs.get("semestre_id") else None
    evenement_id = UUID(champs["evenement_id"]) if champs.get("evenement_id") else None
    if evenement_id is not None and evenement_id != rapport.evenement_id:
        await reponses_agenda.lier_au_rapport(db, rapport.club_id, rapport.contenu_id, evenement_id)
    rapport.evenement_id = evenement_id
    try:
        await db.commit()
    except IntegrityError as erreur:
        await db.rollback()
        if "uq_rapport_evenement_id" not in str(erreur.orig):
            raise
        raise Refus("Cet événement est déjà documenté par un autre rapport.", 409) from None
    return await detail(db, utilisateur, contenu, rapport, "auteur")


async def supprimer(db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID) -> None:
    """Seul un brouillon jamais soumis se supprime, avec ses fichiers (après la validation de la transaction)."""
    contenu, rapport, lecteur = await _charger(db, utilisateur, contenu_id, verrouiller=True)
    if lecteur != "auteur":
        raise Introuvable
    if not await moteur.jamais_soumis(db, contenu):
        raise Refus("Seul un brouillon jamais soumis peut être supprimé.", 409)
    pieces = list((await db.scalars(select(PieceRapport).where(PieceRapport.contenu_id == contenu.id))).all())
    photos = await effacer_du_brouillon(db, contenu)
    await db.execute(delete(VersionPiece).where(VersionPiece.piece_id.in_([p.id for p in pieces])))
    await db.execute(delete(PieceRapport).where(PieceRapport.contenu_id == contenu.id))
    await db.delete(rapport)
    await moteur.supprimer(db, contenu)
    await db.commit()
    await effacer_fichiers(photos)
    await effacer_pieces(pieces)


async def effacer_pieces(pieces: list[PieceRapport]) -> None:
    disque = stockage()
    for piece in pieces:
        try:
            await disque.supprimer(piece.cle_stockage)
        except StockageIndisponible:  # pragma: no cover - la purge réessaiera
            continue


def _periode_close(modele: ModeleRapport, rapport: Rapport, fin_semestre: date | None) -> None:
    """Une activité a eu lieu (ni future, ni de plus d'un an) ; un mensuel se soumet dès le dernier jour du mois, un
    bilan dès le dernier jour du semestre."""
    jour = aujourd_hui()
    if modele is ModeleRapport.activite and rapport.date_activite is not None:
        if rapport.date_activite > jour:
            raise Refus(
                "La date de l'activité est dans le futur : un rapport se dépose une fois l'activité faite.", 422
            )
        if rapport.date_activite < jour - ANCIENNETE_MAX:
            raise Refus("L'activité date de plus d'un an : elle ne se déclare plus.", 422)
    if modele is ModeleRapport.mensuel and rapport.mois is not None:
        dernier_jour = (rapport.mois.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if jour < dernier_jour:
            raise Refus("Un rapport mensuel se soumet à partir du dernier jour du mois.", 422)
    if modele is ModeleRapport.bilan and fin_semestre is not None and jour < fin_semestre:
        raise Refus("Un bilan semestriel se soumet à partir du dernier jour du semestre.", 422)


async def soumettre(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int, ip: str
) -> RapportDetail:
    contenu, rapport = await _du_redacteur(db, utilisateur, contenu_id, version)
    # Le club doit être encore en service, et l'auteur encore autorisé à déposer pour lui.
    club, _ = await club_de_l_auteur(db, utilisateur)
    if club.id != rapport.club_id:
        raise Refus("Tu ne déposes plus de rapport pour ce club.", 403)
    travail = await moteur.version(db, contenu.version_travail_id)
    champs = SCHEMAS[rapport.modele].model_validate(travail.donnees if travail else {})
    absents = manquants(rapport.modele, champs)
    if absents:
        raise Refus(f"Il manque {', '.join(absents)}.", 422)
    semestre = await db.get(Semestre, rapport.semestre_id) if rapport.semestre_id else None
    _periode_close(rapport.modele, rapport, semestre.fin if semestre else None)
    if rapport.evenement_id is not None:
        # Spec 041 : l'événement lié doit être encore publié, du club, et lié à aucun autre rapport en vie.
        await reponses_agenda.lier_au_rapport(db, rapport.club_id, rapport.contenu_id, rapport.evenement_id)
    if rapport.reference is None:
        numero = await db.scalar(select(SEQUENCES[rapport.modele].next_value()))
        rapport.reference = f"{PREFIXES[rapport.modele]}-{aujourd_hui().year}-{numero:06d}"
    await moteur.soumettre(db, contenu, utilisateur, ip)
    titre = titre_de(rapport.modele, travail.donnees if travail else {})
    for destinataire in await types_rapport.destinataires(db, contenu):
        notifier(
            db, destinataire, "rapport_recu", f"Rapport {rapport.reference} reçu : {titre}"[:200], None,
            types_rapport.lien(contenu.id),
        )  # fmt: skip
    await db.commit()
    return await detail(db, utilisateur, contenu, rapport, "auteur")


async def pour_export(db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID) -> RapportDetail:
    """Le rapport tel que son lecteur le voit, s'il est approuvé : seul un rapport approuvé s'exporte."""
    contenu, rapport, lecteur = await _charger(db, utilisateur, contenu_id)
    if contenu.etat is not EtatContenu.publie:
        raise Refus("Seul un rapport approuvé s'exporte en PDF.", 409)
    return await detail(db, utilisateur, contenu, rapport, lecteur)
