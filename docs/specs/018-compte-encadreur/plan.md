# 018 — Plan technique

## Approche

Un nouveau domaine d'API, **`backend/app/encadreurs/`**, construit comme celui des élèves (spec 017) :

- une table de profil `encadreur`, liée un à un à `utilisateur` ;
- l'inscription, l'espace et la file de vérification.

L'état de la vérification vit dans le profil (`en_attente`, `actif`, `refuse`), pas dans
`utilisateur.statut`. Le statut du compte garde son sens de la spec 015, la suspension, qui prime toujours.
Un encadreur en attente peut donc se connecter, voir son espace et corriger son profil, sans autre accès.

**Ce qui est partagé avec l'inscription élève.** Les mécanismes communs aux deux inscriptions quittent
`eleves/service.py` pour un module `app/comptes/inscription.py` :

- la limite par adresse ;
- le choix d'un établissement actif ;
- la proposition d'un établissement ;
- la traduction des doublons en 409 ;
- les exceptions `Refus`, `InscriptionsFermees` et `TropDInscriptions`.

Le comportement de l'inscription élève ne change pas, et ses tests le gardent.

**Le résumé des points** (`points_eleve` et ses schémas) passe dans le domaine `points`, sous le nom
`resume`. L'espace élève et l'espace encadreur s'en servent tous les deux.

**Activation.** Elle se fait en une transaction :

1. verrouiller le profil (`SELECT … FOR UPDATE`) ;
2. vérifier l'état et le statut du compte ;
3. passer le profil à « actif » ;
4. appeler `crediter("encadreur.bienvenue", cle="bienvenue:<id>")` ;
5. journaliser, puis valider.

Le verrou sérialise deux activations simultanées : la seconde trouve un profil déjà actif et répond 409. La
clé du registre garantit en plus une seule ligne de bienvenue, même après un refus suivi d'une activation.
L'e-mail part après la validation, sans faire échouer la décision s'il ne part pas.

**Un module de droits `encadreurs`**, plutôt que `inscrits:modifier`. Ce dernier est réservé au périmètre
national, parce que l'annuaire des inscrits contient des données nominatives (ADR-0008). Pour qu'un
collaborateur de DRE vérifie les encadreurs de sa région sans voir tout l'annuaire, la file a son propre
module :

- `consulter` : lire la file ;
- `approuver` : décider. Ce droit est sensible : il exige la double authentification, car un encadreur
  actif accédera plus tard aux données de ses élèves.

Un collaborateur national voit toute la file. Un collaborateur de DRE ne voit et ne décide que les demandes
des établissements de sa DRE ; pour une autre, l'API répond 404, comme si elle n'existait pas. C'est un
écart assumé à la règle « nominatif = national » de l'ADR-0008 : une note datée l'y consigne.

**Route réservée aux encadreurs actifs.** Une dépendance `encadreur_actif` refuse en 403 un encadreur en
attente ou refusé. Aucune route de R3 n'en a besoin, puisque les clubs n'existent pas encore. Les tests la
vérifient sur une route de test ; R4 et R5 l'utiliseront.

## Fichiers touchés

**Créés, API**

- `backend/app/encadreurs/models.py` : `Encadreur`, `Fonction`, `EtatVerification`.
- `backend/app/encadreurs/schemas.py` :
  - `InscriptionEncadreur` et `EspaceEncadreur` ;
  - `ProfilEncadreurModification` ;
  - `DemandeEncadreur` (une ligne de la file) et `Refus` (le motif).
- `backend/app/encadreurs/service.py` : `inscrire`, `espace`, `modifier_profil`, `renvoyer`.
- `backend/app/encadreurs/verification.py` : `file_attente`, `compter_en_attente`, `activer`, `refuser`.
  Ces fonctions filtrent par périmètre, et l'activation envoie l'e-mail.
- `backend/app/encadreurs/dependances.py` : `encadreur_actif`.
- `backend/app/encadreurs/router.py` : les routes publiques `/encadreurs` et les routes admin
  `/admin/encadreurs`.
- `backend/app/comptes/inscription.py` : les mécanismes partagés décrits plus haut.
- La migration `encadreurs`.
- Les tests (voir la section Tests).

**Modifiés, API**

