"""Clubs : espace de l'élève et du président sous /clubs, lecture publique, suivi sous /admin/clubs.

Depuis la spec 033, un club naît et s'active seul (ADR-0011) : plus de demande de création ni de rattachement manuel ;
l'affiliation d'un élève est confirmée par un encadreur du club ou par l'équipe."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.catalogue import Action
from app.admin.dependances import Acces, adresse_ip, exiger_permission
from app.articles.router import routes_de_redaction
from app.clubs import adhesions, espace, membres_admin, rattachements, service, suivi, verification
from app.clubs import affiliations as affiliations_
from app.clubs import carte as carte_
from app.clubs import mon_club_sante as mon_club_sante_
from app.clubs.schemas import (
    ActivationEntree,
    AffiliationsDuClub,
    Carte,
    ClubFiche,
    ClubPodium,
    ClubPublic,
    DecisionEntree,
    DecisionSignalementEntree,
    DesistementEntree,
    EspaceClub,
    FicheSuivi,
    FileAffiliations,
    FileDesistements,
    FilePassations,
    LotEntree,
    LotRefusEntree,
    MembresDuClub,
    MonClub,
    MonClubSante,
    PageSuivi,
    Passation,
    PassationAConfirmer,
    PassationApercu,
    PassationEntree,
    PresidentEntree,
    PropositionFiche,
    PropositionFicheEntree,
    RefusDemandeEntree,
    RefusEntree,
    RejetSignalementEntree,
    ResultatLot,
    Seuils,
    SignalementResume,
    TerrainEntree,
)
from app.comptes.dependances import utilisateur_courant
from app.comptes.inscription import Refus
from app.comptes.models import Utilisateur
from app.comptes.service import cle_adresse
from app.db import get_session
from app.referentiel.regions import RegionScolaire

Base = Annotated[AsyncSession, Depends(get_session)]
Connecte = Annotated[Utilisateur, Depends(utilisateur_courant)]

router = APIRouter(prefix="/clubs", tags=["clubs"])
router_admin = APIRouter(prefix="/admin/clubs", tags=["admin"])

Lecteur = Annotated[Acces, Depends(exiger_permission("clubs", Action.consulter))]
Decideur = Annotated[Acces, Depends(exiger_permission("clubs", Action.approuver))]


@contextmanager
def _traduire_refus() -> Iterator[None]:
    try:
        yield
    except verification.Introuvable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce club est introuvable.") from None
    except Refus as refus:
        raise HTTPException(refus.statut, str(refus)) from None
    except service.PasUnEleve:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cet espace est réservé aux élèves.") from None


def _adresse(request: Request) -> str:
    return cle_adresse(request.client.host if request.client else None)


# Élève ------------------------------------------------------------------------------------------------------


@router.get("/moi")
async def mon_club(utilisateur: Connecte, db: Base) -> MonClub:
    with _traduire_refus():
        return await service.mon_club(db, utilisateur)


@router.post("/moi/affiliation", status_code=status.HTTP_201_CREATED)
async def redemander_affiliation(request: Request, utilisateur: Connecte, db: Base) -> MonClub:
    """Après un refus ou un retrait, l'élève redemande son affiliation : elle repart « à confirmer » (spec 033)."""
    with _traduire_refus():
        await affiliations_.redemander(db, utilisateur, _adresse(request))
        return await service.mon_club(db, utilisateur)


@router.post("/moi/passation", status_code=status.HTTP_201_CREATED)
async def proposer_passation(
    entree: PassationEntree, request: Request, utilisateur: Connecte, db: Base
) -> PassationApercu:
    with _traduire_refus():
        return await service.proposer_passation(db, utilisateur, entree, _adresse(request))


@router.post("/moi/passation/annuler")
async def annuler_passation(request: Request, utilisateur: Connecte, db: Base) -> PassationApercu:
    with _traduire_refus():
        return await service.annuler_passation(db, utilisateur, _adresse(request))


# « Mon Club Santé » de l'encadreur (spec 033) : déclaré avant les routes /{club_id}/…


@router.get("/mon-club-sante")
async def mon_club_sante(utilisateur: Connecte, db: Base) -> MonClubSante:
    with _traduire_refus():
        return await mon_club_sante_.fiche(db, utilisateur)


@router.get("/mon-club-sante/affiliations")
async def affiliations_du_club(utilisateur: Connecte, db: Base) -> AffiliationsDuClub:
    with _traduire_refus():
        return await mon_club_sante_.affiliations(db, utilisateur)


@router.post("/mon-club-sante/affiliations/{affiliation_id}/confirmer")
async def confirmer_affiliation(
    affiliation_id: UUID, entree: DecisionEntree, request: Request, utilisateur: Connecte, db: Base
) -> AffiliationsDuClub:
    with _traduire_refus():
        return await mon_club_sante_.confirmer(db, utilisateur, affiliation_id, entree.version, _adresse(request))


