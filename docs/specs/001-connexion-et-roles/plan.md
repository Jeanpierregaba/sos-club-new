# 001 — Plan technique

## Approche

Sessions opaques en PostgreSQL et cookie `HttpOnly` (ADR-0003), avec des droits vérifiés dans l'API.

Le plan change un point du cadrage : **le site et l'API partagent la même origine**, l'API étant servie
sous `/api` (ADR-0006, nouvelle décision proposée). Avec `www.` et `api.`, le cookie devrait être partagé
sur tout le domaine parent et il faudrait gérer CORS avec identifiants. Avec une même origine, le cookie
reste limité au site et CORS disparaît. En local, le proxy de Vite renvoie `/api` vers FastAPI ; en
production, ce sera le proxy HTTPS (spec 002).

Les pages publiques ne dépendent pas de l'API : l'en-tête interroge `/api/comptes/moi` depuis le
navigateur, après l'affichage. Seules les pages protégées et `/connexion`, qui renvoie un utilisateur déjà
connecté vers son espace, appellent l'API pendant le rendu serveur, en transmettant le cookie reçu. Ce
contrôle sert l'affichage : la protection réelle reste dans l'API.

## Fichiers touchés

**API**

| Fichier                                  | Rôle                                                           |
| ---------------------------------------- | -------------------------------------------------------------- |
| `backend/app/comptes/models.py`          | `Utilisateur`, `Session`, `TentativeConnexion`                 |
| `backend/app/comptes/schemas.py`         | Connexion, utilisateur courant, chiffres admin                 |
| `backend/app/comptes/service.py`         | Normalisation, authentification, sessions, limites d'essais    |
| `backend/app/comptes/motdepasse.py`      | Hachage et vérification Argon2id, hors de la boucle asynchrone |
| `backend/app/comptes/dependances.py`     | `utilisateur_courant`, `exiger_role`, `verifier_origine`       |
| `backend/app/comptes/router.py`          | Routes `/api/comptes/*` et `/api/admin/chiffres`               |
| `backend/app/comptes/creer_compte.py`    | Commande de création de compte                                 |
| `backend/app/main.py`                    | Routeur, contrôle d'origine, erreurs de validation en français |
| `backend/app/config.py`                  | `site_origine`, durées, seuils                                 |
| `backend/alembic/env.py`                 | Import des modèles                                             |
| `backend/alembic/versions/*.py`          | Première migration                                             |
| `backend/openapi.json`                   | Schéma de l'API, versionné                                     |
| `backend/tests/conftest.py`, `test_*.py` | Base de test dédiée et tests                                   |

**Site**

| Fichier                               | Rôle                                                               |
| ------------------------------------- | ------------------------------------------------------------------ |
| `src/lib/api/schema.gen.ts`           | Types générés depuis `backend/openapi.json`                        |
| `src/lib/api/client.ts`               | Appel de l'API, côté navigateur et côté serveur, et erreurs typées |
| `src/lib/redirection.ts`              | Accepte seulement une page du site comme destination               |
| `src/hooks/use-moi.ts`                | Utilisateur courant pour l'en-tête                                 |
| `src/routes/connexion.tsx`            | Formulaire de connexion                                            |
| `src/routes/_connecte.tsx`            | Garde des pages protégées                                          |
| `src/routes/_connecte/mon-espace.tsx` | Page « Mon espace »                                                |
| `src/routes/index.tsx`                | « Mon espace » dans l'en-tête, lien vers `/connexion`              |
| `src/routes/__root.tsx`               | `lang="fr"`, pages 404 et d'erreur en français                     |
| `vite.config.ts`                      | Proxy `/api`, port 3000                                            |
| `package.json`                        | Script `api:types`, `openapi-typescript`                           |

**Configuration et documentation**

- `.env.example` : `SITE_ORIGINE` (API) et `API_URL_INTERNE` (site), sans valeur.
- `.github/workflows/ci.yml` : vérifie que les types générés sont à jour.
- `AGENTS.md`, `backend/README.md` : commande de création de compte.
- `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, ADR-0002, ADR-0003 : même origine, CORS retiré.
- `TASKS.md` : retire le port et la langue des petites tâches.

## Données

Migration non destructive, la première du projet : trois tables. Identifiants en UUID v7 (`uuid.uuid7()` de
Python 3.14), dates avec fuseau horaire.

```text
utilisateur
  id, role (eleve | encadreur | admin), identifiant (unique, minuscules),
  email (unique, minuscules, facultatif), telephone (facultatif), prenom, nom,
  mot_de_passe_hash, statut (actif | suspendu), consentement_le (facultatif), cree_le
  Contraintes : identifiant au format [a-z0-9._-]{3,30} ; email obligatoire sauf pour un élève

