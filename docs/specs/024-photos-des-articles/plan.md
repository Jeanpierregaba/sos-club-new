# 024 — Plan technique

## Approche

**Stockage** ([ADR-0010](../../decisions/0010-fichiers-sur-le-disque-du-vps.md)). Un domaine `app/fichiers/` :

- `stockage.py` : l'interface `Stockage` (`enregistrer(cle, octets)`, `lire(cle)`, `supprimer(cle)`) et son
  implémentation `Disque`, rangée sous `settings.dossier_fichiers`. L'écriture passe par un fichier temporaire
  puis un renommage : aucun fichier à moitié écrit. Une clé est toujours `photos/<uuid>-<taille>.webp`, tirée par
  l'API ; `Disque` refuse toute clé hors de ce format (pas de `..`).
- `images.py` : `preparer(octets) -> ImagesPreparees`, avec Pillow, dans un fil à part (`asyncio.to_thread`) :
  1. ouvrir l'image et vérifier son format réel (JPEG, PNG, WebP), refuser une image animée ;
  2. plafonner le nombre de pixels (40 millions) contre les « bombes » de décompression ;
  3. redresser selon l'orientation EXIF (`ImageOps.exif_transpose`) ;
  4. produire deux tailles en WebP (qualité 80) : `grande` (1 600 px au plus sur le grand côté) et `vignette`
     (480 px), sans aucune métadonnée (EXIF, GPS, XMP, ICC retirés).

**Photos, sur le moteur de modération** ([ADR-0009](../../decisions/0009-moteur-de-moderation.md)). Les photos sont
génériques : les actualités du club (R8) les réutiliseront. Une photo est un fichier attesté ; son placement
(légende, couverture, ordre) appartient à une version, donc il est versionné comme le texte.

- `photo` : le fichier et son attestation.
- `version_photo` : la photo dans une version, avec sa légende, son ordre et la marque de couverture.

Toute nouvelle version (modification d'un contenu publié, correction) recopie les `version_photo` de la version
qu'elle remplace : le moteur le fait dans `_nouvelle_version`. Ajouter, modifier ou retirer une photo exige une
version de travail : si elle n'existe pas (contenu publié ou dépublié), elle est ouverte comme pour une
modification du texte. Chaque opération verrouille l'en-tête et contrôle sa version (`version` envoyée par le
site), puis fait monter la version de l'en-tête.

**Lecture d'une photo.** Trois routes, une par public, chacune vérifie que la photo appartient à une version
qu'il a le droit de lire :

- l'auteur : toute version de son contenu ;
- le modérateur : toute version d'un contenu de son périmètre (404 sinon) ;
- le public : seulement la version en ligne d'un article publié, par son adresse.

**Effacement.**

- Retirer une photo d'une version de travail qui ne l'a jamais soumise : si aucune autre version ne l'utilise, le
  fichier et la ligne sont supprimés tout de suite.
