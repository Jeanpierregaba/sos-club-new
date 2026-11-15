# 038 — Tâches

Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (registre et points,
droits de lecture, fichiers, données de mineurs) sont écrites en TDD : les tests précèdent le code. Le rapport
d'activité de l'encadreur est livré de bout en bout d'abord (tâches 1 à 11), puis le président (12), le mensuel et
le bilan (13 et 14), l'archive et les exports (15 à 17).

## Socle

- [x] 1. Documents : - note « Lignes du compte collectif (spec 038) » dans l'ADR-0012 ; - note sur les types sans publication dans l'ADR-0009 ; - `docs/PRD.md` (ligne R12), `docs/ROADMAP.md`, `docs/DESIGN.md` (écrans des rapports) ; - `docs/SECURITY.md` (fichiers Word, rapports privés).
- [x] 2. Revue des requêtes du registre. Pour chaque lecture de `mouvement_points.utilisateur_id` (classements,
      années, clôtures, registre, jeux, certification, quiz, commentaires), noter si une ligne sans compte y entre.
      Écrire d'abord le test de non-régression : une ligne de club ne change aucun total, rang ou date d'atteinte
      personnels, et compte dans le classement des clubs. Si la revue montre trop de risques, s'arrêter et
      proposer la table séparée.
- [x] 3. Migration du registre et `crediter_club` : - `utilisateur_id` nullable ; contraintes `ligne_de_club` et `part_du_club_moitie` ; annulation d'une ligne
      de club ; - tests de contraintes (action qui n'est pas `club.*` refusée, part = 2 × montant) ; - club suspendu non crédité ; descente de migration refusée s'il existe des lignes de club.
- [x] 4. Registre admin (spec 036) : - bénéficiaire « Club : <nom> » ; filtre par club ; - annulation d'une ligne de club ; la correction motivée visant un club est reportée (une
      correction vise toujours une personne ; l'annulation suffit pour retirer un crédit de club) ; - tests des routes et de l'écran.

## Rapport d'activité de l'encadreur

- [ ] 5. Migration et modèles : - `rapport`, `piece_rapport`, `version_piece`, `lecture_rapport`, `type_activite` ; - séquences des références ; types d'activité de départ ; - contraintes du moteur élargies (`adresse_si_publie`, `contenu_du_club`) ; - aller-retour de la migration.
- [ ] 6. Types d'activité au référentiel : - routes admin (lister, créer, modifier, désactiver ; journal) et route de lecture pour les auteurs ; - écran `referentiel.types-activite` ; tests.
- [ ] 7. Tests puis code du brouillon et de la soumission (`rapports/service.py`, `router.py`) : - qui peut créer (encadreur vérifié d'un club en service) ; validation des champs ; - dates refusées (future, plus d'un an) ; - version figée ; correction en nouvelle version ; suppression d'un brouillon ; - référence unique sous deux soumissions simultanées ; - notification des encadreurs du club ; alerte de doublon probable.
- [ ] 8. Tests puis code de la lecture et du « consulté » : - auteur, encadreurs du club, autres : 404 ; - brouillon privé ; statut de chacun ; - aucune route publique ne lit un rapport ni une pièce.
- [ ] 9. Tests puis code des justificatifs : - photos par les tables de la spec 024, attestation obligatoire ; - documents PDF (contrôle existant) et Word (`fichiers/docx.py` : macro, faux Word, bombe ZIP) ; - 10 fichiers de 10 Mo au plus, liens YouTube (5 au plus) ; - lecture réservée aux lecteurs du rapport, en pièce jointe.
- [ ] 10. Tests puis code de l'examen et des points : - types enregistrés au moteur ; `avis_approbation` ; aperçu et file d'un rapport ; - +100 encadreur et +50 club une fois, même rejoué ou en parallèle ; - approbation comme doublon (même club, original approuvé), sans point, lien des deux côtés ; - aucun point hors approbation ; - auteur non vérifié ou suspendu : 409 ; - DRE hors périmètre : 404 ; un auteur ne décide pas de son rapport.
- [ ] 11. Site de l'encadreur et de l'admin : types de l'API et client ; - `mes-rapports` (mes rapports, rapports du club, « reçu / consulté ») ; - formulaire du rapport d'activité avec pièces ; détail avec historique ; - blocs « À faire » de l'accueil ; - aperçu de modération avec l'alerte et le choix du doublon ; - tests des composants ; vérification mobile dans le navigateur.

## Président, mensuel et bilan

- [ ] 12. Président : - dépôt d'un rapport d'activité au nom du club (club +50 seulement) ; mensuel et bilan refusés ; - il voit les rapports d'activité du club, pas les mensuels ni les bilans ; - passation sans transfert des rapports ; club sans encadreur vérifié ; - écrans `mon-club.rapports.*` ; tests.
- [ ] 13. Rapport mensuel : - schéma et formulaire ; soumission dès le dernier jour du mois ; - rappel des rapports d'activité du mois ; - +75 une fois par encadreur et par mois (second mensuel : rien) ; doublon probable ; tests.
- [ ] 14. Bilan semestriel : - schéma et formulaire ; soumission dès le dernier jour du semestre ; - +200 par encadreur et par semestre, +100 club une fois ; tests.

## Archive et exports

- [ ] 15. Archive admin : - module de droits `rapports` (consulter, exporter) au catalogue, et rôle modérateur ; - `GET /api/admin/rapports` filtrable, périmètre DRE ; écran `admin/rapports` ; tests.
- [ ] 16. Export PDF d'un rapport approuvé (auteur, lecteurs du club, admin) avec son historique ; refus pour un
      rapport non approuvé ; tests.
- [ ] 17. Export CSV de l'archive : - sans nom ni identifiant d'élève, limité au périmètre ; - journalisé ; tests.

## Fin

- [ ] 18. Lint, typecheck, tests backend et site ; vérification dans le navigateur ; libellés du journal dans
      `src/lib/admin.ts` ; `TASKS.md`.
- [ ] Vérifier tous les critères d'acceptation de `spec.md`.
- [ ] Relecture finale par le sous-agent `reviewer`.
