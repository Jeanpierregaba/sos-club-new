# 041 — Agenda et invitations

## Objectif

Remplacer l'agenda écrit en dur par un vrai agenda (R16, Q22, suites des specs 033 et 038) :

- les encadreurs et le président d'un club proposent les événements de leur club ; l'équipe nationale les approuve
  avant toute publication (`docs/cdc/encadreur.md` § 8, `docs/cdc/club-president.md` § 8, RULES) ;
- l'équipe publie elle-même les événements nationaux et régionaux ;
- l'agenda public `/agenda` et les rendez-vous de l'accueil lisent ces événements, filtrables par région, club,
  type et axe ;
- les membres du club sont invités, répondent, reçoivent un rappel la veille ; après l'événement, les présents
  sont pointés ;
- un rapport d'activité peut être lié à un événement de son club (suite de la spec 038).

Décisions de l'utilisateur (2026-11-17) :

- l'équipe crée les événements nationaux et régionaux, publiés directement ;
- les membres répondent « Je participe », « Peut-être » ou « Je ne peux pas », et l'encadreur ou le président
  pointe les présents après l'événement ;
- seuls les membres du club organisateur s'inscrivent ; le public voit l'événement sans s'inscrire ;
- un rappel la veille, à ceux qui participent.

## Comportement attendu

### Niveaux d'un événement

1. Chaque événement a un **niveau** : « national » (Secrétariat technique permanent), « régional » (Comité, une
   DRE) ou « club ». Ce sont les trois sections de l'agenda actuel.
2. Un événement porte : titre, type (formation, sensibilisation, concours, assainissement, campagne, émission,
   réunion, autre), axe (un des 7, facultatif pour le national), objectif, description, date, heure de début et de
   fin, lieu ou « en ligne » avec lien, public visé, nombre de places facultatif. Le visuel est reporté (voir « Hors périmètre »).
3. Les heures sont saisies et affichées à l'heure de Lomé (UTC+0, sans heure d'été), stockées en UTC.

### Événement d'un club

4. Un encadreur actif rattaché au club, ou le président du club, crée un événement : en **brouillon**, il le
   modifie librement, puis le **soumet**. Il ne choisit que son club.
