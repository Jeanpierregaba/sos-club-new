# 044 — Plan technique

## Approche

**Les partages d'articles sont un nouveau type du moteur de modération** (ADR-0009), comme les commentaires
(spec 025). Ce choix reprend sans les réécrire :

- la file de modération et ses filtres ;
- le périmètre DRE et la double authentification ;
- le verrou de l'auteur ;
- les notifications et le journal des décisions.

Une déclaration de partage est un `Contenu` de type `partage` :

- son parent est l'article partagé (`parent_id`) ;
- sa version unique porte `{reseau, lien, nature}` ;
- `nature` vaut `republication` ou `partage`. Elle est fixée à la déclaration : `partage` si la personne est l'autrice
  de l'article, `republication` sinon.

Une déclaration se crée et se soumet dans la même transaction, sans brouillon, comme un commentaire.

Pourquoi pas une table à part avec son propre écran : il faudrait refaire la file, les droits, les notifications et
le journal. Le moteur sait déjà tout faire, à deux crochets près, déjà prévus dans `TypeContenu` :

- `crediter`, pour choisir l'action et la clé du registre ;
- `complement_apercu`, pour montrer le réseau, le lien et l'article au modérateur.

**La carte de classement est une image PNG dessinée par l'API** avec Pillow et les polices Noto déjà utilisées par
la carte numérique (spec 040). Elle est produite à la demande pour son seul titulaire et jamais stockée.

Pourquoi pas un dessin dans le navigateur (canvas) : le rang et les points viennent de l'API, qui est la seule à
décider de ce que la carte montre. Les tests vérifient aussi l'absence de donnée sensible côté serveur, sans dépendre
du site.

## Fichiers touchés

**API — créés**

- `backend/app/partages/__init__.py`.
- `backend/app/partages/service.py` :
  - le type `partage` : `enregistrer(TypeContenu(...))` ;
  - la déclaration (`declarer`) ;
  - « Mes partages » (`mes_partages`) ;
  - la validation du lien (`verifier_lien`) ;
  - le crédit (`_crediter`) et le complément d'aperçu.
- `backend/app/partages/schemas.py` : `Reseau` (facebook, instagram, tiktok, linkedin), `DeclarationPartage`,
  `PartageAuteur`, `MesPartages`, `EtatPartagesArticle` (les réseaux déjà déclarés par la personne sur un article).
- `backend/app/partages/router.py` : les routes de la section « API ».
- `backend/app/points/carte_classement.py` : le rendu PNG de la carte de classement (Pillow).
- `backend/alembic/versions/<id>_partages.py` : la migration.
- Tests :
  - `backend/tests/test_partages.py` : déclaration, plafonds, liens, droits ;
  - `backend/tests/test_partages_moderation.py` : décisions, points, concurrence, périmètre ;
  - `backend/tests/test_carte_classement.py` : contenu, refus, absence de donnée sensible.

**API — modifiés**

- `backend/app/moderation/models.py` : la contrainte `commentaire_a_un_parent` devient « un commentaire ou un partage,
  et eux seuls, ont un parent ».
- `backend/app/admin/catalogue.py` : le module `partages` (« Partages vérifiés », disponible, actions consulter et
  approuver).
- `backend/app/points/classements.py` : `carte_personnelle(db, utilisateur, niveau, periode)`, qui renvoie rang,
  nombre de classés, points, nom affiché, DRE et club. Elle s'appuie sur `_rang_personnel` et les bases existantes.
- `backend/app/points/router.py` : la route de la carte.
- `backend/app/main.py` : le routeur `partages` et l'import du type, pour qu'il soit enregistré au démarrage.
- `backend/openapi.json`, puis `src/lib/api/schema.gen.ts` (types régénérés).

**Site — créés**

