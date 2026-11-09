"""« Ma certification » (spec 029) : les 12 places, les badges et le certificat du joueur connecté."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bibliotheque.models import EtatRessource, Ressource
from app.certification import progression, regles
from app.certification.models import BadgeObtenu, Certificat, EtatCertificat
from app.certification.schemas import (
    BadgeParcours,
    CertificatJoueur,
    EtatPlace,
    Fascicule,
    MaCertification,
    PlaceParcours,
)
from app.clubs.models import Club
from app.comptes.models import Utilisateur
from app.quiz import horloge, parametres, partie
from app.quiz.models import PARCOURS_CERTIFICATION, PLACES, EtatQuiz, EtatTentative, Quiz, TentativeQuiz


async def ma_certification(db: AsyncSession, joueur: Utilisateur) -> MaCertification:
    # Une partie abandonnée est close avec son score, puis ce qui est dû est délivré (rattrapage).
    await partie.clore_abandonnees(db, joueur)
    await progression.mettre_a_jour(db, joueur)

    p = await parametres.en_cours(db, PARCOURS_CERTIFICATION)
    reussies = await progression.places_reussies(db, joueur.id)
    publies = {
        q.place: q
        for q in (
            await db.scalars(select(Quiz).where(Quiz.parcours == PARCOURS_CERTIFICATION, Quiz.etat == EtatQuiz.publie))
        ).all()
    }
    quiz_ids = [q.id for q in publies.values()]
    fascicules = await _fascicules(db, [q.ressource_id for q in publies.values() if q.ressource_id])
    les_siennes = (
        TentativeQuiz.joueur_id == joueur.id,
        TentativeQuiz.essai.is_(False),
        TentativeQuiz.quiz_id.in_(quiz_ids),
    )
    meilleurs = dict(
        (
            await db.execute(
                select(TentativeQuiz.quiz_id, func.max(TentativeQuiz.score))
                .where(*les_siennes, TentativeQuiz.etat == EtatTentative.terminee)
                .group_by(TentativeQuiz.quiz_id)
            )
        ).all()
    )
    du_jour = dict(
        (
            await db.execute(
                select(TentativeQuiz.quiz_id, func.count())
                .where(*les_siennes, TentativeQuiz.jour == horloge.maintenant().date())
                .group_by(TentativeQuiz.quiz_id)
            )
        ).all()
    )
    en_cours = dict(
        (
            await db.execute(
                select(TentativeQuiz.quiz_id, TentativeQuiz.id).where(
                    *les_siennes, TentativeQuiz.etat == EtatTentative.en_cours
                )
            )
        ).all()
    )

    places: list[PlaceParcours] = []
    ouverte = True
    for numero in range(1, PLACES + 1):
        quiz = publies.get(numero)
        etat: EtatPlace
        if numero in reussies:
            etat = "reussie"
        elif quiz is None:
            etat = "bientot"
        else:
            etat = "ouverte" if ouverte else "verrouillee"
        # Les places suivantes restent fermées dès qu'une place n'est pas réussie.
        ouverte = ouverte and numero in reussies
        places.append(
            PlaceParcours(
                place=numero,
                etat=etat,
                quiz_id=quiz.id if quiz else None,
                titre=quiz.titre if quiz else None,
                description=quiz.description if quiz else None,
                contenu_de_test=quiz.contenu_de_test if quiz else False,
                fascicule=fascicules.get(quiz.ressource_id) if quiz and quiz.ressource_id else None,
                meilleur_score=meilleurs.get(quiz.id) if quiz else None,
                tentatives_restantes=max(0, p.tentatives_par_jour - du_jour.get(quiz.id, 0)) if quiz else None,
                tentative_en_cours=en_cours.get(quiz.id) if quiz else None,
            )
        )

    return MaCertification(
        reussies=len(reussies),
        places=places,
        badges=await _badges(db, joueur.id),
        certificat=await _certificat(db, joueur.id),
        nb_questions=p.nb_questions,
        seuil=p.seuil,
    )


async def _fascicules(db: AsyncSession, ids: list[UUID]) -> dict[UUID, Fascicule]:
    """Seuls les fascicules encore publiés sont proposés."""
    if not ids:
        return {}
    lignes = await db.execute(
        select(Ressource.id, Ressource.titre).where(Ressource.id.in_(ids), Ressource.etat == EtatRessource.publie)
    )
    return {identifiant: Fascicule(id=identifiant, titre=titre) for identifiant, titre in lignes.all()}


async def _badges(db: AsyncSession, joueur_id: UUID) -> list[BadgeParcours]:
    """Les badges obtenus gardent leur nom et leur palier ; les autres suivent les règles en cours."""
    en_cours = await regles.en_cours(db)
    obtenus = {
        b.rang: b for b in (await db.scalars(select(BadgeObtenu).where(BadgeObtenu.utilisateur_id == joueur_id))).all()
    }
    resultat = []
    for rang, (nom, palier) in enumerate(zip(en_cours.noms, en_cours.paliers, strict=True), start=1):
        badge = obtenus.get(rang)
        resultat.append(
            BadgeParcours(rang=rang, nom=badge.nom, palier=badge.palier, obtenu_le=badge.obtenu_le)
            if badge
            else BadgeParcours(rang=rang, nom=nom, palier=palier, obtenu_le=None)
        )
    return resultat


async def certificat_valide(db: AsyncSession, utilisateur_id: UUID) -> Certificat | None:
    return await db.scalar(
        select(Certificat).where(Certificat.utilisateur_id == utilisateur_id, Certificat.etat == EtatCertificat.valide)
    )


async def _certificat(db: AsyncSession, joueur_id: UUID) -> CertificatJoueur | None:
    """Le certificat valide, sinon le dernier (révoqué) ; un certificat remplacé laisse la place au suivant."""
    certificat = await certificat_valide(db, joueur_id) or await db.scalar(
        select(Certificat)
        .where(Certificat.utilisateur_id == joueur_id, Certificat.etat == EtatCertificat.revoque)
        .order_by(Certificat.delivre_le.desc())
        .limit(1)
    )
    if certificat is None:
        return None
    club = await db.get(Club, certificat.club_id) if certificat.club_id else None
    return CertificatJoueur(
        numero=certificat.numero,
        etat=certificat.etat,
        delivre_le=certificat.delivre_le,
        club=club.nom if club else None,
        afficher_club=certificat.afficher_club,
    )


async def choisir_club(db: AsyncSession, joueur: Utilisateur, afficher: bool) -> CertificatJoueur | None:
    """Le titulaire choisit de montrer, ou non, son club à la vérification publique. None sans certificat valide."""
    certificat = await certificat_valide(db, joueur.id)
    if certificat is None:
        return None
    certificat.afficher_club = afficher
    await db.flush()
    return await _certificat(db, joueur.id)
