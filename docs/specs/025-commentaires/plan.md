# 025 — Plan technique

## Approche

Le commentaire est un nouveau type du moteur de modération (ADR-0009), comme l'article : un en-tête `contenu`
de type `commentaire`, une seule version `{"texte": …}`, les mêmes décisions, la même file et les mêmes
notifications. L'ADR prévoyait déjà la colonne « parent d'un commentaire » dans l'en-tête. On n'écrit donc ni
table, ni file, ni écran de décision à part : on ajoute au moteur les quelques réglages par type dont un
commentaire a besoin, et un petit domaine `commentaires` pour ses routes.

Ce qu'un commentaire fait autrement qu'un article, et comment le moteur le permet :

| Besoin du commentaire              | Réglage du moteur                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------ |
| Envoyé en une fois, sans brouillon | `commentaires.service.envoyer` appelle `creer` puis `soumettre` dans la même requête |
| Pas d'adresse publique             | `TypeContenu.adresse = False` ; la contrainte `adresse_si_publie` exempte un enfant  |
| Pas de décision « à corriger »     | `TypeContenu.correction = False` : la route répond 409, le bouton est masqué         |
| 5 commentaires rémunérés par jour  | `TypeContenu.points_permis(db, contenu)`, appelé à la première approbation           |
| Notifier l'auteur de l'article     | `TypeContenu.a_la_publication(db, contenu)`, appelé à la première approbation        |
| Retrait par l'auteur, même publié  | septième état `retire`, sans décision de modérateur                                  |
| La limite de 3 contenus en attente | comptée par type : les commentaires ne bloquent pas les articles, et l'inverse       |

L'alternative, une table `commentaire` hors du moteur, dupliquerait la file, les décisions, le périmètre DRE,
les verrous et les notifications : c'est ce que l'ADR-0009 voulait éviter.

## Fichiers touchés

**API**

- `app/moderation/models.py` : `Contenu.parent_id`, état `retire`, contrainte et index (voir Données).
- `app/moderation/types.py` : champs `adresse`, `correction`, `points_permis`, `a_la_publication` (valeurs par
  défaut : celles de l'article, qui ne change pas).
- `app/moderation/service.py` : `MAX_EN_ATTENTE` compté par type ; `retirer_definitivement` (état `retire`).
- `app/moderation/decisions.py` : `approuver` sans adresse si le type n'en a pas, appelle `points_permis` et
  `a_la_publication` ; `demander_correction` refusée (409) si le type ne l'accepte pas ; message d'encadreur
  non vérifié avec le libellé du type ; file et aperçu montrent l'article parent (titre, adresse).
- `app/moderation/schemas.py` : `ElementFile.parent`, `ApercuModeration.parent`, `correction_possible`.
- `app/commentaires/` (nouveau) : `schemas.py`, `service.py` (type `commentaire`, envoi, plafonds, anti double
  envoi, liste publique, « Mes commentaires », retrait), `router.py`.
- `app/articles/public.py` : `signature` réutilisée telle quelle pour les commentaires.
- `app/main.py` : inclure le routeur.
- Migration Alembic `commentaires` ; `ACTIONS_EN_SERVICE` pour `eleve.commentaire` et `encadreur.commentaire`.
- `app/seed_dev.py` : deux commentaires de démonstration (un publié, un en attente) sur l'article publié.

**Site**

- `src/components/articles/Commentaires.tsx` (nouveau) : liste publique, champ et confirmation, invitation à se
  connecter pour un visiteur ; avec `Commentaires.test.tsx`.
- `src/routes/articles.$adresse.tsx` : la section sous l'article.
- `src/routes/_connecte/mes-commentaires.tsx` (nouveau) : état, article, motif, bouton « Retirer ».
- `src/routes/_connecte/admin/moderation.tsx` : type affiché, lien vers l'article parent, « À corriger » masqué
  pour un commentaire.
- `src/lib/api/client.ts`, types régénérés ; lien « Mes commentaires » à côté de « Mes articles ».

**Docs** : ADR-0009 (note : `parent_id`, état `retire`, réglages par type), `ARCHITECTURE.md`, `SECURITY.md`
(lignes « commentaire » à revalider), `TASKS.md`, `SESSION-LOG.md`.

## Données

Migration non destructive :

- `contenu.parent_id` : UUID nul, clé étrangère vers `contenu.id` (`ON DELETE RESTRICT`) ; seul un commentaire
  en a un.
- Contrainte `adresse_si_publie` remplacée par `version_publiee_id IS NULL OR adresse IS NOT NULL OR parent_id IS
NOT NULL`.
- Contrainte `commentaire_a_un_parent` : `(type = 'commentaire') = (parent_id IS NOT NULL)`.
- État `retire` ajouté à la contrainte d'énumération `etat_contenu` (texte, pas de type natif : un simple
  remplacement de la contrainte CHECK).
- Index partiel `ix_contenu_commentaires_publics (parent_id, publie_le) WHERE version_publiee_id IS NOT NULL` et
  index `(auteur_id, type, cree_le)` pour les plafonds du jour.