- `src/components/partages/PartagerArticle.tsx` (et son test) :
  - les liens de partage (Facebook et LinkedIn par leur adresse de partage ; Instagram et TikTok par « Copier le
    lien », car ils n'ont pas de partage web) ;
  - le formulaire « J'ai partagé cet article » : réseau et lien ;
  - l'état des réseaux déjà déclarés.
- `src/components/partages/MesPartages.tsx` (et son test) : la liste de « Mon espace ».
- `src/components/espace/PartagerClassement.tsx` (et son test) : la boîte de dialogue « Partager mon classement »
  (vue, période, case du club, aperçu, Télécharger et Partager). Le partage natif passe par
  `navigator.share({ files })` quand `navigator.canShare` l'accepte.

**Site — modifiés**

- `src/routes/articles.$adresse.tsx` : le bloc `PartagerArticle` pour une personne connectée, élève ou encadreur.
- `src/routes/_connecte/mon-espace.tsx` : la section « Mes partages » et le bouton « Partager mon classement ».
- `src/routes/hall-of-fame.tsx` : le bouton « Partager mon classement » pour une personne connectée et classée.
- `src/routes/_connecte/admin/moderation.tsx` : le type « Partage » dans les filtres, et l'aperçu (réseau, lien
  cliquable en `rel="noopener noreferrer nofollow"`, titre et lien de l'article, nature).
- `src/lib/api/client.ts` : les appels et les types.

**Docs**

- `docs/PRD.md` : Q23 tranchée, R17 coché.
- `TASKS.md`.
- `docs/ROADMAP.md` : renvoi vers la spec.
- ADR-0009 : une note sur le type `partage`, qui a un parent comme le commentaire.

## Données

Migration non destructive :

- La contrainte `commentaire_a_un_parent` est remplacée par `contenu_a_un_parent` :
  `(type IN ('commentaire', 'partage')) = (parent_id IS NOT NULL)`. Les lignes existantes la respectent déjà.
- Un index partiel sur le lien des déclarations vivantes, pour le contrôle de doublon :
  `ix_version_contenu_lien_partage` sur `(donnees->>'lien')`, avec la condition
  `donnees ? 'lien' AND etat <> 'travail'`. Il n'est pas unique : une déclaration refusée libère son lien, ce que la
  table des versions ne sait pas dire seule. L'unicité se tranche sous verrou (voir « Sécurité »).
- Aucune nouvelle ligne de barème : `eleve.republication` (+10), `eleve.partage` (+50), `encadreur.republication`
  (+10) et `encadreur.partage` (+50) existent déjà et sont actives.

Le retour arrière remet la contrainte d'origine. Il refuse s'il existe des contenus `partage` : on ne supprime rien.

## API / interfaces

| Route                                                                                                  | Qui                                  | Rôle                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /api/articles/{adresse}/partages`                                                                | élève ou encadreur actif (vérifié)   | Déclare un partage `{reseau, lien}`. 201, avec la déclaration en attente.                                                                                              |
| `GET /api/articles/{adresse}/partages/moi`                                                             | idem                                 | Les réseaux déjà déclarés (en attente ou approuvés) sur cet article, la nature possible (republication ou partage) et le nombre de déclarations restantes aujourd'hui. |
| `GET /api/partages/moi`                                                                                | élève ou encadreur                   | « Mes partages » : article, réseau, lien, état, motif d'un refus, points crédités.                                                                                     |
| `GET /api/classements/moi/carte.png?niveau=national\|dre\|club&periode=semestre\|historique&club=0\|1` | élève ou encadreur classé            | La carte PNG, 1080 × 1350, sans cache.                                                                                                                                 |
| File de modération existante (`/api/admin/moderation`)                                                 | modérateur avec `partages:approuver` | Type `partage` : approuver ou refuser. Ni correction ni retrait du site.                                                                                               |

Règles de la déclaration, sous le verrou de l'auteur (`moteur.verrouiller_auteur`) :

1. **L'article** est publié et de type `article`. Sinon 404, sans dire s'il existe.
2. **Le lien** est valide :
   - il commence par `https://` ;
   - il fait 500 caractères au plus ;
   - son domaine (sans `www.` ni `m.`) appartient au réseau choisi :
     - Facebook : `facebook.com`, `fb.com`, `fb.watch` ;
     - Instagram : `instagram.com` ;
     - TikTok : `tiktok.com`, `vm.tiktok.com`, `vt.tiktok.com` ;
     - LinkedIn : `linkedin.com`, `lnkd.in`.

   Sinon 422.

3. **Le plafond du jour** : moins de 3 déclarations créées aujourd'hui (jour UTC, soit l'heure de Lomé), refusées
   comprises. Sinon 429.
4. **Pas de doublon pour la personne** :
   - pour un `partage`, aucune déclaration en attente ou approuvée sur ce réseau pour cet article ;
   - pour une `republication`, aucune déclaration en attente ou approuvée pour cet article.

   Sinon 409.

5. **Lien jamais utilisé** : un verrou transactionnel sur le lien
   (`pg_advisory_xact_lock(hashtextextended(lien, 0))`), puis aucune version d'un partage en attente ou approuvé
   avec ce lien, quel que soit son auteur. Sinon 409.

Crédit à l'approbation (`crediter`) :

- l'action est `<role>.republication` ou `<role>.partage`, selon la nature ;
- la clé est `partage:<article>:<auteur>:<reseau>` pour un partage, `republication:<article>:<auteur>` pour une
  republication. Même si un doublon passait, la base refuse une deuxième ligne pour la même clé.

`crediter` refuse l'approbation (409, « L'article n'est plus en ligne : refuse ce partage ») si l'article a été
dépublié entre-temps. La transaction de la décision est alors annulée.

Le type `partage` se déclare ainsi :

- `adresse=False`, `correction=False`, `depublication=False` ;
- `domaine_droit="partages"` ;
- `avis_approbation="est validé"`, `libelle="partage"` ;
- `lien_auteur` vers `/mon-espace#mes-partages` ;
- `actions_auteur` renseigné pour l'élève et l'encadreur, afin que le moteur enregistre le club bénéficiaire ;
- `max_en_attente=3`.

## Dépendances

