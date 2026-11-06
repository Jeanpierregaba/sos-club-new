# 022 — Plan technique

## Approche

Une migration aligne le barème en base, sans écraser un montant réglé par l'admin (mise à jour seulement si la
ligne a encore l'ancienne valeur par défaut). La question du jour gagne une table de réponses : la contrainte
unique (élève, jour) garantit une seule réponse comptée, et la clé d'idempotence du registre
(`question_jour:<élève>:<jour>`) un seul crédit. Le site ne fait qu'afficher les montants.

## Fichiers touchés

- `backend/app/points/bareme.py` : grille alignée, nouvelles actions (`eleve.question_jour`, `eleve.badge`,
  `club.bienvenue_eleve`, `club.commentaire_eleve`, `club.republication_eleve`, `club.partage_eleve`,
  `club.question_jour_eleve`, `club.badge_eleve`) ; `eleve.question_jour` en service.
- `backend/alembic/versions/…_harmonisation_bareme.py` : mises à jour conditionnelles, insertions, table
  `defi_reponse`.
- `backend/app/jeux/models.py`, `defis.py`, `router.py`, `schemas.py` : réponse d'un élève, crédit,
  « déjà répondu » ; session facultative sur les deux routes du défi.
- `src/components/BulleDefi.tsx`, `src/routes/jeux.tsx`, `src/lib/quiz.ts`, `src/routes/certification.tsx`,
  `src/components/PodiumClubs.tsx`, `src/routes/club-sante.tsx`, `src/routes/inscription.tsx`.
- `docs/PRD.md` (barème, Q7), spec 021 (le défi rapporte désormais des points), `ARCHITECTURE.md`, `SECURITY.md`.

## Données

- `bareme` : montants mis à jour (`eleve.quiz` 25→50, `club.quiz_eleve` 10→25, `club.certification_eleve`
  100→500, `encadreur.quiz` 25→0 ; `club.rapport_activite` reste à 50, proposé) et 8 lignes ajoutées. Non destructif.
- `defi_reponse` : `id`, `eleve_id` (FK utilisateur), `defi_id` (FK defi_question), `jour` (date de Lomé),
  `choix`, `correcte`, `mouvement_id` (FK mouvement_points, nul sans crédit), `repondu_le` ; unique
  (`eleve_id`, `jour`).

## API / interfaces

- `GET /api/jeux/defi-du-jour` : ajoute `ma_reponse` (`choix`, `correcte`, `bonne_reponse`, `explication`,
  `points`) si l'élève connecté a déjà répondu aujourd'hui ; jamais la bonne réponse sinon.
- `POST /api/jeux/defis/{id}/reponse` : ajoute `points` (gagnés par cette réponse) et `deja_repondu`.

## Dépendances

Aucune.

## Sécurité

- Correction et crédit côté serveur ; la bonne réponse ne part qu'avec la correction.
- Crédit seulement pour un élève au compte actif, pour la question du jour même, une fois par jour.
- Les points se lisent dans le registre, une ligne par crédit (ADR-0004).

## Tests

API : migration (montants, valeur réglée conservée), réponse juste (+20, une ligne), fausse (0, bloquée),
deuxième réponse, réponses simultanées, visiteur/encadreur sans point, question d'un autre jour, barème à 0.
Site : bulle (élève, déjà répondu, visiteur), Jeux et Certification sans montant obsolète.

## Risques

- Une question erronée peut créditer à tort : l'admin la désactive ; la correction des crédits passe par des
  annulations tracées (écran à venir).
