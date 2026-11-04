# 016 — Plan technique

## Approche

On crée un nouveau domaine d'API, `backend/app/referentiel/`, qui détient les quatre tables (DRE, IESG,
établissement, axe). Il expose deux faces :

- des listes publiques en lecture, sans compte ;
- des routes d'administration sous `/admin/referentiel`, protégées par les dépendances de la spec 015
  (`exiger_permission`, `exiger_super_admin`).

Le chargement initial est une migration Alembic de données. Elle lit un fichier JSON tiré une fois pour
toutes de l'annuaire du site, puis le site lit ses listes dans l'API et perd ses fichiers de données.

Pourquoi ainsi plutôt que garder les listes dans le site :

- la DRE d'un club, son classement et le périmètre d'un collaborateur doivent venir de la même source (Q2) ;
- seule l'API peut garantir l'intégrité, avec des clés étrangères vers les DRE, les IESG et les
  établissements.

Choix techniques :

- **Codes stables** pour les DRE et les axes, qui servent de clé primaire : `grand-lome`, `genie-imhotep`.
  Les périmètres existants (`collaborateur.perimetre_dre`) gardent ainsi leurs valeurs, et la migration
  n'a qu'à ajouter une clé étrangère.
- **UUID** pour les IESG et les établissements, qui n'ont pas de code officiel.
- **Nom normalisé** : une colonne `nom_normalise`, calculée en Python (sans accents, en minuscules, espaces
  réduits), porte l'unicité et la recherche. On n'a pas besoin de l'extension `unaccent`, dont la
  fonction ne peut pas servir dans un index unique. Avec moins de 1 000 lignes, une recherche `LIKE` mot à
  mot suffit, sans index trigramme.
- **Verrou optimiste** : chaque table a une colonne `version`. Le formulaire renvoie la version qu'il a lue ;
  si elle a changé, l'API répond 409. Le `version_id_col` de SQLAlchemy couvre en plus l'écart entre la
  lecture et l'écriture.
- **Une seule mise à jour par élément** : `PATCH` modifie les champs, déplace l'élément et le désactive ou le
  réactive. Les garde-fous vivent dans `service.py` et chaque changement écrit une entrée de journal avec
  la valeur avant et après.

## Fichiers touchés

**Créés, API**

- `backend/app/referentiel/__init__.py`
- `backend/app/referentiel/models.py` : `Dre`, `Iesg`, `Etablissement`, `Axe`, les énumérations
  `TypeEtablissement` (lycee, college, complexe, autre) et `StatutEtablissement` (actif, inactif, propose).
- `backend/app/referentiel/normalisation.py` : `normaliser(nom)` et `nettoyer(nom)`. Le second retire les
  espaces en trop et refuse un nom vide.
- `backend/app/referentiel/schemas.py` : les sorties publiques et admin, les entrées de création et de
  modification, avec leurs validations (longueur, code en `[a-z0-9-]`).
- `backend/app/referentiel/service.py` : les listes publiques et la recherche.
- `backend/app/referentiel/administration.py` : les créations, `modifier_*` avec les garde-fous, le
  contrôle du périmètre DRE et la journalisation (séparées des listes publiques en cours de route).
- `backend/app/referentiel/router.py` : `router_public` (`/referentiel`) et `router_admin`
  (`/admin/referentiel`).
- `backend/app/referentiel/chargement.py` : `charger(connexion, *, etablissements=True)`. Ce chargement
  tolère d'être relancé (`INSERT … ON CONFLICT DO NOTHING`) ; la migration et les tests l'appellent tous
  les deux.
- `backend/alembic/donnees/annuaire.json` : 7 DRE (code, nom, nom complet, ordre), 19 IESG (DRE, nom,
  zone), 844 établissements (IESG, nom, type), 7 axes (code, libellé, description, ordre). Le chargement
  retire les 6 doublons.
- `backend/alembic/versions/xxxx_referentiel.py` : la migration.
- `backend/tests/test_referentiel_public.py`, `test_referentiel_admin.py`, `test_referentiel_chargement.py`.

**Créés, site**

- `src/routes/_connecte/admin/referentiel.tsx` : la mise en page à onglets.
- `src/routes/_connecte/admin/referentiel.index.tsx` : l'onglet DRE et IESG.
- `src/routes/_connecte/admin/referentiel.etablissements.tsx` : liste paginée, filtres dans l'URL, création
  et modification dans un dialogue.
- `src/routes/_connecte/admin/referentiel.axes.tsx`.

**Modifiés**

- `backend/app/main.py` : inclut les deux routeurs.
- `backend/app/admin/catalogue.py` : le module `clubs` devient disponible et le dictionnaire `DRE` disparaît.
- `backend/app/admin/models.py` : la contrainte `perimetre_dre_connue` devient une clé étrangère vers
  `dre.code`.
