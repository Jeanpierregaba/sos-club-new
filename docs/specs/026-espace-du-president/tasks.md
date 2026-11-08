# 026 — Tâches

Chaque tâche se termine par lint, typecheck et tests verts, puis un commit.

**API**

- [x] 1. Tests de la vue du club, des propositions de fiche et des actualités (`test_espace_club.py`,
      `test_fiche_club.py`, `test_actualites.py`) écrits **avant** le code. Ils doivent échouer.
- [x] 2. Migration `contenus_du_club` (`club_id`, contraintes, index unique de la proposition en attente) et
      réglages du moteur (`depublication`, fiche actuelle dans l'aperçu, club bénéficiaire des seuls types à
      points).
- [ ] 3. Vue « Mon club » et propositions de fiche (`clubs/espace.py`, dépendance `President`). Les tests de
      `test_espace_club.py` et `test_fiche_club.py` passent.
- [ ] 4. Actualités : rédaction paramétrée par le type, routes `/clubs/moi/actualites` avec photos, lecture
      publique (fiche du club, `/articles`), transfert d'auteur à la passation. `test_actualites.py` passe.
      Export OpenAPI et `npm run api:types`.

**Site**

- [ ] 5. Page « Mon club » (président et lecture), proposition de fiche, lien depuis « Mon espace » et pour les
      encadreurs ; tests Vitest.
- [ ] 6. Éditeur des actualités (réutilise l'éditeur et les photos des articles), actualités sur la fiche du club
      et dans `/articles`, centre de modération (types `actualite` et `fiche_club`). Démonstration dans
      `seed_dev.py`.

**Clôture**

- [ ] 7. Documentation (ADR-0009, `ARCHITECTURE.md`, `SECURITY.md`), vérification de chaque critère ; relecture
      par le sous-agent `reviewer` et corrections ; `TASKS.md` et `docs/SESSION-LOG.md`.
