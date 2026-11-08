# 025 — Tâches

Chaque tâche se termine par lint, typecheck et tests verts, puis un commit.

**API**

- [x] 1. Tests de l'envoi, de la modération et de la lecture publique des commentaires
      (`test_commentaires_envoi.py`, `test_commentaires_moderation.py`, `test_commentaires_publics.py`) écrits
      **avant** le code. Ils doivent échouer.
- [x] 2. Migration `commentaires` (`parent_id`, état `retire`, contraintes, index, barème en service) et
      réglages par type du moteur (`adresse`, `correction`, `points_permis`, `a_la_publication`, attente comptée
      par type). Les suites de la spec 023 restent vertes.
- [x] 3. Domaine `commentaires` : envoi (normalisation, anti double envoi, 20 par jour), liste publique,
      « Mes commentaires », retrait ; file et aperçu avec l'article parent. Les tests de la tâche 1 passent.
      Export OpenAPI et `npm run api:types`.

**Site**

- [x] 4. `Commentaires.tsx` sous l'article (liste, champ, confirmation, invitation à se connecter), avec un test
      Vitest.
- [x] 5. Page « Mes commentaires » et lien dans le menu ; centre de modération : type, article parent, « À
      corriger » masqué pour un commentaire. Commentaires de démonstration dans `seed_dev.py`.

**Clôture**

- [x] 6. Documentation (ADR-0009, `ARCHITECTURE.md`, `SECURITY.md`), vérification de chaque critère ; relecture
      par le sous-agent `reviewer` et corrections ; `TASKS.md` (note R13) et `docs/SESSION-LOG.md`.