- `app/eleves/service.py` : importe les mécanismes partagés. `points_eleve` part dans les points.
- `app/eleves/schemas.py` et `app/points/schemas.py` : `PointsEleve`, `SemestreEleve` et `LignePoints`
  deviennent `ResumePoints`, `SemestreResume` et `LignePoints`, dans `points`.
- `app/points/service.py` : `resume(db, utilisateur_id, nombre)`.
- `app/points/bareme.py` : `encadreur.bienvenue` rejoint `EN_SERVICE`.
- `app/admin/catalogue.py` :
  - le module `encadreurs` (`consulter`, `approuver`), et `approuver` dans `SENSIBLES` ;
  - le préréglage « Gestionnaire des clubs et DRE » reçoit les deux droits. Le préréglage de l'admin national
    les inclut, puisqu'il a tous les droits.
  - Les collaborateurs déjà créés ne changent pas : le super-administrateur leur ajoute le droit.
- `app/admin/inscrits.py` et `schemas.py` : la fiche d'un encadreur ajoute `encadreur: ProfilEncadreurAdmin`
  (fonction, établissement, état, demande, décision, motif, points). La recherche trouve aussi un téléphone.
  L'historique ajoute les nouvelles actions du journal.
- `app/admin/tableau_de_bord.py` : l'indicateur « Encadreurs à vérifier », compté dans le périmètre du
  collaborateur.
- `app/referentiel/administration.py` :
  - remplacer une proposition déplace aussi les encadreurs ;
  - la liste admin compte `nb_encadreurs`, à côté de `nb_eleves`.
- `app/comptes/creer_compte.py` : `--role` n'accepte plus `encadreur`.
- `app/seed_dev.py` :
  - `dev.encadreur` reçoit un profil actif et sa bienvenue ;
  - un second compte, `dev.encadreur.attente`, reste en attente, pour montrer la file.
- `app/main.py`, `alembic/env.py`.
- `backend/openapi.json` et `src/lib/api/schema.gen.ts`, régénérés.
- `docs/decisions/0008-…` : la note sur le périmètre DRE de la file.
- `docs/ARCHITECTURE.md` : le domaine `encadreurs`.

**Site**

- `src/routes/inscription.tsx` : choix du profil (deux grandes cartes « Je suis élève » et « Je suis
  encadreur »), lu dans `?profil=eleve|encadreur`. Le formulaire élève actuel part dans
  `src/components/inscription/InscriptionEleve.tsx`, sans changement de comportement.
- `src/components/inscription/InscriptionEncadreur.tsx` (créé) : le formulaire encadreur.
- `src/components/inscription/ChampEtablissement.tsx` (créé) : la recherche (`ChoixEtablissement`) et la
  proposition (DRE, IESG, nom), extraites du formulaire élève pour servir aux deux.
- `src/lib/fonctions.ts` (créé) : les libellés des fonctions.
- `src/routes/_connecte/mon-espace.tsx` : la vue encadreur remplace `EspaceSimple` pour ce rôle. Le
  dialogue du mot de passe est extrait pour servir aux deux vues.
- `src/components/espace/EspaceEncadreur.tsx` (créé) :
  - **en attente** : un encart avec la date de la demande, le profil et le bouton « Modifier » ;
  - **refusé** : le motif, la correction du profil et « Renvoyer ma demande » ;
  - **actif** : les cartes de points, les dernières lignes, le profil, et l'encart « Clubs bientôt ».
- `src/routes/_connecte/admin/encadreurs.tsx` (créé) : la file, avec deux onglets, « À vérifier » et
  « Refusés ».
  - Sur téléphone, une carte par demande ; sur ordinateur, un tableau.
  - « Activer » est un bouton vert, avec une confirmation. « Refuser » ouvre un dialogue où le motif est
    obligatoire.
- `src/routes/_connecte/admin.tsx` : le menu « Encadreurs » (icône `UserCheck`), visible avec
  `encadreurs:consulter`, avec un compteur des demandes en attente.
- `src/routes/_connecte/admin/index.tsx` : la carte « Encadreurs à vérifier », qui mène à la file.
- `src/routes/_connecte/admin/inscrits.$id.tsx` : la section « Encadreur ».
- `src/routes/_connecte/admin/referentiel.etablissements.tsx` : la colonne « Encadreurs ».
- `src/lib/api/client.ts` et `src/lib/admin.ts` : les fonctions, types et libellés du journal.

