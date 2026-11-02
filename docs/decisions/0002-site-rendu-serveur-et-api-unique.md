# 0002 — Site en rendu serveur et API unique

- **Statut** : Accepté
- **Date** : 2026-11-02

## Contexte

Le cahier des charges décrit une application monopage React 18 avec un état local. Or le site existe
déjà en TanStack Start, et le porteur du projet a choisi FastAPI et PostgreSQL (ADR-0001). TanStack
Start pouvant lui-même porter de la logique serveur, il faut dire où vivent les règles métier.

## Options envisagées

- **Site en rendu serveur, API seule détentrice des règles** (retenu) : un seul endroit à sécuriser et à
  tester ; une future application mobile pourrait réutiliser l'API. Il faut faire passer le cookie du
  navigateur à l'API lors du rendu serveur.
- **Application monopage du cahier des charges** : déploiement plus simple, mais site à refaire, moins
  bon référencement et premier affichage plus lent sur un réseau faible.
- **Une partie de la logique dans les fonctions serveur du site** : pratique au début, mais les règles
  finissent éparpillées entre TypeScript et Python.

## Décision

Le site reste en TanStack Start et ne fait qu'afficher : toute donnée et toute règle passent par l'API
FastAPI, et le site n'accède jamais à la base.

## Conséquences

- Deux services à déployer, sur la même origine pour le cookie (ADR-0006).
- Les validations du site ne servent qu'au confort : l'API les refait toujours.
- Le site et l'API doivent rester d'accord sur les types : ils sont générés depuis le schéma OpenAPI.
