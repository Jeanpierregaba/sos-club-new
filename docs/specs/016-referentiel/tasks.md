# 016 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Cochée dès qu'elle est faite et commitée. -->

**API**

- [x] 1. Extraire l'annuaire du site vers `backend/alembic/donnees/annuaire.json`. Ce fichier contient :
  - 7 DRE, 19 IESG avec leur zone, et 844 établissements ;
  - les 7 axes, avec la phrase de `/les-7-axes`.

  Un script jetable fait l'extraction, il n'est pas commité. Contrôle : les nombres par IESG sont
  identiques à ceux de `togo-dre.ts`.

- [x] 2. `normalisation.py` et ses tests :
  - accents, majuscules et espaces ;
  - nom vide ou trop long ;
  - « CEG Adeho » et « CEG Adého » donnent la même clé.
- [x] 3. Modèles, `chargement.py` et migration `referentiel`, avec la clé étrangère du périmètre des
      collaborateurs. Tests :
  - aller-retour de la migration ;
  - 7, 19, 838 et 7 lignes ;
  - le chargement relancé ne crée pas de doublon ;
  - les périmètres existants sont conservés.

  Mise à jour de `conftest.py` : les DRE, IESG et axes sont rechargés après chaque `TRUNCATE`, et une
  fixture `annuaire` charge les établissements.

- [x] 4. Catalogue : le module `clubs` devient disponible et le dictionnaire `DRE` disparaît. Le validateur
      de périmètre lit la base, `Catalogue` sert `dre` et `dre_actives`, et le seed fonctionne toujours.
      Les tests existants de la spec 015 passent.
- [x] 5. Listes publiques : `dre`, `annuaire`, `etablissements` (par IESG ou par recherche), `axes`. Tests
      publics de la spec.
- [x] 6. Tests des droits et des garde-fous de l'admin, écrits **avant** le code (directement, sans sous-agent) :
  - droits par route et périmètre DRE ;
  - doublons et version périmée ;
  - enfants actifs, dernier axe, DRE utilisée comme périmètre, cible inactive ;
  - journal avec la valeur avant et après ;
  - aucune route `DELETE`.
- [x] 7. Routes admin des DRE et des IESG : lister, créer, modifier, déplacer, désactiver, réactiver. Les
      tests correspondants de la tâche 6 passent.
- [x] 8. Routes admin des établissements (liste paginée et filtrée par périmètre, créer, modifier, changer
      d'IESG, désactiver) et des axes. Toute la tâche 6 passe.
- [x] 9. Tableau de bord : indicateurs « DRE actives » et « Établissements actifs ». Export OpenAPI et
      `npm run api:types`.

**Site**

- [x] 10. Client API et types. `togo-dre.ts` réduit au dessin indexé par code. La carte des clubs lit
      `annuaire` (rendu serveur, solution de secours si l'API ne répond pas) ; tests Vitest du regroupement
      et de la recherche. `etablissements.ts` est supprimé.
- [x] 11. L'accueil (`ClubsSection`) et le formulaire du Génie Imhotep lisent `dre` ; le Hall of Fame garde
      les noms des régions du championnat et prend ses couleurs dans le dessin de la carte.
- [x] 12. Sélecteurs de périmètre des collaborateurs sur `dre_actives`. Menu admin « Référentiel ».
- [x] 13. `/admin/referentiel` : onglet DRE et IESG (renommer, ordre, créer, déplacer avec confirmation,
      désactiver).
- [x] 14. Onglet Établissements (recherche, filtres dans l'URL, pagination, dialogue de création et de
      modification, message de conflit de version) et onglet Axes.

**Clôture**

- [x] 15. `ARCHITECTURE.md` (domaine et modèle), règle « désactiver, jamais supprimer » dans `RULES.md`.
      Vérification de chaque critère d'acceptation, en local et dans le navigateur. Relecture par le
      sous-agent `reviewer` et corrections. `TASKS.md` mis à jour.
