# 046 — Plan technique

## Approche

On prolonge `admin/parcours_inscrit.py` (spec 045), en lecture seule et derrière `LecteurInscrits`. Pas de table, pas
de migration, pas de nouveau droit. Tous les temps sont calculés en SQL avec des agrégats (`sum`, `avg`, `count`
filtrés) sur `tentative_quiz` et `reponse_quiz`. Une expression unique `temps_de_jeu` est partagée :
`extract(epoch from derniere_activite - commencee_le)`, bornée à 0 par `greatest`.

- **Quiz** : la durée de `_tentative` passe de `terminee_le` à `derniere_activite`. On ajoute `abandonnee`
  (terminée et `terminee_le − derniere_activite > INACTIVITE`). Le résumé ajoute `temps_total_s` et `temps_moyen_s`.
  Chaque quiz validé reçoit :
  - `temps_premiere_reussite_s`, par une sous-requête `DISTINCT ON (quiz_id)` triée sur `terminee_le` ;
  - `moyenne_nationale_s` et `reussites_nationales`, en un seul `GROUP BY quiz_id` limité aux quiz de la page, hors
    joueur et hors essais, avec `null` sous 5 réussites ;
  - `tres_rapide`.
- **Détail d'une tentative** : nouvelle fonction `tentative_de(db, utilisateur_id, tentative_id)`.
  - Elle vérifie que la tentative appartient à l'inscrit (404 sinon).
  - Elle lit ses `ReponseQuiz` jointes à `QuestionQuiz` et à ses paramètres (`temps_ms`), triées par rang.
  - `etat` vaut `juste`, `fausse`, `temps_ecoule` (envoyée, `choix` nul, `correcte` faux ou délai passé) ou
    `non_posee` (`envoyee_le` nul).
  - `reponse` est `question.choix[ligne.choix]`.
  - On n'expose jamais `bonne_reponse` : le schéma n'a pas ce champ.
- **Certification** : `certification_de` ajoute :
  - par place, `temps_s` et `tentatives`, par un `GROUP BY Quiz.place` sur les tentatives de certification hors
    essais, jointes à `PlaceReussie` pour s'arrêter à `commencee_le <= reussie_le` ;
  - par badge, des fenêtres `(obtenu_le précédent, obtenu_le]` calculées en Python sur la liste des 5 badges au plus,
    puis une requête par fenêtre (5 au plus : borné) ;
  - par certificat, le cumul et la durée calendaire jusqu'à `delivre_le`.
  - La date de première tentative de certification sert de point de départ.
- **Site** : un formateur `dureeLisible(secondes)` dans `src/lib/admin.ts`.
  - `OngletQuiz` affiche les nouveaux champs, la pastille « Très rapide » et la mention « abandonnée ».
  - Un clic sur une tentative ouvre `DetailTentative`, un panneau `Dialog` qui charge à l'ouverture.
  - `OngletCertification` affiche les temps.

## Fichiers touchés

**API**
- `backend/app/admin/parcours_inscrit.py` : expression `temps_de_jeu`, `_tentative`, `quiz_de`, `tentative_de`
  (nouvelle), `certification_de`.
- `backend/app/admin/schemas.py` :
  - `ResumeQuiz` : `+temps_total_s`, `temps_moyen_s` ;
  - `QuizValide` : `+temps_premiere_reussite_s`, `moyenne_nationale_s`, `reussites_nationales`, `tres_rapide` ;
  - `TentativeAdmin` : `+abandonnee` ;
  - nouveaux `QuestionTentative` et `DetailTentative` ;
  - `PlaceAdmin` : `+temps_s`, `tentatives` ;
  - `BadgeAdmin` : `+temps_s`, `temps_cumule_s`, `duree_calendaire_s` ;
  - `CertificatAdmin` : `+temps_cumule_s`, `duree_calendaire_s`.
- `backend/app/admin/router.py` : `GET /inscrits/{id}/tentatives/{tentative_id}`.
- `backend/tests/test_admin_inscrit_temps.py` (nouveau).

**Site**
- `src/lib/api/schema.gen.ts` (régénéré), `src/lib/api/client.ts` : types et `chargerTentativeInscrit`.
- `src/lib/admin.ts` : `dureeLisible` (+ test).
- `src/components/admin/fiche-inscrit/OngletQuiz.tsx`, `OngletCertification.tsx`, `DetailTentative.tsx` (nouveau,
  + test).

## Données

Aucune nouvelle table ni colonne. Une migration sans destruction, `e4a7c2d9b6f1`, ajoute l'index partiel
`ix_tentative_quiz_reussites` sur `tentative_quiz (quiz_id, joueur_id, terminee_le)`, limité aux réussites terminées
hors essais. Il sert la moyenne nationale ; sans lui, chaque ouverture de l'onglet Quiz parcourait toute la table.

## API / interfaces

| Méthode | Route                                              | Droit                | Rôle                     |
| ------- | -------------------------------------------------- | -------------------- | ------------------------ |
| GET     | `/api/admin/inscrits/{id}/tentatives/{tentative_id}` | `inscrits:consulter` | Questions d'une tentative |

Les routes `quiz` et `certification` gardent leur forme. Elles gagnent seulement des champs.

## Dépendances

Aucune.

## Sécurité

- Droit `inscrits:consulter` national, vérifié par la route (ADR-0003).
- 404 si la tentative n'appartient pas à l'inscrit : pas de lecture croisée.
- La bonne réponse n'est jamais renvoyée (ADR-0004) : le schéma ne la contient pas, et un test le vérifie.
- `Cache-Control: no-store`.
- La moyenne nationale ne révèle aucun autre joueur, seulement un agrégat et un effectif d'au moins 5.

## Tests

`test_admin_inscrit_temps.py` couvre :
- durée d'une tentative abandonnée ;
- résumé ;
- moyenne nationale : seuil de 5, exclusion de l'inscrit et des essais ;
- « Très rapide » ;
- détail : 4 états, ordre, absence de `bonne_reponse`, 404 croisé, 403 ;
- temps d'une place, borné à la réussite ;
- fenêtres des badges ;
- certificat ;
- inscrit sans tentative.

Côté site : un test Vitest pour `dureeLisible` et un pour `DetailTentative`. Les tests 045 existants restent verts.

## Risques

- **Seuil de 5 et facteur ½** : ce sont des repères arbitraires, mis en constantes nommées pour être ajustés.
- **Pause de correction des jeux** : `envoyee_le` est posé 1,2 s dans le futur ; le calcul part bien de là, et le
  borne à 0 couvre les arrondis.
- **Temps de jeu ≠ temps d'attention** : le temps entre deux questions (lecture de la correction) est compté dans
  le temps de jeu d'une tentative, pas dans celui d'une question. Le panneau le dit.
