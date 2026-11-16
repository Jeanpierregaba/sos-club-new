# 040 — Plan technique

## Approche

Un nouveau domaine `backend/app/cartes/`, calqué sur le certificat Génie Imhotep (spec 029), qui a déjà un PDF
avec QR code et une page publique de vérification.

- **Une ligne par carte, un statut calculé.** La table `carte` garde ce qui ne se recalcule pas : le numéro, le code
  du QR, le type, la date de délivrance et la suspension par l'équipe. La validité, le club et le rôle se calculent
  à chaque lecture depuis le compte, l'affiliation ou le rattachement et la présidence.
  - Avantage : aucun crochet à poser dans les dizaines d'endroits qui suspendent un compte, retirent une affiliation
    ou passent une présidence. La carte ne peut pas être désynchronisée.
  - Alternative écartée : un champ `statut` tenu à jour à chaque événement. C'est plus rapide à lire, mais fragile :
    un oubli suffit, et la spec 033 a montré le nombre de ces chemins.
- **Délivrance en deux points seulement**, par une fonction idempotente `delivrer(db, utilisateur, type)`
  (`INSERT … ON CONFLICT (utilisateur_id) DO NOTHING`) :
  - à l'inscription d'un élève (`eleves/service.inscrire` et le seed commun) ;
  - à l'activation d'un encadreur (`encadreurs/verification.activer`) : sa carte existe dès la vérification et n'est
    valide qu'avec un rattachement actif.
  - La migration délivre la carte des comptes existants.
- **Fichiers produits à la demande**, jamais stockés :
  - le PDF avec reportlab, à la manière de `certificat_pdf.py` (polices Noto Sans déjà présentes) ;
  - l'image PNG avec Pillow, le QR code étant dessiné par segno.

## Fichiers touchés

### API, créés

- `backend/app/cartes/models.py` : `Carte`, `TypeCarte`, la séquence `carte_numero_seq`.
- `backend/app/cartes/service.py` : `delivrer`, `etat_de(db, carte)` (statut, cause, club, rôle, établissement),
  `ma_carte`, `suspendre`, `reactiver`, `historique`.
- `backend/app/cartes/verification.py` : `verifier(db, code)` et la limite par adresse IP.
- `backend/app/cartes/rendu.py` : `pdf(etat)` et `png(etat)`, avec une mise en page commune (format carte bancaire
  85,6 × 54 mm, PNG à 1012 × 638 px).
- `backend/app/cartes/schemas.py`, `router.py` (espace et public) et `router_admin.py`.
- `backend/alembic/versions/<rev>_cartes_numeriques.py` : la table, la séquence et la délivrance aux comptes
  existants.
- `backend/tests/test_cartes.py` (délivrance, statut, espace, admin) et `test_cartes_verification.py` (page
  publique, limite, aucune fuite).

### API, modifiés

- `eleves/service.py` (`inscrire`), `seed_commun.py` et `encadreurs/verification.py` (`activer`) : appel de
  `delivrer`.
- `main.py` : les routeurs.
- `admin/schemas.py` et `admin/inscrits.py` : la carte dans `InscritDetail`.
- `config.py` : `verifications_carte_max_adresse` (60 par 15 minutes).
- `docs/SECURITY.md` : le code du QR et la page publique.

### Site, créés

- `src/routes/carte.$code.tsx` : la page publique de vérification, avec `noindex`.
- `src/routes/_connecte/ma-carte.tsx` : « Ma carte membre » ou « Ma carte encadreur », selon le rôle.
- `src/components/cartes/ApercuCarte.tsx` : l'aperçu, le statut et les téléchargements.
- `src/components/cartes/VerificationCarte.tsx` : le contenu de la page publique.
- `src/components/admin/CarteInscrit.tsx` : le bloc de la fiche admin, avec la suspension et la réactivation (le
  `DialogueMotif` existant).
- `src/components/cartes/Cartes.test.tsx`.

### Site, modifiés

- `src/components/espace/CarteMembre.tsx` : le numéro, le statut et un lien « Voir et télécharger ma carte ».
- `EspaceEncadreur.tsx` : un raccourci « Ma carte encadreur ».
- La navigation de l'espace : l'entrée « Ma carte ».
- `admin/inscrits.$id.tsx` : le bloc carte.
- `src/lib/api/client.ts` et les types régénérés.

## Données

Nouvelle table `carte`, sans migration destructive :

| Colonne                                             | Type                                                | Rôle                                                                           |
| --------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------ |
| `id`                                                | UUID                                                |                                                                                |
| `utilisateur_id`                                    | UUID, FK `utilisateur` `ON DELETE SET NULL`, unique | Le numéro survit à une suppression future du compte et n'est jamais réattribué |
| `type`                                              | `membre` \| `encadreur`                             |                                                                                |
| `numero`                                            | `String(12)`, unique                                | `CS-M-000123` ou `CS-E-000045`, une séquence unique pour les deux types        |
| `code`                                              | `String(32)`, unique                                | Le code du QR : `secrets.token_urlsafe(24)`, 192 bits                          |
| `delivree_le`                                       | timestamptz                                         |                                                                                |
| `suspendue_le`, `suspendue_par`, `motif_suspension` |                                                     | La suspension par l'équipe, nulle si aucune                                    |

