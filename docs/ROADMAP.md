# ROADMAP

Ordre de construction de la plateforme, établi le 2026-11-04 à partir des quatre cahiers des charges
de `docs/cdc/` (admin, élève, président de club, encadreur) et du [PRD](PRD.md). Les priorités P0, P1 et
P2 sont celles du [CDC admin, § 15](cdc/admin.md).

L'avancement se suit dans [`TASKS.md`](../TASKS.md). Une spec reçoit son numéro à sa création
(`/spec`) ; les codes R1, R2… ci-dessous servent seulement à ordonner.

## Principe

**Chaque spec livre un parcours complet** : l'écran de l'élève, de l'encadreur ou du président, et le
module de l'espace admin qui le valide ou le pilote. On ne construit pas d'écran admin pour des données
qui n'existent pas encore, et aucun espace n'est livré sans son circuit de validation.

Le lot 1 de l'espace admin ([spec 015](specs/015-espace-admin/spec.md)) sert de socle : droits par
module et par action, périmètre DRE, double authentification, journal d'audit. Chaque spec ajoute ses
droits au catalogue des permissions.

## Vue d'ensemble

| Phase                         | Specs                                                                                                                    | Priorité CDC | Jalon                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------ | -------------------- |
| 0. Stabiliser                 | Commit du lot 1 admin, préproduction en ligne, arbitrages bloquants                                                      | —            | —                    |
| 1. Comptes et clubs           | R1 Référentiel · R2 Compte élève et registre des points · R3 Compte encadreur · R4 Clubs et présidence · R5 Affiliations | P0           | **A. Démo pilote**   |
| 2. Modération et publications | R6 Centre de modération et articles · R7 Commentaires · R8 Espace du président                                           | P0           | **A. Démo pilote**   |
| 3. Quiz et certification      | R9 Quiz · R10 Ressources et fascicules · R11 Certification Génie Imhotep                                                 | P0           | B. Ouverture         |
| 4. Rapports d'activités       | R12 Rapports, rapports mensuels et bilans                                                                                | P0           | B. Ouverture         |
| 5. Classements                | R13 Classements et tableaux de bord · R14 Clôture de semestre et Top 3                                                   | P0           | **B. Ouverture**     |
| 6. Vie du réseau              | R15 Cartes numériques · R16 Agenda et invitations · R17 Partages · R18 Forums · R19 Comptes visiteurs                    | P1           | C. Après l'ouverture |
| 7. Contenus éditoriaux        | R20 Vidéos · R21 Campagnes et pages institutionnelles                                                                    | P1           | En parallèle         |
| 8. Optimisation               | R22 Détection d'anomalies et analyses · R23 Chatbot SOS                                                                  | P2           | C. Après l'ouverture |

**Jalons**

- **A. Démo pilote** : en préproduction, avec des données de test. Un élève s'inscrit, crée son club
  ou le rejoint, publie un article ; l'admin valide le club, l'affiliation et l'article ; les points
  tombent au bon moment.
- **B. Ouverture** : tout le P0 du CDC admin, plus les formalités d'ouverture (récépissé de l'IPDCP,
  avis juridique, audit de sécurité, sauvegardes hors du VPS). Aucune vraie donnée d'élève avant.
- **C. Après l'ouverture** : P1, puis P2.

## Phase 0 — Stabiliser

