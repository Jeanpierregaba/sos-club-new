# 0004 — Journal de points et quiz arbitré par le serveur

- **Statut** : Accepté (registre mis en place par la spec 017 ; quiz livrés par la spec 027)
- **Date** : 2026-11-02

## Contexte

Les points font les classements publics, donc la fierté des clubs. Ils doivent pouvoir être expliqués
ligne par ligne, annulés en cas de fraude, et jamais attribués deux fois (double clic, nouvel essai
après une coupure). Le quiz limite le temps par question (5 secondes au départ, 20 pour les jeux depuis le 2026-11-10), ce qu'un navigateur seul ne peut
pas garantir.

## Options envisagées

- **Journal immuable, scores calculés** (retenu) : tout est traçable, une annulation est une ligne
  négative. Le calcul des classements devra rester rapide.
- **Colonne `score` mise à jour** : simple, mais sans historique, et une erreur ne se répare pas.
- **Quiz chronométré par le navigateur** : plus fluide, mais trivial à contourner.

## Décision

Tout gain passe par une seule fonction du domaine `points`, qui écrit dans `mouvement_points` avec une
clé d'idempotence unique (ex. `quiz:<quiz>:<eleve>`) ; un score est la somme de ces lignes. Pour le
quiz, le serveur envoie une question à la fois sans sa réponse, note l'heure d'envoi, compte le temps du parcours
(jeux 20 s, certification 5 s) plus 2 secondes de tolérance réseau, et calcule seul le résultat.

## Conséquences

- La base garantit l'absence de doublon, même en cas de requêtes simultanées.
- Si les classements deviennent lents, on ajoutera une vue matérialisée, sans changer le journal.
- Le retrait d'un faux élève ajoute une ligne négative, le journal ne perd rien.
- Une coupure réseau pendant un quiz fait perdre la question en cours : les reprises restent libres.
- La tolérance et le plafond de commentaires vivent dans la configuration du domaine, pour être ajustés.

## Mise en œuvre (spec 027)

- **Envoi paresseux** : une question n'est « envoyée » (heure enregistrée) qu'au moment où elle part vers le
  joueur. Une coupure ne fait perdre que la question en cours ; recharger la page renvoie la même question avec
  son heure d'envoi d'origine. Une tentative sans activité pendant 10 minutes est close avec le score acquis.
- **Paramètres versionnés** (`parametres_quiz`) : nombre de questions, temps affiché, tolérance, seuil et
  plafond quotidien ; une tentative garde la version de son lancement.
- **Concurrence** : chaque réponse verrouille la tentative ; la clé `quiz:<quiz>:<élève>` du registre garantit
  un seul crédit, quelle que soit la tentative.
- **Exposition** : rien n'est envoyé d'avance : la question en cours ne porte jamais sa bonne réponse ni son
  explication ; les schémas de la banque sont réservés à l'espace admin.

## Amendement du 2026-11-10 : correction des quiz des jeux

À la demande du porteur du projet, un quiz du parcours **jeux** corrige le joueur :

- après chaque réponse, ou quand le temps d'une question est écoulé, l'API renvoie la correction de cette seule
  question, déjà tranchée (`correction` : juste ou non, choix du joueur, choix attendu) ;
- le résultat final récapitule les questions ratées, avec la réponse du joueur, la bonne et l'explication
  (`resultat.erreurs`).

La règle reste : **aucune réponse avant la décision du serveur**. Le site montre la correction pendant 1,2 s ;
le serveur ne démarre le chrono de la question suivante qu'après cette pause (`PAUSE_CORRECTION`). La
certification Génie Imhotep (spec 029) ne corrige rien : score seul à la fin.

Conséquence acceptée : un joueur qui rejoue un quiz connaît les réponses des questions qu'il a déjà vues. Le gain
de points d'un élève (première réussite) devient plus facile à obtenir si la réserve d'un quiz dépasse à peine le
nombre de questions tirées. Le porteur du projet l'a accepté le 2026-11-10 : la correction vaut pour tous les
joueurs, élèves compris, même sur un quiz qui leur rapporte encore des points.
