# 034 — Gamification de l'élève : 100 quiz sur 4 niveaux, étoiles, carte Gold, club à 50 %

Source : cahier des charges « Espace Élève — Gamification et récompenses », référentiel consolidé du
2026-11-10 (reçu le 2026-11-11). Ses montants, la répartition des 100 quiz en 4 niveaux, les 4 étoiles et la
règle « Club = moitié des points Élève » s'appliquent tels quels. Il remplace la spec 022 (harmonisation du
barème) partout où ils divergent.

Décisions du porteur du projet (2026-11-11) :

- livraison en **4 lots** successifs, chacun testé et commité seul ;
- les 100 quiz sont répartis **par cotation** : les 40 moins cotés en Débutant, puis 30 Intermédiaire, 20 Avancé
  et les 10 plus cotés en Expert ; l'équipe peut changer le niveau d'un quiz dans l'admin ;
- certification : **la proposition opérationnelle** du document s'applique, avec 5 thématiques de 4 quiz et un
  badge à la fin de chaque thématique ; les thématiques portent provisoirement le nom de leur badge ;
- **rien de rétroactif** : le nouveau barème vaut pour les crédits à venir ; l'historique reste tel quel.

## Objectif

Donner à l'élève trois parcours récompensés et lisibles (Certification, Jeux, Vie du site), consolidés dans un
score annuel. Le Club Santé de l'élève reçoit, pour chaque gain, exactement la moitié des points.

## Comportement attendu

### Règle transversale : le club reçoit la moitié (lot 1)

- Chaque gain de points d'un **élève** crédite, dans la même écriture, son Club Santé de la moitié du montant
  (+5 → +2,5, sans arrondi).
- Le club n'est crédité que si l'affiliation de l'élève est **active** au moment du crédit et que le club est
  **en service** (actif ou en régularisation, spec 033). Sinon, l'élève garde ses points, aucun club n'est
  crédité.
- Le club crédité reste celui du moment du gain : un changement d'établissement ne transfère rien.
- Une annulation retire aussi la part du club.
- Les encadreurs, visiteurs et joueurs sans compte n'ouvrent aucune part de club.
- Les anciennes lignes « club.* » du barème (part fixe du club) ne servent plus.

### Barème (lot 1, montants Élève ; le club reçoit la moitié)

| Parcours      | Action                                                     | Élève                 |
| ------------- | ---------------------------------------------------------- | --------------------- |
| Certification | Quiz de certification validé (première fois)               | 50                    |
| Certification | Badge obtenu (5)                                           | 500                   |
| Certification | Certificat final                                           | 1 000                 |
| Jeux          | Quiz Débutant / Intermédiaire / Avancé / Expert réussi     | 50/100/150/200        |
| Jeux          | Étoile 1 / 2 / 3 / 4 (niveau validé)                       | 500/1 000/1 500/3 000 |
| Vie du site   | Compte créé et validé                                      | 100                   |
| Vie du site   | Commentaire approuvé                                       | 5                     |
| Vie du site   | Republication vérifiée d'un article, par article et réseau | 10                    |
| Vie du site   | Article personnel approuvé et publié                       | 50                    |
| Vie du site   | Partage vérifié de son article, par réseau                 | 50                    |
| Vie du site   | Bonne réponse à la question du jour                        | 20                    |

Chaque ligne du barème porte son **parcours** (certification, jeux, vie du site) et, pour les Jeux, son
sous-compte (« points des quiz » ou « points des étoiles »). Les actions « republication » et « partage » ne sont
pas encore écrites par le code (spec à venir) : leurs montants sont réglés, sans plus.

### Parcours B — les 100 quiz Jeux (lot 2)

- Les 100 défis du parcours officiel deviennent **100 quiz distincts** côté serveur, chacun avec son niveau,
  son numéro et son pôle. Chaque quiz tire ses questions dans une réserve prise dans le lot de son pôle (922 QCM
  du Jeu Quiz Santé).
- Réussir un quiz pour la première fois rapporte le montant de son niveau. Le rejouer ne rapporte rien.
- Un niveau est **validé** quand tous ses quiz publiés sont réussis : son étoile est débloquée et son bonus
  crédité une seule fois.
- Avec les 4 étoiles, la **carte de membre** numérique de l'élève passe au statut **Gold**. Elle montre le nombre
  de quiz réussis et les 4 étoiles. Le statut Gold rend l'élève éligible au tirage au sort : l'équipe voit la
  liste des élèves Gold dans l'admin (sans tirage automatique).