- Une contrainte CHECK : `suspendue_le` et `motif_suspension` sont nuls ensemble.
- L'historique (délivrance, suspensions, réactivations) vient du `journal_audit` (actions `carte_suspendue` et
  `carte_reactivee`), comme les autres fiches admin. La délivrance vient de `delivree_le`.
- **Le code du QR est stocké en clair.** Il doit être réimprimé à chaque téléchargement et ne donne accès qu'au
  statut, au numéro et au club. Une empreinte obligerait à le générer une seule fois et à ne jamais pouvoir
  reproduire la carte. Il est exclu des exports et du journal (CDC admin § 13).
- **La migration** délivre une carte à chaque élève, puis à chaque encadreur `actif`, dans l'ordre de création des
  comptes, avec `nextval`. Le code est produit en SQL natif, sans extension :
  `translate(left(encode(sha256((gen_random_uuid()::text || gen_random_uuid()::text)::bytea), 'base64'), 32), '+/', '-_')`,
  soit 32 caractères URL-sûrs et 192 bits, la même forme que `secrets.token_urlsafe(24)`.
- **Forme du code** acceptée par la vérification : `^[A-Za-z0-9_-]{32}$`. Tout le reste répond 404 sans requête en
  base.

### Calcul de l'état

| Type      | Valide si                                                                      | Club affiché                                           | Rôle                                                                 |
| --------- | ------------------------------------------------------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------- |
| Membre    | compte `actif`, `utilisateur_id` non nul, pas de suspension par l'équipe       | celui de l'affiliation `active`, sinon « Non affilié » | « Président du club » si `club.president_id` = lui, sinon « Membre » |
| Encadreur | les mêmes conditions, plus `Encadreur.etat = actif` et un rattachement `actif` | celui du rattachement actif                            | « Encadreur »                                                        |

L'établissement vient de `Eleve.etablissement_id` ou de `Encadreur.etablissement_id`.

La cause, montrée au titulaire et à l'admin, prend l'une de ces valeurs : `compte_suspendu`, `non_verifie`,
`sans_rattachement`, `suspendue_par_l_equipe` ou `compte_supprime`.

## API / interfaces

### Espace

| Route                                                  | Réponse                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /api/cartes/moi`                                  | `MaCarte` : le type, le prénom, le nom, le rôle, le numéro, l'établissement, le club, la date de délivrance, la validité, la cause, et l'adresse de vérification (avec le code). 404 pour un visiteur, un collaborateur ou un encadreur pas encore vérifié. `Cache-Control: no-store`. |
| `GET /api/cartes/moi.pdf` et `GET /api/cartes/moi.png` | Le fichier en pièce jointe (`carte-membre-CS-M-000123.pdf`), `no-store`. 409 si la carte n'est pas valide.                                                                                                                                                                             |

### Public

| Route                                 | Réponse                                                                                                                                                                                                                                                                                                                                           |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /api/cartes/verification/{code}` | `VerificationCarte` : le type, le numéro, le club (ou `null` pour « Non affilié »), `valide` (booléen) et `verifiee_le`. Rien d'autre (`extra="forbid"` sur le schéma de sortie). Un code de mauvaise forme ou inconnu renvoie 404 « Cette carte n'existe pas ». Au-delà de la limite par adresse IP, 429. `no-store` et `X-Robots-Tag: noindex`. |

### Admin

| Route                                                            | Rôle                                                                                                                                                                        |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `InscritDetail.carte`                                            | Le numéro, le type, la validité, la cause, `delivree_le`, la suspension (date, motif) et l'historique.                                                                      |
| `POST /api/admin/inscrits/{id}/carte/suspendre` `{motif 10-200}` | Droit `inscrits:modifier`, double authentification. Journalise et notifie le titulaire. Accepté sur une carte déjà non valide. 409 si elle est déjà suspendue par l'équipe. |
| `POST /api/admin/inscrits/{id}/carte/reactiver` `{motif 10-200}` | Mêmes droits. 409 si elle n'est pas suspendue par l'équipe.                                                                                                                 |

### Site

- La page `/carte/<code>` appelle l'API côté serveur (SSR), comme `certificats.$numero.tsx`, et pose
  `<meta name="robots" content="noindex">`.
- Le QR code des fichiers mène à `settings.site_origine + "/carte/" + code`.

## Dépendances

