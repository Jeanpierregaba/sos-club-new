# 043 — Tâches

Les tâches sont dans l'ordre d'exécution. Chacune est petite, testable et committable seule. La sélection et le
suivi touchent la certification (partie critique, `docs/TESTING.md`) : leurs tests précèdent le code.

## Socle

- [x] 1. Documents :
  - `TASKS.md` : spec 043 en cours, avec spec, plan et tâches validés ;
  - `docs/PRD.md` : la banque de 1 000 QCM ;
  - `docs/DESIGN.md` : la page « Suivi » de la certification.

## Banque de 1 000 questions

- [x] 2. Tests de `app/quiz/import_docx.py` sur un petit document construit dans le test : thématiques, numéros,
      3 propositions, réponse en gras ; refus de deux réponses en gras, d'aucune, ou d'un nombre de propositions
      différent de 3.
- [x] 3. Code de `import_docx.py` et de sa commande, jusqu'à ce que les tests passent. Générer
      `backend/alembic/donnees/quiz_sante_lot7.json` depuis le document (78 QCM, 15 thématiques, axe de chaque
      thématique selon la spec). Test sur le JSON commité : 78 QCM, numéros 1 à 78, axes connus, aucun énoncé
      déjà présent dans `quiz_sante.json`.

## Sélection expert

- [ ] 4. Thématiques de la certification dans `certification/regles.py` : l'axe et les lots de chaque badge.
      Tests de `selectionner(banque, defis)`, fonction pure, sur une banque fabriquée :
  - les défis Expert d'abord, à parts égales entre eux ;
  - le complément pris dans le même lot, dans l'ordre du document ;
  - aucun doublon par énoncé normalisé, y compris entre deux thématiques ;
  - 4 places de 10 par thématique, chacune mêlant défis Expert et complément ;
  - refus quand un axe a moins de 40 questions.
- [ ] 5. Code de `certification/selection_expert.py`, puis de sa commande, qui lit la base et écrit le JSON.
      Générer `backend/alembic/donnees/certification_expert.json` depuis la base locale. Test sur le JSON commité :
      200 énoncés distincts, 10 par place, bonne réponse dans les choix, axe conforme à la thématique.

## Migration

- [ ] 6. Tests de la migration `banque_1000_et_certification_expert`, sur une base de test avec une petite banque
      fabriquée :
  - le lot 7 est chargé en 15 quiz dépubliés ;
  - 20 quiz de certification publiés, de 10 questions ;
  - un quiz de test dépublié et un vrai quiz laissé en place ;
  - une seconde exécution ne change rien ;
  - retour arrière ;
  - aucun effet sans banque.
- [ ] 7. Code de la migration jusqu'à ce que les tests passent. L'appliquer sur la base locale et vérifier : 1 000
      QCM dans la banque, places 1 à 20 remplies, quiz « [Test] » dépubliés. Test de bout en bout : un élève
      réussit la place 1 à 10/10, gagne +50, et la place 2 s'ouvre.

## Suivi

- [ ] 8. Tests de `certification/suivi.py` et de `GET /admin/certification/suivi/candidats` :
  - un candidat apparaît dès sa première tentative, avec ses places, sa place en cours, ses tentatives, son début
    et sa dernière activité ;
  - les parties d'essai et les joueurs sans compte sont exclus ;
  - les filtres DRE, club et rôle, les états `en_cours`, `inactif` et `certifie`, la recherche et la pagination ;
  - un certificat révoqué ne compte pas, un certificat réémis compte une fois ;
  - un ancien élève est marqué ;
  - le périmètre DRE s'applique, avec le pseudonyme au lieu du nom ;
  - 403 sans `quiz : consulter`.
- [ ] 9. Code de la liste des candidats, de ses schémas et de sa route, jusqu'à ce que les tests passent.
- [ ] 10. Tests puis code de `GET /admin/certification/suivi/statistiques` :
  - totaux : candidats, actifs sur 30 jours, badges par rang, certifiés ;
  - entonnoir des 20 places : tentés, réussis, taux de réussite, tentatives moyennes avant réussite, place sans
    quiz publié ;
  - chiffres par DRE ;
  - 12 semaines, dont les semaines vides ;
  - périmètre DRE ;
  - aucun candidat.
- [ ] 11. Tests puis code de `POST /admin/certification/suivi/candidats/export` :
  - 403 sans `inscrits : exporter` ou hors du périmètre national ;
  - finalité obligatoire ;
  - mêmes filtres et colonnes que la liste ;
  - cellules neutralisées ;
  - limite de 5 000 lignes ;
  - journal `export_suivi_certification`.

## Site

- [ ] 12. Types de l'API (`export_openapi` puis `api:types`), appels dans `src/lib/api/client.ts` et libellé du
      journal dans `src/lib/admin.ts`.
- [ ] 13. Composant `SuiviCertification` (tuiles, entonnoir, tableau par DRE, graphique par semaine avec Recharts)
      et son test : chiffres affichés, état vide.
- [ ] 14. Page `/admin/certification/suivi` et onglet « Suivi » :
  - filtres, recherche et pagination ;
  - tableau sur bureau, cartes à 375 px ;
  - bouton « Exporter » réservé au national avec le droit, avec une boîte qui demande la finalité ;
  - tests de la page (bouton masqué sans droit, filtres transmis).
- [ ] 15. Vérification au navigateur, à 375 px et sur bureau : suivi avec des candidats de démonstration, export,
      parcours d'un élève sur la place 1.

## Clôture

- [ ] 16. Vérifier tous les critères d'acceptation de `spec.md` ; lint, typecheck et tests (API complète et site).
- [ ] 17. Relecture par le sous-agent `reviewer`, puis corrections.
- [ ] 18. `TASKS.md` (spec 043 dans « Terminé », relecture du JSON par l'équipe nationale dans les suites) et
      cases cochées.
