# 0006 — Site et API sur la même origine

- **Statut** : Accepté (validé avec la spec 001)
- **Date** : 2026-11-02

## Contexte

Le cadrage prévoyait le site sur `www.` et l'API sur `api.`. Or le rendu serveur du site doit recevoir le
cookie de session pour le transmettre à l'API, ce qui n'arrive que si le cookie couvre les deux adresses.

## Options envisagées

- **Même origine, API sous `/api`** (retenu) : cookie limité au site, pas de CORS, moins de surface d'attaque.
  L'API n'existe qu'à travers un proxy, à configurer en local comme en production.
- **Deux sous-domaines, cookie sur le domaine parent** : déploiements plus indépendants, mais cookie envoyé à
  tous les sous-domaines, CORS avec identifiants, et configuration propre à chaque environnement.

## Décision

Toutes les routes de l'API commencent par `/api` et sont servies sur le domaine du site : par le proxy de
Vite en local, par le proxy HTTPS en production. Le rendu serveur du site appelle l'API directement, via
`API_URL_INTERNE`, en transmettant le cookie.

## Conséquences

- L'hébergeur retenu doit permettre d'orienter `/api` vers l'API (spec 002). C'est simple sur un serveur
  virtuel, à vérifier sur une plateforme gérée.
- Pas de CORS à configurer. Le contrôle de l'en-tête `Origin` reste nécessaire.
- `/health` et `/docs` restent hors de `/api`, donc inaccessibles depuis l'extérieur en production.
- Le proxy doit transmettre l'adresse réseau réelle du client, dont dépendent les limites d'essais.
