# 0009 — Moteur commun de modération et notifications internes

- **Statut** : Proposé
- **Date** : 2026-11-07

## Contexte

Tout ce qu'un élève, un président ou un encadreur publie passe par une modération avant d'être visible (PRD,
« Modération et publications ») : articles (R6), commentaires (R7), actualités du club (R8), rapports (R12),
plus tard forums et événements. Les règles sont les mêmes partout :

- six états : brouillon, en attente, à corriger, refusé, publié, dépublié ;
- une modification d'un contenu publié reste masquée jusqu'à sa validation, l'ancienne version reste en ligne ;
- quatre décisions (approuver, demander une correction, refuser, dépublier), avec motif sauf pour approuver ;
- un auteur ne décide jamais de son propre contenu ;
- les points ne sont crédités qu'à la première approbation (ADR-0004) ;
- l'auteur reçoit chaque décision sur le site, avec son motif.

Écrire ces règles une fois par type de contenu multiplierait les écarts et les failles.

## Options envisagées

- **Une table par type, avec ses propres états et décisions** : simple pour le premier type, mais chaque
  spec réécrit la file, les versions, les décisions et les notifications. La file centrale de l'admin devient
  une union de requêtes.
- **Un moteur commun : un en-tête `contenu` et des versions `version_contenu`** (retenu). L'en-tête porte le
  type, l'auteur, l'état, le périmètre et la version publiée ; chaque version porte les champs du type en
  JSONB, validés par un schéma Pydantic propre au type. Les décisions sont dans `decision_moderation`.
  Une seule file, une seule machine à états, une seule règle de points.
- **Une bibliothèque de flux de travail** (machine à états générique) : plus de dépendances et de concepts
  pour six états et quatre décisions.

## Décision

Un domaine `moderation` porte la machine à états, les versions, les décisions et la file ; chaque type de
contenu s'y déclare (schéma de ses champs, action du barème, aperçu) et garde ses propres routes. Un domaine
`notifications` écrit les avis internes dans la même transaction que la décision.

## Conséquences

- Les champs d'un type vivent en JSONB : la base ne vérifie pas leur forme, l'API le fait à chaque écriture. Les
  champs à filtrer ou à joindre (axe, adresse publique, parent d'un commentaire) sont des colonnes de l'en-tête.
- Une version soumise ne change plus ; la version approuvée est celle qu'on lit en public. Les versions et les
  décisions ne sont jamais supprimées une fois soumises : elles forment l'historique de modération.
- Le périmètre (DRE de l'établissement de l'auteur) est copié dans l'en-tête à chaque soumission : la file se
  filtre sans jointure par type, et un collaborateur de DRE ne voit que sa région (comme l'ADR-0008, note de la
  spec 018).
- Les décisions se prennent sous verrou de l'en-tête et avec sa version : deux modérateurs simultanés, ou un
  auteur qui modifie pendant la décision, reçoivent un 409.
- Les points passent par `points.crediter` avec la clé `<type>:<contenu>` : une seule ligne par contenu, même
  après une dépublication puis une nouvelle approbation.
- Les notifications n'existent que sur le site (pas d'e-mail ni de SMS aux élèves) ; elles ne contiennent
  jamais un contenu non approuvé destiné à un autre que son auteur.
- Les photos et pièces jointes privées des contenus (spec 024, puis R12) s'attachent aux versions ; leur
  stockage suit l'ADR-0005, sur le disque du VPS au départ.

## Note (2026-11-08, spec 025)

Les commentaires sont le deuxième type du moteur. Ils ont ajouté :

- `contenu.parent_id` : l'article commenté. Un commentaire n'a pas d'adresse publique ; il se lit sous son article.
- Un septième état, `retire` : retiré par son auteur, sans décision de modérateur, hors ligne et hors de la file.
- Des réglages par type dans `TypeContenu`, avec les valeurs de l'article par défaut : `adresse`, `correction`
  (pas de « à corriger » pour un commentaire), `points_permis` (plafond de 5 commentaires rémunérés par jour
  d'envoi, sous le verrou de l'auteur) et `a_la_publication` (notifier l'auteur de l'article).
- La limite de 3 contenus en attente se compte par type.