## Données

Une migration, non destructive : elle crée une table et passe une ligne du barème en service.

**`encadreur`**

| Colonne                            | Type        | Règle                                                           |
| ---------------------------------- | ----------- | --------------------------------------------------------------- |
| `utilisateur_id`                   | uuid        | clé primaire et clé étrangère `CASCADE`                         |
| `etablissement_id`                 | uuid        | clé étrangère `RESTRICT`, indexée                               |
| `fonction`                         | texte       | `enseignant`, `responsable`, `sante`, `accompagnateur`, `autre` |
| `fonction_precision`               | texte (100) | obligatoire si `autre`, nulle sinon (CHECK)                     |
| `etat`                             | texte       | `en_attente`, `actif`, `refuse`                                 |
| `demande_le`                       | horodatage  | date de la dernière demande ; la file la trie                   |
| `decide_le`, `decide_par`          |             | dernière décision ; `decide_par` en clé étrangère `SET NULL`    |
| `motif_refus`                      | texte (500) | obligatoire si `refuse`, nul sinon (CHECK)                      |
| `charte_version`                   | texte (20)  |                                                                 |
| `version`, `cree_le`, `modifie_le` |             | verrou optimiste, comme les élèves                              |

- Index partiel sur `demande_le` quand `etat = 'en_attente'` : c'est lui que lit la file.
- Le téléphone va dans `utilisateur.telephone`, qui existe déjà, et la date du consentement dans
  `utilisateur.consentement_le`.
