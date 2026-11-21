# 047 — Mode maintenance du site — Plan technique

Validé sur le principe le 2026-11-21 (contournement super-admin uniquement, message fixe, blocage total, photos publiques bloquées). Détail d’implémentation ci-dessous.

## Approche

- **Source de vérité en base** pour que l’état survive aux redémarrages et soit partagé entre processus : une table singleton `etat_site` (une ligne, identifiant fixe) avec `maintenance_active` (bool), `active_le` (timestamptz, nullable), `active_par_id` (FK utilisateur, nullable). Migration Alembic non destructive (création + ligne initiale inactive).
- **Cache en mémoire (par processus)** de l’état, avec TTL court (ex. 5 s) et invalidation immédiate lors d’une activation/désactivation locale, pour éviter une lecture DB à chaque requête tout en propageant l’état rapidement entre workers.
- **Application backend** via une dépendance globale ajoutée au routeur `api` (`app/main.py`) : avant de traiter une requête, si maintenance inactive → passer ; si active → autoriser uniquement les exemptions ou un **super-administrateur connecté** (session résolue, collaborateur `super_admin`, 2FA effective). Sinon répondre `503` JSON `{"detail": "Le site est en maintenance. Réessaie plus tard.", "raison": "maintenance"}`.
  - Exemptions de chemin (sans contournement utilisateur requis, pour permettre la connexion d’un super-admin) : `POST /api/comptes/connexion`, `POST /api/comptes/connexion/code`, `POST /api/comptes/deconnexion`, `GET /api/comptes/moi`.
  - Les routes `/api/admin/*` ne passent que pour un super-admin authentifié avec 2FA effective (y compris lecture/écriture de l’état de maintenance). Les autres collaborateurs (y compris admin non super-admin) reçoivent 503 pendant la maintenance.
  - `/health` est hors du préfixe `/api` → non impacté.
- **Frontend** : exposer l’état maintenance au client (endpoint public léger, ex. `GET /api/etat-site` retournant `{ maintenance: bool }` sans donnée sensible, ou champ dans une réponse existante — de préférence endpoint dédié non bloqué) et/ou réagir au code `raison: "maintenance"` (503) dans `src/lib/api/client.ts`. Une garde globale (root `beforeLoad` ou composant englobant) affiche une `PageMaintenance` (mascottes `mascottes-equipe.webp` + texte fixe) pour tout le monde sauf les super-admins connectés autorisés à contourner. Côté admin, un bandeau « Maintenance active » visible pour le super-admin avec action de désactivation.
- **Audit** : journaliser `maintenance_activee` et `maintenance_desactivee` (acteur = super-admin).

## Fichiers touchés (prévision)

- **Backend**
  - `backend/alembic/versions/<rev>_mode_maintenance.py` — création `etat_site`.
  - `backend/app/maintenance/models.py` (ou `app/site/models.py`) — modèle `EtatSite`.
  - `backend/app/maintenance/service.py` — lecture/écriture, cache TTL, invalidation.
  - `backend/app/maintenance/dependances.py` — dépendance de garde (exemptions, résolution super-admin).
  - `backend/app/maintenance/router.py` — `GET /api/etat-site` (public, non bloqué) et `GET/PUT /api/admin/maintenance` (super-admin).
  - `backend/app/maintenance/schemas.py` — schémas entrée/sortie.
  - `backend/app/main.py` — enregistrement routeurs, ajout de la dépendance de garde au routeur `api`.
  - `backend/app/db.py` / `backend/app/models` imports si nécessaire pour enregistrer le modèle.
- **Frontend**
  - `src/components/PageMaintenance.tsx` — page maintenance (image `@/assets/mascottes-equipe.webp`, texte « La plateforme est actuellement en maintenance et sera de nouveau disponible. »).
  - `src/components/admin/BandeauMaintenance.tsx` (ou intégré) — bandeau + bouton désactiver pour super-admin.
  - `src/lib/api/client.ts` — appels état maintenance / bascule, et détection `raison === "maintenance"` sur 503 pour propager une erreur typée.
  - `src/routes/__root.tsx` (et/ou layout admin) — garde/affichage maintenance et bandeau.
  - `src/routes/_connecte/admin.tsx` ou page dédiée — contrôle d’activation/désactivation (section super-admin).
  - Types API générés (`npm run api:types`) et OpenAPI export.
- **Tests**
  - `backend/tests/test_maintenance.py` — activation/désactivation, journal, idempotence, blocage 503, exemptions, contournement super-admin, non contournement collaborateur, persistance logique, `/health` intact.
  - Tests frontend ciblés si pertinent (affichage page/bandeau selon état).

## Décisions / points d’attention

- La résolution « est super-admin » pendant la maintenance doit réutiliser la logique de session/collaborateur existante sans fuite d’accès (ne pas accorder de contournement partiel) et rester robuste si la DB est momentanément indisponible (→ 503 maintenance ou erreur contrôlée, sans ouvrir le site).
- Le cache mémoire est un optimisme de performance : la désactivation doit invalider immédiatement le cache du processus qui traite la requête ; les autres workers convergent au plus tard au TTL.
- `/api/comptes/moi` est exempté pour permettre au client de connaître la session/super-admin ; si maintenance active et utilisateur non super-admin, la réponse doit être cohérente avec le blocage (à trancher finement à l’implémentation : soit `503 maintenance`, soit réponse indiquant maintenance — le garde backend/frontend doit s’appuyer sur le même signal).

Aucune dépendance externe nouvelle prévue. Aucune décision structurante nécessitant un ADR au-delà de la spec.
