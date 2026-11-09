"""La progression dans le parcours Génie Imhotep (spec 029) : places réussies, badges et certificat.

`mettre_a_jour` délivre ce qui est dû à partir des places réussies. Elle est appelée à la fin d'une partie réussie
et à l'ouverture de « Ma certification » : un palier abaissé ou un compte réactivé sont ainsi rattrapés.

Aucun verrou n'est pris : chaque délivrance est une insertion qui ne fait rien si la ligne existe déjà (clés
primaires et index uniques), et le crédit de points ne suit qu'une insertion effective. Deux fins de partie
simultanées délivrent donc une seule fois ; elles insèrent dans le même ordre (badges par rang, puis certificat),
sans interblocage.
"""

import secrets
from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification import regles
from app.certification.models import BadgeObtenu, Certificat, EtatCertificat, PlaceReussie
from app.clubs.models import Adhesion, EtatAdhesion
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.notifications.service import notifier
from app.points import service as points
from app.points.bareme import BADGE_ELEVE, CERTIFICATION_ELEVE, CERTIFICATION_ENCADREUR
from app.quiz import horloge
from app.quiz.dependances import peut_jouer
from app.quiz.models import PLACES, Quiz, TentativeQuiz

# Base 32 de Crockford : ni I, ni L, ni O, ni U, pour un numéro qui se recopie sans erreur.
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
LIEN = "/certification/parcours"


def nouveau_numero() -> str:
    """60 bits aléatoires : un numéro ne se devine pas et ne s'énumère pas."""
    blocs = ("".join(secrets.choice(ALPHABET) for _ in range(4)) for _ in range(3))
    return "GI-" + "-".join(blocs)


async def places_reussies(db: AsyncSession, utilisateur_id: UUID) -> set[int]:
    return set(
        (await db.scalars(select(PlaceReussie.place).where(PlaceReussie.utilisateur_id == utilisateur_id))).all()
    )


async def place_ouverte(db: AsyncSession, utilisateur_id: UUID, place: int) -> bool:
    """Une place s'ouvre quand toutes les précédentes sont réussies."""
    precedentes = await db.scalar(
        select(func.count())
        .select_from(PlaceReussie)
        .where(PlaceReussie.utilisateur_id == utilisateur_id, PlaceReussie.place < place)
    )
    return precedentes == place - 1


async def club_beneficiaire(db: AsyncSession, utilisateur: Utilisateur) -> UUID | None:
    """Le club de l'élève affilié, pour ses points (R13) ; aucun pour un encadreur ou un élève sans club."""
    if utilisateur.role is not Role.eleve:
        return None
    return await db.scalar(
        select(Adhesion.club_id).where(Adhesion.eleve_id == utilisateur.id, Adhesion.etat == EtatAdhesion.active)
    )


async def enregistrer_reussite(db: AsyncSession, joueur: Utilisateur, quiz: Quiz, tentative: TentativeQuiz) -> None:
    """Une partie réussie sur un quiz publié du parcours : la place est acquise (une fois), puis ce qui est dû est
    délivré."""
    assert quiz.place is not None
    # L'ordre est vérifié au lancement, et de nouveau ici : un quiz déplacé pendant une partie ne fait pas sauter
    # de place.
    if not await place_ouverte(db, joueur.id, quiz.place):
        return
    await db.execute(
        insert(PlaceReussie)
        .values(
            utilisateur_id=joueur.id,
            place=quiz.place,
            quiz_id=quiz.id,
            tentative_id=tentative.id,
            reussie_le=tentative.terminee_le or horloge.maintenant(),
        )
        .on_conflict_do_nothing()
    )
    await mettre_a_jour(db, joueur)


async def mettre_a_jour(db: AsyncSession, joueur: Utilisateur) -> None:
    """Délivre les badges dont le palier est atteint et, les 12 places réussies, le certificat. Rien pour un compte
    qui ne peut pas jouer (suspendu, encadreur non vérifié) : il sera rattrapé à son retour."""
    if not await peut_jouer(db, joueur):
        return
    reussies = len(await places_reussies(db, joueur.id))
    if reussies == 0:
        return
    maintenant = horloge.maintenant()
    club_id = await club_beneficiaire(db, joueur)
    eleve = joueur.role is Role.eleve and joueur.statut is StatutCompte.actif

    en_cours = await regles.en_cours(db)
    obtenus = set((await db.scalars(select(BadgeObtenu.rang).where(BadgeObtenu.utilisateur_id == joueur.id))).all())
    for rang, (nom, palier) in enumerate(zip(en_cours.noms, en_cours.paliers, strict=True), start=1):
        if rang in obtenus or reussies < palier:
            continue
        badge = await db.scalar(
            insert(BadgeObtenu)
            .values(
                utilisateur_id=joueur.id,
                rang=rang,
                nom=nom,
                palier=palier,
                regles_version=en_cours.version,
                club_id=club_id,
                obtenu_le=maintenant,
            )
            .on_conflict_do_nothing()
            .returning(BadgeObtenu)
        )
        if badge is None:
            continue
        message = f"Tu as réussi {palier} quiz du parcours Génie Imhotep."
        if eleve:
            gain = await points.crediter(db, BADGE_ELEVE, joueur.id, f"badge:{rang}:{joueur.id}")
            if gain is not None:
                badge.mouvement_id = gain.id
                message += f" +{gain.montant} points."
        notifier(db, joueur.id, "certification_badge", f"Badge {nom} obtenu", message, LIEN)

    if reussies >= PLACES:
        await _delivrer_certificat(db, joueur, club_id, maintenant)
    await db.flush()


async def _delivrer_certificat(
    db: AsyncSession, joueur: Utilisateur, club_id: UUID | None, maintenant: datetime
) -> None:
    certificat = await db.scalar(
        insert(Certificat)
        .values(
            id=uuid7(),
            numero=nouveau_numero(),
            utilisateur_id=joueur.id,
            role=joueur.role.value,
            titulaire_prenom=joueur.prenom,
            titulaire_nom=joueur.nom,
            etat=EtatCertificat.valide,
            delivre_le=maintenant,
            club_id=club_id,
        )
        # Déjà délivré une fois (même révoqué depuis) : rien de plus. Seule une réémission en crée un autre.
        .on_conflict_do_nothing()
        .returning(Certificat)
    )
    if certificat is None:
        return
    action = CERTIFICATION_ELEVE if joueur.role is Role.eleve else CERTIFICATION_ENCADREUR
    gain = await points.crediter(db, action, joueur.id, f"certification:{joueur.id}")
    message = f"Ton certificat porte le numéro {certificat.numero}."
    if gain is not None:
        certificat.mouvement_id = gain.id
        message += f" +{gain.montant} points."
    notifier(db, joueur.id, "certification_certificat", "Certificat Génie Imhotep obtenu", message, LIEN)