- La page Jeux, le compte de l'élève, l'espace Club Santé et le journal montrent séparément « points des quiz »
  (max 10 000), « points des étoiles » (max 6 000) et le total Jeux (max 16 000).
- Le nombre de questions, le temps, le seuil et le plafond de tentatives des quiz Jeux restent réglables dans
  l'admin et sont affichés avant chaque quiz.

### Parcours A — la certification Génie Imhotep (lot 3)

- **20 places**, jouées dans l'ordre, en 5 thématiques de 4 quiz.
- 10 questions par quiz, 20 secondes par question.
- Réussite à **10/10** : à la première erreur ou au premier temps écoulé, la tentative s'arrête, ne rapporte rien,
  et le quiz recommence à la question 1. On peut recommencer jusqu'à réussite (aucun plafond quotidien).
- Une place validée : +50. Les 4 places d'une thématique validées : son badge (+500). Les 20 places et les 5
  badges : le certificat (+1 000), une seule fois.
- Les 5 badges, dans l'ordre : Ambassadeur Santé Junior ; Pair Éducateur Santé et Citoyenneté ; Sentinelle de la
  Prévention ; Champion de la Santé et EVSS ; Maître Génie Imhotep.
- La certification reste sans correction : score seul (ADR-0004, amendement du 2026-11-10).

### Année académique, tableau de bord et archives (lot 4)

- L'équipe définit les années académiques (septembre N à juillet N+1, dates exactes dans l'admin). Chaque gain
  est rattaché à l'année en cours.
- Les compteurs annuels de l'élève et du club repartent de zéro à chaque nouvelle année ; rien n'est effacé.
- À la clôture d'une année, l'équipe **fige** le classement régional annuel (archivé, daté). Les crédits suivants
  vont dans l'année suivante.
- Le tableau de bord de l'élève montre : la vue annuelle (total élève, total apporté à son club, rang régional,
  place dans son club), puis un décompte par parcours :
  - Certification : quiz validés sur 20, badges, certificat, points quiz / badges / certificat ;
  - Jeux : niveau courant, quiz réussis sur 100, étoiles, points des quiz, points des étoiles, total, carte Gold ;
  - Vie du site : actions en attente de modération et approuvées, points d'engagement, contribution au club ;
  - l'historique des transactions et les archives des années passées.
- L'espace « Mon Club Santé » de l'encadreur montre le total annuel du club, par parcours.
- Un élève qui quitte le système scolaire peut passer **ancien élève** : il garde l'accès à ses archives et ne
  gagne plus de récompenses d'élève.
- Les classements publics ne montrent que pseudonymes, clubs, points et rangs.

## Critères d'acceptation

Lot 1 — club à 50 % et barème

- [ ] Étant donné un élève affilié (affiliation active) à un club en service, quand il gagne +5, alors le
      registre porte +5 pour l'élève et +2,5 pour le club, dans la même écriture.
- [ ] Étant donné un élève sans affiliation active, ou dont le club est suspendu, quand il gagne des points,
      alors aucun club n'est crédité.
- [ ] Étant donné un gain annulé, alors l'élève et le club perdent chacun leur part.
- [ ] Étant donné un élève qui change d'établissement, alors les points déjà crédités restent à son ancien club.
- [ ] Étant donné un gain d'encadreur, alors aucun club n'est crédité.
- [ ] Le barème contient les montants du tableau ci-dessus, avec leur parcours ; les anciennes lignes « club.* »
      sont hors service.
- [ ] Le score d'un club est la somme de ses demi-parts, affichée avec sa décimale (« 2,5 »).

Lot 2 — Jeux

- [ ] Il existe 100 quiz Jeux publiés : 40 Débutant, 30 Intermédiaire, 20 Avancé, 10 Expert.
- [ ] Un quiz Débutant réussi une première fois : +50 élève / +25 club, au sous-compte « points des quiz » ;
      un quiz Expert : +200 / +100.
- [ ] Un quiz déjà récompensé, rejoué et réussi : 0 point de plus, élève comme club.
- [ ] Les 40 quiz Débutant réussis : étoile 1, +500 / +250 ; de même 30 Intermédiaire → +1 000 / +500,
      20 Avancé → +1 500 / +750, 10 Expert → +3 000 / +1 500 et carte Gold.
