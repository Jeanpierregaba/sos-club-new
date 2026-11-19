# 044 — Tâches

Les tâches sont dans l'ordre d'exécution. Chacune est petite, testable et committable seule. Les points et la
confidentialité des mineurs sont des parties critiques (`docs/TESTING.md`) : leurs tests précèdent le code.

## Socle

- [ ] 1. Documents :
  - `TASKS.md` : spec 044 en cours, avec la spec, le plan et les tâches validés ;
  - `docs/PRD.md` : Q23 tranchée (lien vérifié par un modérateur, 3 déclarations par jour, encadreurs compris).
- [ ] 2. Migration `partages` :
  - contrainte `contenu_a_un_parent` (commentaire ou partage) ;
  - index du lien.

  Test : montée sur une base avec des commentaires ; retour arrière refusé s'il existe un partage. Mettre à jour la
  contrainte dans `moderation/models.py`.

## Partages d'articles (API)

- [ ] 3. Tests de la déclaration (`test_partages.py`), écrits avant le code :
  - nature déduite de l'auteur ;
  - article non publié refusé ;
  - liens invalides ;
  - lien déjà utilisé ;
  - réseau ou republication déjà déclarés, puis libérés après un refus ;
  - plafond de 3 par jour ;
  - droits : visiteur, suspendu, encadreur non vérifié, non connecté.
- [ ] 4. Code de `app/partages/` :
  - schémas ;
  - `verifier_lien` ;
  - type `partage` enregistré ;
  - `declarer` sous verrou ;
  - routes `POST /api/articles/{adresse}/partages` et `GET /api/articles/{adresse}/partages/moi`.

  Les tests de la tâche 3 passent.

- [ ] 5. Tests des décisions (`test_partages_moderation.py`), écrits avant le code :
  - +10 ou +50 et part du club ;
  - deux réseaux, deux crédits ;
  - refus sans point ;
  - pas de correction ni de retrait ;
  - droit `partages:approuver` et périmètre DRE ;
  - article dépublié avant la décision ;
  - concurrence ;
  - encadreur.
- [ ] 6. Code :
  - `crediter` et `complement_apercu` du type ;
  - module `partages` du catalogue admin ;
  - notification « est validé ».

  Les tests de la tâche 5 passent.

- [ ] 7. « Mes partages » : `GET /api/partages/moi` et ses tests (seulement les siens ; le lien absent des routes
      publiques des articles).

## Carte de classement (API)

- [ ] 8. Tests de la carte (`test_carte_classement.py`), écrits avant le code :
  - textes dessinés, club en option, encadreur en prénom et initiale, « Classement provisoire » ;
  - refus : non classé, sans club, sans semestre en cours, visiteur, admin, non connecté ;
  - PNG de 1080 × 1350 ;
  - aucune ligne au registre ;
  - limite de 30 images par heure.
- [ ] 9. Code :
  - `carte_personnelle` dans `classements.py` ;
  - rendu `points/carte_classement.py` (textes par une fonction pure) ;
  - route `GET /api/classements/moi/carte.png`.

  Les tests de la tâche 8 passent. Régénérer `openapi.json` et les types du site.

## Site

- [ ] 10. `PartagerArticle` sur la page d'un article :
  - liens de partage, et « Copier le lien » pour Instagram et TikTok ;
  - formulaire « J'ai partagé cet article » ;
  - réseaux déjà déclarés grisés ;
  - nature et points annoncés ;
  - erreurs de l'API.

  Tests Vitest.

- [ ] 11. « Mes partages » et « Partager mon classement » dans « Mon espace », et le bouton sur `/hall-of-fame`.
      La boîte de dialogue propose :
  - la vue et la période ;
  - la case du club ;
  - l'aperçu ;
  - Télécharger et Partager, avec repli sans `navigator.share`.

  Tests Vitest.

- [ ] 12. File de modération : le type « Partage » dans les filtres et l'aperçu (réseau, lien `nofollow`, article,
      nature). Test Vitest de l'aperçu.

## Clôture

- [ ] 13. Vérification au navigateur, à 375 px et sur ordinateur :
  - déclaration d'un partage ;
  - décision dans la file (connexion admin de l'utilisateur) ;
  - carte téléchargée.
- [ ] 14. Vérifier tous les critères d'acceptation de `spec.md` ; lancer la suite API complète, les tests, le
      typecheck, le lint et le build du site.
- [ ] 15. Relecture par le sous-agent `reviewer`, puis les corrections.
- [ ] 16. Clôture :
  - `TASKS.md` : la ligne dans « Terminé », avec les suites ;
  - `docs/ROADMAP.md` ;
  - note dans l'ADR-0009 ;
  - critères et tâches cochés.
