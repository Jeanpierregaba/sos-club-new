"""Règles du pseudonyme (spec 017) : seule identité publique d'un élève."""

import pytest

from app.eleves.pseudonyme import PseudonymeInvalide, cle, contient_le_nom, valider


@pytest.mark.parametrize(
    ("saisie", "attendu"),
    [("Aya", "Aya"), ("  Kofi   le   Grand ", "Kofi le Grand"), ("Éléonore.T", "Éléonore.T"), ("Ama-2010", "Ama-2010")],
)
def test_pseudonymes_acceptes(saisie: str, attendu: str) -> None:
    assert valider(saisie) == attendu


@pytest.mark.parametrize(
    "saisie",
    [
        "Ay",  # trop court
        "A" * 31,  # trop long
        "aya@mail.tg",  # e-mail
        "Aya_K",  # caractère interdit
        "Kofi 90 12 34 56",  # téléphone
        "123456",  # aucune lettre
        "...",  # aucune lettre
        "Le Con",  # mot interdit
        "SuperAdmin",  # se fait passer pour l'équipe
        "Modérateur Kara",
        "SOS Docteur",
        "Аya Kossi",  # « А » cyrillique : imite « Aya Kossi »
        "ﷺﷺﷺ",  # hors de l'alphabet latin, et s'allonge une fois décomposé
        "ﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀﬀ",  # ligatures latines : la clé dépasserait 30 caractères
        "Aya ٣٤",  # chiffres arabes-indiens
    ],
)
def test_pseudonymes_refuses(saisie: str) -> None:
    with pytest.raises(PseudonymeInvalide):
        valider(saisie)


@pytest.mark.parametrize("saisie", ["Constance", "Badminton Star", "Ñandú", "Ægir"])
def test_un_mot_interdit_ne_touche_pas_un_nom_ordinaire(saisie: str) -> None:
    assert valider(saisie) == saisie


def test_le_pseudonyme_ne_reprend_pas_le_nom_complet() -> None:
    assert contient_le_nom("Aya Mensah", "Aya", "Mensah")
    assert contient_le_nom("mensah.aya", "Aya", "Mensah")
    assert not contient_le_nom("Aya la Curieuse", "Aya", "Mensah")


def test_la_cle_ignore_majuscules_accents_espaces_et_ponctuation() -> None:
    assert cle("Àya K") == cle("aya-k") == cle("AYA.K") == cle("ayak") == "ayak"
