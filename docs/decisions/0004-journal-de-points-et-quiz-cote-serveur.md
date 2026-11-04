# 0004 — Journal de points et quiz arbitré par le serveur

- **Statut** : Accepté (registre mis en place par la spec 017 ; la partie quiz reste à livrer avec R9)
- **Date** : 2026-11-02

## Contexte

Les points font les classements publics, donc la fierté des clubs. Ils doivent pouvoir être expliqués
ligne par ligne, annulés en cas de fraude, et jamais attribués deux fois (double clic, nouvel essai
après une coupure). Le quiz limite le temps à 5 secondes par question, ce qu'un navigateur seul ne peut
pas garantir.

## Options envisagées

- **Journal immuable, scores calculés** (retenu) : tout est traçable, une annulation est une ligne
  négative. Le calcul des classements devra rester rapide.
- **Colonne `score` mise à jour** : simple, mais sans historique, et une erreur ne se répare pas.
- **Quiz chronométré par le navigateur** : plus fluide, mais trivial à contourner.

## Décision

Tout gain passe par une seule fonction du domaine `points`, qui écrit dans `mouvement_points` avec une
clé d'idempotence unique (ex. `quiz:<quiz>:<eleve>`) ; un score est la somme de ces lignes. Pour le
quiz, le serveur envoie une question à la fois sans sa réponse, note l'heure d'envoi, compte 5 secondes
plus 2 secondes de tolérance réseau, et calcule seul le résultat.

## Conséquences

- La base garantit l'absence de doublon, même en cas de requêtes simultanées.
- Si les classements deviennent lents, on ajoutera une vue matérialisée, sans changer le journal.
- Le retrait d'un faux élève ajoute une ligne négative, le journal ne perd rien.
- Une coupure réseau pendant un quiz fait perdre la question en cours : les reprises restent libres.
- La tolérance et le plafond de commentaires vivent dans la configuration du domaine, pour être ajustés.
