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
