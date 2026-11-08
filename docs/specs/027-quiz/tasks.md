# 027 — Tâches

- [x] 1. Modèles, migration `quiz` (cinq tables, `eleve.quiz` en service), horloge, paramètres par défaut, module
      `quiz` disponible au catalogue.
- [x] 2. Tests de la partie, écrits avant le code (`test_quiz_partie.py`) : réponses jamais exposées, 6,9 s /
      7,1 s, 11 et 12 sur 15, double envoi, réponses et fins simultanées, points une fois, encadreur sans
      points, plafond, version des paramètres, reprise, clôture après 10 minutes, quiz dépublié, autre joueur.
- [x] 3. La partie (`partie.py`, routes `/quiz`) jusqu'à ce que ces tests passent.
- [ ] 4. Tests de la banque, puis la banque (`banque.py`, routes `/admin/quiz`) : droits, questions, soumission,
      reprise, approbation à deux personnes avec validateur médical, refus, dépublication, paramètres versionnés,
      journal, notifications.
- [ ] 5. Le mode test (essais) et ses tests ; quiz « Contenu de test » dans `seed_dev`.
- [ ] 6. Site, joueur : client, `PartieQuiz`, `/quiz` et `/quiz/$id`, liens depuis « Mon espace » et `/jeux`.
- [ ] 7. Site, admin : banque, éditeur de questions, décisions, essai, paramètres ; entrée « Quiz » du menu.
- [ ] 8. Docs : ADR-0004, ARCHITECTURE, SECURITY, TASKS.
- [ ] Vérifier tous les critères d'acceptation de spec.md
- [ ] Relecture par le sous-agent reviewer
