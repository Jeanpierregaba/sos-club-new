# 039 — Tâches

Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (droits, comptes, jetons)
sont écrites en TDD : les tests précèdent le code.

## Socle

- [x] 1. Documents : - `docs/PRD.md` (Q4 traité par la spec 039) ; - `docs/SECURITY.md` (réinitialisation par l'encadreur, lien par e-mail) ; - `docs/DESIGN.md` (parcours « Mot de passe oublié » et bandeau) ; - `TASKS.md` (spec 039 en cours, spec, plan et tâches validés).
- [x] 2. Migration et modèles : colonne `utilisateur.mot_de_passe_provisoire_le`, table `lien_mot_de_passe` (empreinte
      unique, expiration, usage, remplacement) ; aller-retour de la migration.

## Réinitialisation

- [x] 3. Tests puis code de `comptes.service.reinitialiser` : - provisoire de 12 caractères, sessions coupées, marqueur posé ; - journal sans mot de passe ; notification à l'élève (nom de l'encadreur, ou « l'équipe des Clubs Santé ») ; - `changer_mot_de_passe` efface le marqueur ; `Moi.mot_de_passe_provisoire`.
      La réinitialisation de l'admin (spec 017) passe par cette fonction ; ses tests existants restent verts.
- [x] 4. Tests puis code de la route de l'encadreur
      (`POST /api/clubs/mon-club-sante/affiliations/{id}/mot-de-passe`) : - membre confirmé : le provisoire ouvre une session, l'ancien mot de passe ne marche plus ; - affiliation en attente, retirée ou d'un autre club : 404 ; élève suspendu : refus ; - encadreur non vérifié, sans club ou club hors service : refus ; élève, visiteur ou président : refus ; - motif de 10 à 200 caractères ; - plafond de 10 sur 24 heures, 429, aussi sous requêtes simultanées ; - réponse en `no-store`.

## Lien par e-mail

- [x] 5. Tests puis code de la demande (`POST /api/comptes/mot-de-passe-oublie`) : - e-mail envoyé à un encadreur activé et à un visiteur confirmé ; - rien pour une adresse inconnue, un élève, un collaborateur, un compte suspendu, un encadreur en attente ou un
      visiteur non confirmé, avec la même réponse ; - adresse normalisée (majuscules, espaces) ; 3 liens par adresse et par heure ; limite par adresse IP ; - un nouveau lien remplace le précédent ; jeton stocké en empreinte seulement ; message `lien_mot_de_passe`.
- [x] 6. Tests puis code du choix (`GET` puis `POST /api/comptes/mot-de-passe-oublie/{jeton}`) : - lien valide : mot de passe changé, sessions coupées, marqueur effacé, adresse confirmée, journal ; - lien expiré, utilisé ou remplacé : 410 ; compte suspendu entre-temps : 410 ; - règles de longueur du mot de passe ; limite d'essais.

## Site

- [ ] 7. « Mon Club Santé » : bouton **Réinitialiser son mot de passe** sur chaque membre confirmé, dialogue avec le
      motif, affichage unique du provisoire avec copie et consigne ; tests du composant.
- [ ] 8. Bandeau de l'élève au mot de passe provisoire, ouvrant le changement de mot de passe ; tests.
- [ ] 9. Pages **Mot de passe oublié** (élève renvoyé vers son encadreur, formulaire pour les autres, message
      identique) et **Nouveau mot de passe** (lien valide, expiré, erreurs, `no-referrer`) ; lien depuis la
      connexion ; tests ; libellés du journal dans `src/lib/admin.ts`.

## Fin

- [ ] 10. Lint, typecheck, tests backend et site ; vérification dans le navigateur des pages publiques ;
      `TASKS.md`.
- [ ] Vérifier tous les critères d'acceptation de `spec.md`.
- [ ] Relecture finale par le sous-agent `reviewer`.
