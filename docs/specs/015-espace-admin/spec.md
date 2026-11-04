# 015 — Espace administrateur, lot 1 : les fondations

## Objectif

Donner à l'équipe nationale AIMES-AFRIQUE / SOS DOCTEUR TV un espace d'administration (`/admin`) qui
servira de socle à tous les modules du « Cahier des charges fonctionnel — Espace administrateur » du
03/11/2026 ([le CDC admin](../../cdc/admin.md)). Ce premier lot couvre les sections 3, 4.1, 12A, 12B, 12C et 13 de ce document :

- un tableau de bord national, calculé sur les vraies données ;
- des comptes collaborateurs nominatifs, invités par e-mail, avec des droits par module et par action,
  limités à un périmètre (national ou une DRE) ;
- la double authentification pour les droits sensibles ;
- un journal d'audit des opérations sensibles ;
- l'annuaire des inscrits et les exports CSV/XLSX tracés.

Les autres modules du CDC admin (modération, clubs et DRE, contenus, quiz, points, récompenses, cartes
QR, notifications) arrivent dans les lots suivants. Ils apparaissent déjà dans le menu, marqués « à venir ».

Le PRD classait les exports hors du MVP. Le CDC admin les demande : ce lot les fait entrer dans le
périmètre, limités aux comptes qui existent aujourd'hui.

## Comportement attendu

**Entrer dans l'espace admin**

1. Un collaborateur se connecte sur `/connexion` avec son identifiant ou son e-mail et son mot de passe.
2. Si son compte a la double authentification, une deuxième étape lui demande le code à 6 chiffres de son
   application (Google Authenticator, Microsoft Authenticator…), ou un de ses codes de secours.
3. Il arrive sur `/admin`. Le menu latéral ne montre en actif que les modules qu'il a le droit de consulter.
4. Un élève ou un encadreur qui ouvre `/admin` est renvoyé vers son espace ; l'API lui refuse tout de toute
   façon.

**Tableau de bord** (`/admin`)

- Chiffres réels, avec l'heure de calcul : comptes par profil (élèves, encadreurs, collaborateurs) et par
  statut, inscriptions des 30 derniers jours, invitations en attente, exports du mois.
- Les indicateurs des modules à venir (clubs actifs, quiz joués, contenus en attente…) sont affichés comme
  « disponible avec le module X », jamais avec un chiffre inventé.
- Les dernières opérations du journal d'audit, si le collaborateur a le droit de le consulter.
- Des raccourcis vers les actions disponibles : inviter un collaborateur, chercher un inscrit, exporter.

**Collaborateurs et droits** (`/admin/collaborateurs`, super-administrateur uniquement)

1. Le super-administrateur clique sur « Inviter un collaborateur ». Il renseigne :
   - le nom, le prénom et l'e-mail, qui doit être unique ;
   - un rôle de départ, qui préremplit les droits : administrateur national, modérateur éditorial,
     gestionnaire de contenus, gestionnaire pédagogique, gestionnaire des clubs/DRE, gestionnaire de
     l'agenda et des campagnes, analyste ;
   - le périmètre : national, ou une DRE parmi les 7 ;
   - une date de fin d'accès, facultative.
2. Il ajuste les droits dans une matrice : modules en lignes, actions en colonnes (consulter, créer,
   modifier, soumettre, approuver, dépublier, exporter, gérer les utilisateurs, administrer les
   permissions).
3. Un e-mail part avec un lien d'activation valable 72 heures. Aucun mot de passe n'est envoyé par e-mail.
4. La personne ouvre le lien, choisit son identifiant et son mot de passe, puis, si ses droits sont
   sensibles, active la double authentification et note ses 10 codes de secours.
5. L'annuaire des collaborateurs montre chaque compte avec son statut, filtrable par rôle, e-mail, DRE et
   statut. Les statuts sont :
   - invitation envoyée ;
   - invitation expirée ;
   - actif ;
   - suspendu ;
   - révoqué.
6. Actions possibles sur un compte, chacune avec un motif obligatoire :
   - renvoyer l'invitation, ou l'annuler si elle est partie à la mauvaise adresse ;
   - modifier les droits ;
   - suspendre ou réactiver ;
   - révoquer ;
   - réinitialiser la double authentification.

   Suspendre ou révoquer coupe immédiatement toutes les sessions ouvertes.

7. **Revue des droits.** La liste des collaborateurs indique, pour chaque compte, la date de la dernière
   revue de ses droits. Le super-administrateur marque un compte « revu », ou ajuste ses droits.
8. **Gestion non déléguée.** Dans ce lot, seul un super-administrateur gère les collaborateurs et leurs
   droits. Ces actions ne figurent pas dans la grille des droits : un collaborateur ne peut donc ni s'en
   attribuer, ni en attribuer à un complice qu'il inviterait.

