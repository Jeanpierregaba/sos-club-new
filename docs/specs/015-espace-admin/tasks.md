# 015 — Tâches

<!-- Ordonnées. Chaque tâche est petite, testable et committable seule. Cochée dès qu'elle est faite et commitée. -->

**API**

- [x] 1. Dépendances (`pyotp`, `xlsxwriter`, `segno`, `cryptography`), réglages (`CLE_CHIFFREMENT`, SMTP,
      durées) et variables dans `.env.example` et `deploy/env.example`.
- [x] 2. Modèles et migration `espace_admin` : 8 tables, statut `revoque`, déclencheur du journal, reprise
      des admins existants. Test : aller-retour de la migration, déclencheur qui refuse `UPDATE` et
      `DELETE`.
- [x] 3. Catalogue des modules, des actions, des droits sensibles et des rôles préréglés ; `journaliser()` ;
      `creer_compte --role admin`, qui crée un super-administrateur.
- [x] 4. Tests des droits, écrits **avant** le code (sous-agent `test-writer`) : un test par rôle et par
      route, périmètre DRE, fin d'accès, suspension en cours de session, double authentification requise.
- [x] 5. `collaborateur_courant`, `exiger_permission`, refus journalisés, `couper_sessions` ; `GET
/admin/moi` et `GET /admin/catalogue`. Les tests de la tâche 4 passent.
- [x] 6. Tests de la double authentification, écrits **avant** le code : enrôlement, code juste ou faux,
      rejeu, codes de secours à usage unique, blocage après 5 erreurs, réinitialisation.
- [x] 7. Double authentification : enrôlement avec QR code en SVG, connexion en deux étapes (`POST
/comptes/connexion/code`).
- [x] 8. Envoi des e-mails (SMTP, ou lien dans le terminal hors production) et boîte factice pour les
      tests.
- [x] 9. Collaborateurs :
  - inviter, renvoyer, activer (`/activation/{jeton}`) ;
  - modifier les droits ;
  - suspendre, réactiver, révoquer ;
  - réinitialiser la double authentification, marquer comme revu ;
  - garde-fous (soi-même, dernier super-administrateur avec verrou).
- [x] 10. Annuaire des inscrits (liste, filtres, fiche avec historique), suspension et réactivation avec
      motif.
- [x] 11. Exports :
  - aperçu du volume ;
  - CSV et XLSX, agrégé et nominatif ;
  - colonnes en liste blanche, formules neutralisées ;
  - lien à usage unique de 15 minutes, historique ;
  - purge horaire et au démarrage.
- [x] 12. Journal (lecture filtrée) et tableau de bord (chiffres calculés, date de calcul). L'ancienne
      route `/admin/chiffres` est retirée.

**Site**

- [x] 13. Types régénérés et fonctions du client API ; seconde étape « code » de `/connexion`.
- [x] 14. Page `/activation` : identifiant, mot de passe, double authentification et codes de secours.
- [x] 15. Mise en page `/admin` (menu latéral avec les modules à venir, garde) et tableau de bord ;
      `/mon-espace` renvoie un admin vers `/admin`.
- [x] 16. Collaborateurs : liste avec filtres, invitation avec la grille des droits, fiche et actions avec
      motif.
- [x] 17. Inscrits : annuaire et fiche.
- [x] 18. Exports (dialogue d'aperçu, finalité, colonnes, historique) et journal.
- [x] 19. Page « Double authentification » (activer, régénérer les codes de secours).

**Fin**

- [ ] Vérifier tous les critères d'acceptation de spec.md
- [ ] Relecture par le sous-agent reviewer
