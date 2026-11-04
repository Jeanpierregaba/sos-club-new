# 017 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Cochée dès qu'elle est faite et commitée. -->

**API, points**

- [x] 1. Tests des points écrits **avant** le code (`test_points.py`), directement, sans sous-agent :
  - montant copié et semestre trouvé, ou nul hors semestre ;
  - action inactive ou à 0 ;
  - même clé, y compris en deux sessions simultanées ;
  - barème modifié après coup ;
  - totaux du semestre et historique.

  Ils doivent échouer.

- [x] 2. Modèles `Semestre`, `LigneBareme` et `MouvementPoints`, et la grille `bareme.py`. Migration
      `points_et_eleves`, partie points : tables, exclusion de chevauchement, barème prérempli (copie
      figée). `service.py` : `crediter`, `semestre_en_cours`, `totaux`, `dernieres_lignes`. La tâche 1 passe.
- [x] 3. Tests de l'admin des points (`test_points_admin.py`), puis `administration.py` et routes
      `/admin/points` (semestres, barème). Module `points` disponible dans le catalogue. Indicateur du
      tableau de bord.

**API, élèves**

- [x] 4. Modèle `Eleve` et `Classe`, suite de la migration. `pseudonyme.py` et ses tests (longueur,
      caractères, normalisation, e-mail, téléphone, mots interdits).
- [x] 5. Tests de l'inscription (`test_eleves_inscription.py`), puis `inscrire` et `POST`/`GET
    /eleves/inscription` :
  - découpage de `creer_compte` ;
  - proposition d'établissement ;
  - limite par adresse ;
  - réglage `inscriptions_ouvertes` ;
  - bienvenue dans la même transaction.

  `deploy/env.example` mis à jour.

- [x] 6. Espace élève : `GET`/`PATCH /eleves/moi` et `POST /comptes/mot-de-passe`, avec
      `test_eleves_espace.py`.
- [x] 7. Admin des élèves : fiche enrichie dans les inscrits, imposer un pseudonyme, réinitialiser le mot de
      passe, remplacer une proposition, `nb_eleves` dans la liste des établissements. Avec
      `test_eleves_admin.py`.
- [x] 8. Seed de démonstration (semestre en cours, profils, bienvenue). Export OpenAPI et
      `npm run api:types`.

**Site**

- [x] 9. Client API et `classes.ts`. Page `/inscription` (recherche d'établissement, proposition, champs pris,
      inscriptions fermées), page `/charte`, lien depuis la connexion. Test Vitest de la validation du
      pseudonyme.
- [x] 10. `/mon-espace`, vue élève : points, dernières lignes, profil, modification et mot de passe.
- [x] 11. Admin : onglets Points (semestres, barème avec « Pas encore utilisée ») et menu ; section Élève de
      la fiche d'un inscrit ; propositions dans l'onglet Établissements.

**Clôture**

- [x] 12. `ARCHITECTURE.md` (domaines `points` et `eleves`, modèle) et l'ADR-0004 passé à « Accepté ».
      Vérification de chaque critère d'acceptation, en local et dans le navigateur, sur téléphone. Relecture
      par le sous-agent `reviewer` et corrections. `TASKS.md` mis à jour.
