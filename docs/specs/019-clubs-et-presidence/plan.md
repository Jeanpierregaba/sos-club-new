# 019 — Plan technique

<!-- Le COMMENT. Validé par l'utilisateur avant de découper en tâches. -->

## Approche

Réutiliser le circuit de vérification éprouvé de la spec 018 (demandeur, file filtrable par périmètre DRE ou
national, droits `approuver` sensibles + double authentification, activation/re refus atomiques, refus avec
motif obligatoire et renvoi) plutôt que d'inventer un moteur neuf. Le club est une donnée **collective
rattachée à un établissement** : jamais de compte, aucun mot de passe, la gestion passe par le lien
`president_id` vers un compte `eleve`. Aucune ligne de points n'est écrite par cette spec.

## Fichiers touchés

**API, nouveau domaine `clubs/`**

- `backend/app/clubs/__init__.py`
- `backend/app/clubs/models.py` : `Club` (demande + cycle `en_attente|actif|refuse`), `ClubAxe` (jointure), `ClubPassation`
- `backend/app/clubs/schemas.py` : `DemandeClubEntree`, `DemandeClub`, `ClubResumeEleve`, `ClubPublic`, `ClubFiche`, `PassationEntree`, `Passation`
- `backend/app/clubs/service.py` : création de la demande (transaction unique), activation/refus, renvoi, passation (proposer, valider, refuser, annuler)
- `backend/app/clubs/router.py` : routes `/clubs` (élève) et `/clubs/public` (lecture) ; `router_admin` : `/admin/clubs` (file, décisions, passations)
- `backend/app/clubs/administration.py` : logique admin (file, compteurs, passations) — comme `encadreurs/verification.py`

**API, autres**

- `backend/app/eleves/schemas.py` + `service.py` + `router.py` : `EspaceEleve` gagne `club: ClubApercuEleve | None`
- `backend/app/admin/catalogue.py` : `("clubs", A)` et `("clubs", C)` en `SENSIBLES` ; `gestionnaire_clubs` gagne `("clubs", A)`
- `backend/app/admin/router.py` : compteur `clubs_a_valider` dans `/admin/moi` et 5 routes `/admin/clubs/*`
- `backend/app/admin/tableau_de_bord.py` : `clubs_actifs` (vrai décompte) et `clubs_a_valider` (périmètre, 2FA respectée)
- `backend/app/admin/dependances.py` : rien à ajouter (`exiger_permission` suffit)
- `backend/app/main.py` : inclusion des routeurs clubs
- `backend/app/seed_dev.py` : un club actif avec président (élève de démo) et une demande en attente
- `backend/openapi.json` régénéré ; `src/lib/api/schema.gen.ts` régénéré

**Migration**

- `backend/alembic/versions/<slug>_clubs.py` : tables `club`, `club_axe`, `club_passation` ; index partiels uniques (voir Données) ; aucune donnée à migrer

**Site**

