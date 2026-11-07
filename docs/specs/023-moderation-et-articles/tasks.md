# 023 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Cochée dès qu'elle est faite et commitée. -->

**API, socle**

- [x] 1. Modèles `Contenu`, `VersionContenu`, `DecisionModeration`, `Notification` et migration
      `moderation_articles_notifications` (tables, contraintes, index, `eleve.article` et `encadreur.article` en
      service). Module `moderation` disponible, `consulter` sensible.
- [x] 2. Domaine `notifications` : service, routes, `test_notifications.py`.

**API, articles et modération**

- [x] 3. Registre des types, schémas des articles, service de l'auteur (`creer`, `modifier`, `soumettre`, `retirer`,
      `supprimer`) et routes `/mes-articles`. Avec `test_articles_auteur.py`.
- [x] 4. Tests des décisions (`test_moderation_decisions.py`) écrits **avant** le code. Ils doivent échouer.
- [x] 5. `moderation/decisions.py` et les routes `/admin/moderation` (file, aperçu, quatre décisions). La tâche 4
      passe.
- [x] 6. Lecture publique `/articles`, signature, adresse. Avec `test_articles_publics.py`.
- [x] 7. Admin existant : indicateur du tableau de bord et compteur du menu, historique de la fiche, libellés du
      journal. Seed de démonstration. Export OpenAPI et `npm run api:types`.

**Site**

- [x] 8. `react-markdown`, `TexteArticle` (test Vitest), `EtatContenu`, client d'API.
- [ ] 9. « Mes articles » : liste, création, édition avec aperçu, soumission, retrait ; lien depuis `/mon-espace`.
- [ ] 10. Pages publiques `/articles` et `/articles/$adresse` ; lien depuis `/magazine`.
- [ ] 11. Admin : page `/admin/moderation` (file, filtres, aperçu avant / après, décisions), menu et compteur.
- [ ] 12. Cloche des notifications dans les en-têtes et page `/notifications`.

**Clôture**

- [ ] 13. Documentation (`ARCHITECTURE.md`, `SECURITY.md`, index des ADR), vérification de chaque critère en local
      et dans le navigateur, sur téléphone ; relecture par le sous-agent `reviewer` et corrections ; `TASKS.md` et
      `docs/SESSION-LOG.md`.
