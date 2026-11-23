# 049 — Plan technique

## Approche

Comme la spec 043 : un outil lit le document Word et écrit un **fichier de données relu et commité**, puis **une
migration** le charge et fait la remise à zéro au déploiement (préprod puis prod). Le document lui-même n'entre pas
dans le dépôt.

1. **Lecture du document.** `app/quiz/import_docx.py` sait déjà lire un QCM (gras = bonne réponse, 3 propositions,
   refus de l'ambiguïté). On y ajoute la lecture des titres « Partie N – … » et « Questions moyennement / très
   difficiles » (styles Heading1 et Heading2). Commande :
   `uv run python -m app.quiz.banque_officielle <docx> alembic/donnees/banque_officielle.json`.
2. **Composition** (fonction pure, testée) : les 50 questions D de chaque partie réservées à la certification
   (indices régulièrement espacés), 80 quiz Jeux et 20 quiz de certification, comme décrit dans la spec. Le JSON
   contient les quiz tout faits (titre, niveau, numéro ou place, axe, 10 questions).
3. **Migration** `ouverture_banque_officielle`, en une transaction :
   - dépublie tous les quiz `jeux` et `certification` publiés (motif « Remplacé par la banque officielle (spec
     049). », `version + 1`) ;
   - insère les 80 + 20 quiz publiés et leurs questions (seulement si aucun quiz du JSON n'existe déjà : idempotent) ;
   - annule au registre chaque gain non annulé, de montant non nul, dont l'action a le parcours `jeux` ou
     `certification`, ou est `encadreur.certification` ou `encadreur.certification_eleve` : même requête que
     `points.annuler` (ligne négative, `annule_id`, part du club négative, `cle = annulation:<id>`), avec le motif ;
   - copie `etoile_obtenue`, `place_reussie` et `badge_obtenu` dans `etoile_obtenue_archive`,
     `place_reussie_archive` et `badge_obtenu_archive` (mêmes colonnes + `archive_le`), puis vide les tables en
     service ;
   - révoque les certificats valides (`etat = revoque`, `motif`, `decide_le = now()`) et les marque archivés
     (nouvelle colonne `certificat.archive_le`) ;
   - crée une version des paramètres Jeux à 10 questions et 8 bonnes réponses (les quiz ont 10 questions) ;
   - clôt sans réussite les parties en cours ;
   - ne touche aux données que sur une base qui a les 100 défis d'AIMES-AFRIQUE (préprod, prod, développement),
     jamais sur celle des tests.
4. **Regagner après la remise à zéro.**
   - Les clés d'idempotence des étoiles, places, badges et certificats prennent un suffixe de saison
     (`SAISON = "2"` dans `app/points/bareme.py`) : `etoile:<niveau>:<id>:s2`, etc. Les anciennes clés ne bloquent
     plus. Les quiz Jeux ont de nouveaux identifiants : leur clé change d'elle-même.
   - L'index `uq_certificat_origine` (un seul certificat d'origine par personne) devient partiel sur
     `archive_le IS NULL` : un certificat archivé n'empêche pas un nouveau.
5. **Vies** : `VIES_PAR_JOUR = 3` (API) et les textes du site.
6. **Favicon** : un script du bloc-notes (Pillow, déjà dans l'environnement de l'API) détoure le logo de la capture
   (pixels bleus, rouges et blancs du cartouche), le centre sur un carré blanc et écrit `public/favicon.ico`
   (16/32/48) et `public/apple-touch-icon.png` (180). `__root.tsx` déclare l'icône Apple.

## Fichiers touchés

**Créés**

- `backend/app/quiz/banque_officielle.py` : lecture par parties et composition, commande.
- `backend/alembic/donnees/banque_officielle.json` : les 100 quiz.
- `backend/alembic/versions/<rev>_ouverture_banque_officielle.py`.
- `backend/tests/test_banque_officielle.py` (lecture, composition, JSON commité) et
  `backend/tests/test_remise_a_zero_ouverture.py` (migration : dépublication, annulations, archives, certificats,
  idempotence, base vide ; puis regagner une place, un badge, une étoile).
- `public/apple-touch-icon.png`.

**Modifiés**

- `backend/app/quiz/import_docx.py` : les paragraphes avec leur style.
- `backend/app/jeux/models.py`, `backend/app/certification/models.py` : tables d'archive, `archive_le`, index.
- `backend/app/jeux/progression.py`, `backend/app/certification/progression.py`, `backend/app/points/bareme.py` :
  clés avec saison.
- `backend/app/certification/regles.py` : les thématiques (partie de chaque place).
- `backend/app/quiz/vies.py` et les tests des vies ; `src/lib/vies.ts`, `src/components/quiz/Vies*.tsx` et les
  textes du site qui disent 7.
- `public/favicon.ico`, `src/routes/__root.tsx`.
- `src/lib/quiz.ts` (catalogue des 80 quiz, tiré du JSON), `src/routes/jeux.tsx` (4 parties), `src/lib/bareme.ts`
  (32/24/16/8), `CarteMembre.tsx` et `TableauAnnuel.tsx` (« / 80 quiz »).
- `docs/PRD.md` (banque officielle, 80 quiz, 3 vies), `TASKS.md`.

## Données

- Tables `etoile_obtenue_archive`, `place_reussie_archive`, `badge_obtenu_archive` : colonnes des tables d'origine,
  sans contrainte d'unicité, + `archive_le timestamptz not null`.
- `certificat.archive_le timestamptz null` ; index `uq_certificat_origine` recréé avec `archive_le IS NULL`.

## Sécurité

- Aucune route nouvelle. La remise à zéro ne passe que par la migration, jamais par l'API.
- Rien n'est supprimé : registre annulé, tables archivées, certificats révoqués (RULES, ADR-0004).
- Bonnes réponses : le JSON est dans le dépôt comme les autres banques ; jamais envoyées au joueur (ADR-0004).

## Tests

- Lecture : un petit document construit dans le test (2 parties, M et D, gras) ; refus d'une question à 2 gras.
- Composition : effectifs par niveau, aucun recouvrement Jeux/certification, 1 000 énoncés utilisés une fois.
- JSON commité : 80 + 20 quiz de 10 questions, places et axes.
- Migration (base de test peuplée de quelques gains, étoiles, places, badges, certificat) : tout est annulé ou
  archivé, la vie du club reste, idempotence, base vide.
- Regagner : une place +50 et un badge après la remise à zéro.
- Vies : 3, puis refus.
- Site : Vitest des vies, tsc, lint, build, vérification au navigateur (accueil, favicon).

## Risques

- **Migration lourde en prod** : quelques milliers de lignes au plus pendant la phase de test, une transaction.
  Accepté.
- **Irréversible en pratique** : le retour arrière de la migration ne recrée pas les gains (ils restent annulés,
  l'historique est complet). À dire avant le merge vers `main`.
- **Suivi des certifications et fiche d'un inscrit** : ils gardent l'historique des parties sur les anciens quiz.
  Les compteurs (places, badges, certifiés) repartent de zéro.