- `src/components/clubs/DemandeClub.tsx` : formulaire (nom, description, ≤3 axes, encadreurs associés déclaratifs, case obligatoire)
- `src/components/clubs/CarteDemande.tsx` + `src/components/clubs/CartePassation.tsx` : blocs de l'espace élève (état, CTA)
- `src/components/clubs/FicheClub.tsx` : fiche publique minimale (partagée carte + page `/clubs/$id`)
- `src/routes/_connecte/mon-espace.tsx` : bloc « Club » (ouvrir la demande, voir l'état, proposer une passation si président)
- `src/routes/clubs.$id.tsx` : page publique `/clubs/<id>`
- `src/routes/carte-des-clubs.tsx` : clubs actifs branchés sur l'API ; libellé « Aucun club enregistré pour cet établissement » sinon
- `src/routes/_connecte/admin.tsx` : entrée « Clubs à valider » (droit `clubs:consulter`) + compteur
- `src/routes/_connecte/admin/index.tsx` : carte du tableau de bord (clubs actifs réels)
- `src/routes/_connecte/admin/clubs.tsx` : page file des clubs + onglet Passations
- `src/lib/api/client.ts` : appels `demanderClub`, `chargerMonClub`, `chargerClubsPublics`, `chargerFicheClub`, `admin*Club*`, `proposerPassation`, etc.

**Docs**

- `docs/ARCHITECTURE.md` : tables `club`, `club_axe`, `club_passation` ; module `clubs/` dans la liste
- `docs/decisions/0003-sessions-en-base-et-identifiant-eleve.md` : note du 2026-11-04 (spec 019) — le club n'a pas de
  compte ; un élève désigné président gère l'espace officiel avec son compte ; chaque encadreur a son propre espace
- `docs/decisions/0008-droits-des-collaborateurs-et-double-authentification.md` : `("clubs", C)` et `("clubs", A)` en sensibles
- `docs/SECURITY.md` : après audit de cette spec — ligne « https » inchangée ; ajouter « club » dans les données limitées
- `docs/specs/019-clubs-et-presidence/*` : cette demande

## Données

Nouvelles tables (non destructives) :

```text
club
  id                UUID PK (uuid7)
  etablissement_id  FK etablissement(id) ON DELETE RESTRICT      -- un club par établissement (index unique partiel)
  nom               VARCHAR(150) NOT NULL
  nom_normalise     VARCHAR(150) NOT NULL                        -- unicité par établissement (unique avec etablissement_id)
  description       VARCHAR(300) NULL
  demandeur_id      FK utilisateur(id) ON DELETE RESTRICT         -- qui a demandé
  president_id      FK utilisateur(id) ON DELETE RESTRICT NULL    -- le gestionnaire courant (NULL tant qu'en attente)
  encadreurs_associes  JSONB NOT NULL DEFAULT '[]'               -- [{nom, email?, telephone?}] borné (≤10), déclaratif
  etat              VARCHAR(10) NOT NULL DEFAULT 'en_attente'    -- en_attente | actif | refuse
  motif_refus       VARCHAR(500) NULL                            -- CHECK (etat='refuse') = (motif_refus IS NOT NULL)
  decide_le         timestamptz NULL
  decide_par        FK utilisateur(id) NULL
  demande_le        timestamptz NOT NULL DEFAULT now()
  actif_le          timestamptz NULL
  version           INTEGER NOT NULL DEFAULT 1                   -- verrou optimiste (Suivi)

club_axe                                                  -- ≤ 3 axes, vérifié à l'API ; jointure propre pour les FK
  club_id           FK club(id) ON DELETE CASCADE
  axe_code          FK axe(code) ON DELETE RESTRICT
  PRIMARY KEY (club_id, axe_code)

club_passation
  id                UUID PK (uuid7)
  club_id           FK club(id) ON DELETE CASCADE
  successeur_id     FK utilisateur(id) ON DELETE RESTRICT         -- l'élève du même établissement proposé
  propose_par       FK utilisateur(id) ON DELETE RESTRICT         -- le président sortant
  propose_le        timestamptz NOT NULL DEFAULT now()
  etat              VARCHAR(10) NOT NULL DEFAULT 'en_attente'    -- en_attente | validee | refusee
  motif_refus       VARCHAR(500) NULL
  decide_le         timestamptz NULL
  decide_par        FK utilisateur(id) NULL
  version           INTEGER NOT NULL DEFAULT 1
```

Contraintes :

- **`uq_club_actif_par_etablissement`** : index unique partiel sur `club(etablissement_id) WHERE etat = 'actif'` —
  la base refuse deux clubs actifs au même établissement.
- **`uq_club_passation_en_attente`** : index unique partiel sur `club_passation(club_id) WHERE etat = 'en_attente'`.
- `uq_club_etablissement_nom` : `(etablissement_id, nom_normalise)` unique.
- `club.version` en `Suivi` (`with_for_update` + `version` au corps des décisions, comme spec 018).
- `mouvement_points` : **inchangée** — aucune ligne de points de club n'est écrite ici. Le `club_id` prévu pour les
  points de club sera ajouté par la première spec qui en crédite (R6/R11/R12), pas maintenant.

## API / interfaces

Élève (`utilisateur_courant`, rôle `eleve`) :

- `POST /api/clubs/demande` `{nom, description?, axes: [code…≤3], encadreurs_associes: [{nom, email?, telephone?}…≤10], confirmation: true}`
  → 201 `DemandeClub`. Refus : 403 (inscriptions — non, pas ce réglage : la demande n'est pas une inscription) ; 409 (demande en attente existante / club actif au même établissement / déjà président) ; 422 (nom invalide ou trop long, axes > 3 ou inconnus, confirmation manquante, description trop longue).
- `GET /api/clubs/moi` → `{ demande?: {club, etat, decide_le?, motif_refus?}, club?: ClubApercuEleve, passation?: PassationApercu | null }`
- `POST /api/clubs/moi/passation` `{ pseudonyme, version (club) }` → 201. Refus : 422 (pseudonyme inexistant, soi-même, hors établissement, élève suspendu) ; 409 (demande en attente, déjà une passation en attente) ; 409 (version périmée).
- `POST /api/clubs/moi/passation/annuler` → le président sortant annule sa propre proposition avant décision. 409 sinon.
- `POST /api/clubs/demande/renvoyer` : un club refusé repasse en attente (motif précédent au journal). Seul le demandeur peut renvoyer.

Public :

- `GET /api/clubs` → liste des clubs actifs `{id, nom, etablissement: EtablissementRattache, axes: [code], actif_le}` (nom, IESG, DRE — jamais de membres).
- `GET /api/clubs/{id}` → fiche minimale `{id, nom, description?, etablissement, axes: [libelle...], actif_le}` ; 404 si non actif.
- `GET /api/clubs/par-etablissement?etablissement_id=` → le club actif de l'établissement, ou 204.

Admin (`exiger_permission`, double authentification pour les actions) :

- `GET /api/admin/clubs?etat=en_attente|refuse&page&par_page` : national ou DRE de l'établissement (comme spec 018),
  trie par ancienneté, plafonné à 50/page.
- `GET /api/admin/clubs/passations` : passations en attente, même périmètre.
- `POST /api/admin/clubs/{id}/activer` `{version}` : transaction unique — relit l'établissement (actif + périmètre),
  vérifie le demandeur actif, passe le club `actif`, pose `president_id`, `decide_*`, `actif_le`, journalise
  `club_active` (auteur, périmètre, version). **Deux activations simultanées** : l'index unique partiel tranche, la
  seconde lève 409. **Doublure même établissement** : l'activation refuse l'autre demande en attente
  (`refusée`, motif « Un club a été activé pour cet établissement. ») dans la même transaction ou en 409 — décision à
  la tâche ; préférence : refus automatique en 409 à l'activation si un club actif existe déjà, sinon doublure refusée
  dans une seconde transaction journalisée.
- `POST /api/admin/clubs/{id}/refuser` `{motif, version}` : 422 sans motif ; journal `club_refuse`.
- `POST /api/admin/clubs/passations/{id}/valider` `{version}` : transaction unique — relit club et successeur (même
  établissement, actif), passe `president_id`, journalise `club_passation` (avant/après), marque la passation
  `validee`. Version périmée → 409 comme spec 018.
- `POST /api/admin/clubs/passations/{id}/refuser` `{motif}` : le président sortant reste président ; journal `club_passation_refusee`.
- `GET /api/admin/clubs/passations/{id}` n'existe pas : la passation est rendue dans la file.

Compteur `/admin/moi` : `clubs_a_valider = count(demandes en attente du périmètre) + count(passations en attente du même périmètre)`,
uniquement si `clubs:consulter` **et** pas de double authentification requise.

## Dépendances

Aucune nouvelle bibliothèque. JSON pour `encadreurs_associes` : natif PostgreSQL/SQLAlchemy, déjà en usage.

## Sécurité

- Chaque route admin passe `exiger_permission` + **double authentification** (`("clubs", C)` et `("clubs", A)` en
  SENSIBLES) — comme `encadreurs`.
- Périmètre DRE lu **en base** sur l'établissement, au moment de la décision, sous verrou — comme spec 018.
- Le pseudonyme du demandeur est affiché au collaborateur autorisé ; aucun téléphone/e-mail d'élève n'est exposé
  publiquement ni au-delà du périmètre DRE ; les `encadreurs_associes` (tiers) ne sont visibles que des habilités
  (projet : libérer les données nominatives) — jamais côté public.
- Toute trace publique = fiche minimale (nom du club, établissement, axes) ; rien d'une demande en attente n'est
  public ; les journaux portent les décisions, pas les consultations (`SECURITY.md`, comme tranché le 2026-11-04).
- Club "en attente" : `GET /api/clubs/{id}` renvoie 404 — pas d'oracle.
- Journal : aucune donnée personnelle dans les détails (motif = texte libre, mêmes règles que spec 017/018).
- `SECURITY.md` : relecture au fil de la spec ; rien n'y ajoute une promesse non tenue.

## Tests

TDD sur les parties critiques :

1. **Concurrence** : deux `activer` simultanées → une seule réussit (test avec deux sessions, comme spec 018) ;
   deux demandes concurrentes pour le même établissement → la première activée bloque l'autre (auto-refus en 409 à l'activation).
2. **Passation** : proposer (pseudonyme inexistant / hors établissement / soi-même / suspendu → 422/409),
   valider (l'ancien président perd, le nouveau reçoit — vérifier côté session+droits), refuser (reste président),
   annuler, version périmée → 409.
3. **Périmètre & droits** : collaborateur DRE kara ne voit/ décide que les demandes de sa DRE (hors DRE → 404, comme 018) ;
   national voit tout ; sans le droit → 403/404 ; avec `clubs:approuver` sans 2FA → 403.
4. **Public** : fiche d'un club actif ; fiche d'un club en attente → 404 ; carte sans clubs → réponse vide (le site gère le libellé).
5. **Fonctionnels** : demande créée (état en_attente, rien de public, 0 points), limite (demande en attente existante → 409),
   renvoi après refus (`club_redemande`), casSuspension du président (activation bloquée), axes (>3 → 422, code inconnu → 422).
6. Site : tests Vitest des composants critiques (formulaire demande), et vérification navigateur sur téléphone en fin d'implémentation.

## Risques

- **Concurrence établissement ↔ club** : l'index partiel unique est nécessaire et suffisant ; toute logique applicative seule est
  exclue. Test dédié en TDD.
- **Passation acceptée puis président suspendu avant bascule** : re-lire `statut` de l'utilisateur successeur sous verrou dans la
  même transaction que la bascule ; refus 409 sinon.
- **Périmètre DRE d'un établissement proposé** : le club suit l'établissement ; si celui-ci est désactivé/remplacé, la validation
  est refusée (409) et l'admin est renvoyé vers le référentiel.
- **Encadreurs associés déclaratifs** : jamais traités comme des comptes (pas de connexion, pas de droits) ; un faux encadreur
  nommé dans une demande == donnée visible des habilités seulement, à clarifier si l'admin veut les contacter.
- **Doublon président/demandeur** : le même élève ne peut pas être demandeur de deux clubs ni président de deux clubs
  (409 au moment de l'activation, 422 à la demande) — vérifié par test.
- **Volume** : la carte agrège tous les clubs actifs — acceptable à l'échelle nationale (centaines) ; à mesurer, pas de pagination publique prévue dans cette spec.
