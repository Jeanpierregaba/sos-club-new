# 052 — Plan technique

## Approche

**Paraglide JS** (`@inlang/paraglide-js`) avec la réécriture d'adresses de TanStack Router, comme dans le guide
officiel TanStack Start de Paraglide. Les textes vivent dans `messages/fr.json`, `messages/en.json`,
`messages/de.json` ; le plugin Vite les compile en fonctions typées (`m.accueil_titre()`), une clé manquante est une
erreur de typage et seules les traductions utilisées partent dans le bundle.

Pourquoi Paraglide plutôt que `react-i18next` : clés vérifiées par TypeScript, aucun chargement de dictionnaire à
l'exécution, rendu serveur pris en charge par un middleware, adresses préfixées fournies (`localizeUrl`,
`deLocalizeUrl`) et branchées sur le `rewrite` du routeur. Les fichiers de routes restent tels quels : `/en/jeux` est
réécrit en `/jeux` à l'entrée et réécrit en sortie pour chaque lien, sans dupliquer une seule route.

Stratégie de langue : `["url", "baseLocale"]` seulement. Pas de cookie ni de langue du navigateur (pas de
redirection automatique, rien à consentir) : la langue vient de l'adresse, sinon le français.

Décision structurante → **ADR-0015** (langues de l'interface : Paraglide, préfixes d'adresse, contenus en
français). La ligne « autres langues que le français » du PRD (hors scope) est mise à jour.

## Fichiers touchés

**Créés**

- `project.inlang/settings.json` : langues `fr` (base), `en`, `de`, format des messages.
- `messages/fr.json`, `messages/en.json`, `messages/de.json` : les textes, clés en français sans accent groupées par
  page (`accueil_…`, `jeux_…`, `commun_…`).
- `src/lib/langues.ts` : la liste des **pages traduites** (une seule source), `estTraduite(chemin)`, les libellés
  du sélecteur, `localeDate()` (`fr-FR`, `en-GB`/`en-US`, `de-DE`), les liens `hreflang` d'une page.
- `src/components/SelecteurLangue.tsx` : FR / EN / DE, lien vers la même page dans l'autre langue
  (`localizeHref`), masqué hors des pages traduites.
- `src/components/ContenuEnFrancais.tsx` : la mention « contenu disponible en français », affichée seulement hors
  du français.
- `src/lib/langues.test.ts`, `src/test/messages.test.ts` : voir Tests.
- `docs/decisions/0015-langues-de-l-interface.md`.
- `src/paraglide/` : généré par le plugin (dev, build, Vitest) ou par `npm run langues` (vérification des types,
  CI), ignoré par git, ESLint et Prettier. Le plugin de format des messages est une dépendance npm chargée depuis
  `node_modules` (pas de module téléchargé au build).

**Modifiés**

- `vite.config.ts` : `paraglideVitePlugin` (motifs `/en/:path(.*)?`, `/de/:path(.*)?`, et les pages non
  traduites gardées sans préfixe dans les trois langues pour que leurs liens restent français).
- `src/router.tsx` : `rewrite: { input: deLocalizeUrl, output: localizeUrl }`.
- `src/server.ts` : la requête passe par `paraglideMiddleware` (langue connue pendant le rendu serveur), en gardant
  l'enveloppe d'erreurs existante.
- `src/routes/__root.tsx` : `<html lang>` selon la langue, liens `hreflang` et `x-default`, page 404 et page
  d'erreur traduites, `/fr/...` → redirection vers l'adresse sans préfixe, `/en|de/<page non traduite>` →
  redirection vers la page française.
- `src/components/SiteHeader.tsx`, `SiteFooter.tsx` et le menu mobile : textes traduits, ancien bouton FR/EN
  remplacé par `SelecteurLangue`.
- Les pages publiques listées dans la spec et les composants qu'elles affichent : textes remplacés par `m.…()`,
  `head()` (titre, description) traduit. Les pages des espaces connectés et de l'admin ne bougent pas.
- `src/lib/dates.ts` : la langue de formatage suit `getLocale()` (le français reste la valeur par défaut, donc les
  pages non traduites sont inchangées).
