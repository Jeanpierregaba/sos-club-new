# 015 — Plan technique

## Approche

Un nouveau domaine `backend/app/admin/` porte tout l'espace administrateur :

- les collaborateurs et leurs permissions ;
- les invitations ;
- la double authentification ;
- le journal d'audit ;
- l'annuaire des inscrits ;
- les exports ;
- le tableau de bord.

Le domaine `comptes` garde la connexion et les sessions. Il gagne seulement l'étape de code de la double
authentification et la coupure des sessions à la suspension.

Toutes les règles vivent dans l'API (ADR-0002) : une dépendance FastAPI `exiger_permission(module,
action)` protège chaque route. Le site affiche ce que l'API autorise. Les décisions structurantes sont
dans l'[ADR-0008](../../decisions/0008-droits-des-collaborateurs-et-double-authentification.md).

Côté site, l'espace `/admin` est une mise en page à menu latéral sous la garde `_connecte`. Ses pages
s'appuient sur des fonctions du client API. Deux pages publiques s'ajoutent : `/activation`, pour finir
une invitation, et l'étape « code » de `/connexion`.

## Fichiers touchés

**API, créés : domaine `backend/app/admin/`**

- `catalogue.py` : la liste des modules, avec leur libellé et s'ils sont disponibles ou à venir, la liste
  des actions, les droits sensibles et les rôles préréglés.
- `models.py` : les modèles `Collaborateur`, `Permission`, `Invitation`, `DoubleAuth`, `CodeSecours`,
  `EtapeDoubleAuth`, `JournalAudit` et `Export`.
- `dependances.py` : les dépendances `collaborateur_courant` et `exiger_permission(module, action)`, et le
  journal des refus.
- `journal.py` : la fonction `journaliser(...)`, seule porte d'écriture du journal.
- `collaborateurs.py`, en service et routes : inviter, renvoyer, activer, modifier les droits,
  suspendre, réactiver, révoquer, réinitialiser la double authentification, revoir les droits.
- `double_auth.py` : l'enrôlement (secret chiffré, QR code en SVG, confirmation), la vérification avec
  anti-rejeu et les codes de secours.
- `inscrits.py` : l'annuaire paginé, ses filtres, la fiche d'un compte, la suspension et la réactivation
  d'un inscrit.
- `exports.py` : l'aperçu du volume, la génération en CSV (`csv`) ou XLSX (`xlsxwriter`), la
  neutralisation des formules, le lien de téléchargement et la purge.
- `tableau_de_bord.py` : les chiffres calculés et la date de calcul.
- `courriel.py` : l'envoi SMTP par la bibliothèque standard (`smtplib`, dans `asyncio.to_thread`). Hors
  production et sans SMTP configuré, le lien est seulement écrit dans le terminal de l'API.
- `schemas.py` et `router.py` : les schémas d'entrée et de sortie, et les routes sous `/api/admin`.

**API, modifiés**

- `app/comptes/models.py` : le statut `revoque`.
- `app/comptes/service.py` :
  - la connexion en deux étapes, quand la double authentification est active ;
  - le refus si la date de fin d'accès est passée ;
  - la fonction `couper_sessions(utilisateur_id)`.
- `app/comptes/router.py` : la route `POST /comptes/connexion/code`. L'ancienne route
  `/admin/chiffres` est remplacée par le tableau de bord.
- `app/comptes/creer_compte.py` : `--role admin` crée un super-administrateur. C'est l'amorce : le
  premier compte se crée en ligne de commande, les suivants par invitation.
- `app/config.py` : les réglages SMTP, `CLE_CHIFFREMENT` (obligatoire en HTTPS, comme `DATABASE_URL`) et
  les durées (invitation 72 h, lien d'export 15 min, fichier 24 h, étape de code 5 min).
- `app/main.py` : branchement du routeur, et purge horaire des exports expirés dans le `lifespan`.
- `.env.example` et `deploy/env.example` : les nouvelles variables, sans valeur.

**Migrations Alembic** : une migration `espace_admin`.

**Tests API créés** :

- `test_admin_droits.py`
- `test_collaborateurs.py`
- `test_double_auth.py`
- `test_inscrits.py`
- `test_exports.py`
- `test_journal.py`
- `test_tableau_de_bord.py`

**Site, créés**

- `src/routes/_connecte/admin.tsx` : la mise en page (menu latéral, en-tête) et la garde, qui renvoie
  vers `/mon-espace` si le rôle n'est pas `admin`.
- Les pages sous `src/routes/_connecte/admin/` :
  - `index.tsx` : le tableau de bord ;
  - `collaborateurs.tsx` et `collaborateurs.$id.tsx` ;
  - `inscrits.tsx` et `inscrits.$id.tsx` ;
  - `exports.tsx` ;
  - `journal.tsx` ;
  - `double-authentification.tsx`.
- `src/routes/activation.tsx` : choix de l'identifiant et du mot de passe, puis enrôlement de la double
  authentification si nécessaire.
- `src/components/admin/` : le menu (avec les modules « à venir »), la matrice des droits, le badge de
  statut, la carte de chiffre, les filtres, les dialogues de motif et de confirmation d'export, et le
  champ de code à 6 chiffres.

**Site, modifiés**

- `src/components/FormulaireConnexion.tsx` : la seconde étape « code ».
- `src/routes/_connecte/mon-espace.tsx` : un admin est renvoyé vers `/admin`.
- `src/lib/api/client.ts` : les fonctions de l'espace admin.
- `src/lib/api/schema.gen.ts` : régénéré par `npm run api:types`.

## Données

Migration non destructive : elle ne fait que créer des tables, ajouter une valeur de statut et ajouter
une table de lien pour les admins existants.

| Table               | Colonnes principales                                                                                                                                                                                                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `collaborateur`     | `id`, `utilisateur_id` (unique, nul tant que l'invitation n'est pas acceptée), `email` (unique), `prenom`, `nom`, `role_depart`, `perimetre_dre` (nul = national ; contrainte sur les 7 identifiants), `fin_acces`, `super_admin`, `invite_par_id`, `revu_le`, `cree_le`                               |
| `permission`        | `collaborateur_id`, `module`, `action` : clé primaire sur les trois                                                                                                                                                                                                                                    |
| `invitation`        | `id`, `collaborateur_id`, `jeton_hash` (unique), `expire_le`, `utilisee_le`, `annulee_le`, `envoi` (envoyé / échec), `cree_le`                                                                                                                                                                         |
| `double_auth`       | `utilisateur_id` (clé primaire), `secret_chiffre`, `active_le`, `dernier_pas` (anti-rejeu)                                                                                                                                                                                                             |
| `code_secours`      | `id`, `utilisateur_id`, `code_hash`, `utilise_le`                                                                                                                                                                                                                                                      |
| `etape_double_auth` | `jeton_hash` (unique), `utilisateur_id`, `expire_le`, `essais`                                                                                                                                                                                                                                         |
| `journal_audit`     | `id`, `quand`, `auteur_id` et `auteur_libelle` (sans lien vers `utilisateur`, pour qu'une suppression de compte ne touche pas le journal ; nuls si inconnu), `action`, `cible_type`, `cible_id`, `perimetre`, `details` (JSONB, sans secret), `adresse_ip`. Un déclencheur refuse `UPDATE` et `DELETE` |
| `export`            | `id`, `demandeur_id`, `type` (agrégé / nominatif), `format`, `filtres` (JSONB), `colonnes`, `finalite`, `nb_lignes`, `statut`, `fichier` (bytea, effacé à l'expiration), `jeton_hash`, `lien_expire_le`, `fichier_expire_le`, `telecharge_le`, `cree_le`                                               |

- **Statut d'un collaborateur.** Il est calculé, pas stocké :
  - sans compte, c'est « invitation envoyée » ou « invitation expirée », selon la dernière invitation ;
  - avec un compte, c'est le statut de `utilisateur` (actif, suspendu ou révoqué).
- **Reprise des admins existants.** La migration crée une ligne `collaborateur` super-administrateur
  nationale pour chaque compte `admin` existant.
- **Fiche d'un inscrit.** L'historique de ses changements de statut est lu dans le journal d'audit : pas de
  table en plus.

## API / interfaces

Toutes les routes sont sous `/api`, protégées par `verifier_origine` (ADR-0006). La colonne « Droit »
indique le couple vérifié par `exiger_permission`.

| Route                                                                                                                            | Droit                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `POST /comptes/connexion`                                                                                                        | public. Répond `{ etape: "code", jeton }` si la double authentification est active |
| `POST /comptes/connexion/code`                                                                                                   | public, avec le jeton d'étape                                                      |
| `GET /admin/moi`                                                                                                                 | tout collaborateur actif : son profil, ses droits, et `double_auth_requise`        |
| `GET /admin/catalogue`                                                                                                           | tout collaborateur actif                                                           |
| `GET /admin/tableau-de-bord`                                                                                                     | tableau de bord : consulter                                                        |
| `GET /admin/collaborateurs`, `GET /admin/collaborateurs/{id}`                                                                    | collaborateurs : consulter                                                         |
| `POST /admin/collaborateurs` (inviter), `POST …/{id}/invitation` (renvoyer)                                                      | collaborateurs : gérer les utilisateurs                                            |
| `PUT /admin/collaborateurs/{id}/permissions`                                                                                     | collaborateurs : administrer les permissions                                       |
| `POST …/{id}/invitation/annuler`, `POST …/{id}/suspendre`, `…/reactiver`, `…/revoquer`, `…/double-auth/reinitialiser`, `…/revue` | collaborateurs : gérer les utilisateurs                                            |
| `POST /activation/info`, `POST /activation` (jeton dans le corps, jamais dans l'adresse)                                         | public, avec le jeton d'invitation                                                 |
| `POST /admin/double-auth/enrolement`, `POST /admin/double-auth/confirmer`                                                        | le collaborateur lui-même                                                          |
| `GET /admin/inscrits`, `GET /admin/inscrits/{id}`                                                                                | inscrits : consulter, périmètre national                                           |
| `POST /admin/inscrits/{id}/suspendre`, `…/reactiver`                                                                             | inscrits : modifier                                                                |
| `POST /admin/exports/apercu`, `POST /admin/exports` (type agrégé)                                                                | statistiques : exporter                                                            |
| `POST /admin/exports/apercu`, `POST /admin/exports` (type nominatif)                                                             | inscrits : exporter                                                                |
| `GET /admin/exports`                                                                                                             | inscrits : exporter, ou statistiques : exporter (chacun ne voit que ses types)     |
| `GET /admin/exports/{id}/fichier?jeton=…`                                                                                        | le demandeur seul, lien valide et à usage unique                                   |
| `GET /admin/journal`                                                                                                             | journal : consulter                                                                |

Dans ce lot, la gestion des collaborateurs et des droits est réservée au super-administrateur. Ces
actions ne sont pas dans le catalogue des droits attribuables, faute de quoi un collaborateur pourrait
s'auto-promouvoir ou inviter un complice. Deux garde-fous s'y ajoutent :

- personne ne modifie ses propres droits ;
- le dernier super-administrateur ne peut pas être retiré. Les lignes des super-administrateurs sont
  verrouillées (`SELECT … FOR UPDATE`) pendant l'opération.

Un collaborateur qui a un droit sensible sans double authentification active n'a accès qu'à `GET
/admin/moi` et aux routes d'enrôlement. La fin d'accès dépassée coupe les sessions dès la requête
suivante.

Les types du site sont générés depuis l'OpenAPI (`npm run api:types`).

## Dépendances

Vérifiées sur PyPI le 2026-11-04 : licences libres, versions récentes.

- `pyotp` 2.10.0 (juin 2026, MIT) : codes TOTP (RFC 6238) et URI d'enrôlement.
- `xlsxwriter` 3.3.1 (octobre 2026, BSD-2) : écriture XLSX en flux. Il est préféré à `openpyxl`, dont la
  dernière version date de juin 2024 et qui sert surtout à lire. Les cellules sont écrites avec
  `write_string`, pour qu'aucune ne devienne une formule.
- `segno` 1.6.6 (mars 2025, BSD) : QR code d'enrôlement en SVG, en pur Python, sans dépendance.
- `cryptography` 50.0.2 (septembre 2026) : chiffrement Fernet des secrets TOTP.

L'envoi des e-mails se fait avec `smtplib` et `email` de la bibliothèque standard, sans dépendance.
Aucune dépendance n'est ajoutée au site.

## Sécurité

Points de `docs/SECURITY.md` et du CDC admin concernés :

- **Droits.** Le contrôle se fait côté serveur, route par route. Le site masque, mais l'API refuse. Chaque
  refus d'une route admin est journalisé (action `acces_refuse`).
- **Sessions.** Suspendre, révoquer ou atteindre la fin d'accès supprime toutes les sessions du compte.
  Cela règle aussi la petite tâche de `TASKS.md` sur la suspension.
- **Jetons.** Les jetons d'invitation, de téléchargement et d'étape de code ont 32 octets aléatoires. Seule
  leur empreinte SHA-256 est stockée. Ils sont à usage unique et ont une durée de vie courte.
- **Double authentification.**
  - Le secret est chiffré avec Fernet, sous la clé `CLE_CHIFFREMENT`.
  - L'étape de code est limitée à 5 erreurs par 15 minutes, par le même mécanisme que la connexion.
  - Le rejeu d'un code déjà utilisé est refusé.
  - Les codes de secours sont montrés une seule fois. Ils ont 80 bits d'aléa (16 caractères) et sont
    hachés en SHA-256. Une empreinte rapide suffit pour un secret aléatoire de cette taille, et vérifier
    10 empreintes Argon2 à chaque essai aurait été trop lourd (écart au plan initial, décidé à
    l'implémentation).
- **Exports.**
  - Les colonnes possibles forment une liste blanche : aucune colonne de secret n'y figure.
  - Les cellules commençant par `= + - @` (ou par une tabulation ou un retour chariot) reçoivent un
    apostrophe en tête.
  - Plafond de 50 000 lignes.
  - Le fichier n'est servi qu'au demandeur, avec une session et un lien valides. La réponse porte les
    en-têtes `Content-Disposition: attachment` et `no-store`.
  - Le fichier est effacé dès son téléchargement, ou à l'expiration du lien de 15 minutes, au plus tard
    sous 24 heures. Une purge tourne au démarrage puis toutes les heures.
- **Journal.** Il n'enregistre ni mot de passe, ni jeton, ni code, ni secret, ni contenu d'export : seuls
  les filtres, les colonnes, le nombre de lignes et la finalité y figurent.
- **Données de mineurs.**
  - L'annuaire nominatif exige « inscrits : consulter » et le périmètre national. Aucun collaborateur DRE n'a
    accès aux données nominatives tant que les clubs n'existent pas en base.
  - Le téléphone n'est exportable qu'en le cochant explicitement.

## Tests

- **TDD**, car ce sont des parties critiques de `docs/TESTING.md` (connexion et droits, données d'élèves).
  Le sous-agent `test-writer` écrit d'abord :
  - `test_admin_droits.py` : un test par rôle préréglé et par route, le périmètre DRE, la fin d'accès, la
    suspension en cours de session, la double authentification requise ;
  - `test_double_auth.py`.
- **Ensuite**, un test par critère d'acceptation de la spec :
  - invitation et activation, jeton réutilisé ou expiré ;
  - exports avec colonnes, formules neutralisées, lien expiré ou d'un autre collaborateur, aucun secret
    exporté ;
  - journal sans route d'écriture, et déclencheur qui refuse `UPDATE` et `DELETE` ;
  - tableau de bord sans chiffre codé en dur.
- **E-mails** : l'envoi SMTP est remplacé, dans les tests, par une boîte factice qui capture les messages.
- **Site** :
  - Vitest pour les fonctions du client et la matrice des droits ;
  - parcours vérifiés dans le navigateur, avec la vraie API locale : connexion avec code, invitation,
    activation, export, journal, sur ordinateur et à 375 px.

## Risques

- **Taille du lot.** C'est le plus gros chantier depuis le cadrage. Le découpage en tâches livre d'abord
  l'API par briques testées, puis l'interface. Chaque brique est commitée seule.
- **Perte de `CLE_CHIFFREMENT`** : les doubles authentifications sont à réinitialiser (voir l'ADR-0008).
  La clé doit être sauvegardée hors du VPS.
- **SMTP** : sans les paramètres, les invitations ne partent pas en production. Le reste du lot fonctionne.
- **Purge des exports** : une tâche périodique dans le processus de l'API. Si l'API redémarre souvent,
  la purge tourne aussi au démarrage.
- **Stress-test** : les corrections et les risques acceptés sont dans la spec, section « Points
  d'attention ».