Aucune nouvelle. Pillow et les polices Noto sont déjà là (spec 040). Côté site, `navigator.share` et
`navigator.canShare` sont des API du navigateur, avec le téléchargement comme repli.

## Sécurité

- **Droits dans l'API** (ADR-0003) :
  - déclarer exige un élève actif, ou un encadreur actif et vérifié ;
  - la carte ne concerne que la personne connectée, sans aucun identifiant en paramètre : aucune autre carte n'est
    accessible (pas d'IDOR) ;
  - décider exige la modération et `partages:approuver`, sous double authentification (droit sensible de la
    modération) et dans le périmètre DRE.
- **Données des mineurs** (`docs/RULES.md`) :
  - la carte ne porte que le pseudonyme (ou le prénom et l'initiale d'un encadreur), le rang, les points, le niveau,
    la DRE et le club si la case est cochée ;
  - les tests lisent les textes dessinés (liste rendue par une fonction pure testée) et vérifient l'absence de nom,
    d'établissement et d'identifiant ;
  - le lien d'un partage, qui peut mener au profil d'un mineur, n'est servi que dans la file de modération et dans
    « Mes partages » de son auteur.
- **Liens** :
  - l'API ne visite jamais le lien (pas de SSRF) ;
  - le site l'affiche comme un texte et un lien `nofollow noopener noreferrer` ouvert par le modérateur ;
  - seul `https://` est accepté, jamais `javascript:` ni `data:`.
- **Charge** :
  - 3 déclarations par jour et 3 en attente par auteur ;
  - la carte est limitée à 30 images par heure et par compte, par le limiteur déjà utilisé pour la carte
    numérique.
- **Aucun point sans décision humaine** : le crédit ne passe que par `approuver`.

## Tests

En TDD pour les parties critiques (points et confidentialité, `docs/TESTING.md`) : les tests sont écrits avant le
code.

**`test_partages.py`**

- Déclaration :
  - republication et partage ;
  - nature déduite de l'auteur ;
  - article non publié, brouillon ou dépublié : refusé ;
  - liens invalides : `http`, mauvais domaine, `javascript:`, plus de 500 caractères ;
  - lien déjà utilisé, par soi ou par un autre.
- Unicité et plafonds :
  - réseau déjà déclaré, puis libéré après un refus ;
  - republication unique par article ;
  - plafond de 3 par jour, refus compris.
- Droits : visiteur, suspendu, encadreur non vérifié, non connecté.
- « Mes partages » : seulement les siens ; lien absent des pages publiques et de l'API publique des articles.

**`test_partages_moderation.py`**

- Approbation : +10 ou +50 au registre, part du club, notification.
- Deux réseaux : deux crédits.
- Refus : motif, aucun point.
- Pas de « corriger » ni de « dépublier » (422).
- Collaborateur sans `partages:approuver` : 403 ; collaborateur de DRE hors périmètre : 404.
- Article dépublié avant la décision : approbation refusée.
- Deux approbations simultanées : une seule ligne.
- Encadreur : `encadreur.partage`.

**`test_carte_classement.py`**

- Textes de la carte : pseudonyme, rang, classés, points, niveau, période, « Classement provisoire ».
- Club seulement si la case est cochée ; encadreur en prénom et initiale ; aucun nom complet.
- Non classé : 404 ; vue club sans club : 422 ; pas de semestre en cours avec `periode=semestre` : 409.
- Visiteur ou admin : 403 ; non connecté : 401.
- PNG valide de 1080 × 1350.
- Aucune ligne au registre.

**Migration** : montée sur une base avec commentaires, contrainte respectée, retour arrière refusé s'il existe un
partage.

**Site (Vitest)**

- `PartagerArticle` :
  - réseaux déjà déclarés grisés ;
  - nature affichée (+10 ou +50) ;
  - erreurs de l'API ;
  - masqué pour un visiteur.
- `MesPartages` : états et motif.
- `PartagerClassement` :
  - vues proposées selon le club ;
  - case du club ;
  - repli sur le téléchargement sans `navigator.share`.

**Au navigateur** : déclaration, file de modération, carte téléchargée, à 375 px et sur ordinateur.

## Risques

- **Liens impossibles à vérifier** (compte privé, story expirée). Le modérateur refuse avec un motif ; c'est le prix
  d'une preuve humaine. La capture d'écran a été écartée (décision du 2026-11-19).
- **Charge de modération.** Le plafond de 3 par jour la borne. Si elle déborde, on pourra baisser le plafond ou
  ajouter une file dédiée aux partages.
- **Une même publication sous deux adresses** (lien court et lien long). Le contrôle de doublon ne compare que le
  texte du lien. Le modérateur reste le dernier contrôle, et R22 (anomalies) pourra le renforcer.
- **Partage natif inégal selon les navigateurs** : le téléchargement est toujours proposé.

Correction apportée à la spec à l'occasion du plan : le moteur refuse d'approuver le contenu d'un compte suspendu,
et un lien n'est « déjà utilisé » que par une déclaration en attente ou approuvée (voir la spec, cas limites).
