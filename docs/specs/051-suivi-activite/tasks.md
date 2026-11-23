# 051 — Tâches

Ordre d'exécution. Pour la collecte (données d'un public mineur, partie critique), le test précède le code.

- [ ] 1. ADR-0014 (mesure d'audience interne et anonyme), lignes de `docs/SECURITY.md` et de `docs/PRD.md`
- [ ] 2. Tests de la collecte : empreinte du jour, sel effacé, exclusions (GPC, DNT, robot, admin, maintenance),
      schéma fermé, liste blanche des chemins, débit, aucune IP ni identifiant stocké
- [ ] 3. Domaine `app/activite/` : modèles et migration (`sel_activite`, `evenement_activite`, `total_activite_jour`,
      `presence_semaine`), `enregistrer()`, route `POST /api/activite/evenements` — les tests de la tâche 2 passent
- [ ] 4. Événements côté serveur : étapes d'inscription (élève, encadreur, visiteur), première connexion,
      téléchargements de la bibliothèque, erreurs 500, présence hebdomadaire ; un échec du suivi ne casse jamais
      l'action (tests)
- [ ] 5. Purge horaire : agrégation à 90 jours sans changement des totaux, sels passés, mots sous le seuil,
      présences de plus de 26 semaines (tests)
- [ ] 6. Indicateurs et API de lecture super-admin, bloc par bloc (audience, inscription, Jeux, certification,
      contenus, régions, rétention, erreurs), période précédente, export CSV agrégé, 403 et journal (tests sur jeux de
      données construits, période vide comprise) ; types régénérés
- [ ] 7. Site, collecte : `src/lib/activite.ts`, pages vues dans `__root.tsx`, `LienInscription` partout, étapes
      `ouvert` et `commence`, recherches sans résultat, 404 (tests Vitest)
- [ ] 8. Site, page `/admin/activite` : période, 8 sections, graphiques, heatmap, régions, CSV, mentions des limites,
      entrée du menu pour le super-administrateur (tests Vitest, vérification au navigateur avec les données du seed)
- [ ] 9. Suite complète, critères d'acceptation, relecture par le sous-agent `reviewer`, `TASKS.md`