@router.post("/mon-club-sante/affiliations/{affiliation_id}/refuser")
async def refuser_affiliation(
    affiliation_id: UUID, entree: RefusDemandeEntree, request: Request, utilisateur: Connecte, db: Base
) -> AffiliationsDuClub:
    with _traduire_refus():
        return await mon_club_sante_.refuser(
            db, utilisateur, affiliation_id, entree.motif, entree.version, _adresse(request)
        )


@router.post("/mon-club-sante/affiliations/{affiliation_id}/retirer")
async def retirer_affiliation(
    affiliation_id: UUID, entree: RefusDemandeEntree, request: Request, utilisateur: Connecte, db: Base
) -> AffiliationsDuClub:
    with _traduire_refus():
        return await mon_club_sante_.retirer(
            db, utilisateur, affiliation_id, entree.motif, entree.version, _adresse(request)
        )


@router.post("/mon-club-sante/desistements", status_code=status.HTTP_201_CREATED)
async def signaler_desistement(
    entree: DesistementEntree, request: Request, utilisateur: Connecte, db: Base
) -> SignalementResume:
    with _traduire_refus():
        return await mon_club_sante_.signaler_desistement(
            db, utilisateur, entree.encadreur_id, entree.motif, _adresse(request)
        )


@router.post("/mon-club-sante/president")
async def proposer_president(
    entree: PresidentEntree, request: Request, utilisateur: Connecte, db: Base
) -> MonClubSante:
    with _traduire_refus():
        return await mon_club_sante_.proposer_president(db, utilisateur, entree.affiliation_id, _adresse(request))


# Espace du président (spec 026) : « Mon club », propositions de fiche ; les actualités sont dans `router_actualites`.


@router.post("/moi/fiche", status_code=status.HTTP_201_CREATED)
async def proposer_fiche(
    entree: PropositionFicheEntree, request: Request, president: espace.President, db: Base
) -> PropositionFiche:
    with _traduire_refus():
        return await espace.proposer_fiche(db, president, entree.description, entree.axes, adresse_ip(request))


