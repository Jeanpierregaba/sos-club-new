# 034 — Tâches

Les points et les quiz sont critiques (`docs/TESTING.md`) : dans chaque lot, les tests précèdent le code.

## Lot 1 — Part du club et barème

- [x] 1. ADR-0012 ; spec 022 et PRD renvoient à la spec 034
- [x] 2. Migration : `club_id`, `demi_points_club`, `parcours`, `sous_compte`, nouvelles lignes, anciennes hors service
- [x] 3. Tests puis code : `crediter` et `annuler` avec la part du club, `scores_des_clubs`
- [x] 4. Site et admin : montants à décimale, parcours dans le barème ; types régénérés ; relecture ; commit

## Lot 2 — Jeux

- [x] 5. `defis_jeux.json` et migration des 100 quiz (niveau, numéro, lot, réserves), `etoile_obtenue`
- [x] 6. Tests puis code : gain par niveau, étoiles, Gold, sous-totaux
- [x] 7. API du catalogue et de la progression ; admin (niveau d'un quiz, liste Gold)
- [x] 8. Site : page Jeux par numéro et niveau, progression, carte de membre ; relecture ; commit

## Lot 3 — Certification

- [x] 9. Migration : 20 places, paramètres (arrêt à la première erreur, sans plafond), règles de badges
- [x] 10. Tests puis code : arrêt à la première erreur, +50 par place, badges par thématique, certificat
- [x] 11. Site : parcours en 5 thématiques ; seed de 20 quiz ; relecture ; commit

## Lot 4 — Année académique

- [x] 12. Migration : `annee_academique`, `annee_id`, `classement_annuel`, `ancien_eleve_le`
- [x] 13. Tests puis code : totaux annuels, clôture figée, ancien élève
- [x] 14. API et site : tableau de bord de l'élève, total du club, admin des années
- [x] 15. Vérifier tous les critères d'acceptation ; relecture finale ; `TASKS.md`
