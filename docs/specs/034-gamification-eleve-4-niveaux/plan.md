# 034 — Plan

Quatre lots, chacun avec sa migration, ses tests, sa relecture et son commit. Un ADR (ADR-0012) consigne la part
du club à 50 % en demi-points, l'année académique et le remplacement du barème de la spec 022.

## Lot 1 — Part du club et nouveau barème

**Données** (migration) :

- `mouvement_points` reçoit `club_id` (club crédité, nul sinon) et `demi_points_club` (la part du club, en
  demi-points : +5 élève → 5 demi-points, soit 2,5). Un `CHECK` impose les deux ensemble, et une part égale au
  montant de l'élève (`demi_points_club = montant`). Un index partiel sur `club_id` sert les totaux (le lot 4
  ajoute `annee_id`).
- `bareme` reçoit `parcours` (`certification`, `jeux`, `vie`, nul pour l'encadreur) et `sous_compte`
  (`quiz`, `etoiles`, nul sinon).
- Nouvelles lignes (format de code `eleve.<action>`, sans chiffre) : `eleve.quiz_debutant` (50),
  `eleve.quiz_intermediaire` (100), `eleve.quiz_avance` (150), `eleve.quiz_expert` (200), `eleve.etoile_debutant`
  à `eleve.etoile_expert` (500, 1 000, 1 500, 3 000), `eleve.quiz_certification` (50), ajoutées hors service :
  chaque lot met les siennes en service (et sort `eleve.quiz` au lot 2). Les montants existants restent
  (100, 5, 10, 50, 50, 20, 500, 1 000). Les lignes `club.*_eleve` sont désactivées, pas supprimées
  (`docs/RULES.md`). Rien n'est recalculé.

**Code** :

- `points.service.crediter` : pour une action de bénéficiaire `eleve`, il cherche l'adhésion active de l'élève
  (`clubs.models.Adhesion`, état `active`) et vérifie que le club est en service
  (`clubs.activation.est_en_service`). Si c'est le cas, il écrit `club_id` et `demi_points_club` dans la même
  ligne. La clé d'idempotence reste unique : un seul crédit, pour l'élève comme pour le club.
- `points.service.annuler` copie `club_id` avec la part négative.
- `scores_des_clubs` devient la somme des demi-points ÷ 2 (le podium de l'accueil s'en sert déjà).
- Les montants de club s'affichent avec une décimale (`2,5`) : schémas en `float` côté API, formatage `fr-FR`
  côté site.
- La page admin du barème montre le parcours et la règle « club = 50 % ».

**Tests** : crédit d'un élève affilié ou non, club suspendu, annulation, changement d'établissement, encadreur,
concurrence (deux crédits simultanés → une ligne).

## Lot 2 — Les 100 quiz Jeux, les étoiles, la carte Gold

**Données** (migration avec données) :

- `quiz` reçoit `niveau` (`debutant`, `intermediaire`, `avance`, `expert`), `numero` (1 à 100, unique parmi
  les quiz Jeux) et `lot`. Un `CHECK` impose que niveau et numéro ne servent qu'aux quiz Jeux.
- `backend/alembic/donnees/defis_jeux.json` : les 100 défis (numéro, titre, cotation, lot du pôle), extraits de
  `src/lib/quiz.ts`. Le niveau est tiré de la cotation (40 / 30 / 20 / 10 par rang, ex æquo départagés par
  numéro).
- La migration crée les 100 quiz publiés. Chacun reçoit une réserve de 20 questions copiées du lot de son pôle :
  une fenêtre qui tourne sur le lot, pour que deux quiz voisins ne partagent qu'une partie de leurs questions.
  Les 34 anciens quiz Jeux sont dépubliés : leurs parties restent dans l'historique.
- `etoile_obtenue` (élève, niveau, mouvement, date), unique par élève et niveau.

**Code** :

- `quiz.partie._terminer` : pour un quiz Jeux réussi par un élève actif, il crédite l'action du niveau du quiz
  (`eleve.quiz.<niveau>`, clé `quiz:<quiz>:<élève>` inchangée). Ensuite, il vérifie l'étoile du niveau : tous
  les quiz publiés du niveau réussis → insertion `ON CONFLICT DO NOTHING`, puis crédit `eleve.etoile.<n>`.
- Domaine `jeux/progression.py` : quiz réussis par niveau, étoiles, statut Gold (4 étoiles), sous-totaux
  « points des quiz » et « points des étoiles ».
- Le catalogue `/api/jeux/quiz` donne le numéro et le niveau de chaque quiz. Pour un élève connecté, il donne
  aussi sa progression. La page Jeux relie chaque défi à son quiz par numéro (fin de la répartition par lot du
  site) et affiche les niveaux Débutant, Intermédiaire, Avancé et Expert.
- Le site : bandeau de progression Jeux (quiz sur 100, étoiles, deux sous-totaux, total), carte de membre
  (Gold avec les 4 étoiles) dans « Mon espace ».
- Admin : réglage du niveau d'un quiz dans la banque ; liste des élèves Gold (pseudonyme, club, date).

## Lot 3 — La certification à 20 places

**Données** (migration) :

- Les places vont de 1 à 20 (`PLACES = 20`, contraintes `place_valide` et `dernier_palier`).
- `parametres_quiz` reçoit `arret_premiere_erreur` (vrai pour la certification) ; `tentatives_par_jour` devient
  nullable (nul = aucun plafond). Nouvelle version des paramètres de certification : 10 questions, 20 s, seuil
  10, sans plafond, arrêt à la première erreur.
- Nouvelle version des règles de badges : paliers 4, 8, 12, 16, 20 et les 5 noms officiels. Les badges déjà
  délivrés gardent leur nom (copié).

**Code** :

- `quiz.partie.repondre` : en certification, une réponse fausse ou un temps dépassé termine la tentative tout de
  suite (non réussie). La partie suivante repart de la question 1, avec un nouveau tirage.
- `certification.progression.enregistrer_reussite` : +50 par place validée (`eleve.quiz_certification`, clé
  `certification:place:<place>:<élève>`). Les badges et le certificat suivent les nouvelles règles.
- Les thématiques : la thématique `k` regroupe les places `4k-3` à `4k` et porte le nom de son badge. Le
  parcours de l'élève les affiche ainsi.
- Seed : 20 quiz de certification « [Test] ».

## Lot 4 — Année académique, tableau de bord, archives

**Données** (migration) :

- `annee_academique` (libellé « 2026-2027 », début, fin, clôturée le, clôturée par), sans chevauchement
  (contrainte d'exclusion, comme `semestre`). `mouvement_points.annee_id` est posé à chaque crédit.
- `classement_annuel` : instantané figé à la clôture (année, région, élève, pseudonyme, club, points, rang),
  unique par année et élève.
- `utilisateur.ancien_eleve_le` : nul pour un élève actif.

**Code** :

- `points.service` : totaux annuels (élève, club) par parcours et sous-compte ; `crediter` refuse les actions
  d'élève pour un ancien élève.
- Admin : créer et clôturer une année (la clôture fige le classement régional, une seule fois, après la date de fin).
  Pas de modification : une date fausse se corrige par une migration, les gains déjà rattachés à l'année restant à
  vérifier ;
  passer un élève en ancien élève.
- `GET /api/eleves/moi/gamification` : vue annuelle, rang régional (région du club, sinon de l'établissement),
  place dans le club, décompte des trois parcours, actions en attente de modération, archives par année.
- Site : tableau de bord dans « Mon espace » ; total annuel du club par parcours dans « Mon Club Santé ».
- Seed : année 2026-2027 ouverte.

## Points d'attention

- La spec 022 et le PRD (barème) sont mis à jour pour renvoyer à cette spec.
- `MONTANT_MAX` (10 000) couvre le plus gros montant (3 000).
- Lot 2 : environ 2 000 lignes de questions copiées (100 × 20) : la migration les insère par lots.
- Les tests des parcours complets (100 quiz, 20 places) utilisent des fabriques qui marquent les réussites
  directement en base, sans jouer chaque partie.
