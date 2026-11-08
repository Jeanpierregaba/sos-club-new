# 024 — Photos des articles

## Objectif

Suite de R6 (spec 023). L'auteur d'un article illustre son action par des photos : une photo de couverture et
quelques photos dans l'article. Comme le texte, elles passent par la modération et ne sont visibles de personne
d'autre avant l'approbation. Chaque photo porte l'attestation de l'auteur, que le modérateur contrôle (PRD,
parcours 3 « Publier » ; Q8 ; ADR-0005 ; ADR-0009).

Cette spec pose aussi le **stockage des fichiers** prévu par l'ADR-0005 : sur le disque du VPS au départ
(décision de la spec 023), derrière une couche qui permettra un stockage S3 plus tard sans changer le reste du
code. Les rapports d'activités (R12) et les cartes (R15) le réutiliseront.

## Comportement attendu

**Ajouter des photos (auteur)**

1. Dans l'éditeur d'un article modifiable, l'auteur choisit une photo (5 au plus par article, dont une
   couverture ; 8 Mo au plus avant recompression) sur son téléphone ou son ordinateur.
2. Avant l'envoi, il coche l'attestation : « J'ai l'accord des personnes reconnaissables sur cette photo et,
   pour un élève mineur, celui de son parent ou tuteur. » Sans cette case, l'envoi est impossible.
3. Il ajoute une légende courte (facultative) et choisit si la photo sert de couverture.
4. La photo est envoyée, vérifiée, recompressée et débarrassée de ses métadonnées (dont la position GPS). Il
   voit aussitôt sa vignette dans l'éditeur.
5. Il peut retirer une photo, changer sa légende ou l'ordre des photos tant que l'article est modifiable.
6. Les photos font partie de la version : une nouvelle version d'un article publié peut ajouter ou retirer des
   photos, et la version en ligne garde les siennes jusqu'à la décision.

**Modérer**

- L'aperçu de la file montre chaque photo en grand, sa légende et son attestation (qui, quand).
- Pour une nouvelle version, l'aperçu indique les photos ajoutées et retirées.
- Si une photo pose problème, le modérateur demande une correction ou refuse, avec un motif (spec 023).

**Lire (visiteur)**

- La liste `/articles` montre la photo de couverture de chaque article qui en a une.
- La page de l'article montre la couverture en haut, puis les autres photos avec leur légende, sous le texte.
- Les photos se chargent à la demande et en taille réduite : le site reste léger sur un réseau lent.

## Critères d'acceptation

- [x] Étant donné un article modifiable, quand son auteur envoie une photo JPEG, PNG ou WebP avec l'attestation,
      alors elle est enregistrée, recompressée, sans métadonnées, et rattachée à sa version de travail.
- [x] Étant donné une photo sans attestation, un fichier qui n'est pas une image (même renommé), une image
      corrompue ou trop lourde, alors l'API répond 422 et rien n'est enregistré.
- [x] Étant donné une photo envoyée avec une position GPS dans ses métadonnées, alors le fichier enregistré n'en
      contient plus aucune.
- [x] Étant donné un article en attente, refusé ou d'un autre auteur, quand l'auteur ajoute ou retire une photo,
      alors l'API répond 409 (ou 404 pour un article d'un autre).
- [x] Étant donné une photo d'un article non publié, alors seuls son auteur et les collaborateurs habilités de son
      périmètre peuvent l'afficher ; pour toute autre personne, et pour une adresse devinée, l'API répond 404.
- [x] Étant donné un article publié avec une nouvelle version en attente qui change ses photos, alors le public
      voit les photos de la version en ligne seulement, jusqu'à l'approbation.
- [x] Étant donné un article dépublié, alors ses photos ne sont plus accessibles au public.
- [x] Étant donné 5 photos déjà rattachées à la version, quand l'auteur en ajoute une sixième, alors l'API répond
      409 ; une seule photo de la version est la couverture.
- [x] Étant donné un article refusé (ou une version refusée) depuis plus de 90 jours, quand la purge passe, alors
      les fichiers de ses photos que plus aucune autre version n'utilise sont effacés du disque ; la légende et
      l'attestation restent dans l'historique, et l'aperçu admin indique « photo effacée ».
- [x] Étant donné une photo, alors son attestation (auteur, date, texte accepté) est enregistrée et visible dans
      l'aperçu de modération.
- [x] Le stockage passe par une seule interface (`enregistrer`, `lire`, `supprimer`) : changer de disque à S3 ne
      touche qu'un fichier, et les tests tournent sur un dossier temporaire.
- [x] Le volume des photos est inclus dans la sauvegarde du VPS.
- [x] Le site affiche l'ajout des photos, la vignette, l'attestation, la galerie publique et l'aperçu admin,
      lisibles sur téléphone.

## Cas limites et erreurs

- **Envoi interrompu** (réseau lent) : rien n'est enregistré à moitié ; l'auteur réessaie.
- **Deux envois simultanés** au-delà de la limite : le verrou de l'article les sérialise, la limite tient.
- **Image très grande** (par exemple 6 000 × 4 000) : réduite à 1 600 pixels au plus sur son grand côté.
- **Orientation** d'une photo de téléphone : appliquée avant de retirer les métadonnées, la photo reste droite.
- **Photo animée** (GIF, WebP animé) : refusée ; seule la première image n'aurait pas de sens.
- **Même photo envoyée deux fois** : acceptée, ce sont deux photos.
- **Version remplacée** : une photo reste liée aux versions qui l'utilisent ; elle n'est supprimée du disque que
  lorsque plus aucune version ne l'utilise et qu'elle n'appartient pas à l'historique d'un contenu soumis.
- **Brouillon supprimé** (jamais soumis) : ses photos sont supprimées du disque.
- **Article refusé, ou version refusée** : ses photos restent privées, puis leurs fichiers sont effacés 90 jours
  après le refus, sauf si une autre version (en ligne ou en cours) les utilise encore.
- **Article dépublié** : ses photos restent privées, sans délai d'effacement : l'auteur peut proposer une
  nouvelle version qui les reprend.
- **Photo qui pose problème** : le modérateur ne la retire pas lui-même ; il demande une correction ou refuse,
  avec un motif, comme pour le texte.
- **Disque plein ou indisponible** : 503 avec un message clair ; la version ne référence pas un fichier absent.
- **Fichier présent en base mais absent du disque** : 404 sur la photo, l'article reste lisible.

## Hors périmètre

- Vidéos (liens YouTube, ADR-0005) et PDF : pas d'envoi par les auteurs.
- Photo de profil, photo de carte membre (R15), justificatifs de rapports (R12) : ils réutiliseront le stockage.
- Retouche, recadrage ou floutage dans le site.
- Détection automatique des visages ou des contenus inappropriés.
- Stockage S3 : prévu par l'interface, pas branché.

## Questions ouvertes

Aucune. Tranchées le 2026-11-07 :

1. Place : une couverture en haut, les autres photos en galerie sous le texte, avec leur légende. Aucune image
   dans le texte.
2. Limites : 5 photos au plus par version, dont une couverture ; 8 Mo au plus par photo avant recompression.
3. Conservation : fichiers des photos d'un contenu ou d'une version refusés effacés 90 jours après le refus ;
   l'historique garde la légende et l'attestation.
4. Modérateur : il ne retire pas une photo lui-même ; il demande une correction ou refuse.
