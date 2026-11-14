# 0012 — Part du club à 50 % dans la ligne du gain, et année académique

- **Statut** : Accepté
- **Date** : 2026-11-11
- **Complète** : ADR-0004 (registre des points). **Remplace** le barème collectif de la spec 022.

## Contexte

Le cahier des charges « Espace Élève — Gamification et récompenses » (2026-11-10, spec 034) fixe une règle
transversale : pour chaque gain d'un élève, son Club Santé reçoit exactement la moitié du montant (+5 → +2,5), si
l'affiliation est active au moment du crédit. Le crédit du club est atomique avec celui de l'élève. Les
compteurs repartent de zéro à chaque année académique (septembre à juillet), sans rien effacer.

Jusqu'ici, le barème prévoyait des lignes `club.*` à montant fixe, jamais créditées : les clubs n'ont pas de
compte (ADR-0003) et R13 devait les brancher.

## Options envisagées

1. **Une seconde ligne pour le club** dans `mouvement_points`, avec un bénéficiaire club. Il faut une seconde
   clé d'idempotence, des montants entiers impossibles (2,5) et deux écritures à garder cohérentes.
2. **Un registre à part pour les clubs**. Même problème de cohérence, et une seconde porte d'écriture.
3. **La part du club dans la ligne du gain** : `club_id` et `demi_points_club` (la part en demi-points) sur la
   ligne de l'élève.

## Décision

Option 3. `points.service.crediter` reste la seule porte d'écriture. Pour une action d'élève, elle cherche
l'adhésion active de l'élève et vérifie que son club est en service (ADR-0011). Si c'est le cas, elle écrit le
club et sa part dans la même ligne. Une contrainte impose `demi_points_club = montant` : la part vaut toujours la
moitié, en demi-points entiers, sans arrondi. Le score d'un club est la somme de ses demi-points divisée par 2.
Une annulation copie le club avec la part négative, et l'année du gain annulé : le total de cette année baisse,
celui de l'année en cours ne bouge pas, et le classement d'une année clôturée reste figé.

Chaque ligne du barème porte son parcours (certification, jeux, vie du site) et, pour les Jeux, son sous-compte
(quiz ou étoiles) : les décomptes par parcours se lisent dans le registre.

L'année académique (lot 4 de la spec 034) est une période comme le semestre : chaque ligne porte l'année du
crédit ; un compteur annuel est une somme filtrée ; la clôture fige le classement régional dans un instantané.
Elle n'est possible qu'après la date de fin. Le crédit pose un verrou partagé sur l'année ouverte et la clôture un
verrou exclusif : aucun gain n'entre dans une année après sa clôture.

## Conséquences

- Le club crédité reste celui du jour du gain : un changement d'établissement ne transfère rien.
- Les lignes `club.*_eleve` du barème disparaissent (aucune n'avait été créditée). `club.rapport_activite` et
  `club.bilan_semestriel` restent, pour le référentiel du compte collectif.
- Un nouveau barème ne change jamais les lignes déjà écrites : le montant est copié à chaque gain.
