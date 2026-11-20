"""Modification de l'identité et du profil d'un inscrit par l'équipe (spec 045).

Les règles sont celles de l'inscription : on réutilise ses validateurs. Le journal note les champs changés et le
motif, sans copier les données d'identité (prénom, nom, e-mail, téléphone).
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependances import Acces
from app.admin.journal import journaliser
from app.admin.schemas import ModificationInscrit
from app.comptes.models import Role, Utilisateur
from app.comptes.service import CompteInvalide, _valider_email, empreinte
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, Fonction

MESSAGE_VERSION = "Ce profil a changé entre-temps. Recharge la page."
IDENTITE = ("prenom", "nom", "email", "telephone")
CHAMPS_ELEVE = ("classe",)
CHAMPS_ENCADREUR = ("fonction", "fonction_precision", "discipline", "commune")
# Seuls les élèves et les encadreurs ont une fiche d'inscrit modifiable (spec 045).
ROLES_MODIFIABLES = (Role.eleve, Role.encadreur)
VIOLATION_UNICITE = "23505"


class Introuvable(Exception):
    pass


class Refus(Exception):
    def __init__(self, message: str, statut: int = 422) -> None:
        super().__init__(message)
        self.statut = statut


def _valeur(valeur: Any) -> Any:
    return getattr(valeur, "value", valeur)


async def modifier(db: AsyncSession, acces: Acces, utilisateur_id: UUID, entree: ModificationInscrit, ip: str) -> None:
    utilisateur = await db.scalar(select(Utilisateur).where(Utilisateur.id == utilisateur_id).with_for_update())
    if utilisateur is None or utilisateur.role is Role.invite:
        raise Introuvable
    if utilisateur.role is Role.admin:
        raise Refus("Un collaborateur se gère depuis l'écran des collaborateurs.", 409)
    if utilisateur.role not in ROLES_MODIFIABLES:
        raise Refus("Seuls un élève ou un encadreur se modifient ici.", 409)
    envoyes = entree.model_fields_set - {"motif", "version"}

    eleve = await db.get(Eleve, utilisateur.id, with_for_update=True)
    encadreur = await db.get(Encadreur, utilisateur.id, with_for_update=True)
    profil: Eleve | Encadreur | None = eleve or encadreur
    if envoyes & set(CHAMPS_ELEVE) and eleve is None:
        raise Refus("La classe ne concerne qu'un élève.")
    if envoyes & set(CHAMPS_ENCADREUR) and encadreur is None:
        raise Refus("La fonction, la discipline et la commune ne concernent qu'un encadreur.")
    if profil is not None and profil.version != entree.version:
        raise Refus(MESSAGE_VERSION, 409)

    changes: list[str] = []
    traces: dict[str, Any] = {}
    avant: dict[str, Any] = {}
    apres: dict[str, Any] = {}
    est_encadreur = utilisateur.role is Role.encadreur

    for champ in ("prenom", "nom"):
        if champ in envoyes:
            valeur = getattr(entree, champ)
            if not valeur:
                raise Refus("Le prénom et le nom sont obligatoires.")
            if valeur != getattr(utilisateur, champ):
                setattr(utilisateur, champ, valeur)
                changes.append(champ)

    if "telephone" in envoyes:
        if est_encadreur and not entree.telephone:
            raise Refus("Le téléphone d'un encadreur est obligatoire.")
        if entree.telephone != utilisateur.telephone:
            utilisateur.telephone = entree.telephone
            changes.append("telephone")

    if "email" in envoyes:
        try:
            email = _valider_email((entree.email or "").strip() or None, utilisateur.role)
        except CompteInvalide as erreur:
            raise Refus(str(erreur)) from None
        if email != utilisateur.email:
            if email and await db.scalar(
                select(Utilisateur.id).where(Utilisateur.email == email, Utilisateur.id != utilisateur.id)
            ):
                raise Refus("Cet email est déjà pris.", 409)
            utilisateur.email = email
            # Une adresse changée par l'équipe n'a pas été vérifiée par son titulaire.
            utilisateur.email_confirme_le = None
            changes.append("email")
            # L'adresse n'entre pas au journal en clair, mais son empreinte permet de vérifier après coup vers quelle
            # adresse un compte a été dirigé (prise de compte par « mot de passe oublié »).
            traces["email_empreinte"] = empreinte(email) if email else None

    if eleve is not None and "classe" in envoyes:
        if entree.classe is None:
            raise Refus("Choisis une classe.")
        if entree.classe != eleve.classe:
            avant["classe"], apres["classe"] = eleve.classe.value, entree.classe.value
            eleve.classe = entree.classe
            changes.append("classe")

    if encadreur is not None:
        _modifier_encadreur(encadreur, entree, envoyes, changes, avant, apres)

    if not changes:
        raise Refus("Rien n'a changé.")
    if profil is not None:
        # Le verrou optimiste ne voit que les colonnes du profil : l'identité seule doit aussi faire monter la version.
        profil.modifie_le = datetime.now(UTC)
    # Le profil est lu FOR UPDATE et sa version comparée plus haut : seule l'unicité de l'e-mail peut encore échouer,
    # quand deux enregistrements prennent la même adresse au même instant.
    try:
        await db.flush()
    except IntegrityError as erreur:
        await db.rollback()
        if getattr(erreur.orig, "sqlstate", None) == VIOLATION_UNICITE:
            raise Refus("Cet email est déjà pris.", 409) from None
        raise
    journaliser(
        db, "profil_modifie_par_equipe", acces.utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        details={"motif": entree.motif, "champs": changes, "avant": avant, "apres": apres} | traces, adresse_ip=ip,
    )  # fmt: skip
    await db.commit()


def _modifier_encadreur(
    encadreur: Encadreur,
    entree: ModificationInscrit,
    envoyes: set[str],
    changes: list[str],
    avant: dict[str, Any],
    apres: dict[str, Any],
) -> None:
    if "fonction" in envoyes and entree.fonction is None:
        raise Refus("Choisis une fonction.")
    fonction = entree.fonction if "fonction" in envoyes else encadreur.fonction
    precision = entree.fonction_precision if "fonction_precision" in envoyes else encadreur.fonction_precision
    if fonction is Fonction.autre and not precision:
        raise Refus("Précise la fonction.")
    if fonction is not Fonction.autre:
        precision = None
    commune = entree.commune if "commune" in envoyes else encadreur.commune
    if "commune" in envoyes and not commune:
        raise Refus("La commune d'un encadreur est obligatoire.")
    discipline = entree.discipline if "discipline" in envoyes else encadreur.discipline
    nouveau = {"fonction": fonction, "fonction_precision": precision, "discipline": discipline, "commune": commune}
    ancien = {champ: getattr(encadreur, champ) for champ in nouveau}
    if ancien == nouveau:
        return
    for champ, valeur in nouveau.items():
        if ancien[champ] != valeur:
            avant[champ], apres[champ] = _valeur(ancien[champ]), _valeur(valeur)
            setattr(encadreur, champ, valeur)
            changes.append(champ)
