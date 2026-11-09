"""Gabarit et envoi des e-mails (spec 030) : texte et HTML, valeurs échappées, rien dans les journaux."""

import asyncio
import logging

import pytest

from app.config import settings
from app.courriel import envoi, messages
from app.courriel.gabarit import Bouton, rendre


def test_un_courriel_a_une_version_texte_et_une_version_html() -> None:
    message = envoi.composer("ama@exemple.tg", "Sujet", "Bonjour", "<p>Bonjour</p>")

    assert message.get_content_type() == "multipart/alternative"
    parties = [p.get_content_type() for p in message.iter_parts()]
    assert parties == ["text/plain", "text/html"]


def test_sans_html_le_courriel_reste_du_texte_brut() -> None:
    assert envoi.composer("ama@exemple.tg", "Sujet", "Bonjour").get_content_type() == "text/plain"


def test_les_valeurs_sont_echappees_dans_le_html() -> None:
    courriel = rendre(
        "Sujet",
        surtitre="Test",
        titre=("Un", "titre"),
        salutation="Bonjour <script>alert(1)</script>,",
        paragraphes=['Motif : "<b>gras</b>" & co'],
        bouton=Bouton("Ouvrir", 'https://exemple.tg/?a=1&b="2"'),
    )

    assert "<script>" not in courriel.html
    assert "&lt;script&gt;" in courriel.html
    assert "&lt;b&gt;gras&lt;/b&gt;" in courriel.html
    assert 'href="https://exemple.tg/?a=1&amp;b=&quot;2&quot;"' in courriel.html
    # Le texte brut garde les caractères tels quels.
    assert "<script>alert(1)</script>" in courriel.texte


def test_le_code_du_visiteur_figure_dans_les_deux_versions() -> None:
    courriel = messages.code_visiteur("Kɔfi", "042917", 15)

    assert "042917" in courriel.sujet
    assert "042917" in courriel.texte
    assert "042917" in courriel.html
    assert "Bonjour Kɔfi," in courriel.texte
    assert "15 minutes" in courriel.texte
    assert f"{settings.site_origine}/logo-email.png" in courriel.html


def test_l_invitation_garde_son_lien(monkeypatch: pytest.MonkeyPatch) -> None:
    courriel = messages.invitation("Ama", "https://site.tg/activation?jeton=abc", 48, "Kofi M.")

    assert "https://site.tg/activation?jeton=abc" in courriel.texte
    assert "48 heures" in courriel.texte
    assert "Kofi M. t&#x27;invite" in courriel.html


def test_sans_smtp_hors_production_rien_ne_part_et_rien_nest_journalise(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "smtp_hote", None)
    caplog.set_level(logging.DEBUG)

    asyncio.run(envoi.envoyer("secret@exemple.tg", "Code 123456", "Ton code : 123456", "<p>123456</p>"))

    assert "secret@exemple.tg" not in caplog.text
    assert "123456" not in caplog.text


def test_un_echec_smtp_leve_envoi_impossible_sans_contenu_journalise(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "smtp_hote", "smtp.exemple.tg")
    monkeypatch.setattr(settings, "smtp_expediteur", "Clubs Santé <noreply@exemple.tg>")

    def panne(_: object) -> None:
        raise OSError("connexion refusée")

    monkeypatch.setattr(envoi, "_envoyer", panne)
    caplog.set_level(logging.DEBUG)

    with pytest.raises(envoi.EnvoiImpossible):
        asyncio.run(envoi.envoyer("secret@exemple.tg", "Code 123456", "Ton code : 123456", "<p>123456</p>"))
    assert "secret@exemple.tg" not in caplog.text
    assert "123456" not in caplog.text
