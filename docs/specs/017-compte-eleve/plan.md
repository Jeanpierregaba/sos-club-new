# 017 — Plan technique

## Approche

Deux nouveaux domaines d'API :

- **`backend/app/points/`** : le registre, les semestres et le barème (ADR-0004). Il expose une seule
  fonction d'écriture, `crediter`, et les calculs de totaux. Toutes les specs suivantes l'appellent.
- **`backend/app/eleves/`** : le profil de l'élève (pseudonyme, classe, établissement), l'inscription et
  son espace.

Le profil est une table `eleve` liée un à un à `utilisateur`, au lieu de colonnes ajoutées à
`utilisateur`. La table `utilisateur` sert aux trois rôles : l'encadreur aura sa propre table en R3,
et les colonnes propres à l'élève n'ont pas à y être vides pour les autres.

L'inscription est **une seule transaction**, qui crée :

- l'utilisateur ;
- le profil ;
- la proposition d'établissement, s'il y en a une ;
- la ligne de bienvenue ;
- la session.

Si une étape échoue, rien n'est écrit. `crediter` ne valide jamais la transaction : c'est l'appelant qui
le fait, pour que le gain et l'action qui le déclenche soient écrits ensemble.

Choix techniques :

- **Idempotence par la base** : `crediter` fait un `INSERT … ON CONFLICT (cle) DO NOTHING RETURNING`.
  Deux appels simultanés avec la même clé n'écrivent qu'une ligne, sans verrou applicatif.
- **Le montant est copié** du barème dans la ligne. Une ligne n'est jamais modifiée ; une annulation sera
  une ligne négative qui pointe vers la ligne annulée (colonne prévue, sans écran avant R13).
- **Semestres sans chevauchement garantis par la base** : contrainte d'exclusion PostgreSQL
  `EXCLUDE USING gist (daterange(debut, fin, '[]') WITH &&)`. Elle n'a besoin d'aucune extension, car on
  compare seulement des intervalles. Le Togo est à UTC+0 toute l'année : la date UTC est la date locale, et
  le semestre d'une ligne se déduit de sa date de création.
- **Pseudonyme** : colonne `pseudonyme` pour l'affichage, et `pseudonyme_normalise` unique, calculée par le
  `normaliser` de la spec 016 avec les espaces retirés. Ainsi « Aya K » et « ayak » sont le même
  pseudonyme.
- **Inscriptions ouvertes ou fermées** : réglage `inscriptions_ouvertes` de la configuration, `None` par
  défaut. `None` veut dire : ouvertes en local, fermées dès que le site est en HTTPS (préproduction et
  production). La préproduction l'ouvre par `INSCRIPTIONS_OUVERTES=true` dans son `.env`.
- **Limite par adresse** : on réutilise la table `tentative_connexion` de la spec 001, avec une clé fixe
  `inscription`. La purge d'une heure existe déjà. Le seuil vaut 20 par heure et par adresse, et il est
  réglable : une salle informatique partage souvent une seule adresse. La spec est ajustée en ce sens.
- **Verrou optimiste** sur le profil, le barème et les semestres, avec `version_id_col` comme dans la
  spec 016.

## Fichiers touchés

**Créés, API**

- `backend/app/points/models.py` : `Semestre`, `LigneBareme`, `MouvementPoints`.
- `backend/app/points/service.py` :
  - `crediter(db, action, utilisateur_id, cle, *, valide_par=None)` : renvoie la ligne écrite, ou `None`
    si l'action est inactive, à 0 ou déjà créditée ;
  - `semestre_en_cours(db, jour)` ;
  - `totaux(db, utilisateur_id)` : semestre en cours et historique ;
  - `dernieres_lignes(db, utilisateur_id, n)`.
- `backend/app/points/administration.py` : lister, créer et modifier les semestres ; lister et modifier le
  barème. Chaque changement est journalisé avec la valeur avant et après.
- `backend/app/points/bareme.py` : la grille initiale du PRD (code, bénéficiaire, libellé, montant, ordre).
  La migration en garde une copie figée, comme pour la spec 016.
- `backend/app/points/schemas.py`, `backend/app/points/router.py` : routes admin `/admin/points`.
- `backend/app/eleves/models.py` : `Eleve`, `Classe` (6e, 5e, 4e, 3e, 2nde, 1re, Tle).
- `backend/app/eleves/pseudonyme.py` : nettoyage, normalisation, refus d'un e-mail, d'un numéro de
  téléphone (6 chiffres ou plus) ou d'un mot de la liste interdite (courte liste en français, enrichie par
  l'équipe).
