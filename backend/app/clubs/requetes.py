"""Requêtes partagées des clubs (spec 020), sans dépendance vers les services : les modules de service
s'importent entre eux, celui-ci n'importe que des modèles."""

from uuid import UUID

from sqlalchemy import Select, select

from app.clubs.models import EtatRattachement, Rattachement
from app.comptes.models import StatutCompte, Utilisateur
from app.encadreurs.models import Encadreur, EtatVerification


def encadreurs_actifs(club_id: UUID) -> Select[tuple[UUID]]:
    """Les encadreurs qui peuvent agir pour ce club : rattachement actif, profil vérifié, compte non suspendu.
    Un encadreur suspendu garde son rattachement, mais ne compte plus (il ne peut pas confirmer une passation)."""
    return (
        select(Rattachement.encadreur_id)
        .join(Encadreur, Encadreur.utilisateur_id == Rattachement.encadreur_id)
        .join(Utilisateur, Utilisateur.id == Rattachement.encadreur_id)
        .where(
            Rattachement.club_id == club_id,
            Rattachement.etat == EtatRattachement.actif,
            Encadreur.etat == EtatVerification.actif,
            Utilisateur.statut == StatutCompte.actif,
        )
    )
