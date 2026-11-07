# 024 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Cochée dès qu'elle est faite et commitée. -->

**API, socle**

- [ ] 1. Pillow (doc relue), `app/fichiers/stockage.py` et `images.py`, `dossier_fichiers` dans la configuration.
      Avec `test_fichiers.py`.
- [ ] 2. Modèles `Photo` et `VersionPhoto`, migration `photos_des_contenus` ; `_nouvelle_version` recopie les
      photos.

**API, photos**

- [ ] 3. Tests d'accès aux photos (`test_photos_acces.py`) écrits **avant** le code. Ils doivent échouer.
- [ ] 4. `moderation/photos.py` et les routes : envoi, modification, retrait, lecture par l'auteur, le modérateur
      et le public ; photos dans `ArticleAuteur`, l'aperçu et les articles publics. Les tâches 3 et
      `test_photos_auteur.py` passent.
- [ ] 5. Effacements : brouillon supprimé, purge à 90 jours dans la boucle horaire. Avec `test_photos_purge.py`.
      Export OpenAPI et `npm run api:types`.

**Déploiement**

- [ ] 6. Volume `fichiers` dans `deploy/compose.yaml`, `DOSSIER_FICHIERS`, sauvegarde et restauration du volume,
      `.gitignore`.

**Site**

- [ ] 7. `Photos.tsx` dans l'éditeur (attestation obligatoire, progression, légende, couverture, ordre, retrait),
      avec un test Vitest.
- [ ] 8. `Galerie.tsx` : couverture dans `/articles`, couverture et galerie sur la page de l'article.
- [ ] 9. Aperçu admin : photos, attestations, photos ajoutées et retirées.

**Clôture**

- [ ] 10. Documentation (`ARCHITECTURE.md`, `SECURITY.md`, renvoi de l'ADR-0005), vérification de chaque critère
      (navigateur, téléphone) ; relecture par le sous-agent `reviewer` et corrections ; `TASKS.md` et
      `docs/SESSION-LOG.md`.
