"""Événements de club : droits, brouillons, soumission, copie publique à l'approbation, annulation (spec 041).

Un événement de club est un contenu du moteur de modération (type `evenement`). Sa ligne `evenement` (même
identifiant) n'existe qu'à partir de la première approbation : c'est la copie publique de la version approuvée.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.agenda.models import Evenement, NiveauEvenement, Reponse, ReponseEvenement
from app.agenda.schemas import AgendaDuClub, ChampsEvenement, EvenementDuClub, a_lome
from app.clubs import activation
from app.clubs.espace import club_gere
from app.clubs.models import Adhesion, Club
from app.clubs.mon_club_sante import club_de_l_encadreur
from app.clubs.requetes import encadreurs_actifs
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.moderation import photos
from app.moderation import service as moteur
from app.moderation.models import Contenu, DecisionModeration, EtatContenu
from app.moderation.service import Introuvable
from app.notifications.service import notifier
from app.referentiel.models import Axe

TYPE = "evenement"
INTERDIT = "L'agenda du club est tenu par ses encadreurs vérifiés et son président."


def lien_club(evenement_id: UUID) -> str:
    return f"/mon-club/agenda/{evenement_id}"


def lien_public(evenement_id: UUID) -> str:
    return f"/agenda/{evenement_id}"


# Droits ------------------------------------------------------------------------------------------------------


async def club_du_redacteur(db: AsyncSession, utilisateur: Utilisateur) -> Club:
    """Le club dont cet utilisateur tient l'agenda : encadreur actif rattaché, ou président en place. 403 sinon."""
    club: Club | None = None
    if utilisateur.role is Role.encadreur:
        try:
            club = await club_de_l_encadreur(db, utilisateur)
        except Refus:
            club = None
    elif utilisateur.role is Role.eleve:
        club = await club_gere(db, utilisateur)
    if club is None:
        raise Refus(INTERDIT, 403)
    return club


def _en_service(club: Club) -> None:
    if not activation.est_en_service(club):
        raise Refus("Ton club n'est pas en service : il ne propose pas d'événement pour l'instant.", 403)


async def gestionnaires(db: AsyncSession, club_id: UUID) -> list[UUID]:
    """Les encadreurs actifs du club et son président : ils reçoivent soumissions, décisions et annulations."""
    ids = list((await db.scalars(encadreurs_actifs(club_id))).all())
    president = await db.scalar(select(Club.president_id).where(Club.id == club_id))
    if president is not None:
        ids.append(president)
    return list(dict.fromkeys(ids))


def membres_actifs(club_id: UUID) -> Any:
    """Les invités : les élèves dont l'adhésion au club est active et le compte actif."""
    return activation.eleves_comptes(club_id)


# Validation ---------------------------------------------------------------------------------------------------


def valider(donnees: dict[str, Any]) -> dict[str, Any]:
    try:
        return ChampsEvenement.model_validate(donnees).model_dump(mode="json")
    except ValidationError as erreur:
        premiere = erreur.errors()[0]
        message = str(premiere.get("msg", "")).removeprefix("Value error, ")
        lieu = ".".join(str(x) for x in premiere["loc"])
        raise Refus(f"Champ « {lieu} » : {message}" if lieu else message[:1].upper() + message[1:], 422) from None


async def verifier_axe(db: AsyncSession, champs: dict[str, Any], actuel: str | None = None) -> None:
    """Un axe désactivé reste accepté s'il était déjà celui de l'événement ; sinon il doit être actif."""
    code = champs.get("axe_code")
    if code and code != actuel:
        axe = await db.get(Axe, code)
        if axe is None or not axe.actif:
            raise Refus("Champ « axe_code » : cet axe n'existe pas ou n'est plus proposé.", 422)


# Lecture du club ----------------------------------------------------------------------------------------------


async def _participants(db: AsyncSession, evenement_id: UUID, club_id: UUID | None) -> int:
    requete = (
        select(func.count())
        .select_from(ReponseEvenement)
        .where(ReponseEvenement.evenement_id == evenement_id, ReponseEvenement.reponse == Reponse.participe)
    )
    if club_id is not None:
        requete = requete.where(ReponseEvenement.eleve_id.in_(membres_actifs(club_id)))
    return int(await db.scalar(requete) or 0)