Aucune nouvelle. reportlab 5, segno 1.6 et Pillow 13 sont déjà dans `pyproject.toml` et servent déjà, aux
certificats, à la double authentification et aux images. Pour le PNG, la mise en page passe par Pillow (`ImageDraw`,
polices Noto Sans en `ImageFont.truetype`) et le QR par segno (`segno.make(...).to_pil()` ou un rendu en matrice).
L'API de segno sera vérifiée avec Context7 avant d'écrire `rendu.py`.

## Sécurité

- **Droits (ADR-0003)** : chaque route d'espace ne lit que la carte de `moi`. Aucun identifiant n'est pris dans
  l'adresse. Les routes admin vérifient le droit, la double authentification et l'existence de la cible.
- **RULES, aucune fuite publique** :
  - la vérification ne renvoie ni nom, ni pseudonyme, ni établissement, ni coordonnée, ni cause ;
  - un test compare l'ensemble exact des clés de la réponse ;
  - le club d'un élève y figure sans son nom, conformément à Q30. Seul quelqu'un qui tient la carte, et donc voit
    déjà le nom, peut faire le lien.
- **Énumération** :
  - la vérification n'accepte que le code de 192 bits, jamais le numéro ;
  - la limite par adresse IP (même mécanisme que `oubli._limiter_adresse`, préfixe `carte:`) est une défense en
    profondeur.
- **Injection dans le PDF ou l'image** : les noms passent par `drawString` et `ImageDraw.text`, sans interprétation.
  La longueur est bornée par une coupure à la largeur.
- **Cache** : `no-store` sur les fichiers et sur `moi`. Une carte suspendue ne doit pas rester dans un cache
  partagé.
- **SECURITY.md** : une ligne pour « code de carte : secret du QR, exclu des exports et du journal ».

## Tests

Les parties critiques sont les droits et les données publiques : leurs tests sont écrits avant le code.

### `test_cartes.py`

- une inscription crée une carte « Non affilié » ;
- l'affiliation confirmée affiche le club, avec le même numéro ;
- la fin de l'affiliation remet « Non affilié », la carte reste valide ;
- la présidence et la passation changent le rôle ;
- un encadreur en attente n'a pas de carte (404). Vérifié sans rattachement, il a une carte non valide ; rattaché, sa
  carte devient valide ; son rattachement retiré, elle redevient non valide ;
- un compte suspendu, puis réactivé, garde le même numéro ;
- la suspension par l'équipe tient après la réactivation du compte ;
- un visiteur ou un collaborateur reçoit 404 ;
- l'unicité sous 20 délivrances simultanées (`asyncio.gather`) ;
- le PDF et le PNG :
  - les types MIME et `no-store` ;
  - le PDF contient le numéro, le prénom et l'adresse de vérification ;
  - le QR du PNG, décodé avec `segno` en sens inverse, est impossible. On vérifie plutôt que la fonction de rendu
    reçoit l'adresse et que l'image a la bonne taille ;
- une carte non valide renvoie 409 ;
- côté admin :
  - suspendre et réactiver, avec le journal et la notification sans nom de collaborateur ;
  - sans le droit : 403 ;
  - un motif trop court : 422 ;
  - suspendre deux fois : 409.

### `test_cartes_verification.py`

- les clés exactes de la réponse et les en-têtes ;
- une carte non valide ;
- un code inconnu ou mal formé : 404 ;
- un numéro à la place du code : 404 ;
- la limite par adresse IP : 429 ;
- aucun prénom, nom ni pseudonyme dans le corps.

### Migration

Dans `test_migrations` : la délivrance aux comptes existants, et un encadreur en attente qui n'en reçoit pas.

### Site (Vitest)

- l'aperçu valide, avec les deux boutons de téléchargement ;
- l'aperçu non valide, sans téléchargement, avec la marche à suivre ;
- l'encadreur sans rattachement ;
- la page publique valide, non valide et inconnue ;
- le bloc admin : la suspension avec un motif.

## Risques

- **Q30 et RULES** : le club d'un élève apparaît sur une page publique, sans nom. C'est la décision Q30, mais c'est
  le même sujet que la question encore ouverte des specs 036 et 037 (afficher le club sans le choix de l'élève). À
  signaler au porteur du projet lors de la validation.
- **Écritures sur une route publique** : chaque vérification ajoute une ligne `tentative_connexion` pour la limite
  par IP. Le volume attendu est faible, et ces lignes sont déjà purgées après une heure.
- **Calcul de l'état** : trois ou quatre requêtes par lecture. C'est négligeable pour une page personnelle ou une
  vérification ; il n'y a aucune liste de cartes à calculer en masse.
- **Fiche de l'encadreur multi-clubs** : la spec 033 limite l'encadreur à un club. Si cela change, le club de la carte
  devra devenir une liste.
- **Mise en page** : le rendu doit être vérifié à l'œil, en PDF imprimé au format carte et en PNG sur un téléphone.
  Une capture sera jointe à la relecture.
