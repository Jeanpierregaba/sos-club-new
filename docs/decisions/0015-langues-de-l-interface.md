# 0015 — Langues de l'interface : anglais et allemand par préfixe d'adresse

- **Statut** : Accepté
- **Date** : 2026-11-24
- **Décidé avec** : spec 052 (site en anglais et en allemand)

## Contexte

Le site est en français, la langue des élèves et des encadreurs togolais. Les partenaires, bailleurs et visiteurs
étrangers doivent pouvoir comprendre les pages publiques en anglais et en allemand. Le PRD classait les autres
langues hors du MVP ; le bouton « FR / EN » de l'en-tête ne faisait rien. Les contenus (articles, quiz, livres) sont
saisis en français et le resteront. Les pages publiques doivent garder leur langue dans un lien partagé et être
indexées dans chaque langue.

## Options envisagées

1. **`react-i18next`** : très répandu, mais clés vérifiées seulement à l'exécution, dictionnaires chargés au démarrage
   et adresses localisées à construire soi-même (dupliquer les routes sous `/en` et `/de`, ou les réécrire à la main).
2. **Paraglide JS** (`@inlang/paraglide-js`) avec la réécriture d'adresses de TanStack Router : messages compilés en
   fonctions typées (une clé manquante est une erreur de typage), seules les traductions utilisées dans le bundle,
   `localizeUrl` / `deLocalizeUrl` branchés sur `rewrite` du routeur, middleware pour le rendu serveur ; guide officiel
   pour TanStack Start.
3. **Langue mémorisée** (cookie ou navigateur) sur les mêmes adresses : plus simple, mais un lien partagé s'ouvre en
   français, une seule langue indexée, et un cookie de plus à justifier.

## Décision

Paraglide JS, avec la langue lue dans l'adresse seulement : `/en/...` et `/de/...`, le français sans préfixe et par
défaut ; pas de cookie ni de détection du navigateur ; seules les pages publiques sont traduites, les contenus en base,
les espaces connectés et l'admin restent en français.

## Conséquences

- Les fichiers de routes ne changent pas : le routeur réécrit `/en/jeux` en `/jeux` à l'entrée et ajoute le préfixe
  en sortie. Le suivi d'activité (ADR-0014) voit le même gabarit dans toutes les langues.
- Les textes de l'interface vivent dans `messages/fr.json`, `en.json`, `de.json` ; tout nouveau texte d'une page
  publique s'ajoute dans les trois. Une liste unique des pages traduites (`src/lib/langues.ts`) décide de ce qui
  garde le préfixe.
- L'API reste en français ; le site traduit les erreurs connues des formulaires publics.
- Les traductions sont écrites par l'agent et relues par l'équipe avant la production.
- Ajouter une langue (éwé, kabiyè…) revient à ajouter un fichier de messages et un préfixe.