**Droits sensibles** : modération (approuver, dépublier), gestion des rôles et des permissions, export
nominatif, points, certification. Un compte qui en possède au moins un ne peut ouvrir l'espace admin
qu'avec la double authentification active.

**Annuaire des inscrits** (`/admin/inscrits`)

- Liste de tous les comptes : élèves, encadreurs, collaborateurs. Il n'y a pas encore de visiteurs.
- Recherche par nom, prénom, identifiant ou e-mail ; filtres par profil, statut et période d'inscription.
  Les filtres par club, DRE et établissement arrivent avec la spec 003.
- La fiche d'un compte montre ses informations et l'historique de ses changements de statut.
- Avec le droit « Utilisateurs : modifier », le collaborateur suspend ou réactive un élève ou un encadreur,
  avec un motif.
- Un collaborateur sans droit de consultation nominative ne voit pas cet écran. Il garde les statistiques
  agrégées du tableau de bord.

**Exports** (`/admin/exports`)

1. **Export agrégé** : nombre de comptes par profil, statut et mois d'inscription, en CSV ou XLSX. Ouvert
   aux droits « Statistiques : exporter ».
2. **Export nominatif**, réservé au droit « Inscrits : exporter », avec double authentification :
   1. Le collaborateur choisit les filtres de l'annuaire et coche les colonnes autorisées : identifiant,
      nom, prénom, e-mail, téléphone, profil, statut, date d'inscription, consentement.
   2. Il indique la finalité de l'extraction (texte obligatoire), voit le nombre de lignes, puis confirme.
   3. Le fichier, en CSV ou XLSX, se télécharge par un lien qui exige d'être connecté. Le lien vaut
      15 minutes ; le fichier est supprimé du serveur au bout de 24 heures.
3. **Historique des exports** : qui, quand, quels filtres, quelles colonnes, combien de lignes, quelle
   finalité, et l'état (prêt, téléchargé, expiré, échec).

**Journal d'audit** (`/admin/journal`)

- Chaque opération sensible y est inscrite avec sa date, son auteur, l'action, la cible et le périmètre :
  - invitations, activations, connexions et échecs de connexion des collaborateurs ;
  - changements de droits, suspensions, révocations ;
  - double authentification activée ou réinitialisée ;
  - exports demandés et téléchargés ;
  - changements de statut des inscrits.
- Filtres par auteur, action et période. Personne ne peut modifier ni supprimer une entrée, pas même le
  super-administrateur.

## Critères d'acceptation

Tous vérifiés par des tests de l'API ; les droits sont contrôlés côté serveur, l'interface ne fait que
refléter.

- [ ] Étant donné un super-administrateur, quand il invite un « gestionnaire de contenus » avec un e-mail,
      alors un e-mail d'invitation part avec un lien unique, et le compte est à l'état « invitation envoyée ».
- [ ] Étant donné ce lien, quand la personne choisit son identifiant et son mot de passe, alors le compte
      est actif. Un second usage du lien est refusé, et un lien de plus de 72 heures aussi.
- [ ] Étant donné ce gestionnaire de contenus actif, quand il appelle les routes de gestion des
      collaborateurs ou de modification des droits, alors l'API répond 403 et l'essai est journalisé.
- [ ] Étant donné un modérateur limité à la DRE Kara, quand il lit l'annuaire nominatif ou demande un
      export nominatif, alors l'API répond 403.
- [ ] Étant donné un collaborateur connecté, quand le super-administrateur le suspend, alors sa requête
      suivante est refusée (401), sans attendre la fin de sa session.
- [ ] Étant donné un collaborateur dont la date de fin d'accès est passée, quand il se connecte, alors
      l'accès est refusé.
- [ ] Étant donné un compte avec un droit sensible et sans double authentification, quand il appelle une
      route de l'espace admin, alors l'API répond 403 et demande d'activer la double authentification.
- [ ] Étant donné un compte avec double authentification, quand il saisit un mot de passe juste et un code
      faux, alors la session n'est pas créée. Un code de secours ne sert qu'une fois.
- [ ] Étant donné un analyste avec « Statistiques : exporter » mais sans « Inscrits : exporter », quand il
      demande l'export agrégé, alors il l'obtient ; quand il demande l'export nominatif, alors 403.
- [ ] Étant donné un super-administrateur, quand il exporte tous les inscrits en XLSX puis en CSV avec
      3 colonnes, alors le fichier ne contient que ces 3 colonnes et toutes les lignes filtrées, et l'opération
      apparaît dans l'historique et le journal.
- [ ] Étant donné un lien d'export, quand on l'ouvre sans session, avec la session d'un autre
      collaborateur, ou après 15 minutes, alors le téléchargement est refusé.
- [ ] Aucun export ne contient de mot de passe, d'empreinte, de jeton ou de secret de double
      authentification, quelles que soient les colonnes demandées.
