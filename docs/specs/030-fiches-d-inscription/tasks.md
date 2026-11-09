# 030 — Tâches

Ordre d'exécution. Chaque tâche : lint, typecheck, tests ciblés, puis commit. Les parties critiques (droits,
authentification, code de confirmation) commencent par leurs tests.

## E-mails

- [x] 1. `app/courriel/` : déplacer l'envoi depuis `app/admin/courriel.py`, `envoyer(..., html)` en
      `multipart/alternative`, gabarit `rendre()` (texte + HTML échappé), invitation des collaborateurs portée sur
      le gabarit, logo `public/logo-email.png`. Tests : les deux parties présentes, valeurs échappées, rien dans les
      journaux, invitation inchangée côté API.

## Données

- [x] 2. Migration : `fiche_eleve`, `fiche_eleve_axe`, `fiche_eleve_parcours`, `encadreur.discipline`, rôle
      `visiteur`, `utilisateur.email_confirme_le`, `visiteur`, `code_confirmation` ; module de droit
      `fiches_eleves`. Test : `alembic upgrade head` puis `downgrade -1` puis `upgrade` sur la base de test.

## Fiche élève

- [x] 3. Tests d'abord : inscription élève avec fiche (champs obligatoires, dates, axes 1 à 3 et actifs,
      téléphones normalisés, année scolaire posée par le serveur, transaction unique).
- [x] 4. Schéma `FicheEleveEntree` + service : inscription étendue ; `GET/PUT /eleves/moi/fiche` (fiche partielle
      d'un ancien élève, `complete_le`, verrou de version) ; `fiche_complete` dans `/eleves/moi`.
- [x] 5. Tests d'abord puis route `GET /admin/inscrits/{id}/fiche` : droit sensible, périmètre DRE, double
      authentification, journal ; refus pour élève, encadreur, visiteur, autre DRE ; aucun champ de la fiche dans
      les exports ni les routes publiques.

## Encadreur

- [x] 6. Téléphone requis à l'inscription, `discipline` (inscription, espace, modification, file de vérification),
      `region` et `ville` déduites dans l'espace. Tests.

## Visiteur

- [x] 7. Tests d'abord : inscription visiteur (compte non confirmé, code envoyé ou `code_de_test`, 503 en
      production sans SMTP, inscriptions fermées, limite par adresse, doublon d'e-mail).
- [x] 8. Domaine `app/visiteurs/` : inscription, code (Argon2, 15 min, 5 essais, renvoi 1/min et 5/h,
      réponse 204 neutre), confirmation qui ouvre la session, étape `confirmation` à la connexion, `GET
    /visiteurs/moi`.
- [x] 9. Droits de jeu : `peut_jouer` accepte le visiteur confirmé, `peut_certifier` protège la certification,
      lancement d'une place de certification refusé (403), aucune ligne de points, pas d'affiliation à un club.
      Tests.
- [x] 10. Purge horaire des visiteurs non confirmés de plus de 7 jours (`lifespan`) ; filtre « visiteur » dans
      les inscrits. Tests.

## Site

- [x] 11. Types de l'API régénérés ; `client.ts`. Formulaire élève en étapes avec la fiche, composants
      `ChoixAxes`, `ChoixReseaux`, `ChampTelephone` ; tests Vitest des étapes et de la validation.
- [x] 12. Espace élève : bannière et page « Ma fiche d'adhésion » ; espace encadreur : téléphone, discipline,
      région et ville ; formulaire encadreur mis à jour.
- [x] 13. Visiteur : formulaire, saisie du code (renvoi avec compte à rebours), étape `confirmation` sur
      `/connexion`, espace visiteur minimal, menus sans certification, textes au tutoiement.
- [x] 14. Admin : onglet « Fiche d'adhésion » sur la fiche d'un inscrit (si droit), filtre « Visiteurs » ;
      libellé du droit dans la grille des collaborateurs.

## Clôture

- [x] 15. Seed de développement : fiches des élèves de démonstration, un visiteur confirmé « [Test] ».
- [ ] 16. Documents : SECURITY.md, PRD (Q8, Q27), ROADMAP (R19), ARCHITECTURE (droits, `courriel`, tables),
      `deploy/README.md` (Brevo : domaine, SPF, DKIM, variables `SMTP_*`).
- [ ] 17. Vérification : lint, typecheck, tests du site, suite API complète (lancée seule), parcours visiteur et
      formulaire élève au navigateur à 375 px et en bureau ; relecture `reviewer` et corrections ; TASKS.md.
