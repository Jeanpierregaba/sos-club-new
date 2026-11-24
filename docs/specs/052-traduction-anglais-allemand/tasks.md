# 052 — Tâches

Ordre d'exécution. Chaque groupe de pages est livrable seul : une page pas encore extraite reste en français sous
`/en` et `/de`, sans rien casser.

- [x] 1. ADR-0015 (langues de l'interface), lignes de `docs/PRD.md` (hors scope) et de `docs/DESIGN.md` (ton
      « you » / « du », sélecteur)
- [x] 2. Tests d'abord : `src/lib/langues.test.ts` (adresses, redirections `/fr`, pages non traduites, `/es`, liens
      préfixés ou non, `hreflang`) et test des clés (mêmes clés, aucune vide, mêmes paramètres dans les 3 langues)
      — ils échouent
- [x] 3. Socle : Paraglide (`project.inlang`, `messages/*.json`, plugin Vite, `src/paraglide/` ignoré), `rewrite` du
      routeur, `paraglideMiddleware` dans `server.ts`, `src/lib/langues.ts`, `<html lang>`, `hreflang`, redirections ;
      les tests de la tâche 2 passent, le suivi d'activité garde `/jeux` pour `/de/jeux` (test), rendu serveur vérifié
      avec `curl`
- [x] 4. Cadre commun : en-tête, menu mobile, pied de page, `SelecteurLangue` (remplace le bouton FR/EN),
      `ContenuEnFrancais`, page 404 et page d'erreur, dates selon la langue (tests Vitest)
- [x] 5. Accueil, Club Santé, les 7 axes, charte, témoignages : textes et `head()` traduits (tests)
- [x] 6. Jeux, certification, classements (hall of fame), vérification d'un certificat, carte de classement partagée
- [x] 7. Bibliothèque, galerie, magazine, articles (liste et article), agenda (liste et événement), carte des clubs,
      fiche d'un club, avec la mention « contenu en français »
- [x] 8. Génie Imhotep : description, inscription, palmarès, hall of fame
- [x] 9. Inscription, connexion, activation, mot de passe oublié et nouveau : validation du site et erreurs connues de
      l'API traduites, repli sur le message français (tests)
- [x] 10. Vérification au navigateur : FR → EN → DE sur l'accueil, Jeux, un article, l'inscription, ordinateur et
      téléphone (textes allemands longs), recherche de textes français restés en dur ; `AGENTS.md` (où sont les
      textes, ajouter une clé)
- [ ] 11. Suite complète (lint, typecheck, Vitest, build), critères d'acceptation, relecture par le sous-agent
      `reviewer`, `TASKS.md` ; relecture des traductions par l'équipe avant la fusion dans `main` — fait le 2026-11-24, sauf la relecture
      par l'équipe
