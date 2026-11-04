<!-- Transcription de « Cahier_des_charges_Administrateur_Compte_collaborateurs_Exports.docx », reçu le 2026-11-04. Ne pas modifier : le PRD fait foi en cas d'écart. -->

# CAHIER DES CHARGES FONCTIONNEL

ESPACE ADMINISTRATEUR | CLUBS SANTÉ SOS DOCTEUR TV

Version consolidée – 03 novembre 2026 • Projet AIMES-AFRIQUE / SOS DOCTEUR TV

Objet : définir les fonctionnalités, droits, processus de validation, règles de gamification et exigences techniques du centre de pilotage de la plateforme.

## Décisions structurantes

Les visiteurs ont une inscription légère, sans tableau de bord, points, carte membre ni certification.

Les élèves disposent de points, carte membre, jeux, publications, classement et certification ; les présidents disposent de droits de gestion du Club Santé affilié.

Les encadreurs suivent leurs clubs et élèves, co-animent des forums, proposent des événements et déposent des rapports ; ils ne peuvent jamais créer ni modifier de quiz.

Tout contenu soumis par un élève, un président ou un encadreur devant devenir visible publiquement (articles, commentaires, messages de forum, événements, photos) nécessite une validation préalable d’un administrateur habilité.

Les classements individuels élèves et encadreurs existent aux niveaux Club, DRE et national. Les classements collectifs des clubs existent aux niveaux DRE et national.

Le super-administrateur peut créer des comptes collaborateurs associés à un e-mail et des autorisations ciblées ; l’export de la base des inscrits est soumis à des habilitations spécifiques et à une traçabilité complète.

## 1. Finalité et périmètre

L’espace Administrateur centralise l’exploitation de la plateforme, le contrôle éditorial et pédagogique, les affiliations, les points et récompenses, la supervision territoriale, la sécurité et le reporting. Il est réservé aux personnes habilitées ; ses fonctions critiques ne sont jamais exposées aux profils publics.

## 2. Rôles et délégations

| Rôle                                   | Périmètre / autorisations                                                                                                       |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Super-administrateur national          | Paramètres globaux, création des comptes administrateurs, rôles, DRE, référentiels, barèmes, arbitrages et audit complet.       |
| Administrateur national                | Gestion et validation nationales, clubs, comptes, contenus, quiz et certification selon droits explicites.                      |
| Modérateur éditorial                   | Examiner/valider/refuser contenus et forums ; aucune modification des points, quiz ou rôles sans droit supplémentaire.          |
| Responsable DRE (optionnel)            | Suivi des clubs de sa DRE ; modération et indicateurs seulement si délégation accordée.                                         |
| Gestionnaire pédagogique / quiz        | Créer, tester et publier les quiz autorisés et le parcours de certification ; pas d’accès automatique aux données personnelles. |
| Gestionnaire des résultats (optionnel) | Contrôler les classements, anomalies et récompenses ; modifications tracées et double validation.                               |

L’interface doit permettre des permissions granulaires, non uniquement des rôles prédéfinis. Une personne peut disposer de plusieurs droits documentés. Principe du moindre privilège. Les procédures complètes d’invitation, de gestion de comptes et d’export des inscrits sont précisées aux sections 12A à 12C.

## 3. Tableau de bord national

Indicateurs : inscrits par profil, clubs actifs, DRE couvertes, élèves et encadreurs affiliés, visiteurs enregistrés, certifications obtenues, badges délivrés, quiz joués et réussis.

Activité : publications, événements, forums, rapports déposés, répartition par axe, DRE, établissement et période.

File de validation : articles, commentaires, discussions, photos, événements, profils et rapports ; filtres par urgence, date, type, club, DRE et statut.

Alertes : contenus signalés, tentatives de fraude aux points, QR cartes invalides, comptes en doublon, anomalies de scores, délais de modération.

Raccourcis : valider un contenu, créer un club, vérifier une affiliation, publier un quiz, exporter un rapport, consulter un classement.

## 4. Annuaire, inscriptions et affiliations

### 4.1 Utilisateurs

Afficher, rechercher, filtrer et exporter les comptes selon profil, club, DRE, date de création, statut et autorisation de traitement des données.

Vérifier et valider les statuts Élève, Encadreur et Président ; suspendre, réactiver ou désactiver un compte avec justification.

Gérer les comptes Visiteur (nom, prénom, e-mail, WhatsApp facultatif) ; connexion légère par lien ou code sécurisé ; absence de points et certification.

