# 032 — Plan technique

## Modèle de données (migration Alembic après `ceae698cb3d6`)

Table `partie_quel_axe`, déclarée dans `backend/app/jeux/models.py` :

| Colonne                 | Type                  | Règle                                                       |
| ----------------------- | --------------------- | ----------------------------------------------------------- |
| `id`                    | UUID                  | uuid7                                                       |
| `eleve_id`              | FK `utilisateur.id`   | `ON DELETE CASCADE` : effacée avec le compte                |
| `numero`                | smallint              | `CHECK numero BETWEEN 1 AND 3`, `UNIQUE (eleve_id, numero)` |
| `version_questionnaire` | smallint              | 1 pour cette spec                                           |
| `reponses`              | JSONB                 | liste de 7 lettres ou `null`                                |
| `principal`             | varchar(4), nullable  | rempli à la fin                                             |
| `autres`                | JSONB, nullable       | les 2 axes complémentaires                                  |
| `commencee_le`          | timestamptz           | —                                                           |
| `terminee_le`           | timestamptz, nullable | `null` = en cours                                           |

Contraintes supplémentaires :

- Un index unique partiel `(eleve_id) WHERE terminee_le IS NULL` garantit une seule partie en cours par élève.
- `CHECK` : soit la partie est en cours (`principal` et `terminee_le` nuls), soit elle est terminée (les deux
  remplis).

## Domaine `app/jeux/quel_axe.py`

- Ajouter les questions 6 et 7 et leurs 8 correspondances.
- Créer `QUESTIONNAIRES = {1: QUESTIONS}` et `VERSION = 1`. Le calcul prend la version de la partie.
- Le calcul reste une fonction pure. Il est déjà testé, et l'on ajoute les nouvelles égalités.

Nouveau `app/jeux/parties_quel_axe.py`, qui porte les règles :

- `LIMITE = 3`.
- **`etat(db, eleve)`** renvoie :
  - le compteur (utilisées, restantes) ;
  - la partie en cours (id, numéro, réponses) ;
  - l'historique des parties terminées.
- **`commencer(db, eleve)`** :
  - verrouille la ligne `utilisateur` (`SELECT … FOR UPDATE`) ;
  - renvoie la partie en cours s'il y en a une ;
  - sinon, s'il reste une participation, crée la partie n° utilisées + 1 ;
  - sinon, lève `PlusDeParticipation` (403).
  - Une `IntegrityError` résiduelle entraîne une nouvelle lecture de l'état et le renvoi de la partie en cours.
- **`repondre(db, eleve, partie_id, numero, lettre)`** : agit sur une partie de l'élève (404 sinon) qui est en
  cours (409 sinon), sous verrou de la ligne.
- **`terminer(db, eleve, partie_id)`** : exige 7 réponses (400 sinon), calcule le résultat, puis remplit
  `principal`, `autres` et `terminee_le`. L'appel est idempotent : une partie déjà terminée renvoie son résultat.
- Aucun appel au domaine `points`.

## API (`app/jeux/router.py`, dépendance `EleveActif` déjà en place)

| Méthode | Chemin                                              | Réponse                                                                       |
| ------- | --------------------------------------------------- | ----------------------------------------------------------------------------- |
| GET     | `/api/jeux/quel-axe`                                | `EtatQuelAxe` : questions, limite, utilisées, restantes, en_cours, historique |
| POST    | `/api/jeux/quel-axe/parties`                        | `PartieQuelAxe` (201 si créée, 200 si reprise), 403 au-delà de 3              |
| PUT     | `/api/jeux/quel-axe/parties/{id}/reponses/{numero}` | `{lettre}` → `PartieQuelAxe`                                                  |
| POST    | `/api/jeux/quel-axe/parties/{id}/fin`               | `ResultatQuelAxe` (+ numéro, date)                                            |
| GET     | `/api/jeux/quel-axe/parties/{id}`                   | la partie et son résultat, 404 si elle n'est pas à l'élève                    |

- L'ancienne route sans mémoire `POST /api/jeux/quel-axe/resultat` est supprimée, car elle permettait de jouer
  sans être décompté.
- Les scores détaillés ne sont plus renvoyés : ils ne servent pas à l'affichage.
- Les types du site sont régénérés (`export_openapi` puis `npm run api:types`).

## Site

- **`src/components/QuelAxe.tsx`** : accroche, « sept questions », mentions « Réservé aux élèves inscrits ·
  3 participations maximum », bouton « Commencer le jeu ».
- **`src/components/QuelAxeTest.tsx`**, à réécrire en écrans :
  - Accueil du jeu : compteur, puis « Commencer », « Reprendre la partie » ou le message 3/3, avec l'historique.
  - Question : sauvegarde à chaque choix (`useMutation`), boutons Précédent et Suivant, « Question X sur 7 ».
  - Résultat : partage, « Découvrir cet axe », « Rejouer (Y restante(s)) ».
  - Historique : revoir et partager chaque résultat.
  - La ligne d'information sur la conservation.
- **`src/lib/api/client.ts`** : `etatQuelAxe`, `commencerQuelAxe`, `repondreQuelAxe`, `terminerQuelAxe` et
  `partieQuelAxe`.
- **`src/routes/_connecte/mon-espace.tsx`** : un bloc élève « Mon axe » avec le compteur, les derniers résultats
  et un lien vers le jeu (`/?test=quel-axe#quel-axe`).
- Les textes et les mascottes des résultats restent dans `src/lib/axes-decouverte.ts`, sans changement.

## Tests

- **API (`backend/tests/test_jeux_quel_axe.py`)** :
  - le barème (4 fois en axe principal par axe), le départage et des égalités ;
  - le parcours 1/3, puis la reprise, la modification d'une réponse, la fin et le parcours 2/3 et 3/3 ;
  - le refus de la 4e partie ;
  - la concurrence, avec deux démarrages en parallèle (`asyncio.gather`, comme pour les tentatives de quiz) ;
  - 401, 403 (autre profil, compte suspendu) et 404 (partie d'un autre) ;
  - 409 après la fin ;
  - zéro mouvement de points ;
  - l'effacement des parties avec le compte.
- **Site (Vitest)** : l'écran du compteur selon l'état (Commencer, Reprendre, 3/3), « Rejouer » masqué à 3/3,
  et aucun « 5 questions ».

## Documentation

- `docs/SECURITY.md` : la ligne sur « Quel axe » (parties gardées, limite garantie par la base, données de
  mineurs effacées avec le compte).
- `docs/PRD.md` : le jeu passe à 7 questions et 3 participations.
- Marquer la spec 021 comme dépassée sur ce point.
- `TASKS.md`.

## Risques

- **Concurrence.** Elle est tenue par le verrou du compte et les deux contraintes uniques. Le test parallèle est
  obligatoire.
- **Ancienne route supprimée.** Un site déjà déployé qui l'appelle reçoit un 404 tant que le site n'est pas mis à
  jour. Les deux sont déployés ensemble, donc c'est acceptable.