- `backend/app/eleves/service.py` : `inscrire`, `espace`, `modifier_profil`.
- `backend/app/eleves/administration.py` : `imposer_pseudonyme`, `reinitialiser_mot_de_passe`,
  `remplacer_proposition` (déplace les élèves d'un établissement proposé).
- `backend/app/eleves/schemas.py`, `backend/app/eleves/router.py` : routes publiques `/eleves` et routes
  admin `/admin/inscrits/{id}/…`.
- La migration `points_et_eleves`.
- Les tests (voir la section Tests).

**Modifiés, API**

- `app/config.py` : `inscriptions_ouvertes`, `inscriptions_max_adresse` (20), `version_charte`.
- `app/comptes/service.py` : `creer_compte` est découpé. Une fonction `preparer_utilisateur` valide et
  ajoute sans valider la transaction ; `inscrire` l'utilise. `changer_mot_de_passe` coupe les autres
  sessions.
- `app/comptes/router.py` : `POST /comptes/mot-de-passe` (mot de passe actuel et nouveau), pour tous les
  rôles.
- `app/admin/catalogue.py` : le module `points` devient disponible.
- `app/admin/inscrits.py` et `schemas.py` : la fiche d'un élève ajoute son profil, ses totaux et ses
  50 dernières lignes ; la recherche trouve aussi un pseudonyme.
- `app/admin/tableau_de_bord.py` : indicateur « Semestre en cours », ou une alerte s'il n'y en a pas.
- `app/referentiel/administration.py` et `schemas.py` : la liste admin des établissements ajoute
  `nb_eleves`. Accepter une proposition passe par le `PATCH` existant (`statut: actif`).
- `app/seed_dev.py` : un semestre en cours, un profil pour chaque élève `dev.*` et leur ligne de bienvenue.
- `app/main.py`, `alembic/env.py`, `deploy/env.example` (`INSCRIPTIONS_OUVERTES`).
- `backend/openapi.json` et `src/lib/api/schema.gen.ts`, régénérés.

**Site**

- `src/routes/inscription.tsx` (créé) : le formulaire.
  - L'établissement se cherche avec `chercherEtablissements`.
  - Le lien « Je ne trouve pas mon établissement » ouvre la proposition : DRE, puis IESG (lues dans
    `chargerDre`), puis le nom.
  - Inscriptions fermées : la page l'explique, sans formulaire.
  - Un élève déjà connecté est renvoyé vers son espace.
- `src/routes/charte.tsx` (créé) : la charte des Clubs Santé. Le texte est provisoire et signalé comme
  tel, tiré de `docs/RULES.md` (respect, pseudonyme, modération, pas de données personnelles). Le porteur du
  projet le validera ; sa version est celle de `version_charte`.
- `src/routes/_connecte/mon-espace.tsx` : vue élève.
  - Cartes « Points du semestre » et « Total » ; liste des dernières lignes.
  - Profil, avec un dialogue de modification (classe, établissement, e-mail) et le changement de mot de
    passe.
  - Les vues encadreur et admin ne changent pas.
- `src/routes/connexion.tsx` : « Pas encore de compte ? » mène à `/inscription`.
- `src/routes/_connecte/admin/points.tsx`, `points.semestres.tsx` et `points.bareme.tsx` (créés) :
  onglets, comme `/admin/referentiel`. Menu admin « Points », visible avec `points:consulter`.
- `src/routes/_connecte/admin/inscrits.$id.tsx` : section « Élève » (profil, totaux, registre) ; boutons
  « Imposer un pseudonyme » et « Réinitialiser le mot de passe », avec motif. Le mot de passe
  provisoire s'affiche une seule fois, avec un bouton pour le copier.
- `src/routes/_connecte/admin/referentiel.etablissements.tsx` : colonne « Élèves » ; pour un
  établissement proposé, les boutons « Accepter » et « Remplacer par… », qui ouvre une recherche.
- `src/lib/api/client.ts` : fonctions et types correspondants. `src/lib/admin.ts` : libellés des
  nouvelles actions du journal.
- `src/lib/classes.ts` (créé) : les libellés des classes.

## Données

Une migration, non destructive : elle ne fait qu'ajouter.

**`semestre`**

| Colonne                            | Type       | Règle                                         |
| ---------------------------------- | ---------- | --------------------------------------------- |
| `id`                               | uuid       | clé primaire                                  |
| `libelle`                          | texte (60) | unique, par exemple « 2026-2027, semestre 1 » |
| `debut`, `fin`                     | date       | `fin >= debut` ; exclusion de chevauchement   |
| `version`, `cree_le`, `modifie_le` |            | comme la spec 016                             |

**`bareme`**

| Colonne                                   | Type        | Règle                                                                      |
| ----------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| `code`                                    | texte (60)  | clé primaire, par exemple `eleve.bienvenue`, `club.article_eleve`          |
| `beneficiaire`                            | texte       | `eleve`, `encadreur` ou `club`                                             |
| `libelle`                                 | texte (120) |                                                                            |
| `montant`                                 | entier      | de 0 à 10 000                                                              |
| `propose`                                 | booléen     | montant encore à valider par les organisateurs (Q22), affiché dans l'écran |
| `en_service`    | booléen     | vrai quand une spec livrée écrit déjà cette action ; la migration de chaque spec le passe à vrai |
| `actif`, `ordre`, `version`, `modifie_le` |             |                                                                            |

Préremplie avec toutes les lignes du barème du PRD.

**`mouvement_points`**

| Colonne          | Type        | Règle                                                                     |
| ---------------- | ----------- | ------------------------------------------------------------------------- |
| `id`             | uuid        | clé primaire                                                              |
| `utilisateur_id` | uuid        | clé étrangère `RESTRICT`, non nulle (R4 ajoutera `club_id` et assouplira) |
| `action`         | texte (60)  | clé étrangère vers `bareme.code`                                          |
| `montant`        | entier      | copié du barème ; négatif seulement pour une annulation                   |
| `semestre_id`    | uuid, nul   | clé étrangère ; nulle hors semestre                                       |
| `cle`            | texte (200) | unique : idempotence (`bienvenue:<id>`)                                   |
| `valide_par`     | uuid, nul   | collaborateur qui a validé l'action, s'il y en a un                       |
| `annule_id`      | uuid, nul   | ligne annulée, unique (une ligne ne s'annule qu'une fois)                 |
| `cree_le`        | horodatage  |                                                                           |

Index `(utilisateur_id, semestre_id)`. Aucune route ne modifie ni ne supprime une ligne.

**`eleve`**

| Colonne                 | Type       | Règle                                   |
| ----------------------- | ---------- | --------------------------------------- |
| `utilisateur_id`        | uuid       | clé primaire et clé étrangère `CASCADE` |
| `pseudonyme`            | texte (30) |                                         |
| `pseudonyme_normalise`  | texte (30) | unique                                  |
| `classe`                | texte      | `6e` … `tle`                            |
| `etablissement_id`      | uuid       | clé étrangère `RESTRICT`, indexée       |
| `charte_version`        | texte (20) | version acceptée                        |
| `version`, `modifie_le` |            |                                         |

`utilisateur.consentement_le`, qui existe déjà, reçoit la date du consentement du parent ou tuteur.

## API / interfaces

**Public**

| Route                        | Rôle                                                                                                                                                           |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /eleves/inscription`    | `{ouvertes, version_charte}`                                                                                                                                   |
| `POST /eleves/inscription`   | 201 avec `Moi` et le cookie de session. 403 si fermées, 409 si un champ est déjà pris (le message nomme le champ), 422 si invalide, 429 si trop d'inscriptions |
| `GET /eleves/moi`            | Élève connecté : profil, totaux, semestre en cours, 20 dernières lignes. 403 pour un autre rôle                                                                |
| `PATCH /eleves/moi`          | Classe, établissement (actif seulement), e-mail, avec `version`                                                                                                |
| `POST /comptes/mot-de-passe` | Mot de passe actuel et nouveau ; coupe les autres sessions                                                                                                     |

Corps de l'inscription : `prenom`, `nom`, `pseudonyme`, `identifiant`, `mot_de_passe`, `email?`, `classe`,
`charte` (vrai), `consentement_parent` (vrai), et **soit** `etablissement_id`, **soit**
`proposition {iesg_id, nom}`.

**Admin**

| Route                                                                             | Droit                                                           |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `GET /admin/points/semestres`, `GET /admin/points/bareme`                         | `points:consulter`                                              |
| `POST /admin/points/semestres`, `PATCH …/semestres/{id}`, `PATCH …/bareme/{code}` | `points:modifier` (double authentification)                     |
| `POST /admin/inscrits/{id}/pseudonyme` `{pseudonyme, motif}`                      | `inscrits:modifier`                                             |
| `POST /admin/inscrits/{id}/mot-de-passe` `{motif}` → `{mot_de_passe}`             | `inscrits:modifier`                                             |
| `POST /admin/referentiel/etablissements/{id}/remplacer` `{cible_id, version}`     | `clubs:modifier`, dans le périmètre DRE des deux établissements |

Nouvelles actions du journal :

- `inscription_eleve`, `profil_eleve_modifie`, `mot_de_passe_change` (dans le compte de l'élève) ;
- `pseudonyme_impose`, `mot_de_passe_reinitialise` ;
- `semestre_cree`, `semestre_modifie`, `bareme_modifie` ;
- `etablissement_remplace`.

## Dépendances

Aucune. On réutilise :

- `email-validator`, Argon2 et la limite d'essais de la spec 001 ;
- la normalisation de la spec 016 ;
- les composants admin de la spec 016 (`DialogueFormulaire`, `Champ`).

## Sécurité

- **Mineurs (SECURITY, RULES)**
  - `GET /eleves/moi` ne renvoie que les données de l'élève connecté.
  - Aucune route publique ne renvoie le prénom, le nom ou l'identifiant d'un élève.
  - Le pseudonyme est la seule identité publique, et il ne peut pas être l'identifiant.
- **Fausses inscriptions**
  - Limite par adresse.
  - Les deux cases sont vérifiées par l'API.
  - La bienvenue est idempotente par compte. Un même élève avec plusieurs comptes reste possible : c'est
    la détection d'anomalies de R22, signalée en risque.
- **Points**
  - Une seule fonction écrit au registre ; aucune route ne le modifie.
  - Les changements du barème et des semestres exigent la double authentification et sont journalisés.
- **Réinitialisation du mot de passe**
  - Le mot de passe provisoire fait 12 caractères, sans caractères ambigus, et il est tiré par `secrets`.
  - Il est renvoyé une seule fois, jamais journalisé.
  - Les sessions de l'élève sont coupées.
- **Établissements proposés**
  - Invisibles des listes publiques : elles filtrent déjà sur `actif`.
  - Le nom proposé passe par le `nettoyer` de la spec 016, à 150 caractères au plus.
- **Données réelles** : inscriptions fermées par défaut dès que le site est en HTTPS (RULES, récépissé de
  l'IPDCP).

## Tests

TDD pour les points, partie critique de `docs/TESTING.md`. Le sous-agent `test-writer` écrit les tests
avant le code.

- **`test_points.py`**
  - Crédit simple : montant copié, semestre trouvé, ou nul hors semestre.
  - Action inactive ou à 0 : aucune ligne.
  - Même clé deux fois : une ligne. Même clé en deux sessions simultanées (`asyncio.gather`) : une ligne.
  - Barème modifié : les anciennes lignes ne changent pas.
  - Totaux du semestre et historique.
- **`test_points_admin.py`**
  - Droits : consulter, modifier, double authentification.
  - Semestres : chevauchement refusé par la base même en écritures simultanées, fin avant début,
    semestre commencé figé sauf prolongation, conflit de version.
  - Barème : bornes du montant.
  - Journal avec la valeur avant et après.
- **`test_eleves_inscription.py`**
  - Parcours complet : session, profil, ligne de bienvenue.
  - Cases non cochées, champs pris (message par champ, majuscules et accents du pseudonyme), pseudonyme
    interdit ou égal à l'identifiant.
  - Établissement inactif ou inconnu.
  - Proposition : nouvelle, déjà proposée (réutilisée), déjà active (refus).
  - Inscriptions fermées, limite par adresse, élève déjà connecté.
  - Échec au milieu : rien n'est écrit.
- **`test_eleves_espace.py`**
  - `GET` et `PATCH /eleves/moi` : propres données seulement, autre rôle refusé, établissement inactif
    refusé, conflit de version.
  - Changement de mot de passe : il coupe les autres sessions.
- **`test_eleves_admin.py`**
  - Imposer un pseudonyme, réinitialiser le mot de passe (sessions coupées, mot de passe absent du
    journal).
  - Remplacer une proposition (élèves déplacés, périmètre DRE, journal).
  - Fiche d'un élève dans les inscrits.
- **Site (Vitest)** : la validation locale du pseudonyme, qui reprend les règles de l'API pour un message
  immédiat.
- **Navigateur**
  - Inscription complète sur téléphone, avec et sans proposition.
  - Espace de l'élève.
  - Écrans admin Points et fiche d'un élève.
  - Inscriptions fermées.

## Risques

- **Une salle informatique derrière une seule adresse** peut atteindre la limite. Le seuil est réglable
  (20 par heure) ; si besoin, on l'augmentera pendant une session d'inscription encadrée.
- **Comptes multiples d'un même élève** pour cumuler la bienvenue. Rien ne l'empêche avant R22 :
  détection, signalement et ligne négative.
- **Texte de la charte** : il est provisoire et doit être validé par le porteur du projet et par un juriste
  avec le consentement (Q8). Changer sa version ne force pas encore les élèves inscrits à l'accepter de
  nouveau ; ce sera à traiter si le texte change après l'ouverture.
- **Mot de passe provisoire** : l'élève n'est pas obligé de le changer. Le message de l'admin le lui
  recommande ; une obligation pourra suivre avec R5 (réinitialisation par l'encadreur).
- **Le barème contient des actions qui n'existent pas encore** : la colonne `en_service` les signale « Pas encore
  utilisée », pour que l'admin ne croie pas qu'elles rapportent déjà.
