# 023 — Centre de modération, articles et notifications

## Objectif

Roadmap R6, phase 2 (jalon A, démo pilote). Un élève ou un encadreur actif rédige un article sur une action de
son club ou un thème de santé, le soumet, et l'équipe nationale le modère avant toute publication. L'auteur suit
ses décisions dans un centre de notifications sur le site (PRD, parcours 3 « Publier » ; critères « Modération
et publications » ; Q1, Q8 ; barème : `eleve.article`, `encadreur.article`, `club.article_eleve`).

Cette spec crée aussi le **moteur commun de modération** (états, versions, décisions, notifications) que
réutiliseront les commentaires (R7), les actualités du club (R8) et les rapports (R12). Un ADR le fixe.

R6 est livré en deux temps : cette spec (moteur, articles en texte, notifications), puis la spec 024 (photos
des articles : stockage, attestations Q8, recompression). Les articles de la spec 023 n'ont donc pas de photo.

## Comportement attendu

**Rédiger (élève, ou encadreur actif)**

1. Depuis son espace, l'auteur ouvre « Mes articles » puis « Écrire un article ».
2. Il remplit :
   - un titre (obligatoire) et un chapô court (obligatoire) ;
   - le texte, en paragraphes, avec des intertitres, du gras et des listes (aucun HTML accepté) ;
   - l'axe concerné, parmi les axes actifs (Q1) ;
   - pour un élève affilié, « Afficher mon club avec mon pseudonyme » (coché par défaut, Q20).
3. Il **enregistre un brouillon** autant de fois qu'il veut, puis le **soumet**. L'article passe « en attente »
   et ne se modifie plus tant qu'il est dans la file.
4. Il voit la liste de ses articles et leur état : brouillon, en attente, à corriger, refusé, publié, dépublié.

**Modérer (collaborateur habilité)**

- **File de modération** (menu admin, avec un compteur) : les contenus en attente, des plus anciens aux plus
  récents, filtrables par type, axe, DRE et profil de l'auteur. Un collaborateur national voit tout ; un
  collaborateur d'une DRE ne voit que les contenus des auteurs dont l'établissement est dans sa DRE.
- L'aperçu montre l'article tel qu'il sera publié, l'auteur (nom complet,
  profil, établissement, club) et, pour une nouvelle version, ce qui a changé.
- Quatre décisions :
  - **Approuver** : l'article est publié. Les points sont crédités à la première approbation seulement.
  - **Demander une correction**, avec un message : l'auteur reprend son article et le soumet de nouveau.
  - **Refuser**, avec un motif : l'article est clos, l'auteur ne peut plus le soumettre.
  - **Dépublier** un article publié, avec un motif : il disparaît du site.
- Chaque décision est inscrite au journal d'audit.

**Publier (visiteur)**

- `/articles` liste les articles publiés, du plus récent au plus ancien, filtrables par axe.
- `/articles/<adresse>` montre l'article, son axe, sa date et la signature : un élève par son pseudonyme et son
  club s'il en a un et l'a choisi ; un encadreur par son prénom, l'initiale de son nom et sa fonction (« Kossi A.,
  enseignant »). Jamais de nom complet public.
- Aucun brouillon, aucun article en attente, refusé ou dépublié n'apparaît, ni dans les pages ni dans l'API
  publique ni dans une recherche.

**Modifier un article publié**

- L'auteur peut proposer une nouvelle version. Elle repasse dans la file ; la version approuvée reste en ligne
  jusqu'à la décision. Une nouvelle version approuvée ne rapporte aucun point.

**Centre de notifications**

- Une cloche dans l'en-tête, pour tout compte connecté, avec le nombre de notifications non lues.
- L'auteur y reçoit chaque décision sur ses contenus, avec son motif, et un lien vers le contenu.
- Il les marque comme lues, une par une ou toutes. Pas d'e-mail ni de SMS aux élèves (PRD, hors périmètre).

**Points (barème, ADR-0004)**

- À la première approbation : `eleve.article` (+50) ou `encadreur.article` (+50, proposé) pour l'auteur.
- Pour un élève affilié à un club : `club.article_eleve` (+20) à ce club. Le registre ne crédite pas encore
  les clubs (R13, ADR-0003) : l'approbation enregistre le club bénéficiaire, et R13 lui créditera ses +20.

## Critères d'acceptation

- [ ] Étant donné un élève ou un encadreur actif, quand il enregistre un brouillon puis le soumet, alors l'article
      passe « en attente » et apparaît dans la file de modération.
- [ ] Étant donné un encadreur en attente de vérification, ou un compte suspendu, quand il crée ou soumet un
      article, alors l'API répond 403.
- [ ] Étant donné un article en brouillon, en attente, à corriger, refusé ou dépublié, alors il n'apparaît ni sur
      `/articles`, ni par son adresse (404), ni dans l'API publique, ni dans une recherche, ni dans une
      notification adressée à quelqu'un d'autre que son auteur.
