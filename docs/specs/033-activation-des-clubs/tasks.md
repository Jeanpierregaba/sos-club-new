# 033 — Tâches

Ordonnées. Le moteur d'activation est critique (droits, données d'élèves, enregistrement d'un club,
`docs/TESTING.md`) : ses tests précèdent le code.

- [x] 1. ADR-0011 ; PRD (Q5, Q6, Q16, Q19, vocabulaire) ; bandeaux des specs 019 et 020 ; ADR-0003 renvoie à l'ADR-0011
- [x] 2. Migration : région des DRE, nouveaux statuts et colonnes du club, journal `club_statut`,
      `signalement_desistement`, index « un club par établissement » et « un rattachement actif par encadreur »,
      reprise des données ; aller-retour testé sur la base locale
- [x] 3. Tests du moteur (seuils 2+21, 3+20, 3+21, unicité, comptes suspendus, concurrence, régularisation,
      échéance, retour à actif, suspendu → actif), puis `clubs/activation.py`
- [x] 4. Brancher `recalculer` : inscription d'un élève, changement d'établissement, vérification d'un encadreur,
      suspension et réactivation de compte (la suppression d'un compte élève ou encadreur n'existe pas encore :
      elle devra appeler `recalculer_clubs_du_membre`) ; retirer la demande de club, l'adhésion par le président, les
      rattachements manuels et le retrait par le président
- [x] 5. Routes encadreur « Mon Club Santé » : fiche, affiliations à confirmer (404 hors établissement), retrait,
      signalement de désistement, proposition de président
- [x] 6. Routes admin : suivi des clubs, désistements (confirmer, rejeter), « déclaré sur le terrain », seuils ;
      confirmation des affiliations par l'équipe ; périmètre DRE
- [x] 7. Commande `python -m app.clubs.echeances` (échéance, rappels J+7 et J+14, idempotente) et ligne cron dans
      `deploy/README.md`
- [x] 8. Carte publique `/api/clubs/carte` : trois chiffres, arbre région → DRE → inspection → établissement, aucune
      donnée personnelle ; gel d'un club suspendu (`EN_SERVICE`)
- [x] 9. Site : carte, « Mon Club Santé », espace de l'élève, admin (suivi, désistements, seuils, région des DRE) ;
      types régénérés
- [x] 10. Seeds dev et préprod (club actif, en constitution, en régularisation)
- [x] Vérifier tous les critères d'acceptation de spec.md (couverts par les tests de l'API, dont `test_clubs_evenements.py`)
- [x] Relecture par le sous-agent reviewer (2026-11-10) : liste des membres hors « actif », établissement proposé
      remplacé, nouvelle demande d'affiliation, journal de création et cause de l'échéance, verrous ordonnés,
      décompte « à confirmer », périmètre au journal, état neutre de la carte, tests par route et de concurrence
