import asyncio

from app.comptes.motdepasse import doit_rehacher, hacher, verifier, verifier_factice
from app.comptes.service import normaliser


def test_le_mot_de_passe_est_hache_en_argon2id() -> None:
    empreinte = asyncio.run(hacher("Éléphant 42 !"))

    assert empreinte.startswith("$argon2id$")
    assert "Éléphant" not in empreinte
    assert not doit_rehacher(empreinte)


def test_verification_du_mot_de_passe() -> None:
    empreinte = asyncio.run(hacher("Éléphant 42 !"))

    assert asyncio.run(verifier(empreinte, "Éléphant 42 !"))
    assert not asyncio.run(verifier(empreinte, "elephant 42 !"))


def test_une_empreinte_invalide_ne_provoque_pas_d_erreur() -> None:
    assert not asyncio.run(verifier("pas-une-empreinte", "x"))


def test_la_verification_factice_echoue_toujours() -> None:
    assert not asyncio.run(verifier_factice("nimporte-quoi"))


def test_normalisation_de_la_saisie() -> None:
    assert normaliser("  JeanK ") == "jeank"
    assert normaliser(" Prof@Ecole.TG\n") == "prof@ecole.tg"
