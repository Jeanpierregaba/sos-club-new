# TASKS

<!--
Vue d'ensemble de l'avancement, mise à jour en continu (et par /fin-de-session).
Une ligne par fonctionnalité, avec un lien vers sa spec ; le découpage fin en tâches est dans
docs/specs/NNN-nom/tasks.md. Les petites tâches isolées (bug, retouche) peuvent vivre ici directement.
-->

## En cours

- [ ] Quiz santé (922 QCM) jouables depuis la page des jeux, 3 quiz sans compte puis compte visiteur ; correction en vert ou rouge et récapitulatif des erreurs (2026-11-10, ADR-0004 amendé) (spec 031, livré en urgence le 2026-11-09 : spec écrite à rédiger)
- [ ] Fiches d'inscription : élève, encadreur et visiteur, e-mails (R19 avancé) — [spec 030](docs/specs/030-fiches-d-inscription/spec.md)

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
- [x] R11 — Certification Génie Imhotep : 12 quiz, 5 badges, certificat (Q24, Q25) : [spec 029](docs/specs/029-certification/spec.md)

**Phase 4 — Rapports (P0)**

- [ ] R12 — Rapports d'activités, rapports mensuels et bilans (Q22, Q29)

**Phase 5 — Classements (P0, jalon B)**

- [ ] R13 — Classements DRE et national des élèves, encadreurs et clubs, classement interne du club, rangs personnels, registre des points et corrections motivées (Q21) — [spec 036](docs/specs/036-classements-et-tableaux-de-bord/spec.md) (spec, plan et tâches écrits le 2026-11-14, plan à valider ; la part du club est déjà livrée par la spec 034, le gel, les ex æquo et le Top 3 restent R14)
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

- [ ] Suites de la spec 033 (cahier des charges « Gestion, activation et suivi des Clubs Santé ») : rapports d'activité adressés aux encadreurs du club (R12 amendé), agenda du club (R16 amendé), année académique et remise à zéro annuelle des points (amende ADR-0004, R13, R14), archives par année ; retrait d'un élève par l'équipe depuis le suivi des clubs ; une future suppression de compte élève ou encadreur devra appeler `recalculer_clubs_du_membre`
- [ ] Avant la fusion dans `main` : passer la migration `4b93d2491b34` sur une copie de la base de préprod (une DRE au code inconnu la fait échouer) et ajouter la ligne cron des échéances sur le VPS (`deploy/README.md`, étape 8 bis)

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

- [x] [035 — Annuaire national des établissements du Secondaire I](docs/specs/035-annuaire-secondaire-i/spec.md) (2 396 collèges importés avec préfecture et ordre, noms en casse normale, doublons de nom approchant créés à part ; recherche publique et back office filtrable ; activation des clubs au seuil inchangée ; retour de migration refusé si un établissement importé a déjà des membres)
- [x] [034 — Gamification de l'élève : 100 quiz sur 4 niveaux, étoiles, carte Gold, club à 50 %](docs/specs/034-gamification-eleve-4-niveaux/spec.md) (ADR-0012 : le club reçoit la moitié de chaque gain de l'élève en demi-points ; 100 quiz Jeux sur 4 niveaux, 4 étoiles et carte Gold ; certification à 20 places ; année académique de septembre à juillet, clôture qui fige le classement régional, anciens élèves ; tableau de bord élève et admin des années)
- [x] [033 — Activation automatique des clubs](docs/specs/033-activation-des-clubs/spec.md) (cahier des charges du 2026-11-10, ADR-0011 : le club naît à la première affiliation et s'active seul à 3 encadreurs + 21 élèves confirmés ; régularisation de 15 jours, suspension et retour automatique ; désistement signalé par un encadreur et confirmé par l'équipe ; « Mon Club Santé » pour l'encadreur, suivi des clubs pour l'équipe ; carte nationale à trois chiffres réels et régions ; commande quotidienne des échéances ; demande de club, adhésion par le président et rattachements manuels retirés)
- [x] [032 — « Quel axe est fait pour toi ? » : 7 questions, 3 participations](docs/specs/032-quel-axe-7-questions/spec.md) (parties gardées par l'API, reprise sur un autre appareil, réponse enregistrée à chaque choix ; limite de 3 tenue par le verrou du compte et des contraintes uniques ; résultat principal + 2 axes complémentaires, historique et partage dans le jeu et « Mon espace » ; aucun point ; parties effacées avec le compte)
- [x] [029 — Certification Génie Imhotep](docs/specs/029-certification/spec.md) (R11 : quiz de certification sur 12 places jouées dans l'ordre, sans les +50 ; 5 badges aux paliers réglables et versionnés (+500 pour l'élève) ; certificat unique (+1 000 élève ou encadreur) au numéro non devinable, PDF au seul titulaire avec QR code, vérification publique sans nom complet, club au choix de l'élève ; révocation motivée qui retire les points, réémission ; club bénéficiaire enregistré pour R13)
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