session
  id, utilisateur_id (cascade), jeton_hash (unique, SHA-256), cree_le, expire_le (indexé)

tentative_connexion
  id, cle_hash (SHA-256), adresse_ip, en_cours, cree_le (indexé)
```

Rôle et statut sont des textes avec une contrainte `CHECK`, plus simples à faire évoluer qu'un type enum
PostgreSQL. `tentative_connexion` contient chaque essai en cours et les échecs. La saisie n'y est jamais en clair, un
élève pouvant taper son mot de passe dans le champ identifiant. Les lignes sont purgées à chaque connexion,
réussie ou non, au-delà d'une heure.

## API / interfaces

| Route                           | Accès    | Réponses                                                 |
| ------------------------------- | -------- | -------------------------------------------------------- |
| `POST /api/comptes/connexion`   | Public   | 200 et cookie ; 401 ; 403 si suspendu ; 422 ; 429        |
| `POST /api/comptes/deconnexion` | Public   | 204, efface le cookie, même sans session valide          |
| `GET /api/comptes/moi`          | Connecté | 200 (`id`, `identifiant`, `prenom`, `nom`, `role`) ; 401 |
| `GET /api/admin/chiffres`       | Admin    | 200 (nombre de comptes par rôle) ; 401 ; 403             |

Toutes ces réponses portent `Cache-Control: no-store`.

```bash
cd backend && uv run python -m app.comptes.creer_compte --role admin --identifiant nom --prenom Prénom --nom Nom --email adresse@exemple.tg
```

La commande lit le mot de passe avec `getpass`, ou sur l'entrée standard si elle n'est pas interactive.

Côté site, `chargerMoi()` repose sur `createIsomorphicFn` de TanStack Start : dans le navigateur, un
`fetch("/api/...")` ; sur le serveur, un appel à `API_URL_INTERNE` avec le cookie lu par `getRequestHeader`.
Le formulaire utilise React Hook Form, Zod et les composants `form`, `input`, `button` et `alert` existants.

## Dépendances

| Paquet                                     | Version | Rôle                                 | Vérification du 2026-11-02                                                                 |
| ------------------------------------------ | ------- | ------------------------------------ | ------------------------------------------------------------------------------------------ |
| `argon2-cffi` (API)                        | 25.1.0  | Hachage des mots de passe            | Compatible Python 3.14 ; `argon2-cffi-bindings` 26.1.0 fournit des paquets binaires `abi3` |
| `email-validator` (API)                    | 2.3.0   | Validation des emails de la commande | Déjà présent avec `fastapi[standard]`, déclaré directement car utilisé directement         |
| `openapi-typescript` (site, développement) | 7.13.0  | Types TypeScript depuis OpenAPI      | Dépôt actif, TypeScript 5 requis, 5.9.3 installé                                           |

`slowapi` est écarté : ses compteurs par défaut restent en mémoire, par processus, et se perdent à chaque
redémarrage. La table `tentative_connexion` suffit, sans ajouter Redis.

## Sécurité

Points de `docs/SECURITY.md` couverts :

- **Hachage** : paramètres par défaut d'`argon2-cffi` (Argon2id, 64 Mio), calcul dans un thread, 4 hachages
  simultanés au maximum par processus pour contenir la mémoire. Réécriture de l'empreinte à la connexion si
  les paramètres changent.
- **Énumération de comptes** : même message, et vérification d'une empreinte factice si le compte n'existe
  pas, pour un temps de réponse proche. Les limites comptent aussi les identifiants inconnus.
- **Force brute** : l'essai est réservé en base avant le hachage, puis compté : une rafale simultanée ne
  teste pas plus de mots de passe que le seuil. Un compte a un seul compteur, qu'on saisisse l'identifiant ou
  l'email. Par adresse réseau (un `/64` en IPv6), seuls les échecs confirmés comptent : une classe qui se
  connecte en même temps ne se bloque pas elle-même. La connexion à la base est rendue pendant le hachage.
- **Session** : `secrets.token_urlsafe(32)`, empreinte SHA-256 en base, nouveau jeton à chaque connexion.
- **CSRF** : `SameSite=Lax`, et rejet de toute écriture dont l'en-tête `Origin` diffère de `SITE_ORIGINE`.
  Un appel sans `Origin` n'est pas un navigateur en cross-origin, et reste accepté.
- **Cookie `Secure`** : déduit de `SITE_ORIGINE` (HTTPS en production, `http://localhost:3000` par défaut).
- **Fuites** : gestionnaire d'erreurs de validation sans le champ `input` de FastAPI, qui renverrait le mot
  de passe ; `hide_parameters` sur le moteur SQL pour que ses erreurs n'écrivent aucune valeur dans les logs ;
  saisie refusée si elle dépasse 254 caractères après normalisation ou contient un caractère NUL.