- Supprimer un brouillon jamais soumis : ses photos aussi.
- Purge quotidienne, dans la boucle qui purge déjà les exports : une photo dont toutes les versions sont
  refusées depuis plus de 90 jours, et que ni la version en ligne ni la version de travail n'utilisent, perd ses
  fichiers (`efface_le` est posé, la ligne reste pour l'historique).

## Fichiers touchés

**Créés, API**

- `backend/app/fichiers/__init__.py`, `stockage.py`, `images.py`.
- `backend/app/moderation/photos.py` : `ajouter`, `modifier`, `retirer`, `photos_de(version)`, `lire_pour_auteur`,
  `lire_pour_moderateur`, `lire_publique`, `purger`.
- Migration `photos_des_contenus` : tables `photo` et `version_photo`.
- Tests : `test_fichiers.py` (stockage et images), `test_photos_acces.py` (écrit avant le code),
  `test_photos_auteur.py`, `test_photos_purge.py`.

**Modifiés, API**

- `app/config.py` : `dossier_fichiers` (par défaut `backend/var/fichiers` en local), `.env.example` et
  `deploy/env.example` : `DOSSIER_FICHIERS`.
- `app/moderation/models.py` : `Photo`, `VersionPhoto`.
- `app/moderation/service.py` : `_nouvelle_version` recopie les photos ; `supprimer` efface celles d'un brouillon.
- `app/moderation/decisions.py` et `schemas.py` : l'aperçu ajoute les photos soumises et en ligne, avec leur
  attestation, et les photos ajoutées ou retirées.
- `app/articles/` : `ArticleAuteur`, `ResumeArticle` et `ArticlePublic` ajoutent `couverture` et `photos` (adresse,
  légende, dimensions) ; les routes d'envoi, de modification, de retrait et de lecture.
- `app/admin/exports.py` (ou `main.py`) : la boucle horaire appelle aussi `photos.purger` (une fois par jour).
- `pyproject.toml`, `uv.lock` : Pillow.
- `.gitignore` : `backend/var/`.
- `deploy/compose.yaml` : volume `fichiers` monté sur `/donnees/fichiers` dans le conteneur `api`,
  `DOSSIER_FICHIERS=/donnees/fichiers`. `deploy/sauvegarder.sh` : archive du volume à côté du dump.
  `deploy/README.md` : restauration des fichiers.
- `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, ADR-0005 (renvoi vers l'ADR-0010).

**Site**

- `src/components/articles/Photos.tsx` : dans l'éditeur, l'envoi (attestation obligatoire, légende, couverture),
  la barre de progression, les vignettes, la modification de la légende, l'ordre, le retrait.
- `src/components/articles/Galerie.tsx` : couverture et galerie publiques, `loading="lazy"`, dimensions fixées
  (pas de saut de mise en page), agrandissement au clic.
- `src/components/articles/Editeur.tsx`, `src/routes/articles.index.tsx`, `src/routes/articles.$adresse.tsx`,
  `src/routes/_connecte/admin/moderation.tsx` : branchement.
- `src/lib/api/client.ts` : l'envoi en `multipart/form-data` et les nouveaux types.

## Données

Migration non destructive : deux tables nouvelles.

- `photo` : `id` (UUID), `contenu_id` (FK, CASCADE), `auteur_id` (FK `utilisateur`, RESTRICT), `cle_grande`,
  `cle_vignette`, `largeur`, `hauteur`, `octets` (taille de la grande), `attestation` (texte accepté, copié),
  `attestee_le`, `cree_le`, `efface_le` (nul tant que les fichiers existent).
- `version_photo` : `version_id` (FK, CASCADE) et `photo_id` (FK, RESTRICT), clé primaire composée ; `ordre`,
  `legende` (200 caractères au plus, une ligne), `couverture`. Index unique partiel : une seule couverture par
  version.

## API / interfaces

**Auteur** (`/mes-articles/{id}/photos`, verrou et `version` à chaque écriture) :

- `POST` (multipart : `fichier`, `version`, `attestation`, `legende`, `couverture`) → `ArticleAuteur` ;
- `PATCH /{photo_id}` (`version`, `legende`, `couverture`, `ordre`) → `ArticleAuteur` ;
- `DELETE /{photo_id}?version=` → `ArticleAuteur` ;
- `GET /{photo_id}/{taille}` → l'image (`taille` : `grande` ou `vignette`), `Cache-Control: private, no-store`.

**Modérateur** : `GET /admin/moderation/{id}/photos/{photo_id}/{taille}`, droit `moderation:consulter` et
périmètre ; `no-store`.

**Public** : `GET /articles/{adresse}/photos/{photo_id}/{taille}`, seulement pour la version en ligne ;
`Cache-Control: public, max-age=31536000, immutable` (une clé ne change jamais de contenu).

Toutes les images partent en `image/webp`, avec `X-Content-Type-Options: nosniff`.

## Dépendances

- **Pillow 13.0.0** (API), publié le 2026-10-16, maintenu, compatible Python 3.14, roues avec WebP. Seule
  bibliothèque qui recompresse et retire les métadonnées de façon fiable en Python. Documentation à relire avec
  Context7 au moment de l'ajout (`ImageOps.exif_transpose`, `Image.MAX_IMAGE_PIXELS`, enregistrement WebP sans
  `exif`).
- Rien pour le site : envoi par `FormData` et `XMLHttpRequest` pour la progression.

## Sécurité

- Taille lue au plus 8 Mo + 1 octet : au-delà, 422 sans lire la suite. Le proxy plafonne déjà à 20 Mo.
- Type réel lu par Pillow, jamais l'extension ni le type annoncé ; image ré-encodée : rien du fichier d'origine
  n'est servi.
- Attestation obligatoire, texte et date enregistrés ; nom de l'auteur jamais dans les métadonnées.
- Lecture contrôlée à chaque requête ; une photo privée n'a pas d'adresse publique ; 404 hors droit.
- Clés tirées par l'API, chemin vérifié par `Disque` (aucune traversée de dossier).
- Journal d'audit : ajout et retrait d'une photo (identifiant, version), jamais l'image ni la légende.
- Données personnelles : photos d'élèves possibles ; effacement à 90 jours après un refus ; sauvegarde du volume.

## Tests

En TDD pour l'accès (`docs/TESTING.md` : rien de public avant approbation) :

- `test_photos_acces.py`, écrit avant le code : auteur, autre élève, visiteur, modérateur hors périmètre, version
  en attente d'un article publié, article dépublié, adresse devinée, photo effacée.
- `test_fichiers.py` : écriture atomique, clé invalide refusée, JPEG avec GPS → plus de métadonnées, orientation,
  réduction à 1 600 px, PNG transparent, GIF animé et faux JPEG refusés, image trop grande en pixels.
- `test_photos_auteur.py` : ajout, attestation manquante (422), 6e photo (409), couverture unique, légende, ordre,
  retrait (fichier effacé), version périmée (409), article en attente (409), copie des photos dans une nouvelle
  version, brouillon supprimé.
- `test_photos_purge.py` : 90 jours après un refus, fichiers effacés ; photo encore utilisée gardée ; avant 90
  jours, rien.
- Les tests utilisent un dossier temporaire (`tmp_path`) comme `dossier_fichiers`.
- Site (Vitest) : l'envoi est bloqué sans attestation.
- Navigateur : ajout de photos sur téléphone, galerie publique.

## Risques

Stress-test du 2026-11-07 (spec et plan). Points retenus et réponse apportée :

- **Important — mémoire du VPS.** Décoder une photo de 40 millions de pixels prend environ 160 Mo ; plusieurs
  envois simultanés sur deux processus peuvent épuiser un petit VPS. Réponse : au plus 2 traitements d'image à la
  fois par processus (sémaphore), les suivants attendent.
- **Important — fichiers orphelins.** Les fichiers sont écrits avant la validation de la base : si la transaction
  échoue, ils restent sur le disque. Réponse : en cas d'erreur, l'API les efface aussitôt ; un fichier n'est
  effacé du disque qu'après la validation qui le libère (jamais avant). Un balayage des orphelins restants est
  noté dans `TASKS.md`.
- **Important — photos d'iPhone (HEIC).** Pillow ne lit pas le HEIC sans extension. Réponse : le champ du site
  n'accepte que `image/jpeg,image/png,image/webp` ; Safari convertit alors la photo en JPEG avant l'envoi. Un
  HEIC qui arriverait quand même est refusé avec un message clair (422).
- **Mineur — purge sur deux processus.** La boucle tourne dans chaque processus de l'API. Réponse : la purge pose
  `efface_le` par une mise à jour conditionnelle (`efface_le IS NULL … RETURNING`) avant d'effacer les fichiers :
  un seul processus traite chaque photo.
- **Mineur — cache public.** Une photo publique est mise en cache un an par les navigateurs : après une
  dépublication, un visiteur qui l'avait déjà vue peut la garder en cache. Accepté : l'API ne la sert plus, et
  la page de l'article n'existe plus.
- **Mineur — taille des sauvegardes.** Une archive complète du volume par jour, gardée 14 jours. Accepté au
  pilote ; à revoir (sauvegarde incrémentale) quand le volume dépassera quelques Go.
- **Sur-engineering écarté.** Pas de S3, pas de traitement en tâche de fond, pas de recadrage ; deux tailles
  seulement.
