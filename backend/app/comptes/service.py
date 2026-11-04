import hashlib
import re
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address, ip_network
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import ColumnElement, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.journal import journaliser
from app.admin.models import Collaborateur, DoubleAuth, EtapeDoubleAuth
from app.comptes.models import Role, Session, StatutCompte, TentativeConnexion, Utilisateur
from app.comptes.motdepasse import doit_rehacher, hacher, verifier, verifier_factice
from app.config import settings

type VerificateurCode = Callable[[AsyncSession, Utilisateur, str], Awaitable[bool]]

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


class AccesTermine(Exception):
    """La date de fin d'accès d'un collaborateur est passée."""


class EtapeInvalide(Exception):
    """Jeton d'étape inconnu ou expiré : il faut reprendre la connexion depuis le mot de passe."""


class CodeIncorrect(Exception):
    pass


@dataclass
class Connexion:
    """Issue d'une connexion : une session ouverte, ou une étape « code » à franchir (double authentification)."""

    utilisateur: Utilisateur
    jeton_session: str | None = None
    jeton_etape: str | None = None


class CompteInvalide(Exception):
    """Le message est destiné à la personne qui crée le compte."""


class DejaPris(CompteInvalide):
    """L'identifiant ou l'email appartient déjà à un autre compte."""


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
) -> Connexion:
    """Vérifie les identifiants. Ouvre une session, ou, si la double authentification est active, une étape « code »."""
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
        if utilisateur and utilisateur.role is Role.admin:
            journaliser(
                db,
                "echec_connexion",
                utilisateur,
                cible_type="utilisateur",
                cible_id=utilisateur.id,
                adresse_ip=adresse_ip,
            )
        await db.commit()
        raise IdentifiantsIncorrects
    if utilisateur.statut is not StatutCompte.actif:
        await _supprimer_essai(db, essai)
        await db.commit()
        raise CompteSuspendu
    if utilisateur.role is Role.admin and await acces_termine(db, utilisateur):
        await _supprimer_essai(db, essai)
        await db.commit()
        raise AccesTermine

    if doit_rehacher(utilisateur.mot_de_passe_hash):
        utilisateur.mot_de_passe_hash = await hacher(mot_de_passe)

    await db.execute(delete(TentativeConnexion).where(TentativeConnexion.cle_hash == cle))
    await _purger_vieux_essais(db)

    double_auth = await db.scalar(
        select(DoubleAuth.utilisateur_id).where(
            DoubleAuth.utilisateur_id == utilisateur.id, DoubleAuth.active_le.is_not(None)
        )
    )
    if double_auth:
        maintenant = datetime.now(UTC)
        await db.execute(
            delete(EtapeDoubleAuth).where(
                or_(EtapeDoubleAuth.utilisateur_id == utilisateur.id, EtapeDoubleAuth.expire_le < maintenant)
            )
        )
        jeton_etape = secrets.token_urlsafe(32)
        db.add(
            EtapeDoubleAuth(
                jeton_hash=empreinte(jeton_etape),
                utilisateur_id=utilisateur.id,
                expire_le=maintenant + timedelta(minutes=settings.duree_etape_code_minutes),
            )
        )
        await db.commit()
        return Connexion(utilisateur, jeton_etape=jeton_etape)

    return Connexion(utilisateur, jeton_session=await ouvrir_session(db, utilisateur, jeton_precedent, adresse_ip))


async def acces_termine(db: AsyncSession, utilisateur: Utilisateur) -> bool:
    fin = await db.scalar(select(Collaborateur.fin_acces).where(Collaborateur.utilisateur_id == utilisateur.id))
    return fin is not None and fin <= datetime.now(UTC)


async def ouvrir_session(
    db: AsyncSession, utilisateur: Utilisateur, jeton_precedent: str | None = None, adresse_ip: str | None = None
) -> str:
    """Crée la session et renvoie le jeton à placer dans le cookie. Valide la transaction."""
    maintenant = datetime.now(UTC)
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
    if utilisateur.role is Role.admin:
        journaliser(
            db, "connexion", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id, adresse_ip=adresse_ip
        )
    await db.commit()
    return jeton


async def connecter_avec_code(
    db: AsyncSession,
    jeton_etape: str,
    code: str,
    adresse_ip: str,
    verifier_code: VerificateurCode,
    jeton_precedent: str | None,
) -> Connexion:
    """Seconde étape : le code de l'application ou un code de secours. Les erreurs comptent comme à la connexion."""
    etape = await db.scalar(
        select(EtapeDoubleAuth).where(
            EtapeDoubleAuth.jeton_hash == empreinte(jeton_etape), EtapeDoubleAuth.expire_le > datetime.now(UTC)
        )
    )
    utilisateur = await db.get(Utilisateur, etape.utilisateur_id) if etape else None
    if etape is None or utilisateur is None or utilisateur.statut is not StatutCompte.actif:
        raise EtapeInvalide
    # La fin d'accès a pu tomber entre le mot de passe et le code.
    if await acces_termine(db, utilisateur):
        await db.execute(delete(EtapeDoubleAuth).where(EtapeDoubleAuth.id == etape.id))
        await db.commit()
        raise AccesTermine

    essai = await reserver_essai_code(db, utilisateur, adresse_ip)
    if not await verifier_code(db, utilisateur, code):
        await noter_echec_code(db, utilisateur, essai, adresse_ip)
        await db.commit()
        raise CodeIncorrect

    await effacer_essais_code(db, utilisateur)
    await db.execute(delete(EtapeDoubleAuth).where(EtapeDoubleAuth.id == etape.id))
    return Connexion(utilisateur, jeton_session=await ouvrir_session(db, utilisateur, jeton_precedent, adresse_ip))


