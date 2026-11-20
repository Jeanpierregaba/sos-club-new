# 046 — Temps passé sur les quiz et la certification d'un inscrit

## Objectif

Prolonge la fiche d'un inscrit (spec 045). L'équipe nationale (droit `inscrits:consulter`) voit combien de temps un
élève ou un encadreur passe sur chaque quiz, chaque question, chaque place, chaque badge et pour son certificat. Elle
le compare au temps moyen des autres joueurs, pour repérer un parcours anormalement rapide (soupçon de triche) ou un
élève en difficulté.

Aucune nouvelle donnée n'est collectée : la base enregistre déjà le début, la dernière activité et la fin de chaque
tentative, ainsi que l'heure d'affichage et de réponse de chaque question.

## Définitions

- **Temps de jeu d'une tentative** : de son début à sa dernière activité (`derniere_activite − commencee_le`). Pas
  jusqu'à `terminee_le` : une partie abandonnée est close quand le joueur revient, parfois des jours plus tard, ce
  qui gonflait la durée affichée par la spec 045.
- **Temps d'une question** : de son affichage à la réponse (`repondue_le − envoyee_le`), en secondes, au dixième.
  Une question sans réponse vaut le temps imparti, marquée « temps écoulé ». Une question jamais affichée (partie
  arrêtée avant) est marquée « non posée », sans temps.
- **Temps de jeu d'une place** : somme des temps de jeu des tentatives (hors essais) sur le quiz de cette place,
  jusqu'à la tentative réussie incluse. Avec le nombre de tentatives.
- **Badge** : deux mesures.
  - *Temps de jeu* : somme des temps de jeu des tentatives de certification (hors essais) commencées après le badge
    précédent (ou depuis le début) et au plus tard à l'obtention du badge. Avec le cumul depuis le début.
  - *Durée calendaire* : du badge précédent (ou de la première tentative de certification) à l'obtention.
- **Certificat** : temps de jeu cumulé et durée calendaire de la première tentative de certification à sa
  délivrance.
- **Moyenne nationale d'un quiz** : temps de jeu moyen des tentatives réussies des **autres** joueurs (hors essais)
  sur ce quiz, avec leur nombre. Affichée seulement à partir de 5 tentatives réussies d'autres joueurs.

## Comportement attendu

1. **Onglet Quiz**
   - Le résumé ajoute le temps de jeu total et le temps moyen par tentative.
   - Chaque quiz validé montre le temps de la première réussite, à côté de la moyenne nationale. Une pastille « Très
     rapide » apparaît quand ce temps est inférieur à la moitié de la moyenne (5 réussites d'autres joueurs au
     moins).
   - Chaque tentative montre son temps de jeu (corrigé). Une tentative close après un abandon porte la mention
     « abandonnée ».
2. **Détail d'une tentative** : un clic sur une tentative ouvre un panneau. Pour chaque question, dans l'ordre :
   - le rang et l'énoncé ;
   - la réponse choisie (texte), juste ou fausse, « temps écoulé » ou « non posée » ;
   - les secondes mises et le temps imparti.

   La bonne réponse n'est pas affichée, car elle relève de la banque de quiz et non de la fiche d'un inscrit. Un
   essai de l'équipe se consulte de la même façon.
3. **Onglet Certification**
   - Chaque place réussie montre son temps de jeu et son nombre de tentatives.
   - Chaque badge montre son temps de jeu (depuis le badge précédent et cumulé) et sa durée calendaire.
   - Chaque certificat montre le temps de jeu cumulé et la durée calendaire jusqu'à sa délivrance.

## Critères d'acceptation

- [ ] Étant donné une tentative close 3 jours après sa dernière activité, quand l'équipe ouvre l'onglet Quiz, alors
      son temps de jeu vaut `derniere_activite − commencee_le` et elle est marquée « abandonnée ».
- [ ] Le résumé des quiz donne le temps de jeu total et moyen des tentatives terminées hors essais.
- [ ] Étant donné 5 réussites d'autres joueurs sur un quiz, la moyenne nationale s'affiche avec leur nombre. Avec 4
      réussites, elle est absente (`null`).
- [ ] Les tentatives de l'inscrit lui-même et les essais n'entrent pas dans la moyenne nationale.
- [ ] Une première réussite en moins de la moitié de la moyenne est marquée « Très rapide ».
- [ ] `GET /api/admin/inscrits/{id}/tentatives/{tentative_id}` renvoie les questions dans l'ordre, avec :
  - le temps en secondes ;
  - les états « juste », « fausse », « temps écoulé » et « non posée » ;
  - la réponse choisie dans le texte de la question ;
  - jamais la bonne réponse.
- [ ] Une tentative d'un autre joueur demandée sous la fiche d'un inscrit → 404.
- [ ] Le temps de jeu d'une place cumule les tentatives sur son quiz jusqu'à la réussite incluse, et non celles
      d'après.
- [ ] Le temps de jeu d'un badge cumule les tentatives de certification entre le badge précédent et son obtention.
      Sa durée calendaire part du badge précédent, ou de la première tentative de certification pour le premier.
- [ ] Un certificat montre le temps de jeu cumulé et la durée calendaire jusqu'à sa délivrance.
- [ ] Sans le droit `inscrits:consulter` national → 403 sur la nouvelle route.
- [ ] Le site affiche les durées en « 1 min 05 s », « 2 h 10 min » ou « 3 j 4 h », et le panneau de détail.

## Cas limites et erreurs

- **Tentative en cours** : temps de jeu jusqu'à la dernière activité, marquée « en cours ».
- **Question affichée après une pause de correction** (`envoyee_le` dans le futur au moment de l'envoi) : le temps
  compté part de `envoyee_le`. Il n'est jamais négatif : on le borne à 0.
- **Quiz remplacé à une place** : la place compte les tentatives sur tous les quiz qui ont occupé cette place, pas
  seulement le dernier.
- **Badge obtenu sans tentative retrouvée** (données anciennes) : temps de jeu 0, durée calendaire absente.
- **Inscrit sans tentative** : résumé à 0, aucun quiz validé, places, badges et certificats sans temps.
- **Certificat remplacé ou révoqué** : les temps se calculent de la même façon, d'après sa date de délivrance.
- **Volume** : moyennes et cumuls calculés en SQL (agrégats), jamais toutes les tentatives en mémoire.

## Hors périmètre

- Mesurer le temps passé à lire les contenus ou sur le site en général : rien n'est enregistré.
- Afficher la bonne réponse d'une question (elle se consulte dans la banque de quiz).
- Exporter ces temps, ou les montrer à l'élève ou à son encadreur.
- Signaler ou bloquer automatiquement un joueur jugé trop rapide : la pastille n'est qu'un repère pour l'équipe.

## Questions ouvertes

Aucune. Choix tranchés le 2026-11-20 :
- badge : temps de jeu et durée calendaire ;
- détail par question avec l'énoncé ;
- comparaison à la moyenne nationale.
