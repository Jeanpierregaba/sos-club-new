# 019 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (concurrence, droits) : le test précède le code. -->

**API, socle**

- [ ] 1. Modèle `club`, `club_axe`, `club_passation` et migration `clubs` (index partiels uniques, CHECK refus↔motif).
      `tiers.associes` en JSON. Export OpenAPI + `npm run api:types` quand le routeur existera.

- [ ] 2. Module `clubs` dans le catalogue : `clubs:consulter` et `clubs:approuver` en sensibles ; `gestionnaire_clubs`
      gagne `("clubs", A)` (Tâche 1, étape 2). Tests `test_catalogue` à jour.

**API, demande et consultation**

- [ ] 3. Tests puis code de la demande : `DemandeClubEntree`, `POST /api/clubs/demande` et `GET /api/clubs/moi`
      (`test_clubs_demande.py`) : établissement lu sur le compte, nom normalisé unique par établissement,
      ≤ 3 axes valides, encadreurs déclaratifs bornés, confirmation obligatoire, une seule demande en attente,
      refus du doublon au même établissement (409), club actif au même établissement → 409.

- [ ] 4. Tests puis code du renvoi : `POST /api/clubs/demande/renvoyer` (`test_clubs_renvoi.py`) : seule une demande
      refusée est relançable ; elle repasse en attente ; le motif précédent reste au journal.

- [ ] 5. Lecture publique : `GET /api/clubs`, `GET /api/clubs/{id}`, `GET /api/clubs/par-etablissement`
      (`test_clubs_public.py`) : seuls les clubs actifs ; fiche minimale (nom, établissement IESG/DRE, axes) ;
      en attente → 404 ; rien de nominatif.

**API, admin et passation**

- [ ] 6. **Tests d'abord** de la vérification (`test_clubs_verification.py`) : file et périmètre DRE/national,
      double auth exigée, activation atomique, doublure refusée, version périmée → 409, refus sans motif → 422,
      suspension du demandeur → 409, établissement désactivé → 409 (doivent échouer — échec attendu avant implémentation).

- [ ] 7. `verification.py` clubs (`/admin/clubs` : file, activer, refuser, renvoi) + compteurs `/admin/moi` et
      tableau de bord (`clubs_a_valider`, `clubs_actifs`). La tâche 6 passe.

- [ ] 8. **Tests d'abord** de la passation (`test_clubs_passation.py`) : proposition (pseudonyme inexistant,
      hors établissement, soi-même, élève suspendu → 422/409), valider (l'ancien président perd la gestion, le nouveau
      la reçoit — vérification des droits), refuser (reste président), annuler, double validation impossible,
      journalisation avant/après.

- [ ] 9. Passation côté `clubs` : `POST /api/clubs/moi/passation`, `POST /api/clubs/moi/passation/annuler`,
      `/api/admin/clubs/passations/*`. La tâche 8 passe.

- [ ] 10. Admin existant : file des inscrits (section Club : club de l'élève, état, président), fiche d'un inscrit
        club, compteur du tableau de bord (`test_clubs_admin.py`).

- [ ] 11. Seed de démonstration (un club actif, une demande en attente), `test_seed_dev.py`, OpenAPI + `npm run api:types`.

**Site**

- [ ] 12. Page `/clubs/$id` (fiche publique minimale) + branchement de la carte des clubs sur `GET /api/clubs`
        (clubs actifs réels ; libellé « Aucun club enregistré pour cet établissement »). Test Vitest du branchement.

- [ ] 13. `/mon-espace` : bloc « Club » (demander la création — formulaire `DemandeClub` dans `#etat-vide` ; carte d'état
        si demande ou club actif ; proposer une passation — `CartePassation`). Tests Vitest du formulaire.

- [ ] 14. Admin : page `/admin/clubs` (file des clubs, ongleta Refusés, ongleta Passations), entrée au menu avec
        compteur, carte du tableau de bord. Vérification des critères d'acceptation.

**Clôture**

- [ ] 15. Documentation : `ARCHITECTURE.md`, note de l'ADR-0003 amendé (le club n'a pas de compte), note ADR-0008
        (passations), `SECURITY.md` (club dans les données limitées).
- [ ] 16. Vérifier tous les critères d'acceptation, en local et dans le navigateur sur téléphone.
- [ ] 17. Relecture par le sous-agent `reviewer`, corrections.
- [ ] 18. `TASKS.md` et `docs/SESSION-LOG.md` mis à jour.
