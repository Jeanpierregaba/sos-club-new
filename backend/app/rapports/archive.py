"""Archive des rapports pour l'équipe (spec 038) : recherche, export CSV sans nom d'élève, PDF d'un rapport.

Un collaborateur de DRE ne voit que les rapports des clubs de sa région ; hors de son périmètre, un rapport n'existe
pas. L'export CSV est journalisé.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.admin.dependances import Acces
from app.admin.exports import neutraliser
from app.admin.journal import journaliser
from app.clubs.models import Club
from app.comptes.models import Role, Utilisateur
from app.moderation.models import Contenu, VersionContenu
from app.moderation.service import Introuvable
from app.points.models import Semestre
from app.rapports.models import ModeleRapport, Rapport, TypeActivite
from app.rapports.schemas import titre_de
from app.rapports.service import ETATS, _periode
from app.referentiel.models import Dre, Etablissement, Iesg

PAR_PAGE = 50
EXPORT_MAX = 5000
LIBELLES = {
    ModeleRapport.activite: "Rapport d'activité",
    ModeleRapport.mensuel: "Rapport mensuel",
    ModeleRapport.bilan: "Bilan semestriel",
}


@dataclass(frozen=True)
class Filtres:
    modele: ModeleRapport | None = None
    etat: str | None = None
    club_id: UUID | None = None
    dre: str | None = None
    recherche: str | None = None
    du: date | None = None
    au: date | None = None


_Original = aliased(Rapport)


def _requete(acces: Acces, filtres: Filtres) -> Select:
    derniere = (
        select(VersionContenu.donnees)
        .where(VersionContenu.contenu_id == Contenu.id, VersionContenu.soumise_le.is_not(None))
        .order_by(VersionContenu.numero.desc())
        .limit(1)
        .correlate(Contenu)
        .scalar_subquery()
    )
    requete = (
        select(
            Contenu, Rapport, Club.nom.label("club"), Dre.nom.label("dre"), Utilisateur.role, Utilisateur.prenom,
            Utilisateur.nom, derniere.label("donnees"), _Original.reference.label("original"),
            TypeActivite.libelle.label("type_libelle"),
        )
        .join(Rapport, Rapport.contenu_id == Contenu.id)
        .join(Club, Club.id == Rapport.club_id)
        .join(Etablissement, Etablissement.id == Club.etablissement_id)
        .join(Iesg, Iesg.id == Etablissement.iesg_id)
        .join(Dre, Dre.code == Iesg.dre_code)
        .join(Utilisateur, Utilisateur.id == Contenu.auteur_id)
        .outerjoin(_Original, _Original.contenu_id == Rapport.doublon_de_id)
        .outerjoin(TypeActivite, TypeActivite.code == Rapport.type_activite)
        # Un brouillon jamais soumis n'existe que pour son auteur.
        .where(Rapport.reference.is_not(None))
    )  # fmt: skip
    if not acces.national:
        requete = requete.where(Iesg.dre_code == acces.collaborateur.perimetre_dre)
    if filtres.modele is not None:
        requete = requete.where(Rapport.modele == filtres.modele)
    if filtres.etat:
        etats = [e for e, nom in ETATS.items() if nom == filtres.etat]
        requete = requete.where(Contenu.etat.in_(etats))
    if filtres.club_id is not None:
        requete = requete.where(Rapport.club_id == filtres.club_id)
    if filtres.dre:
        requete = requete.where(Iesg.dre_code == filtres.dre)
    if filtres.du is not None:
        requete = requete.where(Contenu.soumis_le >= datetime.combine(filtres.du, time.min))
    if filtres.au is not None:
        requete = requete.where(Contenu.soumis_le < datetime.combine(filtres.au + timedelta(days=1), time.min))
    if filtres.recherche and filtres.recherche.strip():
        motif = f"%{filtres.recherche.strip().lower()}%"
        requete = requete.where(or_(func.lower(Rapport.reference).like(motif), func.lower(Club.nom).like(motif)))
    return requete.order_by(Contenu.soumis_le.desc().nulls_last(), Rapport.reference.desc())


def _auteur(role: Role, prenom: str, nom: str) -> str:
    """Le nom d'un encadreur ; jamais celui d'un élève : le président apparaît par sa fonction."""
    return "Président du club" if role is Role.eleve else f"{prenom} {nom}".strip()


async def _semestres(db: AsyncSession, lignes: list) -> dict[UUID, str]:
    ids = {l.Rapport.semestre_id for l in lignes if l.Rapport.semestre_id}
    if not ids:
        return {}
    return {s.id: s.libelle for s in (await db.scalars(select(Semestre).where(Semestre.id.in_(ids)))).all()}


async def lister(db: AsyncSession, acces: Acces, filtres: Filtres, page: int) -> dict:
    requete = _requete(acces, filtres)
    total = await db.scalar(select(func.count()).select_from(requete.order_by(None).subquery()))
    lignes = (await db.execute(requete.offset((page - 1) * PAR_PAGE).limit(PAR_PAGE))).all()
    semestres = await _semestres(db, lignes)
    return {
        "total": int(total or 0),
        "page": page,
        "par_page": PAR_PAGE,
        "rapports": [
            {
                "id": l.Contenu.id,
                "reference": l.Rapport.reference,
                "modele": l.Rapport.modele.value,
                "etat": ETATS.get(l.Contenu.etat, "brouillon"),
                "titre": titre_de(l.Rapport.modele, l.donnees or {}),
                "club": {"id": l.Rapport.club_id, "nom": l.club},
                "dre": l.dre,
                "auteur": _auteur(l.role, l.prenom, l.nom),
                "periode": _periode(l.Rapport, semestres),
                "type_activite": l.type_libelle,
                "soumis_le": l.Contenu.soumis_le,
                "points_auteur": l.Rapport.points_auteur,
                "points_club": l.Rapport.points_club,
                "doublon_de": l.original,
            }
            for l in lignes
        ],
    }


ENTETES = [
    "Référence", "Modèle", "État", "Titre", "Club", "DRE", "Auteur", "Période", "Type d'activité", "Soumis le",
    "Participants", "Points de l'auteur", "Points du club", "Doublon de",
]  # fmt: skip


async def exporter_csv(db: AsyncSession, acces: Acces, filtres: Filtres, ip: str) -> bytes:
    lignes = (await db.execute(_requete(acces, filtres).limit(EXPORT_MAX))).all()
    semestres = await _semestres(db, lignes)
    tampon = io.StringIO()
    ecrivain = csv.writer(tampon, delimiter=";")
    ecrivain.writerow(ENTETES)
    for l in lignes:
        donnees = l.donnees or {}
        participants = (donnees.get("participants") or {}).get("total") or donnees.get("participants_total")
        cellules = [
            l.Rapport.reference or "", LIBELLES[l.Rapport.modele], ETATS.get(l.Contenu.etat, ""),
            titre_de(l.Rapport.modele, donnees), l.club, l.dre, _auteur(l.role, l.prenom, l.nom),
            _periode(l.Rapport, semestres) or "", l.type_libelle or "",
            l.Contenu.soumis_le.strftime("%d/%m/%Y") if l.Contenu.soumis_le else "",
            participants if participants is not None else "", l.Rapport.points_auteur or "",
            l.Rapport.points_club or "", l.original or "",
        ]  # fmt: skip
        ecrivain.writerow([neutraliser(c) if isinstance(c, str) else c for c in cellules])
    journaliser(
        db, "rapports_exportes", acces.utilisateur, cible_type="rapport", cible_id=None,
        perimetre=acces.collaborateur.perimetre_dre or "national",
        details={"lignes": len(lignes), "filtres": {k: str(v) for k, v in vars(filtres).items() if v}},
        adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return ("﻿" + tampon.getvalue()).encode()


async def visible(db: AsyncSession, acces: Acces, contenu_id: UUID) -> Contenu:
    """Un rapport soumis du périmètre du collaborateur ; sinon, il n'existe pas."""
    contenu = await db.get(Contenu, contenu_id)
    rapport = await db.get(Rapport, contenu_id) if contenu else None
    if (
        contenu is None
        or rapport is None
        or rapport.reference is None
        or (not acces.national and contenu.dre_code != acces.collaborateur.perimetre_dre)
    ):
        raise Introuvable
    return contenu
