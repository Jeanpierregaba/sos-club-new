# 050 — Plan

## Livres

- PDF et couvertures (PNG de la première page) dans `backend/app/bibliotheque/livres/` : ils partent avec l'image de
  l'API (≈ 11 Mo).
- `app/bibliotheque/livres_officiels.py` : la liste des 4 livres et `charger(db, stockage)`. Pour chaque livre absent
  (même titre), le PDF passe par `fichiers.pdf.examiner`, la couverture par `fichiers.images.preparer`, les trois
  fichiers vont au stockage sous des clés `ressources/<uuid7>-…`, puis la ressource est insérée publiée
  (`deja_publiee`, `publie_le`, validateur, qualité). Les fichiers d'une insertion ratée sont effacés.
  `python -m app.bibliotheque.livres_officiels` l'exécute.
- `deploy/compose.yaml` : le service `migrations` monte le volume `fichiers` avec `DOSSIER_FICHIERS` et enchaîne
  `python -m app.bibliotheque.livres_officiels` après la banque du défi.
- `seed_dev` l'appelle aussi, pour la base locale.

## 100 quiz Jeux

- `banque_officielle.composer_jeux(parties)` : 100 quiz à partir des blocs complets (M puis D), découpés par 10 dans
  l'ordre du document, parties alternées ; niveaux M 40/20 Intermédiaire, D 10/20/10. La composition de la
  certification ne change pas. Nouveau fichier `alembic/donnees/jeux_100.json` ; `banque_officielle.json` reste tel
  quel (la migration de la spec 049 le lit).
- Migration `…_jeux_100_quiz` : garde = les 80 quiz Jeux de la banque officielle publiés ; clôt leurs tentatives en
  cours, les dépublie (motif « Recomposés en 100 quiz (spec 050). »), insère les 100 quiz. Retour arrière refusé si un
  des 100 a une tentative, sinon les supprime et republie les 80.
- Site : `src/lib/quiz.ts` régénéré (4 parties, 100 quiz), `bareme.ts` 40/30/20/10, tests.

## Badges

- `src/routes/certification.tsx` : le champ `metal` disparaît ; cartes des 20 quiz titrées par le nom du badge.
- `certification.parcours.index.tsx` : « Badge <nom> » au lieu de « Thématique N · badge <nom> ».

## Tests

- `test_banque_officielle.py` : composition des 100 quiz (couverture des 1 000, niveaux, certification incluse dans
  les niveaux Intermédiaire à Expert).
- `test_jeux_100_migration.py` : avant/après, motif, tentatives gardées, certification inchangée, rejouée sans effet,
  retour arrière refusé.
- `test_livres_officiels.py` : 4 ressources publiées et lisibles par la route publique, second passage sans effet.
- Vitest : page Jeux et page certification.
