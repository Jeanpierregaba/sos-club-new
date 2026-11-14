# 036 — Tâches

Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (classements, correction,
privacy) sont écrites en TDD : les tests précèdent le code.

- [x] 1. ADR-0013 (classements publics et correction des points) ; mettre à jour `docs/PRD.md`, `docs/ROADMAP.md`,
      `docs/DESIGN.md`, `docs/SECURITY.md` et `docs/TESTING.md` ; lier la spec 034 et la spec 036.
- [x] 2. Migration non destructive et modèles : `mouvement_points.motif`, contraintes `montant_signe` et
      `motif_correction`, valeur `admin` du barème, ligne technique `admin.correction`, index de classement et de
      registre ; test d'aller-retour et des lignes existantes.
- [x] 3. Tests puis code des requêtes de classement dans `points/classements.py` : élèves, encadreurs et clubs ;
      national et DRE ; semestre et historique ; égalités ; exclusions (suspendus, anciens, encadreurs non
      vérifiés, clubs hors service) ; score décimal ; pagination ; absence de semestre.
- [ ] 4. Tests puis code des routes publiques et personnelles : `GET /classements`, `/classements/moi`,
      `/classements/mon-club` et `/admin/points/classements` ; schémas fermés, tests de privacy et d'accès ;
      types de l'API et client du site.
- [ ] 5. Tests puis code du registre admin et de la recherche de bénéficiaires : filtres combinés, pagination,
      champs, absence d'écriture, double authentification et périmètre national.
- [ ] 6. Tests puis code de la correction et de l'annulation : motif, bornes, rôles, aucune part de club, semestre
      et année, journal, idempotence, total négatif, annulation avec part de club et semestre d'origine ; mise à
      jour de `test_clubs_podium.py` avec de vraies lignes de registre.
- [ ] 7. Site : page publique `/hall-of-fame`, entrée **Classements** du menu, filtres dans l'URL, podium,
      pagination, états vides et d'erreur, mobile.
- [ ] 8. Site : rangs personnels dans l'espace élève et encadreur, classement interne du club, distinction avec
      l'année académique, remplacement de « Les classements arrivent bientôt ».
- [ ] 9. Site : onglets **Registre** et **Classements** de l'admin, tableaux, filtres, dialogues de correction et
      d'annulation, refus hors périmètre.
- [ ] 10. Lint, typecheck, tests backend et site ; vérification dans le navigateur ; relecture `reviewer` ;
      `TASKS.md`.
- [ ] Vérifier tous les critères d'acceptation de `spec.md`.
- [ ] Relecture finale par le sous-agent `reviewer`.
