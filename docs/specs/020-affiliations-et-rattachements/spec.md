# 020 — Affiliations des élèves et rattachements des encadreurs

> **Remplacée en partie par la [spec 033](../033-activation-des-clubs/spec.md) (2026-11-10)** : l'affiliation d'un élève est confirmée par un encadreur de son établissement ou par l'équipe, plus par le président ; le rattachement d'un encadreur est automatique et unique.

<!-- R5. Corrigée le 2026-11-05 avec le porteur du projet : quatre décisions (voir « Décisions »). -->

## Objectif

Permettre à un élève de **rejoindre le club** de son établissement (affiliation) et à un encadreur de se
**rattacher à un ou plusieurs clubs** (rattachement). Chaque demande passe par le président du club, puis
par un collaborateur. Seule une affiliation validée fera compter les points d'un élève pour son club (Q7,
PRD § glossaire) ; l'affiliation elle-même ne rapporte aucun point.

Questions liées : Q16 (plusieurs clubs pour un encadreur, avec autorisation de l'admin), Q18 (qui valide
l'affiliation), Q19 (un encadreur rattaché confirme le président), Q20 (qui voit la liste des membres).

## Décisions (2026-11-05)

1. **Validation d'un rattachement** : le premier rattachement d'un encadreur est validé comme une
   affiliation (collaborateur de la DRE du club, sinon l'équipe nationale). Au-delà, la demande est marquée
   « club supplémentaire » et seule l'équipe nationale peut l'autoriser (Q16). Pas de saisie de code à
   chaque décision : les droits du module clubs exigent déjà la double authentification (spec 019, ADR-0008).
2. **Liste des membres** : visible du président, des membres affiliés, des encadreurs rattachés et des
   collaborateurs habilités de la DRE, par pseudonyme uniquement ; jamais publique (`docs/RULES.md`, Q20).
3. **Espace du président** : il gère les demandes et les membres dans `/mon-espace`, bloc « Mon club ».
   L'espace président complet reste pour R8.
4. **Rôles** : l'élève et l'encadreur demandent, le président confirme, le collaborateur valide. Pas
   d'invitation par le président. En plus, un encadreur rattaché confirme le président lors d'une passation
   (Q19, promis par la spec 019).

## Comportement attendu

### Affiliation d'un élève

1. Dans `/mon-espace`, un élève dont l'établissement a un club actif voit « Rejoindre le club ». Un clic
   crée une demande `en_attente_president`.
2. Le président voit la demande dans son bloc « Mon club », onglet Demandes. Il confirme (la demande passe
   `en_attente_validation`) ou refuse avec un motif (`refusee`).
3. Un collaborateur de la DRE de l'établissement (ou l'équipe nationale) la voit dans `/admin/clubs`, onglet
   Affiliations. Il valide (`active` : l'élève est membre) ou refuse avec un motif (`refusee`).
4. L'élève suit l'état de sa demande dans `/mon-espace` ; après un refus, il voit le motif et peut
   redemander.
5. Un membre peut se retirer lui-même ; le président peut retirer un membre avec un motif. L'adhésion passe
   `retiree` ; l'élève peut redemander plus tard.

**Le président est membre de droit** : l'activation du club crée son adhésion active (et une migration la
crée pour les clubs déjà actifs). Il ne peut ni se retirer, ni être retiré, tant qu'il préside.

### Rattachement d'un encadreur

1. Un encadreur actif (spec 018) voit, dans son espace, le club de son établissement s'il existe, et sur la
   fiche publique de n'importe quel club actif (`/clubs/$id`) un bouton « Demander mon rattachement ».
2. La demande passe par le président (confirmer ou refuser avec motif), puis par un collaborateur.
3. **Premier rattachement** : collaborateur de la DRE du club, sinon l'équipe nationale.
   **Club supplémentaire** (l'encadreur a déjà un rattachement actif au moment de la décision) : seule
   l'équipe nationale peut valider ; la file des DRE l'affiche en lecture seule avec la mention
   « Autorisation nationale requise ».
4. L'encadreur rattaché voit ses clubs dans son espace, avec la liste de leurs membres (lecture seule).
5. Il peut se retirer d'un club ; le président peut le retirer avec un motif (`retire`).

### Confirmation du président par un encadreur (Q19)

1. Quand un président propose un successeur (passation, spec 019), et que le club a au moins un encadreur
   rattaché, la passation attend d'abord la confirmation d'un de ces encadreurs (`en_attente_encadreur`).
2. L'encadreur la voit dans son espace : il confirme (elle passe `en_attente`, puis l'admin décide comme
   aujourd'hui) ou refuse avec un motif (`refusee`).
3. Sans encadreur rattaché, rien ne change : la passation va directement à l'admin.
4. Le successeur proposé doit être un **membre affilié** du club.

### Liste des membres

Pseudonyme, date d'adhésion et mention « Président ». Jamais le nom, la classe ni le contact. Visible du
président, des membres actifs, des encadreurs rattachés actifs et des collaborateurs habilités (module
clubs, périmètre DRE). Personne d'autre : 404.

### Côté admin

Dans `/admin/clubs`, deux nouveaux onglets, filtrés par DRE pour un collaborateur de DRE : « Affiliations »
et « Rattachements », avec les demandes `en_attente_validation`. Validation et refus en lot (cocher, un
bouton) : chaque demande est traitée à part, et le résultat dit lesquelles ont réussi et lesquelles ont
échoué (et pourquoi). Le tableau de bord admin compte les demandes en attente.

## Critères d'acceptation

- [ ] Étant donné un élève dont l'établissement a un club actif, quand il demande à le rejoindre, alors une
      demande `en_attente_president` est créée.
- [ ] Étant donné une demande `en_attente_president`, quand le président la confirme, alors elle passe
      `en_attente_validation` ; quand il la refuse avec un motif, alors elle est `refusee` avec ce motif.
- [ ] Étant donné une demande `en_attente_validation`, quand un collaborateur de la DRE la valide, alors
      l'élève est membre (`active`) ; quand il la refuse avec un motif, alors elle est `refusee`.
- [ ] Étant donné plusieurs demandes, dont une déjà traitée, quand le collaborateur les valide en lot, alors
      les autres sont validées et la réponse signale celle qui a échoué.
- [ ] Étant donné un club activé, alors son président a une adhésion active ; il ne peut ni se retirer ni
      être retiré.
- [ ] Étant donné un membre, quand il se retire ou que le président le retire avec un motif, alors son
      adhésion est `retiree` et il peut redemander.
- [ ] Étant donné un encadreur sans rattachement actif, quand sa demande est confirmée par le président,
      alors un collaborateur de la DRE du club peut la valider.
- [ ] Étant donné un encadreur déjà rattaché à un club, quand il demande un autre club, alors la demande est
      marquée « club supplémentaire » et seul un collaborateur national peut la valider (403 pour une DRE).
- [ ] Étant donné un club avec un encadreur rattaché, quand le président propose un successeur, alors la
      passation attend la confirmation de l'encadreur avant d'arriver à l'admin.
- [ ] Étant donné un club, alors la liste de ses membres est visible de ses membres, de son président, de
      ses encadreurs rattachés et des collaborateurs de sa DRE, et de personne d'autre (404).
- [ ] Étant donné un membre (ou un encadreur rattaché) qui change d'établissement, alors son adhésion (ou
      son rattachement au club de l'ancien établissement) prend fin et c'est journalisé.

## Cas limites et erreurs

- **Demande en double** (même élève, double clic ou deux onglets) : la base n'accepte qu'une adhésion non
  terminée par élève, tous clubs confondus ; la seconde reçoit 409.
- **Élève déjà membre** : 409. **Club non actif** ou **d'un autre établissement** : 409 / 403.
- **Refus sans motif** (président ou collaborateur) : 422.
- **Confirmation par un non-président**, **retrait par un non-président** : 403.
- **Collaborateur hors de la DRE** du club : 404 (le club n'existe pas pour lui, comme en spec 019).
- **Club supplémentaire validé par une DRE** : 403 « Autorisation nationale requise ».
- **Deux décisions simultanées** sur la même demande : verrou de version ; la seconde reçoit 409.
- **Président qui change d'établissement** : refusé tant qu'il préside (passation d'abord).
- **Club en attente ou refusé** : aucune demande possible (seul un club actif reçoit des membres ; un club
  actif ne change pas d'état dans le modèle de la spec 019).
- **Encadreur suspendu ou non actif** : ne peut ni demander, ni confirmer une passation.

## Hors périmètre

- **Notifications** (R6) : les espaces affichent des compteurs, pas de messages.
- **Espace du président complet** : tableau de bord, fiche, actualités (R8).
- **Réinitialisation du mot de passe d'un élève par un encadreur rattaché** (Q4) : spec à part, à planifier.
- **Cartes membres** (R15), **points du club** (R13).
- **Invitations par le président** : écartées (décision 4).
- **DRE principale d'un encadreur** (celle de son premier rattachement, Q16) : stockée plus tard si un
  écran en a besoin.

## Questions ouvertes

Aucune : les quatre décisions ci-dessus ont été prises le 2026-11-05.
