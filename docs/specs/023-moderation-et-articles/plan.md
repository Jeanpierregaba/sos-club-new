# 023 — Plan technique

## Approche

Trois domaines d'API, selon l'[ADR-0009](../../decisions/0009-moteur-de-moderation.md) :

- **`backend/app/moderation/`** : le moteur commun. En-tête `contenu`, versions `version_contenu`, décisions
  `decision_moderation`, machine à états, file et décisions de l'admin. Il ne connaît les types que par un
  registre (`TypeContenu` : code, schéma des champs, action de points de l'auteur, résumé pour la file).
- **`backend/app/articles/`** : le premier type. Rédaction par l'auteur, lecture publique, signature.
- **`backend/app/notifications/`** : le centre de notifications, utilisé par le moteur et plus tard par les
  autres domaines (clubs, rattachements).

**États.** L'en-tête porte `etat` : `brouillon`, `en_attente`, `a_corriger`, `refuse`, `publie`, `depublie`. Il
décrit la dernière version, sauf qu'un contenu publié dont une nouvelle version est refusée revient à `publie`.
Ce qui est en ligne ne dépend que de `version_publiee_id` (non nul seulement si le contenu est publié).

| Depuis                          | Action de l'auteur ou du modérateur | Vers         | Effet                                                                                |
| ------------------------------- | ----------------------------------- | ------------ | ------------------------------------------------------------------------------------ |
| (rien)                          | créer                               | `brouillon`  | version 1, modifiable                                                                |
| `brouillon`, `a_corriger`       | modifier                            | inchangé     | la version de travail change                                                         |
| `publie`, `depublie`            | modifier                            | `brouillon`  | une nouvelle version de travail ; la version publiée reste en ligne                  |
| `brouillon`, `a_corriger`       | soumettre                           | `en_attente` | la version est figée ; DRE copiée ; au plus 3 en attente par auteur                  |
| `en_attente`                    | retirer                             | `brouillon`  | la version redevient modifiable                                                      |
| `en_attente`                    | approuver                           | `publie`     | `version_publiee_id` = cette version ; points à la 1re fois ; adresse créée          |
| `en_attente`                    | demander une correction (motif)     | `a_corriger` | la version publiée éventuelle reste en ligne                                         |
| `en_attente`                    | refuser (motif)                     | `refuse`     | contenu clos ; si une version était publiée, elle reste et l'état revient à `publie` |
| `publie` (ou révision en cours) | dépublier (motif)                   | `depublie`   | `version_publiee_id` = nul ; une révision en attente est refusée avec le même motif  |

Un brouillon jamais soumis se supprime ; tout le reste se garde (historique). Pour un contenu déjà publié,
« modifier » d'abord ouvre une nouvelle version : la soumettre repasse par la file.

**Décider.** Une transaction : verrou de l'en-tête (`FOR UPDATE`), contrôle de la version envoyée par le site,
de l'état et du périmètre, puis l'écriture de la décision, du nouvel état, des points, de la notification et du
journal d'audit. La clé `article:<contenu>` garantit une seule ligne de points, même après dépublication.

**Points.** `eleve.article` ou `encadreur.article` pour l'auteur, via `points.crediter`. Le registre ne crédite
pas encore les clubs (R13) : pour un élève affilié (adhésion active), l'approbation copie `club_beneficiaire_id`
dans l'en-tête, et R13 créditera `club.article_eleve` à partir de cette colonne.

**Texte.** Un sous-ensemble de Markdown, stocké tel quel : paragraphes, intertitres (`##`, `###`), gras,
italique, listes. Le site l'affiche avec `react-markdown`, en n'autorisant que ces éléments, sans HTML ni lien.
L'API limite les longueurs et refuse les caractères de contrôle.

**Signature publique.** Calculée à la lecture, jamais stockée : un élève par son pseudonyme, et son club si
l'article a `afficher_club` et que l'adhésion est active ; un encadreur par son prénom, l'initiale de son nom
et sa fonction.

## Fichiers touchés

**Créés, API**

- `backend/app/moderation/models.py` : `Contenu`, `VersionContenu`, `DecisionModeration`, `EtatContenu`,
  `TypeDecision`.
- `backend/app/moderation/types.py` : le registre `TypeContenu` et l'enregistrement du type `article`.
- `backend/app/moderation/service.py` : `creer`, `modifier`, `soumettre`, `retirer`, `supprimer_brouillon`
  (côté auteur, appelés par chaque type).
- `backend/app/moderation/decisions.py` : `file_attente`, `compter_en_attente`, `apercu`, `approuver`,
  `demander_correction`, `refuser`, `depublier`.
- `backend/app/moderation/schemas.py`, `router.py` : `/admin/moderation`.
- `backend/app/articles/schemas.py` : `ArticleChamps` (titre, chapô, texte, axe, afficher_club),
  `ArticleAuteur`, `ArticlePublic`, `ResumeArticle`, `Signature`.
- `backend/app/articles/service.py` : les opérations de l'auteur, la lecture publique, la signature, l'adresse.
- `backend/app/articles/router.py` : `/articles` (public) et `/mes-articles` (auteur).
- `backend/app/notifications/models.py`, `service.py` (`notifier`, `lister`, `compter_non_lues`,
  `marquer_lue`, `marquer_toutes_lues`), `schemas.py`, `router.py`.
- La migration `moderation_articles_notifications`.
- Les tests (voir Tests).

**Modifiés, API**

- `app/admin/catalogue.py` : le module `moderation` devient disponible ; `("moderation", "consulter")` rejoint
  les droits sensibles (la file montre le nom complet de l'auteur). Le préréglage « Modérateur éditorial » a déjà
  les trois droits ; les collaborateurs existants ne changent pas.
- `app/admin/tableau_de_bord.py` et `/admin/moi` : l'indicateur « Contenus à modérer », dans le périmètre.
- `app/admin/inscrits.py` : l'historique de la fiche ajoute les actions de modération ; les libellés du journal.
- `app/points/bareme.py` : `eleve.article` et `encadreur.article` rejoignent `EN_SERVICE` (migration).
- `app/main.py`, `alembic/env.py`, `app/seed_dev.py` (un article publié, un en attente, un à corriger, pour la
  démo), `backend/openapi.json`, `src/lib/api/schema.gen.ts`.
- `docs/ARCHITECTURE.md` (les trois domaines), `docs/SECURITY.md` (données de la file), `docs/decisions/README.md`.

**Site**

- `src/components/articles/TexteArticle.tsx` : le rendu restreint par `react-markdown`.
- `src/components/articles/Editeur.tsx` : champs, barre d'outils (intertitre, gras, italique, liste), aperçu,
  compteurs de caractères, « Enregistrer », « Soumettre », « Retirer », avec la version pour le verrou.
- `src/components/articles/EtatContenu.tsx` : la pastille d'état, lisible sans la couleur.
- `src/routes/_connecte/mes-articles.index.tsx`, `mes-articles.nouveau.tsx`, `mes-articles.$id.tsx` : la liste,
  la création et l'édition, avec le dernier motif reçu.
- `src/routes/articles.index.tsx` (liste publique, filtre par axe, hero clair) et `articles.$adresse.tsx`.
- `src/routes/_connecte/admin/moderation.tsx` : la file (filtres, compteur) et l'aperçu (avant / après pour une
  nouvelle version), les quatre décisions avec motif.
- `src/components/notifications/Cloche.tsx` : la cloche et son compteur dans `SiteHeader` et l'en-tête admin,
  rechargés à chaque navigation ; `src/routes/_connecte/notifications.tsx` : la liste, « Tout marquer comme lu ».
- `src/routes/_connecte/mon-espace.tsx` : le lien « Mes articles » (élève et encadreur actif).
- `src/routes/magazine.tsx` : un lien vers `/articles`. Menu admin : « Modération » et son compteur.
- `src/lib/api/client.ts` : les appels.

## Données

Migration non destructive : trois tables nouvelles, une table de notifications, deux actions du barème mises en
service (sans toucher à leur montant).

- `contenu` : `id` (UUID), `type` (texte, `article`), `auteur_id` (FK `utilisateur`, RESTRICT), `etat`,
  `version_publiee_id` (FK, nul), `version_travail_id` (FK, nul), `axe_id` (FK `axe`, nul selon le type),
  `adresse` (unique, nulle avant la 1re approbation), `afficher_club`, `dre_code` (copiée à la soumission),
  `club_beneficiaire_id` (FK `club`, nul), `soumis_le`, `publie_le`, `cree_le`, `modifie_le`, `version`
  (verrou optimiste). Index : `(etat, soumis_le)` pour la file, `(type, publie_le)` partiel sur
  `version_publiee_id IS NOT NULL` pour la liste publique, `(auteur_id, etat)`.
- `version_contenu` : `id`, `contenu_id`, `numero` (unique par contenu), `donnees` (JSONB), `etat`
  (`travail`, `soumise`, `approuvee`, `a_corriger`, `refusee`, `retiree`), `cree_le`, `soumise_le`.
- `decision_moderation` : `id`, `contenu_id`, `version_id`, `decision`, `motif` (obligatoire sauf pour
  approuver, contrainte CHECK), `decide_par`, `decide_le`.
- `notification` : `id`, `utilisateur_id` (CASCADE), `type`, `titre`, `message`, `lien`, `lue_le`, `cree_le`.
  Index `(utilisateur_id, lue_le, cree_le)`.

## API / interfaces

**Auteur** (élève, ou encadreur actif via `encadreur_actif`) :

- `GET /mes-articles` ; `POST /mes-articles` (crée un brouillon) ; `GET /mes-articles/{id}` (avec le dernier
  motif) ; `PATCH /mes-articles/{id}` (avec `version`) ; `DELETE /mes-articles/{id}` (brouillon jamais soumis) ;
  `POST /mes-articles/{id}/soumettre` et `/retirer`.

**Public** : `GET /articles?axe=&page=` (20 par page) ; `GET /articles/{adresse}` (404 si non publié).

**Admin** (`moderation`) :

- `GET /admin/moderation?type=&axe=&dre=&profil=&etat=` (`consulter`) ; `GET /admin/moderation/{id}` (aperçu,
  version publiée et version soumise) ;
- `POST /admin/moderation/{id}/approuver|corriger|refuser` (`approuver`) ;
  `POST /admin/moderation/{id}/depublier` (`depublier`), avec `version` et `motif`.

**Notifications** (tout compte connecté) : `GET /notifications` (50 dernières), `GET /notifications/compte`,
`POST /notifications/{id}/lue`, `POST /notifications/lues`.

## Dépendances

- **`react-markdown` 10.1.0** (site), du collectif remarkjs (unified), maintenu, compatible React 19. Par
  défaut, il n'interprète aucun HTML ; on restreint en plus les éléments autorisés. Doc à relire avec Context7
  au moment de l'ajout. Aucune dépendance côté API.

## Sécurité

- Droits vérifiés dans l'API sur chaque route (ADR-0003) : auteur = propriétaire du contenu, sinon 404 ;
  modérateur = droit du module et périmètre DRE, sinon 404 pour un contenu hors périmètre.
- Un auteur ne décide jamais de son contenu : `collaborateur.utilisateur_id == auteur_id` → 403.
- `consulter`, `approuver` et `depublier` de la modération exigent la double authentification (ADR-0008).
- Les routes publiques ne lisent que `version_publiee_id` ; aucun schéma public n'expose l'identifiant, le nom ou
  le DRE de l'auteur. Les notifications ne visent que l'auteur.
- Texte : longueurs bornées par Pydantic, aucun HTML interprété au rendu, pas de lien dans cette spec.
- Abus : 3 contenus en attente au plus par auteur, 20 brouillons au plus.
- Journal d'audit : soumission, retrait, et chaque décision avec son motif ; jamais le texte de l'article.

## Tests

En TDD pour les parties critiques (`docs/TESTING.md` : modération et points) :

- `test_moderation_decisions.py`, écrit avant le code : approbation et points une seule fois, concurrence de deux
  approbations, révision d'un article publié, refus et correction avec motif (422 sans motif), dépublication,
  décision sur un contenu déjà traité ou modifié (409), droits, double authentification, périmètre DRE, auteur
  modérateur de son contenu, club bénéficiaire, action du barème désactivée, journal.
- `test_articles_auteur.py` : brouillon, modification, soumission, retrait, suppression, limites, encadreur en
  attente (403), contenu d'un autre (404), longueurs.
- `test_articles_publics.py` : visibilité par état, signature élève et encadreur, `afficher_club`, filtre par
  axe, adresse stable, pagination.
- `test_notifications.py` : création à chaque décision, compteur, lecture, isolement entre comptes.
- Site (Vitest) : `TexteArticle` n'interprète ni HTML ni lien ; l'éditeur envoie la version.
- Navigateur : parcours complet auteur → modérateur → page publique, et la cloche, sur téléphone.

## Risques

Stress-test du 2026-11-07 (spec et plan). Points retenus et réponse apportée :

- **Important — points des clubs différés.** Le registre ne crédite pas les clubs avant R13 : sans suite, les
  +20 seraient perdus. Réponse : `club_beneficiaire_id` est enregistré à l'approbation, et la ligne R13 de
  `docs/ROADMAP.md` note qu'elle doit créditer ces articles avec la clé `club_article:<contenu>`.
- **Important — effacement d'un compte.** `auteur_id` en RESTRICT empêche de supprimer un auteur. Aucun
  effacement de compte n'existe encore ; la spec qui le créera dépubliera ses articles et remplacera la
  signature par « Ancien membre ». Noté ici, sans code dans cette spec.
- **Important — contenu de santé.** Le modérateur porte seul la justesse médicale. Les articles de démonstration
  de `seed_dev` sont signalés « Article de test » dans leur titre et n'existent qu'en local (RULES).
- **Mineur — périmètre figé à la soumission.** Si l'auteur change d'établissement pendant la modération, la
  demande reste dans l'ancienne DRE jusqu'à la prochaine soumission. Accepté : le national voit tout.
- **Mineur — forme des champs en JSONB.** La base ne la vérifie pas ; chaque écriture passe par le schéma du type,
  et un test relit chaque version en base avec ce schéma.
- **Mineur — volume des notifications.** Aucune purge pour l'instant ; une purge des notifications lues de plus
  d'un an viendra plus tard, notée dans `TASKS.md`.
- **Sur-engineering écarté.** Pas de bibliothèque de flux de travail, pas de comparaison mot à mot entre versions
  (avant / après par champ suffit), pas de temps réel pour la cloche (rechargée à chaque navigation).