- La migration passe `en_service = true` pour `encadreur.bienvenue` ; le retour arrière remet `false`.
- Les comptes encadreurs créés avant cette spec n'ont pas de profil. Leur espace l'indique (« Ton profil
  est incomplet, contacte l'équipe »), et ils n'ont aucun accès d'encadreur actif.

## API / interfaces

**Public**

| Route                           | Rôle                                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `GET /eleves/inscription`       | Inchangée. Elle sert aussi pour les encadreurs : `ouvertes` et `version_charte`.                                          |
| `POST /encadreurs/inscription`  | 201 avec `Moi` et le cookie de session. 403 si fermées, 409 si un champ est pris, 422 si invalide, 429                    |
| `GET /encadreurs/moi`           | Encadreur connecté : état, date de demande, motif s'il est refusé, profil ; points s'il est actif. 403 pour un autre rôle |
| `PATCH /encadreurs/moi`         | Téléphone, établissement (actif seulement), fonction et précision, avec `version`                                         |
| `POST /encadreurs/moi/renvoyer` | Fait repasser un refusé en attente ; 409 dans un autre état                                                               |

Corps de l'inscription :

- `prenom`, `nom`, `email` (obligatoire), `telephone?` ;
- `identifiant`, `mot_de_passe` ;
- `fonction`, `fonction_precision?` ;
- `charte` (vrai) et `consentement` (vrai) ;
- **soit** `etablissement_id`, **soit** `proposition {iesg_id, nom}`.

Le téléphone accepte de 8 à 15 chiffres, avec `+`, des espaces ou des tirets, et il est enregistré sans
les séparateurs.

**Admin**

| Route                                           | Droit                                  | Rôle                                                                 |
| ----------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------- |
| `GET /admin/encadreurs?etat=en_attente\|refuse` | `encadreurs:consulter`, filtré par DRE | La file, des plus anciennes demandes aux plus récentes ; `total`     |
| `POST /admin/encadreurs/{id}/activer`           | `encadreurs:approuver`, dans la DRE    | 409 si la demande n'est pas en attente ou si le compte est suspendu  |
| `POST /admin/encadreurs/{id}/refuser`           | `encadreurs:approuver`, dans la DRE    | Motif de 3 à 500 caractères ; 409 si la demande n'est pas en attente |
| `GET /admin/inscrits/{id}`                      | inchangé (national)                    | Ajoute `encadreur`                                                   |

Nouvelles actions du journal :

- `inscription_encadreur` ;
- `encadreur_active` et `encadreur_refuse` (avec le motif) ;
- `encadreur_redemande` ;
- `profil_encadreur_modifie` (avec les valeurs avant et après).

Chacune porte le périmètre de la DRE de l'établissement.

## Dépendances

Aucune nouvelle. L'e-mail passe par `app/admin/courriel.py`, qui existe déjà.

## Sécurité

- **Droits** : chaque route admin vérifie le droit, puis le périmètre sur la DRE de l'établissement
  **actuel** du profil, lu sous verrou au moment de la décision. Un encadreur qui change d'établissement
  pendant l'examen sort donc du périmètre d'une DRE qui n'est plus la sienne.
- **Double authentification** : `encadreurs:approuver` est un droit sensible.
- **Données personnelles** : le nom, l'e-mail et le téléphone ne sont lus que par l'encadreur lui-même et
  par les collaborateurs qui ont le droit, dans leur périmètre. Rien de public. Le téléphone est ajouté à la
  liste des données collectées dans `docs/SECURITY.md`.
- **Énumération** : l'inscription révèle qu'un e-mail ou un identifiant est pris (409), comme pour les
  élèves. La limite par adresse s'applique, partagée entre les deux profils.
- **Escalade** : l'API force le rôle `encadreur` et l'état `en_attente`. Aucun champ du corps de la
  requête ne les fixe, et le PATCH de l'espace ne touche ni l'état ni le rôle.
- **Suspension** : la connexion d'un compte suspendu est déjà refusée (spec 015), et l'activation d'un
  compte suspendu répond 409.

## Tests

En TDD pour la partie critique, l'activation et ses points (`docs/TESTING.md`) : les tests sont écrits
avant le code.

- `test_encadreurs_verification.py` :
  - l'activation écrit une ligne de bienvenue au montant du barème ;
  - deux activations simultanées n'en écrivent qu'une, et la seconde répond 409 ;
  - un refus suivi d'une activation ne donne toujours qu'une ligne ;
  - avec l'action désactivée, l'activation réussit sans ligne ;
  - hors semestre, la ligne est écrite sans semestre ;
  - un compte suspendu ne s'active pas (409) ;
  - un refus sans motif répond 422 ;
  - périmètre : la DRE A ne voit ni ne décide une demande de la DRE B (404), le national voit tout ;
  - un collaborateur sans le droit reçoit 403, et un droit sans double authentification aussi ;
  - chaque décision est au journal.
- `test_encadreurs_inscription.py` :
  - l'inscription valide crée un compte en attente, sans point ;
  - l'e-mail est obligatoire ;
  - un e-mail ou un identifiant pris répond 409 ;
  - inscriptions fermées : 403 ; limite partagée avec les élèves : 429 ;
  - la proposition d'établissement fonctionne ;
  - la précision est exigée pour « autre » ;
  - le téléphone est normalisé ;
  - le rôle et l'état ne peuvent pas être forcés.
- `test_encadreurs_espace.py` :
  - l'espace dans chacun des trois états ;
  - la modification du profil, avec un conflit de version ;
  - renvoyer une demande refusée, et 409 dans un autre état ;
  - `encadreur_actif` sur une route de test ;
  - un élève qui appelle l'espace encadreur reçoit 403 ;
  - un encadreur sans profil voit le message prévu.
- **Non-régression** :
  - les tests de l'inscription élève passent sans changement de comportement ;
  - remplacer une proposition déplace aussi les encadreurs ;
  - `test_seed_dev.py` est mis à jour.
- **Site** : un test Vitest de la normalisation du téléphone. Le reste est vérifié dans le navigateur, sur
  ordinateur et sur téléphone.

## Risques

- **Extraction du code partagé** : déplacer les mécanismes d'inscription pourrait casser l'inscription
  élève. Les 401 tests existants la couvrent, et on les lance juste après l'extraction, avant toute
  nouveauté.
- **Renommage des types de points** : le site doit suivre. `tsc` le signale.
- **Périmètre DRE sur des données nominatives** : c'est l'écart consigné dans l'ADR-0008. Il reste limité à
  la file, à la double authentification, et au journal.
- **Collaborateurs déjà créés** : ils n'ont pas le nouveau droit tant que le super-administrateur ne l'a pas
  ajouté. Sur la préprod et la prod, il faudra le donner à l'équipe nationale après le déploiement. Je le
  noterai dans la clôture.