Prévenir les doublons ; conserver un journal des changements de rôle et affiliations ; prévoir une demande de rectification et de suppression des données selon les obligations applicables.

### 4.2 Clubs et référentiel territorial

Créer/valider le Club Santé : code unique, établissement, région/DRE, contacts institutionnels, président, encadreurs, axes actifs, localisation et statut.

Rattacher chaque club à une DRE ; la structure hiérarchique doit être configurable pour tenir compte des évolutions administratives.

Valider les demandes d’adhésion/retrait des membres et la nomination/changement du président ; transférer les droits sans perte de l’historique du club.

Permettre plusieurs encadreurs affiliés au même club, avec rôles référent/co-encadreur et droits limités à leur périmètre.

Les membres consultent l’espace club ; seul le président autorisé le gère au nom du club ; l’administrateur supervise et valide les contenus.

## 5. Centre de modération obligatoire

Règle bloquante : un contenu non approuvé ne doit jamais apparaître sur les pages publiques, flux, recherches, notifications publiques ou API exposées. Les pièces jointes restent privées avant approbation.

| État                     | Effet                                                                           |
| ------------------------ | ------------------------------------------------------------------------------- |
| Brouillon                | Visible uniquement de l’auteur et des administrateurs habilités.                |
| Soumis / En attente      | Non public ; inscrit dans la file de modération ; aucun point de publication.   |
| À corriger               | Non public ; remarques envoyées à l’auteur ; resoumission possible.             |
| Refusé                   | Non public ; motif enregistré ; aucun point.                                    |
| Approuvé / Publié        | Visible dans le périmètre prévu ; points déclenchés une seule fois si éligible. |
| Masqué après publication | Retiré immédiatement ; réexamen des points et journal d’audit.                  |

Actions en lot possibles seulement pour contenus à faible risque ; validation unitaire conseillée pour photos de mineurs, sujets de santé, témoignages et forum.

Vue côte à côte contenu/pièces jointes + historique + vérification des autorisations de diffusion d’images ; décision motivée.

Modération des commentaires et contributions au forum, y compris celles des visiteurs ; outils de signalement, blocage, escalade et retrait.

Toute modification substantielle d’un contenu publié doit repasser en validation ; notification de l’auteur.

Suivi des délais de traitement, des décisions par modérateur et de la charge par DRE.

### 5.1. Portée universelle du contrôle préalable

Tout contenu soumis pour diffusion par un Visiteur, Élève, Président, Encadreur, Administrateur de contenu ou autre utilisateur autorisé commence à l’état « En attente ». Aucun profil ne peut contourner ce circuit, y compris via une modification, une importation, une programmation ou une API.

Publications : articles, actualités des clubs, témoignages, photos, vidéos, galeries, documents destinés à être visibles et descriptions associées.

Interactions : commentaires des visiteurs et membres, sujets et réponses des forums, messages et contenus d’animation destinés à la communauté.

Agenda et mobilisation : propositions d’événements, campagnes, invitations publiques, affiches et modifications de fiches de clubs destinées à publication.

Rapports : dépôt privé et validation administrative obligatoire ; publication publique d’un rapport ou de son résumé soumise à une autorisation distincte.

Les contenus pédagogiques, quiz et ressources produits par les équipes habilitées sont soumis à leur propre approbation éditoriale avant diffusion.

### 5.2. Circuit de validation et statuts

Brouillon → Soumis / En attente → En cours de vérification → Approuvé / Publié OU À corriger OU Refusé. Un contenu retiré de publication porte le statut « Dépublié ».

L’auteur est informé de chaque décision et peut corriger puis soumettre une nouvelle version ; aucune correction en attente ne remplace la version publique déjà approuvée.

L’administrateur vérifie le fond, les images, le respect de la charte, la pertinence sanitaire, les données personnelles et les autorisations de diffusion des mineurs.

Toute décision est horodatée et traçable : auteur, Club, DRE, version, pièces jointes, modérateur, motif et statut avant/après.

### 5.3. Centre de validation — fonctionnalités obligatoires

File centralisée avec compteur de contenus en attente, recherche, filtres (type, rôle, Club, DRE, date, statut, priorité) et aperçu sécurisé.

Actions : approuver, refuser avec motif, demander une correction, escalader à un responsable, masquer ou dépublier après signalement.

Affichage des pièces jointes et versions, contrôles d’autorisations d’image, avertissements de contenu sensible et gestion des signalements.