- Formulaires d'inscription, connexion, activation, mot de passe : messages de validation du site traduits ; les
  erreurs de l'API traduites par statut et par cas connu (identifiants faux, trop de tentatives, code expiré,
  doublon), sinon le message français de l'API tel quel.
- `eslint.config.js`, `.prettierignore`, `.gitignore`, `tsconfig.json` si besoin pour `src/paraglide/`.
- `docs/PRD.md` (hors scope), `docs/DESIGN.md` (ton en anglais et en allemand, sélecteur), `AGENTS.md` (où sont
  les textes, comment ajouter une clé).

## Données

Aucune : ni migration ni changement d'API. Les contenus en base restent en français.

## API / interfaces

- Aucune route d'API nouvelle. L'API continue de répondre en français ; le site traduit les erreurs connues des
  formulaires publics.
- Suivi d'activité (spec 051) : `pageVue` lit `route.fullPath`, qui est le gabarit **après** la réécriture
  (`/jeux` pour `/en/jeux`) : rien à changer, un test le fixe.
- Les adresses existantes ne changent pas.

## Dépendances

- `@inlang/paraglide-js` 3.2.2 (dépendance de développement : compilateur et plugin Vite ; le runtime généré est
  dans `src/paraglide`). Vérifiée le 2026-11-24 : publiée le 10 novembre 2026, dépôt
  `generaltranslation/paraglide-js` actif, guide TanStack Start à jour lu via Context7 (`rewrite` du routeur,
  `paraglideMiddleware` dans `server.ts`). TanStack Router 1.170 prend en charge `rewrite`.

## Sécurité

- Pas de cookie de langue, pas de donnée nouvelle, rien dans les paramètres d'URL hormis le préfixe.
- Les messages ne contiennent pas de HTML : les mises en forme (gras, liens) passent par des composants, jamais
  par `dangerouslySetInnerHTML`.
- Les redirections de langue ne reprennent que le chemin interne (pas de redirection ouverte).
- `docs/RULES.md` inchangé : pseudonyme et club seulement, tutoiement → « you » / « du ».

## Tests

- **Clés** (Vitest) : `fr.json`, `en.json` et `de.json` ont exactement les mêmes clés, aucune valeur vide, mêmes
  paramètres `{…}` dans chaque traduction.
- **Adresses** (Vitest, `langues.ts`) : `/en/jeux` → `/jeux` en anglais, `/jeux` en français, `/fr/jeux` →
  redirection, `/en/mon-espace` → `/mon-espace`, `/es/jeux` reste inconnu, liens d'une page anglaise : public
  préfixé, espace connecté sans préfixe ; `hreflang` d'une page avec paramètres.
- **Composants** (Vitest) : sélecteur (même page, langue active, masqué hors pages traduites), en-tête et pied de
  page en anglais et en allemand, mention « contenu en français », dates selon la langue, erreurs de connexion en
  anglais.
- **Suivi** : une page vue sur `/de/jeux` donne le chemin `/jeux`.
- **Non-régression** : la suite Vitest existante reste verte sans modifier ses attentes en français (les textes
  français sont repris tels quels dans `fr.json`).
- **Navigateur** : parcours FR → EN → DE sur l'accueil, Jeux, une page d'article, l'inscription, sur ordinateur et
  téléphone (textes allemands longs), rendu serveur (`curl /de` renvoie déjà l'allemand et `lang="de"`).

## Risques

- **Volume** : environ 35 pages et leurs composants à extraire. Découpé par groupes de pages, chacun livrable seul :
  une page pas encore extraite reste en français sous `/en`, ce qui ne casse rien.
- **Oubli d'un texte en dur** : un test rend chaque page traduite en allemand et cherche une liste de mots français
  courants (« Inscris-toi », « Découvre », « Connexion »…) ; utile mais pas exhaustif, complété par la relecture.
- **Qualité des traductions** : écrites par Claude, relues par l'équipe avant la fusion dans `main` (pas de mise en
  prod avant la relecture).
- **Rendu serveur** : le `server.ts` maison enveloppe déjà le gestionnaire ; le middleware s'insère autour, à
  vérifier sur la page d'erreur et la maintenance.
- **Composants partagés avec les espaces connectés** (cartes, badges, champs) : s'ils sont traduits, ils
  s'affichent en français dans ces espaces car la langue y est toujours `fr`.
