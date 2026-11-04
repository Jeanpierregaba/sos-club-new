# TASKS

<!--
Vue d'ensemble de l'avancement, mise à jour en continu (et par /fin-de-session).
Une ligne par fonctionnalité, avec un lien vers sa spec ; le découpage fin en tâches est dans
docs/specs/NNN-nom/tasks.md. Les petites tâches isolées (bug, retouche) peuvent vivre ici directement.
-->

## En cours

_Rien pour l'instant._

## À faire

Ordre et contenu de chaque spec : [`docs/ROADMAP.md`](docs/ROADMAP.md). Chaque spec livre le parcours
utilisateur et son module admin. Les questions Q renvoient à `docs/PRD.md`.

**Phase 0 — Stabiliser**

- [ ] 002 — Préproduction en ligne : fichiers de déploiement prêts (`deploy/`), reste à préparer le VPS et à vérifier le premier déploiement
- [x] Faire trancher les questions bloquantes de la phase 1 par le porteur du projet (Q17 à Q20, Q28), validées le 2026-11-04

**Phase 1 — Comptes et clubs (P0, jalon A)**

- [ ] R2 — Compte élève et registre des points : inscription, pseudonyme, +100, semestres et barème réglables (Q4, Q8, Q17, Q20 à Q22)
- [ ] R3 — Compte encadreur : inscription, vérification par l'admin, +100 (Q16, Q22)
- [ ] R4 — Clubs et présidence : création par l'élève président, validation, passation, carte des clubs réelle ; amender l'ADR-0003 (Q5, Q6, Q16, Q19)
- [ ] R5 — Affiliations des élèves et rattachements des encadreurs (Q16, Q18)

**Phase 2 — Modération et publications (P0, jalon A)**

- [ ] R6 — Centre de modération, articles et notifications internes, avec un ADR sur le moteur de modération (Q8)
- [ ] R7 — Commentaires prémodérés (Q22)
- [ ] R8 — Espace du président : tableau de bord, fiche, actualités du club (Q20)

**Phase 3 — Quiz et certification (P0)**

- [ ] R9 — Quiz chronométrés et banque de quiz (Q11, Q12, Q24)
- [ ] R10 — Ressources et fascicules (Q11)
- [ ] R11 — Certification Génie Imhotep : 12 quiz, 5 badges, certificat (Q24, Q25)

**Phase 4 — Rapports (P0)**

- [ ] R12 — Rapports d'activités, rapports mensuels et bilans (Q22, Q29)

**Phase 5 — Classements (P0, jalon B)**

- [ ] R13 — Classements Club, DRE et national, tableaux de bord, module Points (Q21)
- [ ] R14 — Clôture de semestre et Top 3 (Q21, Q25)
- [ ] Avant l'ouverture : récépissé de l'IPDCP, avis juridique, sauvegardes hors du VPS, audit de sécurité (Q8, Q9)

**Phases 6 à 8 — Après l'ouverture (P1, P2)**

- [ ] R15 — Cartes numériques élève et encadreur, QR code de vérification (Q8, Q30)
- [ ] R16 — Agenda et invitations (Q22)
- [ ] R17 — Partage du classement et partages vérifiés (Q23)
- [ ] R18 — Forums et co-animation, avec un ADR sur les échanges entre élèves (Q26)
- [ ] R19 — Comptes visiteurs (Q27)
- [ ] R20 — Capsules vidéo par axe
- [ ] R21 — Campagnes et pages institutionnelles
- [ ] R22 — Détection d'anomalies et analyses
- [ ] R23 — Chatbot SOS, avec un ADR (Q26)

### Petites tâches

- [ ] Mettre à jour les dépendances du site : 13 failles élevées signalées par `bun audit` (zod, vite, nanoid…), puis rendre cet audit bloquant dans la CI
- [ ] Remplacer les liens vers des pages absentes et les contenus provisoires de l'accueil au fil des specs (dates d'Agenda, chiffres des clubs)
- [ ] Pages du menu : brancher sur l'API les contenus repris du site de référence (agenda, magazine, bibliothèque, Hall of Fame, quiz), mettre en ligne les fichiers (plaquette, documentaire, documents de la bibliothèque, liens en `#`) et ouvrir les formulaires d'inscription Génie Imhotep ; faire confirmer les 6 doublons de l'annuaire écartés au chargement du référentiel (5 dans l'IESG Aného, 1 dans celle de Dapaong)
- [ ] Renommer le paquet `tanstack_start_ts`
- [ ] Suite Playwright des parcours de connexion (garde, en-tête, retour arrière), vérifiés à la main pour l'instant, avant l'ouverture

## Terminé

- [x] [016 — Référentiel : DRE, IESG, établissements et axes](docs/specs/016-referentiel/spec.md) (R1 : 7 DRE, 19 IESG, 838 établissements, 7 axes d'intervention, écrans admin, carte des clubs branchée sur l'API)
- [x] [015 — Espace administrateur, lot 1 : les fondations](docs/specs/015-espace-admin/spec.md) (tableau de bord, collaborateurs et droits, double authentification, journal, annuaire, exports)
- [x] [001 — Connexion et rôles](docs/specs/001-connexion-et-roles/spec.md)
- [x] Installer le backend FastAPI et PostgreSQL (ADR-0001), sans schéma ni lien avec le site pour l'instant
- [x] Retirer les dépendances et les mentions de Lovable (reste à couper la liaison côté Lovable)
- [x] Cadrage à partir du cahier des charges, avec les hypothèses Q1 à Q16 à confirmer
