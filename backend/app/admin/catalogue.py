"""Catalogue des droits de l'espace administrateur (spec 015, ADR-0008).

Un droit est un couple (module, action). Les modules « à venir » sont déjà là pour préparer les rôles,
mais aucune route ne les sert encore. La gestion des collaborateurs n'y figure pas : elle est réservée au
super-administrateur et ne se délègue pas.
"""

from enum import StrEnum


class Action(StrEnum):
    consulter = "consulter"
    creer = "creer"
    modifier = "modifier"
    soumettre = "soumettre"
    approuver = "approuver"
    depublier = "depublier"
    exporter = "exporter"


LIBELLES_ACTIONS: dict[Action, str] = {
    Action.consulter: "Consulter",
    Action.creer: "Créer",
    Action.modifier: "Modifier",
    Action.soumettre: "Soumettre",
    Action.approuver: "Approuver",
    Action.depublier: "Dépublier",
    Action.exporter: "Exporter",
}

C, CR, M, S, A, D, E = (
    Action.consulter,
    Action.creer,
    Action.modifier,
    Action.soumettre,
    Action.approuver,
    Action.depublier,
    Action.exporter,
)

# identifiant : (libellé, disponible dans ce lot, actions possibles)
MODULES: dict[str, tuple[str, bool, tuple[Action, ...]]] = {
    "tableau_de_bord": ("Tableau de bord", True, (C,)),
    "inscrits": ("Inscrits", True, (C, M, E)),
    "statistiques": ("Statistiques", True, (C, E)),
    "journal": ("Journal d'audit", True, (C,)),
    # File de modération (spec 023) : un collaborateur de DRE ne voit que les contenus des auteurs de sa DRE.
    "moderation": ("Modération", True, (C, A, D)),
    # La file des clubs et des passations arrive avec la spec 019 ; le droit `clubs` existait déjà.
    "clubs": ("Clubs et DRE", True, (C, CR, M, A)),
    "contenus": ("Contenus et rubriques", False, (C, CR, M, S, A, D)),
    "agenda": ("Agenda et campagnes", False, (C, CR, M, S, A, D)),
    "rapports": ("Rapports d'activités", False, (C, A)),
    "quiz": ("Quiz et certification", False, (C, CR, M, S, A, D)),
    "points": ("Points et classements", True, (C, M)),
    # Vérification des encadreurs (spec 018) : un collaborateur de DRE ne voit que les demandes de sa DRE.
    "encadreurs": ("Encadreurs à vérifier", True, (C, A)),
    "recompenses": ("Récompenses", False, (C, A)),
    "cartes": ("Cartes et QR codes", False, (C, M)),
    "notifications": ("Notifications et assistance", False, (C, M)),
}

# Droits qui exigent la double authentification (CDC admin, 12A.1).
SENSIBLES: frozenset[tuple[str, Action]] = frozenset(
    {
        # La file montre le nom complet et l'établissement de l'auteur.
        ("moderation", C),
        ("moderation", A),
        ("moderation", D),
        ("contenus", A),
        ("contenus", D),
        ("agenda", A),
        ("agenda", D),
        ("inscrits", M),
        ("inscrits", E),
        ("quiz", A),
        ("quiz", D),
        ("points", M),
        # La file montre l'e-mail et le téléphone ; un encadreur actif accédera aux données de ses élèves.
        ("encadreurs", C),
        ("encadreurs", A),
        # La file des clubs montre des données personnelles (nom, établissement, enquêtes de requête).
        ("clubs", C),
        ("clubs", A),
        ("recompenses", A),
    }
)


def droit_existe(module: str, action: Action) -> bool:
    return module in MODULES and action in MODULES[module][2]


def tous_les_droits() -> set[tuple[str, Action]]:
    return {(module, action) for module, (_, _, actions) in MODULES.items() for action in actions}


class RoleDepart(StrEnum):
    admin_national = "admin_national"
    moderateur = "moderateur"
    gestionnaire_contenus = "gestionnaire_contenus"
    gestionnaire_pedagogique = "gestionnaire_pedagogique"
    gestionnaire_clubs = "gestionnaire_clubs"
    gestionnaire_agenda = "gestionnaire_agenda"
    analyste = "analyste"


LIBELLES_ROLES: dict[RoleDepart, str] = {
    RoleDepart.admin_national: "Administrateur national",
    RoleDepart.moderateur: "Modérateur éditorial",
    RoleDepart.gestionnaire_contenus: "Gestionnaire de contenus",
    RoleDepart.gestionnaire_pedagogique: "Gestionnaire pédagogique",
    RoleDepart.gestionnaire_clubs: "Gestionnaire des clubs et DRE",
    RoleDepart.gestionnaire_agenda: "Gestionnaire de l'agenda et des campagnes",
    RoleDepart.analyste: "Analyste",
}

_TABLEAU = {("tableau_de_bord", C)}

# Préréglages : le super-administrateur ajuste ensuite la grille.
DROITS_DES_ROLES: dict[RoleDepart, set[tuple[str, Action]]] = {
    RoleDepart.admin_national: tous_les_droits(),
    RoleDepart.moderateur: _TABLEAU | {("moderation", C), ("moderation", A), ("moderation", D), ("contenus", C)},
    RoleDepart.gestionnaire_contenus: _TABLEAU | {("contenus", C), ("contenus", CR), ("contenus", M), ("contenus", S)},
    RoleDepart.gestionnaire_pedagogique: _TABLEAU | {("quiz", C), ("quiz", CR), ("quiz", M), ("quiz", S)},
    RoleDepart.gestionnaire_clubs: _TABLEAU
    | {
        ("clubs", C),
        ("clubs", CR),
        ("clubs", M),
        ("clubs", A),
        ("statistiques", C),
        ("encadreurs", C),
        ("encadreurs", A),
    },
    RoleDepart.gestionnaire_agenda: _TABLEAU | {("agenda", C), ("agenda", CR), ("agenda", M), ("agenda", S)},
    RoleDepart.analyste: _TABLEAU | {("statistiques", C), ("statistiques", E)},
}
