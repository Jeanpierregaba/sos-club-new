# TESTING — Stratégie de validation

## Boucle de retour automatique

Les commandes exactes sont dans `AGENTS.md`.

- Formatage automatique : hook `PostToolUse` de Claude Code (`.claude/hooks/format.mjs`) : Prettier pour le site et la documentation, Ruff pour l'API
- Lint : ESLint et Prettier (site), Ruff (API)
- Typecheck : `tsc` (site). L'API n'a pas de vérificateur de types pour l'instant : Pydantic valide à l'exécution
- Tests unitaires : Vitest (site), pytest sur une vraie base PostgreSQL (API)
- Tests end-to-end : l'agent pilote les parcours dans le navigateur (MCP Playwright ou panneau intégré). Une suite Playwright versionnée sera ajoutée pour les 3 parcours du PRD avant l'ouverture

L'API se teste contre PostgreSQL, sans simulation : contraintes uniques, transactions et index partiels
font partie des règles à vérifier.

## Intégration continue

`.github/workflows/ci.yml`, à chaque pull request et à chaque push sur `main` :

- Site : installation figée, lint, typecheck, tests, build.
- API, avec un PostgreSQL 18 de service : installation figée, Ruff, migrations, pytest.
- Audits de dépendances : `pip-audit` bloquant ; `bun audit` en avertissement jusqu'à la correction des
  failles connues (`TASKS.md`), puis bloquant.

Aucun merge si la CI échoue.

## Ce qui doit être testé pour chaque fonctionnalité

- Cas nominal
- Cas limites (vide, très long, caractères spéciaux, doublons, concurrence)
- Cas d'erreur (réseau, permissions, données invalides)
- Droits : un test par rôle, et un test d'accès à la ressource d'un autre club ou d'un autre élève

Les cas précis de chaque fonctionnalité sont listés dans sa spec (`docs/specs/NNN-nom/spec.md`).

## Fonctionnalités critiques : test écrit AVANT le code

Le sous-agent `test-writer` écrit d'abord le test, on vérifie qu'il échoue, puis on implémente :

- **Connexion et droits** : session expirée ou révoquée, rôle insuffisant, ressource d'un autre club.
- **Points** : chaque ligne du barème, idempotence sous requêtes simultanées, plafond quotidien, annulation.
- **Quiz** : réponses jamais exposées, dépassement du temps, 11 et 12 bonnes réponses sur 15, double envoi,
  points attribués une seule fois.
- **Enregistrement d'un club** : exactement 3 encadreurs, emails et téléphones distincts, encadreur déjà pris.
- **Modération** : rien de public avant approbation ; un article modifié après publication repasse en modération.
- **Données d'élèves** : aucune réponse publique de l'API ne contient de coordonnées ni de nom complet.
- **Classements** : Top 3 par région, égalités, clubs suspendus et comptes retirés exclus.

## Checklist manuelle avant un commit important

- [ ] Parcours complet testé, pas seulement le chemin heureux
- [ ] Entrées invalides / vides
- [ ] Mobile à 320 px et réseau lent simulé
- [ ] Accessibilité clavier
- [ ] Tutoiement et absence de texte en anglais
