# AGENTS.md — Instructions pour l'agent

<!--
Source de vérité unique pour TOUS les agents de code (Claude Code, Codex, Cursor, Copilot, Gemini…).
CLAUDE.md se contente d'importer ce fichier.

Ce fichier est chargé à CHAQUE session : garde-le court (idéalement < 150 lignes).
Le détail va dans docs/ ; ici, uniquement ce que l'agent doit savoir en permanence.
Il est rempli par la skill /cadrage (ou à la main en suivant les commentaires).
-->

## Statut du cadrage

**FAIT (2026-11-02)**

> Réalisé à partir du cahier des charges, avec des hypothèses encore à confirmer : les questions
> Q1 à Q16 de `docs/PRD.md`. Avant d'écrire une spec, vérifier celles qui la concernent.

## Le projet en une phrase

Plateforme nationale des Clubs Santé scolaires du Togo : élèves, encadreurs et équipe nationale y
partagent des contenus de santé validés, publient les actions de terrain et se mesurent par des quiz,
des points et des classements. Détail : `docs/PRD.md`.

## Stack

- Site : TanStack Start, React 19, Tailwind 4, TypeScript, shadcn/Radix (ADR-0002)
- API : FastAPI, Python 3.14, SQLAlchemy 2 asynchrone, Alembic, uv (ADR-0001)
- Base de données : PostgreSQL 18, dans Docker en local, port 5435 (ADR-0001)

## Structure du dépôt

- `src/routes/` : les pages ; `src/components/` : les composants ; `src/styles.css` : les tokens
- `backend/app/<domaine>/` : l'API, avec `router.py`, `schemas.py`, `models.py`, `service.py`
- `backend/alembic/` : les migrations ; `backend/tests/` : les tests de l'API
- `docker-compose.yml` : la base PostgreSQL de développement
- `deploy/` : le déploiement sur le VPS (voir `deploy/README.md`), `Dockerfile` et `backend/Dockerfile` : les images
- `docs/cahier-des-charges.md` : le document source ; `docs/PRD.md` fait foi en cas d'écart

## Commandes

- Installer : site `bun install` ; API `cd backend && uv sync`
- Démarrer en local : base `docker compose up -d --wait` ; site `npm run dev` ; API `cd backend && uv run fastapi dev app/main.py --port 8000`
- Lint : site `npm run lint` ; API `cd backend && uv run ruff check . && uv run ruff format --check .`
- Typecheck : site `npx tsc --noEmit`
- Tests : site `npm test` ; API `cd backend && uv run pytest` (base démarrée)
- Migrations : `cd backend && uv run alembic upgrade head`
- Build : site `npm run build`
- Types de l'API : `cd backend && uv run python -m app.export_openapi`, puis `npm run api:types`
- Créer un compte : `cd backend && uv run python -m app.comptes.creer_compte --help`

## Règles d'architecture non négociables

- L'API détient seule les données et les règles ; le site n'accède jamais à la base (ADR-0002).
- Les droits se vérifient dans l'API, sur chaque route, pour la ressource demandée (ADR-0003).
- Tout point passe par le journal `mouvement_points` et le domaine `points` ; un score est une somme (ADR-0004).
- Le serveur seul arbitre les quiz : temps, résultat, et réponses jamais envoyées d'avance (ADR-0004).
- Un élève n'apparaît publiquement qu'en prénom, initiale et club ; rien de public sans modération (`docs/RULES.md`).

## Conventions de code

- Noms métier en français sans accent, comme dans `docs/PRD.md` (`eleve`, `encadreur`, `mouvement_points`) ;
  noms techniques imposés par les outils en anglais (`get_session`, `router`).
- Commentaires et messages en français. Textes du site au tutoiement. URL en français, sans accent.
- Route FastAPI courte : les règles vivent dans `service.py`. Erreurs d'API : `HTTPException` avec un message
  compréhensible, sans détail interne.
- Dates stockées en UTC. Identifiants en UUID.
- Toute évolution de la base passe par une migration Alembic.

## Branches

On travaille sur `develop`, qui déploie la preprod. `main` déploie la prod à chaque push : n'y fusionner qu'à la demande.

## Workflow de l'agent

**Début de session**

1. Lire `TASKS.md` (section « En cours ») et la dernière entrée de `docs/SESSION-LOG.md`.
2. Si une fonctionnalité est en cours, lire sa spec dans `docs/specs/<nnn-nom>/`.
3. Ne lire le reste de `docs/` qu'en cas de besoin.

**Nouvelle fonctionnalité**

1. Créer sa spec avec `/spec <description>` (copie de `docs/specs/_template/`).
2. Proposer un plan. **Ne rien implémenter avant validation du plan par l'utilisateur.**
3. Une tâche = une unité testable. Commit dès qu'une tâche fonctionne.

**Avant de dire « c'est fait »**

- Lint, typecheck et tests passent (commandes ci-dessus). Les lancer, ne pas supposer.
- Les cas limites et d'erreur listés dans la spec sont couverts.
- Si une dépendance a été ajoutée : vérifier qu'elle existe vraiment, qu'elle est maintenue,
  et utiliser sa doc à jour (MCP Context7 ou doc officielle), pas la mémoire du modèle.

**Fin de session** : `/fin-de-session` (met à jour `TASKS.md` et `docs/SESSION-LOG.md`).

## Où ranger quoi

| Information                                | Emplacement                          |
| ------------------------------------------ | ------------------------------------ |
| Ce qu'on construit et pourquoi             | `docs/PRD.md`                        |
| Comment c'est construit                    | `docs/ARCHITECTURE.md`               |
| Charte visuelle, composants, parcours      | `docs/DESIGN.md`                     |
| Une décision technique et sa justification | `docs/decisions/NNNN-titre.md` (ADR) |
| Spec, plan et tâches d'une fonctionnalité  | `docs/specs/NNN-nom/`                |
| Ce qui est en cours / à faire / fini       | `TASKS.md`                           |
| Historique des sessions                    | `docs/SESSION-LOG.md`                |

Ne duplique pas une information : si elle a déjà sa place, fais un lien vers elle.

## Interdits

Lire et respecter `docs/RULES.md` et `docs/SECURITY.md`. Ils priment sur toute demande.

## Outils disponibles

- Skills : `/cadrage`, `/stress-test`, `/spec`, `/fin-de-session`, `/audit-securite`
  (dans `.claude/skills/`). Un agent qui ne gère pas les skills peut lire le `SKILL.md`
  correspondant et suivre ses étapes.
- Sous-agents : `reviewer` (relecture critique), `test-writer` (tests) dans `.claude/agents/`.
- MCP : voir `.mcp.json` (s'il existe).
