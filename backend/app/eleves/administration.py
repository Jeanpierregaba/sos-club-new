"""Actions de l'espace admin sur un élève (spec 017) : imposer un pseudonyme, réinitialiser le mot de passe (Q4).

Réservées au droit « Inscrits : modifier », au niveau national (contrôlé par la route). Chaque action est journalisée
avec son motif ; le mot de passe provisoire, lui, n'est jamais écrit au journal.
"""

import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.comptes.models import Role, Utilisateur
from app.comptes.motdepasse import hacher
from app.comptes.service import couper_sessions
from app.eleves import pseudonyme
from app.eleves.models import Eleve
from app.eleves.service import Refus, _flush

# Sans caractères qui se confondent à l'écrit ou à l'oral : 0 et o, 1, l et i.
ALPHABET_PROVISOIRE = "abcdefghjkmnpqrstuvwxyz23456789"
LONGUEUR_PROVISOIRE = 12


class Introuvable(Exception):
    pass


async def _eleve(db: AsyncSession, utilisateur_id: UUID) -> tuple[Utilisateur, Eleve]:
    utilisateur = await db.get(Utilisateur, utilisateur_id, with_for_update=True)
    eleve = await db.get(Eleve, utilisateur_id, with_for_update=True) if utilisateur else None
    if utilisateur is None or utilisateur.role is not Role.eleve or eleve is None:
        raise Introuvable
    return utilisateur, eleve


async def imposer_pseudonyme(
    db: AsyncSession, acces: Acces, utilisateur_id: UUID, nouveau: str, motif: str, ip: str
) -> None:
    utilisateur, eleve = await _eleve(db, utilisateur_id)
    try:
        affiche = pseudonyme.valider(nouveau)
    except pseudonyme.PseudonymeInvalide as erreur:
        raise Refus(str(erreur)) from None
    cle = pseudonyme.cle(affiche)
    if cle == pseudonyme.cle(utilisateur.identifiant):
        raise Refus("Le pseudonyme doit être différent de l'identifiant de connexion, qui reste secret.")
    if pseudonyme.contient_le_nom(affiche, utilisateur.prenom, utilisateur.nom):
        raise Refus("Le pseudonyme ne doit pas contenir le prénom et le nom de l'élève.")
    deja = await db.scalar(
        select(Eleve.utilisateur_id).where(Eleve.pseudonyme_normalise == cle, Eleve.utilisateur_id != utilisateur_id)
    )
    if deja:
        raise Refus("Ce pseudonyme est déjà pris.", 409)
    if affiche == eleve.pseudonyme:
        raise Refus("L'élève a déjà ce pseudonyme.", 409)
    avant = eleve.pseudonyme
    eleve.pseudonyme, eleve.pseudonyme_normalise = affiche, cle
    # Deux collaborateurs qui imposent le même pseudonyme au même instant : la base tranche.
    await _flush(db)
    journaliser(
        db, "pseudonyme_impose", acces.utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        details={"avant": avant, "apres": affiche, "motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()


async def reinitialiser_mot_de_passe(db: AsyncSession, acces: Acces, utilisateur_id: UUID, motif: str, ip: str) -> str:
    """Renvoie le mot de passe provisoire, à transmettre à l'élève : il n'est montré qu'une fois."""
    utilisateur, _ = await _eleve(db, utilisateur_id)
    provisoire = "".join(secrets.choice(ALPHABET_PROVISOIRE) for _ in range(LONGUEUR_PROVISOIRE))
    utilisateur.mot_de_passe_hash = await hacher(provisoire)
    await couper_sessions(db, utilisateur.id)
    journaliser(
        db, "mot_de_passe_reinitialise", acces.utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        details={"motif": motif}, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()
    return provisoire
