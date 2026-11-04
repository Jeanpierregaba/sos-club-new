import pytest

from app.referentiel.normalisation import LONGUEUR_MAX, nettoyer, normaliser


def test_accents_majuscules_et_espaces_sont_ignores() -> None:
    assert normaliser("  Lycée   de TOKOIN I ") == "lycee de tokoin i"


def test_deux_graphies_d_un_meme_etablissement_donnent_la_meme_cle() -> None:
    assert normaliser("CEG Adeho") == normaliser("CEG Adého")


def test_apostrophes_typographiques_unifiees() -> None:
    assert normaliser("Lycée d’Agoè") == normaliser("Lycee d'Agoe")


def test_nettoyer_retire_les_espaces_en_trop() -> None:
    assert nettoyer("  Lycée   Bè  ") == "Lycée Bè"


@pytest.mark.parametrize("nom", ["", "   ", "\t\n"])
def test_nom_vide_refuse(nom: str) -> None:
    with pytest.raises(ValueError, match="obligatoire"):
        nettoyer(nom)


def test_nom_trop_long_refuse() -> None:
    nettoyer("a" * LONGUEUR_MAX)
    with pytest.raises(ValueError, match="dépasse"):
        nettoyer("a" * (LONGUEUR_MAX + 1))
