# 0011 — Activation automatique des clubs, calculée par l'API

- **Statut** : Accepté
- **Date** : 2026-11-10

## Contexte

Jusqu'ici (spec 019, note du 2026-11-05 de l'ADR-0003), un club naissait d'une demande de son président, un élève,
validée par l'équipe ; élèves et encadreurs s'y rattachaient ensuite par un circuit président puis équipe. Le cahier
des charges « Gestion, activation et suivi des Clubs Santé » (2026-11-10) fixe une autre règle : un club est actif dès
que **3 encadreurs et 21 élèves** affiliés au même établissement sont présents et éligibles, et il perd ce statut
après 15 jours sous le seuil. Le porteur du projet a choisi le « tout automatique » : plus de demande de création.

## Options envisagées

1. **Déclaration du président + seuil** : on garde la demande, le seuil ne fait qu'activer. Moins de changements,
   mais deux sources de vérité (la décision de l'équipe et le seuil) qui peuvent se contredire.
2. **Statut calculé à chaque lecture** à partir des effectifs, sans le stocker. Toujours juste, mais pas de date
   d'activation ni de délai de régularisation possibles sans mémoire, et des lectures coûteuses sur la carte.
3. **Statut stocké, recalculé par l'API à chaque événement** qui change les effectifs, sous verrou du club, avec un
   journal des transitions et une échéance datée.

## Décision

Option 3. Le club est une ligne par établissement, créée par le système à la première affiliation ; son statut
(`en_constitution`, `actif`, `en_regularisation`, `suspendu`) n'est écrit que par `clubs/activation.py:recalculer`,
appelé dans la transaction de chaque événement. Les lectures appliquent l'échéance elles-mêmes (statut effectif) ; une
commande quotidienne l'enregistre et envoie les rappels. L'existence du club sur le terrain est une information à
part (`declare_terrain`), posée par l'équipe, sans effet sur les droits.

## Conséquences

- Le club n'a toujours pas de compte : l'ADR-0003 reste valable sur ce point ; seule la naissance du club change.
- Un élève ou un encadreur n'est membre que d'un club (amende Q16). La confirmation d'un élève passe par un encadreur
  vérifié de son établissement, ou par l'équipe de la DRE (spec 033).
- Chaque nouveau lieu qui change un effectif doit appeler `recalculer` : c'est le prix de l'option 3. Les tests
  d'acceptation de la spec 033 couvrent chaque événement.
- Les seuils (3, 21, 15 jours) sont des constantes du code : les changer passe par une revue.
- Sans la commande quotidienne, l'affichage reste juste mais les rappels ne partent pas.
