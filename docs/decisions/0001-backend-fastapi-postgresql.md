# 0001 — Backend FastAPI et base PostgreSQL

- **Statut** : Accepté
- **Date** : 2026-11-02

## Contexte

Le projet est une plateforme web, pas un simple site : le site TanStack Start
a besoin d'une API et d'une base de données. Le choix de FastAPI et de PostgreSQL a été fait par
le porteur du projet. Restaient à décider les outils autour et l'organisation locale.

## Options envisagées

- **Accès à la base** : SQLAlchemy 2 en asynchrone avec asyncpg et Alembic (retenu, standard avec
  FastAPI, migrations versionnées) ; SQLModel (plus court, mais moins de contrôle sur les requêtes).
- **Paquets Python** : uv (retenu, fichier de verrouillage `uv.lock`, installations reproductibles) ;
  pip avec `requirements.txt` (aucun outil à installer, mais pas de verrouillage complet).
- **PostgreSQL en local** : conteneur Docker dédié (retenu, isolé des autres projets de la machine,
  même version pour tout le monde) ; PostgreSQL de Homebrew (version 16, partagé entre les projets).

## Décision

FastAPI dans `backend/`, SQLAlchemy 2 asynchrone, asyncpg, Alembic et uv, avec PostgreSQL 18 dans
le conteneur de `docker-compose.yml`, sur le port 5435.

## Conséquences

- Le site et l'API vivent dans le même dépôt, mais se déploient séparément : il faudra un hébergeur
  pour l'API et un PostgreSQL de production.
- La base locale n'a pas de mot de passe et n'écoute que sur `127.0.0.1` : aucun secret à partager
  ni de `.env` à créer pour développer. En production, `DATABASE_URL` est obligatoire de fait, car
  la valeur par défaut pointe vers la machine locale.
- Le schéma de la base n'est pas encore défini : aucune table et aucune migration pour l'instant.