- [ ] Étant donné un article en attente, quand un collaborateur habilité l'approuve, alors il est publié, l'auteur
      reçoit une seule ligne de points au montant du barème, et le club de l'élève affilié est enregistré comme
      bénéficiaire.
- [ ] Étant donné deux approbations simultanées du même article, alors une seule réussit et une seule ligne de
      points existe pour l'auteur.
- [ ] Étant donné un article publié, quand l'auteur soumet une nouvelle version, alors l'ancienne reste en ligne
      jusqu'à la décision, et l'approbation de la nouvelle ne crédite aucun point.
- [ ] Étant donné un refus, une demande de correction ou une dépublication sans motif, alors l'API répond 422.
- [ ] Étant donné une décision, alors l'auteur reçoit une notification avec le motif, et elle figure au journal
      d'audit avec son auteur.
- [ ] Étant donné un collaborateur sans le droit de modération, ou hors de son périmètre, quand il lit la file ou
      décide, alors l'API répond 403 (ou ne lui montre pas le contenu).
- [ ] Étant donné un collaborateur qui est aussi l'auteur du contenu, quand il tente de le décider, alors l'API
      répond 403 (un auteur ne valide jamais son propre contenu).
- [ ] Étant donné un article publié d'un encadreur, alors la page et l'API publique ne montrent que son prénom,
      l'initiale de son nom et sa fonction ; pour un élève, que son pseudonyme et son club.
- [ ] Étant donné un texte contenant du HTML ou un lien `javascript:`, alors il est affiché comme du texte, sans
      être interprété.
- [ ] Étant donné des notifications non lues, quand l'utilisateur les marque comme lues, alors le compteur de la
      cloche baisse ; personne ne lit les notifications d'un autre.
- [ ] Le site affiche l'éditeur, la liste « Mes articles », la file et l'aperçu admin, les pages publiques et le
      centre de notifications, lisibles sur téléphone.

## Cas limites et erreurs

- **Décision sur un contenu déjà traité** ou modifié entre-temps : 409, avec l'état actuel (verrou de version).
- **Modification pendant la modération** : impossible tant que l'article est en attente (409) ; l'auteur peut
  le retirer de la file, il redevient brouillon.
- **Trop de soumissions** : au plus 3 articles en attente à la fois par auteur (409, message clair).
- **Auteur suspendu** après soumission : son article reste dans la file ; il peut être refusé, et rien n'est
  publié tant que le compte est suspendu. Un article déjà publié reste en ligne, l'admin peut le dépublier.
- **Élève sans club ou dont l'affiliation prend fin** : l'auteur garde ses points ; le club n'en reçoit que si
  l'affiliation est validée au moment de l'approbation.
- **Dépublication** : les points restent acquis ; l'admin peut les corriger par un ajustement manuel du
  registre (spec 015). Un article dépublié ne se republie pas : l'auteur peut proposer une nouvelle version.
- **Axe désactivé** après la publication : l'article reste publié et rattaché à cet axe (spec 016).
- **Action du barème désactivée** à l'approbation : la publication réussit sans ligne de points.
- **Brouillon abandonné** : l'auteur peut le supprimer ; un contenu déjà soumis ne se supprime pas, il garde
  son historique de décisions.
- **Contenu dangereux ou inexact** (santé) : le modérateur refuse ou demande une correction ; aucun contenu
  n'est publié automatiquement.
- **Adresse de l'article** : générée depuis le titre, unique, et stable après publication même si le titre change.
- **Texte** : longueur limitée (titre 120 caractères, chapô 300, texte 20 000) ; tout HTML est neutralisé.

## Hors périmètre

- Photos des articles : spec 024 (stockage sur le disque du VPS derrière la couche de l'ADR-0005, attestation
  de l'auteur pour chaque photo, recompression et retrait des métadonnées).
- Articles au nom du club par le président : R8 (actualités du club), sur le même moteur.
- Commentaires (R7), partages et republications vérifiés (R17), rapports d'activités (R12).
- Vidéos dans un article : un lien YouTube viendra avec les contenus de l'équipe (ADR-0005) ; pas d'envoi de
  vidéo ni de PDF par les auteurs.
- Le magazine éditorial et « Paroles aux élèves » (R21) : `/magazine` reste tel quel, avec un lien vers
  `/articles`.
- Notifications par e-mail ou SMS aux élèves, notifications en temps réel, rappels automatiques.
- Recherche plein texte des articles.

## Questions ouvertes

Aucune. Tranchées le 2026-11-07 :

1. Photos : sur le disque du VPS (volume Docker sauvegardé), derrière la couche de l'ADR-0005 ; S3 plus tard sans
   changer le code. Elles sont livrées par la spec 024.
2. Modération : au niveau national ou par un collaborateur de la DRE de l'établissement de l'auteur, avec un
   module de droits `moderation` (comme les encadreurs, spec 018).
3. Signature publique d'un encadreur : prénom, initiale du nom et fonction.
4. Livraison en deux temps : spec 023 (moteur, articles en texte, notifications), puis spec 024 (photos).
