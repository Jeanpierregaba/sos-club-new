# 048 — Plan technique

## Approche

Les vies ne sont pas une nouvelle table : elles se **comptent** à partir des parties existantes (`tentative_quiz`).
Vies perdues du jour = parties terminées non réussies du jour (jeux et certification, hors essais) ; une partie en
cours réserve une vie. Vies restantes = 7 − perdues − en cours. Le contrôle se fait dans `partie.lancer`, sous le
verrou du joueur déjà en place, donc sans course possible.

Le chrono passe par une **nouvelle version des paramètres** de chaque parcours (le mécanisme versionné de la
spec 027) : une partie en cours garde sa version, les suivantes prennent 15 s.

## Fichiers touchés

- `backend/app/quiz/vies.py` (nouveau) : `VIES_PAR_JOUR = 7`, `vies_du_jour(db, joueur, jour)`.
- `backend/app/quiz/partie.py` : refus du lancement à 0 vie (`PlusDeVies`, 409) ; vies restantes dans l'état
  et la fin de partie.
- `backend/app/quiz/router.py`, `schemas.py` : `GET /api/quiz/vies` ; champ `vies` dans les réponses de partie.
- `backend/app/certification/joueur.py` : vies dans la vue du parcours de certification.
- `backend/app/quiz/parametres.py` : valeurs par défaut à 15 000 ms.
- Migration : nouvelle version des paramètres des deux parcours, copie de la version en cours avec
  `temps_ms = 15000` (aucune valeur réglée par l'admin n'est perdue).
- Site : composant `Vies` (7 cœurs), sur `/jeux`, la certification et la fin de partie ; bouton de lancement
  désactivé à 0 avec le message ; message d'erreur de l'API affiché si besoin.

## Données

Aucune nouvelle table. Une migration de données : une ligne `parametres_quiz` par parcours.

## API / interfaces

- `GET /api/quiz/vies` → `{restantes, total, perdues, en_cours}` (joueur connecté).
- `POST` de lancement : 409 « Tu as utilisé tes 7 vies aujourd'hui… » quand il n'en reste plus.
- Les réponses de partie (fin) ajoutent `vies_restantes`.

## Sécurité

Le contrôle est côté serveur (ADR-0004) ; le site ne fait qu'afficher.

## Tests

API : 7 parties ratées bloquent ; réussie ne coûte rien ; abandon compte ; partie en cours réserve ; lendemain ;
essais exclus ; jeux + certification partagent la réserve ; nouvelle version à 15 s, partie en cours inchangée.
Site : affichage des cœurs, bouton désactivé à 0.

## Risques

- Certification « arrêt à la première erreur » : les vies peuvent partir vite ; c'est voulu.
- Changer 7 demande un déploiement (choix de simplicité ; un réglage admin pourra venir plus tard).
