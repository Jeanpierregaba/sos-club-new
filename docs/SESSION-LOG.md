# SESSION-LOG

<!--
Une entrée par session de travail, la plus récente EN HAUT. Rempli par /fin-de-session.
Objectif : que la session suivante reparte avec le contexte, sans deviner.
Reste bref : les décisions vont dans un ADR (docs/decisions/), on se contente d'y faire un lien.

Format :

### AAAA-MM-JJ — titre court
- Fait :
- Pièges rencontrés :
- Décisions : (liens vers les ADR)
- Prochaine étape :
-->

### 2026-11-04 — Espace admin lot 1, comptes de démonstration et roadmap

- Fait : spec 015 livrée (collaborateurs et droits, double authentification, journal d'audit, annuaire,
  exports), relue par le sous-agent `reviewer` et corrigée. Seed `python -m app.seed_dev` (11 comptes
  `dev.*`, accès dans `.comptes-dev.local`). Refonte des pages Hall of Fame et Connexion. Quatre CDC
  reçus (admin, élève, club et président, encadreur), transcrits dans `docs/cdc/` ; PRD réécrit,
  [roadmap](ROADMAP.md) en 8 phases ; Q17 à Q20 et Q28 validées, règle du pseudonyme dans `RULES.md`.
- Pièges rencontrés : le port 8000 est pris par un autre projet, l'API locale tourne sur 8001
  (`API_URL_INTERNE`). `uv` est dans `~/.local/bin`, absent du PATH du terminal de l'utilisateur.
- Décisions : [ADR-0008](decisions/0008-droits-des-collaborateurs-et-double-authentification.md).
- Prochaine étape : préparer le VPS de préproduction, puis `/spec` pour R1 (référentiel DRE,
  établissements, axes).

### 2026-11-02 — Préparation du déploiement sur VPS

- Fait : branche `develop` créée, tout poussé sur `develop` et `main` (`f07a23e`), première CI au vert. Images Docker, pile `deploy/`, workflow `deployer.yml`.
- Pièges rencontrés : les secrets d'environnement GitHub ne sont pas disponibles sur un dépôt privé en Free, d'où des secrets au niveau du dépôt et un seul VPS.
- Décisions : [ADR-0007](decisions/0007-deploiement-vps-docker-compose.md).
- Prochaine étape : préparer le VPS en suivant `deploy/README.md`, puis vérifier le premier déploiement en preprod.

### 2026-11-02 — Spec 001 : connexion et rôles

- Fait : API (`backend/app/comptes/`), page `/connexion`, page `/mon-espace`, en-tête de l'accueil, commande de création de compte. Rien n'est commité.
- Pièges rencontrés : la relecture a trouvé un contournement des limites d'essais par requêtes simultanées et une erreur 500 sur une saisie piégée, tous deux corrigés. `router.clearCache()` ne suffit pas à vider les données d'un compte : le routeur remet la page en cache en la quittant, d'où `gcTime: 0`.
- Décisions : ADR-0006 (même origine). Blocage d'une adresse partagée accepté pour l'instant, à revoir dans la spec 002.
- Prochaine étape : réponses aux questions du PRD, puis spec 002 (hébergeur) ou 003 (clubs).

### 2026-11-02 — Cadrage à partir du cahier des charges

- Fait : PRD, architecture, design, règles, sécurité, tests, backlog et CI remplis à partir de `docs/cahier-des-charges.md`. Formatage Prettier de tout le site pour que le lint passe.
- Pièges rencontrés : le cahier des charges contredit le site sur les 7 axes et les régions (Q1, Q2). `bun audit` signale 13 failles élevées (`TASKS.md`). La CI n'avait encore jamais tourné.
- Décisions : ADR-0002 (accepté), ADR-0003 à ADR-0005 (proposés). Hypothèses Q1 à Q16 dans `docs/PRD.md`.
- Prochaine étape : obtenir les réponses aux questions du PRD, puis `/spec` sur 001 — Connexion et rôles.