- [ ] Les 100 quiz et les 4 étoiles : 16 000 élève (10 000 quiz + 6 000 étoiles), 8 000 club.
- [ ] Un élève non affilié qui réussit un quiz : points élève seulement.
- [ ] La page Jeux, le compte de l'élève et l'espace du club affichent les deux sous-totaux et le total Jeux.
- [ ] L'admin liste les élèves Gold.

Lot 3 — Certification

- [ ] Il y a 20 places ; la place N+1 reste fermée tant que la place N n'est pas validée.
- [ ] Une réponse fausse ou un temps dépassé arrête la tentative : quiz non validé, 0 point, la prochaine
      partie recommence à la question 1.
- [ ] 10/10 sur une place : +50 / +25, une seule fois.
- [ ] Les 4 places d'une thématique validées : son badge, +500 / +250.
- [ ] 20 places et 5 badges : certificat, +1 000 / +500 ; total 4 500 élève / 2 250 club.
- [ ] Aucun plafond quotidien de tentatives en certification.

Lot 4 — Année académique, tableau de bord, archives

- [ ] Étant donné une nouvelle année académique ouverte, alors les compteurs annuels élève et club sont à
      zéro, et les archives des années passées sont inchangées.
- [ ] La clôture d'une année fige le classement régional annuel ; le refaire ne change rien.
- [ ] Le tableau de bord de l'élève affiche la vue annuelle et les décomptes des trois parcours.
- [ ] Un ancien élève voit ses archives et ne gagne plus de points.
- [ ] Aucun classement public ne montre un nom complet ou un contact d'élève.

## Cas limites et erreurs

- Deux gains simultanés de la même action : un seul crédit (clé unique), pour l'élève comme pour le club.
- Un élève valide le dernier quiz d'un niveau en même temps sur deux appareils : une seule étoile.
- Un quiz Jeux dépublié : il ne compte plus pour valider un niveau ; l'étoile déjà obtenue reste.
- Un quiz qui change de niveau après avoir été réussi : le gain déjà crédité reste ; le nouveau niveau compte
  pour l'étoile.
- Moins de 4 quiz publiés dans une thématique, ou moins de 20 places : le certificat reste inaccessible.
- Affiliation retirée entre deux gains : le second ne crédite plus le club.
- Le compte de l'élève est crédité à l'inscription, quand son affiliation est encore à confirmer : la moitié de
  ces +100 ne va à aucun club (règle « affiliation active au moment du crédit »).
- Un élève suspendu garde ses points, mais n'alimente plus son club.
- Gain hors de toute année académique : il compte dans le total historique, pas dans un compteur annuel.

## Notes de déploiement

- Les 34 quiz Jeux de la spec 031 sont dépubliés par la migration du lot 2 : une partie commencée dessus avant le
  déploiement ne rapporte plus rien à sa fin.
- Une partie de certification commencée avant la migration du lot 3 finit avec ses anciens paramètres (15
  questions, réussite à 12, sans arrêt) ; une réussite rapporte la place et +50.
- Les badges déjà délivrés sous les anciennes règles (Bronze à 3, Argent à 5…) gardent leur nom ; le rang suivant
  se délivre au palier des nouvelles règles. Le total des points reste juste (rien de rétroactif).
- Le certificat PDF écrit le nombre de quiz réussis à sa délivrance (12 pour un certificat d'avant la spec 034).
- Le passage en ancien élève n'a pas de retour arrière dans l'admin.

## Hors périmètre

- Le règlement et le tirage au sort eux-mêmes (période, gagnants, lots) : seule la liste des éligibles est livrée.
- Les lots des récompenses régionales annuelles et leur départage.
- Les plafonds anti-spam des contributions répétitives (aucune limite sans validation).
- Les points propres au compte collectif du club (rapports des encadreurs) et le barème des encadreurs.
- La vérification des republications et des partages (spec à venir) : seuls leurs montants sont réglés.
- Le renouvellement annuel des parcours, des étoiles, du certificat et du statut Gold (question ouverte 1).

## Questions ouvertes

1. Renouvellement annuel : en attendant l'arbitrage, une récompense de quiz, d'étoile, de badge ou de
   certificat déjà obtenue **ne se gagne pas une seconde fois** une autre année. La carte Gold reste acquise.
   À confirmer par l'équipe (document, section 9).
