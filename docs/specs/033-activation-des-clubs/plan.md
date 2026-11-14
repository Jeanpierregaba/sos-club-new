# 033 — Plan technique

Spec : [spec.md](spec.md). Décision structurante : [ADR-0011](../../decisions/0011-activation-automatique-des-clubs.md)
(à créer avec la tâche 1), qui amende l'ADR-0003 (le club naît de ses membres, plus d'une demande).

## Principe

Un seul point d'entrée calcule le statut d'un club : `clubs/activation.py:recalculer(db, club_id, cause, par)`. Chaque
événement qui change les effectifs l'appelle **dans sa propre transaction**, après sa modification. Le club est
verrouillé (`SELECT … FOR UPDATE`) pendant le recalcul : deux événements simultanés sur le même club s'exécutent l'un
après l'autre, et le second voit le résultat du premier. Le journal des statuts n'est écrit que si le statut change.

L'échéance de régularisation ne dépend d'aucune visite : une commande quotidienne la fait passer (`cron` du VPS), et
toute lecture calcule le **statut effectif** (« en régularisation » dont l'échéance est passée = « suspendu »). La
commande ne fait donc qu'écrire ce que les lectures affichent déjà, et envoyer les rappels.

## Modèle de données (une migration, après `15ac5cbf557f`)

**`dre.region`** : texte contraint (`maritime`, `plateaux`, `centrale`, `kara`, `savanes`), non nul. Rempli par la
migration à partir du code : Grand Lomé et Maritime → maritime ; Plateaux Est et Ouest → plateaux ; les trois autres
à l'identique. Les régions sont une liste fixe en code (`referentiel/regions.py` : code, nom, ordre), pas une table.

**`club`** :

- `etat` reçoit quatre valeurs : `en_constitution`, `actif`, `en_regularisation`, `suspendu`. Les anciennes
  `en_attente` et `refuse` restent permises pour l'historique (aucune nouvelle ligne ne les prend) ;
- `regularisation_jusquau` (horodatage, nul), avec la contrainte `(etat = 'en_regularisation') =
(regularisation_jusquau IS NOT NULL)` ;
- `rappels_envoyes` (petit entier, 0 par défaut) : les rappels J+7 et J+14 déjà partis, remis à 0 à chaque ouverture ;
- `declare_terrain` (booléen), `declare_note`, `declare_le`, `declare_par` ;
- `demandeur_id` devient nul (club créé par le système) ; `actif_le` garde la **première** activation ;
- l'index unique `uq_club_actif_par_etablissement` est remplacé par `uq_club_par_etablissement`, sur les états
  vivants (les quatre nouveaux). La création se fait par `INSERT … ON CONFLICT DO NOTHING` puis relecture.

**`club_statut`** (journal, jamais modifié) : `id`, `club_id`, `ancien` (nul à la création), `nouveau`, `cause`
(texte court : `affiliation_confirmee`, `desistement_confirme`, `echeance`, `migration`…), `nb_encadreurs`,
`nb_eleves`, `par` (nul pour le système), `cree_le`.

**Seuils** (validé le 2026-11-10, simplification du stress-test) : pas de table. `SEUIL_ENCADREURS = 3`,
`SEUIL_ELEVES = 21` et `DELAI_REGULARISATION = 15 jours` sont des constantes de `clubs/activation.py`, que l'admin
consulte (lecture seule). Les changer demande une modification du code et une revue.

**`signalement_desistement`** : `id`, `club_id`, `encadreur_id` (visé), `signale_par`, `motif`, `etat`
(`en_attente`, `confirme`, `rejete`), `decide_par`, `decide_le`, `motif_decision`, `version`. Index unique partiel :
un seul signalement en attente par (club, encadreur visé). Contrainte : `signale_par <> encadreur_id`.

**`adhesion`** : plus de passage par le président. Une nouvelle affiliation est créée directement à
`en_attente_validation` (« à confirmer »). Les lignes `en_attente_president` passent à `en_attente_validation`.

**`rattachement`** : un index unique partiel « un seul rattachement actif par encadreur » remplace la possibilité de
rattachements supplémentaires (décision 1). Les lignes en attente sont closes (`retire`, motif « Remplacé par
l'affiliation automatique (spec 033) »).

**Reprise des données (dans la migration, en SQL)** :

1. clubs `en_attente` → `en_constitution`, sauf si l'établissement a déjà un club actif : alors `refuse`, motif
   « Remplacé par le club de l'établissement » ;
2. chaque encadreur vérifié reçoit un rattachement actif au club de son établissement (club créé s'il manque) ; ses
   autres rattachements actifs sont clos ;
3. chaque élève sans affiliation en cours en reçoit une « à confirmer » au club de son établissement ;
4. chaque club est recalculé : `actif` si le seuil est atteint, sinon `en_constitution` (décision 3), une ligne
   `migration` au journal.

La descente remet le schéma précédent ; elle ramène `en_constitution` à `en_attente` et les deux nouveaux statuts à
`actif`, et ne recrée pas les rattachements clos (descente volontairement incomplète, commentée).

## API

### `clubs/activation.py` (nouveau)

- `club_de(db, etablissement_id) -> Club` : le club vivant de l'établissement, créé `en_constitution` s'il manque.
- `effectifs(db, club_id) -> (encadreurs, eleves)` : comptes **distincts** dont
  - élèves : adhésion `active` au club, `utilisateur.statut = actif` ;
  - encadreurs : rattachement `actif` au club, `encadreur.etat = actif`, `utilisateur.statut = actif` ;
  - signalement de désistement confirmé : le rattachement est déjà clos par la confirmation.
- `recalculer(db, club_id, cause, par=None)` : verrou, échéance d'abord (point 8 de la spec), puis transitions,
  journal et notifications (`notifications.service.notifier`, dans la même transaction). Renvoie le nouveau statut.
- `statut_effectif(club, maintenant)` et son équivalent SQL pour les lectures en lot.
- `EN_SERVICE = (actif, en_regularisation)` : les statuts où le club publie et gagne des points ;
  `VIVANTS` : les quatre nouveaux statuts.

### Appels de `recalculer` (dans les transactions existantes)

| Événement                                     | Fichier                                                                           |
| --------------------------------------------- | --------------------------------------------------------------------------------- |
| Inscription d'un élève (affiliation créée)    | `comptes/inscription.py`                                                          |
| Affiliation confirmée / refusée / retirée     | `clubs/affiliations.py` (nouveau), `clubs/membres_admin.py`, `clubs/adhesions.py` |
| Changement d'établissement (élève, encadreur) | `eleves/service.py`, `encadreurs/service.py` (ancien et nouveau club)             |
| Encadreur vérifié, refusé, remis en attente   | `encadreurs/verification.py`, `encadreurs/service.py`                             |
| Compte suspendu, réactivé, supprimé           | `admin/inscrits.py`, `comptes/service.py`                                         |
| Désistement confirmé                          | `clubs/desistements.py` (nouveau)                                                 |

### Commande quotidienne `python -m app.clubs.echeances`

Pour chaque club `en_regularisation` : échéance passée → `recalculer(cause="echeance")` ; sinon rappel J+7 ou J+14
s'il n'est pas déjà parti (`rappels_envoyes`). Idempotente : la relancer ne double rien. Ligne `cron` ajoutée dans
`deploy/README.md` (étape des sauvegardes), à 6 h.

### Routes

Site (encadreur vérifié affilié au club ; 404 pour tout autre, comme la liste des membres aujourd'hui) :

- `GET /api/clubs/mon-club-sante` : fiche (établissement, inspection, DRE, région), statut effectif, date d'activation,
  échéance, effectifs, seuils, encadreurs du club (prénom, nom, fonction), président, signalements en cours que
  l'encadreur a faits ;
- `GET /api/clubs/mon-club-sante/affiliations` : élèves à confirmer et confirmés (pseudonyme, classe, date) ;
- `POST /api/clubs/mon-club-sante/affiliations/{id}/confirmer` et `/refuser` (motif), `/retirer` (motif) ;
- `POST /api/clubs/mon-club-sante/desistements` (`encadreur_id`, `motif`) ;
- `POST /api/clubs/mon-club-sante/president` (`eleve_id`) : une proposition à l'équipe, réutilise `club_passation`
  (`propose_par` = l'encadreur, état `en_attente`) ; refusée si le club a déjà un président ou n'est pas en service.

Élève : `GET /api/clubs/moi` renvoie désormais son affiliation (état, motif) et le statut effectif du club de son
établissement.

Public : `GET /api/clubs/carte` : les trois chiffres et l'arbre région → DRE → inspection → établissements (nom,
localité, statut public du club : `reference`, `en_constitution`, `actif`, `suspendu` ; `en_regularisation` est
montré `actif`). Aucune donnée personnelle. Calcul en trois requêtes agrégées, sans double compte (une ligne par
établissement).

Admin (module `clubs`, `Lecteur` / `Decideur`, périmètre DRE de l'ADR-0008) :

- `GET /api/admin/clubs/suivi` (filtres statut, région, DRE, inspection, page) et `GET /api/admin/clubs/{id}/suivi`
  (membres pris en compte, journal, signalements) ;
- `GET /api/admin/clubs/desistements`, `POST …/{id}/confirmer`, `POST …/{id}/rejeter` (motif) ;
- `POST /api/admin/clubs/{id}/terrain` (`declare`, `note`) ;
- `GET /api/admin/clubs/seuils` : les trois constantes, en lecture ;
- la file « affiliations à valider » existante sert à la confirmation par l'équipe (décision 2) ; la validation de la
  proposition de président passe par la file des passations existante.

**Retirés** : `POST /api/clubs/demande`, `/demande/renvoyer`, l'activation et le refus de club par l'admin, la file
« clubs à valider », la demande d'adhésion par l'élève et sa confirmation par le président, la demande, la
confirmation et la file des rattachements, **le retrait d'un membre par le président** (validé le 2026-11-10 : avec
le seuil des 21, un élève pourrait faire basculer son club en régularisation ; le retrait est réservé aux encadreurs
du club et à l'équipe). Leurs tests sont supprimés ou réécrits.

### Gel d'un club suspendu

Les contrôles qui lisent aujourd'hui `etat == actif` passent par `EN_SERVICE` pour publier (espace du président,
`moderation/decisions.py`) et par `VIVANTS` pour exister (fiche publique, articles). `points.service.scores_des_clubs`
ne retient que `EN_SERVICE` ; les crédits de club eux-mêmes viendront avec R13, qui devra appliquer la même règle (noté
dans TASKS).

## Site

- `src/routes/carte-des-clubs.tsx` : lit `/api/clubs/carte` ; trois chiffres, état neutre sans données, filtres région,
  DRE, inspection et recherche ; badge de statut par établissement. Les chiffres en dur disparaissent.
- `src/routes/_connecte/mon-club-sante.tsx` (nouveau, encadreur) : fiche, statut avec échéance, effectifs par rapport
  aux seuils (barres), équipe d'encadrement avec « Signaler un désistement » (fenêtre, motif), élèves à confirmer et
  confirmés, proposition de président. Lien depuis `mon-espace` et le menu de l'encadreur ; remplace
  `MesClubsEncadreur`.
- `mon-espace` de l'élève : `AdhesionClub` / `BlocClub` montrent l'état de l'affiliation et le statut du club ; le
  formulaire « Ouvrir l'espace de mon club » et la demande d'adhésion disparaissent.
- `src/routes/_connecte/admin/clubs.tsx` : onglets « Suivi » (liste et fiche avec journal), « Désistements »,
  « Affiliations », « Passations », « Seuils ». L'onglet « Clubs à valider » disparaît.
- Formulaire DRE de l'admin : choix de la région.
- Types régénérés (`export_openapi`, `api:types`).

## Documents à mettre à jour

PRD (Q5, Q6, Q16, Q19, parcours du club, vocabulaire : « club en constitution », « régularisation »), ADR-0003
(renvoi vers l'ADR-0011), DESIGN (badges de statut), `deploy/README.md` (cron), specs 019 et 020 (bandeau « remplacé
en partie par la spec 033 »), `seed_dev` et `seed_preprod` (un club actif à 3 + 21, un en constitution, un en
régularisation).

## Risques

- **Migration de données sur la prod** : les clubs réels sont peu nombreux (inscriptions fermées) ; la migration est
  testée sur une copie de la base de préprod avant la fusion dans `main`.
- **Inscriptions de masse** : chaque inscription d'élève verrouille son club un court instant ; acceptable (une ligne,
  quelques millisecondes).
- **Cron absent** : sans lui, l'affichage reste juste (statut effectif) mais les rappels ne partent pas. Le suivi
  admin montre déjà « suspendu » pour une échéance passée ; aucun signal supplémentaire au tableau de bord.
