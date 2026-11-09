# TASKS

<!--
Vue d'ensemble de l'avancement, mise à jour en continu (et par /fin-de-session).
Une ligne par fonctionnalité, avec un lien vers sa spec ; le découpage fin en tâches est dans
docs/specs/NNN-nom/tasks.md. Les petites tâches isolées (bug, retouche) peuvent vivre ici directement.
-->

## En cours

- [ ] 029 — Certification Génie Imhotep : parcours de 12 quiz, badges, certificat vérifiable (R11, Q24) → [`docs/specs/029-certification/`](docs/specs/029-certification/)

## À faire

Ordre et contenu de chaque spec : [`docs/ROADMAP.md`](docs/ROADMAP.md). Chaque spec livre le parcours
utilisateur et son module admin. Les questions Q renvoient à `docs/PRD.md`.

**Phase 0 — Stabiliser**

- [ ] 002 — Préproduction en ligne : fichiers de déploiement prêts (`deploy/`), reste à préparer le VPS et à vérifier le premier déploiement
- [x] Faire trancher les questions bloquantes de la phase 1 par le porteur du projet (Q17 à Q20, Q28), validées le 2026-11-04

**Phase 1 — Comptes et clubs (P0, jalon A)**

- [x] R4 — Clubs et présidence : création par l'élève président, validation, passation, carte des clubs réelle ; amender l'ADR-0003 (Q5, Q6, Q16, Q19)
- [x] R5 — Affiliations des élèves et rattachements des encadreurs (Q16, Q18)
- [ ] Q4 — Réinitialisation du mot de passe d'un élève par un encadreur rattaché : spec à part (signalée par la spec 020)

**Phase 2 — Modération et publications (P0, jalon A)**

- [x] R6 — Centre de modération, articles et notifications internes (spec 023, ADR-0009)
- [ ] Purge des notifications lues de plus d'un an (signalée par la spec 023)
- [ ] Balayage des fichiers orphelins du stockage (signalé par la spec 024)

**Phase 3 — Quiz et certification (P0)**

- [x] R9 — Quiz chronométrés et banque de quiz (Q11, Q12, Q24) : [spec 027](docs/specs/027-quiz/spec.md)
- [x] R10 — Ressources et fascicules (Q11) : [spec 028](docs/specs/028-bibliotheque/spec.md)
- [ ] R11 — Certification Génie Imhotep : 12 quiz, 5 badges, certificat (Q24, Q25)

**Phase 4 — Rapports (P0)**

- [ ] R12 — Rapports d'activités, rapports mensuels et bilans (Q22, Q29)

**Phase 5 — Classements (P0, jalon B)**

- [ ] R13 — Classements Club, DRE et national, tableaux de bord, module Points (Q21) ; brancher les lignes des clubs dans `points.service.scores_des_clubs`, que lit déjà le podium de l'accueil (spec 021), et créditer `club.article_eleve` aux clubs enregistrés dans `contenu.club_beneficiaire_id` (spec 023), ainsi que `club.commentaire_eleve` pour les seuls commentaires qui ont rapporté des points à leur auteur (ligne `commentaire:<id>` au registre, plafond de 5 par jour, spec 025) et les parts Club du barème harmonisé (spec 022 : compte, commentaire, quiz, question du jour +10, badges, certification), affiliation active au moment du crédit
- [ ] R14 — Clôture de semestre et Top 3 (Q21, Q25)
- [ ] Avant l'ouverture : récépissé de l'IPDCP, avis juridique, sauvegardes hors du VPS, audit de sécurité (Q8, Q9)

**Phases 6 à 8 — Après l'ouverture (P1, P2)**

- [ ] R15 — Cartes numériques élève et encadreur, QR code de vérification (Q8, Q30)
- [ ] R16 — Agenda et invitations (Q22)
- [ ] R17 — Partage du classement et partages vérifiés (Q23)
- [ ] R18 — Forums et co-animation, avec un ADR sur les échanges entre élèves (Q26)
- [ ] R19 — Comptes visiteurs (Q27) : le choix « Particulier / visiteur » est déjà sur `/inscription`, sans formulaire ; le PRD exclut la certification des visiteurs alors que la page l'annonce, à trancher dans la spec
- [ ] R20 — Capsules vidéo par axe
- [ ] R21 — Campagnes et pages institutionnelles
- [ ] R22 — Détection d'anomalies et analyses
- [ ] R23 — Chatbot SOS, avec un ADR (Q26)

### Petites tâches

- [ ] Mettre à jour les dépendances du site : 13 failles élevées signalées par `bun audit` (zod, vite, nanoid…), puis rendre cet audit bloquant dans la CI
- [ ] Remplacer les liens vers des pages absentes et les contenus provisoires de l'accueil au fil des specs (dates d'Agenda, chiffres des clubs)
- [ ] Pages du menu : brancher sur l'API les contenus repris du site de référence (agenda, magazine, bibliothèque, Hall of Fame, quiz), mettre en ligne les fichiers (plaquette, documentaire, documents de la bibliothèque, liens en `#`) et ouvrir les formulaires d'inscription Génie Imhotep ; faire confirmer les 6 doublons de l'annuaire écartés au chargement du référentiel (5 dans l'IESG Aného, 1 dans celle de Dapaong)
- [ ] Défi du jour : faire relire les 30 questions de `backend/app/jeux/banque_initiale.py` par l'équipe nationale ; en prod, `python -m app.jeux.banque_initiale` les charge désactivées, à activer après relecture ; agrandir la banque ; écran admin de la banque avec les quiz (R9)
- [ ] Noms des axes : le document du jeu « Quel axe » (« Gamification & Bourses », « Leadership & Masculinité positive »…) diffère du site (« Bourses & excellence », « Leadership & mentorat »…) : faire trancher et aligner
- [ ] Faire valider par l'équipe nationale (référentiel du 2026-11-05) : noms, visuels et jalons des 5 badges (provisoires sur `/certification` : 3, 5, 7, 9, 12 quiz), seuil de réussite d'un quiz, plafonds et preuve des partages, barème encadreur
- [ ] Renommer le paquet `tanstack_start_ts`
- [ ] Suite Playwright des parcours de connexion (garde, en-tête, retour arrière), vérifiés à la main pour l'instant, avant l'ouverture

