# 031 — Quiz santé jouables sans compte, correction et récapitulatif des erreurs

> Spec rédigée après coup (2026-11-17). La fonctionnalité a été livrée en urgence le 2026-11-09 (commit `5df41d5`),
> puis complétée le 2026-11-10 (`5fec65a`, `cf20a90`). Ce document décrit ce qui est en place aujourd'hui,
> y compris les changements apportés ensuite par la spec 034.

## Objectif

Faire jouer tout le monde aux quiz santé depuis la page des jeux, sans obliger à créer un compte d'abord :

- les 922 QCM du document officiel « Jeu Quiz Santé » (AIMES-AFRIQUE, Clubs Santé SOS Docteur TV) sont chargés
  dans la banque de quiz ;
- un joueur sans compte joue **3 quiz** à l'essai, puis est invité à créer son compte gratuit ;
- les quiz des jeux **corrigent** le joueur : chaque réponse est montrée juste ou fausse, et la fin de partie
  récapitule les erreurs.

Décisions du porteur du projet : essai de 2 quiz le 2026-11-09, porté à 3 le 2026-11-10 ; correction en vert ou en
rouge et récapitulatif le 2026-11-10, pour tous les joueurs des jeux, élèves compris (ADR-0004, amendement du
2026-11-10) ; la certification Génie Imhotep reste sans correction.

## Comportement attendu

### Banque de questions

1. La migration `ceae698cb3d6` charge `backend/alembic/donnees/quiz_sante.json` : 922 QCM en 34 lots, publiés comme
   quiz du parcours « jeux », validés au nom d'AIMES-AFRIQUE. Un quiz déjà présent (même titre) n'est ni dupliqué
   ni modifié.
2. Depuis la spec 034, ces 34 quiz sont dépubliés : les 100 défis du parcours officiel tirent leurs questions dans
   les mêmes lots, par pôle. Les 922 QCM restent la réserve des quiz Jeux.

### Joueur sans compte

3. Sur la page des jeux, « Relever le défi » ouvre une fenêtre de jeu. Sans compte, la partie passe par
   `/api/jeux/quiz` ; connecté, par les routes habituelles des quiz, avec leurs règles et leurs points.
4. Au premier lancement, l'API crée un compte de rôle `invite` : sans e-mail, sans mot de passe valable, nommé
   « Joueur sans compte ». Il est reconnu par un cookie à part (`sosclub_invite`, `HttpOnly`, 7 jours), qui ne vaut
   jamais comme session : aucune autre route ne l'accepte.
5. Le serveur arbitre ses parties comme toutes les autres (ADR-0004) : tirage, temps, résultat. Elles ne
   rapportent aucun point, aucun badge, et la certification lui est fermée.
6. Il joue au plus **3 quiz différents**. Reprendre ou rejouer un quiz déjà commencé ne compte pas une seconde fois.
   Le quatrième est refusé (403, en-tête `X-Raison: fin-essai`). Le site montre alors « Ta période d'essai est
   terminée » et un lien vers `/inscription`. Le site ne lit que cet en-tête : un autre refus 403 (origine,
   certification) garde son propre message.
7. Pendant l'essai, le site n'affiche ni bandeau ni compteur ; le catalogue renvoie les quiz restants.
8. Une même adresse IP crée au plus 30 joueurs sans compte par heure (une salle informatique partage une adresse) ;
   au-delà, 429 « Trop de parties sans compte depuis ce réseau : crée ton compte. ».
9. Les joueurs sans compte de plus de 7 jours sont effacés avec leurs parties, par la purge des visiteurs.
10. Ils n'apparaissent ni dans « Inscrits », ni dans les compteurs du tableau de bord admin ; l'export les nomme
    « Joueur sans compte ».
11. Un compte connecté qui appelle `/api/jeux/quiz/.../tentatives` reçoit 409 « Tu es connecté : joue depuis tes
    quiz. ».

### Correction et récapitulatif (parcours jeux)

12. Après chaque réponse, ou quand le temps est écoulé, l'API renvoie la correction de cette seule question, déjà
    tranchée : juste ou non, choix du joueur, choix attendu. Aucune réponse n'est envoyée avant.
13. Le site fait clignoter le choix en vert ou en rouge et montre la bonne réponse pendant 1,2 s. Le serveur ne
    démarre le chrono de la question suivante qu'après cette pause (`PAUSE_CORRECTION`).
14. À la fin, le résultat récapitule les questions ratées : la question, la réponse du joueur, la bonne réponse et
    l'explication. Un sans-faute donne un récapitulatif vide.
15. La certification Génie Imhotep ne corrige rien : score seul, sans pause.
16. Chaque question des jeux laisse 20 secondes (migration `15ac5cbf557f`).

## Critères d'acceptation

- [x] Le catalogue des quiz Jeux est public et indique, sans compte, les quiz restants.
- [x] Un joueur sans compte termine une partie sans aucune ligne dans `mouvement_points`.
- [x] Le quatrième quiz différent est refusé (403, `X-Raison: fin-essai`) ; rejouer un quiz déjà commencé reste
      permis.
- [x] Le cookie du joueur sans compte n'ouvre aucune route réservée aux comptes connectés.
- [x] La certification reste fermée au joueur sans compte.
- [x] Un compte connecté joue depuis ses quiz (409 sur la route sans compte).
- [x] La partie d'un autre joueur sans compte est introuvable (404).
- [x] Les joueurs sans compte n'apparaissent pas dans « Inscrits ».
- [x] La purge efface les joueurs sans compte de plus de 7 jours.
- [x] Les quiz des jeux laissent 20 secondes par question.
- [x] Un refus d'origine (403 sans l'en-tête) n'est pas pris pour une fin d'essai, côté API et côté site.
- [x] La pause de correction ne prend pas sur le temps de la question suivante ; la certification n'a pas de pause.
- [x] Le récapitulatif liste les erreurs avec la bonne réponse et l'explication ; un sans-faute a un récapitulatif
      vide.

Tests : `backend/tests/test_jeux_quiz_invites.py`, `backend/tests/test_quiz_partie.py`,
`src/components/quiz/DefiQuiz.test.tsx`, `src/components/quiz/PartieQuiz.test.tsx`.

## Cas limites et erreurs

- **Deux lancements simultanés de quiz différents** : le joueur est verrouillé, la limite de 3 tient.
- **Cookie effacé** : un nouveau joueur sans compte est créé ; la limite par adresse IP freine les boucles.
- **Partie commencée sur un des 34 anciens quiz avant la spec 034** : elle finit sans rien rapporter.
- **Rejouer un quiz** : la correction donne les réponses des questions déjà vues. Conséquence acceptée par le
  porteur du projet le 2026-11-10 (ADR-0004).

## Hors périmètre

- Les points, les badges, le classement et la certification pour un joueur sans compte ou un visiteur.
- La reprise des parties d'essai dans un compte créé ensuite.
- La relecture des 922 QCM par l'équipe nationale (document officiel repris tel quel).

## Questions ouvertes

Aucune.
