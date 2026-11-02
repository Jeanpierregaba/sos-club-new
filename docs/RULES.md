# RULES — Interdits stricts

<!--
Ce ne sont PAS des préférences de style (ça va dans AGENTS.md) : ce sont des interdits que l'agent
ne doit JAMAIS enfreindre, quelle que soit la demande. Les règles déjà imposées techniquement
(permissions et hooks dans .claude/settings.json) sont marquées [bloqué].
-->

## Code et dépendances

- Ne jamais ajouter une dépendance sans vérifier qu'elle existe, qu'elle est maintenue et qu'elle est
  bien celle attendue (nom exact : attention aux paquets aux noms proches).
- Ne jamais désactiver un test, une règle de lint ou une vérification de type pour « faire passer ».
- Ne jamais laisser de code mort, de `console.log` de debug ou de TODO sans entrée dans `TASKS.md`.

## Secrets

- Jamais de secret, clé ou mot de passe en dur dans le code, les tests ou les docs.
- Ne jamais lire ni modifier les fichiers `.env` réels. [bloqué]
- Toute nouvelle variable d'environnement est ajoutée (sans valeur) à `.env.example`.

## Données

- Ne jamais exécuter de migration destructive (suppression de table, de colonne, de données)
  sans confirmation explicite de l'utilisateur.
- Ne jamais se connecter à la base de production depuis l'environnement de développement.

## Git

- Ne jamais réécrire l'historique partagé (`push --force`, `reset --hard` sur une branche poussée). [bloqué]
- Ne jamais committer directement sur la branche principale une fois le projet en production.

## Spécifiques au projet

- Ne jamais exposer publiquement les coordonnées d'un élève, ni plus que son prénom, l'initiale de son
  nom et son club. Jamais de liste publique des membres d'un club.
- Ne jamais ajouter de messagerie privée ni de moyen de contacter un élève sans décision écrite dans un ADR.
- Ne jamais collecter de donnée de santé individuelle (dépistage inclus) sans spec et validation juridique.
- Ne jamais charger de vraies données d'élèves avant le récépissé de l'IPDCP (voir `docs/PRD.md`, Q9).
- Ne jamais écrire de points ailleurs que dans le journal `mouvement_points`, via le domaine `points`
  (ADR-0004), ni calculer un résultat de quiz ou de score dans le navigateur.
- Ne jamais inventer un contenu médical présenté comme réel : quiz, article et fiche de test sont
  signalés comme tels, et rien n'est publié sans validation de l'équipe nationale.
- Tous les textes du site tutoient, sans exception.
