# 047 — Mode maintenance du site — Tâches

- [x] 1. **Modèle et migration** : créer la table singleton `etat_site` (maintenance inactive par défaut) via migration Alembic ; ajouter le modèle SQLAlchemy et l’exporter ; vérifier `upgrade`/`downgrade`.
- [x] 2. **Service et garde backend** : service de lecture/écriture avec cache TTL + invalidation ; dépendance de garde (exemptions, contournement super-admin connecté/2FA, réponse 503 `raison: "maintenance"`), branchement sur le routeur `api` sans impacter `/health`.
- [x] 3. **API maintenance** : `GET /api/etat-site` (public, non bloqué), `GET /api/admin/maintenance` et `PUT /api/admin/maintenance` (super-admin, sensible/journalisé, idempotent) + schémas.
- [x] 4. **Tests backend (critiques)** : couverture activation/désactivation, journal, 503 + raison, exemptions connexion, contournement super-admin, refus collaborateur non super-admin, `/health`, état persistant.
- [x] 5. **Client API et types** : exporter OpenAPI, régénérer les types, ajouter appels client et gestion du signal `maintenance` (503 + `raison`).
- [x] 6. **Page maintenance frontend** : composant `PageMaintenance` (mascottes regroupées + texte fixe), et garde globale pour afficher la page quand la maintenance est active (sauf contournement super-admin).
- [x] 7. **Contrôle admin et bandeau** : interface super-admin pour activer/désactiver, bandeau visible « maintenance active » pour le super-admin connecté.
- [ ] 8. **Vérification finale** : lint, typecheck, tests ciblés puis pertinents, vérification manuelle du flux (activation, blocage, connexion super-admin, désactivation) ; mise à jour `TASKS.md`.