- Commiter le lot 1 de l'espace admin sur `develop`.
- Mettre la préproduction en ligne : préparer le VPS et vérifier le premier déploiement (`deploy/README.md`).
- ~~Faire trancher les questions bloquantes de la phase 1 : Q17 à Q20 et Q28 du
  [PRD](PRD.md#questions-ouvertes).~~ Validées le 2026-11-04.

## Phase 1 — Comptes et clubs (P0)

| Code | Spec                                                    | Côté utilisateurs                                                                                                                   | Côté admin                                                                                                          | Taille | Questions            |
| ---- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------ | -------------------- |
| R1   | Référentiel territorial et axes                         | Listes de DRE, d'établissements et d'axes dans les formulaires                                                                      | Module « Clubs et DRE », partie référentiel : DRE configurables, établissements, 7 axes                             | S      | Q1, Q2, Q28          |
| R2   | Compte élève et registre des points                     | Inscription (pseudonyme, classe, établissement, consentement), +100 de bienvenue, profil, tableau de bord minimal ; élève sans club | Validation des statuts, semestres et barème configurables ; le domaine `points` écrit le registre avec le semestre  | M      | Q4, Q8, Q17, Q20–Q22 |
| R3   | Compte encadreur                                        | Inscription (fonction, établissement, club demandé, charte), espace en attente puis actif, +100 après activation                    | File des encadreurs à vérifier, activation                                                                          | M      | Q16, Q22             |
| R4   | Clubs et présidence                                     | Un élève demande la création de l'espace de son club ; le président désigné gère ; fiche publique validée ; carte des clubs réelle  | Validation de la création (doublons, établissement, président), code unique, passation de présidence journalisée    | L      | Q5, Q6, Q16, Q19     |
| R5   | Affiliations des élèves et rattachements des encadreurs | L'élève demande à rejoindre un club ; le président propose ; l'encadreur demande son rattachement (plusieurs clubs possibles)       | Validation des adhésions, retraits et rattachements, en lot pour les cas simples, par un responsable DRE si délégué | M      | Q16, Q18             |

À la fin de la phase, l'ADR-0003 est amendé : le club n'a pas de compte, son espace est géré par le
président, un élève, et chaque encadreur a son propre espace.

## Phase 2 — Modération et publications (P0)

| Code | Spec                             | Côté utilisateurs                                                                                                                   | Côté admin                                                                                                                                              | Taille | Questions |
| ---- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --------- |
| R6   | Centre de modération et articles | Élève, encadreur et président rédigent, enregistrent un brouillon, soumettent, corrigent ; centre de notifications sur le site      | File de modération (filtres, aperçu des médias, approuver, refuser, à corriger, dépublier), versions, pièces jointes privées, +50 / +20 à l'approbation | L      | Q8        |
| R7   | Commentaires                     | Commentaire sur un article publié, en attente jusqu'à validation, +5                                                                | Modération des commentaires, plafonds anti-spam                                                                                                         | S      | Q22       |
| R8   | Espace du président              | Tableau de bord du club, modifications de la fiche, actualités au nom du club, suivi des demandes ; vue en lecture pour les membres | Validation des modifications de fiche et des actualités du club                                                                                         | M      | Q20       |

R6 crée le moteur commun de modération (états, versions, décisions, notifications) : toutes les specs
suivantes qui publient quelque chose le réutilisent. Un ADR fixe ce moteur et le stockage privé des
pièces jointes (suite de l'ADR-0005).

## Phase 3 — Quiz et certification (P0)

| Code | Spec                        | Côté utilisateurs                                                                                                                                     | Côté admin                                                                                                       | Taille | Questions     |
| ---- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------ | ------------- |
| R9   | Quiz                        | Quiz chronométrés arbitrés par le serveur (ADR-0004) ; points à la première réussite seulement (+50 élève, encadreur à 0 ; +25 club en R13, spec 022) | Banque de quiz : créer, tester, publier, paramètres versionnés ; aucun droit pour les encadreurs, même par l'API | L      | Q11, Q12, Q24 |
| R10  | Ressources et fascicules    | Bibliothèque : fascicules, magazines, guides PDF                                                                                                      | Gestion des ressources                                                                                           | S      | Q11           |
| R11  | Certification Génie Imhotep | Parcours des 12 quiz obligatoires, 5 badges, certificat vérifiable, +1 000 (élève et encadreur) et +100 au club                                       | Seuils et règles des badges, réémission et révocation des certificats                                            | M      | Q24, Q25      |

## Phase 4 — Rapports d'activités (P0)

| Code | Spec                                  | Côté utilisateurs                                                                                                                                | Côté admin                                                                                                                          | Taille | Questions |
| ---- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | ------ | --------- |
| R12  | Rapports, rapports mensuels et bilans | L'encadreur et le président déposent un rapport (champs du CDC, pièces justificatives), le suivent, le corrigent ; modèles mensuel et semestriel | Examen, archive privée, publication d'un résumé sur décision distincte, détection des doublons (club, date, référence ou événement) | L      | Q22, Q29  |

## Phase 5 — Classements (P0)

| Code | Spec                            | Côté utilisateurs                                                                                                                                                                             | Côté admin                                                                                           | Taille | Questions |
| ---- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------ | --------- |
| R13  | Classements et tableaux de bord | Classements séparés des élèves et des encadreurs (club, DRE, national) et des clubs (DRE, national), semestre et historique ; tableaux de bord complets ; Hall of Fame sur les vraies données | Module « Points » : registre consultable, correction manuelle motivée et journalisée                 | L      | Q21       |
| R14  | Clôture de semestre et Top 3    | Palmarès archivé, Grand Champion, Vice-Champion, Jeune Talent                                                                                                                                 | Gel, contrôle antifraude, ex æquo, validation, publication ; distinctions des encadreurs si retenues | M      | Q21, Q25  |

R13 crédite aussi les points des clubs laissés en attente par les specs précédentes : par exemple, pour chaque
article approuvé d'un élève affilié (spec 023), `club.article_eleve` au club enregistré dans
`contenu.club_beneficiaire_id`, avec la clé `club_article:<contenu>`.

## Phase 6 — Vie du réseau (P1)

| Code | Spec                   | Contenu                                                                                                                                               | Taille | Questions |
| ---- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | --------- |
| R15  | Cartes numériques      | Carte membre de l'élève et carte encadreur : numéro unique, PDF ou image, page de vérification publique réduite au statut, suspension                 | M      | Q8, Q30   |
| R16  | Agenda et invitations  | Le président et l'encadreur proposent un événement, l'admin le valide ; agenda public filtrable ; invitations des membres et réponses (+30 encadreur) | M      | Q22       |
| R17  | Partages               | « Partager mon classement » (visuel sans donnée sensible) ; republication et partage d'articles avec preuve vérifiée (+10, +50 par réseau)            | M      | Q23       |
| R18  | Forums et co-animation | Sujets et réponses prémodérés, co-animation entre encadreurs d'un même club, invitations des élèves, points des forums                                | L      | Q26       |
| R19  | Comptes visiteurs      | Avancé et livré par la spec 030 : inscription confirmée par un code e-mail, quiz sans points. Reste : commentaires modérés                            | S      | Q27       |

R15 peut remonter juste après R5 si le porteur du projet veut la carte membre dès la démo : elle ne
dépend que du compte et de l'affiliation. R18 exige d'abord un ADR sur les échanges entre élèves
(`docs/RULES.md` l'impose pour tout moyen de contacter un élève).

## Phase 7 — Contenus éditoriaux (P1, en parallèle)

Ces specs ne dépendent que de l'espace admin. Elles peuvent s'intercaler dès qu'une phase attend un
arbitrage.

| Code | Spec                                 | Contenu                                                                                                                | Taille |
| ---- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ------ |
| R20  | Capsules vidéo                       | Vidéos YouTube par axe (ADR-0005), ajoutées depuis l'espace admin                                                      | S      |
| R21  | Campagnes et pages institutionnelles | Campagnes ciblées par profil et DRE, présentation du programme, FAQ, partenaires, chiffres clés sur les vraies données | M      |

## Phase 8 — Optimisation (P2)

- R22 : détection des anomalies (comptes multiples, pics de scores, réponses automatisées), analyses
  comparatives, relances automatiques.
- R23 : chatbot SOS. Il exige un ADR : fournisseur, transfert de données hors du Togo, garde-fous
  médicaux, escalade vers un humain.

## Avant l'ouverture (jalon B)

- Récépissé de l'IPDCP, avis juridique (consentement des mineurs, photos, règlements des prix et de la
  certification, charte de modération, durées de conservation).
- Audit de sécurité (`/audit-securite`), sauvegardes chiffrées hors du VPS, suite Playwright des
  parcours critiques.

## Ancien backlog → nouvelle roadmap

| Ancien (cadrage du 2026-11-02)                 | Devient                                                          |
| ---------------------------------------------- | ---------------------------------------------------------------- |
| 003 Club avec 3 encadreurs, validation admin   | R1, R4, R5 : le club est créé par un élève président             |
| 004 Inscription d'un élève, +50 au club        | R2 : +100 à l'élève, aucun point au club à l'inscription         |
| 005 Passeport Santé et score du club           | R2 (tableau de bord minimal), R13 (classements)                  |
| 006 Activités +100 au club                     | R6 (articles) et R12 (rapports) : deux circuits distincts        |
| 007 Magazine et Paroles aux Élèves             | R6 (articles des élèves, blog) et R21                            |
| 008 Agenda                                     | R16                                                              |
| 009 Capsules vidéo                             | R20                                                              |
| 010 Bibliothèque                               | R10                                                              |
| 011 Quiz                                       | R9, R11                                                          |
| 012 Hall of Fame Top 3 par région              | R13, R14 : Top 3 national des élèves par semestre                |
| 013 Carte des clubs réelle                     | R4                                                               |
| 014 Commentaires des encadreurs, notifications | R7 (tous les profils commentent) et R6 (centre de notifications) |
| 015 suite, modules admin                       | Répartis : chaque spec livre son module admin                    |
| 016 Pages Club Santé                           | R21                                                              |
