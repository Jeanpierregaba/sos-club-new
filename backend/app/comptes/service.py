import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address, ip_network

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import ColumnElement, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.comptes.models import Role, Session, StatutCompte, TentativeConnexion, Utilisateur
from app.comptes.motdepasse import doit_rehacher, hacher, verifier, verifier_factice
from app.config import settings

FORMAT_IDENTIFIANT = re.compile(r"[a-z0-9._-]{3,30}")
FORMAT_TELEPHONE = re.compile(r"\+?[0-9 ().-]{6,30}")
LONGUEUR_MIN_MOT_DE_PASSE = 8
LONGUEUR_MAX_MOT_DE_PASSE = 256
LONGUEUR_MAX_IDENTIFIANT_SAISI = 254
CONSERVATION_ECHECS = timedelta(hours=1)
VIOLATION_UNICITE = "23505"


class IdentifiantsIncorrects(Exception):
    pass


class CompteSuspendu(Exception):
    pass


class TropDEssais(Exception):
    pass


class CompteInvalide(Exception):
    """Le message est destiné à la personne qui crée le compte."""


def normaliser(saisie: str) -> str:
    return saisie.strip().lower()


def empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode()).hexdigest()


def cle_adresse(hote: str | None) -> str:
    """Clé des limites par adresse réseau. En IPv6, un même abonné dispose de tout un /64."""
    try:
        adresse = ip_address(hote or "")
    except ValueError:
        return "inconnue"
    if adresse.version == 6 and adresse.ipv4_mapped:
        adresse = adresse.ipv4_mapped
    return str(ip_network((adresse, 64), strict=False)) if adresse.version == 6 else str(adresse)


def duree_session(role: Role) -> timedelta:
    if role is Role.admin:
        return timedelta(hours=settings.duree_session_admin_heures)
    return timedelta(days=settings.duree_session_jours)


async def _reserver_essai(db: AsyncSession, cle: str, adresse_ip: str) -> TentativeConnexion:
    """Enregistre l'essai avant le hachage : même une rafale simultanée ne teste pas plus de mots de passe que le seuil."""
    reservation = TentativeConnexion(cle_hash=cle, adresse_ip=adresse_ip)
    db.add(reservation)
    # Validé avant de compter : chaque requête voit alors les autres, et le k-ième essai compte au moins k lignes.
    await db.commit()

    debut = datetime.now(UTC) - timedelta(minutes=settings.fenetre_essais_minutes)

    async def compter(*conditions: ColumnElement[bool]) -> int:
        requete = select(func.count()).select_from(TentativeConnexion)
        return await db.scalar(requete.where(TentativeConnexion.cree_le > debut, *conditions))

    trop_d_essais = (
        await compter(TentativeConnexion.cle_hash == cle) > settings.essais_max_identifiant
        # Seuls les échecs confirmés comptent ici : une classe qui se connecte en même temps ne se bloque pas elle-même.
        or await compter(TentativeConnexion.adresse_ip == adresse_ip, TentativeConnexion.en_cours.is_(False))
        >= settings.essais_max_adresse
    )
    if trop_d_essais:
        await _supprimer_essai(db, reservation)
    # Rend la connexion à la base : le hachage dure trop longtemps pour la garder.
    await db.commit()
    if trop_d_essais:
        raise TropDEssais
    return reservation


async def _supprimer_essai(db: AsyncSession, essai: TentativeConnexion) -> None:
    await db.execute(delete(TentativeConnexion).where(TentativeConnexion.id == essai.id))


async def _purger_vieux_essais(db: AsyncSession) -> None:
    limite = datetime.now(UTC) - CONSERVATION_ECHECS
    await db.execute(delete(TentativeConnexion).where(TentativeConnexion.cree_le < limite))


