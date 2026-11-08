# 026 — Espace du président (R8)

## Objectif

Donner au président d'un club actif un espace pour animer son club (PRD : « Le président modifie la fiche du club
et publie des actualités en son nom, après validation ; les membres voient l'espace du club en lecture seule »,
CDC club et président § 2, 4, 5, 6 et 12). Tout ce qui devient public passe par la modération (`docs/RULES.md`) :
les modifications de la fiche et les actualités du club arrivent dans le centre de modération des specs 023 et
025, avec le même périmètre (national ou DRE du club).

Aujourd'hui, le président confirme déjà les demandes d'adhésion et de rattachement depuis « Mon espace » (spec
020). Cette spec lui donne une page dédiée, « Mon club », et ouvre cette page en lecture aux membres et aux
encadreurs rattachés.

## Comportement attendu

**Mon club (président)**

1. Depuis « Mon espace », le président ouvre « Mon club » (`/mon-club`). Il voit :
   - l'identité du club : nom, établissement, DRE, axes, date d'activation et lien vers la fiche publique ;
   - des indicateurs : membres actifs, encadreurs rattachés, actualités publiées, demandes en attente ;
   - les demandes à traiter (adhésions et rattachements, déplacées de « Mon espace ») ;
   - le suivi de ses demandes : modifications de la fiche et actualités, avec leur état et le motif d'un refus.
     Les points et rangs du club apparaîtront avec R13 : l'emplacement l'annonce sans chiffre inventé.

**Modifier la fiche**

2. Le président propose une nouvelle description (300 caractères au plus) et de nouveaux axes (1 à 3, parmi les
   7). La fiche publique ne change pas tant qu'un modérateur n'a pas approuvé.
3. Une seule proposition en attente à la fois : il peut la retirer pour en faire une autre.
4. Le modérateur voit l'avant et l'après, approuve (la fiche publique change aussitôt) ou refuse avec un motif.
   Le président reçoit une notification du résultat.

**Actualités du club**

5. Le président écrit une actualité au nom du club : titre, chapô, texte (le même Markdown restreint que les
   articles), axe et jusqu'à 5 photos avec l'attestation de chacune (spec 024). Il peut la garder en brouillon, la soumettre, la corriger, la retirer de la file, comme un
   article.
6. Une actualité approuvée se lit sur la fiche publique du club (les plus récentes d'abord) et dans
   `/articles`, marquée « Actualité du club ». Elle est signée du nom du club, jamais du nom de l'élève.
7. Une actualité ne rapporte aucun point : le barème n'en prévoit pas (spec 022).

**Vue des membres**

8. Un membre actif et un encadreur rattaché ouvrent `/mon-club` en lecture : identité, indicateurs, actualités
   publiées et liste des membres (pseudonymes, spec 020). Ils ne voient ni les demandes, ni le suivi, ni aucun
   bouton de gestion.

**Passation**

9. À la passation (spec 019), le nouveau président récupère les brouillons, propositions et actualités du club ;
   l'ancien perd tout accès de gestion aussitôt. Une actualité garde la signature du club.

## Critères d'acceptation

- [x] Étant donné le président d'un club actif, quand il ouvre `/api/clubs/moi/espace`, alors il reçoit
      l'identité, les indicateurs, les demandes en attente et le suivi de ses propositions.
- [x] Étant donné un membre actif ou un encadreur rattaché, alors il reçoit l'identité, les indicateurs, les
      actualités publiées et les membres, sans demandes ni suivi ; tout autre compte reçoit 404.
- [x] Étant donné un membre, un encadreur ou un ancien président, quand il tente une action de gestion (modifier
      la fiche, écrire, soumettre ou retirer une actualité, traiter une demande), alors l'API répond 403 ou 404 et
      rien ne change.
- [x] Étant donné une proposition de fiche en attente, alors la fiche publique reste l'ancienne ; une seconde
      proposition est refusée (409) tant que la première n'est pas décidée ou retirée.
- [x] Étant donné une proposition approuvée, alors la description et les axes de la fiche publique changent, et le
      président est notifié ; refusée, rien ne change et le motif est notifié.
- [x] Étant donné une description de plus de 300 caractères, aucun axe, plus de 3 axes ou un axe inconnu, alors
      l'API répond 422.
- [x] Étant donné une actualité en brouillon, en attente, à corriger, refusée ou dépubliée, alors elle n'apparaît
      ni sur la fiche publique, ni dans `/articles`, ni par son adresse.
- [x] Étant donné une actualité approuvée, alors elle apparaît sur la fiche du club et dans `/articles` avec la
      mention « Actualité du club », signée du nom du club, sans nom ni pseudonyme d'élève, et sans point crédité.
- [x] Étant donné une modification de fiche ou une actualité, alors elle arrive dans le centre de modération,
      visible d'un modérateur national ou de la DRE du club, jamais d'un autre ; le président ne décide jamais.
- [x] Étant donné une passation validée, alors le nouveau président voit et gère les actualités et propositions du
      club, et l'ancien reçoit 403 ou 404 sur chacune.
- [x] Étant donné un club non actif (en attente ou refusé), alors son président ne gère rien (403). La suspension d'un club
      n'existe pas encore (spec 019) : le jour où elle existera, l'approbation d'une actualité devra la vérifier.
- [x] Le site affiche « Mon club » pour le président (gestion) et pour les membres (lecture), l'écriture d'une
      actualité, la proposition de fiche et leur modération, lisibles sur téléphone.

## Cas limites et erreurs

- **Passation pendant une modération** : la décision s'applique ; la notification part au président actuel.
- **Proposition de fiche identique à la fiche actuelle** : refusée (422, « Rien n'a changé »).
- **Fiche modifiée par l'admin pendant l'attente** (spec 019) : à l'approbation, la proposition s'applique telle
  que le modérateur l'a lue ; le modérateur voit la fiche actuelle dans l'aperçu.
- **Deux modérateurs simultanés** : verrou et version du moteur, 409 pour le second.
- **Président qui quitte l'établissement ou dont l'adhésion est retirée** : il n'est plus président par
  passation seulement (spec 019) ; rien ne change ici.
- **Membre dont l'adhésion est retirée** : il perd la vue du club aussitôt (404).

## Hors périmètre

- Points, rangs et classements du club (R13).
- Photo ou logo du club.
- Rapports d'activité (R12), événements et invitations (R16), statistiques détaillées.
- Changement du nom ou de l'établissement du club : réservé à l'admin (spec 019).
- Commentaires sur les actualités.

## Questions ouvertes

Tranchées le 2026-11-08 :

1. Fiche : le président propose la description et les axes seulement ; nom, établissement et image restent à
   l'admin.
2. Les actualités ont des photos comme les articles (spec 024) : couverture et galerie, 5 photos de 8 Mo au plus,
   attestation pour chacune.
3. Une actualité publiée apparaît sur la fiche du club et dans `/articles`, marquée « Actualité du club ».
4. Le président seul écrit au nom du club ; les encadreurs rattachés lisent.
