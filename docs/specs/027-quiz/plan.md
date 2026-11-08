# 027 — Plan technique

## Approche

Un nouveau domaine `app/quiz/`, séparé du moteur de modération (ADR-0009). Un quiz n'est pas un contenu rédigé
par un utilisateur : il est préparé et publié par l'équipe, ses états diffèrent (pas de correction demandée, pas
de version publiée qui reste en ligne pendant une modification), et il porte des réponses qui ne doivent jamais
sortir de l'API. Le reprendre dans le moteur demanderait des réglages de plus pour chacune de ces différences.

Le domaine a deux faces :

- **la banque** (`banque.py`, routes `/admin/quiz`) : quiz, réserve de questions, paramètres versionnés, file de
  publication, protégée par les droits `quiz` du catalogue des collaborateurs (spec 015, ADR-0008), déjà prévus
  et rendus disponibles ici ;
- **la partie** (`partie.py`, routes `/quiz`) : le serveur arbitre (ADR-0004). Il tire les questions au début,
  envoie une question à la fois, et chronomètre chaque question à partir de son envoi.

**Envoi paresseux.** Une question n'est « envoyée » (heure d'envoi enregistrée) qu'au moment où le serveur la
renvoie au joueur. Le délai court donc à partir de cet instant ; une coupure ne fait perdre que la question en
cours, et le joueur reprend à la suivante (cas limite de la spec). Renvoyer la question en cours (rechargement
de la page) garde l'heure d'envoi d'origine : on ne gagne pas de temps en rechargeant.

**L'heure.** Toute mesure passe par `quiz.horloge.maintenant()`, que les tests remplacent : 6,9 s et 7,1 s se
testent sans attendre.

**Le mode test** du gestionnaire utilise le même code de partie, sur une tentative marquée `essai`, appartenant
au collaborateur : elle ne compte ni dans les résultats, ni dans le plafond, ni pour les points, et elle est
effacée à sa fin (ou à l'essai suivant).

## Fichiers touchés

**API**

- `app/quiz/models.py` : `ParametresQuiz`, `Quiz`, `QuestionQuiz`, `TentativeQuiz`, `ReponseQuiz`.
- `app/quiz/horloge.py` : `maintenant()`.
- `app/quiz/banque.py` : création, modification, questions, soumission, reprise en brouillon, approbation, refus,
  dépublication, paramètres ; journal d'audit et notifications au gestionnaire.
- `app/quiz/partie.py` : lancer une tentative, état courant, répondre, clore, créditer, résultats du joueur.
- `app/quiz/schemas.py` : deux familles de schémas, sans champ commun pour les réponses : `QuestionJoueur`
  (énoncé et choix mélangés, jamais `bonne_reponse` ni `explication`) et `QuestionBanque` (complète, admin).
- `app/quiz/router.py` : `router` (`/quiz`, joueurs) et `router_admin` (`/admin/quiz`) ; inclus dans `main.py`.
- `app/quiz/dependances.py` : `joueur_actif` (élève ou encadreur au compte actif ; 401 sans session, 403 sinon).
- `app/admin/catalogue.py` : module `quiz` disponible.
- `app/points/bareme.py` : `eleve.quiz` dans `EN_SERVICE` ; `encadreur.quiz` reste à 0.
- `app/seed_dev.py` : deux quiz « Contenu de test » publiés (18 et 15 questions), un brouillon ; jamais en prod
  (`seed_preprod` n'en charge pas).
- Migration `quiz` : les cinq tables, la première version des paramètres du parcours `jeux`, `eleve.quiz` en
  service.

**Site**

- `src/lib/api/client.ts` : fonctions joueur et banque ; types régénérés (`npm run api:types`).
- `src/components/quiz/PartieQuiz.tsx` : déroulé d'une partie (question, choix, compte à rebours affiché,
  résultat), qui reçoit ses fonctions d'appel : le même composant sert au joueur et au mode test.
- `src/routes/_connecte/quiz.index.tsx` : liste des quiz publiés, filtre par axe, « Mes quiz ».
- `src/routes/_connecte/quiz.$id.tsx` : la partie.
- `src/routes/_connecte/admin/quiz.index.tsx` : la banque (onglets brouillons, soumis, publiés, dépubliés),
  création.
- `src/routes/_connecte/admin/quiz.$id.tsx` : éditeur de questions, soumission, test, décision (approuver avec
  le validateur médical, refuser, dépublier).
- `src/routes/_connecte/admin/quiz.parametres.tsx` : paramètres et historique des versions.
- `src/routes/_connecte/mon-espace.tsx` : lien « Quiz » (élève et encadreur actifs).
- `src/routes/jeux.tsx` : le bouton de la vitrine mène à `/quiz`.
- Navigation de l'espace admin : entrée « Quiz ».

**Docs** : ADR-0004 (statut, envoi paresseux, paramètres versionnés), ARCHITECTURE (modèle, droits, routes),
SECURITY (ligne quiz), TESTING si besoin, TASKS.

## Données

```
parametres_quiz   id, parcours ('jeux'), version, nb_questions, temps_ms, tolerance_ms, seuil,
                  tentatives_par_jour, cree_par, cree_le
                  unique (parcours, version) ; check seuil BETWEEN 1 AND nb_questions,
                  nb_questions BETWEEN 1 AND 50, temps_ms > 0, tolerance_ms >= 0, tentatives_par_jour >= 1

quiz              id, titre (120), description (300), axe_code → axe, etat
                  (brouillon | soumis | publie | depublie), essai_contenu (bool : « Contenu de test »),
                  contributeurs uuid[] (créé, modifié ou soumis par), soumis_par, soumis_le,
                  decide_par, decide_le, motif, validateur_nom (120), validateur_qualite (120), publie_le,
                  + Suivi (cree_le, modifie_le, version optimiste)

question_quiz     id, quiz_id → quiz (restrict), enonce (300), choix jsonb (2 à 4), bonne_reponse,
                  explication (500, facultative), ordre, active (bool)
                  checks comme `defi_question`

tentative_quiz    id, quiz_id, joueur_id → utilisateur, parametres_id → parametres_quiz, essai (bool),
                  etat (en_cours | terminee), jour (date de Lomé), commencee_le, derniere_activite,
                  terminee_le, score, reussie, mouvement_id → mouvement_points (nul sauf crédit)
                  unique partiel (quiz_id, joueur_id) WHERE etat = 'en_cours'
                  index (joueur_id, quiz_id, jour) pour le plafond

reponse_quiz      id, tentative_id → tentative (cascade), rang (1..n), question_id, ordre_choix jsonb
                  (permutation des choix), envoyee_le (nulle tant que non envoyée), repondue_le,
                  choix (index d'origine, nul si ratée), correcte (nulle tant que non tranchée)
                  unique (tentative_id, rang)
```

Une question déjà tirée dans une tentative ne s'efface pas : la « supprimer » la désactive (hors tirage et hors
compte de la réserve). Les résultats passés ne bougent pas, car chaque réponse garde `correcte`.

