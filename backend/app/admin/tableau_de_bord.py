"""Tableau de bord national (CDC admin, 3). Chaque chiffre est calculé ici, au moment de la demande : aucun n'est
saisi ni codé en dur (CDC admin, 11)."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces
from app.admin.models import Collaborateur, Export, Invitation, JournalAudit
from app.admin.schemas import EvenementJournal, Indicateur, TableauDeBord
from app.certification.models import BadgeObtenu, Certificat, EtatCertificat
from app.clubs.activation import en_service
from app.clubs.models import Club
from app.clubs.verification import compter_en_attente as compter_clubs_en_attente
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.encadreurs.verification import compter_en_attente as compter_encadreurs_en_attente
from app.moderation.decisions import compter_en_attente as compter_contenus_en_attente
from app.moderation.models import Contenu, EtatContenu
from app.points.service import semestre_en_cours
from app.quiz.models import EtatTentative, TentativeQuiz
from app.referentiel.models import Dre, Etablissement, StatutEtablissement


async def calculer(db: AsyncSession, acces: Acces) -> TableauDeBord:
    maintenant = datetime.now(UTC)

    # Les joueurs sans compte (spec 031) ne sont pas des comptes.
    comptes = Utilisateur.role != Role.invite
    par_profil = {role: 0 for role in Role if role is not Role.invite} | dict(
        (await db.execute(select(Utilisateur.role, func.count()).where(comptes).group_by(Utilisateur.role))).all()
    )
    par_statut = {statut: 0 for statut in StatutCompte} | dict(
        (await db.execute(select(Utilisateur.statut, func.count()).where(comptes).group_by(Utilisateur.statut))).all()
    )

    debut = (maintenant - timedelta(days=29)).date()
    jour = func.date(func.timezone("UTC", Utilisateur.cree_le))
    lignes = await db.execute(
        select(jour, func.count())
        .where(Utilisateur.cree_le >= datetime.combine(debut, datetime.min.time(), UTC), comptes)
        .group_by(jour)
    )
    par_jour: dict[date, int] = dict(lignes.all())
    inscriptions = [
        ((debut + timedelta(days=i)).isoformat(), par_jour.get(debut + timedelta(days=i), 0)) for i in range(30)
    ]

    invitations_en_attente = await db.scalar(
        select(func.count())
        .select_from(Invitation)
        .join(Collaborateur, Collaborateur.id == Invitation.collaborateur_id)
        .where(
            Collaborateur.utilisateur_id.is_(None),
            Invitation.utilisee_le.is_(None),
            Invitation.annulee_le.is_(None),
            Invitation.expire_le > maintenant,
        )
    )
    debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    exports_du_mois = await db.scalar(select(func.count()).select_from(Export).where(Export.cree_le >= debut_mois))
    collaborateurs_actifs = await db.scalar(
        select(func.count())
        .select_from(Collaborateur)
        .join(Utilisateur, Utilisateur.id == Collaborateur.utilisateur_id)
        .where(Utilisateur.statut == StatutCompte.actif)
    )

    dre_actives = await db.scalar(select(func.count()).select_from(Dre).where(Dre.actif))
    etablissements_actifs = await db.scalar(
        select(func.count()).select_from(Etablissement).where(Etablissement.statut == StatutEtablissement.actif)
    )
    clubs_actifs = await db.scalar(select(func.count()).select_from(Club).where(en_service()))
    # Des chiffres nationaux, sans donnée personnelle : la file elle-même reste soumise à ses droits.
    contenus_en_attente = await db.scalar(
        select(func.count()).select_from(Contenu).where(Contenu.etat == EtatContenu.en_attente)
    )
    # Les parties de test des collaborateurs ne comptent pas.
    quiz_joues = await db.scalar(
        select(func.count())
        .select_from(TentativeQuiz)
        .where(TentativeQuiz.etat == EtatTentative.terminee, TentativeQuiz.essai.is_(False))
    )
    certifications = await db.scalar(
        select(func.count()).select_from(Certificat).where(Certificat.etat == EtatCertificat.valide)
    )
    badges = await db.scalar(select(func.count()).select_from(BadgeObtenu))

    indicateurs = [
        Indicateur(id="collaborateurs_actifs", libelle="Collaborateurs actifs", valeur=collaborateurs_actifs or 0),
        Indicateur(id="dre_actives", libelle="DRE actives", valeur=dre_actives or 0),
        Indicateur(id="etablissements_actifs", libelle="Établissements actifs", valeur=etablissements_actifs or 0),
        Indicateur(id="clubs_actifs", libelle="Clubs actifs", valeur=clubs_actifs or 0),
        Indicateur(id="invitations_en_attente", libelle="Invitations en attente", valeur=invitations_en_attente or 0),
        Indicateur(id="exports_du_mois", libelle="Exports ce mois-ci", valeur=exports_du_mois or 0),
        Indicateur(
            id="contenus_en_attente", libelle="Contenus en attente de validation", valeur=contenus_en_attente or 0
        ),
        Indicateur(id="quiz_joues", libelle="Quiz joués", valeur=quiz_joues or 0),
        Indicateur(id="certifications", libelle="Certificats valides", valeur=certifications or 0),
        Indicateur(id="badges", libelle="Badges délivrés", valeur=badges or 0),
    ]

    semestre = await semestre_en_cours(db)

    derniers = None
    # Le journal contient des données nominatives : réservé au périmètre national, comme sa page.
    if acces.a("journal", Action.consulter) and acces.national:
        evenements = await db.scalars(select(JournalAudit).order_by(JournalAudit.quand.desc()).limit(8))
        derniers = [EvenementJournal.model_validate(e) for e in evenements.all()]

    return TableauDeBord(
        calcule_le=maintenant,
        comptes_par_profil=par_profil,
        comptes_par_statut=par_statut,
        inscriptions_30_jours=inscriptions,
        indicateurs=indicateurs,
        semestre_en_cours=semestre.libelle if semestre else None,
        encadreurs_a_verifier=(
            await compter_encadreurs_en_attente(db, acces)
            if acces.a("encadreurs", Action.consulter) and not acces.double_auth_requise
            else None
        ),
        clubs_a_valider=(
            await compter_clubs_en_attente(db, acces)
            if acces.a("clubs", Action.consulter) and not acces.double_auth_requise
            else None
        ),
        contenus_a_moderer=(
            await compter_contenus_en_attente(db, acces)
            if acces.a("moderation", Action.consulter) and not acces.double_auth_requise
            else None
        ),
        derniers_evenements=derniers,
    )
