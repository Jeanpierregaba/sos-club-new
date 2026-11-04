"""Exports des inscrits, agrégés ou nominatifs, et leur historique (CDC admin, 12B)."""

import asyncio
import csv
import io
import logging
import secrets
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import xlsxwriter
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.inscrits import compter, requete_filtree
from app.admin.journal import journaliser
from app.admin.models import Export, FormatExport, StatutExport, TypeExport
from app.admin.schemas import ExportEntree, ExportResume, FiltresInscrits
from app.comptes.models import Utilisateur
from app.comptes.service import empreinte
from app.config import settings
from app.db import SessionLocal

logger = logging.getLogger(__name__)

# Liste blanche : aucune colonne ne peut faire sortir un mot de passe, une empreinte, un jeton ou un secret.
COLONNES: dict[str, str] = {
    "identifiant": "Identifiant",
    "nom": "Nom",
    "prenom": "Prénom",
    "email": "E-mail",
    "telephone": "Téléphone",
    "profil": "Profil",
    "statut": "Statut",
    "date_inscription": "Date d'inscription",
    "consentement": "Consentement",
}
LIBELLES_PROFILS = {"eleve": "Élève", "encadreur": "Encadreur", "admin": "Collaborateur"}
LIBELLES_STATUTS = {"actif": "Actif", "suspendu": "Suspendu", "revoque": "Révoqué"}
DEBUTS_DE_FORMULE = ("=", "+", "-", "@", "\t", "\r")
TYPES_MIME = {
    FormatExport.csv: "text/csv; charset=utf-8",
    FormatExport.xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class Refus(Exception):
    def __init__(self, message: str, statut: int = 422) -> None:
        super().__init__(message)
        self.statut = statut


class LienInvalide(Exception):
    pass


def neutraliser(valeur: str) -> str:
    """Un tableur exécuterait « =… » comme une formule : l'apostrophe en tête le garde comme du texte."""
    return f"'{valeur}" if valeur.startswith(DEBUTS_DE_FORMULE) else valeur


def _cellule(utilisateur: Utilisateur, colonne: str) -> str:
    match colonne:
        case "profil":
            return LIBELLES_PROFILS[utilisateur.role.value]
        case "statut":
            return LIBELLES_STATUTS[utilisateur.statut.value]
        case "date_inscription":
            return utilisateur.cree_le.astimezone(UTC).strftime("%Y-%m-%d %H:%M")
        case "consentement":
            return (
                utilisateur.consentement_le.astimezone(UTC).strftime("%Y-%m-%d") if utilisateur.consentement_le else ""
            )
        case _:
            return getattr(utilisateur, colonne) or ""


def _ecrire(format_: FormatExport, entetes: Sequence[str], lignes: Sequence[Sequence[str | int]]) -> bytes:
    if format_ is FormatExport.csv:
        tampon = io.StringIO()
        ecrivain = csv.writer(tampon, delimiter=";")
        ecrivain.writerow(entetes)
        for ligne in lignes:
            ecrivain.writerow([neutraliser(c) if isinstance(c, str) else c for c in ligne])
        # Le BOM fait reconnaître l'UTF-8 par Excel : les accents restent lisibles.
        return ("﻿" + tampon.getvalue()).encode()

    sortie = io.BytesIO()
    classeur = xlsxwriter.Workbook(sortie, {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False})
    feuille = classeur.add_worksheet("Export")
    gras = classeur.add_format({"bold": True})
    for colonne, entete in enumerate(entetes):
        feuille.write_string(0, colonne, entete, gras)
    for rang, ligne in enumerate(lignes, start=1):
        for colonne, valeur in enumerate(ligne):
            if isinstance(valeur, int):
                feuille.write_number(rang, colonne, valeur)
            else:
                feuille.write_string(rang, colonne, neutraliser(valeur))
    classeur.close()
    return sortie.getvalue()


async def _lignes_nominatives(db: AsyncSession, filtres: FiltresInscrits, colonnes: list[str]) -> list[list[str]]:
    requete = requete_filtree(filtres).order_by(Utilisateur.cree_le, Utilisateur.id)
    return [[_cellule(u, c) for c in colonnes] for u in (await db.scalars(requete)).all()]


async def _lignes_agregees(db: AsyncSession, filtres: FiltresInscrits) -> list[list[str | int]]:
    requete = requete_filtree(filtres).with_only_columns(Utilisateur.role, Utilisateur.statut, Utilisateur.cree_le)
    compteur: Counter[tuple[str, str, str]] = Counter()
    for role, statut, cree_le in await db.execute(requete):
        compteur[
            (LIBELLES_PROFILS[role.value], LIBELLES_STATUTS[statut.value], cree_le.astimezone(UTC).strftime("%Y-%m"))
        ] += 1
    return [[profil, statut, mois, nombre] for (profil, statut, mois), nombre in sorted(compteur.items())]


def _verifier_droit(acces: Acces, entree: ExportEntree) -> None:
    from app.admin.catalogue import Action

    if entree.type is TypeExport.nominatif:
        if not (acces.a("inscrits", Action.exporter) and acces.national):
            raise Refus("Tu n'as pas le droit d'exporter les inscrits.", 403)
        if not entree.colonnes:
            raise Refus("Choisis au moins une colonne.")
        if not entree.finalite or len(entree.finalite.strip()) < 5:
            raise Refus("Indique la finalité de cet export.")
    elif not acces.a("statistiques", Action.exporter):
        raise Refus("Tu n'as pas le droit d'exporter les statistiques.", 403)


async def apercu(db: AsyncSession, acces: Acces, entree: ExportEntree) -> int:
    _verifier_droit(acces, entree)
    return await compter(db, entree.filtres)


async def creer(db: AsyncSession, acces: Acces, entree: ExportEntree, ip: str) -> tuple[Export, str]:
    _verifier_droit(acces, entree)
    nb_inscrits = await compter(db, entree.filtres)
    if nb_inscrits == 0:
        raise Refus("Aucun inscrit ne correspond à ces filtres : aucun fichier n'est créé.")
    if nb_inscrits > settings.export_lignes_max:
        raise Refus(f"Plus de {settings.export_lignes_max} lignes : affine les filtres.")

    colonnes = list(dict.fromkeys(entree.colonnes))
    if entree.type is TypeExport.nominatif:
        entetes = [COLONNES[c] for c in colonnes]
        lignes: list[list[Any]] = await _lignes_nominatives(db, entree.filtres, colonnes)
    else:
        colonnes = []
        entetes = ["Profil", "Statut", "Mois d'inscription", "Nombre de comptes"]
        lignes = await _lignes_agregees(db, entree.filtres)
    fichier = await asyncio.to_thread(_ecrire, entree.format, entetes, lignes)

    maintenant = datetime.now(UTC)
    jeton = secrets.token_urlsafe(32)
    filtres = entree.filtres.model_dump(mode="json", exclude_none=True)
    export = Export(
        demandeur_id=acces.utilisateur.id,
        type=entree.type,
        format=entree.format,
        filtres=filtres,
        colonnes=colonnes,
        finalite=entree.finalite.strip() if entree.finalite else None,
        nb_lignes=len(lignes) if entree.type is TypeExport.nominatif else nb_inscrits,
        statut=StatutExport.pret,
        fichier=fichier,
        jeton_hash=empreinte(jeton),
        lien_expire_le=maintenant + timedelta(minutes=settings.duree_lien_export_minutes),
        fichier_expire_le=maintenant + timedelta(hours=settings.duree_fichier_export_heures),
    )
    db.add(export)
    await db.flush()
    journaliser(
        db,
        "export_demande",
        acces.utilisateur,
        cible_type="export",
        cible_id=export.id,
        perimetre="national",
        details={
            "type": entree.type.value,
            "format": entree.format.value,
            # Le texte recherché peut être le nom d'un élève : le journal, inaltérable, n'en garde que la trace.
            "filtres": {k: ("(texte masqué)" if k == "recherche" else v) for k, v in filtres.items()},
            "colonnes": colonnes,
            "nb_lignes": export.nb_lignes,
            "finalite": export.finalite,
        },
        adresse_ip=ip,
    )
    await db.commit()
    return export, f"/api/admin/exports/{export.id}/fichier?jeton={jeton}"


async def telecharger(db: AsyncSession, acces: Acces, export_id: UUID, jeton: str, ip: str) -> tuple[Export, bytes]:
    """Le demandeur seul, une seule fois, pendant la durée du lien. Le fichier est ensuite effacé."""
    export = await db.scalar(select(Export).where(Export.id == export_id).with_for_update())
    if export is not None and export.type is TypeExport.nominatif:
        # Le droit a pu être retiré depuis la demande : on le revérifie au téléchargement.
        from app.admin.catalogue import Action

        if not (acces.a("inscrits", Action.exporter) and acces.national):
            raise LienInvalide
    if (
        export is None
        or export.demandeur_id != acces.utilisateur.id
        or export.jeton_hash is None
        or not secrets.compare_digest(export.jeton_hash, empreinte(jeton))
        or export.statut is not StatutExport.pret
        or export.lien_expire_le <= datetime.now(UTC)
    ):
        raise LienInvalide
    contenu = await db.scalar(select(Export.fichier).where(Export.id == export.id))
    if contenu is None:
        raise LienInvalide
    export.statut = StatutExport.telecharge
    export.telecharge_le = datetime.now(UTC)
    export.fichier = None
    export.jeton_hash = None
    journaliser(db, "export_telecharge", acces.utilisateur, cible_type="export", cible_id=export.id, adresse_ip=ip)
    await db.commit()
    return export, contenu


def nom_de_fichier(export: Export) -> str:
    date = export.cree_le.astimezone(UTC).strftime("%Y-%m-%d-%H%M")
    return f"inscrits-{export.type.value}-{date}.{export.format.value}"


async def historique(db: AsyncSession, acces: Acces) -> list[ExportResume]:
    """Les exports nominatifs pour qui peut les faire, les agrégés pour qui peut les faire."""
    from app.admin.catalogue import Action

    types = []
    if acces.a("inscrits", Action.exporter) and acces.national:
        types.append(TypeExport.nominatif)
    if acces.a("statistiques", Action.exporter):
        types.append(TypeExport.agrege)
    requete = (
        select(Export, Utilisateur.prenom, Utilisateur.nom)
        .outerjoin(Utilisateur, Utilisateur.id == Export.demandeur_id)
        .where(Export.type.in_(types))
        .order_by(Export.cree_le.desc())
        .limit(200)
    )
    resultats = []
    for export, prenom, nom in await db.execute(requete):
        resume = ExportResume.model_validate(export)
        if export.statut is StatutExport.pret and export.lien_expire_le <= datetime.now(UTC):
            resume.statut = StatutExport.expire
        resume.demandeur_libelle = f"{prenom} {nom}" if prenom else None
        resultats.append(resume)
    return resultats


async def purger(db: AsyncSession) -> int:
    """Efface les fichiers dont le lien ou le délai de conservation est passé. Peut tourner plusieurs fois."""
    maintenant = datetime.now(UTC)
    resultat = await db.execute(
        update(Export)
        .where(
            Export.fichier.is_not(None),
            or_(Export.fichier_expire_le <= maintenant, Export.lien_expire_le <= maintenant),
        )
        .values(fichier=None, jeton_hash=None, statut=StatutExport.expire)
    )
    await db.commit()
    return resultat.rowcount


async def purger_regulierement() -> None:
    while True:
        try:
            async with SessionLocal() as db:
                nombre = await purger(db)
            if nombre:
                logger.info("%s fichier(s) d'export expiré(s) effacé(s)", nombre)
        except Exception:
            logger.exception("Échec de la purge des exports")
        await asyncio.sleep(3600)