Notifications privées aux auteurs et, après publication seulement, aux abonnés concernés ; aucun extrait non approuvé dans les moteurs de recherche, flux ou API.

Droit de validation distinct du droit de rédaction ; un administrateur ne valide jamais son propre contenu (principe de double contrôle).

### 5.4. Attribution des points et règles antifraude

Les points de publication, rapport, commentaire ou animation rémunérée par le barème ne sont crédités qu’après approbation finale et vérification de l’action.

Un identifiant unique de contenu et d’action évite tout double crédit ; la modification, la nouvelle soumission ou la co-rédaction ne déclenche pas une nouvelle récompense automatique.

En cas de dépublication pour fraude ou non-respect des règles, les points associés peuvent être annulés par transaction corrective journalisée.

### 5.5. Tests de recette indispensables

Vérifier qu’un commentaire Visiteur, un article Élève, un forum Encadreur, un événement Président et un rapport non approuvé ne sont jamais visibles dans le site public.

Vérifier qu’une mise à jour non approuvée ne devient pas publique, que les pièces jointes privées ne sont pas accessibles par URL directe et que les notifications ne divulguent rien.

Vérifier que les auteurs ne peuvent pas approuver leurs propres contenus, que les droits sont contrôlés côté serveur et que les points ne sont crédités qu’une seule fois.

Vérifier la traçabilité des refus, les demandes de correction et la possibilité de retrait immédiat par un administrateur habilité.

## 6. Administration des contenus et rubriques

| Module                            | Pouvoirs administrateur                                                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Blog / « C’est vous les stars ! » | Créer et éditer les catégories, approuver articles élèves/encadreurs/présidents, gérer textes et médias, mettre en avant.       |
| Forum                             | Créer catégories et règles, valider sujets/messages, autoriser co-animation entre encadreurs du même club, modérer et archiver. |
| Agenda                            | Valider événements proposés, lieu, public, horaires, date, club, DRE ; publier, reporter ou annuler et notifier.                |
| Rapports d’activités              | Vérifier justificatifs, approuver/refuser/demander correction, lier au club et à l’événement, conserver une archive privée.     |
| Campagnes                         | Créer/planifier/retirer campagnes et contenus officiels, cibler par profil et DRE, gérer dates et CTA.                          |
| Pages institutionnelles           | Gérer présentation du programme, axes, FAQ, partenaires, ressources, cartes et chiffres clés.                                   |

## 7. Quiz, jeux et certification

Seuls les administrateurs habilités et gestionnaires pédagogiques autorisés peuvent créer, modifier, importer, tester, planifier, désactiver et publier les quiz. Les encadreurs, présidents et élèves n’ont jamais ce pouvoir.

Distinguer clairement les jeux libres et la certification : banque de quiz de jeux ; parcours officiel de 12 quiz obligatoires, associé aux fascicules pédagogiques et à cinq badges.

Les paramètres (questions par quiz, minuterie, seuil de réussite, tentatives, validation) doivent être configurables par type de parcours et versionnés.

Gérer les fascicules, corrections, catégories, questions, réponses, niveaux, langues, version des questionnaires et contrôles qualité avant publication.

Gérer attribution automatique des badges, certificat Génie Imhotep et identifiant vérifiable ; conserver historique des réussites et révocations justifiées.

Le visiteur peut jouer mais ne reçoit ni points ni accès à la certification ; les élèves et encadreurs autorisés peuvent accéder à leur parcours et au suivi.

Détecter les anomalies de quiz, réponses automatisées, comptes multiples, tentatives suspectes ; journaliser les décisions.

## 8. Gamification, registre des points et classements

Toute attribution de points doit provenir d’un événement vérifiable et être inscrite dans un registre de transactions : utilisateur, club bénéficiaire éventuel, action, justificatif, date, semestre, montant, auteur de validation, annulation éventuelle.

| Action déjà retenue          | Élève          | Club affilié | Encadreur / Club                                          |
| ---------------------------- | -------------- | ------------ | --------------------------------------------------------- |
| Compte élève validé          | +100           | —            | Barème encadreur à confirmer si applicable                |
| Commentaire approuvé         | +5             | —            | +5 pour encadreur (proposé)                               |
| Republier un article du site | +10            | —            | +10 pour encadreur (proposé)                              |
| Article propre approuvé      | +50            | +20          | +50 encadreur ; attribution au club selon règles validées |
| Partager son propre article  | +50 par réseau | —            | +50 par réseau (proposé, partage vérifié)                 |
| Quiz réussi                  | +25            | +10          | +25 encadreur (proposé)                                   |
| Certification obtenue        | +1 000         | +100         | +1 000 encadreur (proposé)                                |
| Rapport d’activité approuvé  | —              | +50 proposés | +100 encadreur, si auteur éligible (proposés)             |

