# 020 — Plan technique

<!-- Corrigé le 2026-11-05. Le code de l'API déjà écrit (non committé) est repris, corrigé et testé ;
voir la liste « Reprise du code existant ». -->

## Approche

Tout vit dans le domaine `clubs` : l'affiliation et le rattachement sont des liens vers un club, et leurs
règles s'appuient sur celles des clubs (périmètre DRE, verrous, journal). Deux tables à machine à états,
`adhesion` et `rattachement`, et une évolution de `club_passation` pour la confirmation par un encadreur
(Q19). Les décisions des collaborateurs passent par les mêmes gardes que la file des clubs de la spec 019
(`exiger_permission("clubs", approuver)`, double authentification, périmètre DRE lu sous verrou).

## Données

### `adhesion` (élève → club)

| Colonne                       | Type                        | Notes                                                                             |
| ----------------------------- | --------------------------- | --------------------------------------------------------------------------------- |
| `id`                          | UUID                        |                                                                                   |
| `eleve_id`                    | FK `utilisateur.id`         |                                                                                   |
| `club_id`                     | FK `club.id`, index         |                                                                                   |
| `etat`                        | texte contraint             | `en_attente_president`, `en_attente_validation`, `active`, `refusee`, `retiree`   |
| `demande_le`                  | timestamptz                 |                                                                                   |
| `confirme_le`, `confirme_par` | timestamptz, FK utilisateur | le président                                                                      |
| `decide_le`, `decide_par`     | timestamptz, FK utilisateur | le collaborateur (validation ou refus)                                            |
| `motif`                       | texte ≤ 500                 | obligatoire pour `refusee` ; facultatif pour `retiree` (retrait par le président) |
| `retire_le`, `retire_par`     | timestamptz, FK utilisateur |                                                                                   |
| `version`                     | entier                      | verrou optimiste (`Suivi`)                                                        |

- Index unique `uq_adhesion_en_cours_par_eleve` sur `eleve_id` où `etat IN (en_attente_president,
en_attente_validation, active)` : un élève n'a qu'une adhésion en cours, tous clubs confondus.
- Contrainte : `motif_refus` non nul si et seulement si `etat = 'refusee'`.
- Index partiel `(club_id, etat)` sur les états en attente, pour les files.

### `rattachement` (encadreur → club)

Même structure, avec `encadreur_id` (FK `encadreur.utilisateur_id`), des états au masculin (`actif`,
`refuse`, `retire`) et une colonne `supplementaire` (booléen) : vrai si l'encadreur avait déjà un
rattachement actif à la demande. Elle est **recalculée sous verrou au moment de la validation** (un premier
rattachement peut devenir supplémentaire entre-temps). Index unique sur `(encadreur_id, club_id)` pour les
états en cours (`en_attente_*`, `actif`).

### `club_passation`

- Nouvel état `en_attente_encadreur`, avant `en_attente`.
- Colonnes `confirmee_par` (FK utilisateur), `confirmee_le`.
- L'index « une seule passation en attente par club » couvre les deux états d'attente.

### Migration

Une migration (`add_adhesion_rattachement`, à réécrire : l'actuelle n'a pas été déployée) : les deux
tables, l'évolution de `club_passation`, et la **reprise des données** : une adhésion `active` pour le
président de chaque club actif.

## API

### Élève et président — `app/clubs/adhesions.py`, routes dans `router.py`

| Méthode  | Chemin                                      | Qui                                                      | Rôle                                 |
| -------- | ------------------------------------------- | -------------------------------------------------------- | ------------------------------------ |
| `POST`   | `/api/clubs/{id}/adhesions`                 | élève de l'établissement                                 | demander                             |
| `DELETE` | `/api/clubs/{id}/adhesions/moi`             | membre (pas le président)                                | se retirer, ou annuler sa demande    |
| `GET`    | `/api/clubs/{id}/adhesions/demandes`        | président                                                | demandes `en_attente_president`      |
| `POST`   | `/api/clubs/{id}/adhesions/{aid}/confirmer` | président                                                | confirmer                            |
| `POST`   | `/api/clubs/{id}/adhesions/{aid}/refuser`   | président                                                | refuser (motif)                      |
| `POST`   | `/api/clubs/{id}/adhesions/{aid}/retirer`   | président                                                | retirer un membre (motif facultatif) |
| `GET`    | `/api/clubs/{id}/membres`                   | membres, président, encadreurs rattachés, collaborateurs | liste (pseudonymes)                  |

L'espace élève (`GET /api/eleves/moi`, champ `club`) gagne l'état de l'adhésion de l'élève.

### Encadreur — `app/clubs/rattachements.py`

| Méthode  | Chemin                                                                  | Qui                | Rôle                                                |
| -------- | ----------------------------------------------------------------------- | ------------------ | --------------------------------------------------- |
| `POST`   | `/api/clubs/{id}/rattachements`                                         | encadreur actif    | demander                                            |
| `DELETE` | `/api/clubs/{id}/rattachements/moi`                                     | encadreur          | se retirer, ou annuler                              |
| `GET`    | `/api/clubs/{id}/rattachements/demandes`                                | président          | demandes à confirmer                                |
| `POST`   | `/api/clubs/{id}/rattachements/{rid}/confirmer` / `refuser` / `retirer` | président          |                                                     |
| `GET`    | `/api/encadreurs/moi/clubs`                                             | encadreur          | ses clubs, ses demandes, les passations à confirmer |
| `POST`   | `/api/clubs/{id}/passation/confirmer` / `refuser`                       | encadreur rattaché | Q19                                                 |

