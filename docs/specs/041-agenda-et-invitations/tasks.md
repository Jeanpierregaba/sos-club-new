# 041 — Tâches

Ordonnées. Chaque tâche est petite, testable et committable seule. Les parties critiques (droits, points, données
d'élèves, rien de public avant l'approbation) sont écrites en TDD : les tests précèdent le code.

## Socle

- [x] 1. Documents :
  - `TASKS.md` : spec 041 en cours, avec spec, plan et tâches validés ;
  - `docs/DESIGN.md` : les parcours « Agenda du club », « Mes événements » et la page d'un événement ;
  - `docs/SECURITY.md` : les réponses et la présence sont des données d'élèves, jamais publiques ;
  - `docs/PRD.md` : R16 traité par la spec 041.
- [ ] 2. Migration et modèles :
  - les tables `evenement` et `reponse_evenement`, avec leurs CHECK (niveau et club, fin après début, motif si
    annulé, places ≥ 1, lien `https://`) ;
  - la colonne `rapport.evenement_id` et son index unique partiel ;
  - le type `evenement` ajouté à `adresse_si_publie` et à `contenu_du_club` ;
  - le test d'aller-retour de la migration ;
  - la base de fuseaux vérifiée dans l'image Docker de l'API, sinon le repli UTC+0.
- [ ] 3. Moteur de modération, tests puis code :
  - `TypeContenu.domaine_droit` : décider d'un type qui le porte exige aussi « <domaine> : approuver »,
    le retirer « <domaine> : dépublier » ;
  - dans la file, un modérateur sans ce droit voit le contenu sans boutons ;
  - le crochet `a_chaque_approbation`, appelé à chaque version approuvée ;
  - les types existants ne changent pas (leurs tests restent verts).

## Événements de club

- [ ] 4. Tests puis code des droits et des brouillons (`agenda.service`, `types.py`, routes `clubs/moi/agenda`) :
  - un encadreur actif rattaché ou le président crée, modifie et soumet ;
  - un élève non président, un encadreur d'un autre club ou non vérifié, et un visiteur reçoivent 403 ;
  - seul l'auteur encore habilité modifie ;
  - les dates incohérentes, ou passées à la soumission, sont refusées (422) ;
  - un club suspendu ou fermé ne propose plus d'événement ;
  - les heures saisies à Lomé sont stockées en UTC et réaffichées à l'identique.
- [ ] 5. Tests puis code de l'approbation :
  - rien de public avant l'approbation ;
  - la première approbation recopie la version dans `evenement`, crédite +30 à l'encadreur auteur, rien au
    président, et notifie les membres actifs du club ;
  - une modification approuvée recopie sans recréditer ni réinviter ; un changement de date ou de lieu est
    notifié aux invités qui n'ont pas répondu « non » ;
  - le droit « agenda : approuver » est exigé, et l'auteur ne décide pas du sien.
- [ ] 6. Tests puis code de l'annulation :
  - par l'auteur, un encadreur du club, le président ou l'équipe ;
  - motif de 10 à 200 caractères ;
  - l'événement reste visible et marqué « Annulé », les invités sont notifiés ;
  - l'annulation est journalisée.

## Réponses, rappels et présences

- [ ] 7. Tests puis code des réponses :
  - seul un membre actif du club répond, et change d'avis jusqu'au début ;
  - après le début, la réponse est refusée (409) ;
  - au-delà des places, « Je participe » est refusé (409), y compris pour deux réponses simultanées sur la dernière
    place ;
  - un membre parti, suspendu ou supprimé n'est plus compté ;
  - « Mes événements » de l'élève.
- [ ] 8. Tests puis code de la liste des réponses et du pointage :
  - la liste n'est lue que par les encadreurs du club, le président et l'équipe, avec `no-store` ;
  - le pointage n'est possible qu'entre le début et 30 jours après, et seulement sur des membres du club ;
  - il ne rapporte aucun point.
- [ ] 9. Tests puis code de la commande `python -m app.agenda.rappels` :
  - la veille, à ceux qui participent, une seule fois même relancée ;
  - rien pour un événement annulé ;
  - un nouveau rappel après un report à une autre date ;
  - `deploy/README.md` : la ligne cron.

## Équipe, public et rapports

- [ ] 10. Tests puis code des événements nationaux et régionaux (`administration.py`, `router_admin.py`) :
  - les droits « agenda : créer » et « agenda : modifier » ;
  - le périmètre DRE ;
  - publiés à la création ;
  - journalisés.
- [ ] 11. Tests puis code des routes publiques :
  - les filtres par région, club, type, axe et période ;
  - les 3 prochains ;
  - la page d'un événement (404 s'il n'est pas publié) ;
  - le nombre de participants et « Complet » ;
  - aucun nom ni pseudonyme d'élève dans le JSON.
- [ ] 12. Tests puis code du lien entre un rapport et un événement :
  - un rapport se lie à un événement publié de son club ;
  - le lien est refusé si l'événement est déjà lié (y compris sous concurrence), d'un autre club ou non publié ;
  - l'aperçu du rapport montre le titre, la date et le nombre de présents.
- [ ] 13. Seed de démonstration (événements publiés, national, en attente, réponses), types de l'API régénérés et
      fonctions du client.

## Site

- [ ] 14. `/agenda` et `/agenda/$id` sur l'API :
  - les sections, les filtres dans l'URL, à venir puis passés, « Annulé » et « Complet » ;
  - la réponse d'un membre connecté ;
  - `AgendaSidebar` de l'accueil ;
  - tests Vitest.
- [ ] 15. Agenda du club (`mon-club.agenda.*`) :
  - la liste par état, le formulaire avec le visuel, la soumission et l'annulation ;
  - les réponses et le pointage ;
  - le lien depuis « Mon club » ;
  - tests Vitest.
- [ ] 16. « Mes événements » de l'élève, son lien dans l'espace élève, et le choix d'un événement dans le
      formulaire de rapport ; tests.
- [ ] 17. Admin :
  - `/admin/agenda` pour les événements nationaux et régionaux ;
  - les libellés du journal ;
  - l'aperçu d'un événement dans la file de modération ;
  - tests.

## Fin

- [ ] 18. Lint, typecheck, tests du site, suite API complète (lancée seule). Vérification au navigateur, à 375 px et
      en bureau, de ce parcours :
  - proposer, approuver ;
  - répondre, puis voir la réponse dans l'agenda public ;
  - annuler, pointer les présents.
- [ ] Vérifier tous les critères d'acceptation de `spec.md`.
- [ ] Relecture par le sous-agent `reviewer`.
