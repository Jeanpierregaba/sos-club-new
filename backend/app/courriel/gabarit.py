"""Gabarit commun des e-mails (spec 030) : une version texte et une version HTML du même message.

Le HTML suit les règles des messageries : tableaux, styles en ligne, largeur 600 px, aucune ressource externe sauf
le logo servi par le site. Toute valeur insérée est échappée : un prénom ou un motif ne peut pas injecter de HTML.
"""

from dataclasses import dataclass
from html import escape

from app.config import settings

# Couleurs du site (src/styles.css), converties d'oklch en hexadécimal pour les messageries.
BLEU = "#174789"
VERT = "#01ac58"
ROUGE = "#d8100f"
ENCRE = "#221844"
FOND = "#f4f6fb"
SIGNATURE = "L'équipe nationale AIMES-AFRIQUE / SOS Docteur TV"


@dataclass(frozen=True)
class Courriel:
    sujet: str
    texte: str
    html: str


@dataclass(frozen=True)
class Bouton:
    libelle: str
    lien: str


def rendre(
    sujet: str,
    *,
    surtitre: str,
    titre: tuple[str, str],
    salutation: str,
    paragraphes: list[str],
    code: str | None = None,
    bouton: Bouton | None = None,
    apres: list[str] | None = None,
) -> Courriel:
    """`titre` : deux parties, la première en bleu, la seconde en vert, comme les titres du site."""
    apres = apres or []
    return Courriel(
        sujet=sujet,
        texte=_texte(salutation, paragraphes, code, bouton, apres),
        html=_html(sujet, surtitre, titre, salutation, paragraphes, code, bouton, apres),
    )


def _texte(salutation: str, paragraphes: list[str], code: str | None, bouton: Bouton | None, apres: list[str]) -> str:
    blocs = [salutation, *paragraphes]
    if code is not None:
        blocs.append(code)
    if bouton is not None:
        blocs.append(f"{bouton.libelle} : {bouton.lien}")
    blocs.extend(apres)
    blocs.append(SIGNATURE)
    return "\n\n".join(blocs) + "\n"


def _paragraphe(texte: str) -> str:
    return f'<p style="margin:0 0 16px;font-size:16px;line-height:1.55;color:{ENCRE};">{escape(texte)}</p>'


def _html(
    sujet: str,
    surtitre: str,
    titre: tuple[str, str],
    salutation: str,
    paragraphes: list[str],
    code: str | None,
    bouton: Bouton | None,
    apres: list[str],
) -> str:
    police = "font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
    corps = [_paragraphe(salutation), *(_paragraphe(p) for p in paragraphes)]
    if code is not None:
        corps.append(
            f'<p style="margin:8px 0 24px;text-align:center;">'
            f'<span style="display:inline-block;padding:14px 24px;border-radius:14px;background:{FOND};'
            f"font-size:32px;font-weight:700;letter-spacing:10px;color:{BLEU};"
            f'font-family:Consolas,Menlo,monospace;">{escape(code)}</span></p>'
        )
    if bouton is not None:
        corps.append(
            f'<p style="margin:8px 0 24px;text-align:center;">'
            f'<a href="{escape(bouton.lien, quote=True)}" style="display:inline-block;padding:14px 28px;'
            f"border-radius:999px;background:{VERT};color:#ffffff;font-size:16px;font-weight:700;"
            f'text-decoration:none;">{escape(bouton.libelle)}</a></p>'
        )
    corps.extend(_paragraphe(p) for p in apres)
    logo = f"{settings.site_origine}/logo-email.png"
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(sujet)}</title></head>
<body style="margin:0;padding:0;background:{FOND};{police}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{FOND};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:20px;">
<tr><td style="padding:28px 32px 8px;">
<img src="{escape(logo, quote=True)}" alt="Club Santé SOS Docteur TV" width="240" height="46" style="display:block;border:0;">
</td></tr>
<tr><td style="padding:16px 32px 32px;{police}">
<p style="margin:0 0 6px;font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:{ROUGE};">{escape(surtitre)}</p>
<h1 style="margin:0 0 20px;font-size:26px;line-height:1.2;color:{BLEU};">{escape(titre[0])} <span style="color:{VERT};">{escape(titre[1])}</span></h1>
{"".join(corps)}
<p style="margin:24px 0 0;font-size:14px;color:{ENCRE};opacity:.75;">{escape(SIGNATURE)}</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""
