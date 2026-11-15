"""Le PDF d'un rapport approuvé (spec 038), produit à la demande et jamais stocké : texte, participants, liste des
justificatifs et historique des décisions, pour l'archive de l'établissement.

Chaque texte saisi est échappé avant d'entrer dans un paragraphe : aucune balise d'un auteur n'est interprétée.
"""

import io
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.certification.certificat_pdf import GRASSE, NORMALE, date_longue
from app.rapports.schemas import RapportDetail

BLEU = HexColor("#1e3a6e")
GRIS = HexColor("#4b5563")

TEXTES = {
    "activite": [
        ("lieu", "Lieu"), ("responsable", "Responsable"), ("contexte", "Contexte"), ("objectifs", "Objectifs"),
        ("deroulement", "Déroulement"), ("resultats", "Résultats"), ("difficultes", "Difficultés"),
        ("recommandations", "Recommandations"),
    ],
    "mensuel": [
        ("synthese", "Synthèse"), ("analyse", "Analyse"), ("difficultes", "Difficultés"),
        ("perspectives", "Perspectives"),
    ],
    "bilan": [
        ("synthese", "Synthèse"), ("resultats", "Résultats"), ("analyse", "Analyse"),
        ("recommandations", "Recommandations"), ("perspectives", "Perspectives"),
    ],
}  # fmt: skip
PARTICIPANTS = [
    ("total", "Participants"), ("filles", "dont filles"), ("garcons", "dont garçons"),
    ("eleves_club", "dont élèves du club"), ("autres", "dont autres participants"),
]  # fmt: skip
MODELES = {"activite": "Rapport d'activité", "mensuel": "Rapport mensuel", "bilan": "Bilan semestriel"}
DECISIONS = {"approuver": "Approuvé", "corriger": "Correction demandée", "refuser": "Refusé"}

_titre = ParagraphStyle("titre", fontName=GRASSE, fontSize=18, leading=22, textColor=BLEU, spaceAfter=4)
_tete = ParagraphStyle("tete", fontName=NORMALE, fontSize=9, leading=12, textColor=GRIS)
_rubrique = ParagraphStyle("rubrique", fontName=GRASSE, fontSize=11, leading=14, textColor=BLEU, spaceBefore=8)
_texte = ParagraphStyle("texte", fontName=NORMALE, fontSize=10, leading=14)


def _p(texte: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(texte).replace("\n", "<br/>"), style)


def generer(rapport: RapportDetail, genere_le: datetime) -> bytes:
    sortie = io.BytesIO()
    document = SimpleDocTemplate(
        sortie, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"{rapport.reference} — {rapport.titre}", author="Clubs Santé SOS Docteur TV",
    )  # fmt: skip
    donnees: dict[str, Any] = rapport.donnees
    elements: list[Any] = [
        _p(f"{MODELES[rapport.modele.value]} · {rapport.reference or ''}", _tete),
        _p(rapport.titre, _titre),
        _p(
            " · ".join(x for x in (rapport.club.nom, rapport.periode or "", f"par {rapport.auteur}", "approuvé") if x),
            _tete,
        ),
        Spacer(1, 4 * mm),
    ]
    for cle, libelle in TEXTES[rapport.modele.value]:
        valeur = str(donnees.get(cle) or "").strip()
        if valeur:
            elements += [_p(libelle, _rubrique), _p(valeur, _texte)]
    participants = donnees.get("participants") or {}
    nombres = [f"{libelle} : {participants[cle]}" for cle, libelle in PARTICIPANTS if participants.get(cle) is not None]
    if donnees.get("participants_total") is not None:
        nombres.append(f"Participants cumulés : {donnees['participants_total']}")
    if nombres:
        elements += [_p("Participation", _rubrique), _p(" · ".join(nombres), _texte)]
    videos = donnees.get("videos") or []
    if videos:
        elements += [
            _p("Vidéos", _rubrique),
            _p("\n".join(f"https://www.youtube.com/watch?v={v}" for v in videos), _texte),
        ]
    if rapport.documents or rapport.photos:
        noms = [d.nom for d in rapport.documents]
        if rapport.photos:
            noms.append(f"{len(rapport.photos)} photo{'s' if len(rapport.photos) > 1 else ''}")
        elements += [_p("Justificatifs", _rubrique), _p("\n".join(noms), _texte)]
    if rapport.historique:
        lignes = [
            f"{DECISIONS.get(d.decision, d.decision)} le {date_longue(d.decide_le)} (version {d.version})"
            + (f" : {d.motif}" if d.motif else "")
            for d in rapport.historique
        ]
        elements += [_p("Décisions de l'équipe", _rubrique), _p("\n".join(lignes), _texte)]
    elements += [Spacer(1, 6 * mm), _p(f"Document produit le {date_longue(genere_le)}.", _tete)]
    document.build(elements)
    return sortie.getvalue()
