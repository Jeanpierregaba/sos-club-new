"""Aides des tests de l'activation des clubs (spec 033) : peupler un établissement d'encadreurs et d'élèves sans
passer par l'inscription, et figer l'heure du moteur."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid7

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs import activation
from app.clubs.models import Adhesion, EtatAdhesion, EtatRattachement, Rattachement
from app.comptes.models import Role, StatutCompte, Utilisateur
from app.eleves.models import Classe, Eleve
from app.encadreurs.models import Encadreur, EtatVerification, Fonction

DEBUT = datetime(2026, 11, 10, 8, 0, tzinfo=UTC)


class Horloge:
    def __init__(self) -> None:
        self.maintenant = DEBUT

    def avancer(self, jours: float) -> None:
        self.maintenant += timedelta(days=jours)


def figer(monkeypatch: pytest.MonkeyPatch) -> Horloge:
    h = Horloge()
    monkeypatch.setattr(activation, "maintenant", lambda: h.maintenant)
    return h


@dataclass
class Effectif:
    club_id: UUID
    encadreurs: list[UUID] = field(default_factory=list)
    eleves: list[UUID] = field(default_factory=list)


def _compte(role: Role, prefixe: str, statut: StatutCompte) -> Utilisateur:
    ident = f"{prefixe}-{uuid7().hex[-10:]}"
    return Utilisateur(
        identifiant=ident,
        role=role,
        email=f"{ident}@ecole.tg" if role is Role.encadreur else None,
        prenom="Test",
        nom=ident,
        mot_de_passe_hash="inutilise",
        statut=statut,
    )


def ajouter_encadreur(
    en_base: Callable[..., Any],
    etablissement_id: UUID,
    *,
    etat: EtatVerification = EtatVerification.actif,
    statut: StatutCompte = StatutCompte.actif,
    rattache: bool = True,
) -> UUID:
    """Un encadreur de l'établissement ; rattaché au club (comme après sa vérification) si `rattache`."""

    async def inserer(db: AsyncSession) -> UUID:
        compte = _compte(Role.encadreur, "enc", statut)
        db.add(compte)
        await db.flush()
        db.add(
            Encadreur(
                utilisateur_id=compte.id,
                etablissement_id=etablissement_id,
                fonction=Fonction.enseignant,
                etat=etat,
                charte_version="test",
            )
        )
        await db.flush()
        if rattache:
            club = await activation.club_de(db, etablissement_id)
            db.add(Rattachement(encadreur_id=compte.id, club_id=club.id, etat=EtatRattachement.actif))
        return compte.id

    return en_base(inserer)


def ajouter_eleves(
    en_base: Callable[..., Any],
    etablissement_id: UUID,
    nombre: int,
    *,
    etat: EtatAdhesion = EtatAdhesion.active,
    statut: StatutCompte = StatutCompte.actif,
) -> list[UUID]:
    """`nombre` élèves de l'établissement, avec une affiliation dans l'état demandé."""

    async def inserer(db: AsyncSession) -> list[UUID]:
        club = await activation.club_de(db, etablissement_id)
        ids = []
        for _ in range(nombre):
            compte = _compte(Role.eleve, "el", statut)
            db.add(compte)
            await db.flush()
            pseudo = f"p{compte.id.hex[-12:]}"
            db.add(
                Eleve(
                    utilisateur_id=compte.id,
                    pseudonyme=pseudo,
                    pseudonyme_normalise=pseudo,
                    classe=Classe.seconde,
                    etablissement_id=etablissement_id,
                    charte_version="test",
                )
            )
            await db.flush()
            db.add(Adhesion(eleve_id=compte.id, club_id=club.id, etat=etat))
            ids.append(compte.id)
        return ids

    return en_base(inserer)


def peupler(en_base: Callable[..., Any], etablissement_id: UUID, encadreurs: int, eleves: int) -> Effectif:
    """Un club avec `encadreurs` encadreurs vérifiés et `eleves` élèves confirmés, sans recalcul."""
    effectif = Effectif(club_id=en_base(lambda db: activation.club_de(db, etablissement_id)).id)
    effectif.encadreurs = [ajouter_encadreur(en_base, etablissement_id) for _ in range(encadreurs)]
    effectif.eleves = ajouter_eleves(en_base, etablissement_id, eleves)
    return effectif


def recalculer(en_base: Callable[..., Any], club_id: UUID, cause: str = "test") -> Any:
    return en_base(lambda db: activation.recalculer(db, club_id, cause))


def rattacher(en_base: Callable[..., Any], utilisateur_id: UUID, etablissement_id: UUID) -> None:
    """Le rattachement automatique d'un encadreur vérifié (comme à sa vérification), avec recalcul."""
    from app.clubs.affiliations import rattacher_encadreur

    en_base(lambda db: rattacher_encadreur(db, utilisateur_id, etablissement_id, "test", None))


def affilier(en_base: Callable[..., Any], eleve_id: UUID, etablissement_id: UUID) -> UUID:
    """L'affiliation « à confirmer » d'un élève, comme à son inscription."""
    from app.clubs.affiliations import affilier_eleve

    return en_base(lambda db: affilier_eleve(db, eleve_id, etablissement_id)).id


def club_id_de(en_base: Callable[..., Any], etablissement_id: UUID) -> UUID:
    return en_base(lambda db: activation.club_de(db, etablissement_id)).id
