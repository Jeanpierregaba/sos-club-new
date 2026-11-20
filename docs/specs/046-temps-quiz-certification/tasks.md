# 046 — Tâches

- [x] 1. Tests API des temps des quiz :
  - durée corrigée et abandon ;
  - résumé ;
  - moyenne nationale ;
  - « Très rapide ».
- [x] 2. Implémenter `temps_de_jeu`, `_tentative`, et les champs de `quiz_de` et des schémas.
- [x] 3. Tests API du détail d'une tentative :
  - les états des questions ;
  - l'ordre ;
  - l'absence de `bonne_reponse` ;
  - les cas 404 et 403.
- [x] 4. Implémenter `tentative_de` et sa route.
- [x] 5. Tests API des temps de la certification : places, badges, certificat, inscrit vide.
- [x] 6. Implémenter ces temps dans `certification_de`.
- [x] 7. Régénérer les types et ajouter `dureeLisible` (+ test) et `chargerTentativeInscrit`.
- [x] 8. Site : onglet Quiz (temps, moyenne, pastille, abandon) et panneau `DetailTentative` (+ test).
- [x] 9. Site : onglet Certification (temps des places, badges et certificats).
- [x] 10. Vérifier tous les critères d'acceptation de spec.md (lint, typecheck, tests ciblés, build).
- [x] 11. Relecture par le sous-agent reviewer (corrections : moyenne sur les premières réussites par joueur, index
  `ix_tentative_quiz_reussites`, abandon d'une partie restée en cours, une seule requête pour les cumuls).
- [ ] 12. Vérification au navigateur avec une connexion admin (par l'utilisateur).