5. L'événement soumis entre dans la file de modération commune (ADR-0009, type « événement ») : approuver,
   demander une correction, refuser (motif obligatoire). Décider demande le droit « agenda : approuver » du
   domaine existant « Agenda et campagnes » (rôle de départ « Gestionnaire de l'agenda »), retirer un événement
   « agenda : dépublier ». Rien n'est public avant l'approbation.
6. À la première approbation :
   - l'événement paraît dans l'agenda public ;
   - l'encadreur auteur reçoit **+30** (`encadreur.evenement`, réglable) ; le président, élève, ne reçoit rien
     (barème élève) ; un événement ne rapporte qu'une fois, même modifié et réapprouvé ;
   - chaque membre affilié du club (adhésion active) reçoit une **invitation** par notification interne.
7. L'auteur suit l'état de ses événements et reçoit chaque décision avec son motif ; les autres encadreurs du club
   et le président sont aussi notifiés.
8. Une modification d'un événement publié repasse en modération ; l'ancienne version reste affichée jusqu'à la
   décision (moteur commun). Un changement de date ou de lieu approuvé est notifié aux invités qui n'ont pas
   répondu « Je ne peux pas ».
9. L'auteur, un encadreur du club, le président ou l'équipe peut **annuler** un événement publié avec un motif :
   il reste dans l'agenda, marqué « Annulé », et les invités sont notifiés avec le motif. Le motif, écrit sans
   modération, n'est jamais public (relecture du 2026-11-17). Un événement annulé ne se réactive
   pas ; il se repropose.

### Événement national ou régional

10. Un collaborateur avec le droit « agenda : créer » crée un événement national, ou régional dans son
    périmètre (sa DRE) ; avec « agenda : modifier », il le modifie, le reporte ou l'annule. Il est publié sans passer par la file et sans points ;
    chaque action est journalisée.
11. Ces événements n'invitent personne : ils s'affichent dans l'agenda public.

### Invitations et réponses

12. Un membre invité voit ses invitations dans son espace (« Mes événements ») et dans l'agenda : il répond
    « Je participe », « Peut-être » ou « Je ne peux pas », et peut changer d'avis jusqu'au début de l'événement.
13. Un élève qui rejoint le club après la publication voit aussi l'événement dans « Mes événements » et peut y
    répondre, sans notification ; un membre qui quitte le club perd son
    invitation et sa réponse ne compte plus.
14. Si l'événement a un nombre de places, « Je participe » est refusé une fois les places prises (« Complet ») ;
    « Peut-être » reste possible.
15. Les encadreurs du club et le président voient la liste des réponses (pseudonyme, prénom et nom, réponse)
    et les totaux. Personne d'autre ne voit qui a répondu ; l'agenda public n'affiche que le nombre de
    participants.
16. **Rappel** : la veille de l'événement, une notification part à ceux qui ont répondu « Je participe ». Une
    tâche quotidienne l'envoie, au plus une fois par événement.

### Après l'événement

17. Une fois l'événement commencé, un encadreur du club ou le président pointe les **présents** parmi les
    membres du club (qu'ils aient répondu ou non). Le pointage ne rapporte aucun point ; il se corrige jusqu'à
    30 jours après l'événement.
18. Un rapport d'activité (spec 038) peut être **lié** à un événement publié de son club, passé ou en cours, que
    nul autre rapport n'a déjà lié ; le rapport affiche alors le titre, la date et le nombre de présents. Un
    événement lié une fois ne peut l'être de nouveau (pas de double crédit), sauf si ce rapport est refusé : il libère
    alors l'événement. Le lien est revérifié à la soumission du rapport.

### Agenda public

19. `/agenda` liste les événements publiés à venir, puis les passés, avec leurs trois sections. Filtres : région
    (DRE), club, type, axe. Chaque événement a sa page (`/agenda/<id>`), avec le nom du club et de
    l'établissement, jamais le nom d'un élève.
20. L'accueil affiche les trois prochains événements publiés ; s'il n'y en a aucun, le bloc l'indique.
21. Un visiteur ou un élève d'un autre club voit l'événement sans bouton de réponse ; un membre connecté du club y
    répond.

## Critères d'acceptation

- [ ] Un encadreur actif rattaché au club, ou son président, crée un brouillon et le soumet ; un élève qui n'est
      pas président, un encadreur d'un autre club ou non vérifié, ou un visiteur reçoit 403.
- [ ] Un événement en brouillon, en attente, à corriger ou refusé n'apparaît dans aucune route publique.
- [ ] La première approbation publie l'événement, crédite +30 à l'encadreur auteur (rien au président) et invite
      chaque membre affilié du club ; une seconde approbation après modification ne crédite rien ni ne réinvite.
- [ ] Sans « agenda : approuver », on ne décide pas d'un événement ; un auteur ne modère pas le sien ; refus et
      correction exigent un motif.
- [ ] Un collaborateur sans « agenda : créer » ou « agenda : modifier », ou hors de sa DRE pour un événement régional, ne crée ni ne
      modifie un événement national ou régional ; une création autorisée est publiée aussitôt et journalisée.
- [ ] Un membre invité répond et change sa réponse jusqu'au début ; après le début, la réponse est refusée.
- [ ] Un non-membre (autre club, visiteur, encadreur) ne peut pas répondre (403).
- [ ] Avec des places, « Je participe » au-delà de la capacité est refusé (409), y compris sous réponses
      simultanées.
- [ ] La liste nominative des réponses n'est lisible que par les encadreurs du club, le président et l'équipe
      habilitée ; l'agenda public n'expose que le nombre de participants.
- [ ] L'annulation exige un motif, garde l'événement marqué « Annulé » et notifie les invités.
- [ ] La tâche quotidienne envoie un rappel la veille à ceux qui participent, une seule fois même relancée.
- [ ] Le pointage des présents n'est possible qu'après le début, par un encadreur du club ou le président, et
      seulement sur des membres du club.
- [ ] Un rapport se lie à un événement publié de son club ; lier un événement déjà lié, d'un autre club ou non
      publié est refusé.
- [ ] `/agenda` filtre par région, club, type et axe, et ne contient aucun nom d'élève.
- [ ] Les heures saisies à Lomé sont stockées en UTC et réaffichées à l'identique.

## Cas limites et erreurs

- **Dates** : fin avant début, ou événement de club soumis dans le passé → refusé (422). Un événement publié
  dont la date est passée reste dans les « passés ».
- **Club suspendu ou fermé** : on n'y propose plus d'événement ; ses événements publiés à venir restent visibles,
  l'équipe les annule si besoin. Le président d'un club suspendu ne gère plus son agenda ; ses encadreurs, oui.
- **Approbation tardive** : un événement dont le début est passé, ou annulé entre-temps, ne s'approuve pas (409).
- **Auteur parti** : un encadreur dont le rattachement est retiré, ou un président remplacé, ne modifie plus
  l'événement ni n'y accède. Seul l'auteur modifie un événement ; les autres encadreurs du club et le président en
  place l'annulent, gèrent les réponses et pointent les présents, et reproposent l'événement si une modification
  est nécessaire. Les points déjà crédités restent.
- **Compte supprimé ou suspendu** : sa réponse ne compte plus dans les totaux.
- **Concurrence** : deux réponses simultanées sur la dernière place n'en acceptent qu'une.
- **Lien « en ligne »** : seulement `https://`, affiché comme lien sortant `rel="noopener noreferrer"`.
- **Textes** : titres et descriptions en texte brut, jamais interprétés comme du HTML.
- **Rappels** : un événement annulé ou reporté après l'envoi n'envoie pas de second rappel à la même date.

## Hors périmètre

- Le visuel d'un événement (photos du moteur, spec 024) : reporté à une suite de la spec 041.
- La lecture de la liste nominative des réponses depuis l'admin : seuls les gestionnaires du club la lisent.
- L'export iCal ou Google Agenda, et les rappels par e-mail ou SMS.
- L'inscription des élèves d'autres clubs ou des visiteurs, et les listes d'attente.
- La co-organisation par plusieurs clubs.
- Les campagnes ciblées par profil et DRE (R21) ; les affiches à télécharger.
- Les points de présence ou de mobilisation (« Mobilisation vérifiée de 10 participants », +50) : ils viennent
  du rapport approuvé, pas du pointage.
- Les préférences de notification par type : elles n'existent pas encore ; le rappel reste une notification
  interne, sans e-mail.
- Les archives de l'agenda par année académique (suites de la spec 033).

## Questions ouvertes

Aucune : les quatre questions ont été tranchées le 2026-11-17.
