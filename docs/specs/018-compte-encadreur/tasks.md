# 018 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Cochée dès qu'elle est faite et commitée. -->

**API, socle**

- [x] 1. Extraction sans changement de comportement :
  - les mécanismes partagés de l'inscription dans `app/comptes/inscription.py` ;
  - le résumé des points dans `points.service.resume`, avec les schémas renommés.

  Export OpenAPI, `npm run api:types` et `tsc`. Les 401 tests existants passent.

- [x] 2. Modèle `Encadreur` et migration `encadreurs` (table, CHECK, index partiel, `encadreur.bienvenue` en
      service). Module `encadreurs` dans le catalogue, préréglage du gestionnaire des clubs, droit sensible.

**API, encadreurs**

- [x] 3. Tests de la vérification (`test_encadreurs_verification.py`) écrits **avant** le code : activation et
      bienvenue, concurrence, refus puis activation, action désactivée, hors semestre, compte suspendu, motif,
      périmètre DRE, droits et double authentification, journal. Ils doivent échouer.
- [x] 4. `verification.py` et les routes `/admin/encadreurs` (file, activer, refuser), avec l'e-mail après
      validation. La tâche 3 passe.
- [x] 5. Tests puis code de l'inscription : `InscriptionEncadreur`, `service.inscrire`,
      `POST /encadreurs/inscription`. Avec `test_encadreurs_inscription.py`.
- [x] 6. Espace : `GET` et `PATCH /encadreurs/moi`, `POST /encadreurs/moi/renvoyer`, la dépendance
      `encadreur_actif`. Avec `test_encadreurs_espace.py`.
- [x] 7. Admin existant :
  - fiche d'un inscrit encadreur et recherche par téléphone ;
  - indicateur du tableau de bord ;
  - `nb_encadreurs` et remplacement d'une proposition ;
  - `creer_compte` sans `encadreur`.

  Avec les tests correspondants.

- [x] 8. Seed de démonstration (un encadreur actif, un en attente), `test_seed_dev.py`. Export OpenAPI et
      `npm run api:types`.

**Site**

- [x] 9. `/inscription` : choix du profil, extraction de `InscriptionEleve` et `ChampEtablissement`, formulaire
      `InscriptionEncadreur`, `fonctions.ts`. Test Vitest du téléphone.
- [x] 10. `/mon-espace`, vue encadreur dans ses trois états, dialogue du mot de passe partagé.
- [x] 11. Admin : page `/admin/encadreurs` (file, activer, refuser), menu et compteur, carte du tableau de bord,
      section Encadreur de la fiche, colonne Encadreurs des établissements, libellés du journal.

**Clôture**

- [x] 12. Clôture :
  - documentation : `ARCHITECTURE.md`, la note de l'ADR-0008, la liste des données de `SECURITY.md` ;
  - vérification de chaque critère d'acceptation, en local et dans le navigateur, sur téléphone ;
  - relecture par le sous-agent `reviewer`, et corrections (version envoyée par le site à l'activation et au refus,
    verrou `Utilisateur` à la décision, plus aucun contenu d'e-mail dans les journaux) ;
  - `TASKS.md` et `docs/SESSION-LOG.md` mis à jour.
