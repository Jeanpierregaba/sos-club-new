# 001 — Tâches

Une fois une tâche terminée : lint, typecheck et tests, puis tâche cochée et commit proposé.

- [x] 1. Configuration des tests : base `sosclub_test` créée et migrée automatiquement, données effacées entre deux tests, tests `/health` conservés
- [x] 2. Modèles `Utilisateur`, `Session`, `TentativeConnexion` et première migration, testée à l'aller et au retour
- [x] 3. Écrire les tests de hachage et de normalisation (en échec), puis ajouter `argon2-cffi` et implémenter `motdepasse.py` et la normalisation
- [x] 4. Écrire les tests de connexion, sans les limites (en échec)
- [x] 5. Implémenter la connexion, le cookie et la session
- [x] 6. Écrire les tests de limites d'essais (en échec), puis les implémenter
- [x] 7. Écrire les tests de session et de déconnexion (en échec), puis implémenter `utilisateur_courant`, `/moi` et `/deconnexion`
- [x] 8. Écrire les tests de droits (en échec), puis implémenter `exiger_role` et `/api/admin/chiffres`
- [x] 9. Écrire les tests d'origine (en échec), puis implémenter `verifier_origine` et les erreurs de validation sans le mot de passe
- [x] 10. Écrire les tests de la commande (en échec), puis implémenter `creer_compte`
- [x] 11. Exporter `backend/openapi.json` avec son test, ajouter `openapi-typescript` et `npm run api:types`, vérification dans la CI
- [x] 12. Proxy `/api` et port 3000 dans Vite, `client.ts` et `chargerMoi`, avec l'appel vérifié côté navigateur et côté serveur
- [x] 13. Tests puis implémentation de `redirection.ts`
- [x] 14. Page `/connexion` : formulaire, erreurs, responsive, avec ses tests
- [x] 15. Garde `_connecte` et page `/mon-espace`, y compris le message d'API indisponible et les chiffres pour l'admin
- [x] 16. En-tête de l'accueil : « Se connecter » ou « Mon espace », API arrêtée incluse
- [x] 17. `lang="fr"`, pages 404 et d'erreur en français
- [x] 18. Documentation : ADR-0006, ADR-0002, ADR-0003, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `.env.example`, `AGENTS.md`, `backend/README.md`
- [x] 19. Parcours complet dans le navigateur, avec chaque rôle, à 320 px et au clavier
- [x] Vérifier tous les critères d'acceptation de spec.md
- [x] Relecture par le sous-agent reviewer, constats bloquants et importants corrigés
