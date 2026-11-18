# 042 — Plan technique

## Approche

On étend le référentiel (`backend/app/referentiel/`) et l'écran Référentiel > Établissements du back office. Aucun
nouveau domaine n'est créé.

- **Une fusion généralise le « Remplacer par… » actuel.** `remplacer_proposition` déplace déjà les élèves et les
  encadreurs (avec une version qui monte), désactive l'établissement et confie le club à `remplacer_etablissement`
  (spec 033). La nouvelle fonction `fusionner(garde, absorbe)` reprend ce chemin pour tout établissement actif,
  proposé ou inactif. Elle remplace l'ancienne : un seul code à tenir.
- **Les clubs se décident dans le domaine `clubs`.** `remplacer_etablissement` devient
  `fusionner_clubs(db, absorbe_id, garde_id, par, ip)` et applique le tableau de la spec :
  - un club **en constitution** est clos, et ses affiliations et rattachements en cours (actifs compris) passent au
    club restant ; c'est le code actuel ;
  - un club **au-delà** est rattaché au gardé par son `etablissement_id`. C'est le même club, avec le même
    identifiant : ses points, ses contenus et ses rapports le suivent sans rien recopier ;
  - si les deux clubs sont au-delà de « en constitution », la fusion lève `Refus(409)`.
  - Avantage : un club qui suit son établissement ne touche pas au journal des points, conformément à l'ADR-0004.
  - Alternative écartée : recopier les membres d'un club vers l'autre, ce qui casserait les points et l'historique.
- **Le renvoi vers le gardé** est une colonne `fusionne_dans_id` sur `etablissement`. La journalisation reste dans
  `journal_audit`, comme partout ailleurs.
- **Les doublons probables sont calculés à la demande** par un module pur, `referentiel/doublons.py`, qui reprend les
  règles de l'analyse. L'API lit les établissements actifs et proposés du périmètre (au plus environ 2 800), les
  regroupe par clé et compare les noms dans chaque groupe. Rien n'est stocké, sauf les paires écartées.
  - Alternative écartée : une table de suggestions remplie par une tâche planifiée. Elle se désynchronise à chaque
    fusion ou renommage, sans rien gagner sur un volume aussi faible.

## Fichiers touchés

### API, créés

- `backend/app/referentiel/doublons.py` :
  - les fonctions pures `cle_forte`, `corps`, `famille_sigle`, `cle_phonetique`, `distinctifs_differents` et
    `paires(etablissements) -> list[PaireProbable]` ;
  - la raison de chaque paire : `meme_nom`, `nom_proche` ou `meme_prononciation`.
- `backend/app/referentiel/fusion.py` :
  - `apercu(db, acces, garde_id, absorbe_id)`, qui renvoie les deux fiches, leurs clubs, l'effet prévu et le refus
    éventuel en clair ;
  - `fusionner(db, acces, garde_id, entree, ip)` ;
  - `lister_doublons`, `ecarter`, `retablir`.
- `backend/alembic/versions/<rev>_fusion_des_etablissements.py` : la colonne `fusionne_dans_id` et la table
  `ecart_doublon`.
- `backend/tests/test_referentiel_doublons.py` : la détection sur les vrais exemples de l'analyse, en tests
  paramétrés sans base.
- `backend/tests/test_referentiel_fusion.py` : la fusion, les clubs, les droits, la concurrence et les écarts.

### API, modifiés

- `referentiel/models.py` : `Etablissement.fusionne_dans_id` et le modèle `EcartDoublon`.
- `referentiel/schemas.py` :
  - `Remplacement` est retiré ;
  - ajout de `Fusion` (`absorbe_id`, `version_garde`, `version_absorbe`, `nom: "garde" | "absorbe"`), `ApercuFusion`,
    `ClubResume`, `PaireProbable`, `PageDoublons` et `Ecart` ;
  - `EtablissementAdmin` reçoit `fusionne_dans` (id et nom).
- `referentiel/administration.py` : `remplacer_proposition` est retiré, et `_etablissement_admin` remplit
  `fusionne_dans`.
- `referentiel/router.py` : les routes ci-dessous ; `/remplacer` est retiré.
- `clubs/affiliations.py` : `remplacer_etablissement` devient `fusionner_clubs`, selon le tableau de la spec.
- `tests/test_eleves_admin.py` et `tests/test_encadreurs_admin.py` : les tests du remplacement passent par
  `/fusionner`, avec le même résultat attendu.

### Site

- `src/routes/_connecte/admin/referentiel.etablissements.tsx` :
  - « Remplacer par… » (`RemplacerProposition`) est remplacé par l'action « Fusionner avec… », proposée sur toute
    ligne active ou proposée ;
  - la mention « Fusionné dans … » s'affiche sur un absorbé.