async def _vue(db: AsyncSession, utilisateur: Utilisateur, contenu: Contenu) -> EvenementDuClub:
    version = await moteur.version_visible_auteur(db, contenu)
    auteur = await db.get(Utilisateur, contenu.auteur_id)
    evenement = await db.get(Evenement, contenu.id)
    motif = await db.scalar(
        select(DecisionModeration.motif)
        .where(DecisionModeration.contenu_id == contenu.id)
        .order_by(DecisionModeration.decide_le.desc(), DecisionModeration.id.desc())
        .limit(1)
    )
    annule = evenement is not None and evenement.annule_le is not None
    return EvenementDuClub(
        id=contenu.id,
        etat=contenu.etat,
        version=contenu.version,
        auteur=f"{auteur.prenom} {auteur.nom}" if auteur else "Compte supprimé",
        de_moi=contenu.auteur_id == utilisateur.id,
        champs=dict(version.donnees),
        publie=evenement is not None and evenement.publie,
        annule_le=evenement.annule_le if evenement else None,
        motif_annulation=evenement.motif_annulation if evenement else None,
        motif_decision=motif,
        participants=await _participants(db, contenu.id, contenu.club_id) if evenement else 0,
        peut_modifier=contenu.auteur_id == utilisateur.id and not annule and contenu.etat in moteur.MODIFIABLES,
    )


async def agenda_du_club(db: AsyncSession, utilisateur: Utilisateur) -> AgendaDuClub:
    club = await club_du_redacteur(db, utilisateur)
    contenus = (
        await db.scalars(
            select(Contenu).where(Contenu.type == TYPE, Contenu.club_id == club.id).order_by(Contenu.cree_le.desc())
        )
    ).all()
    # Un brouillon jamais publié reste privé à son auteur ; un événement publié en cours de révision reste visible.
    visibles = [
        c
        for c in contenus
        if c.etat is not EtatContenu.brouillon or c.auteur_id == utilisateur.id or c.publie_le is not None
    ]
    return AgendaDuClub(club=club.nom, evenements=[await _vue(db, utilisateur, c) for c in visibles])


async def _du_club(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, *, verrouiller: bool = False
) -> Contenu:
    club = await club_du_redacteur(db, utilisateur)
    contenu = await db.get(Contenu, contenu_id, with_for_update=verrouiller, populate_existing=verrouiller)
    if contenu is None or contenu.type != TYPE or contenu.club_id != club.id:
        raise Introuvable
    if contenu.etat is EtatContenu.brouillon and contenu.auteur_id != utilisateur.id and contenu.publie_le is None:
        raise Introuvable
    return contenu


async def evenement_du_club(db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID) -> EvenementDuClub:
    return await _vue(db, utilisateur, await _du_club(db, utilisateur, contenu_id))


# Brouillons et soumission ------------------------------------------------------------------------------------


async def creer(db: AsyncSession, utilisateur: Utilisateur, donnees: dict[str, Any]) -> EvenementDuClub:
    club = await club_du_redacteur(db, utilisateur)
    _en_service(club)
    champs = valider(donnees)
    await verifier_axe(db, champs)
    contenu = await moteur.creer(db, utilisateur, TYPE, champs, club_id=club.id)
    await db.commit()
    return await _vue(db, utilisateur, contenu)


async def _de_l_auteur(db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int) -> Contenu:
    """L'événement de cet auteur, encore habilité pour son club, verrouillé, version contrôlée."""
    club = await club_du_redacteur(db, utilisateur)
    contenu = await moteur.contenu_de(db, utilisateur, contenu_id, TYPE, verrouiller=True)
    if contenu.club_id != club.id:
        raise Refus("Tu ne tiens plus l'agenda de ce club.", 403)
    moteur.verifier_version(contenu, version)
    evenement = await db.get(Evenement, contenu.id)
    if evenement is not None and evenement.annule_le is not None:
        raise Refus("Cet événement est annulé : propose-en un nouveau.", 409)
    return contenu


