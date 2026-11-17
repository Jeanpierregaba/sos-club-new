"""L'événement de club, déclaré au moteur de modération (ADR-0009, spec 041).

Il n'a pas d'adresse publique du moteur : sa page publique est `/agenda/<id>`, lue dans la table `evenement`, que le
crochet `a_chaque_approbation` remplit. Décider d'un événement exige aussi le droit « agenda : approuver ».
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agenda import service
from app.agenda.schemas import ChampsEvenement
from app.comptes.models import Role
from app.moderation.models import Contenu
from app.moderation.types import TypeContenu, enregistrer


async def destinataires(db: AsyncSession, contenu: Contenu) -> list[UUID]:
    """Les autres encadreurs du club et son président : ils reçoivent soumissions et décisions."""
    assert contenu.club_id is not None
    return [i for i in await service.gestionnaires(db, contenu.club_id) if i != contenu.auteur_id]


EVENEMENT = enregistrer(
    TypeContenu(
        code=service.TYPE,
        libelle="événement",
        schema=ChampsEvenement,
        # Le président est un élève : le barème des élèves ne prévoit rien pour un événement.
        actions_auteur={Role.encadreur: "encadreur.evenement"},
        titre=lambda donnees: str(donnees.get("titre") or "Événement sans titre"),
        lien_auteur=service.lien_club,
        adresse=False,
        avis_approbation="est publié dans l'agenda",
        destinataires=destinataires,
        motif_min=10,
        max_en_attente=10,
        domaine_droit="agenda",
        a_chaque_approbation=service.recopier,
        au_retrait=service.retirer_du_site,
    )
)
