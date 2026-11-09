# 029 — Certification Génie Imhotep : parcours, badges et certificat (R11)

## Objectif

Ouvrir le parcours officiel de certification (PRD : « Le parcours Génie Imhotep compte 12 quiz obligatoires et
des fascicules ; sa réussite donne un certificat vérifiable, 5 badges et le bonus de certification, une seule
fois » ; CDC admin § 7 et § 9). Il réutilise le moteur de quiz arbitré par le serveur (spec 027, ADR-0004) et
les fascicules de la bibliothèque (spec 028).

Trois publics :

- les joueurs : élèves actifs et encadreurs vérifiés suivent les 12 quiz dans l'ordre, débloquent 5 badges et
  obtiennent le certificat ;
- l'équipe nationale : elle prépare les quiz du parcours comme ceux des jeux (publication à deux personnes,
  validateur médical), règle les badges et gère les certificats (réémission, révocation motivée) ;
- tout le monde : une page publique vérifie un certificat par son numéro ou son QR code, sans nom réel.

Règles des badges (Q24) : en attendant l'équipe pédagogique, les paliers affichés sur `/certification` (après
3, 5, 7, 9 et 12 quiz réussis), réglables et versionnés dans l'espace admin.

## Comportement attendu

**Le parcours (équipe, droits `quiz`)**

1. Un quiz appartient à un parcours : « jeux » (spec 027) ou « certification ». Un quiz de certification occupe
   une place de 1 à 12 et peut être relié à un fascicule publié de la bibliothèque. Il se prépare, se teste, se
   soumet et se publie comme un quiz de jeux (deux personnes, validateur médical nommé).
2. Une place n'a qu'un quiz publié à la fois. Publier un quiz sur une place occupée est refusé : il faut d'abord
   dépublier l'autre.
3. Le parcours « certification » a ses propres paramètres versionnés (nombre de questions, temps, tolérance,
   seuil, parties par jour), aux mêmes valeurs par défaut que les jeux (15, 5 s + 2 s, 12, 10).
4. Les règles des badges sont versionnées : pour chacun des 5 badges, un nom et un palier (nombre de quiz du
   parcours réussis). Les paliers sont croissants, le dernier vaut 12. Par défaut : Bronze 3, Argent 5, Or 7,
   Platine 9, Diamant Imhotep 12. Une nouvelle version ne vaut que pour les badges à venir.

**Suivre le parcours (élève actif, encadreur vérifié)**

5. « Ma certification » (`/certification/parcours`) montre les 12 places dans l'ordre, chacune : verrouillée,
   ouverte, réussie (avec le meilleur score) ou « bientôt disponible » (aucun quiz publié sur cette place) ; les 5
   badges (obtenu ou verrouillé, avec leur palier) ; le certificat s'il est obtenu.
6. La place 1 est ouverte d'emblée ; une place s'ouvre quand la précédente est réussie. Avant de jouer, le
   joueur voit le fascicule relié (lire ou télécharger).
7. Une partie de certification se joue comme une partie de jeux : une question à la fois, chrono et score
   arbitrés par le serveur, plafond quotidien, reprises libres. Réussir un quiz de certification ne rapporte pas
   les +50 d'un quiz de jeux : les points du parcours viennent des badges et du certificat.
8. Quand le nombre de quiz du parcours réussis atteint le palier d'un badge, le badge est attribué
   automatiquement. Un élève actif gagne +500 (`eleve.badge`, une fois par badge) ; un encadreur obtient le
   badge sans points (aucun montant au barème).