async def modifier(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int, donnees: dict[str, Any]
) -> EvenementDuClub:
    contenu = await _de_l_auteur(db, utilisateur, contenu_id, version)
    champs = valider(donnees)
    actuels = (await moteur.version_visible_auteur(db, contenu)).donnees
    await verifier_axe(db, champs, actuels.get("axe_code"))
    await moteur.modifier(db, contenu, champs)
    await db.commit()
    return await _vue(db, utilisateur, contenu)


async def soumettre(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int, ip: str
) -> EvenementDuClub:
    contenu = await _de_l_auteur(db, utilisateur, contenu_id, version)
    club = await db.get(Club, contenu.club_id)
    assert club is not None
    _en_service(club)
    travail = await moteur.version(db, contenu.version_travail_id)
    champs = ChampsEvenement.model_validate(travail.donnees if travail else {})
    if a_lome(champs.debut) <= datetime.now(UTC):
        raise Refus("Cet événement commence dans le passé : change sa date avant de le soumettre.", 422)
    if not champs.axe_code:
        raise Refus("Champ « axe_code » : choisis l'axe de l'événement.", 422)
    await moteur.soumettre(db, contenu, utilisateur, ip)
    for destinataire in await gestionnaires(db, club.id):
        if destinataire != utilisateur.id:
            notifier(
                db, destinataire, "evenement_soumis", f"Événement proposé : {champs.titre}"[:200],
                "Il attend la validation de l'équipe nationale.", lien_club(contenu.id),
            )  # fmt: skip
    await db.commit()
    return await _vue(db, utilisateur, contenu)


async def retirer(
    db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int, ip: str
) -> EvenementDuClub:
    """L'auteur reprend un événement en attente pour le modifier."""
    contenu = await _de_l_auteur(db, utilisateur, contenu_id, version)
    await moteur.retirer(db, contenu, utilisateur, ip)
    await db.commit()
    return await _vue(db, utilisateur, contenu)


async def supprimer(db: AsyncSession, utilisateur: Utilisateur, contenu_id: UUID, version: int) -> None:
    contenu = await _de_l_auteur(db, utilisateur, contenu_id, version)
    if not await moteur.jamais_soumis(db, contenu):
        raise Refus("Seul un brouillon jamais soumis peut être supprimé.", 409)
    a_effacer = await photos.effacer_du_brouillon(db, contenu)
    await moteur.supprimer(db, contenu)
    await db.commit()
    # Les fichiers après la validation : jamais un fichier effacé pour une suppression annulée.
    await photos.effacer_fichiers(a_effacer)


# Approbation (crochets du moteur) ---------------------------------------------------------------------------


async def recopier(db: AsyncSession, contenu: Contenu, donnees: dict[str, Any], premiere: bool) -> None:
    """À chaque approbation : la version approuvée devient la copie publique. La première invite les membres ;
    une révision qui change la date ou le lieu prévient les invités qui n'ont pas décliné."""
    assert contenu.club_id is not None
    champs = ChampsEvenement.model_validate(donnees)
    evenement = await db.get(Evenement, contenu.id, with_for_update=True)
    if evenement is not None and evenement.annule_le is not None:
        raise Refus("Cet événement a été annulé : sa modification ne peut plus être publiée. Refuse-la.", 409)
    if a_lome(champs.debut) <= datetime.now(UTC):
        raise Refus(
            "Cet événement commence dans le passé : demande une correction de sa date plutôt que de l'approuver.", 409
        )
    avant = (evenement.debut, evenement.fin, evenement.lieu, evenement.lien) if evenement else None
    if evenement is None:
        club = await db.get(Club, contenu.club_id)
        evenement = Evenement(
            id=contenu.id,
            contenu_id=contenu.id,
            niveau=NiveauEvenement.club,
            club_id=contenu.club_id,
            dre_code=contenu.dre_code,
            cree_par=contenu.auteur_id,
        )
        db.add(evenement)
        assert club is not None
    copier(evenement, champs)
    evenement.publie = True
    await db.flush()
    membres = list((await db.scalars(membres_actifs(contenu.club_id))).all())
    if premiere:
        for membre in membres:
            notifier(
                db, membre, "evenement_invitation", f"Invitation : {champs.titre}"[:200],
                "Ton club t'invite. Dis-nous si tu participes.", lien_public(evenement.id),
            )  # fmt: skip
        return
    apres = (evenement.debut, evenement.fin, evenement.lieu, evenement.lien)
    if avant is not None and avant != apres:
        declines = set(
            (
                await db.scalars(
                    select(ReponseEvenement.eleve_id).where(
                        ReponseEvenement.evenement_id == evenement.id, ReponseEvenement.reponse == Reponse.non
                    )
                )
            ).all()
        )
        for membre in membres:
            if membre not in declines:
                notifier(
                    db, membre, "evenement_modifie", f"Changement : {champs.titre}"[:200],
                    "La date, l'heure ou le lieu de cet événement a changé.", lien_public(evenement.id),
                )  # fmt: skip