### Admin — `app/clubs/membres_admin.py`, routes dans `router_admin`

| Méthode | Chemin                                               | Rôle                                                            |
| ------- | ---------------------------------------------------- | --------------------------------------------------------------- |
| `GET`   | `/api/admin/clubs/affiliations`                      | file `en_attente_validation`, filtrée par DRE                   |
| `POST`  | `/api/admin/clubs/affiliations/valider` / `refuser`  | en lot : `[{id, version}]` (+ motif)                            |
| `GET`   | `/api/admin/clubs/rattachements`                     | file ; `supplementaire` affiché, décidable par le national seul |
| `POST`  | `/api/admin/clubs/rattachements/valider` / `refuser` | en lot                                                          |

Réponse d'un lot : `{ reussies: [...], echecs: [{ id, message }] }`. Chaque élément est traité dans son
propre point de sauvegarde (`begin_nested`) : un échec n'annule pas les autres. Les compteurs du tableau de
bord admin (`compter_en_attente`) intègrent les deux files.

### Règles transverses

- Changement d'établissement (`PATCH /api/eleves/moi`, `PATCH /api/encadreurs/moi`) : l'adhésion en cours
  et les rattachements au club de l'ancien établissement passent `retiree` / `retire`, journalisés ; refusé
  pour un président en exercice.
- Activation d'un club (spec 019) : crée l'adhésion active du président, dans la même transaction.
- Passation : le successeur doit être membre actif ; à la validation, il reste membre, l'ancien président
  aussi.
- Journal (`journaliser`) à chaque transition : `adhesion_*`, `rattachement_*`, `passation_confirmee`.

## Site

- **Élève** (`/mon-espace`, `BlocClub`) : « Rejoindre le club », état de la demande, motif d'un refus,
  « Me retirer », liste des membres une fois membre.
- **Président** (`/mon-espace`, `BlocClub`) : onglets Demandes (élèves et encadreurs, confirmer / refuser)
  et Membres (liste, retirer) ; état de la passation (« en attente de l'encadreur »).
- **Encadreur** (`/mon-espace`, `EspaceEncadreur`) : « Mes clubs » (rattachements, membres en lecture),
  demandes en cours, passations à confirmer ; bouton « Demander mon rattachement » sur `/clubs/$id`.
- **Admin** (`/admin/clubs`) : onglets Affiliations et Rattachements, cases à cocher, « Valider la
  sélection » / « Refuser la sélection » (motif), résultat par ligne.
- Types : `uv run python -m app.export_openapi` puis `npm run api:types`.

## Sécurité

- Chaque route vérifie le rôle **et** la ressource : président de _ce_ club, membre de _ce_ club, encadreur
  rattaché à _ce_ club, collaborateur dont la DRE couvre _ce_ club (ADR-0003).
- Liste des membres : pseudonyme seulement, 404 pour tout autre visiteur (`docs/RULES.md`).
- Décisions admin sous double authentification (droits `clubs` sensibles, spec 019).
- Messages d'erreur sans détail interne.

## Tests

- `tests/test_clubs_adhesions.py` : parcours complet, refus avec et sans motif, doublons concurrents,
  retraits, président membre de droit, liste des membres par profil (y compris 404), changement
  d'établissement. **TDD** pour la confirmation par le président.
- `tests/test_clubs_rattachements.py` : premier rattachement par la DRE, supplémentaire réservé au national
  (403 DRE), recalcul de `supplementaire` à la validation, retraits.
- `tests/test_clubs_passation_q19.py` : passation avec et sans encadreur rattaché, confirmation et refus.
- `tests/test_clubs_lots.py` : lot avec un élément périmé (409) et un hors périmètre, les autres passent.
- Site : `BlocClub` (élève, président), espace encadreur, file admin.

## Reprise du code existant

Le code écrit avant la correction de la spec (`adhesion_models.py`, `adhesion_schemas.py`,
`adhesion_service.py`, routes dans `router.py`, `club_du_perimetre` dans `verification.py`, migration) est
repris ainsi :

- Modèles déplacés dans `clubs/models.py`, aux noms et états ci-dessus ; `EtatRattachement.retire` ajouté
  (son absence faisait planter les retraits) ; index d'unicité corrigés.
- Service découpé en `adhesions.py`, `rattachements.py`, `membres_admin.py` ; noms sans accents.
- Lots : traitement élément par élément avec résultat détaillé, au lieu d'un échec global.
- `club_du_perimetre` conservé.
- Migration réécrite (jamais déployée ; en local : `alembic downgrade -1` avant de la remplacer).

## Risques

- **Changement de comportement de la passation** (spec 019) : un successeur doit désormais être membre, et
  un encadreur peut s'intercaler. Les tests de la spec 019 sont à adapter, pas à supprimer.
- **Migration de reprise** : à vérifier sur une copie de la base de préproduction avant le déploiement.