- `src/components/admin/FusionEtablissements.tsx` (nouveau) :
  - la boîte de dialogue de fusion : recherche de l'autre établissement, fiches côte à côte et inversion des rôles ;
  - le choix du nom, l'annonce de l'effet, puis la confirmation ;
  - un message clair en cas de refus (deux clubs, version dépassée, nom pris).
- `src/routes/_connecte/admin/referentiel.doublons.tsx` (nouveau) :
  - la page « Doublons probables », avec un filtre DRE, un filtre « Écartées » et le compteur par DRE ;
  - par paire : « Fusionner » (même boîte de dialogue) et « Pas un doublon » ou « Rétablir ».
- `src/routes/_connecte/admin/referentiel.tsx` : l'onglet « Doublons probables ».
- `src/lib/api/client.ts` : `adminApercuFusion`, `adminFusionnerEtablissements`, `adminDoublons`, `adminEcarterDoublon`
  et `adminRetablirDoublon` ; `adminRemplacerEtablissement` est retiré.
- `src/lib/admin.ts` : les libellés du journal `etablissement_fusionne`, `doublon_ecarte` et `doublon_retabli`. Les
  anciens libellés sont gardés pour l'historique.
- `src/components/admin/FusionEtablissements.test.tsx` : l'annonce de l'effet, l'inversion des rôles et l'affichage
  d'un refus.
- Types régénérés : `openapi.json` et `src/lib/api/schema.d.ts`.

### Docs

- `docs/specs/016-referentiel/spec.md` : un renvoi vers la spec 042 pour le remplacement des propositions.
- `docs/DESIGN.md` : une ligne sur la page « Doublons probables » dans le back office.
- `TASKS.md`.

## Données

La migration, non destructive, révise la tête actuelle :

- **`etablissement.fusionne_dans_id`** :
  - UUID, nullable, clé étrangère vers `etablissement.id` en `ON DELETE RESTRICT`, indexée ;
  - CHECK `fusionne_dans_id IS NULL OR statut = 'inactif'` ;
  - CHECK `fusionne_dans_id <> id`.
- **Table `ecart_doublon`** : les colonnes `etablissement_a_id` et `etablissement_b_id`, les deux en clé étrangère
  RESTRICT.
  - La clé primaire porte sur `(a, b)`, et un CHECK impose `a < b` : une paire n'a qu'une écriture.
  - Elle garde `ecarte_par` (le collaborateur) et `ecarte_le`.
  - « Rétablir » supprime la ligne. C'est une décision de tri, pas une donnée métier, et le journal garde
    l'écart comme son annulation.
- Le retour arrière supprime la table et la colonne. Il est refusé si une fusion a déjà eu lieu
  (`fusionne_dans_id` renseigné), car le renvoi serait perdu.

## API / interfaces

Toutes les routes ci-dessous sont sous `/api/admin/referentiel`, avec la permission `clubs` et une vérification du
périmètre DRE dans le service.

| Route                                                | Droit     | Rôle                                                                                           |
| ---------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------- |
| `GET /etablissements/doublons?dre=&ecartees=`        | consulter | Les paires, triées par DRE puis par IESG, et `par_dre` (le nombre de paires restantes par DRE) |
| `POST /etablissements/doublons/ecarter`              | modifier  | `{a_id, b_id}`, pour écarter une paire ; 409 si elle l'est déjà                                |
| `POST /etablissements/doublons/retablir`             | modifier  | `{a_id, b_id}`, pour la rétablir                                                               |
| `GET /etablissements/{garde_id}/fusion/{absorbe_id}` | consulter | `ApercuFusion` : les deux fiches, leurs clubs, l'effet prévu et `refus` (un texte, ou null)    |
| `POST /etablissements/{garde_id}/fusionner`          | modifier  | Corps `Fusion` ; renvoie le gardé (`EtablissementAdmin`)                                       |

**Déroulé de `fusionner`, dans une seule transaction :**

1. Verrouiller les deux établissements dans l'ordre de leur identifiant, pour éviter un interblocage. Vérifier :
   - les versions ;
   - le périmètre des deux ;
   - la même DRE ;
   - un gardé actif, et deux établissements différents.
2. Verrouiller leurs clubs vivants, puis appeler `fusionner_clubs`. Il lève le refus des deux clubs avant toute
   écriture.
3. Mettre à jour les élèves et les encadreurs (`etablissement_id` et `version + 1`), en gardant leurs identifiants
   pour le journal.
4. Mettre à jour le gardé : le nom et le `nom_normalise` choisis, puis la préfecture et l'ordre s'ils étaient vides.
   Un conflit sur `(iesg_id, nom_normalise)` donne 409 et nomme l'établissement qui porte déjà ce nom.