- [ ] Le journal d'audit n'a aucune route de modification ni de suppression. Toute opération ci-dessus y
      laisse une entrée avec son auteur et sa date.
- [ ] Un élève ou un encadreur qui appelle une route `/api/admin/...` reçoit 403.
- [ ] Le tableau de bord n'affiche que des chiffres calculés par l'API, avec la date de calcul.

## Cas limites et erreurs

- **E-mail déjà utilisé** par un inscrit ou un collaborateur : l'invitation est refusée avec un message
  clair.
- **Service d'e-mail indisponible** : l'invitation est créée mais marquée « envoi échoué », et le
  super-administrateur peut la renvoyer. Hors production, sans SMTP configuré, le lien s'affiche dans
  l'espace admin et dans le terminal de l'API, pour tester.
- **Dernier super-administrateur** : il ne peut ni se suspendre, ni se révoquer, ni retirer son statut de
  super-administrateur. C'est vrai aussi quand deux super-administrateurs se retirent l'un l'autre au même
  instant : il en reste toujours au moins un.
- **Un collaborateur qui modifie ses propres droits** : refusé, même avec le droit d'administrer les
  permissions.
- **Invitation renvoyée** : l'ancien lien cesse de fonctionner.
- **Activation abandonnée en chemin** : quelqu'un choisit son mot de passe mais n'active pas la double
  authentification alors que ses droits l'exigent. Il ne peut alors ouvrir que la page d'activation de la
  double authentification.
- **Fin d'accès atteinte pendant une session** : la requête suivante est refusée et les sessions sont
  coupées.
- **Codes de double authentification** : 5 essais faux de suite bloquent l'étape 15 minutes, comme la
  connexion. Un code déjà utilisé dans la même fenêtre de 30 secondes est refusé (rejeu).
- **Téléphone perdu** : la personne utilise un code de secours, ou le super-administrateur réinitialise sa
  double authentification. Elle doit alors la réactiver à la connexion suivante.
- **Export vide** (aucune ligne) : on prévient avant la confirmation ; aucun fichier n'est créé.
- **Gros export** : jusqu'à 50 000 lignes. Au-delà, il faut affiner les filtres.
- **Injection de formules** : une cellule qui commence par `=`, `+`, `-` ou `@` est neutralisée dans les
  CSV et les XLSX.
- **Lien d'export** : il ne sert qu'une fois. Un second téléchargement demande un nouvel export.
- **Compte supprimé plus tard** : le journal garde le nom de l'auteur tel qu'il était au moment de
  l'action.
- **Réseau coupé ou API en panne** : l'espace admin affiche le message d'indisponibilité habituel et ne
  montre aucune donnée en cache.

## Hors périmètre

- Les autres modules du CDC admin (sections 4.2 et 5 à 12) : lots suivants, chacun avec sa spec.
- Les filtres par club, DRE et établissement de l'annuaire : avec la spec 003, quand ces données existeront.
- Les comptes visiteurs : il n'en existe pas encore.
- Les exports PDF et les rapports institutionnels périodiques.
- La connexion par un service tiers (Google, Microsoft…).
- Les sauvegardes techniques de la base, qui sont une tâche séparée de `TASKS.md`.

## Questions ouvertes

- Fournisseur SMTP : il faut l'hôte, le port, l'utilisateur et l'adresse d'expédition, à fournir comme
  variables d'environnement. Le développement peut avancer sans, avec le lien affiché hors production.
- Le CDC admin (§ 16) laisse à arbitrer qui peut faire l'export nominatif intégral, ses finalités et ses
  durées de conservation. Par défaut, seul le super-administrateur l'a, et l'historique est conservé 1 an.
  À confirmer avec un juriste avant l'ouverture, avec la question Q8 du PRD.

## Points d'attention (stress-test du 2026-11-04)

Corrections intégrées :

- La gestion des collaborateurs et des droits n'est pas délégable, pour éviter l'escalade de privilèges.
- Le journal n'a pas de lien vers les comptes : il garde l'identifiant et le nom de l'auteur. Supprimer un
  compte reste donc possible, et le journal reste inaltérable.
- Un verrou en base protège le dernier super-administrateur contre les retraits simultanés.
- La fin d'accès coupe les sessions dès la requête suivante.
- Le lien d'export est à usage unique.
- Un compte qui a des droits sensibles mais pas encore de double authentification est limité à la page
  d'activation de celle-ci.
- La revue des droits passe dans la liste des collaborateurs, plutôt que dans un écran séparé.

Risques acceptés :

- Un attaquant qui connaît le mot de passe d'un collaborateur peut bloquer l'étape du code 15 minutes,
  comme la connexion.
- Le jeton d'export apparaît dans l'adresse du téléchargement. Le risque est limité par l'usage unique,
  les 15 minutes de validité et la session du demandeur.
- Avec plusieurs processus d'API, la purge des exports tourne en double. C'est sans effet, puisque
  l'effacement peut se répéter.
