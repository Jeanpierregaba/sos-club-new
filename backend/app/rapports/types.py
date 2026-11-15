"""Les trois modèles de rapport, déclarés au moteur de modération (ADR-0009, note de la spec 038).

Approuver un rapport ne le publie pas : pas d'adresse, pas de dépublication. Les points sont écrits par `crediter`,
avec des clés propres à chaque modèle, et un doublon ne crédite rien.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Club
from app.clubs.requetes import encadreurs_actifs
from app.comptes.inscription import Refus
from app.comptes.models import Role, Utilisateur
from app.moderation.models import Contenu, EtatContenu, VersionContenu
from app.moderation.schemas import DocumentModeration, RapportModeration, RapportVoisin
from app.moderation.types import TypeContenu, enregistrer
from app.points import service as points
from app.points.models import LigneBareme, MouvementPoints, Semestre
from app.rapports.models import TYPES_CONTENU, ModeleRapport, PieceRapport, Rapport, VersionPiece
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


async def _complement_apercu(db: AsyncSession, contenu: Contenu, version_id: UUID) -> RapportModeration:
    """Ce que le modérateur voit en plus : la référence, la période, les documents de la version soumise, les
    doublons probables et les points que l'approbation créditerait au barème actuel."""
    from app.rapports import service  # import tardif : le service importe ce module

    rapport = await db.get(Rapport, contenu.id)
    assert rapport is not None
    auteur = await db.get(Utilisateur, contenu.auteur_id)
    semestres = {}
    if rapport.semestre_id is not None:
        semestre = await db.get(Semestre, rapport.semestre_id)
        semestres = {semestre.id: semestre.libelle} if semestre else {}
    references = await service.doublons_probables(db, contenu, rapport) if rapport.reference else []
    voisins = []
    for reference in references:
        autre = await db.scalar(select(Rapport).where(Rapport.reference == reference))
        if autre is not None:
            voisins.append(await _voisin(db, autre))
    original = await db.get(Rapport, rapport.doublon_de_id) if rapport.doublon_de_id else None
    documents = (
        await db.scalars(
            select(PieceRapport)
            .join(VersionPiece, VersionPiece.piece_id == PieceRapport.id)
            .where(VersionPiece.version_id == version_id, PieceRapport.efface_le.is_(None))
            .order_by(VersionPiece.ordre)
        )
    ).all()
    sans_points = rapport.doublon_de_id is not None or contenu.publie_le is not None
    montant_auteur = montant_club = None
    if not sans_points and auteur is not None and rapport.reference is not None:
        cle_auteur, cle_club = cles(rapport, auteur.id)
        # Ce qui serait vraiment crédité : rien si la clé est déjà prise (second mensuel, bilan du club déjà
        # crédité) ou si le club n'est plus en service.
        pris = set(
            (
                await db.scalars(
                    select(MouvementPoints.cle).where(MouvementPoints.cle.in_([cle_auteur, cle_club or ""]))
                )
            ).all()
        )
        if auteur.role is Role.encadreur and cle_auteur not in pris:
            montant_auteur = await db.scalar(
                select(LigneBareme.montant).where(LigneBareme.code == ENCADREUR[rapport.modele], LigneBareme.actif)
            )
        club = await db.get(Club, rapport.club_id)
        if cle_club is not None and cle_club not in pris and club is not None and activation.est_en_service(club):
            montant_club = await db.scalar(
                select(LigneBareme.montant).where(LigneBareme.code == CLUB[rapport.modele], LigneBareme.actif)
            )
    return RapportModeration(
        reference=rapport.reference,
        modele=rapport.modele.value,
        periode=service._periode(rapport, semestres),
        type_activite=rapport.type_activite,
        doublon_de=await _voisin(db, original) if original else None,
        doublons_probables=voisins,
        documents=[DocumentModeration(id=d.id, nom=d.nom, type=d.type.value, octets=d.octets) for d in documents],
        points_auteur=rapport.points_auteur if contenu.publie_le else montant_auteur,
        points_club=rapport.points_club if contenu.publie_le else montant_club,
    )


async def _voisin(db: AsyncSession, rapport: Rapport) -> RapportVoisin:
    contenu = await db.get(Contenu, rapport.contenu_id)
    assert contenu is not None
    version = await db.scalar(
        select(VersionContenu)
        .where(VersionContenu.contenu_id == contenu.id, VersionContenu.soumise_le.is_not(None))
        .order_by(VersionContenu.numero.desc())
        .limit(1)
    )
    return RapportVoisin(
        id=contenu.id,
        reference=rapport.reference or "",
        etat=contenu.etat,
        titre=titre_de(rapport.modele, version.donnees if version else {}),
    )


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
            complement_apercu=_complement_apercu,
            motif_min=10,
        )
    )
