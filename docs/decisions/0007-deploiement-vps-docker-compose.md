# 0007 — Déploiement sur un VPS avec Docker Compose

- **Statut** : Accepté
- **Date** : 2026-11-02

## Contexte

Le porteur du projet a choisi un VPS et demande une preprod et une prod déployées automatiquement. Le dépôt est
privé, sur le plan GitHub Free : les secrets d'environnement et les approbations de déploiement n'y sont pas
disponibles.

## Options envisagées

- **Images construites par GitHub Actions et publiées sur GHCR** (retenu) : le VPS ne compile rien, chaque commit
  a son image, et revenir en arrière ne demande qu'un SHA. Dépend de la disponibilité de GHCR au déploiement.
- **Compilation sur le VPS avec `git pull`** : aucun registre, mais le VPS doit disposer des outils et de la mémoire
  de compilation, ce qui dégrade la prod pendant le build. Pas de version immuable pour revenir en arrière.
- **Proxy Caddy** (retenu) : certificats HTTPS automatiques et configuration très courte. Nginx et Certbot
  demanderaient davantage de configuration, Traefik ajouterait l'accès au socket Docker.
- **Secrets dans un fichier sur le VPS** (retenu) : ils ne transitent pas par la CI, qui ne connaît que l'accès SSH.
  En contrepartie, ils se créent et se changent à la main.
- **Base PostgreSQL managée** : sauvegardes prises en charge, mais coût plus élevé et transfert de données à
  déclarer si elle est hors du Togo.

## Décision

Un VPS unique héberge la preprod et la prod, chacune dans son projet Docker Compose avec sa propre base, derrière
un seul Caddy. `develop` se déploie sur la preprod, `main` sur la prod, avec des images GHCR identifiées par le SHA
du commit. Le contenu de `deploy/` en est l'application.

## Conséquences

- La branche de travail est `develop` : passer sur `main` revient à mettre en production, sans approbation
  supplémentaire possible avec ce plan GitHub.
- Une panne du VPS arrête les deux environnements, et la preprod partage les ressources de la prod. Séparer plus
  tard demandera surtout de scinder le Caddyfile.
- Les sauvegardes restent sur le VPS tant qu'un stockage externe n'est pas choisi : un risque à fermer avant
  d'accueillir de vraies données.
- Le retour arrière ne concerne pas les migrations : elles doivent rester compatibles avec la version précédente.
- La clé SSH de déploiement équivaut à un accès root au serveur.
- Si le VPS est hors du Togo, l'IPDCP doit en être informée avant tout transfert (loi n° 2019-014, art. 28).
