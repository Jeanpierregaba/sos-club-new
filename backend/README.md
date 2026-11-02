# Backend

API FastAPI de la plateforme, avec PostgreSQL. La décision est expliquée dans
[l'ADR 0001](../docs/decisions/0001-backend-fastapi-postgresql.md).

## Démarrer

Prérequis : [uv](https://docs.astral.sh/uv/) et Docker. Aucun fichier `.env` n'est nécessaire en local.

```bash
docker compose up -d --wait
```

```bash
cd backend && uv run alembic upgrade head
```

```bash
cd backend && uv run fastapi dev app/main.py --port 8000
```

- État de l'API et de la base : <http://127.0.0.1:8000/health>
- Documentation de l'API : <http://127.0.0.1:8000/docs>

## Créer un compte

Les inscriptions depuis le site n'existent pas encore. Pour créer le premier admin, lance cette commande,
qui demande le mot de passe sans l'afficher :

```bash
cd backend && uv run python -m app.comptes.creer_compte --role admin --identifiant ton-identifiant --prenom Prénom --nom Nom --email adresse@exemple.tg
```

Connecte-toi ensuite sur <http://localhost:3000/connexion>. Ouvre bien le site avec `localhost` : avec
`127.0.0.1`, l'origine diffère de `SITE_ORIGINE` et l'API refuse la connexion.

## Vérifier

La base doit être démarrée : les tests utilisent une vraie base `sosclub_test`, recréée à chaque lancement.
La base de développement n'est jamais touchée.

```bash
cd backend && uv run pytest
```

```bash
cd backend && uv run ruff check . && uv run ruff format --check .
```

## Modifier la base

1. Ajouter ou modifier un modèle héritant de `app.db.Base`, et l'importer dans `alembic/env.py`.
2. Générer la migration, puis la relire avant de l'appliquer :

```bash
cd backend && uv run alembic revision --autogenerate -m "description"
```

```bash
cd backend && uv run alembic upgrade head
```