- **Redirection** : seuls les chemins commençant par un seul `/` sont acceptés (ni `//`, ni `/\`).

## Tests

**En TDD** (`test-writer`, test en échec d'abord), sur une vraie base `sosclub_test`, créée et migrée
automatiquement, jamais la base de développement :

- `test_connexion.py` : identifiant, email, normalisation, mêmes réponses pour un mot de passe faux et un
  compte inconnu, suspendu, seuils de 5 et 50 échecs, classe de 40 connexions réussies, cookie, base sans
  secret.
- `test_session.py` : expiration par rôle (dates modifiées en base), suppression, suspension, déconnexion,
  deux appareils, remplacement de session.
- `test_droits.py` : 401, 403 et 200 sur les chiffres admin, pour chaque rôle.
- `test_origine.py` : écriture avec une origine étrangère, avec la bonne origine, sans origine.
- `test_creer_compte.py` : création et refus.
- `test_openapi.py` : `backend/openapi.json` à jour.

**Site (Vitest)** : `redirection.ts`, et validation et messages d'erreur du formulaire.

**Parcours dans le navigateur** : connexion, retour à la page demandée, déconnexion, retour arrière, API
arrêtée, 320 px et clavier. La route `POST` passe par le proxy, ce qu'aucun test unitaire ne couvre.

## Risques

Résultat du stress-test :

- **Blocage volontaire** (important) : quelqu'un peut bloquer un compte pendant 15 minutes en se trompant
  exprès. Risque accepté, le blocage étant court et le choix protégeant les comptes d'élèves.
- **Blocage d'une adresse partagée** (important) : 50 échecs depuis une même adresse bloquent 15 minutes tout
  l'établissement, ou tous les abonnés d'un opérateur qui partage ses adresses. Accepté tant qu'il n'y a pas
  de vrai trafic. À revoir dans la spec 002 avec le proxy retenu et le réseau des écoles.
- **Rafale** (mineur) : pendant une rafale, un essai légitime sur le compte visé peut recevoir 429 alors que
  moins de 5 échecs sont confirmés. La sécurité reste garantie : le système refuse parfois trop, jamais moins.
- **Échecs par adresse** (mineur) : le seuil de 50 ne compte que les échecs confirmés et peut donc être
  légèrement dépassé pendant une rafale. Il reste une protection grossière, le seuil par compte est le vrai rempart.
- **Adresse réseau derrière le proxy** (important) : sans configuration du proxy, tous les utilisateurs
  partageraient une seule adresse, et le seuil de 50 bloquerait tout le monde. Traité avec
  `FORWARDED_ALLOW_IPS` dans `deploy/compose.yaml`, et vérifié derrière Caddy : un en-tête falsifié est ignoré.
- **Mémoire d'Argon2** (important) : 40 élèves simultanés et 4 hachages à la fois donnent une attente de
  quelques secondes, à mesurer sur le serveur retenu.
- **Mise en production** (important) : l'API ne répond sous `/api` que derrière le proxy. Le build Node seul
  ne suffit donc pas, la spec 002 doit le prévoir.
- **Origine exacte** (mineur) : ouvrir le site en `http://127.0.0.1:3000` fait échouer la connexion en local,
  car l'origine diffère de `localhost`. Documenté dans `backend/README.md`.
- **Pas de renouvellement de session** (mineur) : un élève devra se reconnecter tous les 30 jours, même s'il
  utilise le site chaque jour. Choix volontairement simple, facile à faire évoluer.
- **Rendu serveur des pages protégées** (mineur) : `/mon-espace` dépend de l'API dès le rendu. D'où le
  message d'indisponibilité prévu par la spec.