Les paramètres en cours sont la version la plus haute du parcours. Une tentative pointe sa version : un
changement n'agit que sur les tentatives suivantes.

## API

**Joueur** (`joueur_actif`) :

| Route                                 | Effet                                                                                        |
| ------------------------------------- | -------------------------------------------------------------------------------------------- |
| `GET /quiz?axe=`                      | Quiz publiés, avec pour le joueur : réussi, meilleur score, tentatives restantes aujourd'hui |
| `POST /quiz/{id}/tentatives`          | 201 : tire les questions, envoie la première ; 404 si non publié, 429 au plafond             |
| `GET /quiz/tentatives/{id}`           | Reprise : question en cours (heure d'envoi d'origine) ou résultat ; 404 si pas la sienne     |
| `POST /quiz/tentatives/{id}/reponses` | `{rang, choix}` : enregistre si dans le délai, renvoie la question suivante ou le résultat   |

Une question renvoyée au joueur : `rang`, `total`, `enonce`, `choix` (textes dans l'ordre mélangé), `temps_ms`
(temps affiché, pas la tolérance), `restant_ms`. Le choix envoyé est l'index dans cet ordre ; le serveur le
traduit par `ordre_choix`. Le résultat : `score`, `total`, `seuil`, `reussie`, `points` (0 ou 50).

**Banque** (`exiger_permission("quiz", …)`, journal d'audit à chaque écriture) :

| Route                                                                        | Droit                                      |
| ---------------------------------------------------------------------------- | ------------------------------------------ |
| `GET /admin/quiz?etat=`, `GET /admin/quiz/{id}`                              | consulter                                  |
| `POST /admin/quiz`                                                           | créer                                      |
| `PATCH /admin/quiz/{id}`, questions (POST, PATCH, DELETE)                    | modifier (brouillon seul, sinon 409)       |
| `POST /admin/quiz/{id}/soumettre`                                            | soumettre                                  |
| `POST /admin/quiz/{id}/reprendre`                                            | soumettre (soumis ou dépublié → brouillon) |
| `POST /admin/quiz/{id}/approuver`                                            | approuver (403 si contributeur)            |
| `POST /admin/quiz/{id}/refuser`                                              | approuver                                  |
| `POST /admin/quiz/{id}/depublier`                                            | dépublier                                  |
| `POST /admin/quiz/{id}/essais` + routes de partie `/admin/quiz/essais/{id}…` | consulter                                  |
| `GET /admin/quiz/parametres`, `PUT …`                                        | consulter, modifier                        |

Approuver et dépublier sont des droits sensibles (double authentification, déjà au catalogue). Chaque transition
verrouille la ligne du quiz (`with_for_update`) et vérifie l'état attendu : la seconde de deux décisions
simultanées reçoit 409.

## Règles de la partie

1. **Lancer** : verrou sur la ligne `utilisateur` du joueur (sérialise ses lancements). Clôt la tentative en
   cours sur ce quiz. Compte les tentatives non-essai du jour : 429 au plafond. Tire `nb_questions` questions
   (`random.SystemRandom`), une permutation des choix pour chacune, crée les lignes `reponse_quiz`, envoie la
   première.
2. **Répondre** : verrou sur la tentative. Si inactive depuis plus de 10 minutes : close (voir 4). Si `rang` n'est
   pas la question en cours : déjà répondue → renvoie l'état courant sans rien changer (double envoi) ; sinon 404.
   Choix hors limites : 422. Dans le délai (`maintenant ≤ envoyee_le + temps + tolérance`) : `correcte` selon
   le choix ; hors délai : ratée. Puis envoie la suivante, ou termine.
3. **Reprendre** (`GET`) : si la question en cours a expiré, elle est ratée et la suivante est envoyée.
4. **Terminer / clore** : les questions non tranchées sont ratées ; `score` = bonnes réponses ;
   `reussie = score ≥ seuil` de la version de la tentative. Si non-essai, réussie, joueur élève actif et quiz
   toujours publié : `points.crediter("eleve.quiz", joueur, "quiz:<quiz>:<joueur>")` — la clé unique du registre
   garantit un seul crédit, même entre deux fins simultanées. Un essai est effacé.
5. Aucune fonction de la partie ne lit `bonne_reponse` ailleurs que pour trancher une réponse reçue.

## Composants du site

`PartieQuiz` affiche la question, les choix en gros boutons (téléphone d'abord), une barre de temps sur
`temps_ms` à partir de `restant_ms`. À zéro, le site demande l'état courant (la question est perdue) ; le
site ne décide jamais du résultat. Après la dernière question : score, réussite, points gagnés ou « points déjà
gagnés », bouton « Rejouer ». Textes au tutoiement, bouton principal vert, titres en deux couleurs.

## Tests

API (écrits avant le code pour la partie, `docs/TESTING.md`) :

- `test_quiz_partie.py` : aucune clé `bonne_reponse` / `explication` dans aucune réponse joueur ; 6,9 s / 7,1 s ;
  11 et 12 sur 15 ; double envoi ; deux réponses simultanées ; deux fins simultanées → une ligne de points ;
  seconde réussite sans points ; encadreur sans points ; plafond (429) ; version de paramètres conservée ;
  reprise après coupure ; clôture après 10 minutes ; dépublié en cours de partie ; mauvais joueur (404).
- `test_quiz_banque.py` : droits (élève, encadreur, président, collaborateur sans droit → 403 ; double auth) ;
  validation des questions ; soumission sous le nombre requis ; modification d'un soumis (409) ; contributeur qui
  approuve (403) ; validateur manquant (422) ; décisions concurrentes (409) ; paramètres incohérents et nombre
  relevé au-dessus d'une réserve publiée (422) ; journal et notifications.
- `test_quiz_essai.py` : un essai ne laisse ni tentative, ni plafond consommé, ni points.

Site : `PartieQuiz.test.tsx` (déroulé, temps écoulé, résultat), éditeur de questions.

## Stress-test (2026-11-08)

| Gravité   | Point                                                                                   | Traitement                                                                                       |
| --------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Important | Effacer une question d'un quiz repris en brouillon casserait l'historique des tentatives | Question désactivée, jamais effacée une fois tirée (ci-dessus)                                  |
| Important | Relever les réponses par reprises : le score seul suffit à sonder, question par question | Accepté : tirage dans la réserve, plafond de 10 par jour, tentatives conservées pour l'analyse   |
| Important | Une petite équipe où une seule personne a les deux droits ne peut rien publier           | Accepté (choix « deux personnes ») ; le super-administrateur ajuste les droits                   |
| Mineur    | Deux changements de paramètres simultanés                                                | La contrainte unique (parcours, version) tranche : 409                                           |
| Mineur    | Essais abandonnés par un collaborateur                                                   | Effacés au lancement de l'essai suivant et après un jour                                         |
| Mineur    | ROADMAP (R9) annonce encore +25 / +10 et +25 encadreur                                  | Corrigée selon le barème harmonisé (spec 022) : +50 élève, +25 club en R13, 0 encadreur          |

Sur-engineering écarté : pas de détection d'anomalies, pas de planification ni d'import, pas de pôles.

## Points à confirmer (non bloquants)

- La vitrine `/jeux` annonce « 100 quiz officiels en 6 pôles », 10 questions par quiz. Le paramètre par défaut
  reste 15 (Q12) ; il se change dans l'admin si l'équipe garde 10. Les pôles ne sont pas modélisés : les quiz se
  classent par axe (Q1). À revoir quand l'équipe pédagogique livrera la banque.
- Le seuil de 12/15 reste à confirmer avec Q24.
