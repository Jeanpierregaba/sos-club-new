# 045 — Plan technique

## Approche

Tout reste dans le domaine `admin`, derrière les dépendances `LecteurInscrits` et `GestionnaireInscrits` déjà
utilisées par la fiche (droit `inscrits`, périmètre national). Aucune nouvelle table, aucune migration, aucun nouveau
droit au catalogue.

- **Modification** : une route `PATCH`, des règles dans un nouveau module `admin/modification_inscrit.py`. Elle
  réutilise les validateurs de l'inscription (`normaliser_telephone`, `_valider_email`, champs Pydantic de
  `comptes/champs.py`) pour que les règles ne divergent pas.
- **Verrou optimiste** : la fiche renvoie la `version` du profil d'élève ou d'encadreur (`Suivi.version`). La
  modification la renvoie ; on touche `modifie_le` du profil même quand seule l'identité change, comme le fait déjà
  `eleves.service.modifier_profil`, pour que la version monte. Un compte sans profil (créé avant la spec 017) se
  verrouille par `SELECT … FOR UPDATE` sur l'utilisateur, sans version.
- **Registre** : on ajoute un filtre `utilisateur_id` à `points.registre.FiltresRegistre` et on réutilise
  `registre.lister`. La route de la fiche est sous `/api/admin/inscrits/{id}/points`, gardée par le droit
  `inscrits`, pas par le droit `points`.
- **Parcours** : un nouveau module `admin/parcours_inscrit.py`, en lecture seule, avec trois fonctions : `quiz`,
  `certification`, `contenus`. Requêtes paginées en SQL, jamais toute la table en mémoire.
- **Site** : la fiche `inscrits.$id.tsx` passe en onglets ; chaque onglet charge ses données à l'ouverture (pas de
  requête pour un onglet jamais ouvert). L'onglet est dans la recherche de l'URL (`validateSearch`).

## API

| Méthode | Route                                         | Droit               | Rôle                                   |
| ------- | --------------------------------------------- | ------------------- | -------------------------------------- |
| PATCH   | `/api/admin/inscrits/{id}`                    | `inscrits:modifier` | Modifier identité et profil            |
| GET     | `/api/admin/inscrits/{id}/points`             | `inscrits:consulter`| Registre paginé (`semestre_id`, `page`)|
| GET     | `/api/admin/inscrits/{id}/quiz`               | `inscrits:consulter`| Résumé, quiz validés, tentatives       |
| GET     | `/api/admin/inscrits/{id}/certification`      | `inscrits:consulter`| Places, badges, certificats            |
| GET     | `/api/admin/inscrits/{id}/contenus`           | `inscrits:consulter`| Contenus paginés (`type`, `etat`)      |

Toutes : 404 « Compte introuvable. » si l'utilisateur n'existe pas ou est un invité ; refus pour un compte admin sur
le `PATCH` (409, « Un collaborateur se gère depuis l'écran des collaborateurs. ») ; `Cache-Control: no-store`.

### Schémas (`admin/schemas.py`)

- `ModificationInscrit` (`extra="forbid"`) : `motif` (10 à 500), `version: int | None`, et des champs facultatifs
  (seuls ceux envoyés changent, `model_fields_set`) : `prenom`, `nom` (`Requis100`), `email`, `telephone`
  (`Telephone`), `classe`, `fonction`, `fonction_precision`, `discipline`, `commune`.
- `InscritDetail.version: int | None` (version du profil).
- `PagePointsInscrit` : `totaux` (semestre, points du semestre, total) et `PageRegistre`.
- `QuizInscrit` : `resume {quiz_valides, tentatives, echecs, points}`, `valides: list[QuizValide]`,
  `tentatives: PageTentatives`. `TentativeAdmin` : `id, quiz_titre, axe, parcours, place, niveau, commencee_le,
  terminee_le, etat, essai, score, nb_questions, reussie, duree_s, points`.
- `CertificationInscrit` : `places: list[PlaceAdmin]` (20), `badges`, `certificats`.
- `PageContenusInscrit` : `ContenuAdmin {id, type, titre, etat, cree_le, publie_le}`. Le titre vient du champ
  `titre` de la version la plus récente, sinon des 80 premiers caractères du texte.

### Journal

- Nouvelle action `profil_modifie_par_equipe`, ajoutée à `inscrits.HISTORIQUE`, avec
  `details = {"motif", "champs": [...], "avant": {...}, "apres": {...}}`. `avant`/`apres` ne portent que
  `classe`, `fonction`, `fonction_precision`, `discipline`, `commune`.
- Libellé côté site : « Profil modifié par l'équipe ».

## Fichiers touchés

**API — créés**

- `backend/app/admin/modification_inscrit.py` : `modifier(db, acces, utilisateur_id, entree, ip)`.
- `backend/app/admin/parcours_inscrit.py` : `quiz`, `certification`, `contenus`.
- `backend/tests/test_admin_inscrit_modification.py`.
- `backend/tests/test_admin_inscrit_parcours.py` (points, quiz, certification, contenus, droits).

**API — modifiés**

- `backend/app/admin/router.py` : les 5 routes.
- `backend/app/admin/schemas.py` : les schémas ci-dessus.
- `backend/app/admin/inscrits.py` : `version` dans `detail`, nouvelle action dans `HISTORIQUE`.
- `backend/app/points/registre.py` : filtre `utilisateur_id`.

**Site — modifiés**

- `src/lib/api/schema.d.ts` (régénéré), `src/lib/api/client.ts` (fonctions d'appel).
- `src/routes/_connecte/admin/inscrits.index.tsx` : ligne cliquable.
- `src/routes/_connecte/admin/inscrits.$id.tsx` : onglets, dialogue de modification.
- Nouveaux composants dans `src/components/admin/fiche-inscrit/` : `OngletPoints.tsx`, `OngletQuiz.tsx`,
  `OngletCertification.tsx`, `OngletContenus.tsx`, `DialogueModification.tsx`, et leurs tests Vitest pour le
  dialogue (validation, envoi des seuls champs changés).
- Libellé du journal dans le dictionnaire des événements de la fiche.

## Dépendances

Aucune nouvelle.

## Risques

- **Données de mineurs** : rien de nouveau n'est public ; les routes sont nationales et non mises en cache. Le journal
  ne copie pas les données d'identité.
- **Divergence des règles** avec l'inscription : évitée en réutilisant les validateurs existants ; les tests le
  vérifient sur les mêmes cas.
- **Performance** des tentatives : index existant sur `tentative_quiz.joueur_id` à vérifier ; sinon, ajouter un
  index par migration (seule migration possible de la spec).
