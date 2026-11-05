# 020 — Tâches

<!-- Spec et plan corrigés et validés le 2026-11-05 par le porteur du projet.
Chaque tâche est autonome et committable ; lint, typecheck et tests passent avant chaque commit. -->

## Tâche 1 — Données : modèles, migration, reprise

- [x] Modèles `Adhesion`, `Rattachement` dans `clubs/models.py` (états, contraintes, index du plan)
- [x] `club_passation` : état `en_attente_encadreur`, `confirmee_par`, `confirmee_le`
- [x] Migration réécrite, avec la reprise : adhésion active du président de chaque club actif
- [x] Tests des contraintes : une adhésion en cours par élève, motif obligatoire au refus
- [x] Supprimer `adhesion_models.py` ; retirer les routes non testées de `router.py` jusqu'aux tâches 2-4

**Commit :** `feat(clubs): tables adhesion et rattachement (spec 020)`

## Tâche 2 — API affiliations : élève et président

- [x] Tests d'abord pour la confirmation par le président (TDD)
- [x] `adhesions.py` : demander, annuler ou se retirer, confirmer, refuser, retirer
- [x] Président membre de droit : adhésion créée à l'activation du club (spec 019)
- [x] État de l'adhésion dans l'espace élève (`GET /api/eleves/moi`)
- [x] `tests/test_clubs_adhesions.py` (parcours, doublons, droits, retraits)

**Commit :** `feat(clubs): affiliations, demande et confirmation par le président`

## Tâche 3 — API rattachements : encadreur et président

- [x] `rattachements.py` : demander, annuler ou se retirer, confirmer, refuser, retirer
- [x] `supplementaire` calculé à la demande (le recalcul sous verrou à la validation est fait en tâche 4)
- [x] `GET /api/encadreurs/moi/clubs`
- [x] `tests/test_clubs_rattachements.py`

**Commit :** `feat(clubs): rattachements des encadreurs`

## Tâche 4 — API admin : files et décisions en lot

- [x] `membres_admin.py` : files filtrées par DRE, validation et refus en lot avec résultat par élément
- [x] Club supplémentaire : 403 pour un collaborateur de DRE ; `supplementaire` recalculé sous verrou à la validation
- [x] Compteurs du tableau de bord admin
- [x] `tests/test_clubs_lots.py`

**Commit :** `feat(admin): validation des affiliations et rattachements`

## Tâche 5 — API : membres et changements d'établissement

- [x] `GET /api/clubs/{id}/membres` (pseudonymes, 404 pour les autres)
- [x] Fin d'adhésion ou de rattachement au changement d'établissement ; refus pour un président
- [x] Tests par profil (membre, président, encadreur, DRE, autre DRE, visiteur)

**Commit :** `feat(clubs): liste des membres et changement d'établissement`

## Tâche 6 — API : confirmation du président par un encadreur (Q19)

- [x] Passation : `en_attente_encadreur` si le club a un encadreur rattaché ; successeur membre obligatoire
- [x] Routes confirmer / refuser pour l'encadreur rattaché
- [x] Adapter les tests de passation de la spec 019 ; `tests/test_clubs_passation_q19.py`

**Commit :** `feat(clubs): confirmation de la passation par un encadreur (Q19)`

## Tâche 7 — Site : élève et président dans /mon-espace

- [x] Régénérer le schéma OpenAPI et les types du site
- [x] `BlocClub` élève : rejoindre, état, motif, se retirer, membres
- [x] `BlocClub` président : onglets Demandes et Membres, état de la passation
- [x] Tests des composants

**Commit :** `feat(site): affiliation et gestion des membres dans mon-espace`

## Tâche 8 — Site : encadreur

- [x] `EspaceEncadreur` : mes clubs, demandes, passations à confirmer
- [x] Bouton « Demander mon rattachement » sur `/clubs/$id`
- [x] Tests des composants

**Commit :** `feat(site): rattachements dans l'espace encadreur`

## Tâche 9 — Site : admin

- [x] `/admin/clubs` : onglets Affiliations et Rattachements, sélection, décisions en lot, résultat par ligne
- [x] Mention « Autorisation nationale requise » pour un collaborateur de DRE
- [x] Tests

**Commit :** `feat(site): files admin des affiliations et rattachements`

## Tâche 10 — Clôture

- [ ] Vérification sur téléphone (viewport mobile) des trois espaces
- [ ] Relecture par le sous-agent `reviewer`, constats corrigés
- [ ] `ARCHITECTURE.md` (tables, routes), `SECURITY.md` (droits par ressource), note sur Q4 restant à faire
- [ ] `TASKS.md`, `docs/SESSION-LOG.md`

**Commit :** `docs: clôture de la spec 020`