9. Quand les 12 places sont réussies, le certificat est délivré automatiquement avec un numéro unique, non
   devinable. Un élève actif gagne +1 000 (`eleve.certification`), un encadreur vérifié +1 000
   (`encadreur.certification`, mis en service). Une seule fois par personne. Le club bénéficiaire (celui de
   l'élève affilié) est enregistré pour les +200 par badge et +500 de la certification, crédités avec R13.
10. Le joueur est prévenu de chaque badge et du certificat par une notification (spec 023).
11. Le titulaire télécharge son certificat en PDF : prénom et nom, « Certificat Génie Imhotep », date, numéro, et
    un QR code vers la page de vérification. Personne d'autre ne télécharge ce PDF.

**Vérifier (tout le monde)**

12. `/certificats/<numero>` (ou le QR code) indique : certificat valide, révoqué ou introuvable ; pour un élève son
    pseudonyme et son club, pour un encadreur son prénom, l'initiale de son nom et sa fonction ; la date. Jamais
    le nom complet d'un élève, ni son établissement s'il n'a pas de club.

**Gérer les certificats (équipe)**

13. La liste des certificats (numéro, titulaire, date, état) et des badges délivrés est consultable par les droits
    `quiz` consulter. Un collaborateur qui a le droit sensible de dépublier un quiz peut :
    - révoquer un certificat avec un motif (fraude avérée, erreur) : la vérification affiche « révoqué », le PDF
      n'est plus téléchargeable, et les points du certificat sont retirés par une ligne négative au registre ;
    - réémettre un certificat (correction du nom) : un nouveau numéro remplace l'ancien, qui affiche
      « remplacé » ; aucun point de plus.
14. Révocations et réémissions entrent au journal d'audit et sont notifiées au titulaire.

## Critères d'acceptation

- [ ] Étant donné un quiz de certification à la place 4 et un joueur qui n'a pas réussi la place 3, quand il le
      lance, alors l'API refuse (403) ; après la réussite de la place 3, il le lance.
- [ ] Étant donné une place déjà occupée par un quiz publié, quand un autre quiz de cette place est approuvé,
      alors l'API refuse (409).
- [ ] Étant donné les règles par défaut, quand un élève actif réussit son 3e quiz du parcours, alors il reçoit le
      badge Bronze et une seule ligne de +500 ; une nouvelle réussite d'un quiz déjà réussi n'ajoute rien.
- [ ] Étant donné un encadreur vérifié qui atteint un palier, alors il reçoit le badge et aucune ligne de points.
- [ ] Étant donné un joueur qui réussit la place 12 en ayant réussi les 11 autres, alors un certificat est créé
      avec un numéro unique, et une seule ligne de +1 000 est écrite (élève ou encadreur), même si deux fins de
      partie arrivent en même temps.
- [ ] Étant donné un quiz de certification réussi, alors aucune ligne `eleve.quiz` (+50) n'est écrite.
- [ ] Étant donné des règles de badges incohérentes (paliers non croissants, dernier palier différent de 12,
      nom vide), alors l'API refuse (422).
- [ ] Étant donné une nouvelle version des règles des badges, alors les badges déjà obtenus restent, et les
      suivants suivent la nouvelle version.
- [ ] Étant donné un numéro de certificat, alors la page publique n'expose ni le nom complet d'un élève, ni son
      identifiant, ni son établissement ; un numéro inconnu répond « introuvable » (404) ; un numéro révoqué
      répond « révoqué ».
- [ ] Étant donné un autre compte que le titulaire (même un collaborateur), quand il demande le PDF du
      certificat, alors l'API répond 403 ou 404.
- [ ] Étant donné une révocation sans motif ou sans double authentification, alors l'API refuse ; avec motif,
      les points du certificat sont retirés une seule fois et le titulaire est prévenu.
- [ ] Étant donné une réémission, alors l'ancien numéro répond « remplacé » et le nouveau « valide », sans
      nouvelle ligne de points.
- [ ] Étant donné un visiteur, un élève suspendu ou un encadreur non vérifié, quand il appelle une route du
      parcours, alors l'API répond 401 ou 403.
- [ ] Étant donné un élève, un encadreur ou un président, quand il appelle une route de gestion du parcours, des
      badges ou des certificats, alors l'API répond 403.

## Cas limites et erreurs

- **Quiz dépublié d'une place** : les réussites déjà acquises comptent toujours ; la place affiche « bientôt
  disponible » pour qui ne l'a pas réussie, et bloque les suivantes jusqu'à la publication d'un remplaçant. Un
  remplaçant publié sur la même place n'oblige pas à rejouer qui avait réussi l'ancien.
- **Palier abaissé** : un joueur qui l'atteint déjà reçoit le badge à sa prochaine réussite ou à sa prochaine
  ouverture de « Ma certification ».
- **Compte suspendu** : pas de partie ; les badges et le certificat atteints pendant la suspension sont délivrés
  à la réactivation (prochaine ouverture), avec leurs points si l'élève est alors actif.
- **Élève sans club** : badges et certificat délivrés ; aucun club bénéficiaire enregistré.
- **Deux fins de partie simultanées** sur la dernière place : un seul certificat, une seule ligne de points (clés
  uniques du registre et du certificat).
- **Certificat révoqué** puis rejoué : pas de nouveau certificat automatique ; seule une réémission par l'équipe
  le rétablit.
- **Nom modifié après la certification** : le PDF garde le nom de sa délivrance ; l'équipe réémet si besoin.

## Hors périmètre

- Les lots « jusqu'à 1 million FCFA » et leur règlement (gestion hors plateforme, PRD).
- Les points des clubs (+200 par badge, +500 par certification) : enregistrés ici, crédités avec R13.
- Les +50 de l'encadreur pour un élève accompagné jusqu'à la certification (barème proposé, règle à arbitrer).
- Les compétitions Génie Imhotep, le palmarès et le Hall of Fame (R13, R14).
- La carte membre (R15), le certificat en anglais, l'envoi du certificat par e-mail.
- Les badges attribués à la main par l'admin.

## Questions ouvertes

Aucune : paliers du site réglables, parcours dans l'ordre, élèves et encadreurs, nom réel dans le seul PDF
(tranchés le 2026-11-09). Les vraies règles des badges (Q24) seront saisies par l'équipe pédagogique dans
l'espace admin.