5. Mettre à jour l'absorbé : `statut = inactif`, `fusionne_dans_id = garde`.
6. Recalculer le club restant (`activation.recalculer`).
7. Écrire au journal `etablissement_fusionne` :
   - `cible` est l'absorbé, avec le périmètre DRE ;
   - `details` contient `avant` et `apres` pour les deux fiches, `eleves` et `encadreurs` (les identifiants déplacés)
     et `clubs` (l'action faite : `aucun`, `clos`, `rattache` ou `rattache_et_clos`, avec les identifiants).

`aperçu` passe par les mêmes vérifications, sans écrire. Ainsi, le site affiche le refus avant même qu'on clique.

## Dépendances

Aucune. La comparaison des noms utilise `difflib.SequenceMatcher`, de la bibliothèque standard.

## Sécurité

- **Droits (ADR-0003).** La permission `clubs` est vérifiée sur chaque route. Le périmètre DRE est vérifié pour
  **les deux** établissements, et la liste des doublons est filtrée sur la DRE du collaborateur.
- **Données personnelles.** Le journal garde les identifiants des élèves déplacés, jamais leurs noms. L'aperçu et la
  liste des doublons ne renvoient que des nombres : élèves, encadreurs, membres du club.
- **Intégrité.** Tout se fait dans une transaction, avec verrous et versions. Les contraintes de la base (CHECK et
  index unique du club vivant) arrêtent tout état incohérent, même en cas d'oubli dans le code.
- **RULES.** On ne supprime aucun établissement. Seule la ligne `ecart_doublon` se supprime : c'est une décision de
  tri, et le journal la garde.

## Tests

La fusion est une partie critique : elle déplace des comptes et des clubs. Les tests sont écrits avant le code.

- **`test_referentiel_doublons.py`**, sans base :
  - les paires de l'analyse sont trouvées : Tokoin I, Bogou 2 et II, Warkanbou et Warkambou, Kondokopé en trois
    fiches, Koudjoaré et Koundjoare sous deux IESG ;
  - les faux positifs ne le sont pas : Fabienne I, III et M, Souverain G/A et G/B, Bassar Est et Ouest,
    Daroul Hikmah I et IV ;
  - deux établissements de DRE différentes ne forment jamais une paire.
- **`test_referentiel_fusion.py`**, avec la base :
  - chaque ligne du tableau des clubs, et le refus 409 de deux clubs au-delà de « en constitution », sans aucun
    changement ;
  - le déplacement des élèves et des encadreurs, avec la version qui monte ;
  - le nom final, la préfecture et l'ordre, le renvoi et le statut inactif ;
  - le journal ;
  - les refus 422 (soi-même, une autre DRE, un gardé inactif), 403 (hors périmètre, sans le droit) et 409 (version
    dépassée, nom pris) ;
  - l'absorbé absent de la recherche d'inscription et de l'annuaire public ;
  - les doublons : le filtre par périmètre, écarter puis rétablir, une paire écartée absente, un absorbé absent ;
  - une proposition fusionnée donne le même résultat que l'ancien remplacement.
  - Le club rattaché garde son identifiant et la somme de ses points.
- **Site.** Vitest pour la boîte de dialogue, puis un parcours au navigateur à 375 px et sur bureau sur la base
  locale, avec une vraie paire de l'annuaire.
- **Mesure.** La durée de `GET /doublons` sur la base locale complète (2 780 établissements) doit rester sous
  une seconde. Au-delà, on écarte d'avance les paires que `quick_ratio` exclut déjà.

## Risques

- **Faux positifs et faux négatifs de la détection.** Ce n'est qu'une suggestion : rien ne fusionne sans
  confirmation, et « Pas un doublon » supprime le bruit une fois pour toutes. Les numéros, lettres et groupes qui
  distinguent deux établissements (I et III, G/A et G/B, une lettre isolée) excluent la paire. On l'a vérifié sur
  les faux positifs de l'analyse.
- **Club au-delà rattaché à une autre IESG.** Le club garde sa DRE, puisque la fusion entre deux DRE est refusée. Les
  classements par DRE ne bougent pas.
- **Nom du club.** Un club créé automatiquement s'appelle « Club Santé — <nom de l'établissement> ». Il garde son nom
  après un renommage du gardé. C'est le comportement actuel d'un renommage, que les gestionnaires peuvent corriger.
- **Fusion par erreur.** Il n'y a pas d'annulation. L'aperçu annonce l'effet, la confirmation est explicite, et le
  journal garde les identifiants déplacés pour une correction manuelle. On l'accepte, puisque les fusions sont rares
  et faites par l'équipe.
- **Rejeu en préprod puis en prod.** La migration n'ajoute qu'une colonne nullable et une table vide : sans risque sur
  les données existantes.