async def connecter(
    db: AsyncSession, saisie: str, mot_de_passe: str, adresse_ip: str, jeton_precedent: str | None
) -> tuple[Utilisateur, str]:
    """Vérifie les identifiants et ouvre une session. Renvoie l'utilisateur et le jeton à placer dans le cookie."""
    identifiant = normaliser(saisie)
    colonne = Utilisateur.email if "@" in identifiant else Utilisateur.identifiant
    utilisateur = await db.scalar(select(Utilisateur).where(colonne == identifiant))

    # La même clé pour l'identifiant et l'email : passer de l'un à l'autre ne donne pas d'essais en plus.
    cle = empreinte(utilisateur.identifiant if utilisateur else identifiant)
    essai = await _reserver_essai(db, cle, adresse_ip)

    if utilisateur:
        correct = await verifier(utilisateur.mot_de_passe_hash, mot_de_passe)
    else:
        correct = await verifier_factice(mot_de_passe)

    if not correct:
        await db.execute(update(TentativeConnexion).where(TentativeConnexion.id == essai.id).values(en_cours=False))
        await _purger_vieux_essais(db)
        await db.commit()
        raise IdentifiantsIncorrects
    if utilisateur.statut is not StatutCompte.actif:
        await _supprimer_essai(db, essai)
        await db.commit()
        raise CompteSuspendu

    if doit_rehacher(utilisateur.mot_de_passe_hash):
        utilisateur.mot_de_passe_hash = await hacher(mot_de_passe)

    maintenant = datetime.now(UTC)
    await db.execute(delete(TentativeConnexion).where(TentativeConnexion.cle_hash == cle))
    await _purger_vieux_essais(db)
    conditions = [Session.expire_le < maintenant]
    if jeton_precedent:
        conditions.append(Session.jeton_hash == empreinte(jeton_precedent))
    await db.execute(delete(Session).where(or_(*conditions)))

    jeton = secrets.token_urlsafe(32)
    db.add(
        Session(
            utilisateur_id=utilisateur.id,
            jeton_hash=empreinte(jeton),
            expire_le=maintenant + duree_session(utilisateur.role),
        )
    )
    await db.commit()
    return utilisateur, jeton


async def utilisateur_de_la_session(db: AsyncSession, jeton: str) -> Utilisateur | None:
    return await db.scalar(
        select(Utilisateur)
        .join(Session)
        .where(
            Session.jeton_hash == empreinte(jeton),
            Session.expire_le > datetime.now(UTC),
            Utilisateur.statut == StatutCompte.actif,
        )
    )


async def deconnecter(db: AsyncSession, jeton: str) -> None:
    await db.execute(delete(Session).where(Session.jeton_hash == empreinte(jeton)))
    await db.commit()


async def compter_comptes_par_role(db: AsyncSession) -> dict[Role, int]:
    lignes = await db.execute(select(Utilisateur.role, func.count()).group_by(Utilisateur.role))
    return {role: 0 for role in Role} | {role: nombre for role, nombre in lignes}


def _valider_nom(valeur: str, libelle: str) -> str:
    valeur = valeur.strip()
    if not valeur or len(valeur) > 100:
        raise CompteInvalide(f"Le {libelle} est obligatoire et ne dépasse pas 100 caractères.")
    return valeur


def _valider_email(email: str | None, role: Role) -> str | None:
    if not email:
        if role is not Role.eleve:
            raise CompteInvalide(f"L'email est obligatoire pour un compte {role.value}.")
        return None
    try:
        return validate_email(email.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        raise CompteInvalide("Cet email n'est pas valide.") from None


async def creer_compte(
    db: AsyncSession,
    role: Role,
    identifiant: str,
    prenom: str,
    nom: str,
    mot_de_passe: str,
    email: str | None = None,
    telephone: str | None = None,
) -> Utilisateur:
    identifiant = normaliser(identifiant)
    if not FORMAT_IDENTIFIANT.fullmatch(identifiant):
        raise CompteInvalide("L'identifiant doit contenir de 3 à 30 lettres, chiffres, points, tirets ou « _ ».")
    prenom = _valider_nom(prenom, "prénom")
    nom = _valider_nom(nom, "nom")
    email = _valider_email(email, role)
    if telephone and not FORMAT_TELEPHONE.fullmatch(telephone):
        raise CompteInvalide("Ce téléphone n'est pas valide : 6 à 30 chiffres, espaces ou « + », « - », « . », « ( ».")
    if not LONGUEUR_MIN_MOT_DE_PASSE <= len(mot_de_passe) <= LONGUEUR_MAX_MOT_DE_PASSE:
        raise CompteInvalide(
            f"Le mot de passe doit contenir au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères, "
            f"et au plus {LONGUEUR_MAX_MOT_DE_PASSE} caractères."
        )

    if await db.scalar(select(Utilisateur.id).where(Utilisateur.identifiant == identifiant)):
        raise CompteInvalide("Cet identifiant est déjà pris.")
    if email and await db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)):
        raise CompteInvalide("Cet email est déjà pris.")

    utilisateur = Utilisateur(
        role=role,
        identifiant=identifiant,
        email=email,
        telephone=telephone,
        prenom=prenom,
        nom=nom,
        mot_de_passe_hash=await hacher(mot_de_passe),
    )
    db.add(utilisateur)
    try:
        await db.commit()
    except IntegrityError as erreur:
        await db.rollback()
        # Deux créations simultanées : la contrainte unique de la base tranche.
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise CompteInvalide("Cet identifiant ou cet email est déjà pris.") from None
    return utilisateur