- `backend/app/admin/schemas.py` et `collaborateurs.py` :
  - le validateur `dre_connue` est remplacé par un contrôle en base, qui exige une DRE active ;
  - `Catalogue` sert `dre` (toutes les DRE, pour l'affichage) et `dre_actives` (pour les sélecteurs).
- `backend/app/admin/tableau_de_bord.py` : ajoute les indicateurs « DRE actives » et « Établissements
  actifs ».
- `backend/tests/conftest.py` : après chaque `TRUNCATE`, recharge les DRE, les IESG et les axes (33 lignes),
  dont les périmètres des collaborateurs ont besoin. Une fixture `annuaire` charge en plus les
  établissements pour les tests qui en ont besoin.
- `src/lib/api/client.ts` et `schema.gen.ts` : les nouveaux types et appels.
- `src/lib/togo-dre.ts` : ne garde que le dessin, indexé par code de DRE (`d`, `label`, `couleur`).
- `src/routes/_connecte/admin.tsx` : l'entrée « Référentiel » du menu, visible avec `clubs:consulter` ou
  pour le super-administrateur.
- `src/routes/_connecte/admin/collaborateurs.index.tsx` et `collaborateurs.$id.tsx` : les sélecteurs
  utilisent `dre_actives`.
- `src/routes/carte-des-clubs.tsx`, `src/components/ClubsSection.tsx`,
  `src/routes/genie-imhotep/inscription.tsx` : les données viennent des loaders de route, plus des
  imports en dur. Recherche et regroupements de la carte dans `src/lib/carte-des-clubs.ts`.
- `src/routes/genie-imhotep/hall-of-fame.tsx` : garde les noms des régions du championnat
  (`nomsRegions`) et prend leurs couleurs dans le dessin de la carte.
- `docs/ARCHITECTURE.md` : le domaine `referentiel` et le modèle de données.
- `docs/RULES.md` : « On ne supprime pas un élément du référentiel, on le désactive. »

**Supprimés**

- `src/lib/etablissements.ts`.

## Données

Une migration, `referentiel`, non destructive :

| Table           | Colonnes                                                                                                         | Contraintes                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `dre`           | `code` (PK, varchar 30), `nom`, `nom_complet`, `ordre`, `actif`, `version`, `cree_le`, `modifie_le`              | `nom` unique ; `code ~ '^[a-z0-9-]+$'`                          |
| `iesg`          | `id` (UUID), `dre_code` (FK), `nom`, `nom_normalise`, `zone` (facultatif), `actif`, `version`, dates             | unique (`dre_code`, `nom_normalise`)                            |
| `etablissement` | `id` (UUID), `iesg_id` (FK), `nom`, `nom_normalise`, `type`, `localite` (facultatif), `statut`, `version`, dates | unique (`iesg_id`, `nom_normalise`) ; index sur `nom_normalise` |
| `axe`           | `code` (PK), `libelle`, `description` (300 car.), `ordre`, `actif`, `version`, dates                             | `libelle` unique ; `code ~ '^[a-z0-9-]+$'`                      |

- Les noms sont limités à 150 caractères.
- Les clés étrangères sont en `ON DELETE RESTRICT` : rien ne se supprime.
- Sur `collaborateur`, on retire le `CHECK perimetre_dre_connue` et on ajoute une clé étrangère
  `perimetre_dre → dre.code`. Le chargement des DRE passe avant, donc les périmètres existants restent
  valides.
- Le retour en arrière remet le `CHECK` et supprime les quatre tables. Les tests font déjà l'aller-retour.

Codes des 7 axes, dans l'ordre de la page `/les-7-axes` : `genie-imhotep`, `sante-sexuelle-evss`,
`production-tv-medias`, `sport-secourisme`, `bourses-excellence`, `leadership-mentorat`,
`sante-environnement`. Leur description courte reprend la phrase de la page.

## API / interfaces

**Public**, sans compte. Ne renvoie que les éléments actifs, sans auteur ni dates.

| Route                                 | Réponse                                                                                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /api/referentiel/dre`            | DRE dans l'ordre, chacune avec ses IESG (id, nom, zone, nombre d'établissements) et son total.                                          |
| `GET /api/referentiel/annuaire`       | Le même arbre, avec les établissements (id, nom, type) : environ 40 Ko, pour la carte, qui cherche sans aller-retour.                   |
| `GET /api/referentiel/etablissements` | `?iesg=` : tous ceux de l'IESG. `?recherche=` (2 lettres au moins, 20 résultats au plus, `?dre=` facultatif). L'un des deux est requis. |
| `GET /api/referentiel/axes`           | Code, libellé, description, ordre.                                                                                                      |

**Admin.** Sans les droits demandés, l'API répond 403 et journalise le refus, comme dans la spec 015.

| Route                                                   | Droit                                                                                                           |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `GET /api/admin/referentiel/dre`                        | `clubs:consulter`. Liste aussi les éléments inactifs ; un collaborateur limité à une DRE ne voit que la sienne. |
| `POST /api/admin/referentiel/dre`, `PATCH …/dre/{code}` | super-administrateur                                                                                            |
| `POST /api/admin/referentiel/iesg`, `PATCH …/iesg/{id}` | super-administrateur                                                                                            |
| `GET /api/admin/referentiel/etablissements`             | `clubs:consulter` ; paginé par 50 ; filtres `recherche`, `dre`, `iesg`, `type`, `statut`, limités au périmètre. |
| `POST /api/admin/referentiel/etablissements`            | `clubs:creer` ; l'IESG cible doit être dans le périmètre.                                                       |
| `PATCH /api/admin/referentiel/etablissements/{id}`      | `clubs:modifier` ; l'établissement et son IESG cible doivent être dans le périmètre.                            |
| `GET`, `POST`, `PATCH /api/admin/referentiel/axes…`     | lecture avec `clubs:consulter` ; écriture par le super-administrateur.                                          |

Dans le journal :

- les actions s'appellent `referentiel_cree`, `referentiel_modifie`, `referentiel_desactive` et
  `referentiel_reactive` ;
- `cible_type` vaut `dre`, `iesg`, `etablissement` ou `axe` ;
- `details` contient `{avant, apres}`, limité aux champs changés.

Codes de retour :

- 409 pour un doublon ou une version périmée ;
- 422 pour une valeur invalide ;
- 400, avec un message explicite, pour un garde-fou : enfants actifs, dernier axe, DRE utilisée comme
  périmètre, cible inactive.

**Site**

- La carte charge `annuaire` dans son loader, en rendu serveur, et garde sa recherche instantanée.
- L'accueil (`ClubsSection`) et le formulaire du Génie Imhotep chargent `dre`.
- Si l'API ne répond pas, la page s'affiche quand même :
  - la carte garde ses contours et affiche « liste momentanément indisponible » ;
  - les autres pages masquent le bloc concerné.

## Dépendances

Aucune nouvelle bibliothèque. La normalisation utilise `unicodedata`, de la bibliothèque standard.

## Sécurité

- Le contrôle d'accès est fait dans l'API, sur chaque route d'écriture, pour la ressource visée. Pour un
  établissement, le périmètre se vérifie sur la DRE de son IESG actuelle et sur celle de l'IESG cible
  (ADR-0003, ADR-0008).
- Les listes publiques ne contiennent aucune donnée personnelle : on publie des noms d'établissements
  publics.
- Les entrées sont validées par Pydantic : longueur, motif des codes, `extra="forbid"`. Les messages
  d'erreur ne donnent aucun détail interne.
- Le journal d'audit trace toutes les écritures, comme les refus.
- Les listes publiques gardent le `Cache-Control: no-store` commun à `/api`. Une mise en cache viendra si
  la charge le demande.

## Tests

- **Chargement** (`test_referentiel_chargement.py`) :
  - le chargement donne 7, 19, 838 et 7 lignes ;
  - le relancer ne change pas les nombres ;
  - les nombres par IESG sont ceux de la carte, moins les doublons ;
  - les périmètres des collaborateurs survivent à la migration.
- **Public** : éléments inactifs absents ; recherche « lycee tokoin » ; moins de 2 lettres refusé (422) ;
  20 résultats au plus ; aucun champ admin dans les réponses.
- **Droits**, écrits **avant** le code, comme pour la spec 015 (`test-writer`) :
  - sans droit, 403 et un refus au journal ;
  - un collaborateur limité à la Kara ne voit que la Kara et se voit refuser la Savanes ;
  - un `clubs:modifier` ne peut pas toucher aux DRE, aux IESG ni aux axes ;
  - aucune route `DELETE`.
- **Garde-fous** : un cas par règle de « Cas limites et erreurs » (doublons, version périmée, enfants
  actifs, dernier axe, DRE utilisée comme périmètre, cible inactive, réactivation sous une IESG inactive).
- **Journal** : avant et après, sur une modification et sur un déplacement d'IESG.
- **Site** : tests Vitest des fonctions pures, regroupement par type et recherche normalisée sur des
  données de l'API. Les pages sont vérifiées à la main dans le navigateur (carte, accueil, admin).

## Risques

- **Le chargement est du code de l'application appelé par une migration.** Si les modèles changent plus
  tard, la migration ancienne pourrait casser. Parade : `chargement.py` écrit avec des `table()` SQLAlchemy
  Core qui ne listent que les colonnes de cette migration, et ne dépend pas des modèles ORM.
- **Les 6 doublons retirés** sont peut-être deux établissements distincts du même nom. L'admin pourra en
  recréer un avec une localité différente : l'unicité porte sur le nom dans l'IESG, donc il faudra un nom
  distinctif, par exemple « CEG Babigou (Nord) ».
- **La carte dépend maintenant de l'API.** Elle passe en rendu serveur avec une solution de secours (voir
  « Site » ci-dessus) ; la préproduction le vérifiera.
- **Le Hall of Fame** est un palmarès : il garde les noms des régions tels qu'ils étaient pendant le
  championnat, sans appel à l'API (décision prise pendant l'implémentation).
