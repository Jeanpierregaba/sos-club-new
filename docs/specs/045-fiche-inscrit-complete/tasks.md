# 045 — Tâches

Dans l'ordre d'exécution, chacune testable et committable seule. Les droits et les données de mineurs sont critiques
(`docs/TESTING.md`) : leurs tests précèdent le code.

## API

- [x] 1. Documents : `TASKS.md` (spec 045 en cours).
- [x] 2. Tests de la modification (`test_admin_inscrit_modification.py`), écrits avant le code : identité, profil
  élève, profil encadreur, règles, champs hors profil, rien à changer, journal sans donnée en clair, version
  périmée, compte admin, droits.
- [x] 3. Modification : schéma `ModificationInscrit`, `modification_inscrit.py`, route `PATCH`, `version` dans le
  détail, action au journal et à l'historique.
- [x] 4. Points : filtre `utilisateur_id` du registre, route `/points`, tests (pagination, filtre semestre, lignes
  d'autres comptes exclues, corrections).
- [x] 5. Quiz : `parcours_inscrit.quiz`, route `/quiz`, tests (validés, tentatives, essai, en cours, filtres, résumé,
  aucune réponse). Vérifier l'index sur `tentative_quiz.joueur_id`.
- [x] 6. Certification : `parcours_inscrit.certification`, route, tests (progression, badges, certificats, vide).
- [x] 7. Contenus : `parcours_inscrit.contenus`, route, tests (liste, filtres, autres auteurs exclus).
- [x] 8. Droits de toutes les nouvelles routes (consulter, modifier, DRE, élève, encadreur, non connecté) et
  `no-store`.

## Site

- [x] 9. Types de l'API régénérés, fonctions du client.
- [x] 10. Liste : ligne entière cliquable.
- [x] 11. Fiche en onglets, onglet dans l'URL ; sections existantes déplacées sans changement.
- [x] 12. Dialogue de modification et ses tests Vitest.
- [x] 13. Onglets Points, Quiz, Certification et Contenus, avec leurs états vides.
- [ ] 14. Vérification au navigateur (375 px et ordinateur) sur la base de dev. **Reste à faire** : la fiche
  demande une connexion admin, que l'agent ne peut pas ouvrir.

## Clôture

- [x] 15. Lint, typecheck, tests ; relecture par le sous-agent `reviewer` ; critères cochés ; `TASKS.md` à jour.
