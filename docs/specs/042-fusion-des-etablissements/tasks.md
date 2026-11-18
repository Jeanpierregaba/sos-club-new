# 042 — Tâches

Les tâches sont dans l'ordre d'exécution. Chacune est petite, testable et committable seule. La fusion déplace des
comptes et des clubs : c'est une partie critique, écrite en TDD (les tests avant le code).

## Socle

- [x] 1. Documents :
  - `TASKS.md` : spec 042 en cours, avec spec, plan et tâches validés ;
  - l'analyse `docs/analyses/doublons-etablissements.md` commitée avec la spec ;
  - `docs/DESIGN.md` : la page « Doublons probables » et la boîte de dialogue de fusion ;
  - `docs/specs/016-referentiel/spec.md` : un renvoi vers la spec 042 pour le remplacement des propositions.
- [x] 2. Migration et modèles :
  - la colonne `etablissement.fusionne_dans_id`, avec ses CHECK (inactif seulement, jamais vers soi-même) ;
  - la table `ecart_doublon`, avec sa clé primaire `(a, b)` et le CHECK `a < b` ;
  - le test d'aller-retour, et le retour arrière refusé dès qu'une fusion existe.

## Détection des doublons

- [x] 3. Tests de `referentiel/doublons.py`, paramétrés et sans base :
  - les paires de l'analyse sont trouvées : Tokoin I, Bogou 2 et II, Warkanbou et Warkambou, Kondokopé en trois
    fiches, Koudjoaré et Koundjoare sous deux IESG, Ossakré et Ossacre ;
  - les faux positifs sont écartés : Fabienne I, III et M, Souverain G/A et G/B, Bassar Est et Ouest,
    Daroul Hikmah I et IV, Jardin et sa version « (Annexe) » ;
  - deux DRE différentes ne forment jamais une paire, et chaque paire porte sa raison.
- [x] 4. Code de `doublons.py` (clé forte, nom proche, prononciation, éléments distinctifs), jusqu'à ce que les tests
      de la tâche 3 passent.
- [x] 5. Tests puis code de la liste et des écarts : `lister_doublons`, `ecarter`, `retablir`, et les routes
      `GET /etablissements/doublons`, `POST …/ecarter` et `POST …/retablir`.
  - Seuls les actifs et les proposés sont pris en compte : un absorbé ou un inactif n'apparaît pas.
  - Le collaborateur de DRE ne voit que sa DRE.
  - Une paire écartée disparaît, revient une fois rétablie, et les deux sont journalisés.
  - Écarter une paire déjà écartée donne 409.
  - Le compteur `par_dre` est juste.
  - La durée mesurée sur la base locale complète reste sous une seconde.

## Fusion

- [x] 6. Tests des clubs (`fusionner_clubs`), une ligne du tableau de la spec par test :
  - aucun club ;
  - absorbé en constitution, gardé sans club ;
  - les deux en constitution ;
  - absorbé en constitution, gardé actif ;
  - absorbé actif, gardé sans club : le club garde son identifiant et la somme de ses points ;
  - absorbé actif, gardé en constitution ;
  - deux clubs au-delà de « en constitution » : refus 409 et rien ne change.
- [x] 7. Code de `fusionner_clubs` dans `clubs/affiliations.py`, qui remplace `remplacer_etablissement`. La tâche est
      faite quand les tests de la tâche 6 passent, ainsi que les tests existants de la spec 033.
- [x] 8. Tests de `fusionner` et de `apercu` :
  - les élèves et les encadreurs sont déplacés, avec leur version qui monte ;
  - le nom final, puis la préfecture et l'ordre complétés seulement s'ils étaient vides ;
  - l'absorbé devient inactif avec son renvoi, et le journal `etablissement_fusionne` est complet (identifiants, pas
    de noms d'élèves) ;
  - refus 422 : soi-même, une autre DRE, un gardé inactif ;
  - refus 403 : hors périmètre, pour l'un ou l'autre, ou sans le droit ;
  - refus 409 : version dépassée, nom déjà pris dans l'IESG ;
  - l'absorbé est absent de la recherche d'inscription et de l'annuaire public ;
  - l'aperçu annonce le même effet, et le même refus, sans rien écrire.
- [x] 9. Code de `referentiel/fusion.py`, des schémas (`Fusion`, `ApercuFusion`, `ClubResume`,
      `EtablissementAdmin.fusionne_dans`) et des routes `GET …/fusion/{absorbe_id}` et `POST …/fusionner`.
- [x] 10. Retrait du « Remplacer par… » :
  - `remplacer_proposition`, `Remplacement` et la route `/remplacer` disparaissent ;
  - les tests de `test_eleves_admin.py` et `test_encadreurs_admin.py` passent par `/fusionner`, avec le même
    résultat ;
  - un test vérifie que `/remplacer` répond 404 ou 405 ;
  - régénérer `openapi.json` et les types du site.

## Site

- [x] 11. Client et libellés : les fonctions d'API de la fusion et des doublons dans `client.ts`, et
      `adminRemplacerEtablissement` retiré ; les libellés du journal dans `lib/admin.ts`.
- [x] 12. `FusionEtablissements.tsx` et son test Vitest :
  - la recherche de l'autre établissement et les fiches côte à côte ;
  - l'inversion des rôles et le choix du nom ;
  - l'annonce de l'effet, le refus affiché avant la confirmation, puis la confirmation.
- [x] 13. `referentiel.etablissements.tsx` :
  - « Fusionner avec… » remplace « Remplacer par… » ;
  - la mention « Fusionné dans … » apparaît sur un absorbé ;
  - un filtre « Fusionnés » est ajouté s'il reste simple.
- [x] 14. Page `referentiel.doublons.tsx` et son onglet :
  - un filtre par DRE, avec le compteur ;
  - le filtre « Écartées » ;
  - par paire, « Fusionner » et « Pas un doublon » ou « Rétablir » ;
  - un état vide.
- [ ] 15. (À faire : demande une connexion admin dans le navigateur) Vérification au navigateur, sur la base locale avec l'annuaire complet, à 375 px et sur bureau :
  - fusionner une vraie paire, par exemple Lycée de Tokoin I ;
  - écarter Fabienne I et III ;
  - fusionner une proposition ;
  - provoquer le refus de deux clubs actifs.

## Clôture

- [x] 16. Lint, typecheck, tests API complets (une seule suite à la fois), tests et build du site.
- [x] 17. Relecture par le sous-agent `reviewer`, puis les corrections.
- [x] 18. Cocher les critères d'acceptation, passer la spec dans « Terminé » de `TASKS.md`, et noter les suites
      (alias de recherche, annulation, fusion de deux vrais clubs).
