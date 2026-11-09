"""Vérification publique d'un certificat (spec 029) : son état et de quoi reconnaître son titulaire, sans son nom
complet (RULES : un élève n'apparaît publiquement que par son pseudonyme et son club)."""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.certification.models import Certificat
from app.certification.progression import ALPHABET
from app.certification.schemas import TitulaireEleve, TitulaireEncadreur, Verification
from app.clubs.models import Club
from app.eleves.models import Eleve
from app.encadreurs.models import Encadreur, Fonction

FORMAT = re.compile(rf"^GI-[{ALPHABET}]{{4}}-[{ALPHABET}]{{4}}-[{ALPHABET}]{{4}}$")


def normaliser(numero: str) -> str | None:
    """Un numéro recopié à la main : majuscules, espaces retirés. None s'il n'a pas la bonne forme."""
    propre = numero.strip().upper().replace(" ", "")
    return propre if FORMAT.match(propre) else None


async def verifier(db: AsyncSession, numero: str) -> Verification | None:
    propre = normaliser(numero)
    if propre is None:
        return None
    certificat = await db.scalar(select(Certificat).where(Certificat.numero == propre))
    if certificat is None:
        return None
    titulaire: TitulaireEleve | TitulaireEncadreur
    if certificat.role == "eleve":
        eleve = await db.get(Eleve, certificat.utilisateur_id)
        club = await db.get(Club, certificat.club_id) if certificat.club_id else None
        titulaire = TitulaireEleve(pseudonyme=eleve.pseudonyme if eleve else "Élève", club=club.nom if club else None)
    else:
        encadreur = await db.get(Encadreur, certificat.utilisateur_id)
        titulaire = TitulaireEncadreur(
            prenom=certificat.titulaire_prenom,
            initiale=certificat.titulaire_nom[:1].upper() + ".",
            fonction=encadreur.fonction if encadreur else Fonction.autre,
        )
    remplace_par = await db.scalar(select(Certificat.numero).where(Certificat.remplace_id == certificat.id))
    return Verification(
        numero=certificat.numero,
        etat=certificat.etat,
        delivre_le=certificat.delivre_le,
        titulaire=titulaire,
        remplace_par=remplace_par,
    )
