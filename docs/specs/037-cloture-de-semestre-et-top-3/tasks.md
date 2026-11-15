# 037 — Tâches

Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (photo du classement,
ex æquo, cycle de clôture, données publiques) sont écrites en TDD : les tests précèdent le code.

- [x] 1. Documents : mettre à jour `docs/PRD.md` (ligne R14), `docs/ROADMAP.md`, `docs/DESIGN.md` (section
      Palmarès de `/hall-of-fame`, onglet Clôtures) et ADR-0013 (renvoi vers la règle d'ex æquo publiée) ;
      `TASKS.md` : R14 en cours.
- [x] 2. Migration non destructive et modèles `ClotureSemestre`, `CandidatCloture`, `EtatCloture` : contraintes
      d'état, d'unicité (rang, place, élève) et d'écart ; test d'aller-retour de la migration.
- [ ] 3. Tests puis code de `classement_a_figer` dans `points/classements.py` : 50 premiers, exclusions
      (suspendus, anciens, totaux nuls ou négatifs), rang brut et rang départagé, date d'atteinte, ex æquo par
      date puis pseudonyme, égalité qui déborde la 3e place.
- [ ] 4. Tests puis code du gel et du regel dans `points/clotures.py` : refus avant la date de fin, photo copiée
      (libellé, dates, pseudonyme, club, DRE), une seule clôture sous deux gels simultanés, regel qui reporte les
      écarts, regel refusé hors état gelé, journal.
- [ ] 5. Tests puis code de l'écart, de la réintégration et du Top 3 proposé : motif 10 à 500 caractères, candidat
      suivant qui monte, refus hors état gelé, journal ; écart avec le classement actuel (`top3_different`).
- [ ] 6. Tests puis code de la validation, de l'annulation de validation et de la publication : moins de trois
      candidats, aucun candidat, motif d'annulation, lauréat suspendu, notifications dans la même transaction,
      aucune ligne de registre, plus aucune modification après publication, conflit entre deux admins.
- [ ] 7. Tests puis code des routes : admin des clôtures (droits, double authentification, périmètre national,
      collaborateur de DRE refusé), `GET /api/palmares` (schéma fermé, clés exactes, écartés et non publiés
      absents, valeurs figées), champ `distinctions` de `/classements/moi` ; types de l'API et client du site.
- [ ] 8. Site : section **Palmarès des semestres** de `/hall-of-fame` (lauréats, règle d'ex æquo, état vide,
      mobile) et bloc **Mes distinctions** de l'espace élève ; tests des composants.
- [ ] 9. Site : onglet **Clôtures** de l'admin, liste des semestres et écran d'une clôture (photo, Top 3 proposé,
      écarts, actions selon l'état, dialogues motivés, écart avec le classement actuel, refus affichés) ;
      libellés du journal dans `src/lib/admin.ts`.
- [ ] 10. Lint, typecheck, tests backend et site ; vérification dans le navigateur ; `TASKS.md`.
- [ ] Vérifier tous les critères d'acceptation de `spec.md`.
- [ ] Relecture finale par le sous-agent `reviewer`.
