# TASKS

<!--
Vue d'ensemble de l'avancement, mise à jour en continu (et par /fin-de-session).
Une ligne par fonctionnalité, avec un lien vers sa spec ; le découpage fin en tâches est dans
docs/specs/NNN-nom/tasks.md. Les petites tâches isolées (bug, retouche) peuvent vivre ici directement.
-->

## En cours

## À faire

Ordre : dépendances, puis valeur. Les questions Q renvoient à `docs/PRD.md`.

- [ ] 002 — Préproduction en ligne : fichiers de déploiement prêts (`deploy/`), reste à préparer le VPS et à vérifier le premier déploiement
- [ ] Sauvegardes hors du VPS, chiffrées : choisir le service, avant toute donnée réelle
- [ ] 003 — Enregistrement d'un club avec 3 encadreurs, validation par l'admin, régions et axes en base (Q1, Q2, Q5, Q6, Q16)
- [ ] 004 — Inscription d'un élève, retrait par l'encadreur, réinitialisation du mot de passe, journal de points (Q7, Q8)
- [ ] 005 — Passeport Santé et score du club (Q15)
- [ ] 006 — Activités d'un club : soumission, modération, suivi, +100 points (Q1, Q8)
- [ ] 007 — Actualités : Magazine et Paroles aux Élèves
- [ ] 008 — Agenda : calendrier, filtres, ajout par un club
- [ ] 009 — Capsules vidéo par axe (Q1, Q11)
- [ ] 010 — Bibliothèque : magazines et guides PDF (Q11)
- [ ] 011 — Quiz chronométrés : points et badges (Q1, Q11, Q12)
- [ ] 012 — Hall of Fame : Top 3 par région (Q2, Q15)
- [ ] 013 — Carte des clubs sur les vraies données (Q2, Q5)
- [ ] 014 — Commentaires des encadreurs et notifications sur le site (Q13)
- [ ] 015 — Console admin : badges d'excellence et chiffres clés
- [ ] 016 — Pages Club Santé et navigation complète
- [ ] Avant l'ouverture : récépissé de l'IPDCP, avis juridique, mentions d'information, audit de sécurité (Q8, Q9)

### Petites tâches

- [ ] Mettre à jour les dépendances du site : 13 failles élevées signalées par `bun audit` (zod, vite, nanoid…), puis rendre cet audit bloquant dans la CI
- [ ] Remplacer les liens vers des pages absentes et les contenus provisoires de l'accueil au fil des specs (dates d'Agenda, chiffres des clubs)
- [ ] Pages du menu : brancher sur l'API les contenus repris du site de référence (agenda, magazine, bibliothèque, Hall of Fame, quiz), mettre en ligne les fichiers (plaquette, documentaire, documents de la bibliothèque, liens en `#`) et ouvrir les formulaires d'inscription Génie Imhotep ; vérifier 5 doublons probables de l'annuaire (IESG Aného et Dapaong)
- [ ] Renommer le paquet `tanstack_start_ts`
- [ ] Suspension d'un compte (avec son interface) : supprimer aussi les sessions, sinon une réactivation les rend de nouveau valides
- [ ] Suite Playwright des parcours de connexion (garde, en-tête, retour arrière), vérifiés à la main pour l'instant, avant l'ouverture

## Terminé

- [x] [001 — Connexion et rôles](docs/specs/001-connexion-et-roles/spec.md)
- [x] Installer le backend FastAPI et PostgreSQL (ADR-0001), sans schéma ni lien avec le site pour l'instant
- [x] Retirer les dépendances et les mentions de Lovable (reste à couper la liaison côté Lovable)
- [x] Cadrage à partir du cahier des charges, avec les hypothèses Q1 à Q16 à confirmer