@router.delete("/moi/fiche/{contenu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def retirer_fiche(contenu_id: UUID, request: Request, president: espace.President, db: Base) -> Response:
    with _traduire_refus():
        await espace.retirer_fiche(db, president, contenu_id, adresse_ip(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{club_id}/espace")
async def espace_du_club(club_id: UUID, utilisateur: Connecte, db: Base) -> EspaceClub:
    with _traduire_refus():
        return await espace.espace(db, utilisateur, club_id)


@router.get("/{club_id}/membres")
async def membres(club_id: UUID, utilisateur: Connecte, db: Base) -> MembresDuClub:
    """Les membres du club : visibles du président, des membres et des encadreurs rattachés seulement."""
    with _traduire_refus():
        return await adhesions.membres_du_club(db, utilisateur, club_id)


# Passation confirmée par un encadreur rattaché (Q19, spec 020) ------------------------------------------------


@router.post("/{club_id}/passation/confirmer")
async def confirmer_passation(
    club_id: UUID, entree: DecisionEntree, request: Request, utilisateur: Connecte, db: Base
) -> PassationAConfirmer:
    with _traduire_refus():
        return await rattachements.confirmer_passation(db, utilisateur, club_id, entree.version, _adresse(request))


@router.post("/{club_id}/passation/refuser")
async def refuser_passation_encadreur(
    club_id: UUID, entree: RefusDemandeEntree, request: Request, utilisateur: Connecte, db: Base
) -> PassationAConfirmer:
    with _traduire_refus():
        return await rattachements.refuser_passation(
            db, utilisateur, club_id, entree.motif, entree.version, _adresse(request)
        )


# Public -----------------------------------------------------------------------------------------------------


@router.get("")
async def lister_clubs(db: Base) -> list[ClubPublic]:
    return await service.clubs_publics(db)


@router.get("/carte")
async def carte_des_clubs(db: Base) -> Carte:
    """La carte nationale : trois chiffres réels et l'arbre région → DRE → inspection → établissement (spec 033)."""
    return await carte_.carte(db)


@router.get("/podium")
async def podium_des_clubs(db: Base) -> list[ClubPodium]:
    """Les trois clubs qui ont le plus de points, pour l'accueil (spec 021)."""
    return await service.podium(db)


@router.get("/par-etablissement", response_model=None)
async def club_de_letablissement(etablissement_id: UUID, db: Base) -> ClubPublic | Response:
    club = await service.club_par_etablissement(db, etablissement_id)
    if club is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return club


@router.get("/{club_id}")
async def fiche_club(club_id: UUID, db: Base) -> ClubFiche:
    club = await service.club_public(db, club_id)
    if club is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ce club est introuvable.")
    return club


# Vérification par l'espace admin -----------------------------------------------------------------------------


@router_admin.get("/suivi")
async def suivi_des_clubs(
    acces: Lecteur,
    db: Base,
    statut: Literal["en_constitution", "actif", "en_regularisation", "suspendu"] | None = None,
    region: RegionScolaire | None = None,
    dre: Annotated[str | None, Query(max_length=30)] = None,
    iesg: UUID | None = None,
    recherche: Annotated[str | None, Query(max_length=100)] = None,
    terrain: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    par_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PageSuivi:
    return await suivi.lister(
        db, acces, statut=statut, region=region, dre=dre, iesg=iesg, recherche=recherche, terrain=terrain,
        page=page, par_page=par_page,
    )  # fmt: skip


@router_admin.get("/seuils")
async def seuils_des_clubs(_: Lecteur) -> Seuils:
    """Les seuils d'activation, fixés dans le code (spec 033) : en lecture seule."""
    return suivi.seuils()


@router_admin.get("/desistements")
async def file_desistements(acces: Lecteur, db: Base) -> FileDesistements:
    return await suivi.file_desistements(db, acces)


@router_admin.post("/desistements/{signalement_id}/confirmer")
async def confirmer_desistement(
    signalement_id: UUID, entree: DecisionSignalementEntree, request: Request, acces: Decideur, db: Base
) -> FileDesistements:
    with _traduire_refus():
        return await suivi.confirmer_desistement(db, acces, signalement_id, entree.version, adresse_ip(request))


@router_admin.post("/desistements/{signalement_id}/rejeter")
async def rejeter_desistement(
    signalement_id: UUID, entree: RejetSignalementEntree, request: Request, acces: Decideur, db: Base
) -> FileDesistements:
    with _traduire_refus():
        return await suivi.rejeter_desistement(
            db, acces, signalement_id, entree.motif, entree.version, adresse_ip(request)
        )


@router_admin.get("/passations")
async def file_passations(acces: Lecteur, db: Base) -> FilePassations:
    return await verification.file_passations(db, acces)


# Affiliations et rattachements à valider (spec 020) : déclarées avant les routes /{club_id}/… -----------


@router_admin.get("/affiliations")
async def file_affiliations(acces: Lecteur, db: Base) -> FileAffiliations:
    return await membres_admin.file_affiliations(db, acces)


@router_admin.post("/affiliations/valider")
async def valider_affiliations(entree: LotEntree, request: Request, acces: Decideur, db: Base) -> ResultatLot:
    return await membres_admin.valider_affiliations(db, acces, entree.elements, adresse_ip(request))


@router_admin.post("/affiliations/refuser")
async def refuser_affiliations(entree: LotRefusEntree, request: Request, acces: Decideur, db: Base) -> ResultatLot:
    return await membres_admin.refuser_affiliations(db, acces, entree.elements, entree.motif, adresse_ip(request))


@router_admin.get("/{club_id}/suivi")
async def fiche_de_suivi(club_id: UUID, acces: Lecteur, db: Base) -> FicheSuivi:
    with _traduire_refus():
        return await suivi.fiche(db, acces, club_id)


@router_admin.post("/{club_id}/terrain")
async def declarer_terrain(
    club_id: UUID, entree: TerrainEntree, request: Request, acces: Decideur, db: Base
) -> FicheSuivi:
    with _traduire_refus():
        return await suivi.marquer_terrain(
            db, acces, club_id, entree.declare, entree.note, entree.version, adresse_ip(request)
        )


@router_admin.get("/{club_id}/membres")
async def membres_admin_du_club(club_id: UUID, acces: Lecteur, db: Base) -> MembresDuClub:
    with _traduire_refus():
        return await membres_admin.membres_du_club(db, acces, club_id)


@router_admin.post("/passations/{passation_id}/valider")
async def valider_passation(
    passation_id: UUID, request: Request, acces: Decideur, db: Base, entree: ActivationEntree | None = None
) -> Passation:
    with _traduire_refus():
        return await verification.valider_passation(
            db, acces, passation_id, adresse_ip(request), entree.version if entree else None
        )


@router_admin.post("/passations/{passation_id}/refuser")
async def refuser_passation(
    passation_id: UUID, entree: RefusEntree, request: Request, acces: Decideur, db: Base
) -> Passation:
    with _traduire_refus():
        return await verification.refuser_passation(
            db, acces, passation_id, entree.motif, adresse_ip(request), entree.version
        )


# Actualités du club (spec 026) : les routes de rédaction des articles, pour le président en place.
router_actualites = APIRouter(prefix="/clubs/moi/actualites", tags=["clubs"])
routes_de_redaction(router_actualites, espace.President, espace.ACTUALITE, espace.club_du_president)