- Barème : `eleve.commentaire` et `encadreur.commentaire` passent `en_service` (la migration inverse les remet).

Le « jour » des plafonds est le jour UTC de l'envoi (`cree_le`) : le Togo est à UTC+0, sans heure d'été.

## API / interfaces

| Méthode et route                             | Qui                      | Effet                                                                                                           |
| -------------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `GET /articles/{adresse}/commentaires?page=` | tout le monde            | Commentaires publiés d'un article publié, du plus ancien, 50 par page ; 404 sinon                               |
| `POST /articles/{adresse}/commentaires`      | élève ou encadreur actif | `{texte}` → 201 `CommentaireAuteur` en attente ; 404 si l'article n'est pas publié ; 429 au-delà de 20 par jour |
| `GET /mes-commentaires?article=`             | auteur                   | Ses commentaires (tous, ou ceux d'un article), avec état et dernier motif                                       |
| `DELETE /mes-commentaires/{id}`              | auteur                   | Passe à `retire` (204) ; 404 pour un autre compte                                                               |
| File, aperçu, décisions                      | modérateurs (spec 023)   | Inchangées ; `corriger` sur un commentaire → 409                                                                |

Règles de `envoyer`, sous le verrou de l'auteur (`_verrouiller_auteur`) :

1. Texte normalisé : espaces de début et de fin retirés, caractères de contrôle retirés (sauf retour à la ligne),
   plus de deux retours à la ligne d'affilée réduits à deux ; 1 à 1 000 caractères, sinon 422.
2. Même auteur, même article, même texte depuis moins d'une minute : on renvoie le commentaire existant (200).
3. 20 commentaires créés par l'auteur ce jour-là (tous états) : 429 « Tu as déjà envoyé 20 commentaires
   aujourd'hui : réessaie demain. ».
4. `creer` puis `soumettre` : périmètre DRE copié, journal `commentaire_soumis`.

`points_permis` (sous le verrou de l'auteur que prend déjà `approuver`) : vrai si moins de 5 commentaires du même
auteur, envoyés le même jour UTC, ont une ligne `commentaire:<id>` au registre des points.

`a_la_publication` : notification « Nouveau commentaire sur ton article « titre » » à l'auteur de l'article, sauf
s'il est l'auteur du commentaire ; appelée à la première publication seulement.

## Dépendances

Aucune.

## Sécurité

- Droits vérifiés dans l'API pour chaque route (ADR-0003) : rôle et statut actif pour écrire (dépendance
  `articles.dependances.auteur`, qui exige déjà un encadreur vérifié) ; propriété pour lire ses commentaires et
  retirer ; périmètre DRE pour décider.
- Texte rendu en texte simple par React (aucun `dangerouslySetInnerHTML`, ni Markdown, ni lien automatique).
- Aucun nom complet ni contact d'élève : signature `articles.public.signature` (pseudonyme et club, ou prénom,
  initiale et fonction).
- Rien de public avant l'approbation : la liste ne lit que `version_publiee_id`, et seulement si l'article est
  lui-même publié.
- Plafonds contre le spam : 20 envois par jour, 3 en attente à la fois (par type), anti double envoi.

## Tests

Parties critiques (`docs/TESTING.md` : droits, points, modération) écrites **avant** le code :

- `test_commentaires_envoi.py` : droits (anonyme, compte suspendu, encadreur non vérifié, article non publié),
  validation et normalisation du texte, anti double envoi, 429 à 21, limite de 3 en attente par type.
- `test_commentaires_moderation.py` : file et aperçu avec l'article parent, périmètre DRE, auteur qui ne décide
  pas, `corriger` → 409, points +5 une seule fois, sixième du jour sans points (et un commentaire de la veille
  approuvé aujourd'hui compte pour la veille), club bénéficiaire, notifications de l'auteur et de l'auteur de
  l'article (une seule fois, pas pour soi-même).
- `test_commentaires_publics.py` : seuls les publiés d'un article publié, ordre, pagination, signature sans nom
  complet, article dépublié → 404, retrait par l'auteur puis disparition, retrait d'un autre compte → 404,
  retrait pendant une décision → 409.
- Non-régression : les suites des articles et de la modération (spec 023) restent vertes.
- Site : `Commentaires.test.tsx` (visiteur, envoi et confirmation, erreurs 422 et 429, texte affiché sans être
  interprété).

## Risques

- **Réglages par type dans le moteur** : quatre champs de plus dans `TypeContenu`. Leurs valeurs par défaut sont
  celles de l'article, et les tests de la spec 023 tournent sans changement : c'est le garde-fou.
- **Volume** : un article populaire peut recevoir beaucoup de commentaires ; la pagination et l'index partiel
  gardent la lecture rapide. La file de modération reste plafonnée à 200 éléments par page (spec 023).
- **Points du club** : R13 devra ne créditer le club que pour les commentaires rémunérés (ligne
  `commentaire:<id>` au registre), pour respecter le même plafond ; noté dans `TASKS.md`.