def copier(evenement: Evenement, champs: ChampsEvenement) -> None:
    evenement.type = champs.type
    evenement.axe_code = champs.axe_code
    evenement.titre = champs.titre
    evenement.objectif = champs.objectif
    evenement.description = champs.description
    evenement.lieu = None if champs.en_ligne else champs.lieu
    evenement.en_ligne = champs.en_ligne
    evenement.lien = champs.lien if champs.en_ligne else None
    evenement.public_vise = champs.public_vise
    evenement.debut = a_lome(champs.debut)
    evenement.fin = a_lome(champs.fin)
    evenement.places = champs.places
    evenement.modifie_le = datetime.now(UTC)


async def retirer_du_site(db: AsyncSession, contenu: Contenu) -> None:
    evenement = await db.get(Evenement, contenu.id, with_for_update=True)
    if evenement is not None:
        evenement.publie = False


# Annulation --------------------------------------------------------------------------------------------------


async def annuler_evenement(
    db: AsyncSession, evenement: Evenement, par: Utilisateur, motif: str, ip: str, *, perimetre: str
) -> None:
    """Annule un événement publié à venir ou en cours : il reste visible, marqué « Annulé », et ses invités sont
    prévenus. À appeler sur un événement verrouillé."""
    if not evenement.publie:
        raise Refus("Cet événement n'est pas publié.", 409)
    if evenement.annule_le is not None:
        raise Refus("Cet événement est déjà annulé.", 409)
    if evenement.fin <= datetime.now(UTC):
        raise Refus("Cet événement est terminé : il ne s'annule plus.", 409)
    evenement.annule_le = datetime.now(UTC)
    evenement.annule_par = par.id
    evenement.motif_annulation = motif
    if evenement.club_id is not None:
        declines = select(ReponseEvenement.eleve_id).where(
            ReponseEvenement.evenement_id == evenement.id, ReponseEvenement.reponse == Reponse.non
        )
        invites = await db.scalars(membres_actifs(evenement.club_id).where(Adhesion.eleve_id.not_in(declines)))
        for membre in invites.all():
            notifier(
                db, membre, "evenement_annule", f"Annulé : {evenement.titre}"[:200], motif, lien_public(evenement.id)
            )
    journaliser(
        db, "evenement_annule", par, cible_type="evenement", cible_id=evenement.id, perimetre=perimetre,
        details={"niveau": evenement.niveau.value}, adresse_ip=ip,
    )  # fmt: skip


async def annuler_du_club(
    db: AsyncSession, utilisateur: Utilisateur, evenement_id: UUID, motif: str, ip: str
) -> EvenementDuClub:
    contenu = await _du_club(db, utilisateur, evenement_id, verrouiller=True)
    evenement = await db.get(Evenement, contenu.id, with_for_update=True, populate_existing=True)
    if evenement is None:
        raise Refus("Cet événement n'est pas publié.", 409)
    await annuler_evenement(db, evenement, utilisateur, motif, ip, perimetre=evenement.dre_code or "national")
    assert contenu.club_id is not None
    for gestionnaire in await gestionnaires(db, contenu.club_id):
        if gestionnaire != utilisateur.id:
            notifier(
                db, gestionnaire, "evenement_annule", f"Annulé : {evenement.titre}"[:200], motif,
                lien_club(evenement.id),
            )  # fmt: skip
    await db.commit()
    return await _vue(db, utilisateur, contenu)