Empêcher les points multiples sur une même réussite, une même publication ou un même rapport ; des contributions conjointes ne doivent pas doubler le score du club.

Séparer points à vie et points du semestre ; bascule semestrielle conservant l’historique et les récompenses.

Classements Élèves et Encadreurs séparés : Club, DRE et National ; classement collectif Clubs : DRE et National.

Partager un visuel de classement sans rendre visibles les informations personnelles non nécessaires ; autorisations spécifiques pour mineurs.

Prévoir un outil de correction manuelle avec motif obligatoire, justification, validation renforcée, et journal avant/après.

Détection de comportements suspects : répétitions, invitations massives, partages non vérifiés, pics de scores, comptes multiples.

## 9. Récompenses, Top 3 et certificats

À chaque semestre, calculer le Top 3 élèves selon le classement semestriel national prévu ; contrôler éligibilité, fraudes, ex æquo et éventuelles sanctions avant publication.

Prévoir classements et distinctions encadreurs si approuvés par les responsables, avec critères distincts des élèves.

Afficher les résultats provisoires et validés, prévoir gel des scores à date de clôture et voie de contestation.

Piloter les lots de la certification annoncés « jusqu’à 1 MILLION FCFA » selon règlement de concours validé, sans confondre points virtuels et dotations monétaires.

Gérer génération, téléchargement, vérification, réémission et révocation des certificats et cartes numériques.

## 10. Cartes numériques et QR codes

Délivrer une carte membre élève et une carte encadreur après validation de statut ; photo, identifiant unique, club, rôle et période de validité.

QR code menant vers une vérification contrôlée du statut et de l’authenticité, sans exposer coordonnées, date de naissance ou données sensibles.

Suspendre ou révoquer en cas de changement de statut, désaffiliation, perte de rôle ou fraude.

Enregistrer dates de délivrance et de changement de statut ; produire un historique des vérifications si nécessaire.

## 11. Pilotage et données par Club / DRE / National

Tableau de bord filtrable par période, Club, établissement, DRE, axe et profil.

Indicateurs : progression certification (12 quiz, 5 badges), points collectifs, élève/encadreur actif, taux de participation, publications validées, forums, événements, rapports.

Carte géographique des clubs avec position et statut validés ; ne pas exposer d’adresses privées.

Comparatifs temporels et territoriaux ; filtres, exports XLSX/CSV/PDF selon habilitations ; rapports périodiques institutionnels.

Traçabilité de la source et de la date d’actualisation des chiffres ; aucune statistique inventée ou codée en dur.

## 12. Notifications, invitations et assistance

Notifier résultats de modération, demandes de correction, événements validés, activité prévue, quiz disponibles, badges, certificats et décisions de classement.

Permettre au président d’inviter ses membres à des activités ; aux encadreurs de co-animer un forum et d’inviter les membres de leurs clubs ; contrôler quotas et préférences de notification.

Administrer les réponses-types, FAQ et contenus du chatbot ; prévoir escalade vers un humain et filtres de sécurité pour questions médicales.

Recueillir signalements de contenus et demandes d’aide ; suivi des tickets et des délais sans exposer les conversations privées.

## 12A. Gestion des comptes collaborateurs et délégation des droits

Objectif : le super-administrateur national peut créer des accès nominatifs pour une équipe de gestion, sans transmettre son propre identifiant et sans accorder automatiquement tous les droits de la plateforme.

### 12A.1 Création et activation des comptes

Créer un collaborateur en renseignant au minimum son nom, son prénom, une adresse e-mail unique, son rôle, son périmètre territorial (national, DRE ou clubs désignés), son statut et, si besoin, sa date de fin d’accès.

Envoyer automatiquement une invitation à l’adresse e-mail affectée avec un lien d’activation sécurisé et temporaire ; le collaborateur définit lui-même ses informations d’authentification. Aucun mot de passe n’est envoyé par e-mail.

Prévoir les états : invitation envoyée, invitation expirée, actif, suspendu, révoqué ; permettre le renvoi d’une invitation, la suspension immédiate et la révocation des sessions existantes.