# Les codes de double authentification ont leur propre limite : 5 erreurs par 15 minutes et par compte, à la
# connexion comme sur les pages qui redemandent un code (activation, codes de secours).


def _cle_code(utilisateur: Utilisateur) -> str:
    return empreinte(f"code:{utilisateur.identifiant}")


async def reserver_essai_code(db: AsyncSession, utilisateur: Utilisateur, adresse_ip: str) -> TentativeConnexion:
    """Lève TropDEssais au-delà du seuil."""
    return await _reserver_essai(db, _cle_code(utilisateur), adresse_ip)


async def noter_echec_code(
    db: AsyncSession, utilisateur: Utilisateur, essai: TentativeConnexion, adresse_ip: str
) -> None:
    """Ne valide pas la transaction."""
    await db.execute(update(TentativeConnexion).where(TentativeConnexion.id == essai.id).values(en_cours=False))
    journaliser(
        db,
        "echec_code_double_auth",
        utilisateur,
        cible_type="utilisateur",
        cible_id=utilisateur.id,
        adresse_ip=adresse_ip,
    )


async def effacer_essais_code(db: AsyncSession, utilisateur: Utilisateur) -> None:
    await db.execute(delete(TentativeConnexion).where(TentativeConnexion.cle_hash == _cle_code(utilisateur)))


async def couper_sessions(db: AsyncSession, utilisateur_id: UUID) -> None:
    """Supprime toutes les sessions d'un compte : la requête suivante est refusée. Ne valide pas la transaction."""
    await db.execute(delete(Session).where(Session.utilisateur_id == utilisateur_id))


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


async def preparer_utilisateur(
    db: AsyncSession,
    role: Role,
    identifiant: str,
    prenom: str,
    nom: str,
    mot_de_passe: str,
    email: str | None = None,
    telephone: str | None = None,
) -> Utilisateur:
    """Valide les champs et ajoute le compte à la transaction, sans la valider : l'inscription d'un élève y ajoute
    son profil et ses points de bienvenue (spec 017)."""
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
        raise DejaPris("Cet identifiant est déjà pris.")
    if email and await db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)):
        raise DejaPris("Cet email est déjà pris.")

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
    return utilisateur


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
    utilisateur = await preparer_utilisateur(db, role, identifiant, prenom, nom, mot_de_passe, email, telephone)
    try:
        await db.commit()
    except IntegrityError as erreur:
        await db.rollback()
        # Deux créations simultanées : la contrainte unique de la base tranche.
        if getattr(erreur.orig, "sqlstate", None) != VIOLATION_UNICITE:
            raise
        raise DejaPris("Cet identifiant ou cet email est déjà pris.") from None
    return utilisateur


class MotDePasseIncorrect(Exception):
    pass


async def changer_mot_de_passe(
    db: AsyncSession, utilisateur: Utilisateur, actuel: str, nouveau: str, jeton: str, adresse_ip: str
) -> None:
    """Coupe toutes les autres sessions du compte : un appareil oublié ou volé perd l'accès (spec 017).

    Les essais partagent la limite de la connexion : une session restée ouverte ne permet pas de deviner le mot de
    passe actuel, ni d'occuper le serveur avec des hachages."""
    if not LONGUEUR_MIN_MOT_DE_PASSE <= len(nouveau) <= LONGUEUR_MAX_MOT_DE_PASSE:
        raise CompteInvalide(f"Le nouveau mot de passe doit contenir au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères.")
    essai = await _reserver_essai(db, empreinte(utilisateur.identifiant), adresse_ip)
    if not await verifier(utilisateur.mot_de_passe_hash, actuel):
        await db.execute(update(TentativeConnexion).where(TentativeConnexion.id == essai.id).values(en_cours=False))
        await db.commit()
        raise MotDePasseIncorrect
    await _supprimer_essai(db, essai)
    utilisateur.mot_de_passe_hash = await hacher(nouveau)
    await db.execute(
        delete(Session).where(Session.utilisateur_id == utilisateur.id, Session.jeton_hash != empreinte(jeton))
    )
    journaliser(
        db, "mot_de_passe_change", utilisateur, cible_type="utilisateur", cible_id=utilisateur.id,
        adresse_ip=adresse_ip,
    )  # fmt: skip
    await db.commit()
