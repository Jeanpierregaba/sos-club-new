"""Les trois modèles de rapport, déclarés au moteur de modération (ADR-0009, note de la spec 038).

Approuver un rapport ne le publie pas : pas d'adresse, pas de dépublication. Les points sont écrits par `crediter`,
avec des clés propres à chaque modèle, et un doublon ne crédite rien.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Club
from app.clubs.requetes import encadreurs_actifs
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.moderation.models import Contenu, EtatContenu
from app.moderation.types import TypeContenu, enregistrer
from app.points import service as points
from app.rapports.models import TYPES_CONTENU, ModeleRapport, Rapport
from app.rapports.schemas import SCHEMAS, titre_de

ENCADREUR = {
    ModeleRapport.activite: "encadreur.rapport_activite",
    ModeleRapport.mensuel: "encadreur.rapport_mensuel",
    ModeleRapport.bilan: "encadreur.bilan_semestriel",
}
CLUB = {ModeleRapport.activite: "club.rapport_activite", ModeleRapport.bilan: "club.bilan_semestriel"}
MAX_EN_ATTENTE = 20


def lien(contenu_id: UUID) -> str:
    return f"/rapports/{contenu_id}"


def cles(rapport: Rapport, auteur_id: UUID) -> tuple[str, str | None]:
    """Les clés du registre : un rapport d'activité crédite une fois ; un mensuel une fois par encadreur et par mois ;
    un bilan une fois par encadreur et par semestre, et une fois par club et par semestre pour le club."""
    if rapport.modele is ModeleRapport.activite:
        return f"rapport_activite:{rapport.contenu_id}", f"club.rapport_activite:{rapport.contenu_id}"
    if rapport.modele is ModeleRapport.mensuel:
        assert rapport.mois is not None
        return f"rapport_mensuel:{auteur_id}:{rapport.mois:%Y-%m}", None
    return (
        f"bilan_semestriel:{auteur_id}:{rapport.semestre_id}",
        f"club.bilan_semestriel:{rapport.club_id}:{rapport.semestre_id}",
    )


async def _crediter(db: AsyncSession, contenu: Contenu, valide_par: UUID) -> None:
    rapport = await db.get(Rapport, contenu.id)
    assert rapport is not None
    if rapport.doublon_de_id is not None:
        return
    auteur = await db.get(Utilisateur, contenu.auteur_id)
    assert auteur is not None
    cle_auteur, cle_club = cles(rapport, auteur.id)
    # Le président n'a pas de point personnel pour un rapport : le barème des élèves n'en prévoit pas.
    if auteur.role is Role.encadreur:
        ligne = await points.crediter(db, ENCADREUR[rapport.modele], auteur.id, cle_auteur, valide_par=valide_par)
        rapport.points_auteur = ligne.montant if ligne else None
    if cle_club is not None:
        ligne = await points.crediter_club(db, CLUB[rapport.modele], rapport.club_id, cle_club, valide_par=valide_par)
        rapport.points_club = ligne.montant if ligne else None


async def _lier_doublon(db: AsyncSession, contenu: Contenu, original_id: UUID) -> None:
    rapport = await db.get(Rapport, contenu.id)
    original = await db.get(Rapport, original_id)
    assert rapport is not None
    if (
        original is None
        or original_id == contenu.id
        or (original.club_id, original.modele)
        != (
            rapport.club_id,
            rapport.modele,
        )
    ):
        raise Refus("Un doublon se lie à un autre rapport du même club et du même modèle.", 422)
    if await db.scalar(select(Contenu.etat).where(Contenu.id == original_id)) is not EtatContenu.publie:
        raise Refus("Le rapport original doit déjà être approuvé.", 422)
    rapport.doublon_de_id = original_id


async def destinataires(db: AsyncSession, contenu: Contenu) -> list[UUID]:
    """Les encadreurs du club, et le président pour un rapport d'activité : ils reçoivent soumissions et
    décisions."""
    rapport = await db.get(Rapport, contenu.id)
    assert rapport is not None
    ids = list((await db.scalars(encadreurs_actifs(rapport.club_id))).all())
    if rapport.modele is ModeleRapport.activite:
        president = await db.scalar(select(Club.president_id).where(Club.id == rapport.club_id))
        if president is not None:
            ids.append(president)
    return [i for i in dict.fromkeys(ids) if i != contenu.auteur_id]


LIBELLES = {
    ModeleRapport.activite: "rapport d'activité",
    ModeleRapport.mensuel: "rapport mensuel",
    ModeleRapport.bilan: "bilan semestriel",
}

for _modele, _code in TYPES_CONTENU.items():
    enregistrer(
        TypeContenu(
            code=_code,
            libelle=LIBELLES[_modele],
            schema=SCHEMAS[_modele],
            actions_auteur={},
            titre=lambda donnees, modele=_modele: titre_de(modele, donnees),
            lien_auteur=lien,
            adresse=False,
            depublication=False,
            avis_approbation="est approuvé",
            crediter=_crediter,
            lier_doublon=_lier_doublon,
            destinataires=destinataires,
            max_en_attente=MAX_EN_ATTENTE,
        )
    )