Exiger une authentification multifacteur pour les comptes disposant de droits sensibles (modération, gestion des rôles, export nominatif, certification, points).

### 12A.2 Rôles, autorisations et exemples concrets

Super-administrateur : gère les collaborateurs, attribue les permissions, accède aux modules nationaux, supervise les exports et les journaux de sécurité.

Gestionnaire de contenus : prépare les articles officiels, images, pages, catégories et brouillons. Il peut les soumettre à validation, mais ne peut pas automatiquement approuver ou publier ses propres contributions.

Modérateur : examine et approuve/refuse les contributions dans le périmètre autorisé ; ne peut pas modifier les paramètres des points ni exporter la base nominative sans droit supplémentaire.

Gestionnaire des clubs / DRE : suit les clubs, établissements, affiliations et activités dans sa zone ; les actions sensibles et publications restent soumises au circuit de validation.

Gestionnaire pédagogique : prépare les quiz, fascicules, parcours, badges et certificats selon ses permissions ; leur mise en ligne suit l’approbation éditoriale requise.

Gestionnaire de l’agenda et des campagnes : propose, édite et planifie des événements et campagnes, sous réserve du contrôle préalable à publication.

Analyste / reporting : consulte des indicateurs et rapports ; l’accès aux données identifiantes et à l’export doit être expressément autorisé et limité.

Permettre une matrice de droits par module et par action : consulter, créer, modifier, soumettre, approuver, dépublier, exporter, gérer les utilisateurs et administrer les permissions.

### 12A.3 Gouvernance et traçabilité

Séparer strictement droits de création et droits d’approbation : aucun utilisateur ne peut approuver sa propre publication, y compris un gestionnaire de contenus ou un administrateur.

Conserver un journal horodaté des invitations, connexions, changements de droits, désactivations, décisions de validation et opérations sensibles ; indiquer l’auteur, l’action et le périmètre concerné.

Afficher au super-administrateur un annuaire des collaborateurs avec recherche, filtres par rôle, e-mail, DRE et statut, et revue périodique des droits actifs.

## 12B. Base des inscrits et exportation sécurisée

Objectif : permettre aux personnes habilitées de consulter et d’extraire les données nécessaires au pilotage, sans exposer inutilement les informations des élèves mineurs ni les secrets techniques.

### 12B.1 Recherche, filtres et types d’export

Consulter l’annuaire global des inscrits : visiteurs, élèves, encadreurs, présidents, comptes collaborateurs ; filtrer par profil, DRE, club, établissement, période d’inscription, statut et affiliation.

Exporter une sélection filtrée ou, pour les seules personnes spécifiquement habilitées, la base complète des inscrits au format Excel (.xlsx) ou CSV (.csv), avec choix des colonnes et récapitulatif du volume avant confirmation.

Champs possibles selon les droits : identifiant, nom, prénom, e-mail, WhatsApp si fourni et si nécessaire, profil, DRE, établissement, Club Santé, statut, date d’inscription et éventuel indicateur de consentement.

Prévoir aussi des exports statistiques agrégés et anonymisés par DRE, club, profil et période, accessibles à un public administratif plus large que les exports nominatifs.

Ne jamais inclure dans les exports : mots de passe, jetons de connexion, secrets de QR code, clés techniques, données médicales ou autres données sensibles non indispensables.

### 12B.2 Contrôle des accès et journal des téléchargements

Réserver l’export nominatif complet au super-administrateur et à des collaborateurs ayant reçu une autorisation explicite ; appliquer les droits sur le serveur, jamais uniquement dans l’interface.

À chaque export, exiger une finalité de traitement ; enregistrer l’identité du demandeur, la date, la portée des filtres, les catégories de données, le nombre de lignes et le motif.

Protéger les fichiers générés (lien temporaire, accès authentifié, durée de conservation limitée et suppression automatique) ; éviter toute mise à disposition par URL publique.

Prévoir un écran « Historique des exports » accessible uniquement aux habilités, avec suivi des demandes, téléchargements et éventuels échecs.

### 12B.3 Sauvegarde technique et confidentialité

Distinguer l’export métier CSV/XLSX des sauvegardes techniques complètes de la base : les sauvegardes incluent procédures chiffrées, restauration testée, accès technique restreint et stockage sécurisé.

Appliquer la minimisation des données, notamment pour les mineurs ; gérer séparément les consentements à recevoir des communications, dont WhatsApp. Les exigences juridiques applicables doivent être vérifiées avant mise en production.