## Terminé

- [x] [028 — Bibliothèque : ressources et fascicules](docs/specs/028-bibliotheque/spec.md) (R10 : magazines, guides, fiches, affiches et fascicules en PDF, publiés à deux personnes avec validateur nommé ; PDF contrôlé et réécrit par pypdf, servi en flux ; « À la Une », filtres, compteur de téléchargements sans donnée personnelle ; bibliothèque publique)
- [x] [027 — Quiz chronométrés et banque de quiz](docs/specs/027-quiz/spec.md) (R9 : partie arbitrée par le serveur, envoi question par question, 5 s + 2 s de tolérance, tirage de 15 questions dans une réserve, score seul à la fin ; +50 à la première réussite d'un élève ; banque publiée à deux personnes avec validateur médical ; paramètres versionnés ; mode test sans trace)
- [x] [026 — Espace du président](docs/specs/026-espace-du-president/spec.md) (R8 : « Mon club » pour le président, lecture pour les membres et encadreurs ; propositions de fiche et actualités du club modérées, signées du club, sans point ; passation qui transmet les contenus)
- [x] [025 — Commentaires prémodérés](docs/specs/025-commentaires/spec.md) (R7 : type `commentaire` du moteur ADR-0009, rattaché à l'article ; élèves et encadreurs actifs, liste à plat, +5 dans la limite de 5 par jour, 20 envois par jour au plus ; auteur de l'article notifié ; retrait par l'auteur)
- [x] [024 — Photos des articles](docs/specs/024-photos-des-articles/spec.md) (disque du VPS derrière `Stockage`, ADR-0010 ; attestation Q8 ; WebP sans métadonnées ; couverture et galerie, 5 photos de 8 Mo ; purge à 90 jours ; volume sauvegardé)
- [x] [023 — Centre de modération, articles et notifications](docs/specs/023-moderation-et-articles/spec.md) (moteur commun ADR-0009 : six états, versions, quatre décisions, périmètre DRE ; articles en texte, pages publiques, cloche des notifications ; +50 à la première approbation, club bénéficiaire enregistré pour R13)
- [x] [022 — Harmonisation du barème](docs/specs/022-harmonisation-bareme/spec.md) (référentiel de gamification du 2026-11-05 : barème unique API, admin et site ; question du jour à +20, une réponse par élève et par jour, question propre à chaque élève)
- [x] [021 — Accueil : « Quel axe », défi du jour, podium](docs/specs/021-accueil-jeux-decouverte/spec.md) (jeu de découverte réservé aux élèves, banque de défis en base, Top 3 des lycées avec état d'attente)
- [x] [020 — Affiliations et rattachements](docs/specs/020-affiliations-et-rattachements/spec.md) (R5 : adhésion de l'élève confirmée par le président puis validée en lot par la DRE, rattachement des encadreurs avec club supplémentaire réservé au national, liste des membres, passation confirmée par un encadreur rattaché — Q19)
- [x] [019 — Clubs et présidence](docs/specs/019-clubs-et-presidence/spec.md) (R4 : demande de création par l'élève président, vérification par DRE, carte et fiches publiques, passations de présidence)
- [x] [018 — Compte encadreur](docs/specs/018-compte-encadreur/spec.md) (R3 : inscription en attente d'activation, +100 de bienvenue après vérification, file admin filtrable par DRE, refus motivé et renvoi de demande)
- [x] [017 — Compte élève et registre des points](docs/specs/017-compte-eleve/spec.md) (R2 : inscription avec pseudonyme et établissement proposé, +100 de bienvenue, espace élève, registre `mouvement_points`, semestres et barème réglables dans l'admin)
- [x] [016 — Référentiel : DRE, IESG, établissements et axes](docs/specs/016-referentiel/spec.md) (R1 : 7 DRE, 19 IESG, 838 établissements, 7 axes d'intervention, écrans admin, carte des clubs branchée sur l'API)
- [x] [015 — Espace administrateur, lot 1 : les fondations](docs/specs/015-espace-admin/spec.md) (tableau de bord, collaborateurs et droits, double authentification, journal, annuaire, exports)
- [x] [001 — Connexion et rôles](docs/specs/001-connexion-et-roles/spec.md)
- [x] Installer le backend FastAPI et PostgreSQL (ADR-0001), sans schéma ni lien avec le site pour l'instant
- [x] Retirer les dépendances et les mentions de Lovable (reste à couper la liaison côté Lovable)
- [x] Cadrage à partir du cahier des charges, avec les hypothèses Q1 à Q16 à confirmer
