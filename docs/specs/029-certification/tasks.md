# 029 — Tâches

- [x] 1. Données : migration (`quiz.parcours`, `place`, `ressource_id`, place publiée unique ; `regles_badges`,
      `place_reussie`, `badge_obtenu`, `certificat` ; barème en service), modèles, `points.annuler` et son test.
- [x] 2. Banque : parcours, place et fascicule à la création et à la modification, filtre par parcours, place
      unique à l'approbation (409, course comprise), paramètres par parcours. Tests d'abord.
- [x] 3. Tests de la progression (TDD) : ordre des places, pas de +50, badges et leurs points, encadreur sans
      points, certificat unique, fins simultanées, rattrapage, révoqué rejoué.
- [x] 4. Progression : `partie.py` (paramètres du parcours, `PlaceVerrouillee`, fin de partie, liste des jeux
      seulement), `certification/progression.py`, `regles.py` ; les tests de la tâche 3 passent.
- [x] 5. Routes joueur : `GET /certification` (« Ma certification ») et `GET /certification/certificat.pdf`
      (reportlab ajouté, PDF vérifié par extraction de texte, réservé au titulaire).
- [x] 6. Vérification publique `GET /certificats/{numero}` : tests de non-divulgation d'abord.
- [x] 7. Gestion : règles des badges (versions, 422), listes des certificats et des badges, révocation et
      réémission (2FA, motif, annulation des points, audit, notifications). Tests d'abord, droits paramétrés.
- [ ] 8. Seed : 12 quiz « [Test] » du parcours reliés au fascicule de test ; test du seed.
- [ ] 9. Site : client et types, `lib/certification` (+ test), page « Ma certification », retour depuis la partie,
      bouton sur `/certification`.
- [ ] 10. Site : page publique `/certificats/$numero` (+ test), vérifiée dans le navigateur à 375 px.
- [ ] 11. Site admin : parcours, place et fascicule dans la banque ; page « Certification » (paramètres, badges,
      certificats avec révocation et réémission).
- [ ] 12. Docs : ARCHITECTURE, SECURITY, PRD (Q24), TASKS.md, SESSION-LOG.
- [ ] Vérifier tous les critères d'acceptation de spec.md
- [ ] Relecture par le sous-agent reviewer