## 12C. Critères de recette des nouvelles fonctionnalités

Un super-administrateur crée un compte « Gestionnaire de contenus » lié à un e-mail : la personne active son compte et peut rédiger un article, mais ne peut ni gérer les rôles ni approuver son propre article.

Un modérateur limité à une DRE ne peut pas valider des contenus appartenant à une autre DRE, ni accéder à la base nationale nominative.

Un compte désactivé perd immédiatement son accès, y compris lorsque sa session était déjà ouverte.

Un analyste sans droit d’export nominatif peut télécharger un rapport agrégé, mais pas la liste complète des inscrits.

Un super-administrateur habilité peut exporter tous les inscrits en XLSX/CSV ; le fichier contient uniquement les colonnes autorisées et l’opération apparaît dans l’historique.

Aucune URL directe ne permet de télécharger un export sans authentification et autorisation valides ; un lien expiré ne fonctionne plus.

## 13. Sécurité, confidentialité et conformité

Authentification forte pour administrateurs ; gestion des sessions, révocation, journal de connexions et droits granularisés.

Protection des mineurs : profils publics limités, minimisation des données, consentements nécessaires pour photos, limitation d’accès aux données pédagogiques.

Protection des pièces jointes avant approbation, contrôle types/taille, antivirus, sauvegardes, restauration, chiffrement en transit et au repos selon architecture.

Traçabilité immuable des validations, changements de points, rôles, affiliations, certificats et suppressions.

Règles de conservation, suppression et rectification des données à définir après vérification des exigences juridiques applicables au Togo et des partenaires techniques.

Validation humaine obligatoire pour les décisions sensibles et procédures de gestion des incidents et abus.

## 14. Parcours et règles d’acceptation

| Test                                    | Résultat attendu                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------------ |
| Élève soumet une photo/article          | Invisible au public tant que non approuvé ; points à zéro jusqu’à validation.              |
| Président propose un événement          | Non visible dans l’agenda avant approbation ; notification après décision.                 |
| Encadreur essaie de créer un quiz       | Accès interdit par interface ET API ; incident journalisé.                                 |
| Deux rapports sur la même activité      | Pas de double crédit des points du club ; détection et arbitrage.                          |
| Classement filtré Club / DRE / National | Bonne population et bon rang selon profil et période ; élèves/encadreurs séparés.          |
| Changement de président                 | Droits transférés après validation ; anciens droits retirés ; historique du club conservé. |
| Visiteur joue à un quiz                 | Résultat affiché, sans points ni accès certification.                                      |
| Contenu publié puis signalé             | Masquage, audit, notification et révision éventuelle des points.                           |
| QR carte invalide/révoquée              | Vérification indique statut non valide, sans données sensibles.                            |
| Partage réseaux répété                  | Aucun point supplémentaire sans vérification d’une nouvelle action éligible.               |

## 15. Priorités de réalisation

| Lot                | Livrables prioritaires                                                                                                                          |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| P0 – Indispensable | Authentification et rôles ; profils/Clubs/DRE ; modération préalable ; quiz/certification ; barèmes et registre points ; rapports ; classement. |
| P1 – Opérationnel  | Cartes et QR, agendas et campagnes, co-animation, notifications, tableaux de bord et exports, partage classement.                               |
| P2 – Optimisation  | Détection avancée d’anomalies, analyses comparatives, automatisation des relances, enrichissement chatbot.                                      |

## 16. Décisions à arbitrer avant développement

Liste exacte des DRE et modalités de rattachement des établissements.

Nombre et répartition des quiz de jeux, seuils de réussite, durée de chaque quiz ; règles exactes des 5 badges et certification.

Barème définitif des encadreurs, présidents, rapports et éventuels points collectifs ; plafond et règles anti-abus.

Périmètre des rôles délégués, modération et approbation en plusieurs niveaux.

Modalités d’attribution des prix semestriels et lots liés à la certification ; règlement officiel, gestion des ex æquo.

Charte de modération, autorisations pour mineurs, mentions légales, politique de conservation et de confidentialité.

Définir les administrateurs habilités à l’export nominatif intégral, la finalité des extractions, les durées de conservation et les procédures de revue des permissions.

Document de cadrage fonctionnel : les montants et modalités identifiés « proposés » restent soumis à validation. Les règles fermes de modération, d’accès et d’exclusion des quiz pour les encadreurs sont intégrées comme exigences obligatoires.
