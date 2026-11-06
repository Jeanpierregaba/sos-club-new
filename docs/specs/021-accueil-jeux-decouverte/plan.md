# 021 — Plan technique

## Approche

Trois blocs indépendants, chacun avec sa route API et son composant. Les règles vivent dans l'API (ADR-0002) :
la table de correspondance du jeu et le tirage du défi sont côté serveur, les réponses ne partent jamais
d'avance (ADR-0004). Aucun point n'est écrit.

## Fichiers touchés

- `backend/app/jeux/` (nouveau domaine) : `quel_axe.py` (questions, table, calcul), `defis.py` (tirage,
  correction), `models.py` (`DefiQuestion`), `schemas.py`, `router.py`.
- `backend/app/clubs/podium.py` (ou `service.py`) : `podium(db, limite=3)` ; `score_des_clubs` dans
  `app/points/service.py`, qui renvoie un dictionnaire vide tant que R13 n'a pas branché les lignes de club.
- `backend/app/seed_defis.py` + appel depuis `seed_dev` et `seed_preprod` : 30 questions.
- `backend/alembic/versions/…_banque_de_defis.py`.
- `src/components/QuelAxe.tsx` refait, avec `QuelAxeTest.tsx` (le questionnaire, en dialogue plein écran sur
  téléphone) ; `src/lib/axes-decouverte.ts` (codes GI…SE → axe du site, textes des résultats, couleurs,
  mascottes).
- `src/components/BulleDefi.tsx` branché sur l'API.
- `src/components/PodiumClubs.tsx` (nouveau), inséré après `ClubsSection` dans `src/routes/index.tsx`.
- `src/lib/api/client.ts`, `src/lib/api/schema.d.ts` (types régénérés).
- `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `TASKS.md`.

## Données

Nouvelle table `defi_question` : `id` (UUID), `question` (texte), `options` (JSONB, 3 ou 4 libellés),
`bonne_reponse` (entier, index dans `options`, contrôle `0 <= bonne_reponse < nb options`), `explication`
(texte court), `categorie` (texte court), `actif` (booléen), `ordre` (entier, unique), `cree_le`. Non
destructive. Tirage : questions actives triées par `ordre`, indice = numéro du jour (date de Lomé) modulo leur
nombre.

## API / interfaces

- `GET /api/jeux/quel-axe` → `{questions: [{numero, libelle, reponses: [{id: "A", libelle}]}]}` ; élève actif.
- `POST /api/jeux/quel-axe/resultat` `{reponses: ["A","A","A","D","B"]}` →
  `{principal: "TV", autres: ["EVSS","LM"], scores: {...}}` ; élève actif ; 422 si incomplet.
- `GET /api/jeux/defi-du-jour` → `{id, categorie, question, options}` ; public ; 404 si banque vide.
- `POST /api/jeux/defis/{id}/reponse` `{choix}` → `{correcte, bonne_reponse, explication}` ; public.
- `GET /api/clubs/podium` → `[{club_id, nom, etablissement, ville, points}]` (au plus 3, points > 0) ; public.

## Dépendances

Aucune nouvelle.

## Sécurité

- Le jeu : session valide, rôle élève et compte actif vérifiés par l'API sur les deux routes (pas seulement
  dans le site). Aucune donnée personnelle demandée ni conservée.
- Défi et podium publics : rien de personnel (un club s'affiche par son nom, jamais un élève).
- Correction du défi : on ne révèle que la réponse de la question demandée.

## Tests

- API : les 20 réponses de la table, chaque règle de départage, l'exemple [A,A,A,D,B], 401/403 par profil,
  422 ; tirage stable dans la journée et différent le lendemain (date injectée), question désactivée jamais
  tirée, banque vide → 404, correction ; podium : clubs actifs seulement, tri, au plus 3, vide sans points
  (avec un `score_des_clubs` remplacé dans le test).
- Site : cas A/B/C de `QuelAxe`, navigation Précédent/Suivant, réponse exigée, écran de résultat ;
  `BulleDefi` avec réponse juste/fausse ; `PodiumClubs` rempli et vide.

## Risques

- Le podium restera vide jusqu'à R13 : c'est voulu, l'état vide doit être soigné.
- Le contenu des défis n'est pas validé par l'équipe : à relire avant la prod (question ouverte).
